#!/usr/bin/env python3
"""
Comprehensive test runner for all CrewAI tests
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio

print("=" * 80)
print("CREWAI COMPREHENSIVE TEST SUITE")
print("=" * 80)

# Set environment variables
os.environ['OPENAI_API_KEY'] = 'test-key-for-testing'
os.environ['TESTING'] = 'true'

test_results = {
    'passed': 0,
    'failed': 0,
    'errors': []
}

def test_passed(name):
    print(f"✓ {name}")
    test_results['passed'] += 1

def test_failed(name, error):
    print(f"✗ {name}: {error}")
    test_results['failed'] += 1
    test_results['errors'].append((name, str(error)))

print("\n1. TESTING CREWAI TOOLS")
print("-" * 40)

# Test 1.1: PantryScanTool
try:
    with patch('backend_gateway.config.database.get_database_service') as mock_db:
        mock_db_service = Mock()
        mock_db_service.execute_query.return_value = [
            {'user_id': 123, 'product_name': 'Chicken', 'quantity': 2, 'unit': 'lbs', 'expiration_date': '2024-01-20'}
        ]
        mock_db.return_value = mock_db_service
        
        from backend_gateway.services.crew_ai_multi_agent import PantryScanTool
        tool = PantryScanTool()
        result = tool._run(user_id=123)
        
        assert len(result) == 1
        assert result[0]['product_name'] == 'Chicken'
        assert mock_db_service.execute_query.called
        test_passed("PantryScanTool._run()")
except Exception as e:
    test_failed("PantryScanTool._run()", e)

# Test 1.2: IngredientFilterTool
try:
    from backend_gateway.services.crew_ai_multi_agent import IngredientFilterTool
    
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    
    pantry_items = [
        {'product_name': 'Fresh Chicken', 'expiration_date': tomorrow.strftime('%Y-%m-%d')},
        {'product_name': 'Expired Milk', 'expiration_date': yesterday.strftime('%Y-%m-%d')},
        {'product_name': 'Rice', 'expiration_date': None}
    ]
    
    tool = IngredientFilterTool()
    result = tool._run(pantry_items)
    
    assert len(result) == 2
    assert all(item['product_name'] != 'Expired Milk' for item in result)
    test_passed("IngredientFilterTool._run()")
except Exception as e:
    test_failed("IngredientFilterTool._run()", e)

# Test 1.3: UserPreferenceTool
try:
    with patch('backend_gateway.config.database.get_database_service') as mock_db:
        mock_db_service = Mock()
        mock_db_service.execute_query.return_value = [{
            'user_id': 123,
            'preferences': {
                'dietary_restrictions': ['vegetarian'],
                'allergens': ['nuts'],
                'cuisine_preferences': ['italian'],
                'cooking_skill': 'beginner',
                'max_cooking_time': 30
            }
        }]
        mock_db.return_value = mock_db_service
        
        from backend_gateway.services.crew_ai_multi_agent import UserPreferenceTool
        tool = UserPreferenceTool()
        result = tool._run(user_id=123)
        
        assert result['dietary_restrictions'] == ['vegetarian']
        assert result['allergens'] == ['nuts']
        assert result['max_cooking_time'] == 30
        test_passed("UserPreferenceTool._run()")
except Exception as e:
    test_failed("UserPreferenceTool._run()", e)

# Test 1.4: RecipeScoringTool
try:
    from backend_gateway.services.crew_ai_multi_agent import RecipeScoringTool
    
    recipes = [
        {
            'name': 'Quick Salad',
            'time': 15,
            'cuisine_type': 'italian',
            'nutrition': {'nutritional_balance': 'good'}
        },
        {
            'name': 'Slow Roast',
            'time': 120,
            'cuisine_type': 'american',
            'nutrition': {'nutritional_balance': 'poor'}
        }
    ]
    preferences = {
        'max_cooking_time': 30,
        'cuisine_preferences': ['italian', 'asian']
    }
    
    tool = RecipeScoringTool()
    result = tool._run(recipes, preferences)
    
    assert all('score' in recipe for recipe in result)
    assert result[0]['name'] == 'Quick Salad'
    assert result[0]['score'] > result[1]['score']
    test_passed("RecipeScoringTool._run()")
except Exception as e:
    test_failed("RecipeScoringTool._run()", e)

print("\n2. TESTING MULTIAGENT SERVICE")
print("-" * 40)

# Test 2.1: Service initialization with mocks
try:
    with patch('backend_gateway.services.crew_ai_multi_agent.Agent') as MockAgent:
        with patch('backend_gateway.services.crew_ai_multi_agent.Task') as MockTask:
            with patch('backend_gateway.services.crew_ai_multi_agent.Crew') as MockCrew:
                with patch('backend_gateway.services.crew_ai_multi_agent.Process') as MockProcess:
                    MockAgent.return_value = MagicMock(role='Test Agent', tools=[])
                    MockTask.return_value = MagicMock(description='Test Task')
                    MockCrew.return_value = MagicMock()
                    MockProcess.sequential = 'sequential'
                    
                    from backend_gateway.services.crew_ai_multi_agent import MultiAgentCrewAIService
                    
                    service = MultiAgentCrewAIService()
                    assert service.agents is not None
                    assert len(service.agents) == 8
                    test_passed("MultiAgentCrewAIService.__init__()")
except Exception as e:
    test_failed("MultiAgentCrewAIService.__init__()", e)

# Test 2.2: process_message method
try:
    with patch('backend_gateway.services.crew_ai_multi_agent.Agent') as MockAgent:
        with patch('backend_gateway.services.crew_ai_multi_agent.Task') as MockTask:
            with patch('backend_gateway.services.crew_ai_multi_agent.Crew') as MockCrew:
                with patch('backend_gateway.services.crew_ai_multi_agent.Process') as MockProcess:
                    mock_agent = MagicMock()
                    mock_agent.role = 'Test Agent'
                    MockAgent.return_value = mock_agent
                    
                    mock_crew = MagicMock()
                    mock_crew.kickoff.return_value = "Based on your pantry, I recommend Chicken Rice Bowl"
                    MockCrew.return_value = mock_crew
                    
                    MockProcess.sequential = 'sequential'
                    
                    from backend_gateway.services.crew_ai_multi_agent import MultiAgentCrewAIService
                    
                    service = MultiAgentCrewAIService()
                    
                    async def test_process():
                        result = await service.process_message(123, "What's for dinner?")
                        return result
                    
                    result = asyncio.run(test_process())
                    
                    assert 'response' in result
                    assert 'recipes' in result
                    assert mock_crew.kickoff.called
                    test_passed("MultiAgentCrewAIService.process_message()")
except Exception as e:
    test_failed("MultiAgentCrewAIService.process_message()", e)

print("\n3. TESTING AGENT AND TASK CREATION")
print("-" * 40)

# Test 3.1: Agent creation with mocks
try:
    with patch('backend_gateway.services.crew_ai_multi_agent.Agent') as MockAgent:
        # Create a mock agent that has the expected attributes
        def create_mock_agent(*args, **kwargs):
            mock = MagicMock()
            mock.role = kwargs.get('role', 'Default Role')
            mock.goal = kwargs.get('goal', 'Default Goal')
            mock.backstory = kwargs.get('backstory', 'Default Backstory')
            mock.tools = kwargs.get('tools', [])
            mock.verbose = kwargs.get('verbose', True)
            return mock
        
        MockAgent.side_effect = create_mock_agent
        
        from backend_gateway.services.crew_ai_multi_agent import create_agents
        
        agents = create_agents()
        
        expected_agents = [
            'pantry_scan', 'ingredient_filter', 'preference',
            'recipe_search', 'nutritional', 'scoring',
            'evaluator', 'formatter'
        ]
        
        assert all(agent_name in agents for agent_name in expected_agents)
        assert agents['pantry_scan'].role == 'Pantry Scanner'
        assert len(agents['pantry_scan'].tools) == 1
        test_passed("create_agents()")
except Exception as e:
    test_failed("create_agents()", e)

# Test 3.2: Task creation with mocks
try:
    with patch('backend_gateway.services.crew_ai_multi_agent.Agent') as MockAgent:
        with patch('backend_gateway.services.crew_ai_multi_agent.Task') as MockTask:
            # Create mock agents
            def create_mock_agent(*args, **kwargs):
                mock = MagicMock()
                mock.role = kwargs.get('role', 'Default Role')
                return mock
            
            MockAgent.side_effect = create_mock_agent
            
            # Create mock tasks
            def create_mock_task(*args, **kwargs):
                mock = MagicMock()
                mock.description = kwargs.get('description', 'Default Description')
                mock.agent = kwargs.get('agent')
                mock.expected_output = kwargs.get('expected_output', 'Default Output')
                return mock
            
            MockTask.side_effect = create_mock_task
            
            from backend_gateway.services.crew_ai_multi_agent import create_agents, create_tasks
            
            agents = create_agents()
            tasks = create_tasks(agents, user_id=123, message="What's for dinner?")
            
            assert len(tasks) == 8
            assert "user 123" in tasks[0].description
            assert "What's for dinner?" in tasks[3].description
            test_passed("create_tasks()")
except Exception as e:
    test_failed("create_tasks()", e)

print("\n4. TESTING INTEGRATION SCENARIOS")
print("-" * 40)

# Test 4.1: Full flow with database mocking
try:
    with patch('backend_gateway.config.database.get_database_service') as mock_db:
        mock_db_service = Mock()
        mock_db_service.execute_query.return_value = [
            {'user_id': 123, 'product_name': 'Chicken', 'quantity': 2, 'unit': 'lbs'}
        ]
        mock_db.return_value = mock_db_service
        
        from backend_gateway.services.crew_ai_multi_agent import PantryScanTool, IngredientFilterTool
        
        # Test tool chain
        pantry_tool = PantryScanTool()
        filter_tool = IngredientFilterTool()
        
        pantry_items = pantry_tool._run(user_id=123)
        filtered_items = filter_tool._run(pantry_items)
        
        assert len(pantry_items) > 0
        assert len(filtered_items) > 0
        test_passed("Tool chain execution")
except Exception as e:
    test_failed("Tool chain execution", e)

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"Total Tests: {test_results['passed'] + test_results['failed']}")
print(f"Passed: {test_results['passed']}")
print(f"Failed: {test_results['failed']}")

if test_results['errors']:
    print("\nFailed Tests:")
    for name, error in test_results['errors']:
        print(f"  - {name}: {error}")

print("\n" + "=" * 80)