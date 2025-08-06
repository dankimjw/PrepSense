# CrewAI Agent Monitoring & Observability Guide

This guide covers the comprehensive monitoring and observability system for PrepSense's 8 CrewAI agents, including setup, usage, and best practices for production deployment.

## Overview

The PrepSense CrewAI monitoring system provides:
- **Comprehensive agent monitoring** with retry logic and circuit breaker protection
- **Tool usage tracking** and performance analytics
- **Error handling and categorization** with automatic recovery
- **Decision point tracking** for debugging agent reasoning
- **Performance metrics** and trend analysis
- **PII-safe logging** and data sanitization
- **Real-time health monitoring** with alerting capabilities

## Agent Types

The system monitors these 8 specialized agents:

1. **food_categorizer** - Categorizes raw food items using USDA database
2. **fresh_filter** - Analyzes freshness and expiry data for pantry optimization
3. **judge_thyme** - Recipe quality evaluation and recommendation scoring
4. **nutri_check** - Nutritional analysis and dietary compliance checking
5. **pantry_ledger** - Pantry inventory management and tracking
6. **recipe_search** - Recipe discovery and matching with available ingredients
7. **unit_canon** - Unit normalization and conversion for ingredients
8. **user_preferences** - User preference analysis and personalization

## Quick Start

### 1. Basic Agent Monitoring

```python
from backend_gateway.crewai.agent_monitoring import monitor_nutri_check

@monitor_nutri_check("nutritional_analysis")
async def analyze_nutrition(ingredients, user_id):
    # Your agent logic here
    return {"status": "success", "nutrition": {...}}
```

### 2. Enhanced Tool Monitoring

```python
from backend_gateway.crewai.tools.monitoring_tool import MonitoredBaseTool

class MyEnhancedTool(MonitoredBaseTool):
    name = "my_tool"
    description = "Enhanced tool with monitoring"
    
    def _run(self, input_data):
        # Tool implementation with automatic monitoring
        return result
```

### 3. Manual Context Management

```python
from backend_gateway.crewai.agent_monitoring import create_agent_context
from backend_gateway.core.crewai_observability import AgentType

with create_agent_context(AgentType.NUTRI_CHECK, "analysis") as context:
    # Your logic here
    context.add_decision_point("strategy", "Using comprehensive analysis", 0.9)
    result = perform_analysis()
```

## Core Components

### 1. Enhanced Observability System

**Location**: `backend_gateway/core/crewai_observability.py`

**Key Features**:
- Automatic retry logic with exponential backoff
- Circuit breaker pattern for fault tolerance
- Performance tracking and trend analysis
- Error categorization and Sentry integration
- PII-safe data sanitization

**Configuration**:
```python
from backend_gateway.core.crewai_observability import RetryConfig

# Custom retry configuration
retry_config = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    exponential_backoff=True,
    jitter=True
)
```

### 2. Agent-Specific Monitoring

**Location**: `backend_gateway/crewai/agent_monitoring.py`

**Pre-configured Decorators**:
- `@monitor_food_categorizer()` - Fast categorization with minimal retries
- `@monitor_fresh_filter()` - Standard monitoring for freshness analysis
- `@monitor_judge_thyme()` - Extended timeout for complex recipe evaluation
- `@monitor_nutri_check()` - Comprehensive nutrition analysis monitoring
- `@monitor_pantry_ledger()` - Robust pantry operations with multiple retries
- `@monitor_recipe_search()` - Extended timeout for recipe discovery
- `@monitor_unit_canon()` - Fast unit conversion (no circuit breaker)
- `@monitor_user_preferences()` - Standard preference analysis monitoring

### 3. Tool Monitoring System

**Location**: `backend_gateway/crewai/tools/monitoring_tool.py`

**Features**:
- Automatic tool execution tracking
- Performance metrics per tool
- Tool usage patterns across agents
- Error tracking and recovery

**Usage**:
```python
# Enhanced tool base class
class MyTool(MonitoredBaseTool):
    def _run(self, input_data):
        # Automatic monitoring included
        return self.process_data(input_data)

# Manual monitoring decorator
@monitor_tool_execution("my_tool", "nutri_check")
def tool_function(data):
    return process_data(data)
```

