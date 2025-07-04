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
    print(f"{Colors.CYAN}1.{Colors.END} Complete Setup (Dependencies + Google Cloud ADC + OpenAI)")
    print(f"{Colors.CYAN}2.{Colors.END} Configure API Keys Only")
    print(f"{Colors.CYAN}3.{Colors.END} Show Virtual Environment Activation")
    print(f"{Colors.CYAN}4.{Colors.END} Exit")
    print()
    print(f"{Colors.YELLOW}Note:{Colors.END} Option 1 uses Google Cloud ADC (recommended). For JSON keys, see option 2.")
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

def complete_setup():
    """Complete setup with ADC as the default authentication method"""
    print_header("Complete PrepSense Setup")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Step 1: Check prerequisites
    print(f"{Colors.BOLD}Step 1/5: Checking Prerequisites{Colors.END}")
    if not check_prerequisites():
        print_error("\nPlease install missing prerequisites and run setup again.")
        return False
    
    # Step 2: Create directories
    print(f"\n{Colors.BOLD}Step 2/5: Creating Directories{Colors.END}")
    if not create_directories():
        return False
    
    # Step 3: Setup environment file
    print(f"\n{Colors.BOLD}Step 3/5: Setting Up Environment{Colors.END}")
    if not setup_environment_file():
        print_error("\nEnvironment file setup failed.")
        return False
    
    # Create OpenAI key file placeholder
    if not create_openai_key_file():
        return False
    
    # Step 4: Setup Python and iOS dependencies
    print(f"\n{Colors.BOLD}Step 4/5: Installing Dependencies{Colors.END}")
    if not setup_python_environment():
        print_error("\nPython environment setup failed.")
        return False
    
    if not setup_ios_app():
        print_error("\niOS app setup failed.")
        return False
    
    # Step 5: Setup authentication
    print(f"\n{Colors.BOLD}Step 5/5: Setting Up Authentication{Colors.END}")
    
    # Setup OpenAI first
    print(f"\n{Colors.YELLOW}5a. OpenAI API Key:{Colors.END}")
    openai_key_file = Path("config/openai_key.txt")
    if openai_key_file.exists():
        current_key = openai_key_file.read_text().strip()
        if current_key and current_key != "your_openai_api_key_here":
            print_success("OpenAI key is already configured")
        else:
            setup_openai_key(openai_key_file)
    else:
        setup_openai_key(openai_key_file)
    
    # Setup Google Cloud ADC (default)
    print(f"\n{Colors.YELLOW}5b. Google Cloud Authentication (ADC):{Colors.END}")
    print(f"{Colors.GREEN}Using Application Default Credentials (recommended){Colors.END}")
    
    # Check if user wants to use ADC or has existing JSON files
    existing_json = list(Path("config").glob("*.json"))
    gcp_json_files = [f for f in existing_json if "openai" not in f.name.lower()]
    
    if gcp_json_files:
        print_warning(f"Found {len(gcp_json_files)} JSON file(s) in config/")
        print("Would you like to:")
        print(f"  {Colors.CYAN}1.{Colors.END} Use ADC (recommended) - remove JSON files")
        print(f"  {Colors.CYAN}2.{Colors.END} Keep using JSON files (not recommended)")
        
        choice = input("\nYour choice (1/2): ").strip()
        if choice == "2":
            print_info("Keeping existing JSON configuration")
            update_gcp_credentials_in_env()
        else:
            # Setup ADC
            if setup_google_cloud_adc():
                print_success("ADC setup completed!")
                # Suggest removing JSON files
                print(f"\n{Colors.YELLOW}Recommended:{Colors.END} Remove JSON key files from config/")
                print("They're no longer needed with ADC.")
            else:
                print_warning("ADC setup incomplete. You can set it up later with option 2.")
    else:
        # No existing files, go straight to ADC
        if not setup_google_cloud_adc():
            print_warning("ADC setup incomplete. You can set it up later with option 2.")
            print_info("The app will still work if you add JSON files to config/ later.")
    
    # Complete!
    print_header("Setup Complete! 🎉")
    print(f"{Colors.GREEN}✓ All dependencies installed{Colors.END}")
    print(f"{Colors.GREEN}✓ Environment configured{Colors.END}")
    print(f"{Colors.GREEN}✓ Authentication ready{Colors.END}")
    
    print(f"\n{Colors.BOLD}To run the application:{Colors.END}")
    print(f"  1. {Colors.YELLOW}Activate the virtual environment:{Colors.END}")
    if platform.system() == "Windows":
        print(f"     {Colors.CYAN}venv\\Scripts\\activate{Colors.END}")
    else:
        print(f"     {Colors.CYAN}source venv/bin/activate{Colors.END}")
    print(f"  2. {Colors.GREEN}python run_app.py{Colors.END}")
    
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

