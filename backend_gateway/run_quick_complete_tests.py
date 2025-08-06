#!/usr/bin/env python3
"""
Simple test runner for Quick Complete tests without testcontainers
"""

import os
import subprocess
import sys

# Add the backend_gateway directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_tests():
    """Run Quick Complete tests with proper configuration"""

    # Set test environment
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test"

    # Run pytest with specific test file
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_quick_complete.py",
        "-v",
        "--tb=short",
        "-k",
        "not integration",  # Skip integration tests for now
    ]

    print("Running Quick Complete unit tests...")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
