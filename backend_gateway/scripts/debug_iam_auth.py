#!/usr/bin/env python3
"""
Debug IAM authentication issues
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

from google.auth import default
from google.auth.transport.requests import Request

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def debug_credentials():
    """Debug credential issues"""

    print("=== Debugging IAM Authentication ===\n")

    # Check environment
    print("1. Environment Variables:")
    print(
        f"   GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'Not set')}"
    )
    print(f"   GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', 'Not set')}")
    print(f"   Current working directory: {os.getcwd()}")
    print()

    # Check credentials
    print("2. Getting credentials:")
    try:
        credentials, project = default(
            scopes=[
                "https://www.googleapis.com/auth/cloud-platform",
                "https://www.googleapis.com/auth/sqlservice.admin",
            ]
        )
        print(f"   ✓ Got credentials: {type(credentials).__name__}")
        print(f"   ✓ Project: {project}")
        print()

        # Check if credentials have token
        print("3. Token status:")
        print(f"   Has token: {hasattr(credentials, 'token') and credentials.token is not None}")
        print(f"   Token valid: {credentials.valid if hasattr(credentials, 'valid') else 'N/A'}")
        print(f"   Expired: {credentials.expired if hasattr(credentials, 'expired') else 'N/A'}")

        # Try to refresh
        print("\n4. Refreshing token:")
        try:
            credentials.refresh(Request())
            print(f"   ✓ Token refreshed successfully")
            print(f"   Token (first 20 chars): {credentials.token[:20]}...")
        except Exception as e:
            print(f"   ✗ Failed to refresh: {e}")

    except Exception as e:
        print(f"   ✗ Failed to get credentials: {e}")
        print("\n   This might be the issue!")

    # Check ADC file
    print("\n5. ADC File Check:")
    adc_path = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    if os.path.exists(adc_path):
        print(f"   ✓ ADC file exists: {adc_path}")
        import json

        try:
            with open(adc_path, "r") as f:
                adc_data = json.load(f)
                print(f"   Type: {adc_data.get('type', 'unknown')}")
                print(f"   Client ID: {adc_data.get('client_id', 'N/A')[:30]}...")
        except:
            print("   ✗ Could not read ADC file")
    else:
        print(f"   ✗ ADC file not found at: {adc_path}")


if __name__ == "__main__":
    debug_credentials()
