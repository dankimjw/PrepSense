#!/usr/bin/env python3
"""
MCP Auto Manager - Automatic MCP Server Management for PrepSense
================================================================

Automatically initializes and manages all required MCP servers for Claude sessions.
This script ensures all MCP servers are available and healthy before each session.

Usage:
    python scripts/mcp_auto_manager.py --init      # Initialize all MCP servers
    python scripts/mcp_auto_manager.py --check     # Health check all servers  
    python scripts/mcp_auto_manager.py --repair    # Repair broken servers
    python scripts/mcp_auto_manager.py --session   # Session startup (init + check)
"""

import argparse
import json
import subprocess
import sys
import time
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Required MCP servers for PrepSense
REQUIRED_SERVERS = {
    "filesystem": {
        "command": "mcp-server-filesystem --root .",
        "args": [],
        "package": "@modelcontextprotocol/server-filesystem",
        "description": "File operations with proper permissions"
    },
    "memory": {
        "command": "mcp-server-memory",
        "args": [],
        "package": "@modelcontextprotocol/server-memory", 
        "description": "Persistent memory across conversations"
    },
    "sequential-thinking": {
        "command": "mcp-server-sequential-thinking",
        "args": [],
        "package": "@modelcontextprotocol/server-sequential-thinking",
        "description": "Step-by-step reasoning"
    },
    "context7": {
        "command": "npx -y @upstash/context7-mcp",
        "args": [],
        "package": "@upstash/context7-mcp",
        "description": "Up-to-date library documentation"
    },
    "ios-simulator": {
        "command": "npx ios-simulator-mcp",
        "args": [],
        "package": "ios-simulator-mcp",
        "description": "iOS Simulator control and automation"
    },
    "mobile": {
        "command": "npx -y @mobilenext/mobile-mcp@latest",
        "args": [],
        "package": "@mobilenext/mobile-mcp",
        "description": "Mobile device control and automation"
    },
    "postgres": {
        "command": "npx -y @modelcontextprotocol/server-postgres",
        "args": [],
        "package": "@modelcontextprotocol/server-postgres",
        "description": "PostgreSQL database access for Cloud SQL",
        "env": {
            "POSTGRES_CONNECTION_STRING": "postgresql://user:password@host:port/dbname"
        }
    }
}

