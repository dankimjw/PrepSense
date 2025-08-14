"""Enhanced Tool Monitoring for CrewAI Tools

This module provides monitoring and observability features for CrewAI tools,
tracking their usage, performance, and integration with agents.
"""

import time
import logging
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
from dataclasses import dataclass
from contextlib import contextmanager

from crewai.tools import BaseTool
from prometheus_client import Counter, Histogram

from backend_gateway.core.logging_config import get_logger
from backend_gateway.core.crewai_observability import observability_manager

logger = get_logger("crewai.tool_monitoring")

# Prometheus metrics for tool monitoring
TOOL_EXECUTION_COUNT = Counter(
    "crewai_tool_executions_total",
    "Total tool executions",
    ["tool_name", "agent_type", "status"]
)

TOOL_EXECUTION_DURATION = Histogram(
    "crewai_tool_execution_seconds",
    "Tool execution duration",
    ["tool_name", "agent_type"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, float('inf'))
)


@dataclass
class ToolExecutionContext:
    """Context for tracking tool execution."""
    tool_name: str
    agent_type: Optional[str] = None
    task_id: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.error is None


class MonitoredBaseTool(BaseTool):
    """Enhanced BaseTool with built-in monitoring capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execution_history: List[ToolExecutionContext] = []
        self.max_history = 100
    
    def _run_with_monitoring(self, *args, **kwargs) -> Any:
        """Execute tool with comprehensive monitoring."""
        context = ToolExecutionContext(
            tool_name=self.name,
            input_data=self._sanitize_inputs(kwargs),
            metadata={"args_count": len(args), "kwargs_count": len(kwargs)}
        )
        
        # Try to get agent context if available
        try:
            # Look for active agent execution context
            for execution_context in observability_manager.active_executions.values():
                if execution_context.status == "running":
                    context.agent_type = execution_context.agent_type.value
                    context.task_id = execution_context.task_id
                    break
        except Exception:
            pass  # Continue without agent context
        
        context.start_time = time.time()
        
        try:
            # Execute the actual tool
            result = self._run(*args, **kwargs)
            context.end_time = time.time()
            context.output_data = self._sanitize_outputs(result)
            
            # Record successful execution
            self._record_execution_metrics(context)
            self._add_to_history(context)
            
            # Update agent context if available
            if context.task_id and context.task_id in observability_manager.active_executions:
                agent_context = observability_manager.active_executions[context.task_id]
                agent_context.record_tool_usage(
                    tool_name=self.name,
                    duration_seconds=context.duration_seconds,
                    success=True,
                    inputs=context.input_data,
                    outputs=context.output_data
                )
            
            return result
            
        except Exception as e:
            context.end_time = time.time()
            context.error = e
            
            # Record failed execution
            self._record_execution_metrics(context)
            self._add_to_history(context)
            
            # Update agent context if available
            if context.task_id and context.task_id in observability_manager.active_executions:
                agent_context = observability_manager.active_executions[context.task_id]
                agent_context.record_tool_usage(
                    tool_name=self.name,
                    duration_seconds=context.duration_seconds,
                    success=False,
                    inputs=context.input_data,
                    outputs=None
                )
            
            # Log error
            logger.error(
                f"Tool execution failed",
                extra={
                    "tool_name": self.name,
                    "agent_type": context.agent_type,
                    "task_id": context.task_id,
                    "duration_seconds": context.duration_seconds,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
            raise
    
    def _record_execution_metrics(self, context: ToolExecutionContext):
        """Record Prometheus metrics for tool execution."""
        status = "success" if context.success else "error"
        
        TOOL_EXECUTION_COUNT.labels(
            tool_name=context.tool_name,
            agent_type=context.agent_type or "unknown",
            status=status
        ).inc()
        
        TOOL_EXECUTION_DURATION.labels(
            tool_name=context.tool_name,
            agent_type=context.agent_type or "unknown"
        ).observe(context.duration_seconds)
        
        # Structured logging
        logger.info(
            f"Tool execution completed",
            extra={
                "tool_name": context.tool_name,
                "agent_type": context.agent_type,
                "task_id": context.task_id,
                "duration_seconds": context.duration_seconds,
                "status": status,
                "input_size": len(str(context.input_data)) if context.input_data else 0,
                "output_size": len(str(context.output_data)) if context.output_data else 0
            }
        )
    
    def _add_to_history(self, context: ToolExecutionContext):
        """Add execution to history."""
        self.execution_history.append(context)
        
        # Trim history if too large
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]
    
    def _sanitize_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize inputs for safe logging."""
        return self._sanitize_data(inputs)
    
    def _sanitize_outputs(self, outputs: Any) -> Any:
        """Sanitize outputs for safe logging."""
        return self._sanitize_data(outputs)
    
    def _sanitize_data(self, data: Any, max_length: int = 200) -> Any:
        """Remove PII and truncate large data."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in ["password", "token", "key", "secret", "email", "phone"]):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = self._sanitize_data(value, max_length)
            return sanitized
        elif isinstance(data, (list, tuple)):
            return [self._sanitize_data(item, max_length) for item in data[:10]]
        elif isinstance(data, str):
            if len(data) > max_length:
                return data[:max_length] + "..."
            return data
        else:
            return data
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for this tool."""
        if not self.execution_history:
            return {
                "tool_name": self.name,
                "total_executions": 0,
                "success_rate": 0.0,
                "average_duration": 0.0
            }
        
        successful = len([ctx for ctx in self.execution_history if ctx.success])
        total = len(self.execution_history)
        durations = [ctx.duration_seconds for ctx in self.execution_history]
        
        return {
            "tool_name": self.name,
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": total - successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_duration": sum(durations) / len(durations) if durations else 0.0,
            "min_duration": min(durations) if durations else 0.0,
            "max_duration": max(durations) if durations else 0.0,
            "last_execution": self.execution_history[-1].start_time if self.execution_history else None
        }


