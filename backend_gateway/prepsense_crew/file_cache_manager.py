"""
File-based Cache Manager for CrewAI Artifacts

Alternative to Redis-based cache manager that works without external dependencies.
Provides the same interface as ArtifactCacheManager but uses local file storage.
"""

import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional
import hashlib

from .models import CacheKey, PantryArtifact, PreferenceArtifact, RecipeArtifact

logger = logging.getLogger(__name__)


class CacheMetrics:
    """Track cache performance metrics"""
    def __init__(self):
        self.hits = defaultdict(int)
        self.misses = defaultdict(int)
        self.errors = defaultdict(int)
        self.operation_times = defaultdict(list)
        self.last_error_time = None
        self.consecutive_errors = 0


class FileCacheManager:
    """File-based cache manager for CrewAI artifacts with monitoring and guardrails"""

    def __init__(self, cache_dir: str = None, alert_callback: Optional[Callable] = None):
        """Initialize file cache manager with storage directory and monitoring"""
        self.cache_dir = Path(cache_dir) if cache_dir else Path(os.getenv("CACHE_DIR", "/tmp/prepsense_cache"))
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Monitoring and alerting
        self.metrics = CacheMetrics()
        self.alert_callback = alert_callback
        self.health_check_interval = 60  # seconds
        self.last_health_check = 0

        # Thresholds for alerts
        self.error_threshold = 5  # consecutive errors before alert
        self.hit_rate_threshold = 0.5  # minimum acceptable hit rate
        
        # Cache expiration cleanup interval
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

        try:
            # Test write permissions
            test_file = self.cache_dir / ".test_write"
            test_file.write_text("test")
            test_file.unlink()
            logger.info(f"File cache initialized at {self.cache_dir}")
            
        except Exception as e:
            logger.error(f"Failed to initialize file cache: {e}")
            raise

    def _monitor_operation(self, operation: str, artifact_type: str):
        """Decorator to monitor cache operations"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.metrics.operation_times[f"{operation}_{artifact_type}"].append(duration)

                    # Log slow operations
                    if duration > 0.1:  # 100ms
                        logger.warning(f"Slow cache {operation} for {artifact_type}: {duration:.3f}s")

                    return result
                except Exception:
                    self.metrics.errors[f"{operation}_{artifact_type}"] += 1
                    self._check_error_threshold()
                    raise
            return wrapper
        return decorator

    def _handle_connection_failure(self, error_type: str, error_msg: str):
        """Handle cache failures with proper alerting"""
        self.metrics.consecutive_errors += 1
        self.metrics.last_error_time = datetime.now()

        if self.metrics.consecutive_errors >= self.error_threshold:
            self._send_alert("File Cache Failed", {
                "error_type": error_type,
                "error_message": error_msg,
                "consecutive_errors": self.metrics.consecutive_errors,
                "cache_dir": str(self.cache_dir)
            })

    def _send_alert(self, alert_type: str, details: dict[str, Any]):
        """Send alert through configured callback or log as ERROR"""
        alert_message = f"CACHE ALERT - {alert_type}: {json.dumps(details)}"

        if self.alert_callback:
            try:
                self.alert_callback(alert_type, details)
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")

        # Always log as ERROR for visibility
        logger.error(alert_message)

    def _check_error_threshold(self):
        """Check if error threshold has been exceeded"""
        if self.metrics.consecutive_errors >= self.error_threshold:
            self._send_alert("Error Threshold Exceeded", {
                "consecutive_errors": self.metrics.consecutive_errors,
                "last_error_time": self.metrics.last_error_time.isoformat() if self.metrics.last_error_time else None
            })

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key"""
        # Hash the key to avoid filesystem issues with special characters
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def _cleanup_expired(self):
        """Clean up expired cache files"""
        if time.time() - self.last_cleanup < self.cleanup_interval:
            return
            
        try:
            current_time = time.time()
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    stat = cache_file.stat()
                    # Simple TTL check - delete files older than 1 hour
                    if current_time - stat.st_mtime > 3600:
                        cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Error cleaning up {cache_file}: {e}")
                    
            self.last_cleanup = current_time
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

    def save_pantry_artifact(self, artifact: PantryArtifact) -> bool:
        """Save pantry artifact to cache with monitoring"""
        @self._monitor_operation("save", "pantry")
        def _save():
            key = CacheKey.pantry(artifact.user_id)
            cache_path = self._get_cache_path(key)
            
            cache_data = {
                "artifact": json.loads(artifact.to_json()),
                "timestamp": time.time(),
                "ttl_seconds": artifact.ttl_seconds
            }
            
            cache_path.write_text(json.dumps(cache_data), encoding='utf-8')
            logger.debug(f"Saved pantry artifact for user {artifact.user_id} to {cache_path}")
            self.metrics.consecutive_errors = 0  # Reset on success
            return True

        try:
            self._cleanup_expired()
            return _save()
        except Exception as e:
            logger.error(f"Error saving pantry artifact for user {artifact.user_id}: {e}")
            return False

    def get_pantry_artifact(self, user_id: int) -> Optional[PantryArtifact]:
        """Get pantry artifact from cache with monitoring"""
        @self._monitor_operation("get", "pantry")
        def _get():
            key = CacheKey.pantry(user_id)
            cache_path = self._get_cache_path(key)
            
            if not cache_path.exists():
                logger.debug(f"Cache MISS: No pantry artifact found for user {user_id}")
                self.metrics.misses["pantry"] += 1
                return None
                
            try:
                cache_data = json.loads(cache_path.read_text(encoding='utf-8'))
                timestamp = cache_data["timestamp"]
                ttl_seconds = cache_data["ttl_seconds"]
                
                # Check if expired
                if time.time() - timestamp > ttl_seconds:
                    logger.info(f"Cache STALE: Pantry artifact for user {user_id} is stale, deleting")
                    cache_path.unlink()
                    self.metrics.misses["pantry"] += 1
                    return None
                    
                # Reconstruct artifact
                artifact = PantryArtifact.from_json(json.dumps(cache_data["artifact"]))
                logger.debug(f"Cache HIT: Retrieved fresh pantry artifact for user {user_id}")
                self.metrics.hits["pantry"] += 1
                self.metrics.consecutive_errors = 0
                return artifact
                
            except Exception as e:
                logger.error(f"Error reading cache file {cache_path}: {e}")
                cache_path.unlink()  # Remove corrupted file
                self.metrics.misses["pantry"] += 1
                return None

        try:
            return _get()
        except Exception as e:
            logger.error(f"Error getting pantry artifact for user {user_id}: {e}")
            self.metrics.misses["pantry"] += 1
            return None

    def save_preference_artifact(self, artifact: PreferenceArtifact) -> bool:
        """Save preference artifact to cache with monitoring"""
        @self._monitor_operation("save", "preferences")
        def _save():
            key = CacheKey.preferences(artifact.user_id)
            cache_path = self._get_cache_path(key)
            
            cache_data = {
                "artifact": json.loads(artifact.to_json()),
                "timestamp": time.time(),
                "ttl_seconds": artifact.ttl_seconds
            }
            
            cache_path.write_text(json.dumps(cache_data), encoding='utf-8')
            logger.debug(f"Saved preference artifact for user {artifact.user_id} to {cache_path}")
            self.metrics.consecutive_errors = 0  # Reset on success
            return True

        try:
            self._cleanup_expired()
            return _save()
        except Exception as e:
            logger.error(f"Error saving preference artifact for user {artifact.user_id}: {e}")
            return False

    def get_preference_artifact(self, user_id: int) -> Optional[PreferenceArtifact]:
        """Get preference artifact from cache with monitoring"""
        @self._monitor_operation("get", "preferences")
        def _get():
            key = CacheKey.preferences(user_id)
            cache_path = self._get_cache_path(key)
            
            if not cache_path.exists():
                logger.debug(f"Cache MISS: No preference artifact found for user {user_id}")
                self.metrics.misses["preferences"] += 1
                return None
                
            try:
                cache_data = json.loads(cache_path.read_text(encoding='utf-8'))
                timestamp = cache_data["timestamp"]
                ttl_seconds = cache_data["ttl_seconds"]
                
                # Check if expired
                if time.time() - timestamp > ttl_seconds:
                    logger.info(f"Cache STALE: Preference artifact for user {user_id} is stale, deleting")
                    cache_path.unlink()
                    self.metrics.misses["preferences"] += 1
                    return None
                    
                # Reconstruct artifact
                artifact = PreferenceArtifact.from_json(json.dumps(cache_data["artifact"]))
                logger.debug(f"Cache HIT: Retrieved fresh preference artifact for user {user_id}")
                self.metrics.hits["preferences"] += 1
                self.metrics.consecutive_errors = 0
                return artifact
                
            except Exception as e:
                logger.error(f"Error reading cache file {cache_path}: {e}")
                cache_path.unlink()  # Remove corrupted file
                self.metrics.misses["preferences"] += 1
                return None

        try:
            return _get()
        except Exception as e:
            logger.error(f"Error getting preference artifact for user {user_id}: {e}")
            self.metrics.misses["preferences"] += 1
            return None

    def save_recipe_artifact(self, artifact: RecipeArtifact) -> bool:
        """Save recipe artifact to cache with monitoring"""
        @self._monitor_operation("save", "recipes")
        def _save():
            key = CacheKey.recipes(artifact.user_id, artifact.context)
            cache_path = self._get_cache_path(key)
            
            cache_data = {
                "artifact": json.loads(artifact.to_json()),
                "timestamp": time.time(),
                "ttl_seconds": artifact.ttl_seconds
            }
            
            cache_path.write_text(json.dumps(cache_data), encoding='utf-8')
            logger.debug(f"Saved recipe artifact for user {artifact.user_id} with context '{artifact.context}' to {cache_path}")
            self.metrics.consecutive_errors = 0  # Reset on success
            return True

        try:
            self._cleanup_expired()
            return _save()
        except Exception as e:
            logger.error(f"Error saving recipe artifact for user {artifact.user_id}: {e}")
            return False

    def get_recipe_artifact(self, user_id: int, context: Optional[str] = None) -> Optional[RecipeArtifact]:
        """Get recipe artifact from cache with monitoring"""
        @self._monitor_operation("get", "recipes")
        def _get():
            key = CacheKey.recipes(user_id, context)
            cache_path = self._get_cache_path(key)
            
            if not cache_path.exists():
                logger.debug(f"Cache MISS: No recipe artifact found for user {user_id} with context '{context}'")
                self.metrics.misses["recipes"] += 1
                return None
                
            try:
                cache_data = json.loads(cache_path.read_text(encoding='utf-8'))
                timestamp = cache_data["timestamp"]
                ttl_seconds = cache_data["ttl_seconds"]
                
                # Check if expired
                if time.time() - timestamp > ttl_seconds:
                    logger.info(f"Cache STALE: Recipe artifact for user {user_id} with context '{context}' is stale, deleting")
                    cache_path.unlink()
                    self.metrics.misses["recipes"] += 1
                    return None
                    
                # Reconstruct artifact
                artifact = RecipeArtifact.from_json(json.dumps(cache_data["artifact"]))
                logger.debug(f"Cache HIT: Retrieved fresh recipe artifact for user {user_id} with context '{context}'")
                self.metrics.hits["recipes"] += 1
                self.metrics.consecutive_errors = 0
                return artifact
                
            except Exception as e:
                logger.error(f"Error reading cache file {cache_path}: {e}")
                cache_path.unlink()  # Remove corrupted file
                self.metrics.misses["recipes"] += 1
                return None

        try:
            return _get()
        except Exception as e:
            logger.error(f"Error getting recipe artifact for user {user_id}: {e}")
            self.metrics.misses["recipes"] += 1
            return None

    def invalidate_recipe_cache(self, user_id: int, context: Optional[str] = None) -> list[str]:
        """Invalidate recipe cache entries for a user"""
        try:
            key = CacheKey.recipes(user_id, context)
            cache_path = self._get_cache_path(key)
            
            deleted = 0
            if cache_path.exists():
                cache_path.unlink()
                deleted = 1

            logger.info(f"Invalidated {deleted} recipe cache entries for user {user_id}")
            self.metrics.consecutive_errors = 0  # Reset on success
            return [f"Invalidated {deleted} recipe cache entries for user {user_id}"]
        except Exception as e:
            logger.error(f"Error invalidating recipe cache: {e}")
            self.metrics.errors["invalidate_recipes"] += 1
            self._check_error_threshold()
            return []

    def warm_cache(self, user_id: int, artifacts: dict[str, Any]) -> dict[str, bool]:
        """Warm cache with provided artifacts"""
        results = {}
        # Implementation would create artifacts from provided data
        # and save them to cache
        # This is a placeholder for the actual implementation
        return results

    def get_cache_stats(self) -> dict[str, Any]:
        """Get enhanced cache statistics with monitoring data"""
        # Check if we need to run health check
        current_time = time.time()
        if current_time - self.last_health_check > self.health_check_interval:
            self._perform_health_check()
            self.last_health_check = current_time

        try:
            # Calculate application-level metrics
            app_stats = self._calculate_app_metrics()
            
            # Get cache directory stats
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files if f.exists())

            stats = {
                "connected": True,
                "cache_type": "file_based",
                "cache_info": {
                    "cache_directory": str(self.cache_dir),
                    "total_files": len(cache_files),
                    "total_size_bytes": total_size,
                    "total_size_human": f"{total_size / 1024:.1f} KB" if total_size < 1024*1024 else f"{total_size / (1024*1024):.1f} MB",
                },
                "application_metrics": app_stats,
                "health": {
                    "consecutive_errors": self.metrics.consecutive_errors,
                    "last_error_time": self.metrics.last_error_time.isoformat() if self.metrics.last_error_time else None,
                    "alerts_needed": self._check_alert_conditions(app_stats)
                }
            }

            return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            self.metrics.errors["stats"] += 1
            return {"connected": True, "error": str(e), "consecutive_errors": self.metrics.consecutive_errors}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)

    def _calculate_app_metrics(self) -> dict[str, Any]:
        """Calculate application-level cache metrics"""
        metrics = {}

        for artifact_type in ["pantry", "preferences", "recipes"]:
            hits = self.metrics.hits[artifact_type]
            misses = self.metrics.misses[artifact_type]
            errors = self.metrics.errors.get(f"get_{artifact_type}", 0) + self.metrics.errors.get(f"save_{artifact_type}", 0)
            
            metrics[artifact_type] = {
                "hits": hits,
                "misses": misses,
                "errors": errors,
                "hit_rate": self._calculate_hit_rate(hits, misses),
                "avg_latency_ms": self._calculate_avg_latency(artifact_type)
            }

        return metrics

    def _calculate_avg_latency(self, artifact_type: str) -> float:
        """Calculate average operation latency in milliseconds"""
        all_times = []
        for op in ["get", "save"]:
            times = self.metrics.operation_times.get(f"{op}_{artifact_type}", [])
            all_times.extend(times)

        if not all_times:
            return 0.0

        # Keep only last 100 operations
        recent_times = all_times[-100:]
        return round(sum(recent_times) / len(recent_times) * 1000, 2)  # Convert to ms

    def _check_alert_conditions(self, app_stats: dict[str, Any]) -> list[str]:
        """Check if any alert conditions are met"""
        alerts = []

        # Check hit rates
        for artifact_type, stats in app_stats.items():
            if stats["hit_rate"] < self.hit_rate_threshold * 100 and (stats["hits"] + stats["misses"]) > 10:
                alerts.append(f"Low hit rate for {artifact_type}: {stats['hit_rate']}%")

            if stats["avg_latency_ms"] > 100:
                alerts.append(f"High latency for {artifact_type}: {stats['avg_latency_ms']}ms")

        return alerts

    def _perform_health_check(self):
        """Perform periodic health check and send alerts if needed"""
        stats = self._calculate_app_metrics()
        alerts = self._check_alert_conditions(stats)

        if alerts:
            self._send_alert("Cache Health Check Failed", {
                "alerts": alerts,
                "stats": stats
            })

    def health_check(self) -> bool:
        """Check if cache manager is healthy"""
        try:
            # Test write permissions
            test_file = self.cache_dir / ".health_test"
            test_file.write_text("health_check")
            test_file.unlink()
            return True
        except Exception:
            return False