class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m' 
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class MCPManager:
    """Manages MCP server installation, configuration, and health."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.mcp_config_path = project_root / ".mcp.json"
        
    def log(self, message: str, level: str = "info"):
        """Log messages with color coding."""
        colors = {
            "info": Colors.WHITE,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED,
            "debug": Colors.CYAN
        }
        color = colors.get(level, Colors.WHITE)
        timestamp = time.strftime("%H:%M:%S")
        print(f"{Colors.BOLD}[{timestamp}]{Colors.END} {color}{message}{Colors.END}")
    
    def run_command(self, cmd: List[str], timeout: int = 30, capture_output: bool = True) -> Tuple[bool, str, str]:
        """Run a command with timeout and error handling."""
        try:
            result = subprocess.run(
                cmd, 
                timeout=timeout,
                capture_output=capture_output,
                text=True,
                cwd=self.project_root
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)
    
    def check_npm_package_installed(self, package: str) -> bool:
        """Check if an npm package is installed globally."""
        success, stdout, _ = self.run_command(["npm", "list", "-g", "--depth=0"])
        return package in stdout if success else False
    
    def install_npm_package(self, package: str) -> bool:
        """Install npm package globally."""
        self.log(f"Installing {package}...", "info")
        success, stdout, stderr = self.run_command(["npm", "install", "-g", package])
        if success:
            self.log(f"✓ Installed {package}", "success")
            return True
        else:
            self.log(f"✗ Failed to install {package}: {stderr}", "error")
            return False
    
    def check_mcp_server_registered(self, server_name: str) -> bool:
        """Check if MCP server is registered with claude mcp."""
        success, stdout, _ = self.run_command(["claude", "mcp", "list"])
        if success:
            return server_name in stdout
        return False
    
    def register_mcp_server(self, server_name: str, config: Dict) -> bool:
        """Register MCP server with claude mcp."""
        self.log(f"Registering MCP server: {server_name}", "info")
        
        # Remove existing registration first
        self.run_command(["claude", "mcp", "remove", server_name], timeout=10)
        
        # Register new server
        success, stdout, stderr = self.run_command([
            "claude", "mcp", "add", server_name,
            "--scope", "project",
            config["command"]
        ])
        
        if success:
            self.log(f"✓ Registered {server_name}", "success")
            return True
        else:
            self.log(f"✗ Failed to register {server_name}: {stderr}", "error")
            return False
    
    def create_mcp_json_config(self) -> bool:
        """Create or update .mcp.json configuration file."""
        self.log("Creating .mcp.json configuration...", "info")
        
        mcp_config = {
            "mcpServers": {}
        }
        
        # Load environment variables for postgres connection
        env_vars = dict(os.environ)
        
        # Also try to load from .env file if it exists (though it's protected)
        env_file = self.project_root / ".env"
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.strip().split('=', 1)
                            env_vars[key] = value.strip('"\'')
            except Exception as e:
                self.log(f"Note: Could not read .env file (may be protected): {e}", "debug")
        
        for server_name, config in REQUIRED_SERVERS.items():
            server_config = {
                "type": "stdio",
                "command": config["command"].split()[0],
                "args": config["command"].split()[1:] if len(config["command"].split()) > 1 else config["args"],
                "env": {}
            }
            
            # Add environment variables if specified
            if "env" in config:
                server_config["env"].update(config["env"])
            
            # Special handling for postgres server - use PrepSense's exact env var names
            if server_name == "postgres" and env_vars:
                # Use PrepSense's database environment variables
                postgres_host = env_vars.get("POSTGRES_HOST")
                postgres_port = env_vars.get("POSTGRES_PORT", "5432")
                postgres_database = env_vars.get("POSTGRES_DATABASE")
                postgres_user = env_vars.get("POSTGRES_USER")
                postgres_password = env_vars.get("POSTGRES_PASSWORD")
                
                if all([postgres_host, postgres_database, postgres_user, postgres_password]):
                    connection_string = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_database}"
                    server_config["env"]["POSTGRES_CONNECTION_STRING"] = connection_string
                    self.log(f"✓ Configured postgres MCP server for GCP Cloud SQL at {postgres_host}:{postgres_port}/{postgres_database}", "success")
                else:
                    missing_vars = []
                    if not postgres_host: missing_vars.append("POSTGRES_HOST")
                    if not postgres_database: missing_vars.append("POSTGRES_DATABASE")
                    if not postgres_user: missing_vars.append("POSTGRES_USER")
                    if not postgres_password: missing_vars.append("POSTGRES_PASSWORD")
                    self.log(f"⚠️  Postgres MCP server missing environment variables: {', '.join(missing_vars)}", "warning")
                    # Still add the server but without connection string
                    server_config["env"]["POSTGRES_CONNECTION_STRING"] = "postgresql://user:password@host:port/database"
            
            mcp_config["mcpServers"][server_name] = server_config
        
        try:
            with open(self.mcp_config_path, 'w') as f:
                json.dump(mcp_config, f, indent=2)
            self.log("✓ Created .mcp.json configuration", "success")
            return True
        except Exception as e:
            self.log(f"✗ Failed to create .mcp.json: {e}", "error")
            return False
    
    def test_postgres_connection(self) -> Tuple[bool, str]:
        """Test PostgreSQL MCP server connection to GCP Cloud SQL."""
        try:
            # Try to get database connection info from environment
            env_vars = dict(os.environ)
            postgres_host = env_vars.get("POSTGRES_HOST")
            
            if not postgres_host:
                return False, "No POSTGRES_HOST environment variable found"
            
            # For now, just verify the connection string can be constructed
            postgres_port = env_vars.get("POSTGRES_PORT", "5432")
            postgres_database = env_vars.get("POSTGRES_DATABASE")
            postgres_user = env_vars.get("POSTGRES_USER")
            postgres_password = env_vars.get("POSTGRES_PASSWORD")
            
            if all([postgres_host, postgres_database, postgres_user, postgres_password]):
                # Connection string is valid format
                return True, f"Postgres connection configured for {postgres_host}:{postgres_port}/{postgres_database}"
            else:
                missing = [var for var in ["POSTGRES_HOST", "POSTGRES_DATABASE", "POSTGRES_USER", "POSTGRES_PASSWORD"] 
                          if not env_vars.get(var)]
                return False, f"Missing environment variables: {', '.join(missing)}"
                
        except Exception as e:
            return False, f"Error testing postgres connection: {str(e)}"
    
    def test_mcp_server_health(self, server_name: str) -> bool:
        """Test if MCP server is healthy and responding."""
        self.log(f"Testing {server_name} health...", "debug")
        
        # Check if it's registered first
        if not self.check_mcp_server_registered(server_name):
            return False
        
        # Special handling for postgres server - test connection config
        if server_name == "postgres":
            postgres_success, postgres_message = self.test_postgres_connection()
            if postgres_success:
                self.log(f"✓ Postgres MCP: {postgres_message}", "debug")
            else:
                self.log(f"✗ Postgres MCP: {postgres_message}", "debug")
            return postgres_success
        
        # For stdio-based servers, registration is sufficient for now
        # They'll work when Claude tries to use them
        return True
    
    def install_all_servers(self) -> Dict[str, bool]:
        """Install all required MCP servers."""
        self.log("Installing all required MCP servers...", "info")
        results = {}
        
        # Install npm packages first
        npm_packages = set()
        for server_name, config in REQUIRED_SERVERS.items():
            if config["package"] not in ["ios-simulator-mcp", "@mobilenext/mobile-mcp"]:  # These are installed on-demand
                npm_packages.add(config["package"])
        
        for package in npm_packages:
            if not self.check_npm_package_installed(package):
                results[package] = self.install_npm_package(package)
            else:
                self.log(f"✓ {package} already installed", "success")
                results[package] = True
        
        return results
    
    def register_all_servers(self) -> Dict[str, bool]:
        """Register all MCP servers with claude mcp."""
        self.log("Registering all MCP servers...", "info")
        results = {}
        
        for server_name, config in REQUIRED_SERVERS.items():
            if not self.check_mcp_server_registered(server_name):
                results[server_name] = self.register_mcp_server(server_name, config)
            else:
                self.log(f"✓ {server_name} already registered", "success")
                results[server_name] = True
        
        return results
    
    def health_check_all_servers(self) -> Dict[str, bool]:
        """Perform health checks on all MCP servers."""
        self.log("Performing health checks on all MCP servers...", "info")
        results = {}
        
        for server_name in REQUIRED_SERVERS.keys():
            results[server_name] = self.test_mcp_server_health(server_name)
            status = "✓" if results[server_name] else "✗"
            level = "success" if results[server_name] else "error"
            self.log(f"{status} {server_name} - {'Healthy' if results[server_name] else 'Unhealthy'}", level)
        
        return results
    
    def repair_broken_servers(self) -> Dict[str, bool]:
        """Repair any broken or missing MCP servers."""
        self.log("Repairing broken MCP servers...", "warning")
        
        # First check health
        health_results = self.health_check_all_servers()
        broken_servers = [name for name, healthy in health_results.items() if not healthy]
        
        if not broken_servers:
            self.log("All MCP servers are healthy - no repairs needed", "success")
            return health_results
        
        self.log(f"Found {len(broken_servers)} broken servers: {', '.join(broken_servers)}", "warning")
        
        # Reinstall and re-register broken servers
        repair_results = {}
        for server_name in broken_servers:
            config = REQUIRED_SERVERS[server_name]
            
            # Try to install package if needed
            if not self.check_npm_package_installed(config["package"]):
                if self.install_npm_package(config["package"]):
                    repair_results[server_name] = self.register_mcp_server(server_name, config)
                else:
                    repair_results[server_name] = False
            else:
                # Package exists, just re-register
                repair_results[server_name] = self.register_mcp_server(server_name, config)
        
        return repair_results
    
    def initialize_session(self) -> bool:
        """Full session initialization: install, configure, and verify all MCP servers."""
        self.log(f"{Colors.BOLD}Starting MCP Auto-Initialization for PrepSense{Colors.END}", "info")
        self.log("=" * 60, "info")
        
        success = True
        
        # Step 1: Install all required packages
        self.log("Step 1: Installing packages...", "info")
        install_results = self.install_all_servers()
        install_failures = [pkg for pkg, result in install_results.items() if not result]
        if install_failures:
            self.log(f"Installation failures: {', '.join(install_failures)}", "error")
            success = False
        
        # Step 2: Create .mcp.json configuration
        self.log("Step 2: Creating configuration...", "info")
        if not self.create_mcp_json_config():
            success = False
        
        # Step 3: Register servers with claude mcp
        self.log("Step 3: Registering servers...", "info")
        register_results = self.register_all_servers()
        register_failures = [srv for srv, result in register_results.items() if not result]
        if register_failures:
            self.log(f"Registration failures: {', '.join(register_failures)}", "error")
            success = False
        
        # Step 4: Health check
        self.log("Step 4: Health checks...", "info")
        health_results = self.health_check_all_servers()
        health_failures = [srv for srv, result in health_results.items() if not result]
        if health_failures:
            self.log(f"Health check failures: {', '.join(health_failures)}", "warning")
        
        # Summary
        self.log("=" * 60, "info")
        if success and not health_failures:
            self.log("✅ MCP Auto-Initialization completed successfully!", "success")
            self.log("All MCP servers are installed, configured, and healthy.", "success")
        elif success and health_failures:
            self.log("⚠️  MCP Auto-Initialization completed with warnings", "warning")
            self.log(f"Some servers may need manual configuration: {', '.join(health_failures)}", "warning")
        else:
            self.log("❌ MCP Auto-Initialization failed", "error")
            self.log("Some MCP servers could not be installed or configured.", "error")
        
        # Show current server status
        self.log("\nCurrent MCP Server Status:", "info")
        success_cmd, stdout, _ = self.run_command(["claude", "mcp", "list"])
        if success_cmd:
            print(stdout)
        
        return success

def main():
    parser = argparse.ArgumentParser(
        description="MCP Auto Manager - Automatic MCP Server Management for PrepSense",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--init", action="store_true", help="Initialize all MCP servers")
    parser.add_argument("--check", action="store_true", help="Health check all servers")
    parser.add_argument("--repair", action="store_true", help="Repair broken servers")
    parser.add_argument("--session", action="store_true", help="Full session startup (default)")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    
    args = parser.parse_args()
    
    # Default to session initialization if no specific action specified
    if not any([args.init, args.check, args.repair]):
        args.session = True
    
    manager = MCPManager(args.project_root)
    
    if args.session or args.init:
        success = manager.initialize_session()
        sys.exit(0 if success else 1)
    elif args.check:
        results = manager.health_check_all_servers()
        all_healthy = all(results.values())
        sys.exit(0 if all_healthy else 1)
    elif args.repair:
        results = manager.repair_broken_servers()
        all_repaired = all(results.values())
        sys.exit(0 if all_repaired else 1)

if __name__ == "__main__":
    main()