def monitor_tool_execution(tool_name: str, agent_type: Optional[str] = None):
    """Decorator for monitoring tool execution."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            context = ToolExecutionContext(
                tool_name=tool_name,
                agent_type=agent_type,
                input_data=kwargs.copy(),
                metadata={"args_count": len(args), "kwargs_count": len(kwargs)}
            )
            
            context.start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                context.end_time = time.time()
                context.output_data = result
                
                # Record metrics
                TOOL_EXECUTION_COUNT.labels(
                    tool_name=tool_name,
                    agent_type=agent_type or "unknown",
                    status="success"
                ).inc()
                
                TOOL_EXECUTION_DURATION.labels(
                    tool_name=tool_name,
                    agent_type=agent_type or "unknown"
                ).observe(context.duration_seconds)
                
                logger.info(
                    f"Tool execution successful",
                    extra={
                        "tool_name": tool_name,
                        "agent_type": agent_type,
                        "duration_seconds": context.duration_seconds
                    }
                )
                
                return result
                
            except Exception as e:
                context.end_time = time.time()
                context.error = e
                
                # Record error metrics
                TOOL_EXECUTION_COUNT.labels(
                    tool_name=tool_name,
                    agent_type=agent_type or "unknown",
                    status="error"
                ).inc()
                
                logger.error(
                    f"Tool execution failed",
                    extra={
                        "tool_name": tool_name,
                        "agent_type": agent_type,
                        "duration_seconds": context.duration_seconds,
                        "error": str(e)
                    }
                )
                
                raise
        
        return wrapper
    return decorator


@contextmanager
def tool_execution_span(tool_name: str, agent_type: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    """Context manager for manual tool execution monitoring."""
    context = ToolExecutionContext(
        tool_name=tool_name,
        agent_type=agent_type,
        metadata=metadata or {}
    )
    
    context.start_time = time.time()
    
    try:
        yield context
        context.end_time = time.time()
        
        # Record success metrics
        TOOL_EXECUTION_COUNT.labels(
            tool_name=tool_name,
            agent_type=agent_type or "unknown",
            status="success"
        ).inc()
        
        TOOL_EXECUTION_DURATION.labels(
            tool_name=tool_name,
            agent_type=agent_type or "unknown"
        ).observe(context.duration_seconds)
        
    except Exception as e:
        context.end_time = time.time()
        context.error = e
        
        # Record error metrics
        TOOL_EXECUTION_COUNT.labels(
            tool_name=tool_name,
            agent_type=agent_type or "unknown",
            status="error"
        ).inc()
        
        logger.error(
            f"Tool execution context failed",
            extra={
                "tool_name": tool_name,
                "agent_type": agent_type,
                "duration_seconds": context.duration_seconds,
                "error": str(e)
            }
        )
        
        raise


class ToolPerformanceAnalyzer:
    """Analyzer for tool performance across agents."""
    
    @staticmethod
    def get_tool_usage_report() -> Dict[str, Any]:
        """Get comprehensive tool usage report."""
        # This would aggregate data from all monitored tools
        # For now, return placeholder structure
        return {
            "timestamp": time.time(),
            "total_tools": 0,
            "most_used_tools": [],
            "slowest_tools": [],
            "error_prone_tools": [],
            "agent_tool_usage": {}
        }
    
    @staticmethod
    def detect_tool_performance_issues() -> List[Dict[str, Any]]:
        """Detect performance issues with tools."""
        issues = []
        
        # This would analyze tool metrics and detect issues
        # For now, return placeholder
        return issues
    
    @staticmethod
    def get_tool_recommendations() -> List[Dict[str, Any]]:
        """Get optimization recommendations for tools."""
        recommendations = []
        
        # This would analyze usage patterns and suggest optimizations
        # For now, return placeholder
        return recommendations


# Utility functions for tool monitoring
def get_all_tool_stats() -> Dict[str, Any]:
    """Get statistics for all monitored tools."""
    # This would collect stats from all MonitoredBaseTool instances
    return {
        "timestamp": time.time(),
        "tools": {}
    }


def reset_tool_metrics():
    """Reset all tool metrics (useful for testing)."""
    # This would reset Prometheus counters if supported
    logger.info("Tool metrics reset requested")


__all__ = [
    "MonitoredBaseTool",
    "ToolExecutionContext",
    "monitor_tool_execution",
    "tool_execution_span",
    "ToolPerformanceAnalyzer",
    "get_all_tool_stats",
    "reset_tool_metrics"
]