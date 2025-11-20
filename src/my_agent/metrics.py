import time
from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import threading

@dataclass
class QueryMetrics:
    """Metrics for a single query execution"""
    query_text: str
    timestamp: datetime
    total_time: float = 0.0
    parse_time: float = 0.0
    sql_gen_time: float = 0.0
    validation_time: float = 0.0
    execution_time: float = 0.0
    format_time: float = 0.0
    viz_time: float = 0.0
    sql_generated: str = ""
    sql_valid: bool = False
    results_count: int = 0
    chart_type: str = "none"
    success: bool = False
    error: str = ""

class MetricsTracker:
    """Thread-safe metrics tracker for analytics"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.queries: List[QueryMetrics] = []
        self.max_history = 100  # Keep last 100 queries
        self._current_metrics: Dict[str, QueryMetrics] = {}
        self.slow_queries: List[Dict[str, Any]] = []  # Queries > 5s
        self.query_cache: Dict[str, Any] = {}  # Cache for common queries
        self.max_cache_size = 50
        self._load_from_file()  # Load persisted data on startup

    def start_query(self, session_id: str, query_text: str) -> None:
        """Start tracking a new query"""
        self._current_metrics[session_id] = QueryMetrics(
            query_text=query_text,
            timestamp=datetime.now()
        )

    def record_step(self, session_id: str, step_name: str, duration: float) -> None:
        """Record time for a specific step"""
        if session_id not in self._current_metrics:
            return
        metrics = self._current_metrics[session_id]

        step_map = {
            'parse': 'parse_time',
            'sql_gen': 'sql_gen_time',
            'validation': 'validation_time',
            'execution': 'execution_time',
            'format': 'format_time',
            'visualization': 'viz_time'
        }

        if step_name in step_map:
            setattr(metrics, step_map[step_name], duration)

    def complete_query(self, session_id: str, success: bool, **kwargs) -> QueryMetrics:
        """Complete query tracking and return metrics"""
        if session_id not in self._current_metrics:
            return None

        metrics = self._current_metrics[session_id]
        metrics.success = success
        metrics.total_time = (datetime.now() - metrics.timestamp).total_seconds()

        # Update with additional info
        for key, value in kwargs.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)

        # Store in history
        self.queries.append(metrics)
        if len(self.queries) > self.max_history:
            self.queries.pop(0)

        # Track slow queries (> 5s)
        if metrics.total_time > 5.0:
            self.slow_queries.append({
                'query': metrics.query_text,
                'time': round(metrics.total_time, 2),
                'timestamp': metrics.timestamp.isoformat(),
                'sql_gen_time': round(metrics.sql_gen_time, 2),
                'execution_time': round(metrics.execution_time, 2)
            })
            # Keep only last 20 slow queries
            if len(self.slow_queries) > 20:
                self.slow_queries.pop(0)

        # Cleanup
        del self._current_metrics[session_id]

        return metrics

    def get_analytics(self) -> Dict[str, Any]:
        """Get aggregated analytics"""
        if not self.queries:
            return {
                'total_queries': 0,
                'avg_response_time': 0,
                'success_rate': 0,
                'avg_parse_time': 0,
                'avg_sql_gen_time': 0,
                'avg_execution_time': 0,
                'queries_under_5s': 0,
                'chart_distribution': {},
                'recent_queries': []
            }

        total = len(self.queries)
        successful = sum(1 for q in self.queries if q.success)

        # Calculate averages
        avg_total = sum(q.total_time for q in self.queries) / total
        avg_parse = sum(q.parse_time for q in self.queries) / total
        avg_sql_gen = sum(q.sql_gen_time for q in self.queries) / total
        avg_execution = sum(q.execution_time for q in self.queries) / total

        # Queries under 5 seconds
        under_5s = sum(1 for q in self.queries if q.total_time < 5)

        # Chart type distribution
        chart_dist = {}
        for q in self.queries:
            chart_dist[q.chart_type] = chart_dist.get(q.chart_type, 0) + 1

        # Recent queries (last 10)
        recent = [
            {
                'query': q.query_text[:50] + '...' if len(q.query_text) > 50 else q.query_text,
                'time': round(q.total_time, 2),
                'success': q.success,
                'chart': q.chart_type
            }
            for q in self.queries[-10:]
        ]

        return {
            'total_queries': total,
            'avg_response_time': round(avg_total, 2),
            'success_rate': round((successful / total) * 100, 1),
            'avg_parse_time': round(avg_parse, 2),
            'avg_sql_gen_time': round(avg_sql_gen, 2),
            'avg_execution_time': round(avg_execution, 2),
            'queries_under_5s': round((under_5s / total) * 100, 1),
            'chart_distribution': chart_dist,
            'recent_queries': recent,
            'slow_queries': self.slow_queries[-10:],  # Last 10 slow queries
            'cache_size': len(self.query_cache)
        }

    def get_cached_result(self, query: str) -> Any:
        """Get cached result for a query"""
        # Normalize query for cache key
        cache_key = query.strip().lower()
        return self.query_cache.get(cache_key)

    def cache_result(self, query: str, result: Any) -> None:
        """Cache a query result"""
        cache_key = query.strip().lower()
        if len(self.query_cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.query_cache))
            del self.query_cache[oldest_key]
        self.query_cache[cache_key] = result

    def clear(self) -> None:
        """Clear all metrics"""
        self.queries.clear()
        self._current_metrics.clear()

    def save_to_file(self, filepath: str = 'test_results.json') -> None:
        """Save current session analytics to JSON file"""
        import json
        import os

        analytics = self.get_analytics()

        # Load existing data if file exists
        existing_data = {}
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    existing_data = json.load(f)
            except Exception:
                pass

        # Update with session analytics
        existing_data['session_analytics'] = analytics
        existing_data['session_timestamp'] = datetime.now().isoformat()

        # Persist slow queries and query history
        existing_data['slow_queries'] = self.slow_queries
        existing_data['query_history'] = [
            {
                'query': q.query_text,
                'timestamp': q.timestamp.isoformat(),
                'total_time': round(q.total_time, 2),
                'sql_gen_time': round(q.sql_gen_time, 2),
                'execution_time': round(q.execution_time, 2),
                'sql_query': q.sql_generated,
                'chart_type': q.chart_type,
                'success': q.success,
                'results_count': q.results_count
            }
            for q in self.queries
        ]

        # Save back
        with open(filepath, 'w') as f:
            json.dump(existing_data, f, indent=2, default=str)

    def _load_from_file(self, filepath: str = 'test_results.json') -> None:
        """Load persisted data from JSON file"""
        import json
        import os

        if not os.path.exists(filepath):
            return

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Load slow queries
            self.slow_queries = data.get('slow_queries', [])

            # Load query history as QueryMetrics
            for q in data.get('query_history', []):
                metrics = QueryMetrics(
                    query_text=q.get('query', ''),
                    timestamp=datetime.fromisoformat(q.get('timestamp', datetime.now().isoformat())),
                    total_time=q.get('total_time', 0),
                    sql_gen_time=q.get('sql_gen_time', 0),
                    execution_time=q.get('execution_time', 0),
                    sql_generated=q.get('sql_query', ''),
                    chart_type=q.get('chart_type', 'none'),
                    success=q.get('success', True),
                    results_count=q.get('results_count', 0)
                )
                self.queries.append(metrics)

        except Exception:
            pass  # Silently fail if file is corrupted

# Global instance
metrics_tracker = MetricsTracker()
