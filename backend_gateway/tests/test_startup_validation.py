#!/usr/bin/env python3
"""
Startup validation tests for PrepSense
Tests all critical scenarios when the app is first launched
"""

import unittest
import subprocess
import time
import requests
import json
import os
from typing import Dict, List
from pathlib import Path

class StartupValidationTests(unittest.TestCase):
    """Test suite for validating app startup scenarios"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.backend_url = "http://localhost:8001"
        cls.test_results = []
        
    def test_01_environment_setup(self):
        """Test: Environment variables and configuration"""
        print("\n🧪 Testing environment setup...")
        
        # Check .env file exists
        env_path = Path("/Users/danielkim/_Capstone/PrepSense/.env")
        self.assertTrue(env_path.exists(), ".env file not found")
        
        # Check critical environment variables
        required_vars = [
            "DATABASE_URL",
            "OPENAI_API_KEY", 
            "SPOONACULAR_API_KEY",
            "JWT_SECRET_KEY"
        ]
        
        # Load .env file
        env_vars = {}
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
        
        for var in required_vars:
            self.assertIn(var, env_vars, f"Missing {var} in .env")
            self.assertNotEqual(env_vars[var], "", f"{var} is empty")
            self.assertNotIn("changeme", env_vars[var].lower(), f"{var} contains placeholder value")
            
    def test_02_backend_startup(self):
        """Test: Backend starts without errors"""
        print("\n🧪 Testing backend startup...")
        
        # Check if backend is running
        try:
            response = requests.get(f"{self.backend_url}/api/v1/health", timeout=5)
            self.assertEqual(response.status_code, 200, "Backend health check failed")
            
            health_data = response.json()
            self.assertIn("status", health_data)
            self.assertEqual(health_data["status"], "healthy")
            
        except requests.exceptions.ConnectionError:
            self.fail("Backend is not running - cannot test startup")
            
    def test_03_database_connectivity(self):
        """Test: Database connection on startup"""
        print("\n🧪 Testing database connectivity...")
        
        response = requests.get(f"{self.backend_url}/api/v1/health", timeout=5)
        health_data = response.json()
        
        # Check database status
        self.assertIn("database", health_data)
        self.assertTrue(health_data["database"]["connected"], "Database not connected")
        self.assertIn("google-cloud-sql", health_data["database"].get("type", "").lower(), 
                     "Not connected to Google Cloud SQL")
        
    def test_04_api_initialization(self):
        """Test: All API endpoints initialize correctly"""
        print("\n🧪 Testing API initialization...")
        
        # Get OpenAPI schema
        response = requests.get(f"{self.backend_url}/openapi.json")
        self.assertEqual(response.status_code, 200)
        
        schema = response.json()
        paths = schema.get("paths", {})
        
        # Check critical endpoints exist
        critical_endpoints = [
            "/api/v1/health",
            "/api/v1/units", 
            "/api/v1/ingredients",
            "/api/v1/recipes",
            "/api/v1/shopping-list",
            "/api/v1/stats/comprehensive"
        ]
        
        for endpoint in critical_endpoints:
            self.assertIn(endpoint, paths, f"Missing endpoint: {endpoint}")
            
    def test_05_external_api_connectivity(self):
        """Test: External API connections work on startup"""
        print("\n🧪 Testing external API connectivity...")
        
        # Test Spoonacular connectivity through our API
        response = requests.get(f"{self.backend_url}/api/v1/demo/recipes")
        self.assertEqual(response.status_code, 200, "Spoonacular API not accessible")
        
        recipes = response.json()
        self.assertIsInstance(recipes, list)
        self.assertGreater(len(recipes), 0, "No recipes returned from Spoonacular")
        
    def test_06_frontend_bundle_validity(self):
        """Test: Frontend bundle builds correctly"""
        print("\n🧪 Testing frontend bundle...")
        
        # Check Metro bundler is running
        try:
            response = requests.get("http://localhost:8082", timeout=5)
            self.assertEqual(response.status_code, 200, "Metro bundler not running")
        except:
            self.skipTest("Metro bundler not running - skipping frontend tests")
            
        # Check bundle can be accessed
        bundle_response = requests.get("http://localhost:8082/index.bundle?platform=ios")
        self.assertEqual(bundle_response.status_code, 200, "Bundle not accessible")
        self.assertIn("__d(", bundle_response.text[:1000], "Invalid bundle format")
        
    def test_07_error_recovery(self):
        """Test: App handles startup errors gracefully"""
        print("\n🧪 Testing error recovery...")
        
        # Test invalid endpoint handling
        response = requests.get(f"{self.backend_url}/api/v1/nonexistent")
        self.assertEqual(response.status_code, 404, "404 errors not handled properly")
        
        # Test malformed request handling
        response = requests.post(
            f"{self.backend_url}/api/v1/recipes/search",
            json={"invalid_field": "test"},
            headers={"Content-Type": "application/json"}
        )
        self.assertIn(response.status_code, [400, 422], "Invalid data not rejected")
        
    def test_08_concurrent_requests(self):
        """Test: Backend handles concurrent requests on startup"""
        print("\n🧪 Testing concurrent request handling...")
        
        import concurrent.futures
        
        def make_request(endpoint):
            return requests.get(f"{self.backend_url}{endpoint}")
        
        endpoints = ["/api/v1/health", "/api/v1/units", "/api/v1/demo/recipes"]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, ep) for ep in endpoints * 3]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        for result in results:
            self.assertEqual(result.status_code, 200, "Concurrent request failed")
            
    def test_09_memory_and_resources(self):
        """Test: Check initial memory usage and resource allocation"""
        print("\n🧪 Testing resource usage...")
        
        import psutil
        
        # Find backend process
        backend_process = None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'uvicorn' in str(proc.info['cmdline']):
                    backend_process = proc
                    break
            except:
                continue
                
        if backend_process:
            memory_info = backend_process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # Backend shouldn't use excessive memory on startup
            self.assertLess(memory_mb, 500, f"Backend using too much memory: {memory_mb:.1f}MB")
            
            # Check CPU usage
            cpu_percent = backend_process.cpu_percent(interval=1)
            self.assertLess(cpu_percent, 50, f"Backend using too much CPU: {cpu_percent}%")
            
    def test_10_data_consistency(self):
        """Test: Initial data is consistent and valid"""
        print("\n🧪 Testing data consistency...")
        
        # Check units are loaded
        response = requests.get(f"{self.backend_url}/api/v1/units")
        units = response.json()
        
        self.assertIsInstance(units, list)
        self.assertGreater(len(units), 0, "No units loaded")
        
        # Verify unit structure
        for unit in units[:5]:  # Check first 5
            self.assertIn("name", unit)
            self.assertIn("abbreviation", unit)
            self.assertIn("type", unit)
            
        # Check stats return valid data
        response = requests.get(f"{self.backend_url}/api/v1/stats/comprehensive?timeframe=week")
        stats = response.json()
        
        expected_fields = ["recipes_completed", "ingredients_used", "current_streak"]
        for field in expected_fields:
            self.assertIn(field, stats, f"Missing stats field: {field}")
            
    def test_11_security_headers(self):
        """Test: Security headers are set correctly"""
        print("\n🧪 Testing security configuration...")
        
        response = requests.get(f"{self.backend_url}/api/v1/health")
        
        # Check CORS headers
        self.assertIn("access-control-allow-origin", response.headers)
        
        # Check content type
        self.assertEqual(response.headers.get("content-type"), "application/json")
        
    def test_12_logging_system(self):
        """Test: Logging system initializes correctly"""
        print("\n🧪 Testing logging system...")
        
        # Check if log directory exists
        log_dir = Path("logs")
        if not log_dir.exists():
            self.skipTest("No logs directory - logging might be to stdout only")
            
        # Check for recent log files
        log_files = list(log_dir.glob("*.log"))
        self.assertGreater(len(log_files), 0, "No log files found")
        
    @classmethod
    def tearDownClass(cls):
        """Generate test report"""
        print("\n" + "="*60)
        print("🏁 STARTUP VALIDATION COMPLETE")
        print("="*60)
        
def generate_startup_test_report():
    """Generate detailed test report"""
    report = {
        "test_categories": {
            "environment": ["Environment variables", "Configuration files", "Dependencies"],
            "connectivity": ["Backend API", "Database", "External APIs", "Frontend bundle"],
            "functionality": ["API endpoints", "Error handling", "Concurrent requests"],
            "performance": ["Memory usage", "CPU usage", "Response times"],
            "security": ["Headers", "Authentication", "Input validation"],
            "data": ["Initial data load", "Data consistency", "Stats calculation"]
        },
        "critical_checks": [
            "Database password is not placeholder",
            "All API keys are configured",
            "Backend starts without errors",
            "Database connection is established",
            "External APIs are accessible",
            "Frontend bundle builds correctly",
            "Error handling works properly",
            "System handles concurrent load"
        ],
        "recommendations": [
            "Run these tests after any configuration change",
            "Add to CI/CD pipeline for automated validation",
            "Monitor resource usage trends over time",
            "Test with production-like data volumes"
        ]
    }
    
    with open("startup_validation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n📄 Detailed report saved to startup_validation_report.json")

if __name__ == "__main__":
    # Check if services are running before tests
    try:
        response = requests.get("http://localhost:8001/api/v1/health", timeout=2)
        if response.status_code != 200:
            print("❌ Backend is not running! Start it with: python run_app.py")
            exit(1)
    except:
        print("❌ Backend is not accessible! Start it with: python run_app.py")
        exit(1)
    
    # Run tests
    unittest.main(verbosity=2, exit=False)
    
    # Generate report
    generate_startup_test_report()