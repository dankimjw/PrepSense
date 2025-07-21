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
    print(f"{Colors.CYAN}1.{Colors.END} Complete Setup (Install all dependencies)")
    print(f"{Colors.CYAN}2.{Colors.END} Exit")
    print()

def get_user_choice():
    """Get user menu choice"""
    while True:
        try:
            choice = input(f"\n{Colors.BOLD}Enter your choice (1-2): {Colors.END}").strip()
            if choice in ['1', '2']:
                return int(choice)
            else:
                print_error("Please enter 1 or 2")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)
        except:
            print_error("Invalid input. Please enter a number.")

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

def create_api_key_files():
    """Create placeholder API key files if they don't exist"""
    print_header("Creating API Key Files")
    
    config_dir = Path("config")
    if not config_dir.exists():
        config_dir.mkdir(parents=True)
    
    # Create OpenAI key file
    openai_key_file = config_dir / "openai_key.txt"
    if not openai_key_file.exists():
        openai_key_file.write_text("YOUR_OPENAI_API_KEY_HERE")
        print_success("Created config/openai_key.txt (placeholder)")
        print_warning("Please update config/openai_key.txt with your actual OpenAI API key")
    else:
        print_success("config/openai_key.txt already exists")
    
    # Create Spoonacular key file
    spoonacular_key_file = config_dir / "spoonacular_key.txt"
    if not spoonacular_key_file.exists():
        spoonacular_key_file.write_text("YOUR_SPOONACULAR_API_KEY_HERE")
        print_success("Created config/spoonacular_key.txt (placeholder)")
        print_warning("Please update config/spoonacular_key.txt with your actual Spoonacular API key")
    else:
        print_success("config/spoonacular_key.txt already exists")
    
    return True

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist"""
    print_header("Setting Up Python Virtual Environment")
    
    venv_path = Path("venv")
    
    # Check if venv already exists
    if venv_path.exists():
        print_success("Virtual environment already exists")
        return True
    
    # Create virtual environment
    print("Creating virtual environment...")
    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print_success("Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error creating virtual environment: {e}")
        return False

def get_venv_python():
    """Get the path to the Python executable in the virtual environment"""
    if platform.system() == "Windows":
        python_path = Path("venv/Scripts/python.exe")
    else:
        python_path = Path("venv/bin/python")
    
    if python_path.exists():
        return str(python_path)
    else:
        return None

def setup_python_environment():
    """Install Python dependencies in the virtual environment"""
    print_header("Installing Python Dependencies")
    
    # Get venv Python path
    venv_python = get_venv_python()
    
    if not venv_python:
        print_error("Virtual environment Python executable not found!")
        print_info("Please run the setup again to create the virtual environment.")
        return False
    
    print_success(f"Using virtual environment Python: {venv_python}")
    
    # Upgrade pip in the virtual environment
    print("Upgrading pip...")
    if not run_command([venv_python, '-m', 'pip', 'install', '--upgrade', 'pip']):
        print_warning("Failed to upgrade pip, continuing anyway...")
    
    # Install requirements in the virtual environment
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        print("Installing Python dependencies in virtual environment...")
        if not run_command([venv_python, '-m', 'pip', 'install', '-r', 'requirements.txt']):
            return False
        print_success("Python dependencies installed in virtual environment")
    else:
        print_error("requirements.txt not found!")
        return False
    
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

def complete_setup():
    """Complete setup - install all dependencies"""
    print_header("Complete Setup")
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("\nPlease install missing prerequisites and run setup again.")
        return False
    
    print()
    
    # Create virtual environment
    if not create_virtual_environment():
        return False
    
    print()
    
    # Create directories
    if not create_directories():
        return False
    
    print()
    
    # Create API key files
    if not create_api_key_files():
        return False
    
    print()
    
    # Setup Python environment
    if not setup_python_environment():
        return False
    
    print()
    
    # Setup iOS app
    if not setup_ios_app():
        return False
    
    print()
    
    # Final success message
    print_header("Setup Complete!")
    print_success("All dependencies have been installed successfully!")
    
    print(f"\n{Colors.BOLD}IMPORTANT - Manual Setup Required:{Colors.END}")
    print(f"\n1. {Colors.YELLOW}Environment File (.env):{Colors.END}")
    print(f"   - Copy the .env template provided by the team")
    print(f"   - Save it as {Colors.CYAN}.env{Colors.END} in the project root directory")
    print(f"   - Update your {Colors.CYAN}SPOONACULAR_API_KEY{Colors.END}")
    print(f"   - Choose a unique {Colors.CYAN}DEMO_USER_ID{Colors.END} (e.g., john-2, jane-3)")
    
    print(f"\n2. {Colors.YELLOW}API Keys:{Colors.END}")
    print(f"   - Update {Colors.CYAN}config/openai_key.txt{Colors.END} with your OpenAI API key")
    print(f"   - Update {Colors.CYAN}config/spoonacular_key.txt{Colors.END} with your Spoonacular API key")
    print(f"   - API keys should start with 'sk-proj-' or 'sk-' for OpenAI")
    
    print(f"\n3. {Colors.YELLOW}Running the App:{Colors.END}")
    print(f"   - The virtual environment has been created automatically")
    print(f"   - Activate it before running the app:")
    if platform.system() == "Windows":
        print(f"     {Colors.CYAN}.\\venv\\Scripts\\activate{Colors.END}")
    else:
        print(f"     {Colors.CYAN}source venv/bin/activate{Colors.END}")
    print(f"   - Run the app: {Colors.GREEN}python run_app.py{Colors.END}")
    print(f"   - The iOS simulator will launch automatically")
    
    print(f"\n{Colors.YELLOW}Note:{Colors.END} Database credentials are already configured in the .env template.")
    
    return True

def main():
    """Main function"""
    while True:
        show_menu()
        choice = get_user_choice()
        
        if choice == 1:
            success = complete_setup()
            if success:
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
            else:
                print_error("\nSetup failed!")
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
        
        elif choice == 2:
            print("\nExiting setup script. Goodbye!")
            break
        
        else:
            print_error("Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup interrupted. Goodbye!")
        sys.exit(0)