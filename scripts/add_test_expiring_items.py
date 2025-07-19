#!/usr/bin/env python3
"""Add test items with various expiration dates to test the stats page"""

import asyncio
from datetime import datetime, timedelta
from backend_gateway.config.database import get_database_service

async def add_test_items():
    db_service = get_database_service()
    
    # Define test items with various expiration dates
    test_items = [
        # Expired items
        ("Expired Milk", "1", "gallon", (datetime.now() - timedelta(days=5)).date(), "Dairy"),
        ("Expired Bread", "1", "loaf", (datetime.now() - timedelta(days=3)).date(), "Bakery"),
        
        # Expiring soon (within 7 days)
        ("Soon-to-expire Yogurt", "2", "cups", (datetime.now() + timedelta(days=2)).date(), "Dairy"),
        ("Soon-to-expire Berries", "1", "pound", (datetime.now() + timedelta(days=4)).date(), "Produce"),
        ("Soon-to-expire Lettuce", "1", "head", (datetime.now() + timedelta(days=6)).date(), "Produce"),
        
        # Recently added (will have today's created_at)
        ("Fresh Apples", "5", "pieces", (datetime.now() + timedelta(days=14)).date(), "Produce"),
        ("Fresh Chicken", "2", "pounds", (datetime.now() + timedelta(days=10)).date(), "Meat"),
    ]
    
    print("Adding test items with various expiration dates...")
    
    for product_name, quantity, unit, exp_date, category in test_items:
        try:
            query = """
                INSERT INTO pantry_items (
                    preparer_id, product_name, quantity, unit_of_measurement, 
                    expiration_date, food_category, is_deleted, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            params = (
                111,  # user_id
                product_name,
                quantity,
                unit,
                exp_date,
                category,
                False,  # is_deleted
                datetime.now(),  # created_at
                datetime.now()   # updated_at
            )
            await db_service.execute_query(query, params)
            
            days_until = (exp_date - datetime.now().date()).days
            status = "EXPIRED" if days_until < 0 else f"expires in {days_until} days"
            print(f"✓ Added: {product_name} - {status}")
            
        except Exception as e:
            print(f"✗ Error adding {product_name}: {e}")
    
    # Verify the counts
    print("\nVerifying counts...")
    
    # Count expired
    expired_query = """
        SELECT COUNT(*) as count
        FROM pantry_items 
        WHERE preparer_id = %s 
        AND is_deleted = FALSE
        AND expiration_date IS NOT NULL
        AND expiration_date < CURRENT_DATE
    """
    expired_result = await db_service.fetch_one(expired_query, (111,))
    print(f"Expired items: {expired_result['count']}")
    
    # Count expiring soon
    expiring_query = """
        SELECT COUNT(*) as count
        FROM pantry_items 
        WHERE preparer_id = %s 
        AND is_deleted = FALSE
        AND expiration_date IS NOT NULL
        AND expiration_date <= CURRENT_DATE + INTERVAL '7 days'
        AND expiration_date > CURRENT_DATE
    """
    expiring_result = await db_service.fetch_one(expiring_query, (111,))
    print(f"Expiring soon (7 days): {expiring_result['count']}")
    
    # Count recently added (last 7 days)
    recent_query = """
        SELECT COUNT(*) as count
        FROM pantry_items 
        WHERE preparer_id = %s 
        AND is_deleted = FALSE
        AND created_at >= CURRENT_DATE - INTERVAL '7 days'
    """
    recent_result = await db_service.fetch_one(recent_query, (111,))
    print(f"Recently added (7 days): {recent_result['count']}")

if __name__ == "__main__":
    asyncio.run(add_test_items())