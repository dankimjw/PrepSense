#!/usr/bin/env python3
"""
Test runner script for PrepSense backend testing
Provides organized test execution with reporting
"""
import subprocess
import sys
import os
import time
from pathlib import Path


def run_command(cmd, description, cwd=None):
    """Run a command and return success status"""
    print(f"\n🏃 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        print(f"✅ {description} - PASSED")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        return False


def main():
    """Main test runner"""
    print("🚀 PrepSense Backend Test Suite")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Test categories
    test_results = {}
    
    # 1. Unit Tests
    print("\n📋 Running Unit Tests")
    test_results['unit'] = run_command([
        sys.executable, "-m", "pytest", 
        "tests/domain/", 
        "-v", "--tb=short", "-m", "not slow"
    ], "Unit Tests")
    
    # 2. Integration Tests
    print("\n🔗 Running Integration Tests")
    test_results['integration'] = run_command([
        sys.executable, "-m", "pytest", 
        "tests/api/", 
        "-v", "--tb=short"
    ], "Integration Tests")
    
    # 3. Database Tests
    print("\n🗄️ Running Database Tests")
    test_results['database'] = run_command([
        sys.executable, "-m", "pytest", 
        "tests/db/", 
        "-v", "--tb=short"
    ], "Database Tests")
    
    # 4. Contract Tests
    print("\n📋 Running Contract Tests")
    test_results['contract'] = run_command([
        sys.executable, "-m", "pytest", 
        "tests/contracts/", 
        "-v", "--tb=short"
    ], "Contract Tests")
    
    # 5. Performance Tests
    print("\n⚡ Running Performance Tests")
    test_results['performance'] = run_command([
        sys.executable, "-m", "pytest", 
        "tests/perf/", 
        "-v", "--tb=short", "-m", "performance"
    ], "Performance Tests")
    
    # 6. Ingredient Matching Tests
    print("\n🧪 Running Ingredient Matching Tests")
    test_results['ingredient_matching'] = run_command([
        sys.executable, "test_ingredient_matching_simple.py"
    ], "Ingredient Matching Tests")
    
    # 7. Code Quality Checks
    print("\n✨ Running Code Quality Checks")
    
    # Black formatter check
    test_results['black'] = run_command([
        "python", "-m", "black", "--check", "--diff", "."
    ], "Black Code Formatting")
    
    # Ruff linter
    test_results['ruff'] = run_command([
        "python", "-m", "ruff", "check", "."
    ], "Ruff Linting")
    
    # 8. Security Checks
    print("\n🔒 Running Security Checks")
    
    # Bandit security scan
    test_results['bandit'] = run_command([
        "python", "-m", "bandit", "-r", ".", "-f", "json"
    ], "Bandit Security Scan")
    
    # pip-audit
    test_results['pip_audit'] = run_command([
        "python", "-m", "pip_audit", "--desc"
    ], "Pip Audit Security Check")
    
    # 9. Load Testing (optional)
    if len(sys.argv) > 1 and sys.argv[1] == "--load":
        print("\n🔥 Running Load Tests")
        test_results['load'] = run_command([
            "locust", "-H", "http://localhost:8000", 
            "-u", "10", "-r", "5", "--run-time", "30s", 
            "--headless", "--only-summary"
        ], "Load Testing")
    
    # Summary Report
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    total = passed + failed
    print(f"\nTotal: {total}, Passed: {passed}, Failed: {failed}")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"💥 {failed} test suites failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())