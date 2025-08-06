#!/usr/bin/env python3
"""
Run specific CrewAI tests without pytest dependencies
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch

# Temporarily rename conftest.py to avoid import issues
conftest_path = "tests/conftest.py"
conftest_backup = "tests/conftest.py.bak"

if os.path.exists(conftest_path):
    os.rename(conftest_path, conftest_backup)

try:
    # Import test modules directly
    from tests.services.test_crew_ai_multi_agent import (
        TestCrewAIAgents,
        TestCrewAITools,
        TestIntegration,
        TestMultiAgentCrewAIService,
    )

    print("Running CrewAI Unit Tests")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Run tool tests
    print("\n1. Testing CrewAI Tools...")
    tool_suite = loader.loadTestsFromTestCase(TestCrewAITools)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(tool_suite)

    print(
        f"\nTool Tests - Passed: {result.testsRun - len(result.failures) - len(result.errors)}, Failed: {len(result.failures) + len(result.errors)}"
    )

    # Run agent tests
    print("\n2. Testing CrewAI Agents...")
    agent_suite = loader.loadTestsFromTestCase(TestCrewAIAgents)
    result = runner.run(agent_suite)

    print(
        f"\nAgent Tests - Passed: {result.testsRun - len(result.failures) - len(result.errors)}, Failed: {len(result.failures) + len(result.errors)}"
    )

    # Run service tests
    print("\n3. Testing MultiAgentCrewAIService...")
    service_suite = loader.loadTestsFromTestCase(TestMultiAgentCrewAIService)

    # Mock the async environment
    def run_async_tests(test_case):
        """Helper to run async tests"""
        test_methods = [method for method in dir(test_case) if method.startswith("test_")]
        for method_name in test_methods:
            method = getattr(test_case, method_name)
            if asyncio.iscoroutinefunction(method):
                try:
                    asyncio.run(method())
                    print(f"✓ {method_name}")
                except Exception as e:
                    print(f"✗ {method_name}: {e}")
            else:
                try:
                    method()
                    print(f"✓ {method_name}")
                except Exception as e:
                    print(f"✗ {method_name}: {e}")

    # Run integration tests
    print("\n4. Testing Integration...")
    integration_suite = loader.loadTestsFromTestCase(TestIntegration)
    result = runner.run(integration_suite)

    print("\n" + "=" * 60)
    print("All CrewAI Tests Complete!")

finally:
    # Restore conftest.py
    if os.path.exists(conftest_backup):
        os.rename(conftest_backup, conftest_path)