### 4. Monitoring API Endpoints

**Location**: `backend_gateway/routers/crewai_monitoring_router.py`

**Endpoints**:
- `GET /crewai/monitoring/health` - Overall system health
- `GET /crewai/monitoring/health/{agent_type}` - Specific agent health
- `GET /crewai/monitoring/metrics` - Performance metrics
- `GET /crewai/monitoring/performance/summary` - Performance summary
- `POST /crewai/monitoring/circuit-breaker/{agent_type}/reset` - Reset circuit breaker
- `GET /crewai/monitoring/executions/active` - Active executions
- `GET /crewai/monitoring/debug/{agent_type}` - Debugging information
- `GET /crewai/monitoring/dashboard/data` - Dashboard data

## Configuration

### Agent-Specific Settings

Each agent has optimized configuration in `agent_monitoring.py`:

```python
AGENT_CONFIGS = {
    AgentType.FOOD_CATEGORIZER: {
        "retry_config": RetryConfig(max_retries=2, base_delay=0.5),
        "timeout_seconds": 15.0,
        "enable_circuit_breaker": True
    },
    # ... other agents
}
```

### Circuit Breaker Configuration

```python
class CircuitBreakerState:
    failure_threshold: int = 5      # Failures before opening
    reset_timeout: int = 300        # 5 minutes in open state
    half_open_max_calls: int = 3    # Test calls in half-open state
```

### Prometheus Metrics

The system exposes these metrics:
- `crewai_agent_executions_total` - Total agent executions by status
- `crewai_agent_execution_duration_seconds` - Execution duration histogram
- `crewai_agent_errors_total` - Error counts by type
- `crewai_agent_retry_attempts_total` - Retry attempt counts
- `crewai_agent_circuit_breaker_state` - Circuit breaker states
- `crewai_tool_executions_total` - Tool execution counts
- `crewai_tool_execution_seconds` - Tool execution duration

## Usage Examples

### 1. Basic Agent Function with Monitoring

```python
from backend_gateway.crewai.agent_monitoring import monitor_nutri_check

@monitor_nutri_check("comprehensive_analysis")
async def analyze_meal_nutrition(ingredients, user_id, dietary_restrictions=None):
    """
    Analyze nutrition with automatic monitoring:
    - Retry on transient failures
    - Circuit breaker protection
    - Performance tracking
    - Error categorization
    """
    try:
        nutrition_data = await calculate_nutrition(ingredients)
        return {
            "status": "success",
            "nutrition": nutrition_data,
            "user_id": user_id,
            "dietary_compliance": check_restrictions(nutrition_data, dietary_restrictions)
        }
    except ValidationError as e:
        # Won't retry validation errors
        return {"status": "error", "error": "validation", "message": str(e)}
    except ServiceError as e:
        # Will retry service errors automatically
        raise  # Let monitoring handle retry
```

### 2. Complex Workflow with Manual Context

```python
from backend_gateway.crewai.agent_monitoring import (
    create_agent_context, 
    track_agent_decision,
    create_tool_tracker
)

async def complex_meal_planning_workflow(user_id, dietary_goals):
    with create_agent_context(AgentType.RECIPE_SEARCH, "meal_planning") as context:
        # Track decision points for debugging
        track_agent_decision(
            context,
            decision="meal_planning_strategy",
            reasoning="Using preference-based recipe matching",
            confidence=0.85,
            context_data={"user_id": user_id, "goals": dietary_goals}
        )
        
        # Track tool usage
        tool_tracker = create_tool_tracker(context)
        
        # Your workflow logic here
        recipes = await search_recipes(user_preferences)
        
        # Track tool call
        tool_tracker.track_tool_call(
            tool_name="recipe_search",
            duration_seconds=1.2,
            success=True,
            inputs={"preferences": user_preferences},
            outputs={"recipe_count": len(recipes)}
        )
        
        return {"meal_plan": recipes, "status": "success"}
```

### 3. Enhanced Tool Implementation

