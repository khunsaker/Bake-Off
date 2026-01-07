#!/usr/bin/env python3
"""
Metrics Collection using HDR Histogram
High-accuracy latency measurement for Shark Bake-Off benchmarks
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from hdrh.histogram import HdrHistogram


@dataclass
class PercentileStats:
    """Percentile statistics"""
    min: float
    p50: float
    p75: float
    p90: float
    p95: float
    p99: float
    p999: float
    max: float
    mean: float
    stddev: float


@dataclass
class QueryMetrics:
    """Metrics for a single query type"""
    query_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration_sec: float
    latency_stats: PercentileStats
    throughput_qps: float
    error_rate: float


class MetricsCollector:
    """
    High-accuracy metrics collector using HDR Histogram

    HDR Histogram provides:
    - Accurate percentile measurements (even at high percentiles like p99.999)
    - Minimal memory footprint
    - Consistent overhead regardless of data volume
    """

    def __init__(
        self,
        name: str,
        lowest_trackable_value: int = 1,  # 1 microsecond
        highest_trackable_value: int = 3600000000,  # 1 hour in microseconds
        significant_figures: int = 3,
    ):
        """
        Initialize metrics collector

        Args:
            name: Name of the metric being collected
            lowest_trackable_value: Minimum value to track (microseconds)
            highest_trackable_value: Maximum value to track (microseconds)
            significant_figures: Precision (1-5, higher = more accurate)
        """
        self.name = name
        self.histogram = HdrHistogram(
            lowest_trackable_value,
            highest_trackable_value,
            significant_figures
        )
        self.start_time = time.time()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.errors: List[str] = []

    def record_latency(self, latency_seconds: float, success: bool = True):
        """
        Record a latency measurement

        Args:
            latency_seconds: Latency in seconds
            success: Whether the request succeeded
        """
        latency_micros = int(latency_seconds * 1_000_000)

        if success:
            self.histogram.record_value(latency_micros)
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        self.total_requests += 1

    def record_error(self, error_message: str):
        """Record an error"""
        self.errors.append(error_message)
        self.failed_requests += 1
        self.total_requests += 1

    def get_percentile_stats(self) -> PercentileStats:
        """Get percentile statistics"""
        if self.successful_requests == 0:
            return PercentileStats(
                min=0.0, p50=0.0, p75=0.0, p90=0.0, p95=0.0,
                p99=0.0, p999=0.0, max=0.0, mean=0.0, stddev=0.0
            )

        return PercentileStats(
            min=self.histogram.get_min_value() / 1000.0,  # Convert to ms
            p50=self.histogram.get_value_at_percentile(50.0) / 1000.0,
            p75=self.histogram.get_value_at_percentile(75.0) / 1000.0,
            p90=self.histogram.get_value_at_percentile(90.0) / 1000.0,
            p95=self.histogram.get_value_at_percentile(95.0) / 1000.0,
            p99=self.histogram.get_value_at_percentile(99.0) / 1000.0,
            p999=self.histogram.get_value_at_percentile(99.9) / 1000.0,
            max=self.histogram.get_max_value() / 1000.0,
            mean=self.histogram.get_mean_value() / 1000.0,
            stddev=self.histogram.get_stddev() / 1000.0,
        )

    def get_metrics(self) -> QueryMetrics:
        """Get complete metrics"""
        duration = time.time() - self.start_time
        throughput = self.successful_requests / duration if duration > 0 else 0
        error_rate = self.failed_requests / self.total_requests if self.total_requests > 0 else 0

        return QueryMetrics(
            query_name=self.name,
            total_requests=self.total_requests,
            successful_requests=self.successful_requests,
            failed_requests=self.failed_requests,
            total_duration_sec=duration,
            latency_stats=self.get_percentile_stats(),
            throughput_qps=throughput,
            error_rate=error_rate,
        )

    def reset(self):
        """Reset all metrics"""
        self.histogram.reset()
        self.start_time = time.time()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.errors.clear()

    def print_summary(self):
        """Print metrics summary"""
        metrics = self.get_metrics()
        stats = metrics.latency_stats

        print(f"\n{'='*70}")
        print(f"Metrics: {self.name}")
        print(f"{'='*70}")
        print(f"Total Requests:      {metrics.total_requests:,}")
        print(f"Successful:          {metrics.successful_requests:,}")
        print(f"Failed:              {metrics.failed_requests:,}")
        print(f"Error Rate:          {metrics.error_rate*100:.2f}%")
        print(f"Duration:            {metrics.total_duration_sec:.2f}s")
        print(f"Throughput:          {metrics.throughput_qps:.2f} qps")
        print(f"\nLatency (ms):")
        print(f"  Min:               {stats.min:.2f}")
        print(f"  Mean:              {stats.mean:.2f}")
        print(f"  p50 (median):      {stats.p50:.2f}")
        print(f"  p75:               {stats.p75:.2f}")
        print(f"  p90:               {stats.p90:.2f}")
        print(f"  p95:               {stats.p95:.2f}")
        print(f"  p99:               {stats.p99:.2f}")
        print(f"  p99.9:             {stats.p999:.2f}")
        print(f"  Max:               {stats.max:.2f}")
        print(f"  StdDev:            {stats.stddev:.2f}")
        print(f"{'='*70}\n")


class BenchmarkSession:
    """
    Manages multiple metric collectors for a benchmark session
    """

    def __init__(self, session_name: str):
        self.session_name = session_name
        self.collectors: Dict[str, MetricsCollector] = {}
        self.start_time = datetime.utcnow()

    def get_collector(self, name: str) -> MetricsCollector:
        """Get or create a metrics collector"""
        if name not in self.collectors:
            self.collectors[name] = MetricsCollector(name)
        return self.collectors[name]

    def record_request(
        self,
        query_name: str,
        latency_seconds: float,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Record a request"""
        collector = self.get_collector(query_name)

        if success:
            collector.record_latency(latency_seconds, success=True)
        else:
            collector.record_latency(latency_seconds, success=False)
            if error:
                collector.record_error(error)

    def get_all_metrics(self) -> List[QueryMetrics]:
        """Get metrics for all collectors"""
        return [collector.get_metrics() for collector in self.collectors.values()]

    def print_summary(self):
        """Print summary for all collectors"""
        print(f"\n{'#'*70}")
        print(f"# Benchmark Session: {self.session_name}")
        print(f"# Start Time: {self.start_time.isoformat()}")
        print(f"{'#'*70}")

        for collector in self.collectors.values():
            collector.print_summary()

    def export_json(self, filename: str):
        """Export metrics to JSON"""
        data = {
            'session_name': self.session_name,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.utcnow().isoformat(),
            'metrics': [asdict(m) for m in self.get_all_metrics()]
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Metrics exported to {filename}")

    def export_csv(self, filename: str):
        """Export metrics to CSV"""
        import pandas as pd

        rows = []
        for metrics in self.get_all_metrics():
            row = {
                'query_name': metrics.query_name,
                'total_requests': metrics.total_requests,
                'successful_requests': metrics.successful_requests,
                'failed_requests': metrics.failed_requests,
                'duration_sec': metrics.total_duration_sec,
                'throughput_qps': metrics.throughput_qps,
                'error_rate': metrics.error_rate,
                'latency_min_ms': metrics.latency_stats.min,
                'latency_p50_ms': metrics.latency_stats.p50,
                'latency_p75_ms': metrics.latency_stats.p75,
                'latency_p90_ms': metrics.latency_stats.p90,
                'latency_p95_ms': metrics.latency_stats.p95,
                'latency_p99_ms': metrics.latency_stats.p99,
                'latency_p999_ms': metrics.latency_stats.p999,
                'latency_max_ms': metrics.latency_stats.max,
                'latency_mean_ms': metrics.latency_stats.mean,
                'latency_stddev_ms': metrics.latency_stats.stddev,
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False)
        print(f"Metrics exported to {filename}")


# Example usage
if __name__ == '__main__':
    import random

    session = BenchmarkSession("test-session")

    # Simulate some requests
    for i in range(1000):
        latency = random.gauss(0.010, 0.005)  # 10ms mean, 5ms stddev
        session.record_request("s1_simple_lookup", latency, success=True)

    for i in range(500):
        latency = random.gauss(0.050, 0.020)  # 50ms mean
        session.record_request("s3_two_hop", latency, success=True)

    # Print summary
    session.print_summary()

    # Export
    session.export_json('/tmp/test-metrics.json')
    session.export_csv('/tmp/test-metrics.csv')
