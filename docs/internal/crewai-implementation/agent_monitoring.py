"""Agent-specific monitoring configurations and decorators for CrewAI agents.

This module provides pre-configured monitoring decorators for each of the 8 CrewAI agents
with appropriate retry strategies, timeouts, and error handling based on their specific roles.
"""

from typing import Dict, Any, Optional, Callable
from functools import wraps

from backend_gateway.core.crewai_observability import (
    AgentType,
    RetryConfig,
    monitor_crewai_execution,
    agent_execution_span,
    get_agent_health,
    observability_manager
)
from backend_gateway.core.logging_config import get_logger

logger = get_logger("crewai.agent_monitoring")

# Agent-specific configurations
AGENT_CONFIGS = {
    AgentType.FOOD_CATEGORIZER: {
        "retry_config": RetryConfig(max_retries=2, base_delay=0.5, exponential_backoff=True),
        "timeout_seconds": 15.0,
        "enable_circuit_breaker": True,
        "description": "Categorizes raw food items using USDA database"
    },
    AgentType.FRESH_FILTER: {
        "retry_config": RetryConfig(max_retries=3, base_delay=1.0, exponential_backoff=True),
        "timeout_seconds": 20.0,
        "enable_circuit_breaker": True,
        "description": "Analyzes freshness and expiry data for pantry optimization"
    },
    AgentType.JUDGE_THYME: {
        "retry_config": RetryConfig(max_retries=2, base_delay=1.0, exponential_backoff=True),
        "timeout_seconds": 30.0,
        "enable_circuit_breaker": True,
        "description": "Recipe quality evaluation and recommendation scoring"
    },
    AgentType.NUTRI_CHECK: {
        "retry_config": RetryConfig(max_retries=3, base_delay=0.5, exponential_backoff=True),
        "timeout_seconds": 25.0,
        "enable_circuit_breaker": True,
        "description": "Nutritional analysis and dietary compliance checking"
    },
    AgentType.PANTRY_LEDGER: {
        "retry_config": RetryConfig(max_retries=4, base_delay=1.0, exponential_backoff=True),
        "timeout_seconds": 35.0,
        "enable_circuit_breaker": True,
        "description": "Pantry inventory management and tracking"
    },
    AgentType.RECIPE_SEARCH: {
        "retry_config": RetryConfig(max_retries=3, base_delay=1.5, exponential_backoff=True),
        "timeout_seconds": 40.0,
        "enable_circuit_breaker": True,
        "description": "Recipe discovery and matching with available ingredients"
    },
    AgentType.UNIT_CANON: {
        "retry_config": RetryConfig(max_retries=2, base_delay=0.3, exponential_backoff=False),
        "timeout_seconds": 10.0,
        "enable_circuit_breaker": False,  # Unit conversion is critical and fast
        "description": "Unit normalization and conversion for ingredients"
    },
    AgentType.USER_PREFERENCES: {
        "retry_config": RetryConfig(max_retries=3, base_delay=1.0, exponential_backoff=True),
        "timeout_seconds": 20.0,
        "enable_circuit_breaker": True,
        "description": "User preference analysis and personalization"
    }
}


def get_agent_config(agent_type: AgentType) -> Dict[str, Any]:
    """Get configuration for specific agent type."""
    return AGENT_CONFIGS.get(agent_type, {
        "retry_config": RetryConfig(),
        "timeout_seconds": 30.0,
        "enable_circuit_breaker": True,
        "description": "Generic agent configuration"
    })


# Pre-configured monitoring decorators for each agent
def monitor_food_categorizer(task_type: str = "categorize"):
    """Monitoring decorator for Food Categorizer Agent."""
    config = get_agent_config(AgentType.FOOD_CATEGORIZER)
    return monitor_crewai_execution(
        agent_type=AgentType.FOOD_CATEGORIZER,
        task_type=task_type,
        retry_config=config["retry_config"],
        timeout_seconds=config["timeout_seconds"],
        enable_circuit_breaker=config["enable_circuit_breaker"]
    )


def monitor_fresh_filter(task_type: str = "filter_freshness"):
    """Monitoring decorator for Fresh Filter Agent."""
    config = get_agent_config(AgentType.FRESH_FILTER)
    return monitor_crewai_execution(
        agent_type=AgentType.FRESH_FILTER,
        task_type=task_type,
        retry_config=config["retry_config"],
        timeout_seconds=config["timeout_seconds"],
        enable_circuit_breaker=config["enable_circuit_breaker"]
    )


