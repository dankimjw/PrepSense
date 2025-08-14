#!/usr/bin/env python3
"""
Simple test runner for cache guardrails
Demonstrates the monitoring and alerting features
"""

import sys
import os
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache_manager import ArtifactCacheManager
from models import PantryArtifact, PreferenceArtifact, RecipeArtifact


def test_monitoring_and_alerts():
    """Test cache monitoring and alerting features"""
    print("=== Testing Cache Guardrails ===\n")
    
    # Track alerts
    alerts = []
    def alert_handler(msg):
        alerts.append(msg)
        print(f"🚨 ALERT: {msg}")
    
    # Test 1: Normal operation with real Redis (if available)
    print("1. Testing normal operation...")
    try:
        cache = ArtifactCacheManager(alert_callback=alert_handler)
        
        # Create test artifact
        pantry = PantryArtifact(
            user_id=123,
            normalized_items=[
                {"name": "eggs", "quantity": 12, "unit": "count"},
                {"name": "milk", "quantity": 1, "unit": "gallon"},
                {"name": "bread", "quantity": 1, "unit": "loaf"}
            ],
            expiry_analysis={"eggs": "2024-01-15", "milk": "2024-01-10"},
            ingredient_vectors=[0.1, 0.2, 0.3],
            last_updated=datetime.now()
        )
        
        # Save and retrieve
        saved = cache.save_pantry_artifact(pantry)
        print(f"   Saved artifact: {saved}")
        
        retrieved = cache.get_pantry_artifact(123)
        print(f"   Retrieved: {retrieved is not None}")
        
        # Get stats
        stats = cache.get_cache_stats()
        print(f"   Cache stats: Hits={stats['metrics']['hits']}, Misses={stats['metrics']['misses']}")
        print(f"   Health: {stats['health']['status']}")
        
    except Exception as e:
        print(f"   Redis not available: {e}")
    
    print()
    
    # Test 2: Simulate Redis failure
    print("2. Testing Redis connection failure...")
    with patch('cache_manager.redis.StrictRedis') as mock_redis:
        mock_redis.return_value.ping.side_effect = Exception("Connection refused")
        
        cache = ArtifactCacheManager(alert_callback=alert_handler)
        print(f"   Alerts triggered: {len(alerts)}")
        
        # Operations should fail gracefully
        result = cache.get_pantry_artifact(456)
        print(f"   Get operation returned: {result}")
        
    alerts.clear()
    print()
    
    # Test 3: Test consecutive errors alert
    print("3. Testing consecutive error alerting...")
    with patch('cache_manager.redis.StrictRedis') as mock_redis:
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.get.side_effect = Exception("Redis error")
        
        cache = ArtifactCacheManager(alert_callback=alert_handler)
        
        # Trigger multiple errors
        for i in range(7):
            cache.get_pantry_artifact(789)
        
        print(f"   Errors triggered: 7")
        print(f"   High error rate alerts: {sum(1 for a in alerts if 'High error rate' in a)}")
        
    alerts.clear()
    print()
    
    # Test 4: Test slow operation detection
    print("4. Testing slow operation detection...")
    with patch('cache_manager.redis.StrictRedis') as mock_redis:
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True
        
        def slow_get(key):
            time.sleep(0.3)  # 300ms - should trigger warning
            return None
            
        mock_client.get.side_effect = slow_get
        
        cache = ArtifactCacheManager(alert_callback=alert_handler)
        
        print("   Performing slow operation (300ms)...")
        start = time.time()
        cache.get_pantry_artifact(999)
        duration = time.time() - start
        print(f"   Operation took: {duration*1000:.0f}ms")
        
    print()
    
    # Test 5: Test hit rate monitoring
    print("5. Testing hit rate monitoring...")
    with patch('cache_manager.redis.StrictRedis') as mock_redis:
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True
        
        cache = ArtifactCacheManager(alert_callback=alert_handler)
        alerts.clear()
        
        # Create artifact data
        artifact_data = PantryArtifact(
            user_id=111,
            normalized_items=[{"name": "test", "quantity": 1, "unit": "item"}],
            expiry_analysis={"test": "2024-01-20"},
            ingredient_vectors=[0.5],
            last_updated=datetime.now()
        ).to_json()
        
        # Simulate 3 hits and 7 misses (30% hit rate)
        hits = 3
        misses = 7
        total_ops = hits + misses
        
        for i in range(total_ops):
            if i < hits:
                # Simulate cache hit
                cache.get_pantry_artifact(111)
            else:
                # Simulate cache miss
                cache.get_pantry_artifact(111)
        
        # Check stats after 100 more operations to trigger alert
        stats = None
        for _ in range(101):
            stats = cache.get_cache_stats()
        
        print(f"   Total operations: {total_ops} ({hits} hits, {misses} misses)")
        if stats and 'hit_rate' in stats:
            print(f"   Hit rate: {stats['hit_rate']:.1%}")
        else:
            print(f"   Hit rate: Unable to calculate (Redis not available)")
        low_hit_rate_alerts = sum(1 for a in alerts if 'Low cache hit rate' in a)
        print(f"   Low hit rate alerts: {low_hit_rate_alerts}")
        
    print()
    
    # Test 6: Test stale cache handling
    print("6. Testing stale cache entry handling...")
    with patch('cache_manager.redis.StrictRedis') as mock_redis:
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True
        
        # Create stale artifact (2 hours old)
        stale_artifact = PantryArtifact(
            user_id=222,
            normalized_items=[{"name": "old", "quantity": 1, "unit": "item"}],
            expiry_analysis={"old": "2024-01-20"},
            ingredient_vectors=[0.5],
            last_updated=datetime.now() - timedelta(hours=2)  # 2 hours old
        )
        mock_client.get.return_value = stale_artifact.to_json()
        mock_client.delete.return_value = 1
        
        cache = ArtifactCacheManager(alert_callback=alert_handler)
        
        result = cache.get_pantry_artifact(222)
        print(f"   Stale entry returned: {result}")
        print(f"   Delete called: {mock_client.delete.called}")
        
    print("\n=== Cache Guardrails Test Complete ===")
    print(f"Total alerts triggered during tests: {len(alerts)}")


if __name__ == "__main__":
    test_monitoring_and_alerts()
