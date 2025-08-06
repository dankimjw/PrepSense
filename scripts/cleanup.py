import os
import platform
import subprocess


def kill_processes_on_ports(ports):
    """Kills processes running on a list of ports."""
    for port in ports:
        try:
            if platform.system() == "Windows":
                command = f"netstat -ano | findstr :{port}"
                output = subprocess.check_output(command, shell=True, text=True)
                for line in output.strip().split("\n"):
                    if "LISTENING" in line:
                        pid = line.rstrip().split()[-1]
                        subprocess.run(["taskkill", "/F", "/PID", pid], check=True)
                        print(f"Killed process {pid} on port {port}")
            else:
                command = f"lsof -t -i:{port}"
                output = subprocess.check_output(command, shell=True, text=True)
                for pid in output.strip().split("\n"):
                    subprocess.run(["kill", "-9", pid], check=True)
                    print(f"Killed process {pid} on port {port}")
        except subprocess.CalledProcessError:
            print(f"No process found on port {port}")


def kill_processes_by_name(names):
    """Kills processes by their name."""
    for name in names:
        try:
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", f"{name}*"], check=True)
            else:
                subprocess.run(["pkill", "-f", name], check=True)
            print(f"Killed processes matching name: {name}")
        except subprocess.CalledProcessError:
            print(f"No processes found matching name: {name}")


if __name__ == "__main__":
    print("--- Starting PrepSense Cleanup ---")
    ports_to_kill = [8001, 8082, 8083, 19000, 19001, 19002, 19006]
    processes_to_kill = ["expo", "metro", "start.py", "run_app.py", "uvicorn", "fastapi"]

    print("\n--- Killing processes by port ---")
    kill_processes_on_ports(ports_to_kill)

    print("\n--- Killing processes by name ---")
    kill_processes_by_name(processes_to_kill)

    print("\n--- Cleanup Complete ---")
