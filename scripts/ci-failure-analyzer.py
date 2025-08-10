#!/usr/bin/env python3
"""
CI/CD Failure Analyzer
Analyzes failed CI/CD pipelines and provides automated fixes and recommendations.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import yaml


@dataclass
class FailurePattern:
    name: str
    patterns: list[str]
    category: str
    severity: str
    fix_commands: list[str]
    description: str

class CIFailureAnalyzer:
    def __init__(self):
        """Initialize the CI failure analyzer."""
        self.failure_patterns = self._load_failure_patterns()
        self.fixes_applied = []
        self.analysis_results = []

    def _load_failure_patterns(self) -> list[FailurePattern]:
        """Load known failure patterns and their fixes."""
        return [
            # Python/Backend failures
            FailurePattern(
                name="Import Error",
                patterns=[
                    r"ImportError: No module named",
                    r"ModuleNotFoundError: No module named",
                    r"cannot import name"
                ],
                category="dependency",
                severity="high",
                fix_commands=[
                    "pip install -r requirements.txt",
                    "python -m pip install --upgrade pip"
                ],
                description="Missing Python dependencies"
            ),

            FailurePattern(
                name="Linting Errors",
                patterns=[
                    r"ruff check.*failed",
                    r"black.*failed",
                    r"flake8.*failed",
                    r"mypy.*failed"
                ],
                category="code_quality",
                severity="medium",
                fix_commands=[
                    "black .",
                    "ruff check . --fix",
                    "isort ."
                ],
                description="Code formatting and linting issues"
            ),

            FailurePattern(
                name="Test Failures",
                patterns=[
                    r"FAILED.*test_",
                    r"AssertionError",
                    r"pytest.*failed",
                    r"E\s+assert"
                ],
                category="testing",
                severity="high",
                fix_commands=[
                    "python -m pytest --lf",
                    "python -m pytest -x"
                ],
                description="Unit/integration test failures"
            ),

            FailurePattern(
                name="Database Connection",
                patterns=[
                    r"could not connect to server",
                    r"connection refused",
                    r"database.*does not exist",
                    r"authentication failed"
                ],
                category="database",
                severity="high",
                fix_commands=[
                    "alembic upgrade head",
                    "python scripts/setup_database.py"
                ],
                description="Database connectivity issues"
            ),

            # Node.js/Frontend failures
            FailurePattern(
                name="NPM Install Failure",
                patterns=[
                    r"npm ERR!",
                    r"npm install.*failed",
                    r"package-lock.json.*conflict"
                ],
                category="dependency",
                severity="high",
                fix_commands=[
                    "rm -rf node_modules package-lock.json",
                    "npm install"
                ],
                description="NPM dependency installation issues"
            ),

            FailurePattern(
                name="TypeScript Errors",
                patterns=[
                    r"TypeScript error",
                    r"tsc.*failed",
                    r"Type.*is not assignable",
                    r"Property.*does not exist"
                ],
                category="code_quality",
                severity="medium",
                fix_commands=[
                    "npm run typecheck",
                    "npx tsc --noEmit"
                ],
                description="TypeScript compilation errors"
            ),

            FailurePattern(
                name="ESLint Errors",
                patterns=[
                    r"ESLint.*error",
                    r"eslint.*failed",
                    r"lint.*failed"
                ],
                category="code_quality",
                severity="medium",
                fix_commands=[
                    "npm run lint:fix",
                    "npx eslint . --fix"
                ],
                description="ESLint code quality issues"
            ),

            FailurePattern(
                name="Build Errors",
                patterns=[
                    r"build.*failed",
                    r"compilation.*failed",
                    r"webpack.*error",
                    r"Metro.*error"
                ],
                category="build",
                severity="high",
                fix_commands=[
                    "rm -rf node_modules/.cache",
                    "npm run clean",
                    "npm run build"
                ],
                description="Build compilation failures"
            ),

            # Security failures
            FailurePattern(
                name="Security Vulnerabilities",
                patterns=[
                    r"High severity vulnerability",
                    r"security audit.*failed",
                    r"bandit.*SEVERITY",
                    r"pip-audit.*found"
                ],
                category="security",
                severity="high",
                fix_commands=[
                    "npm audit fix",
                    "pip-audit --fix"
                ],
                description="Security vulnerability detected"
            ),

            # Coverage failures
            FailurePattern(
                name="Coverage Below Threshold",
                patterns=[
                    r"coverage.*below.*threshold",
                    r"TOTAL.*coverage.*failed",
                    r"Coverage check failed"
                ],
                category="coverage",
                severity="medium",
                fix_commands=[
                    "# Add more tests to increase coverage"
                ],
                description="Code coverage below required threshold"
            ),

            # Environment failures
            FailurePattern(
                name="Environment Issues",
                patterns=[
                    r"Environment variable.*not set",
                    r"\.env.*not found",
                    r"configuration.*missing"
                ],
                category="environment",
                severity="high",
                fix_commands=[
                    "cp .env.example .env",
                    "# Configure required environment variables"
                ],
                description="Environment configuration issues"
            ),
        ]

    def analyze_log(self, log_content: str) -> list[dict[str, Any]]:
        """Analyze log content for known failure patterns."""
        failures = []

        lines = log_content.split("\n")

        for i, line in enumerate(lines):
            for pattern in self.failure_patterns:
                for regex in pattern.patterns:
                    if re.search(regex, line, re.IGNORECASE):
                        context_lines = []
                        # Capture surrounding context
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        context_lines = lines[start:end]

                        failures.append({
                            "pattern": pattern,
                            "line": line.strip(),
                            "line_number": i + 1,
                            "context": context_lines,
                            "category": pattern.category,
                            "severity": pattern.severity
                        })
                        break

        return failures

    def analyze_github_actions_log(self, log_file: str) -> dict[str, Any]:
        """Analyze GitHub Actions log file."""
        if not os.path.exists(log_file):
            print(f"❌ Log file not found: {log_file}")
            return {}

        with open(log_file, encoding="utf-8", errors="ignore") as f:
            log_content = f.read()

        failures = self.analyze_log(log_content)

        # Categorize failures
        categorized = {}
        for failure in failures:
            category = failure["category"]
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(failure)

        return {
            "total_failures": len(failures),
            "categorized_failures": categorized,
            "raw_failures": failures,
            "log_size": len(log_content)
        }

    def generate_fix_suggestions(self, analysis_result: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate fix suggestions based on analysis."""
        suggestions = []

        for category, failures in analysis_result.get("categorized_failures", {}).items():
            # Group similar failures
            pattern_counts = {}
            for failure in failures:
                pattern_name = failure["pattern"].name
                if pattern_name not in pattern_counts:
                    pattern_counts[pattern_name] = []
                pattern_counts[pattern_name].append(failure)

            for pattern_name, pattern_failures in pattern_counts.items():
                pattern = pattern_failures[0]["pattern"]

                suggestion = {
                    "pattern_name": pattern_name,
                    "category": category,
                    "severity": pattern.severity,
                    "description": pattern.description,
                    "fix_commands": pattern.fix_commands,
                    "occurrences": len(pattern_failures),
                    "examples": [f["line"] for f in pattern_failures[:3]],  # Show first 3 examples
                    "auto_fixable": len([cmd for cmd in pattern.fix_commands if not cmd.startswith("#")]) > 0
                }

                suggestions.append(suggestion)

        # Sort by severity and occurrence count
        severity_order = {"high": 3, "medium": 2, "low": 1}
        suggestions.sort(key=lambda x: (severity_order.get(x["severity"], 0), x["occurrences"]), reverse=True)

        return suggestions

    def apply_automatic_fixes(self, suggestions: list[dict[str, Any]], dry_run: bool = True) -> list[dict[str, Any]]:
        """Apply automatic fixes for fixable issues."""
        applied_fixes = []

        for suggestion in suggestions:
            if suggestion["auto_fixable"] and suggestion["severity"] in ["high", "medium"]:
                print(f"\n🔧 Attempting to fix: {suggestion['pattern_name']}")

                for command in suggestion["fix_commands"]:
                    if command.startswith("#"):
                        print(f"💡 Manual action required: {command}")
                        continue

                    if dry_run:
                        print(f"🔍 Would run: {command}")
                    else:
                        try:
                            print(f"🏃 Running: {command}")
                            result = subprocess.run(command, check=False, shell=True, capture_output=True, text=True)

                            if result.returncode == 0:
                                print(f"✅ Success: {command}")
                                applied_fixes.append({
                                    "command": command,
                                    "pattern": suggestion["pattern_name"],
                                    "success": True,
                                    "output": result.stdout
                                })
                            else:
                                print(f"❌ Failed: {command}")
                                print(f"Error: {result.stderr}")
                                applied_fixes.append({
                                    "command": command,
                                    "pattern": suggestion["pattern_name"],
                                    "success": False,
                                    "error": result.stderr
                                })
                        except Exception as e:
                            print(f"❌ Exception running {command}: {e}")
                            applied_fixes.append({
                                "command": command,
                                "pattern": suggestion["pattern_name"],
                                "success": False,
                                "error": str(e)
                            })

        return applied_fixes

    def generate_report(self, analysis_result: dict[str, Any], suggestions: list[dict[str, Any]],
                       applied_fixes: list[dict[str, Any]] = None) -> dict[str, Any]:
        """Generate comprehensive failure analysis report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_failures": analysis_result.get("total_failures", 0),
                "categories": list(analysis_result.get("categorized_failures", {}).keys()),
                "auto_fixable_issues": len([s for s in suggestions if s["auto_fixable"]]),
                "manual_action_required": len([s for s in suggestions if not s["auto_fixable"]])
            },
            "failure_analysis": analysis_result,
            "fix_suggestions": suggestions,
            "applied_fixes": applied_fixes or [],
            "recommendations": []
        }

        # Generate recommendations
        high_severity_count = len([s for s in suggestions if s["severity"] == "high"])
        if high_severity_count > 0:
            report["recommendations"].append(
                f"❗ {high_severity_count} high severity issues require immediate attention"
            )

        coverage_issues = [s for s in suggestions if s["category"] == "coverage"]
        if coverage_issues:
            report["recommendations"].append(
                "📊 Consider increasing test coverage to meet quality gates"
            )

        security_issues = [s for s in suggestions if s["category"] == "security"]
        if security_issues:
            report["recommendations"].append(
                "🔒 Address security vulnerabilities before deployment"
            )

        return report

    def export_report(self, report: dict[str, Any], format_type: str = "json", output_file: str = None):
        """Export analysis report to file."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"ci_failure_analysis_{timestamp}.{format_type}"

        if format_type == "json":
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2, default=str)
        elif format_type == "yaml":
            with open(output_file, "w") as f:
                yaml.safe_dump(report, f, default_flow_style=False)
        elif format_type == "md":
            self._export_markdown_report(report, output_file)

        print(f"📄 Report exported to: {output_file}")

    def _export_markdown_report(self, report: dict[str, Any], output_file: str):
        """Export report in Markdown format."""
        with open(output_file, "w") as f:
            f.write("# CI/CD Failure Analysis Report\n\n")
            f.write(f"**Generated:** {report['timestamp']}\n\n")

            # Summary
            f.write("## Summary\n\n")
            summary = report["summary"]
            f.write(f"- **Total Failures:** {summary['total_failures']}\n")
            f.write(f"- **Categories:** {', '.join(summary['categories'])}\n")
            f.write(f"- **Auto-fixable Issues:** {summary['auto_fixable_issues']}\n")
            f.write(f"- **Manual Action Required:** {summary['manual_action_required']}\n\n")

            # Recommendations
            if report["recommendations"]:
                f.write("## Recommendations\n\n")
                for rec in report["recommendations"]:
                    f.write(f"- {rec}\n")
                f.write("\n")

            # Fix Suggestions
            f.write("## Fix Suggestions\n\n")
            for suggestion in report["fix_suggestions"]:
                f.write(f"### {suggestion['pattern_name']} ({suggestion['severity']} severity)\n\n")
                f.write(f"**Description:** {suggestion['description']}\n\n")
                f.write(f"**Category:** {suggestion['category']}\n\n")
                f.write(f"**Occurrences:** {suggestion['occurrences']}\n\n")

                if suggestion["examples"]:
                    f.write("**Examples:**\n")
                    for example in suggestion["examples"]:
                        f.write(f"```\n{example}\n```\n")
                    f.write("\n")

                if suggestion["fix_commands"]:
                    f.write("**Fix Commands:**\n")
                    for cmd in suggestion["fix_commands"]:
                        f.write(f"```bash\n{cmd}\n```\n")
                    f.write("\n")

            # Applied Fixes
            if report["applied_fixes"]:
                f.write("## Applied Fixes\n\n")
                for fix in report["applied_fixes"]:
                    status = "✅" if fix["success"] else "❌"
                    f.write(f"- {status} `{fix['command']}` - {fix['pattern']}\n")

    def print_analysis_summary(self, analysis_result: dict[str, Any], suggestions: list[dict[str, Any]]):
        """Print analysis summary to console."""
        print("\n" + "="*50)
        print("🔍 CI/CD Failure Analysis Summary")
        print("="*50)

        total_failures = analysis_result.get("total_failures", 0)
        print(f"\n📊 Total Failures Detected: {total_failures}")

        if total_failures == 0:
            print("🎉 No known failure patterns detected!")
            return

        # Print by category
        for category, failures in analysis_result.get("categorized_failures", {}).items():
            print(f"\n📂 {category.title()} Issues: {len(failures)}")

        # Print top suggestions
        print("\n🔧 Top Fix Suggestions:")
        for i, suggestion in enumerate(suggestions[:5], 1):
            severity_icon = {"high": "🚨", "medium": "⚠️", "low": "ℹ️"}.get(suggestion["severity"], "❓")
            auto_fix_icon = "🤖" if suggestion["auto_fixable"] else "👤"

            print(f"{i}. {severity_icon} {auto_fix_icon} {suggestion['pattern_name']} ({suggestion['occurrences']} occurrences)")
            print(f"   {suggestion['description']}")

        auto_fixable = len([s for s in suggestions if s["auto_fixable"]])
        manual_required = len(suggestions) - auto_fixable

        print(f"\n🤖 Auto-fixable: {auto_fixable}")
        print(f"👤 Manual action required: {manual_required}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze CI/CD failures and suggest fixes")
    parser.add_argument("log_file", help="Path to CI/CD log file")
    parser.add_argument("--apply-fixes", action="store_true", help="Apply automatic fixes")
    parser.add_argument("--dry-run", action="store_true", help="Show what fixes would be applied")
    parser.add_argument("--export", choices=["json", "yaml", "md"], help="Export report format")
    parser.add_argument("--output", help="Output file path")

    args = parser.parse_args()

    analyzer = CIFailureAnalyzer()

    # Analyze log file
    print(f"🔍 Analyzing log file: {args.log_file}")
    analysis_result = analyzer.analyze_github_actions_log(args.log_file)

    # Generate suggestions
    suggestions = analyzer.generate_fix_suggestions(analysis_result)

    # Print summary
    analyzer.print_analysis_summary(analysis_result, suggestions)

    applied_fixes = []

    # Apply fixes if requested
    if args.apply_fixes or args.dry_run:
        print(f"\n🔧 {'Dry run - showing' if args.dry_run else 'Applying'} automatic fixes...")
        applied_fixes = analyzer.apply_automatic_fixes(suggestions, dry_run=args.dry_run)

    # Generate and export report
    if args.export:
        report = analyzer.generate_report(analysis_result, suggestions, applied_fixes)
        analyzer.export_report(report, args.export, args.output)

    # Exit with appropriate code
    high_severity_issues = len([s for s in suggestions if s["severity"] == "high"])
    if high_severity_issues > 0:
        print(f"\n❌ {high_severity_issues} high severity issues require attention")
        sys.exit(1)
    else:
        print("\n✅ Analysis completed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()
