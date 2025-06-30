#!/usr/bin/env python3
"""
PrepSense Setup Script
This script provides setup options for the PrepSense application.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    """Print a formatted header message"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(message):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_error(message):
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    """Print an info message"""
    print(f"{Colors.CYAN}ℹ {message}{Colors.END}")

def check_command(command):
    """Check if a command is available"""
    return shutil.which(command) is not None

def run_command(command, cwd=None, shell=False):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=shell, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print_error(f"Command failed: {' '.join(command) if isinstance(command, list) else command}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print_error(f"Failed to run command: {e}")
        return False

def show_menu():
    """Display the main menu"""
    print_header("PrepSense Setup Script")
    print(f"{Colors.BOLD}Please select an option:{Colors.END}\n")
    print(f"{Colors.CYAN}1.{Colors.END} Initial Setup (Install dependencies, create directories)")
    print(f"{Colors.CYAN}2.{Colors.END} Setup API Keys (Configure OpenAI and other API keys)")
    print(f"{Colors.CYAN}3.{Colors.END} Show Virtual Environment Activation")
    print(f"{Colors.CYAN}4.{Colors.END} Exit")
    print()

def get_user_choice():
    """Get user menu choice"""
    while True:
        try:
            choice = input(f"{Colors.BOLD}Enter your choice (1-4): {Colors.END}").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print_error("Please enter 1, 2, 3, or 4")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)
        except Exception:
            print_error("Invalid input. Please enter 1, 2, 3, or 4")

def check_prerequisites():
    """Check if all required tools are installed"""
    print_header("Checking Prerequisites")
    
    prerequisites = {
        'python3': 'Python 3.8+',
        'node': 'Node.js',
        'npm': 'npm',
        'git': 'Git'
    }
    
    all_good = True
    for cmd, name in prerequisites.items():
        if check_command(cmd):
            print_success(f"{name} is installed")
        else:
            print_error(f"{name} is not installed")
            all_good = False
    
    # Check Python version
    if check_command('python3'):
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"  Python version: {version}")
        
        # Extract version number
        try:
            version_parts = version.split()[1].split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            if major < 3 or (major == 3 and minor < 8):
                print_error("Python 3.8 or higher is required")
                all_good = False
        except:
            print_warning("Could not verify Python version")
    
    return all_good

def create_directories():
    """Create necessary directories"""
    print_header("Creating Required Directories")
    
    directories = [
        "config",  # For API keys and credentials
        "logs",    # For application logs
        "data"     # For any local data storage
    ]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print_success(f"Created {dir_name}/ directory")
        else:
            print_success(f"{dir_name}/ directory already exists")
    
    return True

def setup_python_environment():
    """Set up Python virtual environment and install dependencies"""
    print_header("Setting Up Python Environment")
    
    venv_path = Path("venv")
    
    # Create virtual environment if it doesn't exist
    if not venv_path.exists():
        print("Creating virtual environment...")
        if not run_command([sys.executable, '-m', 'venv', 'venv']):
            return False
        print_success("Virtual environment created")
    else:
        print_success("Virtual environment already exists")
    
    # Determine pip path based on OS
    if platform.system() == "Windows":
        pip_path = venv_path / "Scripts" / "pip"
    else:
        pip_path = venv_path / "bin" / "pip"
    
    # Upgrade pip
    print("Upgrading pip...")
    run_command([str(pip_path), "install", "--upgrade", "pip"])
    
    # Install requirements
    print("Installing Python dependencies...")
    print_info(f"Using virtual environment pip: {pip_path}")
    if not run_command([str(pip_path), "install", "-r", "requirements.txt"]):
        return False
    print_success("Python dependencies installed in virtual environment")
    
    return True

def setup_ios_app():
    """Set up iOS app dependencies"""
    print_header("Setting Up iOS App")
    
    ios_path = Path("ios-app")
    
    if not ios_path.exists():
        print_error("ios-app directory not found")
        return False
    
    # Install npm dependencies
    print("Installing npm dependencies...")
    if not run_command(["npm", "install"], cwd=ios_path):
        return False
    print_success("npm dependencies installed")
    
    # Check if Expo CLI is installed
    if not check_command('expo'):
        print_warning("Expo CLI not found. Installing globally...")
        if not run_command(["npm", "install", "-g", "expo-cli"], shell=True):
            print_warning("Failed to install Expo CLI globally. You can still use npx expo.")
    else:
        print_success("Expo CLI is installed")
    
    return True

