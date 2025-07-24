# Key_Loader.py
import os
from pathlib import Path
from dotenv import load_dotenv

def load_openai_key_from_file(project_root: Path) -> None:
    """
    If OPENAI_API_KEY isn’t set but OPENAI_API_KEY_FILE points at a file
    under <project_root>/config, read it, inject it into os.environ,
    and rewrite .env so you never have a FILE=… reference again.
    """
    # 1) Load whatever’s in .env already (don’t override existing keys)
    load_dotenv(dotenv_path=project_root / ".env", override=False)

    key_file = os.getenv("OPENAI_API_KEY_FILE")
    if not key_file or os.getenv("OPENAI_API_KEY"):
        return

    # 2) Resolve relative → project_root/config/openai_key.txt
    key_path = Path(key_file)
    if not key_path.is_absolute():
        key_path = project_root / key_file

    if not key_path.is_file():
        print(f"Warning: key file {key_path!s} not found")
        return

    secret = key_path.read_text().strip()
    if not secret:
        print(f"Warning: key file {key_path!s} is empty")
        return

    # 3) Inject into current process
    os.environ["OPENAI_API_KEY"] = secret
    print(f"Loaded OpenAI API key from {key_path!s}")

    # 4) Persist back to .env
    env_path = project_root / ".env"
    if env_path.exists():
        lines = env_path.read_text().splitlines()
        # drop any old FILE= or direct-key lines
        lines = [
            l for l in lines
            if not l.startswith("OPENAI_API_KEY_FILE=")
            and not l.startswith("OPENAI_API_KEY=")
        ]
        lines.append(f"OPENAI_API_KEY={secret}")
        env_path.write_text("\n".join(lines) + "\n")
        print("Rewrote .env → OPENAI_API_KEY with actual key")

        # reload so .env changes take effect immediately
        from dotenv import load_dotenv as _reload
        _reload(dotenv_path=env_path, override=True)
