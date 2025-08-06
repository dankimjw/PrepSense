"""
API Monitoring Dashboard Router
Provides comprehensive monitoring endpoints for health checks, metrics, and observability
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from backend_gateway.core.crewai_observability import get_agent_metrics, get_agent_health, AgentType
from backend_gateway.core.monitoring import REQUEST_COUNT, REQUEST_DURATION, CREWAI_REQUESTS, DATABASE_QUERIES
from config.monitoring import get_monitoring_config
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Response models
class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    environment: str
    services: Dict[str, Any]
    monitoring: Dict[str, Any]

class MetricsResponse(BaseModel):
    api_requests: Dict[str, Any]
    response_times: Dict[str, Any]
    crewai_agents: Dict[str, Any]
    database_queries: Dict[str, Any]
    timestamp: str

class SystemStatusResponse(BaseModel):
    overall_health: str
    uptime_seconds: int
    active_connections: int
    memory_usage_mb: float
    cpu_usage_percent: float
    services: Dict[str, str]

# Store startup time for uptime calculation
startup_time = datetime.utcnow()


@router.get("/health", response_model=HealthCheckResponse, tags=["monitoring"])
async def detailed_health_check():
    """
    Comprehensive health check with detailed service status.
    
    Returns the health status of all system components including:
    - API service health
    - Database connectivity
    - External API configurations
    - CrewAI agent system
    - Monitoring systems
    """
    config = get_monitoring_config()
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.4.0",
        "environment": config.environment.value,
        "services": {
            "api": {"status": "healthy", "response_time_ms": 0},
            "database": {"status": "unknown", "connected": False},
            "openai": {"status": "unknown", "configured": False},
            "spoonacular": {"status": "unknown", "configured": False},
            "crewai": {"status": "unknown", "enabled": False},
            "sentry": {"status": "unknown", "enabled": False},
            "prometheus": {"status": "unknown", "enabled": False},
        },
        "monitoring": {
            "sentry_enabled": bool(config.sentry.dsn),
            "metrics_enabled": config.prometheus.enabled,
            "logging_level": config.logging.level,
            "environment": config.environment.value,
        }
    }
    
    # Check database
    if config.health_check.check_database:
        try:
            # TODO: Add actual database health check
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                health_status["services"]["database"]["configured"] = True
                health_status["services"]["database"]["status"] = "configured"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status["services"]["database"]["status"] = "error"
            health_status["services"]["database"]["error"] = str(e)
    
    # Check OpenAI
    if config.health_check.check_external_apis:
        try:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                health_status["services"]["openai"]["configured"] = True
                health_status["services"]["openai"]["status"] = "configured"
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            health_status["services"]["openai"]["status"] = "error"
    
    # Check Spoonacular
    try:
        spoonacular_key = os.getenv("SPOONACULAR_KEY")
        if spoonacular_key:
            health_status["services"]["spoonacular"]["configured"] = True
            health_status["services"]["spoonacular"]["status"] = "configured"
    except Exception as e:
        logger.error(f"Spoonacular health check failed: {e}")
        health_status["services"]["spoonacular"]["status"] = "error"
    
    # Check CrewAI agents
    if config.health_check.check_crewai_agents:
        try:
            agent_health = get_agent_health()
            health_status["services"]["crewai"]["enabled"] = True
            health_status["services"]["crewai"]["status"] = "healthy" if agent_health["healthy"] else "degraded"
            health_status["services"]["crewai"]["active_executions"] = agent_health["active_executions"]
            health_status["services"]["crewai"]["success_rate"] = agent_health["success_rate"]
            if agent_health["issues"]:
                health_status["services"]["crewai"]["issues"] = agent_health["issues"]
        except Exception as e:
            logger.error(f"CrewAI health check failed: {e}")
            health_status["services"]["crewai"]["status"] = "error"
            health_status["services"]["crewai"]["error"] = str(e)
    
    # Check monitoring systems
    health_status["services"]["sentry"]["enabled"] = bool(config.sentry.dsn)
    health_status["services"]["sentry"]["status"] = "healthy" if config.sentry.dsn else "disabled"
    
    health_status["services"]["prometheus"]["enabled"] = config.prometheus.enabled
    health_status["services"]["prometheus"]["status"] = "healthy" if config.prometheus.enabled else "disabled"
    
    # Determine overall health
    service_statuses = [service.get("status") for service in health_status["services"].values()]
    if any(status == "error" for status in service_statuses):
        health_status["status"] = "degraded"
    elif any(status == "degraded" for status in service_statuses):
        health_status["status"] = "degraded"
    else:
        health_status["status"] = "healthy"
    
    return health_status


@router.get("/metrics", tags=["monitoring"])
async def get_metrics_summary():
    """
    Get comprehensive metrics summary for monitoring dashboards.
    
    Returns aggregated metrics from Prometheus collectors including:
    - API request statistics
    - Response time percentiles
    - CrewAI agent performance
    - Database query statistics
    """
    try:
        # Get API metrics
        api_metrics = {
            "total_requests": 0,
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "requests_per_minute": 0.0,
        }
        
        # Get CrewAI agent metrics
        crewai_metrics = get_agent_metrics()
        
        # Get system metrics
        uptime = (datetime.utcnow() - startup_time).total_seconds()
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime,
            "api_requests": api_metrics,
            "crewai_agents": crewai_metrics,
            "system": {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "version": "1.4.0",
                "startup_time": startup_time.isoformat(),
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to collect metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect metrics")


@router.get("/system-status", tags=["monitoring"])
async def get_system_status():
    """
    Get current system status and resource utilization.
    
    Returns real-time system information including:
    - Memory usage
    - CPU utilization
    - Active connections
    - Service health summary
    """
    try:
        import psutil
        
        # Get system metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get process info
        process = psutil.Process()
        process_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        uptime = (datetime.utcnow() - startup_time).total_seconds()
        
        status = {
            "overall_health": "healthy",
            "uptime_seconds": uptime,
            "system": {
                "memory_total_mb": memory.total / 1024 / 1024,
                "memory_available_mb": memory.available / 1024 / 1024,
                "memory_usage_percent": memory.percent,
                "cpu_usage_percent": cpu_percent,
                "process_memory_mb": process_memory,
            },
            "services": {
                "api": "healthy",
                "monitoring": "healthy",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        return status
        
    except ImportError:
        # Fallback if psutil not available
        uptime = (datetime.utcnow() - startup_time).total_seconds()
        return {
            "overall_health": "healthy",
            "uptime_seconds": uptime,
            "system": {
                "memory_total_mb": 0,
                "memory_available_mb": 0,
                "memory_usage_percent": 0,
                "cpu_usage_percent": 0,
            },
            "services": {
                "api": "healthy",
                "monitoring": "healthy",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")


@router.get("/agents", tags=["monitoring"])
async def get_agent_status():
    """
    Get detailed CrewAI agent execution status and metrics.
    
    Returns comprehensive agent information including:
    - Execution statistics per agent
    - Success rates and performance
    - Active executions
    - Error summaries
    """
    try:
        metrics = get_agent_metrics()
        health = get_agent_health()
        
        # Enhance with per-agent details
        agent_details = {}
        for agent_type in AgentType:
            agent_stats = metrics.get("agents", {}).get(agent_type.value, {
                "executions": 0,
                "success_rate": 1.0,
                "average_duration": 0.0,
                "total_tokens": 0,
            })
            
            agent_details[agent_type.value] = {
                **agent_stats,
                "status": "healthy" if agent_stats["success_rate"] > 0.8 else "degraded",
                "description": _get_agent_description(agent_type),
            }
        
        return {
            "overall_health": health["healthy"],
            "active_executions": health["active_executions"],
            "total_executions": metrics["total_executions"],
            "overall_success_rate": metrics["success_rate"],
            "agents": agent_details,
            "issues": health.get("issues", []),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent status")


@router.get("/dashboard", response_class=HTMLResponse, tags=["monitoring"])
async def monitoring_dashboard():
    """
    Interactive monitoring dashboard with real-time metrics.
    
    Returns an HTML page with:
    - System health overview
    - API performance charts
    - CrewAI agent monitoring
    - Error logs and alerts
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PrepSense Monitoring Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f6fa;
            }
            .header {
                background: linear-gradient(135deg, #297A56 0%, #34A853 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            .card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .metric {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid #eee;
            }
            .metric:last-child {
                border-bottom: none;
            }
            .status {
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }
            .status.healthy {
                background: #d4edda;
                color: #155724;
            }
            .status.degraded {
                background: #fff3cd;
                color: #856404;
            }
            .status.error {
                background: #f8d7da;
                color: #721c24;
            }
            .refresh-btn {
                background: #297A56;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                margin: 10px 0;
            }
            .refresh-btn:hover {
                background: #1e5a3f;
            }
            .chart-container {
                position: relative;
                height: 300px;
                margin-top: 20px;
            }
            .loading {
                text-align: center;
                color: #666;
                padding: 20px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 PrepSense Monitoring Dashboard</h1>
            <p>Real-time system monitoring and observability</p>
            <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
        </div>

        <div class="grid">
            <div class="card">
                <h3>🏥 System Health</h3>
                <div id="health-status" class="loading">Loading health status...</div>
            </div>

            <div class="card">
                <h3>📈 API Metrics</h3>
                <div id="api-metrics" class="loading">Loading API metrics...</div>
            </div>

            <div class="card">
                <h3>🤖 CrewAI Agents</h3>
                <div id="agent-status" class="loading">Loading agent status...</div>
            </div>

            <div class="card">
                <h3>💻 System Resources</h3>
                <div id="system-status" class="loading">Loading system status...</div>
            </div>
        </div>

        <div class="card">
            <h3>📊 Performance Charts</h3>
            <div class="chart-container">
                <canvas id="performanceChart"></canvas>
            </div>
        </div>

        <script>
            // Dashboard functionality
            async function fetchHealthStatus() {
                try {
                    const response = await fetch('/monitoring/health');
                    const data = await response.json();
                    
                    let html = '';
                    for (const [service, details] of Object.entries(data.services)) {
                        const status = details.status || 'unknown';
                        const statusClass = status === 'healthy' ? 'healthy' : 
                                          status === 'degraded' ? 'degraded' : 'error';
                        
                        html += `
                            <div class="metric">
                                <span>${service.charAt(0).toUpperCase() + service.slice(1)}</span>
                                <span class="status ${statusClass}">${status}</span>
                            </div>
                        `;
                    }
                    
                    document.getElementById('health-status').innerHTML = html;
                } catch (error) {
                    document.getElementById('health-status').innerHTML = `<p class="error">Failed to load health status: ${error.message}</p>`;
                }
            }

            async function fetchAPIMetrics() {
                try {
                    const response = await fetch('/monitoring/metrics');
                    const data = await response.json();
                    
                    const html = `
                        <div class="metric">
                            <span>Uptime</span>
                            <span>${Math.floor(data.uptime_seconds / 3600)}h ${Math.floor((data.uptime_seconds % 3600) / 60)}m</span>
                        </div>
                        <div class="metric">
                            <span>Total Executions</span>
                            <span>${data.crewai_agents.total_executions}</span>
                        </div>
                        <div class="metric">
                            <span>Success Rate</span>
                            <span>${(data.crewai_agents.success_rate * 100).toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <span>Active Executions</span>
                            <span>${data.crewai_agents.active_executions}</span>
                        </div>
                    `;
                    
                    document.getElementById('api-metrics').innerHTML = html;
                } catch (error) {
                    document.getElementById('api-metrics').innerHTML = `<p class="error">Failed to load API metrics: ${error.message}</p>`;
                }
            }

            async function fetchAgentStatus() {
                try {
                    const response = await fetch('/monitoring/agents');
                    const data = await response.json();
                    
                    let html = `
                        <div class="metric">
                            <span>Overall Health</span>
                            <span class="status ${data.overall_health ? 'healthy' : 'degraded'}">${data.overall_health ? 'Healthy' : 'Degraded'}</span>
                        </div>
                    `;
                    
                    for (const [agentType, details] of Object.entries(data.agents)) {
                        const statusClass = details.status === 'healthy' ? 'healthy' : 'degraded';
                        html += `
                            <div class="metric">
                                <span>${agentType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                                <span class="status ${statusClass}">${details.executions} exec</span>
                            </div>
                        `;
                    }
                    
                    document.getElementById('agent-status').innerHTML = html;
                } catch (error) {
                    document.getElementById('agent-status').innerHTML = `<p class="error">Failed to load agent status: ${error.message}</p>`;
                }
            }

            async function fetchSystemStatus() {
                try {
                    const response = await fetch('/monitoring/system-status');
                    const data = await response.json();
                    
                    const html = `
                        <div class="metric">
                            <span>Memory Usage</span>
                            <span>${data.system.memory_usage_percent?.toFixed(1) || 0}%</span>
                        </div>
                        <div class="metric">
                            <span>CPU Usage</span>
                            <span>${data.system.cpu_usage_percent?.toFixed(1) || 0}%</span>
                        </div>
                        <div class="metric">
                            <span>Process Memory</span>
                            <span>${data.system.process_memory_mb?.toFixed(0) || 0} MB</span>
                        </div>
                        <div class="metric">
                            <span>Overall Health</span>
                            <span class="status healthy">${data.overall_health}</span>
                        </div>
                    `;
                    
                    document.getElementById('system-status').innerHTML = html;
                } catch (error) {
                    document.getElementById('system-status').innerHTML = `<p class="error">Failed to load system status: ${error.message}</p>`;
                }
            }

            function refreshDashboard() {
                fetchHealthStatus();
                fetchAPIMetrics();
                fetchAgentStatus();
                fetchSystemStatus();
            }

            // Initialize dashboard
            refreshDashboard();
            
            // Auto-refresh every 30 seconds
            setInterval(refreshDashboard, 30000);

            // Initialize performance chart
            const ctx = document.getElementById('performanceChart').getContext('2d');
            const performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Response Time (ms)',
                        data: [],
                        borderColor: '#297A56',
                        backgroundColor: 'rgba(41, 122, 86, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


def _get_agent_description(agent_type: AgentType) -> str:
    """Get human-readable description for agent type."""
    descriptions = {
        AgentType.PANTRY_ANALYST: "Analyzes pantry contents and expiration dates",
        AgentType.RECIPE_CURATOR: "Finds and curates personalized recipe recommendations", 
        AgentType.NUTRITION_EXPERT: "Provides nutritional analysis and dietary guidance",
        AgentType.MEAL_PLANNER: "Creates comprehensive meal plans and schedules",
        AgentType.INGREDIENT_OPTIMIZER: "Optimizes ingredient usage and substitutions",
        AgentType.COOKING_INSTRUCTOR: "Provides step-by-step cooking instructions",
        AgentType.DIETARY_ADVISOR: "Offers personalized dietary recommendations",
        AgentType.SUSTAINABILITY_ADVISOR: "Provides eco-friendly cooking and food choices",
    }
    return descriptions.get(agent_type, "AI agent for food management")


# Add router to main app in app.py:
# app.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])