def update_gcp_credentials_in_env():
    """Automatically update GCP credentials in .env without user interaction"""
    # Define paths
    config_dir = Path("config")
    env_file = Path(".env")
    
    # Find all JSON files in config directory
    json_files = list(config_dir.glob("*.json"))
    
    # Filter out non-GCP files (like openai.json)
    gcp_files = [
        f for f in json_files 
        if not f.name.lower().startswith("openai") and 
           any(pattern in f.name.lower() for pattern in 
               ["service", "gcp", "google", "bigquery", "prep-sense", "adsp", "credentials", "-key.json"])
    ]
    
    if not gcp_files:
        print_warning("No GCP credential files found in config/")
        return False
    
    # Use the first matching file
    gcp_file = gcp_files[0]
    relative_path = f"config/{gcp_file.name}"
    print_success(f"Found GCP credentials file: {gcp_file.name}")
    
    # Read current .env content
    if not env_file.exists():
        print_error("Error: .env file not found")
        return False
    
    env_content = env_file.read_text()
    
    # Update or add GOOGLE_APPLICATION_CREDENTIALS line
    if "GOOGLE_APPLICATION_CREDENTIALS=" in env_content:
        # Update existing line
        lines = env_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith("GOOGLE_APPLICATION_CREDENTIALS="):
                lines[i] = f"GOOGLE_APPLICATION_CREDENTIALS={relative_path}"
                break
        env_content = '\n'.join(lines)
    else:
        # Add new line
        env_content += f"\nGOOGLE_APPLICATION_CREDENTIALS={relative_path}\n"
    
    # Write updated content back to .env
    env_file.write_text(env_content)
    print_success(f"Updated .env with: GOOGLE_APPLICATION_CREDENTIALS={relative_path}")
    return True

