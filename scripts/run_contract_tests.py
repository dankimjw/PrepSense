#!/usr/bin/env python3
"""
Contract Testing Automation Script for PrepSense API

Coordinates and runs comprehensive contract testing including:
- OpenAPI schema validation with Spectral
- API contract testing with Schemathesis
- Schema drift detection
- Performance SLA validation
- Error format compliance testing

Usage:
    python run_contract_tests.py --full          # Run all contract tests
    python run_contract_tests.py --quick         # Run quick validation only
    python run_contract_tests.py --ci            # CI mode with appropriate exit codes
    python run_contract_tests.py --baseline-mode # Update baseline and exit
"""

import os
import sys
import subprocess
import argparse
import json
import time
import asyncio
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
SPECTRAL_RULES_FILE = PROJECT_ROOT / ".spectral.yml"
RESULTS_DIR = PROJECT_ROOT / "test-results" / "contract"
TIMEOUT_SECONDS = int(os.getenv("CONTRACT_TEST_TIMEOUT", "300"))  # 5 minutes

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

class ContractTestRunner:
    """Orchestrates contract testing workflow."""
    
    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "api_url": api_url,
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "skipped_tests": 0
            },
            "performance": {
                "total_duration": 0,
                "test_durations": {}
            },
            "violations": [],
            "recommendations": []
        }
        
    def wait_for_api(self, timeout: int = 30) -> bool:
        """Wait for API to be available."""
        logger.info(f"Waiting for API at {self.api_url}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.api_url}/api/v1/health", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ API is available")
                    return True
            except requests.RequestException:
                pass
            time.sleep(1)
        
        logger.error(f"❌ API not available after {timeout}s")
        return False
    
    def run_spectral_validation(self) -> Dict[str, Any]:
        """Run OpenAPI schema validation with Spectral."""
        logger.info("🔍 Running Spectral API validation...")
        start_time = time.time()
        
        test_result = {
            "test_name": "spectral_validation",
            "status": "skipped",
            "duration": 0,
            "violations": [],
            "details": {}
        }
        
        try:
            # Check if Spectral is available
            spectral_check = subprocess.run(
                ["npx", "spectral", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if spectral_check.returncode != 0:
                logger.warning("Spectral not available, skipping validation")
                test_result["status"] = "skipped"
                test_result["details"]["reason"] = "Spectral not installed"
                return test_result
            
            # Run Spectral validation
            spectral_cmd = [
                "npx", "spectral", "lint",
                f"{self.api_url}/openapi.json",
                "--ruleset", str(SPECTRAL_RULES_FILE),
                "--format", "json"
            ]
            
            result = subprocess.run(
                spectral_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            test_result["duration"] = time.time() - start_time
            
            if result.stdout:
                try:
                    violations = json.loads(result.stdout)
                    test_result["violations"] = violations
                    
                    # Categorize violations
                    error_count = sum(1 for v in violations if v.get("severity") == 0)
                    warning_count = sum(1 for v in violations if v.get("severity") == 1)
                    info_count = sum(1 for v in violations if v.get("severity") == 2)
                    
                    test_result["details"] = {
                        "total_violations": len(violations),
                        "errors": error_count,
                        "warnings": warning_count,
                        "info": info_count
                    }
                    
                    # Determine status
                    if error_count > 0:
                        test_result["status"] = "failed"
                        logger.error(f"❌ Spectral validation failed: {error_count} errors")
                    else:
                        test_result["status"] = "passed"
                        logger.info(f"✅ Spectral validation passed with {warning_count} warnings")
                
                except json.JSONDecodeError:
                    test_result["status"] = "failed"
                    test_result["details"]["error"] = "Failed to parse Spectral output"
                    logger.error("Failed to parse Spectral JSON output")
            else:
                # No output usually means no violations
                test_result["status"] = "passed"
                test_result["details"] = {"total_violations": 0}
                logger.info("✅ Spectral validation passed - no violations found")
        
        except subprocess.TimeoutExpired:
            test_result["status"] = "failed"
            test_result["details"]["error"] = "Spectral validation timed out"
            logger.error("❌ Spectral validation timed out")
        except Exception as e:
            test_result["status"] = "failed"
            test_result["details"]["error"] = str(e)
            logger.error(f"❌ Spectral validation error: {e}")
        
        return test_result
    
    def run_schemathesis_tests(self) -> Dict[str, Any]:
        """Run Schemathesis API contract tests."""
        logger.info("🧪 Running Schemathesis contract tests...")
        start_time = time.time()
        
        test_result = {
            "test_name": "schemathesis_contract",
            "status": "skipped",
            "duration": 0,
            "violations": [],
            "details": {}
        }
        
        try:
            # Check if Schemathesis is available
            schemathesis_check = subprocess.run(
                ["python", "-c", "import schemathesis; print(schemathesis.__version__)"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if schemathesis_check.returncode != 0:
                logger.warning("Schemathesis not available, skipping contract tests")
                test_result["status"] = "skipped"
                test_result["details"]["reason"] = "Schemathesis not installed"
                return test_result
            
            # Run contract tests using pytest
            contract_test_file = PROJECT_ROOT / "tests" / "contract" / "test_api_contract.py"
            
            pytest_cmd = [
                "python", "-m", "pytest",
                str(contract_test_file),
                "-v",
                "--tb=short",
                "--json-report",
                "--json-report-file=" + str(RESULTS_DIR / "contract_test_report.json"),
                f"--base-url={self.api_url}",
                "-m", "contract",
                "--maxfail=10"  # Stop after 10 failures
            ]
            
            # Set environment variables for tests
            env = os.environ.copy()
            env["API_BASE_URL"] = self.api_url
            env["PYTHONPATH"] = str(PROJECT_ROOT)
            
            result = subprocess.run(
                pytest_cmd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                env=env
            )
            
            test_result["duration"] = time.time() - start_time
            
            # Parse pytest results
            report_file = RESULTS_DIR / "contract_test_report.json"
            if report_file.exists():
                try:
                    with open(report_file, 'r') as f:
                        pytest_report = json.load(f)
                    
                    test_result["details"] = {
                        "total_tests": pytest_report["summary"]["total"],
                        "passed": pytest_report["summary"]["passed"],
                        "failed": pytest_report["summary"]["failed"],
                        "skipped": pytest_report["summary"]["skipped"],
                        "exit_code": result.returncode
                    }
                    
                    if result.returncode == 0:
                        test_result["status"] = "passed"
                        logger.info("✅ Contract tests passed")
                    else:
                        test_result["status"] = "failed"
                        logger.error("❌ Contract tests failed")
                
                except (json.JSONDecodeError, KeyError) as e:
                    test_result["status"] = "failed"
                    test_result["details"]["error"] = f"Failed to parse test results: {e}"
            else:
                # Fallback to exit code
                if result.returncode == 0:
                    test_result["status"] = "passed"
                    logger.info("✅ Contract tests completed successfully")
                else:
                    test_result["status"] = "failed"
                    test_result["details"]["stderr"] = result.stderr
                    logger.error("❌ Contract tests failed")
        
        except subprocess.TimeoutExpired:
            test_result["status"] = "failed"
            test_result["details"]["error"] = f"Contract tests timed out after {TIMEOUT_SECONDS}s"
            logger.error(f"❌ Contract tests timed out after {TIMEOUT_SECONDS}s")
        except Exception as e:
            test_result["status"] = "failed"
            test_result["details"]["error"] = str(e)
            logger.error(f"❌ Contract tests error: {e}")
        
        return test_result
    
    def run_schema_drift_detection(self, update_baseline: bool = False) -> Dict[str, Any]:
        """Run schema drift detection."""
        logger.info("🔄 Running schema drift detection...")
        start_time = time.time()
        
        test_result = {
            "test_name": "schema_drift",
            "status": "skipped",
            "duration": 0,
            "violations": [],
            "details": {}
        }
        
        try:
            # Import schema drift detector
            drift_script = SCRIPT_DIR / "schema_drift_detector.py"
            
            if not drift_script.exists():
                test_result["status"] = "skipped"
                test_result["details"]["reason"] = "Schema drift detector not found"
                logger.warning("Schema drift detector not found")
                return test_result
            
            # Run drift detection
            drift_cmd = [
                "python", str(drift_script),
                "--base-url", self.api_url,
                "--output", str(RESULTS_DIR / "schema_drift_report.json")
            ]
            
            if update_baseline:
                drift_cmd.append("--create-baseline")
            
            result = subprocess.run(
                drift_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            test_result["duration"] = time.time() - start_time
            
            # Check if report was generated
            drift_report_file = RESULTS_DIR / "schema_drift_report.json"
            
            if result.returncode == 0:
                test_result["status"] = "passed"
                
                if drift_report_file.exists():
                    try:
                        with open(drift_report_file, 'r') as f:
                            drift_data = json.load(f)
                        
                        test_result["details"] = {
                            "baseline_version": drift_data.get("baseline_version"),
                            "current_version": drift_data.get("api_version"),
                            "total_changes": drift_data.get("total_changes", 0),
                            "breaking_changes": drift_data.get("impact_analysis", {}).get("breaking_changes", 0),
                            "compatibility": drift_data.get("impact_analysis", {}).get("compatibility", "unknown")
                        }
                        
                        if test_result["details"]["breaking_changes"] > 0:
                            test_result["status"] = "failed"
                            logger.error("❌ Breaking schema changes detected")
                        else:
                            logger.info("✅ No breaking schema changes detected")
                    
                    except (json.JSONDecodeError, KeyError):
                        logger.warning("Could not parse drift report")
                
                if update_baseline:
                    logger.info("✅ Schema baseline updated")
            else:
                test_result["status"] = "failed"
                test_result["details"]["stderr"] = result.stderr
                logger.error("❌ Schema drift detection failed")
        
        except subprocess.TimeoutExpired:
            test_result["status"] = "failed"
            test_result["details"]["error"] = "Schema drift detection timed out"
            logger.error("❌ Schema drift detection timed out")
        except Exception as e:
            test_result["status"] = "failed"
            test_result["details"]["error"] = str(e)
            logger.error(f"❌ Schema drift detection error: {e}")
        
        return test_result
    
    def run_performance_validation(self) -> Dict[str, Any]:
        """Run basic performance validation."""
        logger.info("⚡ Running performance validation...")
        start_time = time.time()
        
        test_result = {
            "test_name": "performance_validation",
            "status": "passed",
            "duration": 0,
            "violations": [],
            "details": {}
        }
        
        try:
            # Test key endpoints for performance
            endpoints = [
                "/api/v1/health",
                "/openapi.json",
                "/docs",
                "/metrics"
            ]
            
            endpoint_results = {}
            total_violations = 0
            sla_threshold = 5.0  # 5 seconds SLA
            
            for endpoint in endpoints:
                endpoint_start = time.time()
                try:
                    response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
                    endpoint_duration = time.time() - endpoint_start
                    
                    endpoint_results[endpoint] = {
                        "status_code": response.status_code,
                        "response_time": round(endpoint_duration, 3),
                        "sla_compliant": endpoint_duration < sla_threshold
                    }
                    
                    if endpoint_duration >= sla_threshold:
                        total_violations += 1
                        test_result["violations"].append({
                            "type": "sla_violation",
                            "endpoint": endpoint,
                            "response_time": endpoint_duration,
                            "threshold": sla_threshold
                        })
                
                except requests.RequestException as e:
                    endpoint_results[endpoint] = {
                        "status_code": None,
                        "response_time": None,
                        "error": str(e),
                        "sla_compliant": False
                    }
                    total_violations += 1
            
            test_result["duration"] = time.time() - start_time
            test_result["details"] = {
                "endpoints_tested": len(endpoints),
                "sla_violations": total_violations,
                "sla_threshold_seconds": sla_threshold,
                "endpoint_results": endpoint_results
            }
            
            if total_violations > 0:
                test_result["status"] = "failed"
                logger.error(f"❌ Performance validation failed: {total_violations} SLA violations")
            else:
                logger.info("✅ Performance validation passed")
        
        except Exception as e:
            test_result["status"] = "failed"
            test_result["details"]["error"] = str(e)
            logger.error(f"❌ Performance validation error: {e}")
        
        return test_result
    
    def generate_summary_report(self) -> None:
        """Generate and save comprehensive test summary."""
        logger.info("📊 Generating summary report...")
        
        # Calculate summary statistics
        for test_name, test_result in self.results["tests"].items():
            self.results["summary"]["total_tests"] += 1
            self.results["performance"]["test_durations"][test_name] = test_result.get("duration", 0)
            
            if test_result["status"] == "passed":
                self.results["summary"]["passed_tests"] += 1
            elif test_result["status"] == "failed":
                self.results["summary"]["failed_tests"] += 1
            else:
                self.results["summary"]["skipped_tests"] += 1
        
        # Calculate total duration
        self.results["performance"]["total_duration"] = sum(
            self.results["performance"]["test_durations"].values()
        )
        
        # Generate recommendations
        recommendations = []
        
        if self.results["summary"]["failed_tests"] > 0:
            recommendations.append("❌ Some contract tests failed. Review failures and fix issues before deployment.")
        
        violations_count = sum(len(test.get("violations", [])) for test in self.results["tests"].values())
        if violations_count > 0:
            recommendations.append(f"⚠️  {violations_count} contract violations detected. Review and address violations.")
        
        spectral_result = self.results["tests"].get("spectral_validation")
        if spectral_result and spectral_result["status"] == "failed":
            recommendations.append("📋 OpenAPI schema validation failed. Fix schema issues for better API consistency.")
        
        performance_result = self.results["tests"].get("performance_validation")
        if performance_result and performance_result["status"] == "failed":
            recommendations.append("🚀 Performance SLA violations detected. Optimize slow endpoints.")
        
        if not recommendations:
            recommendations.append("✅ All contract tests passed! API is ready for deployment.")
        
        self.results["recommendations"] = recommendations
        
        # Save comprehensive report
        report_file = RESULTS_DIR / "contract_test_summary.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📄 Summary report saved: {report_file}")
    
    def print_summary(self) -> None:
        """Print test summary to console."""
        print("\n" + "="*80)
        print("CONTRACT TESTING SUMMARY")
        print("="*80)
        print(f"API URL: {self.api_url}")
        print(f"Tests Run: {self.results['summary']['total_tests']}")
        print(f"Passed: {self.results['summary']['passed_tests']}")
        print(f"Failed: {self.results['summary']['failed_tests']}")
        print(f"Skipped: {self.results['summary']['skipped_tests']}")
        print(f"Duration: {self.results['performance']['total_duration']:.1f}s")
        print()
        
        # Test details
        for test_name, test_result in self.results["tests"].items():
            status_icon = {
                "passed": "✅",
                "failed": "❌",
                "skipped": "⏭️"
            }.get(test_result["status"], "❓")
            
            duration = test_result.get("duration", 0)
            print(f"{status_icon} {test_name}: {test_result['status'].upper()} ({duration:.2f}s)")
            
            if test_result["status"] == "failed" and "error" in test_result.get("details", {}):
                print(f"    Error: {test_result['details']['error']}")
        
        print()
        
        # Recommendations
        if self.results["recommendations"]:
            print("RECOMMENDATIONS:")
            for rec in self.results["recommendations"]:
                print(f"  {rec}")
            print()
        
        print("="*80)
    
    def run_all_tests(self, quick_mode: bool = False, update_baseline: bool = False) -> bool:
        """Run complete contract testing suite."""
        logger.info("🚀 Starting contract testing suite...")
        overall_start = time.time()
        
        # Wait for API
        if not self.wait_for_api():
            logger.error("❌ API not available - cannot run tests")
            return False
        
        # Run tests based on mode
        if quick_mode:
            logger.info("🏃 Running in quick mode...")
            # Quick validation only
            self.results["tests"]["spectral_validation"] = self.run_spectral_validation()
            self.results["tests"]["performance_validation"] = self.run_performance_validation()
        else:
            logger.info("🔄 Running full contract testing suite...")
            # Run all tests
            self.results["tests"]["spectral_validation"] = self.run_spectral_validation()
            self.results["tests"]["schemathesis_contract"] = self.run_schemathesis_tests()
            self.results["tests"]["schema_drift"] = self.run_schema_drift_detection(update_baseline)
            self.results["tests"]["performance_validation"] = self.run_performance_validation()
        
        # Generate reports
        self.generate_summary_report()
        
        # Print results
        self.print_summary()
        
        # Determine overall success
        failed_tests = self.results["summary"]["failed_tests"]
        success = failed_tests == 0
        
        total_duration = time.time() - overall_start
        logger.info(f"🏁 Contract testing completed in {total_duration:.1f}s - {'SUCCESS' if success else 'FAILED'}")
        
        return success

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Run PrepSense API contract tests")
    parser.add_argument("--api-url", default=API_BASE_URL, help="API base URL")
    parser.add_argument("--full", action="store_true", help="Run full test suite (default)")
    parser.add_argument("--quick", action="store_true", help="Run quick validation only")
    parser.add_argument("--ci", action="store_true", help="CI mode - appropriate exit codes")
    parser.add_argument("--baseline-mode", action="store_true", help="Update schema baseline and exit")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS, help="Test timeout in seconds")
    
    args = parser.parse_args()
    
    # Update global timeout
    global TIMEOUT_SECONDS
    TIMEOUT_SECONDS = args.timeout
    
    # Create test runner
    runner = ContractTestRunner(api_url=args.api_url)
    
    try:
        if args.baseline_mode:
            logger.info("📏 Baseline mode - updating schema baseline...")
            result = runner.run_schema_drift_detection(update_baseline=True)
            if result["status"] == "passed":
                print("✅ Schema baseline updated successfully")
                sys.exit(0)
            else:
                print("❌ Failed to update schema baseline")
                sys.exit(1)
        
        # Determine test mode
        quick_mode = args.quick
        if not args.full and not args.quick:
            # Default to full unless quick is specified
            quick_mode = False
        
        # Run tests
        success = runner.run_all_tests(
            quick_mode=quick_mode,
            update_baseline=False
        )
        
        # Exit codes for CI
        if args.ci:
            if success:
                print("🎉 All contract tests passed - ready for deployment")
                sys.exit(0)
            else:
                print("💥 Contract tests failed - deployment not recommended")
                sys.exit(1)
        else:
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.info("Contract testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Contract testing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()