```python
from backend_gateway.crewai.tools.monitoring_tool import MonitoredBaseTool

class AdvancedNutritionTool(MonitoredBaseTool):
    name = "advanced_nutrition"
    description = "Advanced nutrition analysis with monitoring"
    
    def _run(self, ingredients, analysis_level="standard"):
        # Automatic monitoring included:
        # - Performance tracking
        # - Error handling
        # - Agent context integration
        # - PII sanitization
        
        try:
            result = self.perform_analysis(ingredients, analysis_level)
            return {
                "status": "success",
                "nutrition": result,
                "confidence": self.calculate_confidence(result),
                "warnings": self.generate_warnings(result)
            }
        except Exception as e:
            # Error automatically tracked and categorized
            raise
    
    def perform_analysis(self, ingredients, level):
        # Your tool implementation
        pass
```

## Health Monitoring

### System Health Check

```python
from backend_gateway.crewai.agent_monitoring import check_all_agents_health

health_status = check_all_agents_health()

# Returns:
{
    "overall_healthy": True,
    "system_stats": {
        "total_active_executions": 5,
        "overall_success_rate": 0.95
    },
    "agent_health": {
        "nutri_check": {
            "health_status": "healthy",
            "success_rate": 0.98,
            "circuit_breaker": {"state": "closed"},
            "warnings": []
        }
    }
}
```

### Individual Agent Health

```python
from backend_gateway.crewai.agent_monitoring import check_agent_health
from backend_gateway.core.crewai_observability import AgentType

health = check_agent_health(AgentType.NUTRI_CHECK)

# Returns detailed health information:
{
    "agent_type": "nutri_check",
    "health_status": "healthy",  # healthy, degraded, unhealthy
    "performance": {
        "total_executions": 150,
        "success_rate": 0.96,
        "average_duration_seconds": 1.2
    },
    "circuit_breaker": {
        "state": "closed",
        "failure_count": 0
    },
    "warnings": []
}
```

## Performance Analysis

### Performance Summary

```python
from backend_gateway.crewai.agent_monitoring import get_agent_performance_summary

summary = get_agent_performance_summary()

# Returns performance data for all agents with:
# - Health status
# - Success rates
# - Average durations
# - Active executions
# - Circuit breaker states
```

### Performance Recommendations

```python
from backend_gateway.crewai.agent_monitoring import get_performance_recommendations

recommendations = get_performance_recommendations()

# Returns actionable recommendations:
{
    "recommendations": [
        {
            "agent": "recipe_search",
            "issue": "slow_performance",
            "current_duration": 5.2,
            "recommendation": "Profile agent execution and optimize slow operations"
        }
    ]
}
```

## Debugging

### Get Debugging Information

```python
from backend_gateway.core.crewai_observability import get_agent_debugging_info

# Get general agent debugging info
debug_info = get_agent_debugging_info(AgentType.NUTRI_CHECK)

# Get specific task debugging info
debug_info = get_agent_debugging_info(AgentType.NUTRI_CHECK, task_id="task_123")

# Returns:
{
    "agent_type": "nutri_check",
    "recent_executions": [...],
    "health": {...},
    "execution": {  # if task_id provided
        "decision_points": [...],
        "tool_usage": [...],
        "performance_metrics": {...}
    }
}
```

### Decision Point Tracking

```python
# Track agent reasoning for debugging
track_agent_decision(
    context,
    decision="use_detailed_analysis",
    reasoning="High-value user requires comprehensive nutrition data",
    confidence=0.92,
    context_data={
        "user_tier": "premium",
        "ingredient_complexity": "high"
    }
)
```

## Error Handling

### Error Types

The system categorizes errors for better handling:

- `VALIDATION_ERROR` - Input validation failures (no retry)
- `TIMEOUT_ERROR` - Operation timeouts (retry with backoff)
- `RESOURCE_ERROR` - Memory/CPU resource issues (retry)
- `API_ERROR` - External API failures (retry)
- `AUTHENTICATION_ERROR` - Auth failures (no retry)
- `RATE_LIMIT_ERROR` - Rate limiting (retry with longer delay)
- `NETWORK_ERROR` - Network connectivity (retry)
- `DATA_ERROR` - Data format/parsing issues (limited retry)

