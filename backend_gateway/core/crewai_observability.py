"""
Enhanced CrewAI Agent Observability Integration
Provides comprehensive monitoring, error tracking, and performance analysis for all 8 PrepSense agents
"""

import asyncio
import functools
import logging
import threading
import time
import traceback
import uuid
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

import sentry_sdk
from prometheus_client import Counter, Gauge, Histogram

from backend_gateway.core.monitoring import capture_crewai_metrics, report_error

logger = logging.getLogger(__name__)


# CrewAI Agent Types for PrepSense (matching actual implementation)
class AgentType(str, Enum):
    """Enumeration of all PrepSense CrewAI agents."""

    FOOD_CATEGORIZER = "food_categorizer"
    FRESH_FILTER = "fresh_filter"
    JUDGE_THYME = "judge_thyme"
    NUTRI_CHECK = "nutri_check"
    PANTRY_LEDGER = "pantry_ledger"
    RECIPE_SEARCH = "recipe_search"
    UNIT_CANON = "unit_canon"
    USER_PREFERENCES = "user_preferences"


# Prometheus metrics for CrewAI agents
AGENT_EXECUTION_COUNT = Counter(
    "crewai_agent_executions_total",
    "Total number of CrewAI agent executions",
    ["agent_type", "status", "task_type"],
)

AGENT_EXECUTION_DURATION = Histogram(
    "crewai_agent_execution_seconds",
    "Duration of CrewAI agent executions",
    ["agent_type", "task_type"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, float("inf")),
)

AGENT_ACTIVE_TASKS = Gauge(
    "crewai_agent_active_tasks", "Number of currently active agent tasks", ["agent_type"]
)

AGENT_TOKEN_USAGE = Counter(
    "crewai_agent_tokens_total",
    "Total tokens used by CrewAI agents",
    ["agent_type", "model", "token_type"],  # token_type: prompt, completion
)

AGENT_ERROR_COUNT = Counter(
    "crewai_agent_errors_total",
    "Total number of agent errors",
    ["agent_type", "error_type", "severity"],
)

AGENT_RETRY_COUNT = Counter(
    "crewai_agent_retries_total",
    "Total number of agent retry attempts",
    ["agent_type", "retry_reason"],
)

AGENT_CIRCUIT_BREAKER_STATE = Gauge(
    "crewai_agent_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=half-open, 2=open)",
    ["agent_type"],
)

AGENT_QUEUE_DEPTH = Gauge(
    "crewai_agent_queue_depth", "Current queue depth for agent executions", ["agent_type"]
)


class ErrorType(str, Enum):
    """Categorized error types for better monitoring."""

    VALIDATION_ERROR = "validation"
    TIMEOUT_ERROR = "timeout"
    RESOURCE_ERROR = "resource"
    API_ERROR = "api"
    DATA_ERROR = "data"
    NETWORK_ERROR = "network"
    AUTHENTICATION_ERROR = "authentication"
    RATE_LIMIT_ERROR = "rate_limit"
    UNKNOWN_ERROR = "unknown"


@dataclass
class CircuitBreakerState:
    """Circuit breaker state for agent failure management."""

    failure_count: int = 0
    last_failure_time: Optional[float] = None
    state: str = "closed"  # closed, half-open, open
    failure_threshold: int = 5
    reset_timeout: int = 300  # 5 minutes
    half_open_max_calls: int = 3
    half_open_calls: int = 0

    def can_execute(self) -> bool:
        """Check if execution should be allowed based on circuit breaker state."""
        current_time = time.time()

        if self.state == "closed":
            return True
        elif self.state == "open":
            if (
                self.last_failure_time
                and current_time - self.last_failure_time > self.reset_timeout
            ):
                self.state = "half-open"
                self.half_open_calls = 0
                return True
            return False
        elif self.state == "half-open":
            return self.half_open_calls < self.half_open_max_calls
        return False

    def record_success(self):
        """Record successful execution."""
        if self.state == "half-open":
            self.state = "closed"
        self.failure_count = 0
        self.half_open_calls += 1 if self.state == "half-open" else 0

    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == "half-open" or self.failure_count >= self.failure_threshold:
            self.state = "open"

    def get_state_value(self) -> int:
        """Get numeric state value for Prometheus."""
        state_map = {"closed": 0, "half-open": 1, "open": 2}
        return state_map.get(self.state, 0)