def monitor_judge_thyme(task_type: str = "evaluate_recipe"):
    """Monitoring decorator for Judge Thyme Agent."""
    config = get_agent_config(AgentType.JUDGE_THYME)
    return monitor_crewai_execution(
        agent_type=AgentType.JUDGE_THYME,
        task_type=task_type,
        retry_config=config["retry_config"],
        timeout_seconds=config["timeout_seconds"],
        enable_circuit_breaker=config["enable_circuit_breaker"]
    )


def monitor_nutri_check(task_type: str = "analyze_nutrition"):
    """Monitoring decorator for Nutri Check Agent."""
    config = get_agent_config(AgentType.NUTRI_CHECK)
    return monitor_crewai_execution(
        agent_type=AgentType.NUTRI_CHECK,
        task_type=task_type,
        retry_config=config["retry_config"],
        timeout_seconds=config["timeout_seconds"],
        enable_circuit_breaker=config["enable_circuit_breaker"]
    )


def monitor_pantry_ledger(task_type: str = "manage_pantry"):
    """Monitoring decorator for Pantry Ledger Agent."""
    config = get_agent_config(AgentType.PANTRY_LEDGER)
    return monitor_crewai_execution(
        agent_type=AgentType.PANTRY_LEDGER,
        task_type=task_type,
        retry_config=config["retry_config"],
        timeout_seconds=config["timeout_seconds"],
        enable_circuit_breaker=config["enable_circuit_breaker"]
    )


def monitor_recipe_search(task_type: str = "search_recipes"):
    """Monitoring decorator for Recipe Search Agent."""
    config = get_agent_config(AgentType.RECIPE_SEARCH)
    return monitor_crewai_execution(
        agent_type=AgentType.RECIPE_SEARCH,
        task_type=task_type,
        retry_config=config["retry_config"],
        timeout_seconds=config["timeout_seconds"],
        enable_circuit_breaker=config["enable_circuit_breaker"]
    )


def monitor_unit_canon(task_type: str = "normalize_units"):
    """Monitoring decorator for Unit Canon Agent."""
    config = get_agent_config(AgentType.UNIT_CANON)
    return monitor_crewai_execution(
        agent_type=AgentType.UNIT_CANON,
        task_type=task_type,
        retry_config=config["retry_config"],
        timeout_seconds=config["timeout_seconds"],
        enable_circuit_breaker=config["enable_circuit_breaker"]
    )


def monitor_user_preferences(task_type: str = "analyze_preferences"):
    """Monitoring decorator for User Preferences Agent."""
    config = get_agent_config(AgentType.USER_PREFERENCES)
    return monitor_crewai_execution(
        agent_type=AgentType.USER_PREFERENCES,
        task_type=task_type,
        retry_config=config["retry_config"],
        timeout_seconds=config["timeout_seconds"],
        enable_circuit_breaker=config["enable_circuit_breaker"]
    )


