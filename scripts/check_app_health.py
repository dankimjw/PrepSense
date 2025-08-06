#!/usr/bin/env python3
"""
Comprehensive health check for PrepSense application
Tests actual functionality, not just service connectivity
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil
import requests


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class HealthChecker:
    def __init__(self):
        self.results = []
        self.errors = []
        self.warnings = []
        self.backend_base_url = "http://localhost:8001"
        self.metro_url = "http://localhost:8082"

    def log(self, message: str, status: str = "info"):
        """Log message with color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if status == "success":
            print(f"{Colors.GREEN}✅ [{timestamp}] {message}{Colors.RESET}")
        elif status == "error":
            print(f"{Colors.RED}❌ [{timestamp}] {message}{Colors.RESET}")
        elif status == "warning":
            print(f"{Colors.YELLOW}⚠️  [{timestamp}] {message}{Colors.RESET}")
        else:
            print(f"{Colors.BLUE}ℹ️  [{timestamp}] {message}{Colors.RESET}")

    def check_port(self, port: int, service_name: str) -> bool:
        """Check if a port is open and listening"""
        try:
            # Use lsof command like quick_check.sh does
            result = subprocess.run(
                ["lsof", "-Pi", f":{port}", "-sTCP:LISTEN", "-t"], capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                self.log(f"{service_name} is listening on port {port}", "success")
                return True
            else:
                self.log(f"{service_name} is NOT listening on port {port}", "error")
                return False
        except Exception as e:
            # Fallback to trying to connect
            import socket

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex(("localhost", port))
                    if result == 0:
                        self.log(f"{service_name} is listening on port {port}", "success")
                        return True
                    else:
                        self.log(f"{service_name} is NOT listening on port {port}", "error")
                        return False
            except Exception:
                self.log(f"{service_name} port check failed", "error")
                return False

    def check_backend_health(self) -> Dict:
        """Check backend API health and functionality"""
        results = {
            "basic_connectivity": False,
            "api_endpoints": {},
            "database_connection": False,
            "external_apis": {},
        }

        # Basic health check
        try:
            response = requests.get(f"{self.backend_base_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                results["basic_connectivity"] = True
                self.log("Backend health endpoint responding", "success")
                health_data = response.json()
                if health_data.get("database", {}).get("connected"):
                    results["database_connection"] = True
                    self.log("Database connection verified", "success")
                else:
                    self.log("Database connection failed", "error")
            else:
                self.log(f"Backend health check failed: {response.status_code}", "error")
        except Exception as e:
            self.log(f"Backend not accessible: {str(e)}", "error")
            return results

        # Test critical API endpoints
        test_endpoints = [
            ("/api/v1/units", "GET", None, "Units endpoint"),
            ("/api/v1/demo/recipes", "GET", None, "Demo recipes"),
            ("/api/v1/stats/comprehensive?timeframe=week", "GET", None, "Stats endpoint"),
        ]

        for endpoint, method, data, description in test_endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.backend_base_url}{endpoint}", timeout=5)
                else:
                    response = requests.post(
                        f"{self.backend_base_url}{endpoint}", json=data, timeout=5
                    )

                if response.status_code in [200, 201]:
                    results["api_endpoints"][endpoint] = True
                    self.log(f"{description} working", "success")

                    # Validate response structure
                    try:
                        json_data = response.json()
                        if not json_data:
                            self.log(f"{description} returned empty data", "warning")
                    except:
                        self.log(f"{description} returned invalid JSON", "warning")
                else:
                    results["api_endpoints"][endpoint] = False
                    self.log(f"{description} failed: {response.status_code}", "error")
                    if response.text:
                        self.errors.append(f"{endpoint}: {response.text[:100]}")
            except Exception as e:
                results["api_endpoints"][endpoint] = False
                self.log(f"{description} error: {str(e)}", "error")

        # Check external API connectivity (if configured)
        if os.getenv("OPENAI_API_KEY"):
            results["external_apis"]["openai"] = True
            self.log("OpenAI API key configured", "success")
        else:
            self.log("OpenAI API key not configured", "warning")

        if os.getenv("SPOONACULAR_API_KEY"):
            results["external_apis"]["spoonacular"] = True
            self.log("Spoonacular API key configured", "success")
        else:
            self.log("Spoonacular API key not configured", "warning")

        return results

    def check_frontend_health(self) -> Dict:
        """Check frontend/React Native health"""
        results = {"metro_bundler": False, "bundle_valid": False, "simulator_running": False}

        # Check Metro bundler
        try:
            response = requests.get(self.metro_url, timeout=5)
            if response.status_code == 200:
                results["metro_bundler"] = True
                self.log("Metro bundler is running", "success")
            else:
                self.log("Metro bundler not responding properly", "error")
        except:
            self.log("Metro bundler not accessible", "error")

        # Check if iOS simulator is running
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "booted"], capture_output=True, text=True
            )
            if result.stdout.strip():
                results["simulator_running"] = True
                self.log("iOS Simulator is running", "success")
            else:
                self.log("iOS Simulator not running", "warning")
        except:
            self.log("Cannot check iOS Simulator status", "warning")

        # Check if bundle can be built
        bundle_path = Path("ios-app/ios/build/Build/Products/Debug-iphonesimulator/PrepSense.app")
        if bundle_path.exists():
            results["bundle_valid"] = True
            self.log("iOS app bundle found", "success")
        else:
            self.log("iOS app bundle not found - may need to build", "warning")

        return results

    def check_database_operations(self) -> Dict:
        """Test actual database operations through the API"""
        results = {"read_operations": False, "write_operations": False, "complex_queries": False}

        # Test read operation
        try:
            response = requests.get(f"{self.backend_base_url}/api/v1/ingredients", timeout=5)
            if response.status_code == 200:
                results["read_operations"] = True
                self.log("Database read operations working", "success")
            else:
                self.log(f"Database read failed: {response.status_code}", "error")
        except Exception as e:
            self.log(f"Database read error: {str(e)}", "error")

        # Test complex query (stats with aggregation)
        try:
            response = requests.get(
                f"{self.backend_base_url}/api/v1/stats/comprehensive?timeframe=week", timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if "recipes_completed" in data:
                    results["complex_queries"] = True
                    self.log("Complex database queries working", "success")
            else:
                self.log("Complex queries not working properly", "error")
        except:
            self.log("Complex query error", "error")

        return results

    def check_error_handling(self) -> Dict:
        """Test error handling and edge cases"""
        results = {
            "handles_404": False,
            "handles_invalid_data": False,
            "handles_auth_errors": False,
        }

        # Test 404 handling
        try:
            response = requests.get(f"{self.backend_base_url}/api/v1/nonexistent", timeout=5)
            if response.status_code == 404:
                results["handles_404"] = True
                self.log("404 error handling working", "success")
        except:
            pass

        # Test invalid data handling
        try:
            response = requests.post(
                f"{self.backend_base_url}/api/v1/recipes/search",
                json={"invalid": "data"},
                timeout=5,
            )
            if response.status_code in [400, 422]:
                results["handles_invalid_data"] = True
                self.log("Invalid data handling working", "success")
        except:
            pass

        return results

    def run_full_check(self) -> Tuple[bool, Dict]:
        """Run comprehensive health check"""
        print(f"\n{Colors.BOLD}🏥 PrepSense Comprehensive Health Check{Colors.RESET}")
        print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

        all_results = {}

        # Check services
        self.log("Checking service connectivity...", "info")
        backend_running = self.check_port(8001, "Backend API")

        # Check if Metro should be running (look for metro/expo/npm processes)
        try:
            # Use ps command to avoid psutil permission issues
            result = subprocess.run(
                ["pgrep", "-f", "metro|expo|npm.*start"], capture_output=True, text=True
            )
            metro_expected = bool(result.stdout.strip())
        except Exception:
            # Fallback to checking if port 8082 is open (someone is trying to use it)
            try:
                import socket

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    metro_expected = sock.connect_ex(("localhost", 8082)) == 0
            except Exception:
                metro_expected = False

        if metro_expected:
            metro_running = self.check_port(8082, "Metro Bundler")
        else:
            metro_running = False
            self.log("Metro Bundler not expected - backend-only mode", "info")

        if not backend_running:
            self.log("Backend not running - skipping API tests", "error")
            self.errors.append("Backend service not running")
        else:
            # Backend functionality
            self.log("\nChecking backend functionality...", "info")
            all_results["backend"] = self.check_backend_health()

            # Database operations
            self.log("\nChecking database operations...", "info")
            all_results["database"] = self.check_database_operations()

            # Error handling
            self.log("\nChecking error handling...", "info")
            all_results["error_handling"] = self.check_error_handling()

        # Frontend checks
        if metro_expected and metro_running:
            self.log("\nChecking frontend health...", "info")
            all_results["frontend"] = self.check_frontend_health()
        elif metro_expected and not metro_running:
            self.log("\nFrontend expected but Metro not running", "error")
        else:
            self.log("\nSkipping frontend checks - backend-only mode", "info")

        # Summary
        print(f"\n{Colors.BOLD}📊 Health Check Summary{Colors.RESET}")
        print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")

        total_checks = 0
        passed_checks = 0

        def count_checks(obj):
            nonlocal total_checks, passed_checks
            if isinstance(obj, dict):
                for v in obj.values():
                    if isinstance(v, bool):
                        total_checks += 1
                        if v:
                            passed_checks += 1
                    else:
                        count_checks(v)

        count_checks(all_results)

        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0

        if success_rate >= 90:
            status_color = Colors.GREEN
            status_emoji = "✅"
        elif success_rate >= 70:
            status_color = Colors.YELLOW
            status_emoji = "⚠️"
        else:
            status_color = Colors.RED
            status_emoji = "❌"

        print(
            f"\n{status_color}{status_emoji} Overall Health: {success_rate:.1f}% ({passed_checks}/{total_checks} checks passed){Colors.RESET}"
        )

        if self.errors:
            print(f"\n{Colors.RED}🚨 Errors Found:{Colors.RESET}")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"  • {error}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}⚠️  Warnings:{Colors.RESET}")
            for warning in self.warnings[:5]:
                print(f"  • {warning}")

        # Action items
        print(f"\n{Colors.BOLD}🔧 Recommended Actions:{Colors.RESET}")
        if not backend_running:
            print("  1. Start backend: source venv/bin/activate && python run_app.py --backend")
            print("  2. Or start both: source venv/bin/activate && python run_app.py")
        if metro_expected and not metro_running:
            print("  3. Start iOS app: python run_app.py --ios (or cd ios-app && npm start)")
        if success_rate < 90:
            print("  3. Review error logs and fix failing checks")
            print("  4. Run unit tests to identify specific issues")

        # Save detailed results
        with open(".health_check_results.json", "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "success_rate": success_rate,
                    "results": all_results,
                    "errors": self.errors,
                    "warnings": self.warnings,
                },
                f,
                indent=2,
            )

        print(f"\n{Colors.BLUE}Detailed results saved to .health_check_results.json{Colors.RESET}")

        return success_rate >= 70, all_results


if __name__ == "__main__":
    checker = HealthChecker()
    success, results = checker.run_full_check()

    # Exit with appropriate code for CI/CD
    sys.exit(0 if success else 1)
