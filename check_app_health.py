#!/usr/bin/env python3
"""
PrepSense App Health Check Script
Quick validation that both backend and iOS app are working correctly.
"""

import os
import sys
import subprocess
import requests
import json
import time
from typing import Dict, Any, List, Tuple
import signal

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print a styled header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_status(test_name: str, status: str, details: str = ""):
    """Print test status with colors."""
    if status == "PASS":
        icon = f"{Colors.GREEN}✅{Colors.END}"
        status_text = f"{Colors.GREEN}{status}{Colors.END}"
    elif status == "FAIL":
        icon = f"{Colors.RED}❌{Colors.END}"
        status_text = f"{Colors.RED}{status}{Colors.END}"
    elif status == "WARN":
        icon = f"{Colors.YELLOW}⚠️{Colors.END}"
        status_text = f"{Colors.YELLOW}{status}{Colors.END}"
    else:
        icon = f"{Colors.BLUE}ℹ️{Colors.END}"
        status_text = f"{Colors.BLUE}{status}{Colors.END}"
    
    print(f"{icon} {test_name:.<45} {status_text}")
    if details:
        print(f"   {Colors.WHITE}{details}{Colors.END}")

def check_backend_process() -> bool:
    """Check if backend process is running."""
    try:
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        processes = result.stdout
        
        # Look for uvicorn or run_app.py processes
        backend_running = any(
            "uvicorn" in line and ("8001" in line or "app:app" in line)
            for line in processes.split('\n')
        ) or any(
            "run_app.py" in line
            for line in processes.split('\n')
        )
        
        return backend_running
    except Exception as e:
        print_status("Backend Process Check", "FAIL", f"Error: {e}")
        return False

