#!/usr/bin/env python3

"""PrepSense Repository Health Check - Validates repository state and structure"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class RepositoryHealthChecker:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "repository_structure": {},
            "git_status": {},
            "cache_analysis": {},
            "dependency_status": {},
            "warnings": [],
            "errors": [],
        }

    def log(self, message: str, status: str = "info"):
        """Log message with color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if status == "success":
            print(f"{Colors.GREEN}✅ [{timestamp}] {message}{Colors.RESET}")
        elif status == "error":
            print(f"{Colors.RED}❌ [{timestamp}] {message}{Colors.RESET}")
            self.results["errors"].append(message)
        elif status == "warning":
            print(f"{Colors.YELLOW}⚠️  [{timestamp}] {message}{Colors.RESET}")
            self.results["warnings"].append(message)
        else:
            print(f"{Colors.BLUE}ℹ️  [{timestamp}] {message}{Colors.RESET}")

    def check_required_files(self) -> dict:
        """Check for essential repository files"""
        required_files = [
            ".gitignore",
            "README.md",
            "run_app.py",
            "quick_check.sh",
            ".env.template",
            "requirements.txt",
        ]

        results = {}
        for file_path in required_files:
            full_path = self.repo_root / file_path
            exists = full_path.exists()
            results[file_path] = exists

            if exists:
                self.log(f"Required file found: {file_path}", "success")
            else:
                self.log(f"Missing required file: {file_path}", "error")

        return results

    def analyze_cache_files(self) -> dict:
        """Analyze cache and temporary files in the repository"""
        cache_patterns = {
            "python_cache": ["**/__pycache__", "**/*.pyc"],
            "system_files": ["**/.DS_Store"],
            "build_cache": [".mypy_cache"],
            "logs": ["**/*.log"],
            "test_cache": [".pytest_cache", "**/.coverage"],
        }

        results = {}
        for category, patterns in cache_patterns.items():
            count = 0
            for pattern in patterns:
                try:
                    if "*" in pattern:
                        count += len(list(self.repo_root.glob(pattern)))
                    else:
                        path = self.repo_root / pattern
                        if path.exists():
                            count += 1
                except Exception:
                    pass

            results[category] = count
            if count > 0:
                self.log(f"Found {count} {category} files/directories", "info")

        total_cache = sum(results.values())
        if total_cache > 100:
            self.log(f"High cache file count: {total_cache} items", "warning")

        return results

    def check_git_status(self) -> dict:
        """Check git repository status"""
        try:
            # Check if we're in a git repository
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            # Get status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            current_branch = branch_result.stdout.strip()
            status_lines = (
                status_result.stdout.strip().split("\n") if status_result.stdout.strip() else []
            )

            results = {
                "is_git_repo": True,
                "current_branch": current_branch,
                "staged_files": len(
                    [
                        line
                        for line in status_lines
                        if line.startswith("A ") or line.startswith("M ")
                    ]
                ),
                "unstaged_files": len(
                    [
                        line
                        for line in status_lines
                        if line.startswith(" M") or line.startswith("?? ")
                    ]
                ),
                "untracked_files": len([line for line in status_lines if line.startswith("??")]),
            }

            self.log(f"Git repository on branch: {current_branch}", "success")
            if results["staged_files"] > 0:
                self.log(f"{results['staged_files']} staged files", "info")
            if results["unstaged_files"] > 0:
                self.log(f"{results['unstaged_files']} unstaged changes", "warning")
            if results["untracked_files"] > 0:
                self.log(f"{results['untracked_files']} untracked files", "info")

            return results

        except subprocess.CalledProcessError:
            self.log("Not a git repository", "error")
            return {"is_git_repo": False}

    def check_dependencies(self) -> dict:
        """Check dependency files and virtual environment"""
        results = {}

        # Check Python virtual environment
        venv_path = self.repo_root / "venv"
        results["virtual_env"] = venv_path.exists()

        if results["virtual_env"]:
            self.log("Python virtual environment found", "success")
        else:
            self.log("Python virtual environment not found", "warning")

        # Check requirements.txt
        requirements_path = self.repo_root / "requirements.txt"
        results["requirements_txt"] = requirements_path.exists()

        # Check package.json for iOS app
        package_json_path = self.repo_root / "ios-app" / "package.json"
        results["package_json"] = package_json_path.exists()

        # Check node_modules
        node_modules_path = self.repo_root / "ios-app" / "node_modules"
        results["node_modules"] = node_modules_path.exists()

        if results["node_modules"]:
            self.log("Node.js dependencies installed", "success")
        else:
            self.log("Node.js dependencies not installed", "warning")

        return results

    def check_todos_in_production(self) -> dict:
        """Check for TODOs in production code"""
        todo_count = 0
        fixme_count = 0
        todo_files = []

        # Check Python files
        for py_file in self.repo_root.glob("backend_gateway/**/*.py"):
            if "__pycache__" in str(py_file) or "test" in str(py_file).lower():
                continue
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                    file_todos = content.count("TODO")
                    file_fixmes = content.count("FIXME")
                    if file_todos > 0 or file_fixmes > 0:
                        todo_files.append(str(py_file.relative_to(self.repo_root)))
                        todo_count += file_todos
                        fixme_count += file_fixmes
            except Exception:
                pass

        results = {
            "todo_count": todo_count,
            "fixme_count": fixme_count,
            "files_with_todos": len(todo_files),
        }

        if todo_count > 0 or fixme_count > 0:
            self.log(
                f"Found {todo_count} TODOs and {fixme_count} FIXMEs in production code", "warning"
            )
        else:
            self.log("No TODOs or FIXMEs in production code", "success")

        return results

    def run_comprehensive_check(self) -> dict:
        """Run all health checks"""
        print(f"{Colors.BOLD}PrepSense Repository Health Check{Colors.RESET}")
        print(f"Repository: {self.repo_root}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # Run all checks
        self.results["repository_structure"] = self.check_required_files()
        self.results["git_status"] = self.check_git_status()
        self.results["cache_analysis"] = self.analyze_cache_files()
        self.results["dependency_status"] = self.check_dependencies()
        self.results["todo_analysis"] = self.check_todos_in_production()

        # Summary
        print("\n" + "=" * 70)
        print(f"{Colors.BOLD}Health Check Summary{Colors.RESET}")

        error_count = len(self.results["errors"])
        warning_count = len(self.results["warnings"])

        if error_count == 0 and warning_count == 0:
            self.log("Repository health check passed!", "success")
        elif error_count == 0:
            self.log(f"Repository health check completed with {warning_count} warnings", "warning")
        else:
            self.log(
                f"Repository health check found {error_count} errors and {warning_count} warnings",
                "error",
            )

        return self.results

    def save_results(self, output_file: Optional[str] = None):
        """Save results to JSON file"""
        if output_file is None:
            output_file = self.repo_root / "health_check_results.json"

        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        self.log(f"Results saved to: {output_file}", "info")


if __name__ == "__main__":
    repo_root = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    checker = RepositoryHealthChecker(repo_root)
    results = checker.run_comprehensive_check()

    # Don't save results file in git - just display
    if "--save" in sys.argv:
        checker.save_results()