def setup_environment_file():
    """Set up .env file from template and update with GCP credentials if found"""
    print_header("Setting Up Environment File")
    
    env_template = Path(".env.template")
    env_file = Path(".env")
    
    if not env_template.exists():
        print_error(".env.template not found")
        return False
    
    # Determine if we need to create a new .env file
    create_new_env = True
    if env_file.exists():
        print_warning(".env file already exists")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("Keeping existing .env file")
            create_new_env = False
    
    # Create or update .env file
    if create_new_env:
        # Copy template to .env
        shutil.copy2(env_template, env_file)
        print_success(".env file created from template")
    
    # Always check for GCP credentials and update .env if found
    check_google_credentials()
    
    return True

def create_openai_key_file():
    """Create OpenAI key file with placeholder"""
    openai_key_file = Path("config/openai_key.txt")
    
    if not openai_key_file.exists():
        openai_key_file.write_text("your_openai_api_key_here\n")
        print_success("Created config/openai_key.txt placeholder")
    else:
        print_success("config/openai_key.txt already exists")
    
    return True

def initial_setup():
    """Perform initial setup"""
    print_header("Starting Initial Setup")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("\nPlease install missing prerequisites and run setup again.")
        return False
    
    # Create directories
    if not create_directories():
        return False
    
    # Setup environment file
    if not setup_environment_file():
        print_error("\nEnvironment file setup failed.")
        return False
    
    # Create OpenAI key file
    if not create_openai_key_file():
        return False
    
    # Check for Google Cloud credentials after creating config directory
    print(f"\n{Colors.BOLD}Checking for Google Cloud Credentials:{Colors.END}")
    print_info("Looking for service account JSON files...")
    gcp_configured = check_google_credentials()
    if not gcp_configured:
        print_info("You can add Google Cloud credentials later by placing the JSON file in config/ and running setup again")
    
    # Setup Python environment
    if not setup_python_environment():
        print_error("\nPython environment setup failed.")
        return False
    
    # Setup iOS app
    if not setup_ios_app():
        print_error("\niOS app setup failed.")
        return False
    
    print_header("Initial Setup Complete! 🎉")
    print(f"{Colors.BOLD}Dependencies installed in virtual environment!{Colors.END}")
    print(f"{Colors.GREEN}✓ Python packages installed in venv{Colors.END}")
    print(f"{Colors.GREEN}✓ npm packages installed{Colors.END}")
    print(f"{Colors.GREEN}✓ Directories and config files created{Colors.END}")
    
    print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
    print(f"  1. Run option 2 to configure your API keys")
    print(f"  2. {Colors.YELLOW}To run the application, activate the virtual environment:{Colors.END}")
    
    # Show platform-specific activation command
    if platform.system() == "Windows":
        print(f"     {Colors.CYAN}venv\\Scripts\\activate{Colors.END}")
    else:
        print(f"     {Colors.CYAN}source venv/bin/activate{Colors.END}")
    
    print(f"  3. Start the application with: {Colors.GREEN}python run_app.py{Colors.END}")
    
    return True

