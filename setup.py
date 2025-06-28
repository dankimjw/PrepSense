#!/usr/bin/env python3
"""
PrepSense Automated Setup Script
This script automates the setup process for the PrepSense application.
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
    if not run_command([str(pip_path), "install", "-r", "requirements.txt"]):
        return False
    print_success("Python dependencies installed")
    
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
    """Set up .env file from template"""
    print_header("Setting Up Environment Variables")
    
    env_template = Path(".env.template")
    env_file = Path(".env")
    
    if not env_template.exists():
        print_error(".env.template not found")
        return False
    
    if env_file.exists():
        print_warning(".env file already exists")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("Keeping existing .env file")
            return True
    
    # Copy template to .env
    shutil.copy2(env_template, env_file)
    print_success(".env file created from template")
    
    print(f"\n{Colors.YELLOW}Please edit the .env file and add your API keys:{Colors.END}")
    print(f"  1. Open {Colors.BOLD}.env{Colors.END} in your text editor")
    print(f"  2. Add your OpenAI API key")
    print(f"  3. Add your Google Cloud credentials path")
    print(f"  4. Save the file")
    
    return True

def create_directories():
    """Create necessary directories"""
    print_header("Creating Required Directories")
    
    directories = [
        "config",  # For Google Cloud credentials
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

def print_next_steps():
    """Print next steps for the user"""
    print_header("Setup Complete! 🎉")
    
    print(f"{Colors.BOLD}Next Steps:{Colors.END}")
    print("\n1. Configure your environment variables:")
    print(f"   {Colors.BLUE}Edit .env file with your API keys{Colors.END}")
    
    print("\n2. Add Google Cloud credentials:")
    print(f"   {Colors.BLUE}Place your service account JSON file in the config/ directory{Colors.END}")
    print(f"   {Colors.BLUE}Update GOOGLE_APPLICATION_CREDENTIALS path in .env{Colors.END}")
    
    print("\n3. Start the application:")
    print(f"   {Colors.GREEN}Backend:{Colors.END} python run_app.py")
    print(f"   {Colors.GREEN}iOS App:{Colors.END} python run_ios.py")
    
    print("\n4. Access the services:")
    print(f"   {Colors.BLUE}API Documentation:{Colors.END} http://localhost:8001/docs")
    print(f"   {Colors.BLUE}iOS App:{Colors.END} Scan QR code with Expo Go")
    
    print(f"\n{Colors.BOLD}For more help, see the documentation in docs/{Colors.END}")

def main():
    """Main setup function"""
    print_header("PrepSense Automated Setup")
    print("This script will set up your development environment for PrepSense\n")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("\nPlease install missing prerequisites and run setup again.")
        return 1
    
    # Create directories
    if not create_directories():
        return 1
    
    # Setup Python environment
    if not setup_python_environment():
        print_error("\nPython environment setup failed.")
        return 1
    
    # Setup iOS app
    if not setup_ios_app():
        print_error("\niOS app setup failed.")
        return 1
    
    # Setup environment file
    if not setup_environment_file():
        print_error("\nEnvironment file setup failed.")
        return 1
    
    # Print next steps
    print_next_steps()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())