def check_google_credentials():
    """Check for Google Cloud credentials and update .env if needed.
    
    This function will:
    1. Look for GCP credentials in common locations and copy to config/ if found
    2. Always update .env with the path to any existing GCP credentials in config/
    """
    config_dir = Path("config")
    env_file = Path(".env")
    
    # First, update .env with any existing GCP credentials in config/
    update_gcp_credentials_in_env()
    
    # Look for GCP credentials in common locations and copy if found
    search_locations = [
        Path.home() / "Downloads",
        Path.home() / "Desktop",
        Path.home() / "Documents",
    ]
    
    # Only add current directory if it's different from the project directory
    if Path.cwd() != Path(__file__).parent:
        search_locations.append(Path.cwd())
    
    gcp_patterns = ["service", "gcp", "google", "bigquery", "prep-sense", "adsp", "credentials"]
    copied_file = None
    
    for location in search_locations:
        if location.exists() and location != config_dir:
            # Look for JSON files that might be GCP credentials
            for json_file in location.glob("*.json"):
                name_lower = json_file.name.lower()
                if any(pattern in name_lower for pattern in gcp_patterns) or name_lower.endswith("-key.json"):
                    print_info(f"Found potential GCP credentials file: {json_file}")
                    response = input(f"Copy {json_file.name} to config directory? (y/N): ").lower()
                    if response == 'y':
                        dest_path = config_dir / json_file.name
                        try:
                            shutil.copy2(json_file, dest_path)
                            print_success(f"Copied {json_file.name} to config/")
                            copied_file = dest_path
                            
                            # Update .env with the new credentials path
                            update_gcp_credentials_in_env()
                            
                            # Add the copied file to json_files since we'll process it next
                            json_files = [dest_path]
                            break
                        except Exception as e:
                            print_error(f"Failed to copy or update: {e}")
                            continue
            if copied_file:
                break
    
    # Find JSON files in config directory if we haven't found any yet
    if not copied_file:
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
        
        # Update the GOOGLE_APPLICATION_CREDENTIALS line with actual filename
        new_path = f"config/{credentials_file.name}"
        if "GOOGLE_APPLICATION_CREDENTIALS=" in env_content:
            # Replace existing line
            lines = env_content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("GOOGLE_APPLICATION_CREDENTIALS="):
                    lines[i] = f"GOOGLE_APPLICATION_CREDENTIALS={new_path}"
                    print_info(f"Updating existing GOOGLE_APPLICATION_CREDENTIALS to: {new_path}")
                    break
            env_content = '\n'.join(lines)
        else:
            # Add new line
            env_content += f"\nGOOGLE_APPLICATION_CREDENTIALS={new_path}\n"
            print_info(f"Adding GOOGLE_APPLICATION_CREDENTIALS: {new_path}")
        
        # Write updated content
        env_file.write_text(env_content)
        print_success(f"Updated .env with Google Cloud credentials path")
        return True
    else:
        # Check if we have any JSON files at all (excluding openai.json)
        non_openai_json = [f for f in json_files if "openai" not in f.name.lower()]
        if non_openai_json:
            print_warning("Found JSON files in config/ but none match Google Cloud service account patterns")
            print_info("Google Cloud service account files typically contain: 'service', 'gcp', 'google', or end with '-key.json'")
            print(f"  Place your service account key file in {Colors.CYAN}config/{Colors.END}")
        elif not copied_file:  # Only show this message if we didn't find any files anywhere
            print_warning("No Google Cloud service account JSON files found")
            print_info("Searched in: Downloads, Desktop, Documents, and current directory")
            print(f"  Download your service account key from Google Cloud Console")
            print(f"  Place it in {Colors.CYAN}config/{Colors.END} or in Downloads/Desktop for auto-detection")
        return False

def setup_api_keys():
    """Setup API keys with option for JSON files"""
    print_header("API Key Configuration")
    
    print(f"{Colors.YELLOW}Note:{Colors.END} For Google Cloud, we recommend using ADC (option 1) instead of JSON files.")
    print(f"This option is primarily for OpenAI keys and legacy JSON file setup.\n")
    
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
        print(f"\n{Colors.YELLOW}Recommended:{Colors.END} Use Application Default Credentials (ADC) instead!")
        print(f"  Run {Colors.CYAN}option 3{Colors.END} to set up ADC - it's more secure and easier for teams")
        print(f"\n{Colors.BOLD}Or, to use a service account key file:{Colors.END}")
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