# Enhanced monitoring context managers for manual instrumentation
class AgentMonitoringContext:
    """Context manager for manual agent monitoring with enhanced features."""
    
    def __init__(self, agent_type: AgentType, task_type: str, metadata: Optional[Dict[str, Any]] = None):
        self.agent_type = agent_type
        self.task_type = task_type
        self.metadata = metadata or {}
        self.config = get_agent_config(agent_type)
        self.context = None
        
    def __enter__(self):
        """Start monitoring context."""
        self.context = observability_manager.create_execution_context(
            agent_type=self.agent_type,
            task_type=self.task_type,
            metadata=self.metadata,
            retry_config=self.config["retry_config"],
            enable_circuit_breaker=self.config["enable_circuit_breaker"],
            timeout_seconds=self.config["timeout_seconds"]
        )
        
        self.context.start()
        return self.context
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End monitoring context."""
        if exc_type:
            self.context.fail(exc_val)
        else:
            self.context.succeed()
        
        observability_manager.complete_execution_context(self.context)


def create_agent_context(agent_type: AgentType, task_type: str, metadata: Optional[Dict[str, Any]] = None):
    """Create monitoring context for specific agent type."""
    return AgentMonitoringContext(agent_type, task_type, metadata)


# Agent health check utilities
def check_agent_health(agent_type: AgentType) -> Dict[str, Any]:
    """Check health of specific agent."""
    return observability_manager.get_agent_health_detailed(agent_type)


def check_all_agents_health() -> Dict[str, Any]:
    """Check health of all agents."""
    return get_agent_health()


def get_agent_performance_summary() -> Dict[str, Any]:
    """Get performance summary for all agents."""
    summary = {
        "timestamp": observability_manager.execution_history[-1].get("timestamp") if observability_manager.execution_history else None,
        "agents": {}
    }
    
    for agent_type in AgentType:
        health = observability_manager.get_agent_health_detailed(agent_type)
        config = get_agent_config(agent_type)
        
        summary["agents"][agent_type.value] = {
            "description": config["description"],
            "health_status": health["health_status"],
            "success_rate": health["performance"]["success_rate"],
            "avg_duration": health["performance"]["average_duration_seconds"],
            "active_executions": health["active_executions"],
            "circuit_breaker_state": health["circuit_breaker"]["state"],
            "warnings": health["warnings"]
        }
    
    return summary


# Tool usage tracking utilities
class ToolUsageTracker:
    """Helper class for tracking tool usage within agent executions."""
    
    def __init__(self, context):
        self.context = context
        
    def track_tool_call(self, tool_name: str, duration_seconds: float, success: bool, 
                       inputs: Optional[Dict[str, Any]] = None, outputs: Optional[Dict[str, Any]] = None):
        """Track individual tool call."""
        self.context.record_tool_usage(tool_name, duration_seconds, success, inputs, outputs)
        
        logger.info(
            f"Tool usage recorded",
            extra={
                "tool_name": tool_name,
                "duration_seconds": duration_seconds,
                "success": success,
                "agent_type": self.context.agent_type.value,
                "task_id": self.context.task_id
            }
        )


def create_tool_tracker(context) -> ToolUsageTracker:
    """Create tool usage tracker for agent context."""
    return ToolUsageTracker(context)


# Decision point tracking utilities  
def track_agent_decision(context, decision: str, reasoning: str, confidence: float = 1.0, 
                        context_data: Optional[Dict[str, Any]] = None):
    """Track agent decision points for debugging."""
    context.add_decision_point(decision, reasoning, confidence, context_data)
    
    logger.info(
        f"Agent decision recorded",
        extra={
            "decision": decision,
            "reasoning": reasoning,
            "confidence": confidence,
            "agent_type": context.agent_type.value,
            "task_id": context.task_id
        }
    )


# Performance optimization suggestions
def get_performance_recommendations() -> Dict[str, Any]:
    """Get performance optimization recommendations based on agent metrics."""
    recommendations = {
        "timestamp": observability_manager.execution_history[-1].get("timestamp") if observability_manager.execution_history else None,
        "recommendations": []
    }
    
    for agent_type in AgentType:
        health = observability_manager.get_agent_health_detailed(agent_type)
        
        # Check for performance issues and provide recommendations
        if health["performance"]["success_rate"] < 0.8:
            recommendations["recommendations"].append({
                "agent": agent_type.value,
                "issue": "low_success_rate",
                "current_rate": health["performance"]["success_rate"],
                "recommendation": "Investigate error patterns and consider adjusting retry configuration or input validation"
            })
            
        if health["performance"]["average_duration_seconds"] > 30:
            recommendations["recommendations"].append({
                "agent": agent_type.value,
                "issue": "slow_performance",
                "current_duration": health["performance"]["average_duration_seconds"],
                "recommendation": "Profile agent execution and optimize slow operations or increase timeout"
            })
            
        if health["circuit_breaker"]["state"] != "closed":
            recommendations["recommendations"].append({
                "agent": agent_type.value,
                "issue": "circuit_breaker_issues",
                "state": health["circuit_breaker"]["state"],
                "recommendation": "Investigate root cause of failures and consider manual circuit breaker reset"
            })
    
    return recommendations


__all__ = [
    "monitor_food_categorizer",
    "monitor_fresh_filter", 
    "monitor_judge_thyme",
    "monitor_nutri_check",
    "monitor_pantry_ledger",
    "monitor_recipe_search",
    "monitor_unit_canon",
    "monitor_user_preferences",
    "create_agent_context",
    "check_agent_health",
    "check_all_agents_health",
    "get_agent_performance_summary",
    "create_tool_tracker",
    "track_agent_decision",
    "get_performance_recommendations",
    "AgentMonitoringContext",
    "ToolUsageTracker"
]