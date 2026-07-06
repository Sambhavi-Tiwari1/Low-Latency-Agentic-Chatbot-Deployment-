"""
Performance monitoring for low-latency tracking [citation:9]
"""
import logging
import time
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

class MetricsCollector:
    """
    Collect and track performance metrics [citation:9]
    """
    
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'total_latency_ms': 0,
            'avg_latency_ms': 0,
            'p50_latency_ms': 0,
            'p95_latency_ms': 0,
            'p99_latency_ms': 0,
            'success_rate': 100.0,
            'ttft_avg_ms': 0,
            'tokens_per_second': 0,
            'cache_hit_rate': 0
        }
        self.latencies = []
        self.ttfts = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = 0
        self.logger = logging.getLogger(__name__)
    
    def record_request(self, latency_ms: float, ttft_ms: float = None,
                      cache_hit: bool = False, error: bool = False) -> None:
        """
        Record a request metrics [citation:9]
        """
        self.metrics['total_requests'] += 1
        self.metrics['total_latency_ms'] += latency_ms
        
        # Latency tracking
        self.latencies.append(latency_ms)
        if len(self.latencies) > 10000:
            self.latencies = self.latencies[-10000:]
        
        # TTFT tracking
        if ttft_ms:
            self.ttfts.append(ttft_ms)
            if len(self.ttfts) > 10000:
                self.ttfts = self.ttfts[-10000:]
        
        # Cache tracking
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        # Error tracking
        if error:
            self.errors += 1
        
        # Update metrics
        self._update_metrics()
    
    def _update_metrics(self) -> None:
        """Update aggregate metrics"""
        total = self.metrics['total_requests']
        if total > 0:
            self.metrics['avg_latency_ms'] = self.metrics['total_latency_ms'] / total
        
        # Percentiles
        if self.latencies:
            sorted_latencies = sorted(self.latencies)
            n = len(sorted_latencies)
            self.metrics['p50_latency_ms'] = sorted_latencies[int(n * 0.5)]
            self.metrics['p95_latency_ms'] = sorted_latencies[int(n * 0.95)]
            self.metrics['p99_latency_ms'] = sorted_latencies[int(n * 0.99)]
        
        # TTFT
        if self.ttfts:
            self.metrics['ttft_avg_ms'] = sum(self.ttfts) / len(self.ttfts)
        
        # Cache hit rate
        cache_total = self.cache_hits + self.cache_misses
        if cache_total > 0:
            self.metrics['cache_hit_rate'] = (self.cache_hits / cache_total) * 100
        
        # Success rate
        if self.metrics['total_requests'] > 0:
            self.metrics['success_rate'] = ((self.metrics['total_requests'] - self.errors) / 
                                           self.metrics['total_requests'] * 100)
    
    def get_metrics(self) -> Dict:
        """Get current metrics"""
        return {
            **self.metrics,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'errors': self.errors,
            'timestamp': datetime.now().isoformat()
        }
    
    def reset(self) -> None:
        """Reset metrics"""
        self.metrics = {
            'total_requests': 0,
            'total_latency_ms': 0,
            'avg_latency_ms': 0,
            'p50_latency_ms': 0,
            'p95_latency_ms': 0,
            'p99_latency_ms': 0,
            'success_rate': 100.0,
            'ttft_avg_ms': 0,
            'tokens_per_second': 0,
            'cache_hit_rate': 0
        }
        self.latencies = []
        self.ttfts = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = 0
