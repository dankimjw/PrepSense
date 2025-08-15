"""
Test suite for cache guardrails in ArtifactCacheManager
Tests monitoring, alerting, metrics, and health checks
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import json
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..cache_manager import ArtifactCacheManager
from ..models import PantryArtifact, PreferenceArtifact, RecipeArtifact


class TestCacheGuardrails(unittest.TestCase):
    """Test cache guardrails functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.alerts = []
        self.alert_callback = lambda msg: self.alerts.append(msg)
        
    def tearDown(self):
        """Clean up after tests"""
        self.alerts.clear()

    @patch('cache_manager.redis.StrictRedis')
    def test_monitoring_successful_operations(self, mock_redis_class):
        """Test that successful operations are monitored correctly"""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = None  # Cache miss
        
        # Create cache manager with alert callback
        cache_manager = ArtifactCacheManager(alert_callback=self.alert_callback)
        
        # Create test artifact
        pantry_artifact = PantryArtifact(
            user_id=123,
            items=["eggs", "milk"],
            timestamp=datetime.now()
        )
        
        # Save artifact (should succeed)
        result = cache_manager.save_pantry_artifact(pantry_artifact)
        self.assertTrue(result)
        
        # Get artifact (should be a miss)
        result = cache_manager.get_pantry_artifact(123)
        self.assertIsNone(result)
        
        # Check metrics
        stats = cache_manager.get_cache_stats()
        self.assertEqual(stats['metrics']['hits']['pantry'], 0)
        self.assertEqual(stats['metrics']['misses']['pantry'], 1)
        self.assertEqual(stats['metrics']['errors']['save_pantry'], 0)
        self.assertEqual(stats['metrics']['consecutive_errors'], 0)
        
        # No alerts should be triggered for successful operations
        self.assertEqual(len(self.alerts), 0)

    @patch('cache_manager.redis.StrictRedis')
    def test_monitoring_failed_operations(self, mock_redis_class):
        """Test that failed operations trigger alerts"""
        # Mock Redis client that fails
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.side_effect = Exception("Connection failed")
        
        # Create cache manager with alert callback
        cache_manager = ArtifactCacheManager(alert_callback=self.alert_callback)
        
        # Should have connection alert
        self.assertTrue(any("Failed to connect to Redis" in alert for alert in self.alerts))
        
        # Operations should fail gracefully
        result = cache_manager.get_pantry_artifact(123)
        self.assertIsNone(result)
        
        # Check that miss was recorded even with no Redis
        stats = cache_manager.get_cache_stats()
        self.assertEqual(stats['metrics']['misses']['pantry'], 1)

    @patch('cache_manager.redis.StrictRedis')
    def test_consecutive_error_alerting(self, mock_redis_class):
        """Test that consecutive errors trigger alerts"""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        
        # Create cache manager
        cache_manager = ArtifactCacheManager(alert_callback=self.alert_callback)
        self.alerts.clear()  # Clear connection alerts
        
        # Make operations fail
        mock_redis.get.side_effect = Exception("Redis error")
        
        # Trigger multiple errors to exceed threshold
        for i in range(7):  # Threshold is 5
            cache_manager.get_pantry_artifact(123)
        
        # Should have error threshold alert
        self.assertTrue(any("High error rate detected" in alert for alert in self.alerts))
        
        # Check metrics
        stats = cache_manager.get_cache_stats()
        self.assertGreaterEqual(stats['metrics']['errors']['get_pantry'], 7)

    @patch('cache_manager.redis.StrictRedis')
    def test_slow_operation_logging(self, mock_redis_class):
        """Test that slow operations are logged"""
        # Mock Redis client with slow operations
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        
        # Create slow get operation
        def slow_get(key):
            time.sleep(0.2)  # 200ms
            return None
        mock_redis.get.side_effect = slow_get
        
        # Create cache manager
        cache_manager = ArtifactCacheManager(alert_callback=self.alert_callback)
        
        # Perform slow operation
        with self.assertLogs('cache_manager', level='WARNING') as cm:
            cache_manager.get_pantry_artifact(123)
            
        # Should have slow operation warning
        self.assertTrue(any("Slow cache operation" in log for log in cm.output))

    @patch('cache_manager.redis.StrictRedis')
    def test_hit_rate_monitoring(self, mock_redis_class):
        """Test cache hit rate calculation and alerting"""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        
        # Create cache manager
        cache_manager = ArtifactCacheManager(alert_callback=self.alert_callback)
        self.alerts.clear()
        
        # Create test artifact
        pantry_artifact = PantryArtifact(
            user_id=123,
            items=["eggs", "milk"],
            timestamp=datetime.now()
        )
        
        # Simulate cache hits and misses
        mock_redis.get.return_value = pantry_artifact.to_json()  # Hit
        for _ in range(3):
            result = cache_manager.get_pantry_artifact(123)
            self.assertIsNotNone(result)
        
        mock_redis.get.return_value = None  # Miss
        for _ in range(7):
            result = cache_manager.get_pantry_artifact(123)
            self.assertIsNone(result)
        
        # Force health check by calling stats multiple times
        for _ in range(101):  # Trigger health check
            stats = cache_manager.get_cache_stats()
        
        # Should have low hit rate alert (30% < 50% threshold)
        self.assertTrue(any("Low cache hit rate" in alert for alert in self.alerts))
        
        # Verify hit rate calculation
        final_stats = cache_manager.get_cache_stats()
        self.assertAlmostEqual(final_stats['hit_rate'], 0.3, places=1)

    @patch('cache_manager.redis.StrictRedis')
    def test_health_check_status(self, mock_redis_class):
        """Test health check provides accurate status"""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        
        # Create cache manager
        cache_manager = ArtifactCacheManager(alert_callback=self.alert_callback)
        
        # Get initial health status
        stats = cache_manager.get_cache_stats()
        health = stats['health']
        
        self.assertEqual(health['status'], 'healthy')
        self.assertTrue(health['redis_connected'])
        self.assertEqual(health['consecutive_errors'], 0)
        
        # Simulate degraded health
        mock_redis.get.side_effect = Exception("Redis error")
        for _ in range(3):
            cache_manager.get_pantry_artifact(123)
        
        # Check degraded status
        stats = cache_manager.get_cache_stats()
        health = stats['health']
        self.assertEqual(health['consecutive_errors'], 3)

    @patch('cache_manager.redis.StrictRedis')
    def test_stale_cache_handling(self, mock_redis_class):
        """Test that stale cache entries are handled correctly"""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        
        # Create stale artifact (2 hours old for 1-hour TTL)
        stale_artifact = PantryArtifact(
            user_id=123,
            items=["old_eggs"],
            timestamp=datetime.now() - timedelta(hours=2)
        )
        
        mock_redis.get.return_value = stale_artifact.to_json()
        mock_redis.delete.return_value = 1
        
        # Create cache manager
        cache_manager = ArtifactCacheManager(alert_callback=self.alert_callback)
        
        # Get stale artifact
        with self.assertLogs('cache_manager', level='INFO') as cm:
            result = cache_manager.get_pantry_artifact(123)
            
        # Should return None and log stale entry
        self.assertIsNone(result)
        self.assertTrue(any("Cache STALE" in log for log in cm.output))
        
        # Verify delete was called
        mock_redis.delete.assert_called()
        
        # Should count as a miss
        stats = cache_manager.get_cache_stats()
        self.assertEqual(stats['metrics']['misses']['pantry'], 1)
        self.assertEqual(stats['metrics']['hits']['pantry'], 0)

    @patch('cache_manager.redis.StrictRedis')
    def test_latency_tracking(self, mock_redis_class):
        """Test operation latency tracking"""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True
        
        # Variable latency operations
        latencies = [0.05, 0.1, 0.15, 0.3]  # Mix of fast and slow
        call_count = 0
        
        def variable_latency_get(key):
            nonlocal call_count
            time.sleep(latencies[call_count % len(latencies)])
            call_count += 1
            return None
            
        mock_redis.get.side_effect = variable_latency_get
        
        # Create cache manager
        cache_manager = ArtifactCacheManager(alert_callback=self.alert_callback)
        self.alerts.clear()
        
        # Perform operations
        for _ in range(4):
            cache_manager.get_pantry_artifact(123)
        
        # Force health check
        for _ in range(101):
            stats = cache_manager.get_cache_stats()
        
        # Should have high latency alert (avg > 200ms)
        self.assertTrue(any("High average latency" in alert for alert in self.alerts))
        
        # Check latency metrics
        final_stats = cache_manager.get_cache_stats()
        avg_latency = final_stats['health']['avg_latency_ms']['pantry']
        self.assertGreater(avg_latency, 100)  # Should be ~150ms average


if __name__ == '__main__':
    unittest.main(verbosity=2)
