#!/usr/bin/env python3
"""
Comprehensive setup verification script for PrepSense.
Checks all dependencies, configurations, and connections after running setup.py.
"""

import importlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path


# Colors for output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    END = "\033[0m"
    BOLD = "\033[1m"


def print_header(message: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ {message}{Colors.END}")


def check_python_environment() -> dict[str, bool]:
    """Check Python environment setup."""
    print_header("Python Environment")
    results = {}

    # Check Python version
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python version: {version.major}.{version.minor}.{version.micro}")
        results["python_version"] = True
    else:
        print_error(f"Python {version.major}.{version.minor} - Need 3.8+")
        results["python_version"] = False

    # Check virtual environment
    if sys.prefix != sys.base_prefix:
        print_success("Running in virtual environment")
        print_info(f"Virtual env: {sys.prefix}")
        results["virtual_env"] = True
    else:
        print_error("Not running in virtual environment")
        print_info("Run: source venv/bin/activate")
        results["virtual_env"] = False

    # Check requirements.txt exists
    req_file = Path("requirements.txt")
    if req_file.exists():
        print_success("requirements.txt found")
        results["requirements_file"] = True
    else:
        print_error("requirements.txt not found")
        results["requirements_file"] = False

    return results


def check_python_dependencies() -> dict[str, bool]:
    """Check if all Python dependencies are installed."""
    print_header("Python Dependencies")
    results = {}

    critical_packages = [
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("sqlalchemy", "Database ORM"),
        ("psycopg2", "PostgreSQL adapter"),
        ("google-cloud-bigquery", "BigQuery client"),
        ("google-cloud-sql-connector", "Cloud SQL connector"),
        ("openai", "OpenAI API client"),
        ("httpx", "HTTP client"),
        ("pydantic", "Data validation"),
        ("python-dotenv", "Environment variables"),
        ("crewai", "CrewAI framework"),
        ("langchain", "LangChain framework"),
    ]

    missing_packages = []

    for package, description in critical_packages:
        try:
            if package == "psycopg2":
                # Special handling for psycopg2
                try:
                    importlib.import_module("psycopg2")
                    print_success(f"{description} ({package})")
                    results[package] = True
                except:
                    try:
                        importlib.import_module("psycopg2_binary")
                        print_success(f"{description} (psycopg2-binary)")
                        results[package] = True
                    except:
                        print_error(f"{description} ({package})")
                        missing_packages.append(package)
                        results[package] = False
            else:
                importlib.import_module(package.replace("-", "_"))
                print_success(f"{description} ({package})")
                results[package] = True
        except ImportError:
            print_error(f"{description} ({package})")
            missing_packages.append(package)
            results[package] = False

    if missing_packages:
        print_warning(f"\nMissing packages: {', '.join(missing_packages)}")
        print_info("Run: pip install -r requirements.txt")

    return results


def check_nodejs_environment() -> dict[str, bool]:
    """Check Node.js and npm setup."""
    print_header("Node.js Environment")
    results = {}

    # Check Node.js
    try:
        node_version = subprocess.run(["node", "--version"], check=False, capture_output=True, text=True)
        if node_version.returncode == 0:
            print_success(f"Node.js installed: {node_version.stdout.strip()}")
            results["nodejs"] = True
        else:
            print_error("Node.js not found")
            results["nodejs"] = False
    except FileNotFoundError:
        print_error("Node.js not installed")
        results["nodejs"] = False

    # Check npm
    try:
        npm_version = subprocess.run(["npm", "--version"], check=False, capture_output=True, text=True)
        if npm_version.returncode == 0:
            print_success(f"npm installed: {npm_version.stdout.strip()}")
            results["npm"] = True
        else:
            print_error("npm not found")
            results["npm"] = False
    except FileNotFoundError:
        print_error("npm not installed")
        results["npm"] = False

    # Check package.json
    package_json = Path("ios-app/package.json")
    if package_json.exists():
        print_success("ios-app/package.json found")
        results["package_json"] = True

        # Check node_modules
        node_modules = Path("ios-app/node_modules")
        if node_modules.exists() and node_modules.is_dir():
            # Count packages
            package_count = len(list(node_modules.iterdir()))
            print_success(f"node_modules exists ({package_count} packages)")
            results["node_modules"] = True
        else:
            print_error("node_modules not found")
            print_info("Run: cd ios-app && npm install")
            results["node_modules"] = False
    else:
        print_error("ios-app/package.json not found")
        results["package_json"] = False
        results["node_modules"] = False

    return results


def check_npm_dependencies() -> dict[str, bool]:
    """Check critical npm dependencies."""
    print_header("NPM Dependencies")
    results = {}

    ios_app_path = Path("ios-app")
    if not ios_app_path.exists():
        print_error("ios-app directory not found")
        return {"ios_app": False}

    package_json_path = ios_app_path / "package.json"
    if not package_json_path.exists():
        print_error("package.json not found")
        return {"package_json": False}

    # Read package.json
    with open(package_json_path) as f:
        package_data = json.load(f)

    critical_deps = [
        "expo",
        "react",
        "react-native",
        "@react-navigation/native",
        "axios",
        "expo-router",
    ]

    dependencies = package_data.get("dependencies", {})

    for dep in critical_deps:
        if dep in dependencies:
            print_success(f"{dep}: {dependencies[dep]}")
            results[dep] = True
        else:
            print_error(f"{dep} not in package.json")
            results[dep] = False

    # Check if dependencies are actually installed
    node_modules = ios_app_path / "node_modules"
    if node_modules.exists():
        for dep in critical_deps:
            dep_path = node_modules / dep
            if dep_path.exists():
                results[f"{dep}_installed"] = True
            else:
                print_warning(f"{dep} not installed in node_modules")
                results[f"{dep}_installed"] = False

    return results


def check_environment_files() -> dict[str, bool]:
    """Check environment configuration files."""
    print_header("Environment Configuration")
    results = {}

    # Check .env file
    env_file = Path(".env")
    if env_file.exists():
        print_success(".env file exists")
        results["env_file"] = True

        # Read and check critical variables
        env_vars = {}
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

        critical_vars = [
            "POSTGRES_HOST",
            "POSTGRES_DATABASE",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "GCP_PROJECT_ID",
            "SPOONACULAR_API_KEY",
            "UNSPLASH_ACCESS_KEY",
        ]

        print_info("\nChecking critical environment variables:")
        for var in critical_vars:
            if var in env_vars and env_vars[var]:
                # Don't show actual values for security
                if "PASSWORD" in var or "KEY" in var:
                    print_success(f"{var}: ****** (set)")
                else:
                    print_success(f"{var}: {env_vars[var]}")
                results[f"env_{var}"] = True
            else:
                print_error(f"{var}: not set")
                results[f"env_{var}"] = False

        # Check for Google credentials
        if "GOOGLE_APPLICATION_CREDENTIALS" in env_vars:
            cred_path = env_vars["GOOGLE_APPLICATION_CREDENTIALS"]
            if not cred_path.startswith("#"):
                print_info(f"\nGoogle credentials path: {cred_path}")
                if Path(cred_path).exists():
                    print_success("Google credentials file exists")
                    results["google_creds_file"] = True
                else:
                    print_error("Google credentials file not found")
                    results["google_creds_file"] = False
            else:
                print_info("Using Application Default Credentials (ADC)")
                results["google_creds_adc"] = True

        # Check OpenAI key file
        openai_key_file = Path("config/openai_key.txt")
        if openai_key_file.exists():
            key_content = openai_key_file.read_text().strip()
            if key_content and key_content != "your_openai_api_key_here":
                print_success("OpenAI key file configured")
                results["openai_key_file"] = True
            else:
                print_warning("OpenAI key file contains placeholder")
                results["openai_key_file"] = False
        else:
            print_error("config/openai_key.txt not found")
            results["openai_key_file"] = False

    else:
        print_error(".env file not found")
        print_info("Run: python setup.py")
        results["env_file"] = False

    return results


def check_directory_structure() -> dict[str, bool]:
    """Check required directory structure."""
    print_header("Directory Structure")
    results = {}

    required_dirs = [
        ("backend_gateway", "Backend API code"),
        ("backend_gateway/routers", "API routers"),
        ("backend_gateway/services", "Business logic"),
        ("backend_gateway/schemas", "Data models"),
        ("backend_gateway/tests", "Backend tests"),
        ("ios-app", "iOS application"),
        ("ios-app/app", "App screens"),
        ("ios-app/components", "React components"),
        ("config", "Configuration files"),
        ("logs", "Application logs"),
        ("docs", "Documentation"),
        ("venv", "Python virtual environment"),
    ]

    for dir_path, description in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print_success(f"{description} ({dir_path}/)")
            results[dir_path] = True
        else:
            print_error(f"{description} ({dir_path}/) - missing")
            results[dir_path] = False

    return results


def check_backend_connectivity() -> dict[str, bool]:
    """Check if backend can be started and is accessible."""
    print_header("Backend Connectivity")
    results = {}

    # Check if port 8001 is available
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port_available = sock.connect_ex(("localhost", 8001)) != 0
    sock.close()

    if port_available:
        print_success("Port 8001 is available")
        results["port_8001"] = True
    else:
        print_warning("Port 8001 is in use")
        print_info("Backend might already be running")
        results["port_8001"] = False

    # Check if backend module can be imported
    try:
        sys.path.insert(0, str(Path.cwd()))

        print_success("Backend app module can be imported")
        results["backend_import"] = True
    except Exception as e:
        print_error(f"Cannot import backend app: {str(e)}")
        results["backend_import"] = False

    return results


def check_database_configuration() -> dict[str, bool]:
    """Check database configuration."""
    print_header("Database Configuration")
    results = {}

    # Check environment variables
    db_vars = {
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST"),
        "POSTGRES_DATABASE": os.getenv("POSTGRES_DATABASE"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID"),
    }

    all_set = True
    for var, value in db_vars.items():
        if value:
            if "PASSWORD" in var:
                print_success(f"{var}: ****** (set)")
            else:
                print_success(f"{var}: {value}")
            results[f"db_{var}"] = True
        else:
            print_error(f"{var}: not set")
            results[f"db_{var}"] = False
            all_set = False

    if all_set:
        print_info("\nDatabase is configured for Google Cloud SQL")
        print_warning("Note: Actual connection test requires valid credentials")
    else:
        print_error("\nDatabase configuration incomplete")

    return results


def check_api_integrations() -> dict[str, bool]:
    """Check external API configurations."""
    print_header("External API Integrations")
    results = {}

    # Check Spoonacular
    spoon_key = os.getenv("SPOONACULAR_API_KEY")
    if spoon_key and spoon_key != "your_spoonacular_api_key_here":
        print_success("Spoonacular API key configured")
        results["spoonacular"] = True
    else:
        print_warning("Spoonacular API key not configured")
        results["spoonacular"] = False

    # Check Unsplash
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if unsplash_key and unsplash_key != "your_unsplash_access_key_here":
        print_success("Unsplash API key configured")
        results["unsplash"] = True
    else:
        print_warning("Unsplash API key not configured")
        results["unsplash"] = False

    # Check OpenAI
    openai_key_file = Path("config/openai_key.txt")
    if openai_key_file.exists():
        key_content = openai_key_file.read_text().strip()
        if key_content and key_content != "your_openai_api_key_here":
            print_success("OpenAI API key configured")
            results["openai"] = True
        else:
            print_warning("OpenAI API key not configured")
            results["openai"] = False
    else:
        print_error("OpenAI key file missing")
        results["openai"] = False

    return results


def generate_summary(all_results: dict[str, dict[str, bool]]) -> None:
    """Generate a summary of all checks."""
    print_header("Setup Verification Summary")

    total_checks = 0
    passed_checks = 0

    for category, results in all_results.items():
        category_passed = sum(1 for v in results.values() if v)
        category_total = len(results)
        total_checks += category_total
        passed_checks += category_passed

        if category_passed == category_total:
            print_success(f"{category}: {category_passed}/{category_total} checks passed")
        elif category_passed > 0:
            print_warning(f"{category}: {category_passed}/{category_total} checks passed")
        else:
            print_error(f"{category}: {category_passed}/{category_total} checks passed")

    print(f"\n{Colors.BOLD}Overall: {passed_checks}/{total_checks} checks passed{Colors.END}")

    if passed_checks == total_checks:
        print(
            f"\n{Colors.GREEN}{Colors.BOLD}✨ Setup is complete! Ready to run the application.{Colors.END}"
        )
        print(f"\n{Colors.BOLD}To start:{Colors.END}")
        print(f"1. Activate virtual environment: {Colors.CYAN}source venv/bin/activate{Colors.END}")
        print(f"2. Run application: {Colors.GREEN}python run_app.py{Colors.END}")
    else:
        print(
            f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Some checks failed. Please address the issues above.{Colors.END}"
        )
        print(f"\n{Colors.BOLD}Recommended actions:{Colors.END}")

        # Provide specific recommendations
        if not all_results.get("Python Environment", {}).get("virtual_env", False):
            print(
                f"• Create/activate virtual environment: {Colors.CYAN}source venv/bin/activate{Colors.END}"
            )

        if not all_results.get("Python Dependencies", {}).get("fastapi", False):
            print(
                f"• Install Python dependencies: {Colors.CYAN}pip install -r requirements.txt{Colors.END}"
            )

        if not all_results.get("NPM Dependencies", {}).get("node_modules", False):
            print(f"• Install npm dependencies: {Colors.CYAN}cd ios-app && npm install{Colors.END}")

        if not all_results.get("Environment Configuration", {}).get("env_file", False):
            print(f"• Run setup script: {Colors.CYAN}python setup.py{Colors.END}")


def main():
    """Main verification function."""
    print(f"{Colors.BOLD}{Colors.CYAN}PrepSense Setup Verification Script{Colors.END}")
    print("This script verifies your PrepSense installation\n")

    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    all_results = {}

    # Run all checks
    all_results["Python Environment"] = check_python_environment()
    all_results["Python Dependencies"] = check_python_dependencies()
    all_results["Node.js Environment"] = check_nodejs_environment()

    # Only check npm dependencies if Node.js is available
    if all_results["Node.js Environment"].get("npm", False):
        all_results["NPM Dependencies"] = check_npm_dependencies()

    all_results["Directory Structure"] = check_directory_structure()
    all_results["Environment Configuration"] = check_environment_files()
    all_results["Database Configuration"] = check_database_configuration()
    all_results["API Integrations"] = check_api_integrations()
    all_results["Backend Connectivity"] = check_backend_connectivity()

    # Generate summary
    generate_summary(all_results)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVerification interrupted.")
    except Exception as e:
        print(f"\n{Colors.RED}Error during verification: {e}{Colors.END}")
        import traceback

        traceback.print_exc()
