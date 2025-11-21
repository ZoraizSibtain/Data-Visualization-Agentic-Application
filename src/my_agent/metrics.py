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
    result_data: List[Dict[str, Any]] = field(default_factory=list)
    from_cache: bool = False

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
        self.saved_queries: List[Dict[str, Any]] = [] # Explicitly saved queries
        self._load_from_file()  # Load persisted data on startup
        self._load_saved_queries() # Load saved queries

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

    def complete_query(self, session_id: str, success: bool, data: List[Dict[str, Any]] = None, **kwargs) -> QueryMetrics:
        """Complete query tracking and return metrics"""
        if session_id not in self._current_metrics:
            return None

        metrics = self._current_metrics[session_id]
        metrics.success = success
        metrics.total_time = (datetime.now() - metrics.timestamp).total_seconds()
        
        if data:
            metrics.result_data = data

        # Update with additional info
        for key, value in kwargs.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)

        # Set from_cache flag
        if 'from_cache' in kwargs:
            metrics.from_cache = kwargs['from_cache']

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

        # Cached vs non-cached stats
        cached_queries = [q for q in self.queries if q.from_cache]
        non_cached_queries = [q for q in self.queries if not q.from_cache]

        cached_count = len(cached_queries)
        non_cached_count = len(non_cached_queries)

        avg_cached_time = round(sum(q.total_time for q in cached_queries) / cached_count, 2) if cached_count > 0 else 0
        avg_non_cached_time = round(sum(q.total_time for q in non_cached_queries) / non_cached_count, 2) if non_cached_count > 0 else 0

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
            'cache_size': len(self.query_cache),
            'cached_queries': cached_count,
            'non_cached_queries': non_cached_count,
            'avg_cached_time': avg_cached_time,
            'avg_non_cached_time': avg_non_cached_time
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

    def is_query_saved(self, query_text: str) -> bool:
        """Check if a query is already saved"""
        if not query_text:
            return False
        return any(q['query_text'] == query_text for q in self.saved_queries)

    def save_query(self, query_data: Dict[str, Any]) -> None:
        """Save a query for future use"""
        # Check if already saved
        if self.is_query_saved(query_data['query_text']):
            return
        
        query_data['saved_at'] = datetime.now().isoformat()
        self.saved_queries.append(query_data)
        self._save_saved_queries()

    def delete_saved_query(self, index: int) -> None:
        """Delete a saved query by index"""
        if 0 <= index < len(self.saved_queries):
            self.saved_queries.pop(index)
            self._save_saved_queries()

    def _save_saved_queries(self, filepath: str = 'saved_queries.json') -> None:
        """Persist saved queries to file"""
        import json
        try:
            with open(filepath, 'w') as f:
                json.dump(self.saved_queries, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving queries: {e}")

    def _load_saved_queries(self, filepath: str = 'saved_queries.json') -> None:
        """Load saved queries from file"""
        import json
        import os
        if not os.path.exists(filepath):
            return
        
        try:
            with open(filepath, 'r') as f:
                self.saved_queries = json.load(f)
        except Exception:
            pass

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
                'results_count': q.results_count,
                'result_data': q.result_data
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
                    results_count=q.get('results_count', 0),
                    result_data=q.get('result_data', [])
                )
                self.queries.append(metrics)

        except Exception:
            pass  # Silently fail if file is corrupted

# Global instance
metrics_tracker = MetricsTracker()
