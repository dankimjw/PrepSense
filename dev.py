#!/usr/bin/env python3
"""Development utility script for PrepSense backend - Python equivalent of package.json scripts."""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Optional
import concurrent.futures
import time

# Colors for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def run_command(cmd: List[str], description: str, check: bool = True, capture: bool = False) -> Optional[subprocess.CompletedProcess]:
    """Run a command with colored output."""
    print(f"{Colors.CYAN}🔧 {description}...{Colors.END}")
    print(f"{Colors.BLUE}   Command: {' '.join(cmd)}{Colors.END}")
    
    try:
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        else:
            result = subprocess.run(cmd, check=check)
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ {description} completed successfully{Colors.END}\n")
        else:
            print(f"{Colors.RED}❌ {description} failed with return code {result.returncode}{Colors.END}\n")
        
        return result
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ {description} failed: {e}{Colors.END}\n")
        if check:
            raise
        return e
    except FileNotFoundError:
        print(f"{Colors.RED}❌ Command not found: {cmd[0]}{Colors.END}")
        print(f"{Colors.YELLOW}💡 Make sure {cmd[0]} is installed and in your PATH{Colors.END}\n")
        if check:
            sys.exit(1)
        return None


def check_venv():
    """Check if we're in a virtual environment."""
    if not hasattr(sys, 'real_prefix') and sys.base_prefix == sys.prefix:
        print(f"{Colors.YELLOW}⚠️  Warning: Not in a virtual environment{Colors.END}")
        print(f"{Colors.YELLOW}   Run: source venv/bin/activate{Colors.END}\n")


def format_code():
    """Format code using Black and isort."""
    print(f"{Colors.BOLD}📝 FORMATTING CODE{Colors.END}")
    print("=" * 80)
    
    # Run isort first
    run_command(
        ["python", "-m", "isort", "backend_gateway/", "src/", "tests/", "scripts/"],
        "Sorting imports with isort"
    )
    
    # Then run Black
    run_command(
        ["python", "-m", "black", "backend_gateway/", "src/", "tests/", "scripts/"],
        "Formatting code with Black"
    )


def lint_code():
    """Lint code using Ruff and Flake8."""
    print(f"{Colors.BOLD}🔍 LINTING CODE{Colors.END}")
    print("=" * 80)
    
    # Run Ruff (fast linter)
    run_command(
        ["python", "-m", "ruff", "check", "backend_gateway/", "src/", "tests/", "--fix"],
        "Linting with Ruff (auto-fixing)",
        check=False
    )
    
    # Run Flake8 for additional checks
    run_command(
        ["python", "-m", "flake8", "backend_gateway/", "src/", "tests/"],
        "Linting with Flake8",
        check=False
    )


def type_check():
    """Run type checking with mypy."""
    print(f"{Colors.BOLD}🔍 TYPE CHECKING{Colors.END}")
    print("=" * 80)
    
    run_command(
        ["python", "-m", "mypy", "backend_gateway/", "src/"],
        "Type checking with mypy",
        check=False
    )


def run_tests(test_type: str = "all", verbose: bool = False):
    """Run tests with pytest."""
    print(f"{Colors.BOLD}🧪 RUNNING TESTS{Colors.END}")
    print("=" * 80)
    
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration": 
        cmd.extend(["-m", "integration"])
    elif test_type == "api":
        cmd.extend(["-m", "api"])
    elif test_type == "crewai":
        cmd.extend(["-m", "crewai"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    
    # Add coverage if running all tests
    if test_type == "all":
        cmd.extend(["--cov=backend_gateway", "--cov-report=term-missing", "--cov-report=html"])
    
    run_command(cmd, f"Running {test_type} tests", check=False)


def quality_check():
    """Run all quality checks in parallel where possible."""
    print(f"{Colors.BOLD}🎯 COMPREHENSIVE QUALITY CHECK{Colors.END}")
    print("=" * 80)
    
    start_time = time.time()
    
    # Step 1: Format code first (sequential)
    format_code()
    
    # Step 2: Run checks in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(lint_code): "Linting",
            executor.submit(type_check): "Type checking",
            executor.submit(run_tests, "fast"): "Fast tests"
        }
        
        for future in concurrent.futures.as_completed(futures):
            task_name = futures[future]
            try:
                future.result()
                print(f"{Colors.GREEN}✅ {task_name} completed{Colors.END}")
            except Exception as e:
                print(f"{Colors.RED}❌ {task_name} failed: {e}{Colors.END}")
    
    elapsed = time.time() - start_time
    print(f"\n{Colors.BOLD}🏁 Quality check completed in {elapsed:.1f}s{Colors.END}")


def install_deps():
    """Install development dependencies."""
    print(f"{Colors.BOLD}📦 INSTALLING DEPENDENCIES{Colors.END}")
    print("=" * 80)
    
    run_command(
        ["pip", "install", "-r", "requirements.txt"],
        "Installing requirements"
    )


def clean():
    """Clean up generated files."""
    print(f"{Colors.BOLD}🧹 CLEANING UP{Colors.END}")
    print("=" * 80)
    
    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo", 
        "**/.mypy_cache",
        "**/.ruff_cache",
        "**/.pytest_cache",
        "**/htmlcov",
        "**/.coverage",
        "**/*.egg-info"
    ]
    
    for pattern in patterns:
        import glob
        files = glob.glob(pattern, recursive=True)
        for file in files:
            path = Path(file)
            if path.is_file():
                path.unlink()
                print(f"Removed file: {file}")
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)
                print(f"Removed directory: {file}")