@dataclass
class RetryConfig:
    """Configuration for agent execution retry logic."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        if self.exponential_backoff:
            delay = min(self.base_delay * (2**attempt), self.max_delay)
        else:
            delay = self.base_delay

        if self.jitter:
            import random

            delay *= 0.5 + random.random() * 0.5  # Add 0-50% jitter

        return delay


class AgentExecutionContext:
    """Context manager for tracking agent execution with full observability."""

    def __init__(
        self,
        agent_type: AgentType,
        task_type: str,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        retry_config: Optional[RetryConfig] = None,
        enable_circuit_breaker: bool = True,
        timeout_seconds: Optional[float] = None,
    ):
        self.agent_type = agent_type
        self.task_type = task_type
        self.task_id = task_id or str(uuid.uuid4())
        self.user_id = user_id
        self.metadata = metadata or {}
        self.retry_config = retry_config or RetryConfig()
        self.enable_circuit_breaker = enable_circuit_breaker
        self.timeout_seconds = timeout_seconds

        self.start_time = None
        self.end_time = None
        self.duration = None
        self.status = "pending"
        self.error = None
        self.result = None
        self.token_usage = {"prompt": 0, "completion": 0}
        self.sentry_transaction = None
        self.retry_count = 0
        self.decision_points = []  # Track agent reasoning
        self.tool_usage = []  # Track tool calls
        self.performance_metrics = {}
        self.sanitized_input = None  # PII-safe input logging

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.fail(exc_val)
        else:
            self.succeed()

    def start(self):
        """Start execution tracking."""
        self.start_time = datetime.utcnow()
        self.status = "running"

        # Increment active tasks counter
        AGENT_ACTIVE_TASKS.labels(agent_type=self.agent_type.value).inc()

        # Start Sentry transaction
        self.sentry_transaction = sentry_sdk.start_transaction(
            op=f"crewai.agent.{self.agent_type.value}",
            name=f"{self.agent_type.value}:{self.task_type}",
            tags={
                "agent_type": self.agent_type.value,
                "task_type": self.task_type,
                "task_id": self.task_id,
            },
        )

        # Add structured logging
        logger.info(
            "CrewAI agent execution started",
            extra={
                "agent_type": self.agent_type.value,
                "task_type": self.task_type,
                "task_id": self.task_id,
                "user_id": self.user_id,
                "metadata": self.metadata,
            },
        )

        return self

    def succeed(self, result: Any = None):
        """Mark execution as successful."""
        self.end_time = datetime.utcnow()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = "success"
        self.result = result

        self._record_completion()

    def fail(self, error: Exception):
        """Mark execution as failed."""
        self.end_time = datetime.utcnow()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = "error"
        self.error = error

        self._record_completion()
        self._handle_error(error)

    def add_token_usage(self, prompt_tokens: int, completion_tokens: int, model: str = "unknown"):
        """Track token usage for cost monitoring."""
        self.token_usage["prompt"] += prompt_tokens
        self.token_usage["completion"] += completion_tokens

        # Record in Prometheus
        AGENT_TOKEN_USAGE.labels(
            agent_type=self.agent_type.value, model=model, token_type="prompt"
        ).inc(prompt_tokens)

        AGENT_TOKEN_USAGE.labels(
            agent_type=self.agent_type.value, model=model, token_type="completion"
        ).inc(completion_tokens)

    def set_metadata(self, key: str, value: Any):
        """Add metadata to the execution context."""
        self.metadata[key] = value

        # Add to Sentry transaction if active
        if self.sentry_transaction:
            self.sentry_transaction.set_tag(f"meta.{key}", str(value))

    def add_decision_point(
        self,
        decision: str,
        reasoning: str,
        confidence: float = 1.0,
        context: Optional[dict[str, Any]] = None,
    ):
        """Track agent decision points for debugging and analysis."""
        self.decision_points.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "decision": decision,
                "reasoning": reasoning,
                "confidence": confidence,
                "context": context or {},
            }
        )

    def record_tool_usage(
        self,
        tool_name: str,
        duration_seconds: float,
        success: bool,
        inputs: Optional[dict[str, Any]] = None,
        outputs: Optional[dict[str, Any]] = None,
    ):
        """Record tool usage for performance analysis."""
        self.tool_usage.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "tool_name": tool_name,
                "duration_seconds": duration_seconds,
                "success": success,
                "inputs": self._sanitize_data(inputs) if inputs else None,
                "outputs": self._sanitize_data(outputs) if outputs else None,
            }
        )

    def sanitize_input_data(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize input data for safe logging."""
        self.sanitized_input = self._sanitize_data(input_data)
        return self.sanitized_input

    def _sanitize_data(self, data: Any, max_length: int = 200) -> Any:
        """Remove PII and truncate large data for safe logging."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Skip sensitive keys
                if any(
                    sensitive in key.lower()
                    for sensitive in ["password", "token", "key", "secret", "email", "phone"]
                ):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = self._sanitize_data(value, max_length)
            return sanitized
        elif isinstance(data, (list, tuple)):
            return [self._sanitize_data(item, max_length) for item in data[:10]]  # Limit list size
        elif isinstance(data, str):
            if len(data) > max_length:
                return data[:max_length] + "..."
            return data
        else:
            return data

    def _record_completion(self):
        """Record completion metrics and logs."""
        # Decrement active tasks counter
        AGENT_ACTIVE_TASKS.labels(agent_type=self.agent_type.value).dec()

        # Record execution count
        AGENT_EXECUTION_COUNT.labels(
            agent_type=self.agent_type.value, status=self.status, task_type=self.task_type
        ).inc()

        # Record execution duration
        AGENT_EXECUTION_DURATION.labels(
            agent_type=self.agent_type.value, task_type=self.task_type
        ).observe(self.duration)

        # Update legacy monitoring
        capture_crewai_metrics(self.agent_type.value, self.status)

        # Finish Sentry transaction
        if self.sentry_transaction:
            self.sentry_transaction.set_status(
                "ok" if self.status == "success" else "internal_error"
            )
            self.sentry_transaction.set_data("duration", self.duration)
            self.sentry_transaction.set_data("token_usage", self.token_usage)
            self.sentry_transaction.finish()

        # Structured logging
        log_level = logging.INFO if self.status == "success" else logging.ERROR
        logger.log(
            log_level,
            "CrewAI agent execution completed",
            extra={
                "agent_type": self.agent_type.value,
                "task_type": self.task_type,
                "task_id": self.task_id,
                "user_id": self.user_id,
                "status": self.status,
                "duration_seconds": self.duration,
                "token_usage": self.token_usage,
                "metadata": self.metadata,
                "error": str(self.error) if self.error else None,
            },
        )

    def _handle_error(self, error: Exception):
        """Handle and categorize errors for better observability."""
        error_type_class = type(error).__name__
        error_message = str(error).lower()

        # Categorize error type for better monitoring
        if "timeout" in error_message:
            error_type = ErrorType.TIMEOUT_ERROR
        elif "validation" in error_message or "invalid" in error_message:
            error_type = ErrorType.VALIDATION_ERROR
        elif "authentication" in error_message or "unauthorized" in error_message:
            error_type = ErrorType.AUTHENTICATION_ERROR
        elif "rate limit" in error_message or "quota" in error_message:
            error_type = ErrorType.RATE_LIMIT_ERROR
        elif "api" in error_message or "http" in error_message or "request" in error_message:
            error_type = ErrorType.API_ERROR
        elif "network" in error_message or "connection" in error_message:
            error_type = ErrorType.NETWORK_ERROR
        elif "memory" in error_message or "resource" in error_message:
            error_type = ErrorType.RESOURCE_ERROR
        elif "data" in error_message or "format" in error_message or "parse" in error_message:
            error_type = ErrorType.DATA_ERROR
        else:
            error_type = ErrorType.UNKNOWN_ERROR

        # Categorize error severity
        severity = "medium"
        if error_type in [ErrorType.TIMEOUT_ERROR, ErrorType.RATE_LIMIT_ERROR]:
            severity = "low"
        elif error_type in [ErrorType.AUTHENTICATION_ERROR, ErrorType.VALIDATION_ERROR]:
            severity = "high"
        elif error_type in [ErrorType.RESOURCE_ERROR, ErrorType.API_ERROR]:
            severity = "critical"

        # Record error metrics
        AGENT_ERROR_COUNT.labels(
            agent_type=self.agent_type.value, error_type=error_type.value, severity=severity
        ).inc()

        # Enhanced error context for debugging
        error_context = {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "duration": self.duration,
            "token_usage": self.token_usage,
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "decision_points_count": len(self.decision_points),
            "tools_used_count": len(self.tool_usage),
            "sanitized_input": self.sanitized_input,
            "error_type_categorized": error_type.value,
            "error_class": error_type_class,
            "traceback": traceback.format_exc(),
        }

        # Send to Sentry with enhanced context
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("agent_type", self.agent_type.value)
            scope.set_tag("task_type", self.task_type)
            scope.set_tag("error_severity", severity)
            scope.set_tag("error_type_categorized", error_type.value)
            scope.set_context("agent_execution", error_context)
            sentry_sdk.capture_exception(error)

        # Also use existing error reporting
        report_error(
            error,
            {
                "component": "crewai_agent",
                "agent_type": self.agent_type.value,
                "task_type": self.task_type,
                "error_type": error_type.value,
            },
        )


class CrewAIObservabilityManager:
    """Central manager for CrewAI observability across all agents."""

    def __init__(self):
        self.active_executions: dict[str, AgentExecutionContext] = {}
        self.execution_history: list[dict[str, Any]] = []
        self.max_history = 1000  # Keep last 1000 executions
        self.circuit_breakers: dict[str, CircuitBreakerState] = {}
        self.agent_queues: dict[str, deque] = defaultdict(deque)
        self.performance_stats: dict[str, dict[str, Any]] = defaultdict(dict)
        self._lock = threading.Lock()

    def get_circuit_breaker(self, agent_type: AgentType) -> CircuitBreakerState:
        """Get or create circuit breaker for agent."""
        with self._lock:
            if agent_type.value not in self.circuit_breakers:
                self.circuit_breakers[agent_type.value] = CircuitBreakerState()
            return self.circuit_breakers[agent_type.value]

    def create_execution_context(
        self,
        agent_type: AgentType,
        task_type: str,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        retry_config: Optional[RetryConfig] = None,
        enable_circuit_breaker: bool = True,
        timeout_seconds: Optional[float] = None,
    ) -> AgentExecutionContext:
        """Create a new execution context for tracking."""
        # Check circuit breaker before creating context
        circuit_breaker = self.get_circuit_breaker(agent_type)
        if enable_circuit_breaker and not circuit_breaker.can_execute():
            raise RuntimeError(
                f"Agent {agent_type.value} is temporarily unavailable due to circuit breaker (state: {circuit_breaker.state})"
            )

        context = AgentExecutionContext(
            agent_type=agent_type,
            task_type=task_type,
            task_id=task_id,
            user_id=user_id,
            metadata=metadata,
            retry_config=retry_config,
            enable_circuit_breaker=enable_circuit_breaker,
            timeout_seconds=timeout_seconds,
        )

        with self._lock:
            self.active_executions[context.task_id] = context
            # Update queue metrics
            AGENT_QUEUE_DEPTH.labels(agent_type=agent_type.value).inc()

        return context

    def complete_execution_context(self, context: AgentExecutionContext):
        """Complete and clean up execution context."""
        with self._lock:
            # Update circuit breaker
            circuit_breaker = self.get_circuit_breaker(context.agent_type)
            if context.status == "success":
                circuit_breaker.record_success()
            else:
                circuit_breaker.record_failure()

            # Update circuit breaker metrics
            AGENT_CIRCUIT_BREAKER_STATE.labels(agent_type=context.agent_type.value).set(
                circuit_breaker.get_state_value()
            )

            # Update queue metrics
            AGENT_QUEUE_DEPTH.labels(agent_type=context.agent_type.value).dec()

            # Move to history if completed
            if context.task_id in self.active_executions:
                self.active_executions.pop(context.task_id)
                self._add_to_history(context)

    def _add_to_history(self, context: AgentExecutionContext):
        """Add completed execution to history."""
        self.execution_history.append(
            {
                "task_id": context.task_id,
                "agent_type": context.agent_type.value,
                "task_type": context.task_type,
                "user_id": context.user_id,
                "status": context.status,
                "duration": context.duration,
                "token_usage": context.token_usage,
                "metadata": context.metadata,
                "retry_count": context.retry_count,
                "decision_points_count": len(context.decision_points),
                "tools_used_count": len(context.tool_usage),
                "timestamp": context.start_time.isoformat() if context.start_time else None,
                "error": str(context.error) if context.error else None,
            }
        )

    def reset_circuit_breaker(self, agent_type: AgentType):
        """Manually reset circuit breaker for an agent."""
        with self._lock:
            if agent_type.value in self.circuit_breakers:
                self.circuit_breakers[agent_type.value] = CircuitBreakerState()
                AGENT_CIRCUIT_BREAKER_STATE.labels(agent_type=agent_type.value).set(0)
                logger.info(f"Circuit breaker reset for agent: {agent_type.value}")

    def get_agent_health_detailed(self, agent_type: AgentType) -> dict[str, Any]:
        """Get detailed health information for specific agent."""
        with self._lock:
            circuit_breaker = self.get_circuit_breaker(agent_type)

            # Get recent executions for this agent
            recent_executions = [
                h
                for h in self.execution_history[-100:]  # Last 100 executions
                if h.get("agent_type") == agent_type.value
            ]

            # Calculate statistics
            total_executions = len(recent_executions)
            successful_executions = len(
                [h for h in recent_executions if h.get("status") == "success"]
            )
            failed_executions = total_executions - successful_executions

            success_rate = (
                (successful_executions / total_executions) if total_executions > 0 else 1.0
            )

            # Calculate average duration
            durations = [h.get("duration", 0) for h in recent_executions if h.get("duration")]
            avg_duration = sum(durations) / len(durations) if durations else 0.0

            # Get error breakdown
            error_breakdown = defaultdict(int)
            for execution in recent_executions:
                if execution.get("status") != "success" and execution.get("error"):
                    error_type = "unknown"
                    error_msg = execution.get("error", "").lower()
                    if "timeout" in error_msg:
                        error_type = "timeout"
                    elif "validation" in error_msg:
                        error_type = "validation"
                    elif "api" in error_msg or "http" in error_msg:
                        error_type = "api"
                    error_breakdown[error_type] += 1

            # Determine health status
            health_status = "healthy"
            warnings = []

            if circuit_breaker.state == "open":
                health_status = "unhealthy"
                warnings.append("Circuit breaker is open due to excessive failures")
            elif circuit_breaker.state == "half-open":
                health_status = "degraded"
                warnings.append("Circuit breaker is in half-open state")
            elif success_rate < 0.8 and total_executions > 5:
                health_status = "degraded"
                warnings.append(f"Low success rate: {success_rate:.1%}")

            # Check for performance regression
            if len(durations) > 10:
                recent_avg = sum(durations[-5:]) / 5 if len(durations) >= 5 else avg_duration
                if recent_avg > avg_duration * 1.5:
                    if health_status == "healthy":
                        health_status = "degraded"
                    warnings.append("Performance regression detected")

            return {
                "agent_type": agent_type.value,
                "health_status": health_status,
                "warnings": warnings,
                "circuit_breaker": {
                    "state": circuit_breaker.state,
                    "failure_count": circuit_breaker.failure_count,
                    "last_failure_time": circuit_breaker.last_failure_time,
                    "failure_threshold": circuit_breaker.failure_threshold,
                },
                "performance": {
                    "total_executions": total_executions,
                    "successful_executions": successful_executions,
                    "failed_executions": failed_executions,
                    "success_rate": success_rate,
                    "average_duration_seconds": avg_duration,
                    "error_breakdown": dict(error_breakdown),
                },
                "active_executions": len(
                    [ctx for ctx in self.active_executions.values() if ctx.agent_type == agent_type]
                ),
            }

    def get_execution_stats(self, agent_type: Optional[AgentType] = None) -> dict[str, Any]:
        """Get execution statistics for monitoring dashboards."""
        stats = {
            "total_executions": len(self.execution_history),
            "active_executions": len(self.active_executions),
            "success_rate": 0.0,
            "average_duration": 0.0,
            "total_tokens": 0,
            "agents": {},
        }

        if not self.execution_history:
            return stats

        # Filter by agent type if specified
        history = self.execution_history
        if agent_type:
            history = [h for h in history if h.get("agent_type") == agent_type.value]

        # Calculate overall stats
        successful = [h for h in history if h.get("status") == "success"]
        stats["success_rate"] = len(successful) / len(history) if history else 0.0

        durations = [h.get("duration", 0) for h in history if h.get("duration")]
        stats["average_duration"] = sum(durations) / len(durations) if durations else 0.0

        # Calculate per-agent stats
        agent_stats = {}
        for agent in AgentType:
            agent_history = [h for h in history if h.get("agent_type") == agent.value]
            if agent_history:
                agent_successful = [h for h in agent_history if h.get("status") == "success"]
                agent_durations = [h.get("duration", 0) for h in agent_history if h.get("duration")]

                agent_stats[agent.value] = {
                    "executions": len(agent_history),
                    "success_rate": len(agent_successful) / len(agent_history),
                    "average_duration": (
                        sum(agent_durations) / len(agent_durations) if agent_durations else 0.0
                    ),
                    "total_tokens": sum(
                        h.get("token_usage", {}).get("prompt", 0)
                        + h.get("token_usage", {}).get("completion", 0)
                        for h in agent_history
                    ),
                }

        stats["agents"] = agent_stats
        return stats

    def cleanup_completed_executions(self):
        """Clean up completed executions to prevent memory leaks."""
        completed_ids = [
            task_id
            for task_id, context in self.active_executions.items()
            if context.status in ["success", "error"]
        ]

        for task_id in completed_ids:
            context = self.active_executions.pop(task_id)

            # Add to history
            self.execution_history.append(
                {
                    "task_id": context.task_id,
                    "agent_type": context.agent_type.value,
                    "task_type": context.task_type,
                    "user_id": context.user_id,
                    "status": context.status,
                    "duration": context.duration,
                    "token_usage": context.token_usage,
                    "metadata": context.metadata,
                    "timestamp": context.start_time.isoformat() if context.start_time else None,
                    "error": str(context.error) if context.error else None,
                }
            )

        # Trim history if too large
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history :]


# Global observability manager instance
observability_manager = CrewAIObservabilityManager()


def monitor_crewai_execution(
    agent_type: AgentType,
    task_type: str,
    user_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    retry_config: Optional[RetryConfig] = None,
    enable_circuit_breaker: bool = True,
    timeout_seconds: Optional[float] = None,
    sanitize_inputs: bool = True,
):
    """
    Enhanced decorator for monitoring CrewAI agent execution with comprehensive observability,
    retry logic, circuit breaker, and performance tracking.

    Usage:
    @monitor_crewai_execution(
        AgentType.FOOD_CATEGORIZER,
        "categorize_food",
        retry_config=RetryConfig(max_retries=3, base_delay=1.0),
        timeout_seconds=30.0
    )
    async def categorize_food(self, food_items):
        # Agent implementation
        pass
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract dynamic user_id from kwargs if available
            dynamic_user_id = kwargs.get("user_id", user_id)

            # Sanitize input data for logging
            input_data = kwargs.copy() if sanitize_inputs else {}

            context = observability_manager.create_execution_context(
                agent_type=agent_type,
                task_type=task_type,
                user_id=dynamic_user_id,
                metadata=metadata,
                retry_config=retry_config,
                enable_circuit_breaker=enable_circuit_breaker,
                timeout_seconds=timeout_seconds,
            )

            # Sanitize and store input data
            context.sanitize_input_data(input_data)

            last_exception = None

            try:
                with context:
                    # Retry loop with exponential backoff
                    for attempt in range(context.retry_config.max_retries + 1):
                        try:
                            if attempt > 0:
                                context.retry_count = attempt

                                # Record retry attempt
                                AGENT_RETRY_COUNT.labels(
                                    agent_type=agent_type.value, retry_reason="execution_failed"
                                ).inc()

                                # Calculate delay for retry
                                delay = context.retry_config.get_delay(attempt)

                                logger.warning(
                                    f"Retrying agent execution (attempt {attempt + 1}/{context.retry_config.max_retries + 1})",
                                    extra={
                                        "agent_type": agent_type.value,
                                        "task_type": task_type,
                                        "task_id": context.task_id,
                                        "user_id": dynamic_user_id,
                                        "retry_delay_seconds": delay,
                                        "previous_error": (
                                            str(last_exception) if last_exception else None
                                        ),
                                    },
                                )

                                await asyncio.sleep(delay)

                            # Execute function with optional timeout
                            if timeout_seconds:
                                result = await asyncio.wait_for(
                                    func(*args, **kwargs), timeout=timeout_seconds
                                )
                            else:
                                result = await func(*args, **kwargs)

                            # Success - record and return
                            context.succeed(result)
                            observability_manager.complete_execution_context(context)
                            return result

                        except asyncio.TimeoutError as e:
                            last_exception = e
                            logger.error(
                                f"Agent execution timed out (attempt {attempt + 1})",
                                extra={
                                    "agent_type": agent_type.value,
                                    "task_type": task_type,
                                    "task_id": context.task_id,
                                    "timeout_seconds": timeout_seconds,
                                },
                            )

                            if attempt == context.retry_config.max_retries:
                                break

                        except Exception as e:
                            last_exception = e

                            # Don't retry validation errors or authentication errors
                            error_msg = str(e).lower()
                            if any(
                                term in error_msg
                                for term in [
                                    "validation",
                                    "invalid",
                                    "authentication",
                                    "unauthorized",
                                ]
                            ):
                                logger.error(
                                    "Non-retryable error in agent execution",
                                    extra={
                                        "agent_type": agent_type.value,
                                        "task_type": task_type,
                                        "task_id": context.task_id,
                                        "error": str(e),
                                        "error_type": "non_retryable",
                                    },
                                )
                                break

                            logger.error(
                                f"Agent execution failed (attempt {attempt + 1})",
                                extra={
                                    "agent_type": agent_type.value,
                                    "task_type": task_type,
                                    "task_id": context.task_id,
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                },
                            )

                            if attempt == context.retry_config.max_retries:
                                break

                    # All retries exhausted - fail the context
                    context.fail(last_exception)
                    observability_manager.complete_execution_context(context)
                    raise last_exception

            finally:
                # Clean up completed executions periodically
                observability_manager.cleanup_completed_executions()

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, convert to async for consistency
            return asyncio.run(async_wrapper(*args, **kwargs))

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


