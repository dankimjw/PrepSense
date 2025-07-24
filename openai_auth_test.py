"""Simple authentication test for OpenAI API key.

Usage:
    python openai_auth_test.py --api-key YOUR_KEY
    python openai_auth_test.py               # uses OPENAI_API_KEY env var

Exit code 0 on success, 1 on auth failure or network error.
"""
import argparse
import os
import sys
from openai import OpenAI, AuthenticationError, APIConnectionError, APIError


def main() -> int:  # return status
    parser = argparse.ArgumentParser(description="Validate OpenAI API key authentication")
    parser.add_argument("--api-key", help="OpenAI API key (overrides env var)")

    args = parser.parse_args()

    if args.api_key:
        api_key = args.api_key
    else:
        # fall back to project helper to load from env or key file
        try:
            from backend_gateway.core.config_utils import get_openai_api_key
            api_key = get_openai_api_key()
        except Exception:
            api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: No API key provided (use --api-key or set OPENAI_API_KEY)")
        return 1

    try:
        client = OpenAI(api_key=api_key)
        # Cheapest call that still validates auth – list models is free
        client.models.list()
        print("AUTH OK: OpenAI key valid and reachable")
        return 0
    except AuthenticationError as e:
        print(f"AUTH FAILED: {e}")
    except (APIConnectionError, APIError) as e:
        print(f"OPENAI ERROR: {e}")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
