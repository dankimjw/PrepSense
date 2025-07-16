#!/usr/bin/env python3
"""
Unified launcher for PrepSense backend server and iOS app.
This script ensures both the backend and the Expo‑based iOS front‑end
share a consistent IP/port configuration.

Typical usage
-------------
python3 run_app.py            # start backend + iOS (default)
python3 run_app.py --backend  # backend only
python3 run_app.py --ios      # iOS only
python3 run_app.py --help     # full CLI
"""

import argparse
import atexit
import os
import platform
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Optional

import uvicorn
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────────────────────
# 1. **Environment‑variable cleanup** – values in .env (or pydantic settings)
#    always win over ad‑hoc `export`‑ed ones.
# ──────────────────────────────────────────────────────────────────────────────
_VARIABLES_TO_UNSET: List[str] = [
    "BIGQUERY_PROJECT",   # comes from .env or Settings
    "PORT",               # set via CLI or .env
    # add more here as needed
]
for var in _VARIABLES_TO_UNSET:
    if var in os.environ:
        print(f"run_app.py: Unsetting {var} (found '{os.getenv(var)}' in shell env)")
        del os.environ[var]
        # If on Python 3.11+ with os.environ.mapping
        if hasattr(os.environ, "mapping"):
            os.environ.mapping.pop(var, None)

# ──────────────────────────────────────────────────────────────────────────────
# 2.  Defaults
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_HOST = "0.0.0.0"
DEFAULT_BACKEND_PORT = 8001
DEFAULT_IOS_PORT = 8082

# ──────────────────────────────────────────────────────────────────────────────
# 3.  Helper utilities
# ──────────────────────────────────────────────────────────────────────────────
def get_local_ip(fallback: str = DEFAULT_HOST) -> str:
    """Best‑effort LAN IP discovery (used when HOST is 0.0.0.0/localhost)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return fallback


def check_port_available(host: str, port: int) -> bool:
    """Return True iff <host,port> can be bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
        test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            test_sock.bind((host, port))
            return True
        except OSError:
            return False


def kill_processes_on_port(port: int, host: str = "0.0.0.0") -> bool:
    """SIGTERM/SIGKILL whatever is bound to *port* (cross‑platform)."""
    killed_any = False
    if platform.system() == "Windows":
        result = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        for line in lines:
            if f":{port} " in line and (f"{host}:" in line or "0.0.0.0" in line):
                pid = line.split()[-1]
                subprocess.run(["taskkill", "/F", "/PID", pid], stderr=subprocess.PIPE)
                print(f"Killed PID {pid} on port {port}")
                killed_any = True
    else:
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True)
        for pid in result.stdout.splitlines():
            if pid.strip():
                # Try TERM, fall back to KILL if necessary
                if subprocess.run(["kill", "-TERM", pid]).returncode != 0:
                    subprocess.run(["kill", "-KILL", pid])
                print(f"Terminated PID {pid} on port {port}")
                killed_any = True
    if killed_any:
        time.sleep(1.5)
    return killed_any


