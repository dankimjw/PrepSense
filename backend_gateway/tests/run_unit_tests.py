#!/usr/bin/env python
"""
Run unit tests for service clients without loading the full app configuration.
This allows testing API client wrappers in isolation.
"""
import sys
import os
import unittest

# Set test environment variables before any imports
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "postgresql://test@localhost/test_db"
os.environ["POSTGRES_PASSWORD"] = "test_password_123"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_DATABASE"] = "test_db"
os.environ["POSTGRES_USER"] = "test"
os.environ["OPENAI_API_KEY"] = "test-key-123"
os.environ["SPOONACULAR_API_KEY"] = "test-spoon-key"
os.environ["UNSPLASH_ACCESS_KEY"] = "test-unsplash-key"
os.environ["GCP_PROJECT_ID"] = "test-project"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "test-credentials.json"

# Add backend_gateway to path
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_path)

# Import and run the test
from test_spoonacular_client import TestSpoonacularClient

if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSpoonacularClient)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)