@contextmanager
def agent_execution_span(
    agent_type: AgentType,
    task_type: str,
    user_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
):
    """
    Context manager for manual agent execution tracking.

    Usage:
    with agent_execution_span(AgentType.RECIPE_CURATOR, "curate_recipes") as span:
        span.set_metadata("recipe_count", 10)
        result = do_work()
        span.add_token_usage(50, 100, "gpt-4")
    """
    context = observability_manager.create_execution_context(
        agent_type=agent_type, task_type=task_type, user_id=user_id, metadata=metadata
    )

    with context:
        yield context


def get_agent_metrics() -> dict[str, Any]:
    """Get current agent metrics for health checks and dashboards."""
    return observability_manager.get_execution_stats()


def get_agent_health() -> dict[str, Any]:
    """Get comprehensive system health status for all agents."""
    all_agent_health = {}
    overall_healthy = True
    system_issues = []

    # Check health for each agent type
    for agent_type in AgentType:
        agent_health = observability_manager.get_agent_health_detailed(agent_type)
        all_agent_health[agent_type.value] = agent_health

        if agent_health["health_status"] == "unhealthy":
            overall_healthy = False
            system_issues.extend(
                [f"{agent_type.value}: {warning}" for warning in agent_health["warnings"]]
            )
        elif agent_health["health_status"] == "degraded" and overall_healthy:
            system_issues.extend(
                [f"{agent_type.value}: {warning}" for warning in agent_health["warnings"]]
            )

    # Get overall statistics
    stats = get_agent_metrics()

    return {
        "overall_healthy": overall_healthy,
        "timestamp": datetime.utcnow().isoformat(),
        "system_stats": {
            "total_active_executions": stats["active_executions"],
            "overall_success_rate": stats["success_rate"],
            "total_executions": stats["total_executions"],
        },
        "system_issues": system_issues,
        "agent_health": all_agent_health,
    }