# ──────────────────────────────────────────────────────────────────────────────
# 4.  Fancy CLI
# ──────────────────────────────────────────────────────────────────────────────
def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PrepSense App Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples
--------
python3 run_app.py                 # backend + iOS
python3 run_app.py --backend       # backend only
python3 run_app.py --ios           # iOS only
python3 run_app.py --backend --port 9000
""",
    )
    parser.add_argument("--backend", action="store_true", help="Start backend only")
    parser.add_argument("--ios", action="store_true", help="Start iOS only")
    parser.add_argument("--host", type=str, help="Backend host (overrides HOST env)")
    parser.add_argument("--port", type=int, help="Backend port (overrides PORT env)")
    parser.add_argument("--ios-port", type=int, help="Expo/iOS port (overrides IOS_PORT)")
    parser.add_argument("--gcp", action="store_true", help="Use GCP Cloud Run backend")
    return parser.parse_args()


# ──────────────────────────────────────────────────────────────────────────────
# 5.  Process manager – guarantees cleanup on SIGINT/SIGTERM/exit
# ──────────────────────────────────────────────────────────────────────────────
class ProcessManager:
    def __init__(self):
        self.backend: Optional[subprocess.Popen] = None
        self.ios: Optional[subprocess.Popen] = None
        self._cleanup_registered = False

    def _signal_handler(self, signum, _frame):
        print(f"\nReceived signal {signum} – shutting down…")
        self.cleanup()
        sys.exit(0)

    def register(self):
        if not self._cleanup_registered:
            atexit.register(self.cleanup)
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            self._cleanup_registered = True

    def cleanup(self):
        print("Cleaning up child processes…")
        for proc, name in [(self.ios, "iOS"), (self.backend, "backend")]:
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    print(f"{name} process stopped")
                except subprocess.TimeoutExpired:
                    proc.kill()
                    print(f"{name} forcibly killed")

        # Expo uses several well‑known ports
        expo_ports = [19000, 19001, 19002, 19006, 8081]
        for p in expo_ports:
            kill_processes_on_port(p)
        if self.ios:
            kill_processes_on_port(self.ios.args[-1])  # ios‑port


# ──────────────────────────────────────────────────────────────────────────────
# 6.  Starters
# ──────────────────────────────────────────────────────────────────────────────
def start_backend(host: str, port: int, hot_reload: bool = True):
    print(f"Starting backend on {host}:{port}")

    # auto‑open http://<host>:<port>/docs three seconds after launch
    def _open_docs():
        docs_host = "127.0.0.1" if host in {"0.0.0.0", "localhost"} else host
        docs_url = f"http://{docs_host}:{port}/docs"
        print(f"\nOpening Swagger UI at {docs_url} …")
        try:
            import webbrowser

            webbrowser.open_new_tab(docs_url)
        except Exception as exc:
            print(f"(Could not launch browser automatically: {exc})")

    timer = threading.Timer(3.0, _open_docs)
    timer.daemon = True
    timer.start()

    uvicorn.run(
        "backend_gateway.app:app",
        host=host,
        port=port,
        reload=hot_reload,
        log_level="info",
    )


def start_ios(backend_url: str, ios_port: int, project_root: Path) -> subprocess.Popen:
    ios_dir = project_root / "ios-app"
    if not ios_dir.exists():
        raise FileNotFoundError("ios-app directory not found")

    env = os.environ.copy()
    env["EXPO_PUBLIC_API_BASE_URL"] = backend_url

    print(f"Starting Expo/iOS on port {ios_port} (backend → {backend_url})")
    return subprocess.Popen(["npm", "start", "--", "--port", str(ios_port)], cwd=ios_dir, env=env)


# ──────────────────────────────────────────────────────────────────────────────
# 7.  Main
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print("🚀 PrepSense Unified App Launcher\n" + "═" * 50)

    # Must be in a venv
    if sys.prefix == sys.base_prefix:
        print("❌ Not running inside a virtual environment.  Activate it first:")
        print("   source venv/bin/activate && python3 run_app.py")
        sys.exit(1)

    # Load .env **before** evaluating env vars
    load_dotenv()

    args = parse_arguments()

    host = args.host or os.getenv("HOST", DEFAULT_HOST)
    port = args.port or int(os.getenv("PORT", DEFAULT_BACKEND_PORT))
    ios_port = args.ios_port or int(os.getenv("IOS_PORT", DEFAULT_IOS_PORT))

    # Determine mode
    if args.backend and args.ios:
        mode = "both"
    elif args.backend:
        mode = "backend"
    elif args.ios:
        mode = "ios"
    else:
        mode = os.getenv("LAUNCH_MODE", "both")  # default

    # Expand IP for local‑only binds
    host_ip = get_local_ip() if host in {"0.0.0.0", "127.0.0.1", "localhost"} else host
    backend_url = (
        "https://my-api-xyz.a.run.app/api/v1"
        if args.gcp or os.getenv("USE_GCP_BACKEND", "false").lower() == "true"
        else f"http://{host_ip}:{port}/api/v1"
    )

    print(f"Mode: {mode}")
    if mode in {"both", "backend"}:
        print(f"  Backend → {host}:{port}")
    if mode in {"both", "ios"}:
        print(f"  iOS     → http://localhost:{ios_port} (calls {backend_url})")
    print()

    # Google credentials logic + IAM toggle
    project_root = Path(__file__).resolve().parent
    credentials_json = project_root / "config" / "adsp-34002-on02-prep-sense-ef1111b0833b.json"
    using_iam = os.getenv("POSTGRES_USE_IAM", "").lower() == "true"
    if using_iam:
        # Must use ADC, not service‑account file
        os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
        print("Using Application Default Credentials (POSTGRES_USE_IAM=true)")
    else:
        current_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not current_creds or not Path(current_creds).exists():
            if credentials_json.exists():
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_json)
                print(f"Set GOOGLE_APPLICATION_CREDENTIALS → {credentials_json}")
            else:
                print("⚠️  Service‑account JSON not found – running unauthenticated")

    pm = ProcessManager()
    pm.register()

    # Clean ports first
    print("🧹 Cleaning pre‑existing processes…")
    if mode in {"both", "backend"} and kill_processes_on_port(port, host):
        print(f"  cleared backend port {port}")
    if mode in {"both", "ios"}:
        for p in [ios_port, 19000, 19001, 19002, 19006, 8081]:
            if kill_processes_on_port(p):
                print(f"  cleared port {p}")

    if mode in {"both", "backend"} and not check_port_available(host, port):
        print(f"❌ Backend port {port} still busy – aborting.")
        sys.exit(1)

    try:
        if mode == "backend":
            start_backend(host, port)
        elif mode == "ios":
            pm.ios = start_ios(backend_url, ios_port, project_root)
            pm.ios.wait()
        else:  # both
            pm.ios = start_ios(backend_url, ios_port, project_root)
            print("Waiting 3 s for Expo to initialise…")
            time.sleep(3)
            start_backend(host, port)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    finally:
        pm.cleanup()
        print("👋 Done – launcher stopped.")


if __name__ == "__main__":
    main()