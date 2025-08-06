#!/usr/bin/env python3
"""Fix CrewAI import issues to get the backend running."""

import os
import re
from pathlib import Path


def fix_nutrient_auditor_imports():
    """Fix the problematic imports in nutrient_auditor_agent.py"""
    print("🔧 Fixing CrewAI import issues...")

    file_path = Path("backend_gateway/agents/nutrient_auditor_agent.py")

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    # Read the file
    with open(file_path, "r") as f:
        content = f.read()

    # Comment out the problematic import
    original_import = "from crewai.flow import Flow, listen, start"
    if original_import in content:
        content = content.replace(
            original_import,
            "# " + original_import + " # Commented out - not available in crewai 0.1.32",
        )
        print("✅ Commented out incompatible crewai.flow import")

    # Also comment out any usage of Flow, listen, start
    content = re.sub(
        r"^(\s*)(.*(?:Flow|listen|start)\(.*\))$",
        r"\1# \2  # Commented out - not available",
        content,
        flags=re.MULTILINE,
    )

    # Write back
    with open(file_path, "w") as f:
        f.write(content)

    print(f"✅ Fixed imports in {file_path}")
    return True


def create_mock_flow_classes():
    """Create mock classes to prevent errors."""
    print("\n📝 Creating mock Flow classes...")

    mock_file = Path("backend_gateway/agents/mock_flow.py")
    mock_content = '''"""Mock classes for CrewAI flow functionality not available in v0.1.32"""

class Flow:
    """Mock Flow class"""
    def __init__(self, *args, **kwargs):
        pass

def listen(*args, **kwargs):
    """Mock listen decorator"""
    def decorator(func):
        return func
    return decorator

def start(*args, **kwargs):
    """Mock start decorator"""
    def decorator(func):
        return func
    return decorator
'''

    with open(mock_file, "w") as f:
        f.write(mock_content)

    print(f"✅ Created mock classes at {mock_file}")
    return True


def update_nutrient_auditor_to_use_mocks():
    """Update the import to use mock classes."""
    file_path = Path("backend_gateway/agents/nutrient_auditor_agent.py")

    with open(file_path, "r") as f:
        lines = f.readlines()

    # Find and update the import line
    for i, line in enumerate(lines):
        if "# from crewai.flow import Flow, listen, start" in line:
            lines.insert(
                i + 1,
                "from .mock_flow import Flow, listen, start  # Using mocks for compatibility\n",
            )
            break

    with open(file_path, "w") as f:
        f.writelines(lines)

    print("✅ Updated to use mock Flow classes")


def check_other_crewai_usage():
    """Check for other potential CrewAI compatibility issues."""
    print("\n🔍 Checking for other CrewAI usage patterns...")

    issues_found = []

    # Search for CrewAI imports in all Python files
    for py_file in Path("backend_gateway").rglob("*.py"):
        with open(py_file, "r") as f:
            content = f.read()

        # Check for newer CrewAI features
        if "from crewai import Process" in content:
            issues_found.append(f"{py_file}: Uses Process (not in v0.1.32)")
        if "from crewai.tools" in content:
            issues_found.append(f"{py_file}: Uses tools module (not in v0.1.32)")
        if "crew.kickoff" in content:
            issues_found.append(f"{py_file}: Uses kickoff method (might not be in v0.1.32)")

    if issues_found:
        print("⚠️  Found potential compatibility issues:")
        for issue in issues_found:
            print(f"   - {issue}")
    else:
        print("✅ No other obvious compatibility issues found")

    return len(issues_found) == 0


def main():
    """Main function to fix all CrewAI issues."""
    print("🚀 CrewAI Import Fixer")
    print("=" * 50)

    # Fix the imports
    if fix_nutrient_auditor_imports():
        create_mock_flow_classes()
        update_nutrient_auditor_to_use_mocks()

    # Check for other issues
    check_other_crewai_usage()

    print("\n✅ Import fixes complete!")
    print("\n📋 Next steps:")
    print("1. Start the backend: source venv/bin/activate && python run_app.py")
    print("2. Test the health endpoint: curl http://localhost:8001/api/v1/health")
    print("3. Test the chat endpoint with: python test_chat_endpoint.py")

    print("\n⚠️  Note: This is a temporary fix. Consider either:")
    print("   - Upgrading to latest CrewAI (0.41+) and implementing proper agents")
    print("   - Removing CrewAI dependency and renaming the services")


if __name__ == "__main__":
    main()
