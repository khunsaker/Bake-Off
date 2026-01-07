#!/usr/bin/env python3
"""
Threshold Evaluation for Shark Bake-Off
Evaluates benchmark results against "fast enough" criteria
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
from metrics import QueryMetrics, PercentileStats


class QueryCategory(Enum):
    """Query categories with different threshold requirements"""
    IDENTIFIER_LOOKUP = "identifier_lookup"  # S1-S2
    TWO_HOP_TRAVERSAL = "two_hop_traversal"  # S3-S5
    THREE_HOP_TRAVERSAL = "three_hop_traversal"  # S6-S8
    SIX_HOP_TRAVERSAL = "six_hop_traversal"  # S9-S10
    PROPERTY_WRITE = "property_write"  # S7
    RELATIONSHIP_WRITE = "relationship_write"  # S8


@dataclass
class LatencyThresholds:
    """Latency thresholds for a query category (in milliseconds)"""
    target_p50: float  # Target for p50
    acceptable_p95: float  # Acceptable for p95
    maximum_p99: float  # Maximum for p99


# Thresholds from SHARK-BAKEOFF-PLAN.md
THRESHOLDS = {
    QueryCategory.IDENTIFIER_LOOKUP: LatencyThresholds(
        target_p50=10.0,
        acceptable_p95=50.0,
        maximum_p99=100.0
    ),
    QueryCategory.TWO_HOP_TRAVERSAL: LatencyThresholds(
        target_p50=50.0,
        acceptable_p95=150.0,
        maximum_p99=300.0
    ),
    QueryCategory.THREE_HOP_TRAVERSAL: LatencyThresholds(
        target_p50=100.0,
        acceptable_p95=300.0,
        maximum_p99=500.0
    ),
    QueryCategory.SIX_HOP_TRAVERSAL: LatencyThresholds(
        target_p50=500.0,
        acceptable_p95=1000.0,
        maximum_p99=2000.0
    ),
    QueryCategory.PROPERTY_WRITE: LatencyThresholds(
        target_p50=50.0,
        acceptable_p95=200.0,
        maximum_p99=500.0
    ),
    QueryCategory.RELATIONSHIP_WRITE: LatencyThresholds(
        target_p50=100.0,
        acceptable_p95=300.0,
        maximum_p99=500.0
    ),
}


@dataclass
class ThroughputThresholds:
    """Throughput thresholds (queries per second)"""
    baseline: float  # Baseline throughput
    peak: float  # Peak load target
    stress_test: float  # Stress test target


# Throughput requirements from plan
THROUGHPUT_REQUIREMENTS = {
    "identifier_lookups": ThroughputThresholds(625, 1000, 1750),
    "analytics_queries": ThroughputThresholds(100, 200, 500),
    "writes": ThroughputThresholds(30, 100, 500),
}


class EvaluationResult(Enum):
    """Evaluation result status"""
    PASS = "PASS"  # Meets all thresholds
    CONDITIONAL_PASS = "CONDITIONAL_PASS"  # Passes with caching
    FAIL = "FAIL"  # Does not meet thresholds


@dataclass
class ThresholdEvaluation:
    """Result of threshold evaluation"""
    query_name: str
    category: QueryCategory
    result: EvaluationResult
    p50_status: str
    p95_status: str
    p99_status: str
    throughput_status: Optional[str] = None
    details: Optional[str] = None


class ThresholdEvaluator:
    """
    Evaluates query metrics against thresholds
    """

    def __init__(self, cache_enabled: bool = False):
        """
        Initialize evaluator

        Args:
            cache_enabled: Whether caching is enabled
        """
        self.cache_enabled = cache_enabled

    def evaluate_query(
        self,
        metrics: QueryMetrics,
        category: QueryCategory,
        expected_throughput: Optional[float] = None
    ) -> ThresholdEvaluation:
        """
        Evaluate a single query against thresholds

        Args:
            metrics: Query metrics
            category: Query category
            expected_throughput: Expected minimum throughput (qps)

        Returns:
            ThresholdEvaluation result
        """
        thresholds = THRESHOLDS[category]
        stats = metrics.latency_stats

        # Evaluate latencies
        p50_pass = stats.p50 <= thresholds.target_p50
        p95_pass = stats.p95 <= thresholds.acceptable_p95
        p99_pass = stats.p99 <= thresholds.maximum_p99

        # Status strings with color indicators
        p50_status = self._format_status(stats.p50, thresholds.target_p50, p50_pass)
        p95_status = self._format_status(stats.p95, thresholds.acceptable_p95, p95_pass)
        p99_status = self._format_status(stats.p99, thresholds.maximum_p99, p99_pass)

        # Throughput evaluation
        throughput_pass = True
        throughput_status = None
        if expected_throughput:
            throughput_pass = metrics.throughput_qps >= expected_throughput
            throughput_status = f"{metrics.throughput_qps:.2f} qps (expected >={expected_throughput:.2f}): {'✓' if throughput_pass else '✗'}"

        # Overall result
        all_pass = p50_pass and p95_pass and p99_pass and throughput_pass

        if all_pass:
            result = EvaluationResult.PASS
            details = "All thresholds met"
        elif p99_pass and self.cache_enabled:
            result = EvaluationResult.CONDITIONAL_PASS
            details = "Passes with caching enabled (80%+ hit rate required)"
        else:
            result = EvaluationResult.FAIL
            details = self._failure_details(p50_pass, p95_pass, p99_pass, throughput_pass)

        return ThresholdEvaluation(
            query_name=metrics.query_name,
            category=category,
            result=result,
            p50_status=p50_status,
            p95_status=p95_status,
            p99_status=p99_status,
            throughput_status=throughput_status,
            details=details
        )

    def _format_status(self, actual: float, threshold: float, passed: bool) -> str:
        """Format status string"""
        symbol = "✓" if passed else "✗"
        return f"{actual:.2f}ms (threshold <={threshold:.2f}ms): {symbol}"

    def _failure_details(
        self,
        p50_pass: bool,
        p95_pass: bool,
        p99_pass: bool,
        throughput_pass: bool
    ) -> str:
        """Generate failure details"""
        failures = []
        if not p50_pass:
            failures.append("p50 exceeded target")
        if not p95_pass:
            failures.append("p95 exceeded acceptable")
        if not p99_pass:
            failures.append("p99 exceeded maximum")
        if not throughput_pass:
            failures.append("throughput below expected")

        return "Failed: " + ", ".join(failures)

    def print_evaluation(self, evaluation: ThresholdEvaluation):
        """Print evaluation result"""
        print(f"\n{'='*70}")
        print(f"Query: {evaluation.query_name}")
        print(f"Category: {evaluation.category.value}")
        print(f"{'='*70}")
        print(f"p50:  {evaluation.p50_status}")
        print(f"p95:  {evaluation.p95_status}")
        print(f"p99:  {evaluation.p99_status}")

        if evaluation.throughput_status:
            print(f"Throughput: {evaluation.throughput_status}")

        print(f"\nResult: {evaluation.result.value}")
        print(f"Details: {evaluation.details}")
        print(f"{'='*70}\n")


class BenchmarkEvaluator:
    """
    Evaluates full benchmark results
    """

    def __init__(self, cache_enabled: bool = False):
        self.evaluator = ThresholdEvaluator(cache_enabled=cache_enabled)
        self.evaluations: List[ThresholdEvaluation] = []

    def evaluate_benchmark(
        self,
        metrics_list: List[QueryMetrics],
        category_map: Dict[str, QueryCategory],
        throughput_map: Optional[Dict[str, float]] = None
    ):
        """
        Evaluate all benchmark queries

        Args:
            metrics_list: List of query metrics
            category_map: Map of query name to category
            throughput_map: Optional map of query name to expected throughput
        """
        throughput_map = throughput_map or {}

        for metrics in metrics_list:
            category = category_map.get(metrics.query_name)
            if not category:
                print(f"Warning: No category mapping for {metrics.query_name}")
                continue

            expected_throughput = throughput_map.get(metrics.query_name)

            evaluation = self.evaluator.evaluate_query(
                metrics,
                category,
                expected_throughput
            )

            self.evaluations.append(evaluation)

    def print_summary(self):
        """Print benchmark summary"""
        print(f"\n{'#'*70}")
        print(f"# BENCHMARK EVALUATION SUMMARY")
        print(f"{'#'*70}\n")

        # Count results
        pass_count = sum(1 for e in self.evaluations if e.result == EvaluationResult.PASS)
        conditional_pass_count = sum(1 for e in self.evaluations if e.result == EvaluationResult.CONDITIONAL_PASS)
        fail_count = sum(1 for e in self.evaluations if e.result == EvaluationResult.FAIL)

        total = len(self.evaluations)

        print(f"Total Queries Evaluated: {total}")
        print(f"  PASS:             {pass_count} ({pass_count/total*100:.1f}%)")
        print(f"  CONDITIONAL PASS: {conditional_pass_count} ({conditional_pass_count/total*100:.1f}%)")
        print(f"  FAIL:             {fail_count} ({fail_count/total*100:.1f}%)")
        print()

        # Print individual evaluations
        for evaluation in self.evaluations:
            self.evaluator.print_evaluation(evaluation)

        # Overall recommendation
        print(f"\n{'#'*70}")
        print(f"# OVERALL RECOMMENDATION")
        print(f"{'#'*70}\n")

        if fail_count == 0 and conditional_pass_count == 0:
            print("✓ PASS: All queries meet performance thresholds")
            print("Recommendation: Proceed with this configuration")
        elif fail_count == 0:
            print("⚠ CONDITIONAL PASS: All queries pass with caching")
            print("Recommendation: Deploy with Redis caching (80%+ hit rate required)")
        else:
            print("✗ FAIL: Some queries do not meet thresholds")
            print("Recommendation: Consider hybrid architecture or query optimization")
            print("\nFailed queries:")
            for e in self.evaluations:
                if e.result == EvaluationResult.FAIL:
                    print(f"  - {e.query_name}: {e.details}")

        print(f"\n{'#'*70}\n")

    def export_results(self, filename: str):
        """Export evaluation results to JSON"""
        import json

        data = {
            'summary': {
                'total': len(self.evaluations),
                'pass': sum(1 for e in self.evaluations if e.result == EvaluationResult.PASS),
                'conditional_pass': sum(1 for e in self.evaluations if e.result == EvaluationResult.CONDITIONAL_PASS),
                'fail': sum(1 for e in self.evaluations if e.result == EvaluationResult.FAIL),
            },
            'evaluations': [
                {
                    'query_name': e.query_name,
                    'category': e.category.value,
                    'result': e.result.value,
                    'p50_status': e.p50_status,
                    'p95_status': e.p95_status,
                    'p99_status': e.p99_status,
                    'throughput_status': e.throughput_status,
                    'details': e.details,
                }
                for e in self.evaluations
            ]
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Evaluation results exported to {filename}")


# Example usage
if __name__ == '__main__':
    from metrics import BenchmarkSession, PercentileStats
    import random

    # Create sample metrics
    session = BenchmarkSession("test")

    # Simulate S1 (identifier lookup) - should pass
    for i in range(1000):
        session.record_request("s1_simple_lookup", random.gauss(0.005, 0.002), success=True)

    # Simulate S3 (two-hop) - should pass
    for i in range(500):
        session.record_request("s3_two_hop", random.gauss(0.040, 0.015), success=True)

    # Simulate S6 (three-hop) - borderline
    for i in range(300):
        session.record_request("s6_three_hop", random.gauss(0.120, 0.050), success=True)

    metrics_list = session.get_all_metrics()

    # Define category mappings
    category_map = {
        "s1_simple_lookup": QueryCategory.IDENTIFIER_LOOKUP,
        "s3_two_hop": QueryCategory.TWO_HOP_TRAVERSAL,
        "s6_three_hop": QueryCategory.THREE_HOP_TRAVERSAL,
    }

    # Evaluate
    evaluator = BenchmarkEvaluator(cache_enabled=True)
    evaluator.evaluate_benchmark(metrics_list, category_map)
    evaluator.print_summary()
