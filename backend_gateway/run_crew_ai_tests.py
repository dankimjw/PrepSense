#!/usr/bin/env python3
"""
Standalone test runner for CrewAI tests
Runs without requiring testcontainers or other complex dependencies
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Import the tests
from tests.services.test_crew_ai_multi_agent import (
    TestCrewAITools,
    TestCrewAIAgents,
    TestMultiAgentCrewAIService,
    TestIntegration
)


def mock_dependencies():
    """Mock all external dependencies"""
    # Mock database
    with patch('backend_gateway.config.database.get_database_service'):
        # Mock Spoonacular
        with patch('backend_gateway.services.spoonacular_service.SpoonacularService'):
            # Mock CrewAI imports
            with patch('backend_gateway.services.crew_ai_multi_agent.Crew'):
                with patch('backend_gateway.services.crew_ai_multi_agent.Process'):
                    yield


def run_tests():
    """Run all CrewAI tests"""
    print("Running CrewAI Multi-Agent Tests...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCrewAITools))
    suite.addTests(loader.loadTestsFromTestCase(TestCrewAIAgents))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiAgentCrewAIService))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    with mock_dependencies():
        result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)