def show_activation_instructions():
    """Show virtual environment activation instructions"""
    print_header("Virtual Environment Activation")
    
    venv_path = Path("venv")
    if not venv_path.exists():
        print_error("Virtual environment not found!")
        print(f"Please run {Colors.CYAN}option 1 (Initial Setup){Colors.END} first to create the virtual environment.")
        return False
    
    print_success("Virtual environment found!")
    print(f"\n{Colors.BOLD}To activate the virtual environment:{Colors.END}")
    
    if platform.system() == "Windows":
        activation_cmd = "venv\\Scripts\\activate"
        deactivation_cmd = "deactivate"
        print(f"  {Colors.CYAN}{activation_cmd}{Colors.END}")
        print(f"\n{Colors.BOLD}To deactivate later:{Colors.END}")
        print(f"  {Colors.CYAN}{deactivation_cmd}{Colors.END}")
        print(f"\n{Colors.BOLD}Full workflow:{Colors.END}")
        print(f"  1. {Colors.CYAN}{activation_cmd}{Colors.END}")
        print(f"  2. {Colors.GREEN}python run_app.py{Colors.END}")
        print(f"  3. {Colors.CYAN}{deactivation_cmd}{Colors.END} (when done)")
    else:
        activation_cmd = "source venv/bin/activate"
        deactivation_cmd = "deactivate"
        print(f"  {Colors.CYAN}{activation_cmd}{Colors.END}")
        print(f"\n{Colors.BOLD}To deactivate later:{Colors.END}")
        print(f"  {Colors.CYAN}{deactivation_cmd}{Colors.END}")
        print(f"\n{Colors.BOLD}Full workflow:{Colors.END}")
        print(f"  1. {Colors.CYAN}{activation_cmd}{Colors.END}")
        print(f"  2. {Colors.GREEN}python run_app.py{Colors.END}")
        print(f"  3. {Colors.CYAN}{deactivation_cmd}{Colors.END} (when done)")
    
    print(f"\n{Colors.YELLOW}Note:{Colors.END} You need to activate the virtual environment")
    print("each time you open a new terminal to run the application.")
    
    return True

def check_google_credentials():
    """Check for Google Cloud credentials and update .env if needed"""
    config_dir = Path("config")
    env_file = Path(".env")
    
    # Find JSON files in config directory
    json_files = list(config_dir.glob("*.json"))
    print_info(f"Found {len(json_files)} JSON files in config/")
    
    # Filter for Google Cloud service account files
    service_account_files = []
    for f in json_files:
        name_lower = f.name.lower()
        # Skip openai.json and other non-GCP files
        if "openai" in name_lower:
            continue
        # Look for GCP-specific patterns
        if any(pattern in name_lower for pattern in ["service", "gcp", "google", "bigquery", "prep-sense", "adsp"]):
            service_account_files.append(f)
        elif f.name.endswith("-key.json") or "credentials" in name_lower:
            service_account_files.append(f)
    
    if not service_account_files and json_files:
        # If no obvious service account files, show all JSON files and let user choose
        print_warning("Multiple JSON files found. Please specify which is your Google Cloud service account:")
        for i, f in enumerate(json_files, 1):
            if "openai" not in f.name.lower():  # Skip openai.json
                print(f"  {i}. {f.name}")
        
        try:
            choice = input("Enter the number of your service account file (or 0 to skip): ").strip()
            if choice == "0":
                print("Skipping Google Cloud credentials setup")
                return False
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len([f for f in json_files if "openai" not in f.name.lower()]):
                non_openai_files = [f for f in json_files if "openai" not in f.name.lower()]
                service_account_files = [non_openai_files[choice_idx]]
            else:
                print_error("Invalid choice")
                return False
        except (ValueError, KeyboardInterrupt):
            print_error("Invalid input")
            return False
    
    if service_account_files:
        # Use the first service account file found
        credentials_file = service_account_files[0]
        print_success(f"Found Google Cloud credentials: {credentials_file.name}")
        
        # Read current .env content
        env_content = env_file.read_text()
        
        # Update the GOOGLE_APPLICATION_CREDENTIALS line
        new_path = f"config/{credentials_file.name}"
        if "GOOGLE_APPLICATION_CREDENTIALS=" in env_content:
            # Replace existing line
            lines = env_content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("GOOGLE_APPLICATION_CREDENTIALS="):
                    lines[i] = f"GOOGLE_APPLICATION_CREDENTIALS={new_path}"
                    break
            env_content = '\n'.join(lines)
        else:
            # Add new line
            env_content += f"\nGOOGLE_APPLICATION_CREDENTIALS={new_path}\n"
        
        # Write updated content
        env_file.write_text(env_content)
        print_success(f"Updated .env with Google Cloud credentials path")
        return True
    else:
        print_warning("No Google Cloud service account JSON files found in config/")
        print(f"  Place your service account key file in {Colors.CYAN}config/{Colors.END}")
        return False

