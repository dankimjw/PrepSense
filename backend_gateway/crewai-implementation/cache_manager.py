"""
CrewAI Artifact Cache Manager

Redis-based caching for pantry artifacts, preference artifacts, and recipe artifacts.
Provides automatic TTL management and serialization.
"""

import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

import redis

from models import CacheKey, PantryArtifact, PreferenceArtifact, RecipeArtifact

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


class ArtifactCacheManager:
    """Redis-based cache manager for CrewAI artifacts with monitoring and guardrails"""

    def __init__(self, redis_host: str = None, redis_port: int = None, redis_db: int = None,
                 alert_callback: Optional[Callable] = None):
        """Initialize cache manager with Redis connection and monitoring"""
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = redis_db or int(os.getenv("REDIS_DB", "0"))

        # Monitoring and alerting
        self.metrics = CacheMetrics()
        self.alert_callback = alert_callback
        self.health_check_interval = 60  # seconds
        self.last_health_check = 0

        # Thresholds for alerts
        self.error_threshold = 5  # consecutive errors before alert
        self.hit_rate_threshold = 0.5  # minimum acceptable hit rate

        try:
            # Initialize Redis client
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")

        except redis.ConnectionError as e:
            logger.warning(f"Failed to connect to Redis: {e} - Cache operations will be disabled")
            self._handle_connection_failure("ConnectionError", str(e))
            self.redis_client = None
        except Exception as e:
            logger.warning(f"Redis initialization error: {e} - Cache operations will be disabled")
            self._handle_connection_failure("InitializationError", str(e))
            self.redis_client = None

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
        """Handle Redis connection failures with proper alerting"""
        self.metrics.consecutive_errors += 1
        self.metrics.last_error_time = datetime.now()

        if self.metrics.consecutive_errors >= self.error_threshold:
            self._send_alert("Redis Connection Failed", {
                "error_type": error_type,
                "error_message": error_msg,
                "consecutive_errors": self.metrics.consecutive_errors,
                "host": self.redis_host,
                "port": self.redis_port
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

    def save_pantry_artifact(self, artifact: PantryArtifact) -> bool:
        """Save pantry artifact to cache with monitoring"""
        if not self.redis_client:
            logger.warning("Cache save attempted but Redis is not connected")
            return False

        @self._monitor_operation("save", "pantry")
        def _save():
            key = CacheKey.pantry(artifact.user_id)
            json_data = artifact.to_json()
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            logger.debug(f"Saved pantry artifact for user {artifact.user_id}")
            self.metrics.consecutive_errors = 0  # Reset on success
            return bool(result)

        try:
            return _save()
        except Exception as e:
            logger.error(f"Error saving pantry artifact for user {artifact.user_id}: {e}")
            return False

    def get_pantry_artifact(self, user_id: int) -> Optional[PantryArtifact]:
        """Get pantry artifact from cache with monitoring"""
        if not self.redis_client:
            logger.warning(f"Cache get attempted for user {user_id} but Redis is not connected")
            self.metrics.misses["pantry"] += 1
            return None

        @self._monitor_operation("get", "pantry")
        def _get():
            key = CacheKey.pantry(user_id)
            json_data = self.redis_client.get(key)

            if json_data:
                artifact = PantryArtifact.from_json(json_data)
                if artifact.is_fresh():
                    logger.debug(f"Cache HIT: Retrieved fresh pantry artifact for user {user_id}")
                    self.metrics.hits["pantry"] += 1
                    self.metrics.consecutive_errors = 0
                    return artifact
                else:
                    logger.info(f"Cache STALE: Pantry artifact for user {user_id} is stale, deleting")
                    self.redis_client.delete(key)
                    self.metrics.misses["pantry"] += 1
            else:
                logger.debug(f"Cache MISS: No pantry artifact found for user {user_id}")
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
        if not self.redis_client:
            logger.warning("Cache save attempted but Redis is not connected")
            return False

        @self._monitor_operation("save", "preferences")
        def _save():
            key = CacheKey.preferences(artifact.user_id)
            json_data = artifact.to_json()
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            logger.debug(f"Saved preference artifact for user {artifact.user_id}")
            self.metrics.consecutive_errors = 0  # Reset on success
            return bool(result)

        try:
            return _save()
        except Exception as e:
            logger.error(f"Error saving preference artifact for user {artifact.user_id}: {e}")
            return False

    def get_preference_artifact(self, user_id: int) -> Optional[PreferenceArtifact]:
        """Get preference artifact from cache with monitoring"""
        if not self.redis_client:
            logger.warning(f"Cache get attempted for user {user_id} but Redis is not connected")
            self.metrics.misses["preferences"] += 1
            return None

        @self._monitor_operation("get", "preferences")
        def _get():
            key = CacheKey.preferences(user_id)
            json_data = self.redis_client.get(key)

            if json_data:
                artifact = PreferenceArtifact.from_json(json_data)
                if artifact.is_fresh():
                    logger.debug(f"Cache HIT: Retrieved fresh preference artifact for user {user_id}")
                    self.metrics.hits["preferences"] += 1
                    self.metrics.consecutive_errors = 0
                    return artifact
                else:
                    logger.info(f"Cache STALE: Preference artifact for user {user_id} is stale, deleting")
                    self.redis_client.delete(key)
                    self.metrics.misses["preferences"] += 1
            else:
                logger.debug(f"Cache MISS: No preference artifact found for user {user_id}")
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
        if not self.redis_client:
            logger.warning("Cache save attempted but Redis is not connected")
            return False

        @self._monitor_operation("save", "recipes")
        def _save():
            key = CacheKey.recipes(artifact.user_id, artifact.context)
            json_data = artifact.to_json()
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            logger.debug(
                f"Saved recipe artifact for user {artifact.user_id} with context '{artifact.context}'"
            )
            self.metrics.consecutive_errors = 0  # Reset on success
            return bool(result)

        try:
            return _save()
        except Exception as e:
            logger.error(f"Error saving recipe artifact for user {artifact.user_id}: {e}")
            return False

    def get_recipe_artifact(
        self, user_id: int, context: Optional[str] = None
    ) -> Optional[RecipeArtifact]:
        """Get recipe artifact from cache with monitoring"""
        if not self.redis_client:
            logger.warning(f"Cache get attempted for user {user_id} but Redis is not connected")
            self.metrics.misses["recipes"] += 1
            return None

        @self._monitor_operation("get", "recipes")
        def _get():
            key = CacheKey.recipes(user_id, context)
            json_data = self.redis_client.get(key)

            if json_data:
                artifact = RecipeArtifact.from_json(json_data)
                if artifact.is_fresh():
                    logger.debug(
                        f"Cache HIT: Retrieved fresh recipe artifact for user {user_id} with context '{context}'"
                    )
                    self.metrics.hits["recipes"] += 1
                    self.metrics.consecutive_errors = 0
                    return artifact
                else:
                    logger.info(
                        f"Cache STALE: Recipe artifact for user {user_id} with context '{context}' is stale, deleting"
                    )
                    self.redis_client.delete(key)
                    self.metrics.misses["recipes"] += 1
            else:
                logger.debug(f"Cache MISS: No recipe artifact found for user {user_id} with context '{context}'")
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
        if not self.redis_client:
            return []

        try:
            patterns = [
                CacheKey.recipes(user_id, context),
            ]

            deleted = 0
            for pattern in patterns:
                if "*" in pattern:
                    # Use scan for pattern matching
                    deleted += self._delete_by_pattern(pattern)
                else:
                    deleted += self.redis_client.delete(pattern)

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

        if not self.redis_client:
            return {
                "connected": False,
                "error": "Redis not connected",
                "consecutive_errors": self.metrics.consecutive_errors,
                "last_error_time": self.metrics.last_error_time.isoformat() if self.metrics.last_error_time else None
            }

        try:
            info = self.redis_client.info()

            # Calculate application-level metrics
            app_stats = self._calculate_app_metrics()

            stats = {
                "connected": True,
                "redis_info": {
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
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
        if not self.redis_client:
            return False

        try:
            return self.redis_client.ping()
        except Exception:
            return False