def get_agent_performance_report() -> dict[str, Any]:
    """Get detailed performance report for all agents."""
    performance_data = {}

    for agent_type in AgentType:
        health_data = observability_manager.get_agent_health_detailed(agent_type)

        # Calculate additional performance metrics
        recent_executions = [
            h
            for h in observability_manager.execution_history[-200:]
            if h.get("agent_type") == agent_type.value
        ]

        # Performance trends
        if len(recent_executions) >= 10:
            # Split recent executions into two halves for trend analysis
            mid_point = len(recent_executions) // 2
            older_half = recent_executions[:mid_point]
            newer_half = recent_executions[mid_point:]

            older_success_rate = len([h for h in older_half if h.get("status") == "success"]) / len(
                older_half
            )
            newer_success_rate = len([h for h in newer_half if h.get("status") == "success"]) / len(
                newer_half
            )

            older_avg_duration = sum(h.get("duration", 0) for h in older_half) / len(older_half)
            newer_avg_duration = sum(h.get("duration", 0) for h in newer_half) / len(newer_half)

            performance_trend = {
                "success_rate_trend": (
                    "improving" if newer_success_rate > older_success_rate else "declining"
                ),
                "performance_trend": (
                    "improving" if newer_avg_duration < older_avg_duration else "declining"
                ),
                "success_rate_change": newer_success_rate - older_success_rate,
                "duration_change_percent": (
                    ((newer_avg_duration - older_avg_duration) / older_avg_duration * 100)
                    if older_avg_duration > 0
                    else 0
                ),
            }
        else:
            performance_trend = {
                "success_rate_trend": "insufficient_data",
                "performance_trend": "insufficient_data",
                "success_rate_change": 0,
                "duration_change_percent": 0,
            }

        performance_data[agent_type.value] = {
            "health": health_data,
            "trends": performance_trend,
            "recent_activity": {
                "last_24h_executions": len(
                    [
                        h
                        for h in recent_executions
                        if h.get("timestamp")
                        and (
                            datetime.utcnow() - datetime.fromisoformat(h["timestamp"])
                        ).total_seconds()
                        < 86400
                    ]
                )
            },
        }

    return {"timestamp": datetime.utcnow().isoformat(), "agents": performance_data}