def setup_google_cloud_adc():
    """Setup Google Cloud Application Default Credentials"""
    print_header("Google Cloud ADC Setup (Recommended)")
    
    print(f"{Colors.BOLD}Application Default Credentials (ADC) Benefits:{Colors.END}")
    print(f"  • {Colors.GREEN}More secure{Colors.END} - No JSON key files to manage")
    print(f"  • {Colors.GREEN}Better for teams{Colors.END} - Each developer uses their own Google account")
    print(f"  • {Colors.GREEN}Automatic{Colors.END} - No need to update .env files")
    print(f"  • {Colors.GREEN}Best practice{Colors.END} - Recommended by Google Cloud")
    
    print(f"\n{Colors.BOLD}Prerequisites:{Colors.END}")
    
    # Check if gcloud is installed
    if not check_command('gcloud'):
        print_error("Google Cloud SDK is not installed")
        print(f"\n{Colors.BOLD}To install Google Cloud SDK:{Colors.END}")
        if platform.system() == "Darwin":  # macOS
            print(f"  {Colors.CYAN}brew install google-cloud-sdk{Colors.END}")
        elif platform.system() == "Windows":
            print(f"  Download from: {Colors.BLUE}https://cloud.google.com/sdk/docs/install{Colors.END}")
        else:  # Linux
            print(f"  {Colors.CYAN}curl https://sdk.cloud.google.com | bash{Colors.END}")
        print(f"\nAfter installing, run this setup option again.")
        return False
    else:
        print_success("Google Cloud SDK is installed")
    
    # Check current authentication status
    print(f"\n{Colors.BOLD}Checking current authentication:{Colors.END}")
    
    # Check gcloud auth list
    result = subprocess.run(['gcloud', 'auth', 'list'], capture_output=True, text=True)
    if result.returncode == 0:
        print_info("Current authenticated accounts:")
        print(result.stdout)
    
    # Setup steps
    print(f"\n{Colors.BOLD}Setup Steps:{Colors.END}")
    print(f"\n1. {Colors.YELLOW}First, login to your Google account:{Colors.END}")
    print(f"   {Colors.CYAN}gcloud auth login{Colors.END}")
    
    response = input("\nHave you completed this step? (y/N): ").lower()
    if response != 'y':
        print_info("Please run the command above and try again")
        return False
    
    print(f"\n2. {Colors.YELLOW}Now, set up Application Default Credentials:{Colors.END}")
    print(f"   {Colors.CYAN}gcloud auth application-default login{Colors.END}")
    print_info("This will open a browser window for authentication")
    
    response = input("\nReady to proceed? (y/N): ").lower()
    if response == 'y':
        # Run the ADC login command
        result = run_command(['gcloud', 'auth', 'application-default', 'login'])
        if result:
            print_success("ADC setup completed successfully!")
        else:
            print_error("ADC setup failed. Please try running the command manually.")
            return False
    else:
        print_info("Please run the command manually when ready")
        return False
    
    print(f"\n3. {Colors.YELLOW}Set the default project:{Colors.END}")
    print(f"   {Colors.CYAN}gcloud config set project adsp-34002-on02-prep-sense{Colors.END}")
    
    result = run_command(['gcloud', 'config', 'set', 'project', 'adsp-34002-on02-prep-sense'])
    if result:
        print_success("Project set successfully!")
    
    # Update .env to comment out GOOGLE_APPLICATION_CREDENTIALS
    print(f"\n{Colors.BOLD}Updating .env configuration:{Colors.END}")
    env_file = Path(".env")
    if env_file.exists():
        env_content = env_file.read_text()
        lines = env_content.split('\n')
        updated = False
        
        for i, line in enumerate(lines):
            if line.strip().startswith("GOOGLE_APPLICATION_CREDENTIALS=") and not line.strip().startswith("#"):
                lines[i] = f"# {line}  # Commented out - using ADC instead"
                updated = True
                print_success("Commented out GOOGLE_APPLICATION_CREDENTIALS in .env")
                break
        
        if updated:
            env_file.write_text('\n'.join(lines))
    
    # Test the setup
    print(f"\n{Colors.BOLD}Testing ADC setup:{Colors.END}")
    test_script = '''
from google.cloud import bigquery
try:
    client = bigquery.Client()
    print("✓ ADC is working correctly!")
    print(f"  Project: {client.project}")
except Exception as e:
    print(f"✗ ADC test failed: {e}")
'''
    
    # Write test script to temporary file
    test_file = Path("test_adc.py")
    test_file.write_text(test_script)
    
    # Run test with virtual environment python if it exists
    venv_python = Path("venv/bin/python") if platform.system() != "Windows" else Path("venv/Scripts/python.exe")
    if venv_python.exists():
        result = run_command([str(venv_python), "test_adc.py"])
    else:
        result = run_command([sys.executable, "test_adc.py"])
    
    # Clean up test file
    test_file.unlink()
    
    if result:
        print(f"\n{Colors.GREEN}{Colors.BOLD}ADC Setup Complete!{Colors.END}")
        print(f"\n{Colors.BOLD}Your app will now use ADC automatically.{Colors.END}")
        print(f"No JSON key files needed!")
        print(f"\n{Colors.BOLD}Next steps:{Colors.END}")
        print(f"  1. Make sure all team members run the same ADC setup")
        print(f"  2. Remove any JSON key files from the config/ directory")
        print(f"  3. Never commit credential files to Git")
        return True
    else:
        print_error("\nADC test failed. Please check your setup and try again.")
        print_info("Make sure you have the necessary BigQuery permissions.")
        return False

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
            success = complete_setup()
            if success:
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
            else:
                print_error("\nSetup failed!")
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