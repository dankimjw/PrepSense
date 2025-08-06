#!/usr/bin/env python3
"""Main entry point for the PrepSense backend application."""

import uvicorn
import os
import sys
import logging
import signal
import asyncio
from datetime import datetime
from typing import Dict, Any

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import the FastAPI app
from app import app


def check_system_health() -> Dict[str, Any]:
    """Check system health and dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    health_status["checks"]["python_version"] = {
        "status": "ok",
        "version": python_version,
        "required": ">=3.9"
    }
    
    # Check required modules
    required_modules = [
        "fastapi",
        "uvicorn", 
        "openai",
        "psycopg2",
        "sqlalchemy",
        "pydantic",
        "httpx"
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            health_status["checks"][f"module_{module}"] = {"status": "ok"}
        except ImportError:
            health_status["checks"][f"module_{module}"] = {"status": "missing"}
            health_status["status"] = "degraded"
    
    # Check disk space
    try:
        import shutil
        free_space = shutil.disk_usage('.').free / (1024**3)  # GB
        health_status["checks"]["disk_space"] = {
            "status": "ok" if free_space > 1 else "warning",
            "free_gb": round(free_space, 2)
        }
    except Exception as e:
        health_status["checks"]["disk_space"] = {"status": "error", "error": str(e)}
    
    return health_status


def setup_signal_handlers():
    """Setup graceful shutdown handlers"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        print(f"\n🛑 Received shutdown signal, stopping server gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def validate_environment() -> Dict[str, Any]:
    """Validate environment configuration"""
    # Import here to avoid circular imports
    from core.config_utils import get_openai_api_key
    from core.config import settings
    
    # Critical environment variables
    critical_vars = {
        "OPENAI_API_KEY": {
            "description": "OpenAI API access for chat and recipe features",
            "required": True,
            "sensitive": True,
            "validator": lambda: get_openai_api_key()  # Will raise if not found
        },
        "SPOONACULAR_API_KEY": {
            "description": "Spoonacular recipe API",
            "required": True,
            "sensitive": True,
            "validator": lambda: settings.SPOONACULAR_API_KEY or None
        },
        "POSTGRES_HOST": {
            "description": "PostgreSQL database host (Google Cloud SQL)",
            "required": True,
            "sensitive": False,
            "validator": lambda: settings.POSTGRES_HOST or None
        },
        "POSTGRES_DATABASE": {
            "description": "PostgreSQL database name",
            "required": True,
            "sensitive": False,
            "validator": lambda: settings.POSTGRES_DATABASE or None
        },
        "POSTGRES_USER": {
            "description": "PostgreSQL database user",
            "required": True,
            "sensitive": False,
            "validator": lambda: settings.POSTGRES_USER or None
        },
        "POSTGRES_PASSWORD": {
            "description": "PostgreSQL database password",
            "required": True,
            "sensitive": True,
            "validator": lambda: settings.POSTGRES_PASSWORD or None
        }
    }
    
    # Optional environment variables
    optional_vars = {
        "GOOGLE_APPLICATION_CREDENTIALS": {
            "description": "Google Cloud credentials for image processing",
            "required": False,
            "sensitive": True
        },
        "UNSPLASH_ACCESS_KEY": {
            "description": "Unsplash API for recipe images",
            "required": False,
            "sensitive": True
        },
        "REDIS_URL": {
            "description": "Redis for caching",
            "required": False,
            "sensitive": True
        },
        "SENTRY_DSN": {
            "description": "Sentry for error tracking",
            "required": False,
            "sensitive": True
        }
    }
    
    env_status = {
        "critical": {},
        "optional": {},
        "all_critical_configured": True
    }
    
    # Check critical variables
    for var, config in critical_vars.items():
        try:
            # Use validator if provided, otherwise check env var directly
            if "validator" in config:
                value = config["validator"]()
                is_set = bool(value)
            else:
                value = os.getenv(var)
                is_set = bool(value)
            
            env_status["critical"][var] = {
                "configured": is_set,
                "description": config["description"],
                "value": "***" if is_set and config["sensitive"] else value,
                "error": None
            }
            
            if not is_set:
                env_status["all_critical_configured"] = False
                env_status["critical"][var]["error"] = f"{var} is not configured"
                
        except Exception as e:
            env_status["all_critical_configured"] = False
            env_status["critical"][var] = {
                "configured": False,
                "description": config["description"],
                "value": None,
                "error": str(e)
            }
    
    # Check optional variables
    for var, config in optional_vars.items():
        value = os.getenv(var)
        is_set = bool(value)
        
        env_status["optional"][var] = {
            "configured": is_set,
            "description": config["description"],
            "value": "***" if is_set and config["sensitive"] else value
        }
    
    return env_status


