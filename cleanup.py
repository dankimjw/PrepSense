#!/usr/bin/env python3
"""
Cleanup script for PrepSense - kills all running backend and iOS processes
"""

import subprocess
import signal
import os
import sys
import time

def kill_processes_on_port(port):
    """Kill any processes running on the specified port"""
    try:
        # Find processes using the port
        result = subprocess.run(['lsof', '-t', f'-i:{port}'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    pid = int(pid.strip())
                    print(f"Killing process {pid} on port {port}")
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.5)
                    # Force kill if still running
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # Process already dead
                except (ValueError, ProcessLookupError):
                    pass
        else:
            print(f"No processes found on port {port}")
    except Exception as e:
        print(f"Error killing processes on port {port}: {e}")

def kill_processes_by_name(name_pattern):
    """Kill processes by name pattern"""
    try:
        # Find processes by name
        result = subprocess.run(['pgrep', '-f', name_pattern], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    pid = int(pid.strip())
                    print(f"Killing process {pid} matching '{name_pattern}'")
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.5)
                    # Force kill if still running
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # Process already dead
                except (ValueError, ProcessLookupError):
                    pass
        else:
            print(f"No processes found matching '{name_pattern}'")
    except Exception as e:
        print(f"Error killing processes matching '{name_pattern}': {e}")

def main():
    """Main cleanup function"""
    print("🧹 PrepSense Cleanup Script")
    print("=" * 40)
    
    # Kill processes by port
    ports_to_clean = [8001, 8082, 8083, 19000, 19001, 19002, 19006]
    
    for port in ports_to_clean:
        print(f"\n🔍 Checking port {port}...")
        kill_processes_on_port(port)
    
    # Kill processes by name pattern
    print(f"\n🔍 Checking for expo/metro processes...")
    kill_processes_by_name("expo start")
    kill_processes_by_name("metro")
    
    print(f"\n🔍 Checking for python backend processes...")
    kill_processes_by_name("start.py")
    kill_processes_by_name("run_app.py")
    kill_processes_by_name("uvicorn")
    
    print(f"\n🔍 Checking for fastapi processes...")
    kill_processes_by_name("fastapi")
    
    print("\n✅ Cleanup complete!")
    print("All PrepSense processes should now be stopped.")
    
    # Verify cleanup
    print("\n🔍 Verification - checking remaining processes...")
    remaining_processes = []
    
    for port in [8001, 8082, 8083]:
        result = subprocess.run(['lsof', '-t', f'-i:{port}'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            remaining_processes.append(f"Port {port}: {result.stdout.strip()}")
    
    if remaining_processes:
        print("⚠️  Some processes may still be running:")
        for proc in remaining_processes:
            print(f"   {proc}")
    else:
        print("✅ All target ports are clear!")

if __name__ == "__main__":
    main()
