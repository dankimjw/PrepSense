#!/bin/bash
# Run all PrepSense tests

echo "🧪 Running PrepSense Test Suite"
echo "=============================="

echo -e "\n📋 Test 1: Recipe Completion (Minimal)"
python test_recipe_completion_minimal.py

echo -e "\n📋 Test 2: Edge Cases"
python test_recipe_edge_cases.py

echo -e "\n📋 Test 3: CrewAI Preferences"
python test_crew_ai_preferences.py

echo -e "\n📋 Test 4: Integration Test (Automated)"
python test_integration_full_workflow.py --auto

echo -e "\n✅ All tests completed!"
echo "See TEST_SUMMARY.md for detailed results"