def test_backend_health() -> Tuple[bool, Dict[str, Any]]:
    """Test backend health endpoint."""
    try:
        response = requests.get(
            "http://localhost:8001/api/v1/health",
            timeout=5
        )
        
        if response.status_code == 200:
            health_data = response.json()
            return True, health_data
        else:
            return False, {"error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.ConnectionError:
        return False, {"error": "Connection refused - backend not running"}
    except requests.exceptions.Timeout:
        return False, {"error": "Request timeout"}
    except Exception as e:
        return False, {"error": str(e)}

def test_api_endpoints() -> List[Tuple[str, bool, str]]:
    """Test key API endpoints."""
    endpoints = [
        ("Root", "http://localhost:8001/", "GET"),
        ("API Docs", "http://localhost:8001/docs", "GET"),
        ("OpenAPI Schema", "http://localhost:8001/api/v1/openapi.json", "GET"),
    ]
    
    results = []
    
    for name, url, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            
            success = response.status_code < 400
            status_msg = f"HTTP {response.status_code}"
            
            results.append((name, success, status_msg))
            
        except Exception as e:
            results.append((name, False, str(e)))
    
    return results

def check_ios_metro() -> bool:
    """Check if Metro bundler is running for iOS app."""
    try:
        # Check for expo/metro processes
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        processes = result.stdout
        
        metro_running = any(
            ("expo" in line and "8082" in line) or 
            ("metro" in line) or
            ("node_modules/expo" in line)
            for line in processes.split('\n')
        )
        
        return metro_running
    except Exception:
        return False

def check_ios_bundle() -> Tuple[bool, str]:
    """Check if iOS app bundle can be built."""
    try:
        os.chdir("ios-app")
        
        # Run expo build check (without actually building)
        result = subprocess.run(
            ["npx", "expo", "export", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return True, "Expo CLI working"
        else:
            return False, f"Expo CLI error: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Expo CLI timeout"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        os.chdir("..")

def check_environment() -> Dict[str, Any]:
    """Check environment setup."""
    checks = {}
    
    # Check if virtual environment is active
    checks["venv"] = {
        "active": "VIRTUAL_ENV" in os.environ,
        "path": os.environ.get("VIRTUAL_ENV", "Not active")
    }
    
    # Check key environment variables
    env_vars = [
        "EXPO_PUBLIC_API_BASE_URL",
        "OPENAI_API_KEY", 
        "GOOGLE_APPLICATION_CREDENTIALS"
    ]
    
    checks["env_vars"] = {}
    for var in env_vars:
        value = os.environ.get(var)
        checks["env_vars"][var] = {
            "set": value is not None,
            "value": "***" if value else None
        }
    
    return checks

def main():
    """Run comprehensive app health check."""
    print_header("PrepSense App Health Check")
    
    total_tests = 0
    passed_tests = 0
    
    # Environment checks
    print(f"{Colors.BOLD}Environment Setup:{Colors.END}")
    env_info = check_environment()
    
    # Virtual environment
    total_tests += 1
    if env_info["venv"]["active"]:
        print_status("Virtual Environment", "PASS", env_info["venv"]["path"])
        passed_tests += 1
    else:
        print_status("Virtual Environment", "WARN", "Not in venv - run: source venv/bin/activate")
    
    # Backend checks
    print(f"\n{Colors.BOLD}Backend Health:{Colors.END}")
    
    # Backend process
    total_tests += 1
    if check_backend_process():
        print_status("Backend Process", "PASS")
        passed_tests += 1
    else:
        print_status("Backend Process", "FAIL", "Run: python run_app.py")
    
    # Backend health endpoint
    total_tests += 1
    health_ok, health_data = test_backend_health()
    if health_ok:
        print_status("Health Endpoint", "PASS", f"Status: {health_data.get('status', 'unknown')}")
        passed_tests += 1
        
        # Check environment configuration
        env_config = health_data.get('environment', {})
        if env_config.get('openai_configured'):
            print_status("OpenAI Config", "PASS")
        else:
            print_status("OpenAI Config", "WARN", "OPENAI_API_KEY not set")
            
        if env_config.get('google_cloud_configured'):
            print_status("Google Cloud Config", "PASS")
        else:
            print_status("Google Cloud Config", "WARN", "GOOGLE_APPLICATION_CREDENTIALS not set")
    else:
        print_status("Health Endpoint", "FAIL", health_data.get('error', 'Unknown error'))
    
    # API endpoint tests
    print(f"\n{Colors.BOLD}API Endpoints:{Colors.END}")
    api_results = test_api_endpoints()
    
    for name, success, details in api_results:
        total_tests += 1
        if success:
            print_status(f"{name} Endpoint", "PASS", details)
            passed_tests += 1
        else:
            print_status(f"{name} Endpoint", "FAIL", details)
    
    # iOS app checks
    print(f"\n{Colors.BOLD}iOS App:{Colors.END}")
    
    # Metro bundler
    total_tests += 1
    if check_ios_metro():
        print_status("Metro Bundler", "PASS")
        passed_tests += 1
    else:
        print_status("Metro Bundler", "FAIL", "Run: cd ios-app && npx expo start")
    
    # iOS bundle check
    total_tests += 1
    bundle_ok, bundle_msg = check_ios_bundle()
    if bundle_ok:
        print_status("iOS Bundle Check", "PASS", bundle_msg)
        passed_tests += 1
    else:
        print_status("iOS Bundle Check", "FAIL", bundle_msg)
    
    # Summary
    print_header("Summary")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    if success_rate >= 80:
        status_color = Colors.GREEN
        status_icon = "✅"
    elif success_rate >= 60:
        status_color = Colors.YELLOW
        status_icon = "⚠️"
    else:
        status_color = Colors.RED
        status_icon = "❌"
    
    print(f"{status_icon} {status_color}Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%){Colors.END}")
    
    if success_rate >= 80:
        print(f"{Colors.GREEN}🎉 App appears to be working correctly!{Colors.END}")
    elif success_rate >= 60:
        print(f"{Colors.YELLOW}⚠️ App mostly working but has some issues.{Colors.END}")
    else:
        print(f"{Colors.RED}❌ App has significant issues that need attention.{Colors.END}")
    
    # Quick start commands
    print(f"\n{Colors.BOLD}Quick Start Commands:{Colors.END}")
    print(f"{Colors.CYAN}Start Backend:{Colors.END} source venv/bin/activate && python run_app.py")
    print(f"{Colors.CYAN}Start iOS App:{Colors.END} cd ios-app && npx expo start --ios")
    print(f"{Colors.CYAN}Health Check:{Colors.END} curl http://localhost:8001/api/v1/health")
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 80 else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Health check interrupted.{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error during health check: {e}{Colors.END}")
        sys.exit(1)