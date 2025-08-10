"""CrewAI Agent Monitoring API Router

This router provides comprehensive monitoring and observability endpoints
for all 8 CrewAI agents, including health checks, performance metrics,
circuit breaker management, and debugging tools.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import JSONResponse

from backend_gateway.core.crewai_observability import (
    AgentType,
    get_agent_debugging_info,
    get_agent_health,
    get_agent_performance_report,
    observability_manager,
    reset_agent_circuit_breaker,
)
from backend_gateway.core.logging_config import get_logger
from backend_gateway.crewai.agent_monitoring import (
    check_agent_health,
    get_agent_performance_summary,
    get_performance_recommendations,
)
from backend_gateway.crewai.tools.monitoring_tool import ToolPerformanceAnalyzer, get_all_tool_stats

logger = get_logger("crewai.monitoring.router")

router = APIRouter(prefix="/crewai/monitoring", tags=["CrewAI Monitoring"])


@router.get("/health", summary="Get overall system health for all agents")
async def get_system_health() -> JSONResponse:
    """
    Get comprehensive health status for all CrewAI agents.

    Returns:
        - Overall system health status
        - Individual agent health details
        - Active executions count
        - System-wide issues and warnings
    """
    try:
        health_data = get_agent_health()
        return JSONResponse(content=health_data)
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}") from e


@router.get("/health/{agent_type}", summary="Get health status for specific agent")
async def get_agent_health_status(
    agent_type: str = Path(..., description="Agent type to check health for")
) -> JSONResponse:
    """
    Get detailed health status for a specific agent.

    Args:
        agent_type: One of the 8 agent types (food_categorizer, fresh_filter, etc.)

    Returns:
        - Agent health status (healthy, degraded, unhealthy)
        - Performance metrics
        - Circuit breaker state
        - Recent error patterns
        - Warnings and recommendations
    """
    try:
        # Validate agent type
        try:
            agent_enum = AgentType(agent_type)
        except ValueError:
            valid_types = [agent.value for agent in AgentType]
            raise HTTPException(
                status_code=400, detail=f"Invalid agent type. Valid types: {valid_types}"
            ) from None

        health_data = check_agent_health(agent_enum)
        return JSONResponse(content=health_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent health for {agent_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Agent health check failed: {str(e)}") from e


@router.get("/metrics", summary="Get comprehensive performance metrics")
async def get_performance_metrics(
    agent_type: Optional[str] = Query(None, description="Filter metrics by agent type"),
    include_trends: bool = Query(True, description="Include performance trend analysis"),
) -> JSONResponse:
    """
    Get comprehensive performance metrics for agents.

    Args:
        agent_type: Optional agent type filter
        include_trends: Whether to include trend analysis

    Returns:
        - Execution statistics
        - Success rates and durations
        - Performance trends
        - Resource usage metrics
    """
    try:
        if include_trends:
            metrics = get_agent_performance_report()
        elif agent_type:
            try:
                agent_enum = AgentType(agent_type)
                metrics = observability_manager.get_execution_stats(agent_enum)
            except ValueError:
                valid_types = [agent.value for agent in AgentType]
                raise HTTPException(
                    status_code=400, detail=f"Invalid agent type. Valid types: {valid_types}"
                )
        else:
            metrics = observability_manager.get_execution_stats()

        return JSONResponse(content=metrics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}") from e


@router.get("/performance/summary", summary="Get performance summary for all agents")
async def get_performance_summary() -> JSONResponse:
    """
    Get high-level performance summary for all agents.

    Returns:
        - Agent descriptions and configurations
        - Health status summary
        - Key performance indicators
        - Circuit breaker states
    """
    try:
        summary = get_agent_performance_summary()
        return JSONResponse(content=summary)

    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=f"Performance summary failed: {str(e)}") from e


@router.get("/performance/recommendations", summary="Get performance optimization recommendations")
async def get_optimization_recommendations() -> JSONResponse:
    """
    Get AI-powered recommendations for improving agent performance.

    Returns:
        - Performance issues detected
        - Optimization recommendations
        - Configuration suggestions
        - Priority levels for fixes
    """
    try:
        recommendations = get_performance_recommendations()
        return JSONResponse(content=recommendations)

    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}") from e


@router.post("/circuit-breaker/{agent_type}/reset", summary="Reset circuit breaker for agent")
async def reset_circuit_breaker(
    agent_type: str = Path(..., description="Agent type to reset circuit breaker for")
) -> JSONResponse:
    """
    Manually reset the circuit breaker for a specific agent.

    Args:
        agent_type: Agent type to reset circuit breaker for

    Returns:
        - Reset confirmation
        - New circuit breaker state
        - Timestamp of reset
    """
    try:
        # Validate agent type
        try:
            agent_enum = AgentType(agent_type)
        except ValueError:
            valid_types = [agent.value for agent in AgentType]
            raise HTTPException(
                status_code=400, detail=f"Invalid agent type. Valid types: {valid_types}"
            ) from None

        result = reset_agent_circuit_breaker(agent_enum)

        logger.info(
            "Circuit breaker reset for agent",
            extra={"agent_type": agent_type, "timestamp": result["timestamp"]},
        )

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker for {agent_type}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Circuit breaker reset failed: {str(e)}"
        ) from e


@router.get("/executions/active", summary="Get currently active executions")
async def get_active_executions(
    agent_type: Optional[str] = Query(None, description="Filter by agent type")
) -> JSONResponse:
    """
    Get information about currently active agent executions.

    Args:
        agent_type: Optional agent type filter

    Returns:
        - List of active executions
        - Execution details and progress
        - Duration and status information
    """
    try:
        active_executions = []

        for _task_id, context in observability_manager.active_executions.items():
            if agent_type is None or context.agent_type.value == agent_type:
                execution_info = {
                    "task_id": context.task_id,
                    "agent_type": context.agent_type.value,
                    "task_type": context.task_type,
                    "user_id": context.user_id,
                    "status": context.status,
                    "start_time": context.start_time.isoformat() if context.start_time else None,
                    "duration_seconds": context.duration,
                    "retry_count": context.retry_count,
                    "decision_points_count": len(context.decision_points),
                    "tools_used_count": len(context.tool_usage),
                    "metadata": context.metadata,
                }
                active_executions.append(execution_info)

        return JSONResponse(
            content={
                "timestamp": (
                    observability_manager.execution_history[-1].get("timestamp")
                    if observability_manager.execution_history
                    else None
                ),
                "total_active": len(active_executions),
                "executions": active_executions,
            }
        )

    except Exception as e:
        logger.error(f"Failed to get active executions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Active executions retrieval failed: {str(e)}"
        ) from e


@router.get("/executions/history", summary="Get execution history")
async def get_execution_history(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of executions to return"),
    status: Optional[str] = Query(None, description="Filter by execution status"),
) -> JSONResponse:
    """
    Get historical execution data for analysis.

    Args:
        agent_type: Optional agent type filter
        limit: Maximum number of executions to return
        status: Optional status filter (success, error)

    Returns:
        - Historical execution data
        - Performance statistics
        - Error patterns and trends
    """
    try:
        history = observability_manager.execution_history[-limit:]

        # Apply filters
        if agent_type:
            history = [h for h in history if h.get("agent_type") == agent_type]

        if status:
            history = [h for h in history if h.get("status") == status]

        return JSONResponse(
            content={
                "timestamp": (
                    observability_manager.execution_history[-1].get("timestamp")
                    if observability_manager.execution_history
                    else None
                ),
                "total_returned": len(history),
                "filters": {"agent_type": agent_type, "status": status, "limit": limit},
                "executions": history,
            }
        )

    except Exception as e:
        logger.error(f"Failed to get execution history: {e}")
        raise HTTPException(
            status_code=500, detail=f"Execution history retrieval failed: {str(e)}"
        ) from e


@router.get("/debug/{agent_type}", summary="Get debugging information for agent")
async def get_agent_debug_info(
    agent_type: str = Path(..., description="Agent type to get debug info for"),
    task_id: Optional[str] = Query(None, description="Specific task ID to debug"),
) -> JSONResponse:
    """
    Get detailed debugging information for an agent or specific execution.

    Args:
        agent_type: Agent type to debug
        task_id: Optional specific task ID for detailed debugging

    Returns:
        - Detailed execution information
        - Decision points and reasoning
        - Tool usage patterns
        - Performance bottlenecks
        - Error traces
    """
    try:
        # Validate agent type
        try:
            agent_enum = AgentType(agent_type)
        except ValueError:
            valid_types = [agent.value for agent in AgentType]
            raise HTTPException(
                status_code=400, detail=f"Invalid agent type. Valid types: {valid_types}"
            ) from None

        debug_info = get_agent_debugging_info(agent_enum, task_id)
        return JSONResponse(content=debug_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get debug info for {agent_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Debug info retrieval failed: {str(e)}") from e


@router.get("/tools/stats", summary="Get tool usage statistics")
async def get_tool_statistics() -> JSONResponse:
    """
    Get comprehensive statistics about tool usage across all agents.

    Returns:
        - Tool usage patterns
        - Performance metrics per tool
        - Error rates and common issues
        - Agent-tool interaction patterns
    """
    try:
        tool_stats = get_all_tool_stats()

        # Add tool performance analysis
        analyzer = ToolPerformanceAnalyzer()
        usage_report = analyzer.get_tool_usage_report()
        performance_issues = analyzer.detect_tool_performance_issues()
        recommendations = analyzer.get_tool_recommendations()

        return JSONResponse(
            content={
                "statistics": tool_stats,
                "usage_report": usage_report,
                "performance_issues": performance_issues,
                "recommendations": recommendations,
            }
        )

    except Exception as e:
        logger.error(f"Failed to get tool statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Tool statistics failed: {str(e)}") from e


@router.get("/dashboard/data", summary="Get dashboard data for monitoring UI")
async def get_dashboard_data() -> JSONResponse:
    """
    Get comprehensive data for monitoring dashboards.

    Returns:
        - Real-time system status
        - Key performance indicators
        - Alert status and warnings
        - Trending data for visualization
    """
    try:
        # Gather all dashboard data
        health_data = get_agent_health()
        performance_summary = get_agent_performance_summary()
        recommendations = get_performance_recommendations()

        # Active executions count per agent
        active_by_agent = {}
        for context in observability_manager.active_executions.values():
            agent_type = context.agent_type.value
            active_by_agent[agent_type] = active_by_agent.get(agent_type, 0) + 1

        # Recent error patterns
        recent_errors = []
        for execution in observability_manager.execution_history[-100:]:
            if execution.get("status") != "success":
                recent_errors.append(
                    {
                        "agent_type": execution.get("agent_type"),
                        "error": execution.get("error"),
                        "timestamp": execution.get("timestamp"),
                    }
                )

        dashboard_data = {
            "timestamp": (
                observability_manager.execution_history[-1].get("timestamp")
                if observability_manager.execution_history
                else None
            ),
            "system_health": {
                "overall_healthy": health_data["overall_healthy"],
                "total_active_executions": len(observability_manager.active_executions),
                "system_issues_count": len(health_data["system_issues"]),
            },
            "agent_status": {
                agent_type.value: {
                    "health": health_data["agent_health"][agent_type.value]["health_status"],
                    "active_executions": active_by_agent.get(agent_type.value, 0),
                    "circuit_breaker": health_data["agent_health"][agent_type.value][
                        "circuit_breaker"
                    ]["state"],
                }
                for agent_type in AgentType
            },
            "performance_overview": performance_summary,
            "recent_errors": recent_errors[-10:],  # Last 10 errors
            "recommendations": recommendations["recommendations"][:5],  # Top 5 recommendations
            "alerts": health_data["system_issues"],
        }

        return JSONResponse(content=dashboard_data)

    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Dashboard data retrieval failed: {str(e)}"
        ) from e


# Health check endpoint specifically for monitoring
@router.get("/healthz", summary="Simple health check endpoint")
async def health_check() -> JSONResponse:
    """
    Simple health check endpoint for external monitoring systems.

    Returns:
        - Basic system status
        - Response time
        - Critical issues only
    """
    try:
        # Quick health check - just verify observability manager is working
        active_count = len(observability_manager.active_executions)
        history_count = len(observability_manager.execution_history)

        # Check for critical issues
        critical_issues = []
        for agent_type in AgentType:
            health = observability_manager.get_agent_health_detailed(agent_type)
            if health["health_status"] == "unhealthy":
                critical_issues.append(f"{agent_type.value}: {', '.join(health['warnings'])}")

        status = "healthy" if not critical_issues else "unhealthy"

        return JSONResponse(
            content={
                "status": status,
                "timestamp": (
                    observability_manager.execution_history[-1].get("timestamp")
                    if observability_manager.execution_history
                    else None
                ),
                "active_executions": active_count,
                "total_processed": history_count,
                "critical_issues": critical_issues,
            }
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": (
                    observability_manager.execution_history[-1].get("timestamp")
                    if observability_manager.execution_history
                    else None
                ),
            },
        )