### Circuit Breaker States

- `CLOSED` - Normal operation
- `HALF_OPEN` - Testing after failure threshold reached  
- `OPEN` - Blocking requests due to excessive failures

## Security & Privacy

### PII Protection

The monitoring system automatically sanitizes sensitive data:

```python
# Sensitive keys are automatically redacted
input_data = {
    "user_email": "user@example.com",  # -> "***REDACTED***"
    "ingredients": ["chicken", "rice"],  # -> preserved
    "api_key": "secret_key"  # -> "***REDACTED***"
}
```

### Safe Logging

All monitoring logs are structured and PII-safe:

```python
logger.info(
    "Agent execution completed",
    extra={
        "agent_type": "nutri_check",
        "duration_ms": 1200,
        "success": True,
        "user_id": "user123",  # Safe identifier
        "input_preview": "ingredients: 3 items..."  # Truncated preview
    }
)
```

## Production Deployment

### Required Environment Variables

```bash
# Sentry integration
SENTRY_DSN=https://your-sentry-dsn
SENTRY_ENVIRONMENT=production

# Logging configuration
LOG_FORMAT=json
LOG_LEVEL=INFO

# Monitoring settings
CREWAI_MONITORING_ENABLED=true
PROMETHEUS_METRICS_ENABLED=true
```

### Monitoring Endpoints Integration

Add the monitoring router to your FastAPI app:

```python
from backend_gateway.routers.crewai_monitoring_router import router

app.include_router(router)

# Access monitoring at:
# GET /crewai/monitoring/health
# GET /crewai/monitoring/metrics
# etc.
```

### Alerting Configuration

Set up alerts based on these metrics:

1. **Circuit Breaker Open**: Alert when any agent's circuit breaker opens
2. **Low Success Rate**: Alert when success rate < 90% over 10 minutes
3. **High Error Rate**: Alert when error rate > 5% over 5 minutes
4. **Performance Degradation**: Alert when avg duration increases > 50%
5. **High Queue Depth**: Alert when active executions > 50 per agent

### Dashboard Integration

The monitoring system provides dashboard-ready data:

```bash
# Get comprehensive dashboard data
curl /crewai/monitoring/dashboard/data

# Get real-time health status
curl /crewai/monitoring/healthz
```

## Troubleshooting

### Common Issues

1. **High Error Rate**
   - Check `/crewai/monitoring/debug/{agent_type}` for error patterns
   - Review recent decision points for logic issues
   - Check external service availability

2. **Circuit Breaker Open**
   - Investigate root cause via debugging endpoint
   - Fix underlying issue
   - Reset circuit breaker: `POST /crewai/monitoring/circuit-breaker/{agent_type}/reset`

3. **Performance Degradation**
   - Check `/crewai/monitoring/performance/recommendations`
   - Review tool usage patterns
   - Profile slow operations

4. **Memory Leaks**
   - Monitor execution history size
   - Check for stuck executions
   - Review cleanup procedures

### Best Practices

1. **Always use monitoring decorators** for production agent functions
2. **Track decision points** for complex logic that might need debugging
3. **Monitor tool usage** to identify performance bottlenecks
4. **Set up proper alerting** for critical failure scenarios
5. **Regular health checks** in CI/CD pipeline
6. **Performance regression testing** with each deployment
7. **Circuit breaker testing** in staging environment

## API Reference

See the full API documentation in the monitoring router for detailed endpoint specifications and response schemas.

## Contributing

When adding new agents or tools:

1. Create monitoring configuration in `agent_monitoring.py`
2. Use `MonitoredBaseTool` base class for tools
3. Add appropriate timeout and retry settings
4. Test circuit breaker behavior
5. Update health check endpoints
6. Add performance benchmarks

## Support

For monitoring system issues:
- Check logs in `logs/crewai.log`
- Use debugging endpoints for agent-specific issues
- Monitor Prometheus metrics for trends
- Review Sentry for error details