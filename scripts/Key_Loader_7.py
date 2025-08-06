# Key_Loader_7.py
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def validate_openai_key(api_key: str) -> bool:
    """Validate OpenAI API key by making a minimal API call."""
    try:
        client = OpenAI(api_key=api_key)
        # Make a minimal API call to validate the key
        response = client.models.list()
        # If we get here, the key is valid
        return True
    except Exception as e:
        print(f"API key validation failed: {e}")
        return False


def load_openai_key_from_file(project_root: Path) -> None:
    """
    Handle OpenAI API key loading with proper validation and cycling logic:

    1. If OPENAI_API_KEY exists in env, validate it:
       - If valid: use it
       - If invalid: replace with OPENAI_API_KEY_FILE=config/openai_key.txt

    2. If OPENAI_API_KEY_FILE exists:
       - Read the key from the file
       - Validate the key
       - If valid: replace OPENAI_API_KEY_FILE with OPENAI_API_KEY in .env
       - If invalid: keep OPENAI_API_KEY_FILE in .env

    Never comment out keys. Prevent any commenting of API keys.
    """
    # Load .env without overriding existing environment
    env_path = project_root / ".env"
    load_dotenv(dotenv_path=env_path, override=False)

    # Check if we have a direct API key
    current_key = os.getenv("OPENAI_API_KEY")
    key_file = os.getenv("OPENAI_API_KEY_FILE")

    if current_key:
        # We have a direct key, validate it
        print("Found OPENAI_API_KEY in environment, validating...")
        if validate_openai_key(current_key):
            print("✅ OPENAI_API_KEY is valid")
            # Ensure the key is never commented out in .env
            ensure_key_not_commented(env_path)
            return
        else:
            print("❌ OPENAI_API_KEY is invalid, reverting to file reference")
            # Replace invalid key with file reference
            update_env_file(env_path, use_file_reference=True)
            # Clear the invalid key from current environment
            os.environ.pop("OPENAI_API_KEY", None)
            # Set the file reference
            os.environ["OPENAI_API_KEY_FILE"] = "config/openai_key.txt"
            key_file = "config/openai_key.txt"

    # At this point, we should have OPENAI_API_KEY_FILE
    if not key_file:
        print("Warning: No OPENAI_API_KEY or OPENAI_API_KEY_FILE found")
        return

    # Resolve the key file path
    key_path = Path(key_file)
    if not key_path.is_absolute():
        key_path = project_root / key_file

    if not key_path.is_file():
        print(f"Warning: Key file {key_path} not found")
        return

    # Read the key from file
    try:
        file_key = key_path.read_text().strip()
        if not file_key:
            print(f"Warning: Key file {key_path} is empty")
            return

        print(f"Found key in {key_path}, validating...")
        if validate_openai_key(file_key):
            print("✅ Key from file is valid, updating .env")
            # Valid key - replace OPENAI_API_KEY_FILE with OPENAI_API_KEY
            os.environ["OPENAI_API_KEY"] = file_key
            update_env_file(env_path, use_file_reference=False, api_key=file_key)
            # Reload to ensure consistency
            load_dotenv(dotenv_path=env_path, override=True)
        else:
            print("❌ Key from file is invalid, keeping file reference")
            # Invalid key - keep the file reference
            os.environ["OPENAI_API_KEY_FILE"] = str(key_file)

    except Exception as e:
        print(f"Error reading key file: {e}")


def update_env_file(env_path: Path, use_file_reference: bool, api_key: str = None) -> None:
    """Update .env file with either file reference or direct key."""
    if not env_path.exists():
        return

    lines = env_path.read_text().splitlines()
    new_lines = []
    key_added = False

    for line in lines:
        # Skip any OPENAI_API_KEY related lines (including commented ones)
        if line.strip().startswith("OPENAI_API_KEY") or line.strip().startswith("# OPENAI_API_KEY"):
            continue
        new_lines.append(line)

    # Add the appropriate line
    if use_file_reference:
        new_lines.append("OPENAI_API_KEY_FILE=config/openai_key.txt")
    else:
        new_lines.append(f"OPENAI_API_KEY={api_key}")

    # Write back
    env_path.write_text("\n".join(new_lines) + "\n")


def ensure_key_not_commented(env_path: Path) -> None:
    """Ensure OPENAI_API_KEY is never commented out in .env file."""
    if not env_path.exists():
        return

    content = env_path.read_text()
    lines = content.splitlines()
    modified = False

    for i, line in enumerate(lines):
        # Check if OPENAI_API_KEY is commented
        if line.strip().startswith("# OPENAI_API_KEY="):
            print("⚠️  Found commented OPENAI_API_KEY, uncommenting...")
            lines[i] = line.lstrip("# ")
            modified = True

    if modified:
        env_path.write_text("\n".join(lines) + "\n")
        print("✅ Uncommented OPENAI_API_KEY in .env")