def reset_agent_circuit_breaker(agent_type: AgentType) -> dict[str, Any]:
    """Reset circuit breaker for a specific agent."""
    observability_manager.reset_circuit_breaker(agent_type)
    return {
        "agent_type": agent_type.value,
        "action": "circuit_breaker_reset",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success",
    }


def get_agent_debugging_info(
    agent_type: AgentType, task_id: Optional[str] = None
) -> dict[str, Any]:
    """Get detailed debugging information for an agent or specific task."""
    debugging_info = {"agent_type": agent_type.value, "timestamp": datetime.utcnow().isoformat()}

    if task_id:
        # Get specific execution details
        execution = observability_manager.active_executions.get(task_id)
        if execution:
            debugging_info["execution"] = {
                "task_id": execution.task_id,
                "status": execution.status,
                "start_time": execution.start_time.isoformat() if execution.start_time else None,
                "duration": execution.duration,
                "retry_count": execution.retry_count,
                "decision_points": execution.decision_points,
                "tool_usage": execution.tool_usage,
                "metadata": execution.metadata,
                "sanitized_input": execution.sanitized_input,
            }
        else:
            # Check execution history
            historical_execution = next(
                (h for h in observability_manager.execution_history if h.get("task_id") == task_id),
                None,
            )
            if historical_execution:
                debugging_info["execution"] = historical_execution
            else:
                debugging_info["error"] = f"Task {task_id} not found"
    else:
        # Get recent executions for this agent
        recent_executions = [
            h
            for h in observability_manager.execution_history[-50:]
            if h.get("agent_type") == agent_type.value
        ]

        debugging_info["recent_executions"] = recent_executions
        debugging_info["health"] = observability_manager.get_agent_health_detailed(agent_type)

    return debugging_info


# Export commonly used components
__all__ = [
    "AgentType",
    "ErrorType",
    "AgentExecutionContext",
    "RetryConfig",
    "CircuitBreakerState",
    "monitor_crewai_execution",
    "agent_execution_span",
    "get_agent_metrics",
    "get_agent_health",
    "get_agent_performance_report",
    "reset_agent_circuit_breaker",
    "get_agent_debugging_info",
    "observability_manager",
]
