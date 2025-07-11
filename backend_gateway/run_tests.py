#!/usr/bin/env python3
"""
Test runner script for backend_gateway tests
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list) -> int:
    """Run a command and return the exit code"""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run backend_gateway tests")
    parser.add_argument(
        "--unit", 
        action="store_true", 
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration", 
        action="store_true", 
        help="Run only integration tests"
    )
    parser.add_argument(
        "--spoonacular", 
        action="store_true", 
        help="Run only Spoonacular-enhanced agent tests"
    )
    parser.add_argument(
        "--hybrid", 
        action="store_true", 
        help="Run only hybrid service tests"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--failfast", "-x", 
        action="store_true", 
        help="Stop on first failure"
    )
    parser.add_argument(
        "tests", 
        nargs="*", 
        help="Specific test files or test names to run"
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test selection
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.spoonacular:
        cmd.append("tests/test_spoonacular_enhanced_agents.py")
    elif args.hybrid:
        cmd.extend([
            "tests/test_hybrid_crew_service.py",
            "tests/test_hybrid_chat_router.py"
        ])
    elif args.tests:
        cmd.extend(args.tests)
    
    # Add options
    if args.verbose:
        cmd.append("-vv")
    
    if args.failfast:
        cmd.append("-x")
    
    if not args.coverage:
        cmd.append("--no-cov")
    
    # Run tests
    exit_code = run_command(cmd)
    
    # Generate HTML coverage report if requested
    if args.coverage and exit_code == 0:
        print("\nGenerating HTML coverage report...")
        run_command(["python", "-m", "coverage", "html"])
        print(f"\nCoverage report generated at: {Path('htmlcov/index.html').absolute()}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())