def start_server(port: int = 8001, reload: bool = True, mock: bool = False):
    """Start the FastAPI development server."""
    print(f"{Colors.BOLD}🚀 STARTING DEVELOPMENT SERVER{Colors.END}")
    print("=" * 80)
    
    env = os.environ.copy()
    if mock:
        env["USE_MOCK_DATA"] = "true"
        print(f"{Colors.YELLOW}🎭 Mock data enabled{Colors.END}")
    
    cmd = [
        "python", "-m", "uvicorn", 
        "backend_gateway.main:app",
        "--host", "0.0.0.0",
        "--port", str(port)
    ]
    
    if reload:
        cmd.extend(["--reload", "--reload-dir", "backend_gateway", "--reload-dir", "src"])
    
    print(f"{Colors.CYAN}🌐 Server will be available at: http://localhost:{port}{Colors.END}")
    print(f"{Colors.CYAN}📚 API docs: http://localhost:{port}/docs{Colors.END}")
    
    subprocess.run(cmd, env=env)


def main():
    """Main CLI entry point."""
    check_venv()
    
    parser = argparse.ArgumentParser(
        description="PrepSense Backend Development Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Colors.BOLD}Available Commands:{Colors.END}
  format        Format code with Black and isort
  lint          Lint code with Ruff and Flake8
  typecheck     Run type checking with mypy
  test          Run tests with pytest
  quality       Run comprehensive quality checks (format + lint + typecheck + test)
  install       Install development dependencies
  clean         Clean up generated files
  serve         Start development server
  
{Colors.BOLD}Examples:{Colors.END}
  python dev.py format           # Format all code
  python dev.py test --type=unit # Run unit tests only
  python dev.py serve --port=8002 --mock  # Start server on port 8002 with mock data
  python dev.py quality          # Run all quality checks
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Format command
    subparsers.add_parser("format", help="Format code with Black and isort")
    
    # Lint command
    subparsers.add_parser("lint", help="Lint code with Ruff and Flake8")
    
    # Type check command
    subparsers.add_parser("typecheck", help="Run type checking with mypy")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests with pytest")
    test_parser.add_argument("--type", choices=["all", "unit", "integration", "api", "crewai", "fast"], 
                           default="all", help="Type of tests to run")
    test_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Quality command
    subparsers.add_parser("quality", help="Run comprehensive quality checks")
    
    # Install command
    subparsers.add_parser("install", help="Install development dependencies")
    
    # Clean command
    subparsers.add_parser("clean", help="Clean up generated files")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start development server")
    serve_parser.add_argument("--port", type=int, default=8001, help="Port to serve on")
    serve_parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    serve_parser.add_argument("--mock", action="store_true", help="Enable mock data")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "format":
            format_code()
        elif args.command == "lint":
            lint_code()
        elif args.command == "typecheck":
            type_check()
        elif args.command == "test":
            run_tests(args.type, args.verbose)
        elif args.command == "quality":
            quality_check()
        elif args.command == "install":
            install_deps()
        elif args.command == "clean":
            clean()
        elif args.command == "serve":
            start_server(args.port, not args.no_reload, args.mock)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Operation cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()