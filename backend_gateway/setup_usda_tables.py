#!/usr/bin/env python3
"""
Setup USDA tables in the PrepSense database.
Run this after the backend is already started with run_app.py
"""

import asyncio
import aiohttp
import json
from pathlib import Path

async def setup_usda_tables():
    """Create USDA tables via the backend API."""
    
    # Read the SQL file
    sql_file = Path(__file__).parent / "migrations" / "create_usda_food_tables.sql"
    
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return
    
    print("📄 Reading SQL migration file...")
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    # Since we can't directly execute SQL through the API, let's check what tables exist
    async with aiohttp.ClientSession() as session:
        # First check if backend is running
        try:
            async with session.get('http://localhost:8001/api/v1/health') as resp:
                if resp.status == 200:
                    print("✅ Backend is running")
                else:
                    print("❌ Backend health check failed")
                    return
        except Exception as e:
            print(f"❌ Cannot connect to backend: {e}")
            print("Please run: python run_app.py")
            return
    
    print("\n📋 USDA Tables to be created:")
    print("  - usda_foods (main food database)")
    print("  - usda_food_categories")
    print("  - usda_measure_units") 
    print("  - usda_nutrients")
    print("  - usda_food_nutrients")
    print("  - usda_food_portions")
    print("  - pantry_item_usda_mapping")
    
    print("\n⚠️  To create these tables, you need to:")
    print("1. Connect to the database directly")
    print("2. Run the SQL migration")
    
    print("\n🔧 Option 1: Use psql (if you have direct access):")
    print("   psql $DATABASE_URL < backend_gateway/migrations/create_usda_food_tables.sql")
    
    print("\n🔧 Option 2: Add a migration endpoint to the backend")
    print("   This would allow running migrations via API")
    
    print("\n📦 After creating tables, import USDA data with:")
    print("   python backend_gateway/scripts/import_usda_data.py")

if __name__ == "__main__":
    print("🗄️  USDA Database Setup for PrepSense")
    print("=====================================\n")
    asyncio.run(setup_usda_tables())