def display_startup_banner(host: str, port: int, reload: bool):
    """Display startup banner with system information"""
    print(f"\n{'='*80}")
    print(f"🚀 PREPSENSE BACKEND SERVER")
    print(f"{'='*80}")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Auto-reload: {reload}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"💻 Platform: {sys.platform}")
    print(f"{'='*80}")


def display_api_endpoints(port: int):
    """Display available API endpoints"""
    print(f"📚 API DOCUMENTATION:")
    print(f"   - Swagger UI: http://localhost:{port}/docs")
    print(f"   - ReDoc: http://localhost:{port}/redoc")
    print(f"   - OpenAPI JSON: http://localhost:{port}/api/v1/openapi.json")
    print(f"{'='*80}")


def display_multi_agent_info(port: int):
    """Display multi-agent system information"""
    print(f"🤖 MULTI-AGENT SYSTEM:")
    print(f"   Status: ✅ Enabled")
    print(f"   Agents: 8 specialized AI agents")
    print(f"   Architecture: Sequential processing with tool delegation")
    print(f"   ")
    print(f"   📡 Endpoints:")
    print(f"   - POST /api/v1/chat/multi-agent/recommend - Get recipe recommendations")
    print(f"   - GET  /api/v1/chat/multi-agent/status    - Check system status")
    print(f"   - POST /api/v1/chat/multi-agent/test      - Test system functionality")
    print(f"   ")
    print(f"   🔧 Agent Roles:")
    print(f"   - Pantry Scanner: Database inventory access")
    print(f"   - Ingredient Filter: Expiration date validation")
    print(f"   - Preference Specialist: User dietary restrictions")
    print(f"   - Recipe Researcher: Recipe database search")
    print(f"   - Nutritional Analyst: Health and nutrition scoring")
    print(f"   - Recipe Scorer: Relevance and preference ranking")
    print(f"   - Recipe Evaluator: Feasibility validation")
    print(f"   - Response Formatter: User-friendly output")
    print(f"{'='*80}")


def display_environment_status(env_status: Dict[str, Any]):
    """Display environment configuration status"""
    print(f"🔍 ENVIRONMENT STATUS:")
    
    # Critical variables
    print(f"   Critical Configuration:")
    for var, config in env_status["critical"].items():
        status = "✅" if config["configured"] else "❌"
        print(f"   {status} {var}: {config['description']}")
    
    # Optional variables
    configured_optional = sum(1 for c in env_status["optional"].values() if c["configured"])
    total_optional = len(env_status["optional"])
    print(f"   ")
    print(f"   Optional Configuration ({configured_optional}/{total_optional} configured):")
    for var, config in env_status["optional"].items():
        status = "✅" if config["configured"] else "⚪"
        print(f"   {status} {var}: {config['description']}")
    
    if not env_status["all_critical_configured"]:
        print(f"   ")
        print(f"   ⚠️  Warning: Some critical environment variables are missing.")
        print(f"       The application may have limited functionality.")
        print(f"       Please check the MULTI_AGENT_README.md for setup instructions.")
    
    print(f"{'='*80}")


def display_system_health(health: Dict[str, Any]):
    """Display system health status"""
    print(f"🏥 SYSTEM HEALTH:")
    print(f"   Overall Status: {health['status'].upper()}")
    
    for check_name, check_result in health["checks"].items():
        status_icon = "✅" if check_result["status"] == "ok" else "⚠️" if check_result["status"] == "warning" else "❌"
        print(f"   {status_icon} {check_name.replace('_', ' ').title()}: {check_result['status']}")
        
        if "version" in check_result:
            print(f"      Version: {check_result['version']}")
        if "free_gb" in check_result:
            print(f"      Free Space: {check_result['free_gb']} GB")
    
    print(f"{'='*80}")