def setup_api_keys():
    """Setup API keys"""
    print_header("API Key Configuration")
    
    # Check if config directory exists
    config_dir = Path("config")
    if not config_dir.exists():
        print_error("Config directory not found. Please run Initial Setup first.")
        return False
    
    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        print_error(".env file not found. Please run Initial Setup first.")
        return False
    
    # Setup OpenAI API Key
    print(f"{Colors.BOLD}1. OpenAI API Key Setup:{Colors.END}")
    openai_key_file = Path("config/openai_key.txt")
    openai_key_updated = False
    
    # Check current key
    if openai_key_file.exists():
        current_key = openai_key_file.read_text().strip()
        if current_key and current_key != "your_openai_api_key_here":
            print_success("OpenAI key is already configured")
            response = input("Do you want to update it? (y/N): ").lower()
            if response != 'y':
                print("Keeping existing OpenAI key")
            else:
                openai_key_updated = setup_openai_key(openai_key_file)
        else:
            print_warning("OpenAI key is not configured (placeholder found)")
            openai_key_updated = setup_openai_key(openai_key_file)
    else:
        print_warning("OpenAI key file not found, creating it")
        openai_key_file.touch()
        openai_key_updated = setup_openai_key(openai_key_file)
    
    # Always check for Google Cloud Credentials after OpenAI setup
    print(f"\n{Colors.BOLD}2. Google Cloud Credentials Setup:{Colors.END}")
    print_info("Checking for Google Cloud service account files...")
    gcp_updated = check_google_credentials()
    
    if not gcp_updated:
        print_info("To add Google Cloud credentials later:")
        print(f"  1. Download your service account JSON from Google Cloud Console")
        print(f"  2. Place it in the {Colors.CYAN}config/{Colors.END} directory")
        print(f"  3. Run this setup again to auto-detect and configure it")
    
    # Show next steps
    print(f"\n{Colors.BOLD}Setup Complete! Next Steps:{Colors.END}")
    print(f"  1. {Colors.YELLOW}Activate the virtual environment:{Colors.END}")
    
    # Show platform-specific activation command
    if platform.system() == "Windows":
        print(f"     {Colors.CYAN}venv\\Scripts\\activate{Colors.END}")
    else:
        print(f"     {Colors.CYAN}source venv/bin/activate{Colors.END}")
    
    print(f"  2. Start the backend: {Colors.GREEN}python run_app.py{Colors.END}")
    print(f"  3. Start the iOS app: {Colors.GREEN}python run_ios.py{Colors.END}")
    print(f"  4. Access API docs: {Colors.BLUE}http://localhost:8001/docs{Colors.END}")
    
    return True

def setup_openai_key(openai_key_file):
    """Setup OpenAI API key"""
    print(f"Current key file: {Colors.CYAN}{openai_key_file}{Colors.END}")
    
    # Get new key from user
    print(f"\n{Colors.BOLD}Please enter your OpenAI API key:{Colors.END}")
    print("(The key should start with 'sk-proj-' or 'sk-')")
    
    while True:
        try:
            api_key = input("OpenAI API Key: ").strip()
            
            if not api_key:
                print_error("API key cannot be empty")
                continue
            
            if not (api_key.startswith('sk-proj-') or api_key.startswith('sk-')):
                print_warning("API key should start with 'sk-proj-' or 'sk-'")
                response = input("Continue anyway? (y/N): ").lower()
                if response != 'y':
                    continue
            
            # Save the key
            openai_key_file.write_text(api_key + '\n')
            print_success("OpenAI API key saved successfully!")
            break
            
        except KeyboardInterrupt:
            print("\n\nCancelled API key setup")
            return False
        except Exception as e:
            print_error(f"Error saving API key: {e}")
            return False
    
    return True

def main():
    """Main function"""
    while True:
        show_menu()
        choice = get_user_choice()
        
        if choice == 1:
            success = initial_setup()
            if success:
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
            else:
                print_error("\nInitial setup failed!")
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
        
        elif choice == 2:
            success = setup_api_keys()
            if success:
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
            else:
                print_error("\nAPI key setup failed!")
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
        
        elif choice == 3:
            success = show_activation_instructions()
            if success:
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
            else:
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
        
        elif choice == 4:
            print("\nExiting setup script. Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup interrupted. Goodbye!")
        sys.exit(0)