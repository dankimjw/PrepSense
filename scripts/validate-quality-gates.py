#!/usr/bin/env python3
"""
PrepSense Quality Gates Validation Script
Validates code quality against defined thresholds and standards.
"""

import json
import os
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import argparse
from dataclasses import dataclass
import xml.etree.ElementTree as ET

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

@dataclass
class QualityResult:
    name: str
    passed: bool
    score: float
    threshold: float
    details: str = ""
    
class QualityGatesValidator:
    def __init__(self, config_path: str = ".quality-gates.yml"):
        """Initialize the quality gates validator."""
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.results: List[QualityResult] = []
        self.project_root = Path.cwd()
        
    def load_config(self) -> Dict[str, Any]:
        """Load quality gates configuration."""
        if not self.config_path.exists():
            print(f"{Colors.RED}❌ Quality gates config not found: {self.config_path}{Colors.END}")
            sys.exit(1)
            
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def run_command(self, command: str, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd or self.project_root
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)
    
    def check_coverage(self) -> List[QualityResult]:
        """Check code coverage for backend and frontend."""
        results = []
        
        # Backend coverage
        backend_config = self.config['quality_gates']['coverage']['backend']
        backend_path = self.project_root / "backend_gateway"
        
        if backend_path.exists():
            # Run pytest with coverage
            cmd = "python -m pytest tests/ --cov=. --cov-report=json --cov-report=term-missing"
            exit_code, stdout, stderr = self.run_command(cmd, backend_path)
            
            coverage_file = backend_path / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                
                line_coverage = coverage_data['totals']['percent_covered']
                threshold = backend_config['minimum_line_coverage']
                
                results.append(QualityResult(
                    name="Backend Line Coverage",
                    passed=line_coverage >= threshold,
                    score=line_coverage,
                    threshold=threshold,
                    details=f"{line_coverage:.1f}% (threshold: {threshold}%)"
                ))
            else:
                results.append(QualityResult(
                    name="Backend Coverage",
                    passed=False,
                    score=0,
                    threshold=backend_config['minimum_line_coverage'],
                    details="Coverage report not generated"
                ))
        
        # Frontend coverage
        frontend_config = self.config['quality_gates']['coverage']['frontend']
        frontend_path = self.project_root / "ios-app"
        
        if frontend_path.exists():
            # Run Jest with coverage
            cmd = "npm run test:coverage -- --watchAll=false --coverageReporters=json"
            exit_code, stdout, stderr = self.run_command(cmd, frontend_path)
            
            coverage_file = frontend_path / "coverage" / "coverage-final.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                
                # Calculate overall coverage
                total_lines = sum(data['s']['total'] for data in coverage_data.values())
                covered_lines = sum(data['s']['covered'] for data in coverage_data.values())
                line_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
                
                threshold = frontend_config['minimum_line_coverage']
                
                results.append(QualityResult(
                    name="Frontend Line Coverage",
                    passed=line_coverage >= threshold,
                    score=line_coverage,
                    threshold=threshold,
                    details=f"{line_coverage:.1f}% (threshold: {threshold}%)"
                ))
            else:
                results.append(QualityResult(
                    name="Frontend Coverage",
                    passed=False,
                    score=0,
                    threshold=frontend_config['minimum_line_coverage'],
                    details="Coverage report not generated"
                ))
        
        return results
    
    def check_code_quality(self) -> List[QualityResult]:
        """Check code quality metrics."""
        results = []
        
        # Backend quality checks
        backend_path = self.project_root / "backend_gateway"
        if backend_path.exists():
            # Check with ruff
            exit_code, stdout, stderr = self.run_command("ruff check . --output-format=json", backend_path)
            
            if exit_code == 0:
                results.append(QualityResult(
                    name="Backend Linting (Ruff)",
                    passed=True,
                    score=100,
                    threshold=100,
                    details="No linting issues found"
                ))
            else:
                try:
                    ruff_output = json.loads(stdout) if stdout else []
                    issue_count = len(ruff_output)
                    results.append(QualityResult(
                        name="Backend Linting (Ruff)",
                        passed=issue_count == 0,
                        score=max(0, 100 - issue_count),
                        threshold=100,
                        details=f"{issue_count} issues found"
                    ))
                except json.JSONDecodeError:
                    results.append(QualityResult(
                        name="Backend Linting (Ruff)",
                        passed=False,
                        score=0,
                        threshold=100,
                        details="Linting failed"
                    ))
            
            # Check complexity with radon (if available)
            exit_code, stdout, stderr = self.run_command("radon cc . --json", backend_path)
            if exit_code == 0 and stdout:
                try:
                    complexity_data = json.loads(stdout)
                    max_complexity = self.config['quality_gates']['code_quality']['backend']['max_cyclomatic_complexity']
                    
                    high_complexity_functions = 0
                    total_functions = 0
                    
                    for file_data in complexity_data.values():
                        for func in file_data:
                            total_functions += 1
                            if func['complexity'] > max_complexity:
                                high_complexity_functions += 1
                    
                    complexity_score = 100 - (high_complexity_functions / max(total_functions, 1) * 100)
                    
                    results.append(QualityResult(
                        name="Backend Complexity",
                        passed=high_complexity_functions == 0,
                        score=complexity_score,
                        threshold=100,
                        details=f"{high_complexity_functions}/{total_functions} functions exceed complexity threshold"
                    ))
                except (json.JSONDecodeError, KeyError):
                    pass
        
        # Frontend quality checks
        frontend_path = self.project_root / "ios-app"
        if frontend_path.exists():
            # ESLint check
            exit_code, stdout, stderr = self.run_command("npm run lint:strict", frontend_path)
            
            results.append(QualityResult(
                name="Frontend Linting (ESLint)",
                passed=exit_code == 0,
                score=100 if exit_code == 0 else 0,
                threshold=100,
                details="Passed" if exit_code == 0 else "Linting issues found"
            ))
            
            # TypeScript check
            exit_code, stdout, stderr = self.run_command("npm run typecheck", frontend_path)
            
            results.append(QualityResult(
                name="Frontend Type Checking",
                passed=exit_code == 0,
                score=100 if exit_code == 0 else 0,
                threshold=100,
                details="Passed" if exit_code == 0 else "Type errors found"
            ))
        
        return results
    
    def check_security(self) -> List[QualityResult]:
        """Check security vulnerabilities."""
        results = []
        
        # Backend security
        backend_path = self.project_root / "backend_gateway"
        if backend_path.exists():
            # Bandit security scan
            exit_code, stdout, stderr = self.run_command("bandit -r . -f json", backend_path)
            
            if stdout:
                try:
                    bandit_data = json.loads(stdout)
                    high_issues = len([issue for issue in bandit_data.get('results', []) 
                                     if issue.get('issue_severity') == 'HIGH'])
                    medium_issues = len([issue for issue in bandit_data.get('results', []) 
                                       if issue.get('issue_severity') == 'MEDIUM'])
                    
                    max_high = self.config['quality_gates']['security']['max_high_severity_vulnerabilities']
                    max_medium = self.config['quality_gates']['security']['max_medium_severity_vulnerabilities']
                    
                    results.append(QualityResult(
                        name="Backend Security (High Severity)",
                        passed=high_issues <= max_high,
                        score=max(0, 100 - high_issues * 25),
                        threshold=max_high,
                        details=f"{high_issues} high severity issues (max: {max_high})"
                    ))
                    
                    results.append(QualityResult(
                        name="Backend Security (Medium Severity)",
                        passed=medium_issues <= max_medium,
                        score=max(0, 100 - medium_issues * 5),
                        threshold=max_medium,
                        details=f"{medium_issues} medium severity issues (max: {max_medium})"
                    ))
                except json.JSONDecodeError:
                    results.append(QualityResult(
                        name="Backend Security Scan",
                        passed=False,
                        score=0,
                        threshold=100,
                        details="Security scan failed"
                    ))
        
        # Dependency vulnerability scan
        exit_code, stdout, stderr = self.run_command("pip-audit --format=json")
        if exit_code == 0 and stdout:
            try:
                audit_data = json.loads(stdout)
                vulnerabilities = len(audit_data.get('vulnerabilities', []))
                
                results.append(QualityResult(
                    name="Dependency Security",
                    passed=vulnerabilities == 0,
                    score=max(0, 100 - vulnerabilities * 10),
                    threshold=0,
                    details=f"{vulnerabilities} vulnerabilities found"
                ))
            except json.JSONDecodeError:
                pass
        
        return results
    
    def check_tests(self) -> List[QualityResult]:
        """Check test requirements."""
        results = []
        
        # Backend tests
        backend_path = self.project_root / "backend_gateway"
        if backend_path.exists():
            test_dir = backend_path / "tests"
            if test_dir.exists():
                test_files = list(test_dir.glob("**/test_*.py")) + list(test_dir.glob("**/*_test.py"))
                min_test_files = self.config['quality_gates']['testing']['minimum_test_files']
                
                results.append(QualityResult(
                    name="Backend Test Coverage",
                    passed=len(test_files) >= min_test_files,
                    score=min(100, len(test_files) / min_test_files * 100),
                    threshold=min_test_files,
                    details=f"{len(test_files)} test files (minimum: {min_test_files})"
                ))
                
                # Run tests to check if they pass
                exit_code, stdout, stderr = self.run_command("python -m pytest tests/ --tb=no -q", backend_path)
                results.append(QualityResult(
                    name="Backend Test Execution",
                    passed=exit_code == 0,
                    score=100 if exit_code == 0 else 0,
                    threshold=100,
                    details="All tests passed" if exit_code == 0 else "Some tests failed"
                ))
        
        # Frontend tests
        frontend_path = self.project_root / "ios-app"
        if frontend_path.exists():
            test_dir = frontend_path / "__tests__"
            if test_dir.exists():
                test_files = list(test_dir.glob("**/*.test.*")) + list(test_dir.glob("**/*.spec.*"))
                min_test_files = 5  # Reasonable minimum for frontend
                
                results.append(QualityResult(
                    name="Frontend Test Coverage",
                    passed=len(test_files) >= min_test_files,
                    score=min(100, len(test_files) / min_test_files * 100),
                    threshold=min_test_files,
                    details=f"{len(test_files)} test files (minimum: {min_test_files})"
                ))
                
                # Run tests
                exit_code, stdout, stderr = self.run_command("npm test -- --watchAll=false --passWithNoTests", frontend_path)
                results.append(QualityResult(
                    name="Frontend Test Execution",
                    passed=exit_code == 0,
                    score=100 if exit_code == 0 else 0,
                    threshold=100,
                    details="All tests passed" if exit_code == 0 else "Some tests failed"
                ))
        
        return results
    
    def run_all_checks(self, categories: List[str] = None) -> None:
        """Run all quality gate checks."""
        print(f"{Colors.BLUE}{Colors.BOLD}🚪 PrepSense Quality Gates Validation{Colors.END}")
        print(f"{Colors.BLUE}{'=' * 50}{Colors.END}")
        
        if not categories:
            categories = ['coverage', 'quality', 'security', 'tests']
        
        if 'coverage' in categories:
            print(f"\n{Colors.YELLOW}📊 Checking Code Coverage...{Colors.END}")
            self.results.extend(self.check_coverage())
        
        if 'quality' in categories:
            print(f"\n{Colors.YELLOW}🔍 Checking Code Quality...{Colors.END}")
            self.results.extend(self.check_code_quality())
        
        if 'security' in categories:
            print(f"\n{Colors.YELLOW}🔒 Checking Security...{Colors.END}")
            self.results.extend(self.check_security())
        
        if 'tests' in categories:
            print(f"\n{Colors.YELLOW}🧪 Checking Tests...{Colors.END}")
            self.results.extend(self.check_tests())
    
    def print_results(self) -> bool:
        """Print validation results and return overall pass/fail."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}📋 Quality Gates Results{Colors.END}")
        print(f"{Colors.BLUE}{'=' * 50}{Colors.END}")
        
        passed = 0
        failed = 0
        
        for result in self.results:
            status_color = Colors.GREEN if result.passed else Colors.RED
            status_symbol = "✅" if result.passed else "❌"
            
            print(f"{status_symbol} {Colors.BOLD}{result.name}{Colors.END}")
            print(f"   Score: {status_color}{result.score:.1f}{Colors.END} (Threshold: {result.threshold})")
            if result.details:
                print(f"   Details: {result.details}")
            print()
            
            if result.passed:
                passed += 1
            else:
                failed += 1
        
        # Overall summary
        total = passed + failed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"{Colors.BLUE}{Colors.BOLD}📈 Overall Summary{Colors.END}")
        print(f"{Colors.BLUE}{'=' * 20}{Colors.END}")
        print(f"Total Checks: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        overall_passed = failed == 0
        if overall_passed:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All Quality Gates Passed! 🎉{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ Quality Gates Failed{Colors.END}")
            print(f"{Colors.YELLOW}Please fix the failing checks before proceeding.{Colors.END}")
        
        return overall_passed
    
    def export_results(self, format_type: str = "json", output_file: str = None) -> None:
        """Export results to file."""
        if not output_file:
            output_file = f"quality-gates-results.{format_type}"
        
        if format_type == "json":
            results_data = {
                "summary": {
                    "total": len(self.results),
                    "passed": sum(1 for r in self.results if r.passed),
                    "failed": sum(1 for r in self.results if not r.passed),
                    "success_rate": sum(1 for r in self.results if r.passed) / len(self.results) * 100 if self.results else 0
                },
                "results": [
                    {
                        "name": r.name,
                        "passed": r.passed,
                        "score": r.score,
                        "threshold": r.threshold,
                        "details": r.details
                    }
                    for r in self.results
                ]
            }
            
            with open(output_file, 'w') as f:
                json.dump(results_data, f, indent=2)
                
        elif format_type == "junit":
            # Create JUnit XML format
            testsuites = ET.Element("testsuites")
            testsuite = ET.SubElement(testsuites, "testsuite", {
                "name": "Quality Gates",
                "tests": str(len(self.results)),
                "failures": str(sum(1 for r in self.results if not r.passed)),
                "time": "0"
            })
            
            for result in self.results:
                testcase = ET.SubElement(testsuite, "testcase", {
                    "name": result.name,
                    "classname": "QualityGates",
                    "time": "0"
                })
                
                if not result.passed:
                    failure = ET.SubElement(testcase, "failure", {
                        "message": f"Score {result.score} below threshold {result.threshold}"
                    })
                    failure.text = result.details
            
            tree = ET.ElementTree(testsuites)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        print(f"{Colors.GREEN}Results exported to: {output_file}{Colors.END}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate PrepSense quality gates")
    parser.add_argument("--config", default=".quality-gates.yml", help="Path to quality gates config")
    parser.add_argument("--categories", nargs="+", choices=["coverage", "quality", "security", "tests"], 
                       help="Categories to check")
    parser.add_argument("--export", choices=["json", "junit"], help="Export results format")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--fail-fast", action="store_true", help="Exit on first failure")
    
    args = parser.parse_args()
    
    validator = QualityGatesValidator(args.config)
    
    try:
        validator.run_all_checks(args.categories)
        
        if args.export:
            validator.export_results(args.export, args.output)
        
        overall_passed = validator.print_results()
        
        sys.exit(0 if overall_passed else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Quality gate validation interrupted{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Error during validation: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()