def display_test_info():
    """Display testing information"""
    print(f"🧪 TESTING:")
    print(f"   - Unit Tests: python run_all_crew_ai_tests.py")
    print(f"   - Integration Tests: python -m pytest tests/ -v")
    print(f"   - Load Tests: python -m pytest tests/services/test_crew_ai_performance.py -v")
    print(f"   - Test Coverage: 105 tests across 8 categories")
    print(f"{'='*80}")


def main():
    """Main application entry point"""
    # Setup signal handlers
    setup_signal_handlers()
    
    # Get configuration from environment or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    workers = int(os.getenv("WORKERS", "1"))
    
    # Display startup information
    display_startup_banner(host, port, reload)
    
    # Check system health
    health = check_system_health()
    display_system_health(health)
    
    # Validate environment
    env_status = validate_environment()
    display_environment_status(env_status)
    
    # Check if all critical environment variables are configured
    if not env_status["all_critical_configured"]:
        print(f"\n❌ CRITICAL CONFIGURATION ERROR")
        print(f"{'='*80}")
        print(f"The following required API keys are missing or invalid:\n")
        
        for var, config in env_status["critical"].items():
            if not config["configured"]:
                print(f"  ❌ {var}:")
                print(f"     Description: {config['description']}")
                if config.get("error"):
                    print(f"     Error: {config['error']}")
                print()
        
        print(f"📚 Setup Instructions:")
        print(f"{'='*80}")
        print(f"1. Create a .env file in the project root (not in backend_gateway/)")
        print(f"   Location: /path/to/PrepSense/.env\n")
        print(f"2. Add the required configuration:")
        print(f"   # Database Configuration (Google Cloud SQL)")
        print(f"   POSTGRES_HOST=35.184.61.42")
        print(f"   POSTGRES_PORT=5432")
        print(f"   POSTGRES_DATABASE=prepsense")
        print(f"   POSTGRES_USER=postgres")
        print(f"   POSTGRES_PASSWORD=your-password-here\n")
        print(f"   # API Keys")
        print(f"   OPENAI_API_KEY=sk-your-openai-key-here")
        print(f"   SPOONACULAR_API_KEY=your-spoonacular-key-here\n")
        print(f"3. Get your credentials:")
        print(f"   - Database password: Ask your team lead")
        print(f"   - OpenAI: https://platform.openai.com/api-keys")
        print(f"   - Spoonacular: https://spoonacular.com/food-api (free tier available)\n")
        print(f"4. For detailed setup help, see:")
        print(f"   - Automated setup: docs/BACKEND_SETUP_GUIDE.md")
        print(f"   - Manual setup: docs/MANUAL_SETUP_GUIDE.md")
        print(f"{'='*80}")
        print(f"\n🛑 Server cannot start without required configuration.")
        sys.exit(1)
    
    # Display API information
    display_api_endpoints(port)
    display_multi_agent_info(port)
    display_test_info()
    
    print(f"🚀 SERVER STARTING...")
    print(f"   Press Ctrl+C to stop the server")
    print(f"   Logs will appear below")
    print(f"{'='*80}\n")
    
    try:
        # Configure uvicorn
        config = {
            "app": "app:app",
            "host": host,
            "port": port,
            "reload": reload,
            "log_level": log_level.lower(),
            "access_log": True,
            "date_header": True,
            "server_header": True
        }
        
        # Add workers only in production
        if not reload and workers > 1:
            config["workers"] = workers
            logger.info(f"Running with {workers} workers")
        
        # Run the server
        uvicorn.run(**config)
        
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
        logger.info("Server stopped by user interrupt")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"\n❌ Server failed to start: {e}")
        print(f"   Check the logs above for more details")
        sys.exit(1)
    finally:
        print(f"\n{'='*80}")
        print(f"🏁 PrepSense Backend Server Shutdown Complete")
        print(f"   Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")


if __name__ == "__main__":
    main()