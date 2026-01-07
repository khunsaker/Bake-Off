#!/usr/bin/env python3
"""
Parametric Workload Generator for Shark Bake-Off
Generates mixed workloads with different query distributions
"""

import random
from typing import List, Dict, Tuple, Callable, Any
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    """Query types for workload generation"""
    LOOKUP = "lookup"  # S1-S2: Simple identifier lookups
    ANALYTICS = "analytics"  # S3-S10: Multi-hop traversals
    WRITE = "write"  # S7-S8: Property and relationship updates


@dataclass
class WorkloadPattern:
    """
    Workload pattern definition

    Ratios are [lookup%, analytics%, write%]
    """
    name: str
    lookup_pct: int
    analytics_pct: int
    write_pct: int

    def __post_init__(self):
        """Validate percentages sum to 100"""
        total = self.lookup_pct + self.analytics_pct + self.write_pct
        if total != 100:
            raise ValueError(f"Percentages must sum to 100, got {total}")


# Pre-defined workload patterns from the plan
WORKLOAD_PATTERNS = {
    # Lookup-heavy patterns
    "lookup-95": WorkloadPattern("Lookup Heavy (95/4/1)", 95, 4, 1),
    "lookup-90": WorkloadPattern("Lookup Heavy (90/8/2)", 90, 8, 2),
    "lookup-85": WorkloadPattern("Lookup Heavy (85/12/3)", 85, 12, 3),
    "lookup-80": WorkloadPattern("Lookup Medium (80/15/5)", 80, 15, 5),
    "lookup-75": WorkloadPattern("Lookup Medium (75/20/5)", 75, 20, 5),

    # Balanced patterns
    "balanced-60": WorkloadPattern("Balanced (60/35/5)", 60, 35, 5),
    "balanced-50": WorkloadPattern("Balanced (50/40/10)", 50, 40, 10),
    "balanced-40": WorkloadPattern("Balanced (40/45/15)", 40, 45, 15),

    # Analytics-heavy patterns
    "analytics-30": WorkloadPattern("Analytics Heavy (30/60/10)", 30, 60, 10),
    "analytics-20": WorkloadPattern("Analytics Heavy (20/70/10)", 20, 70, 10),
    "analytics-10": WorkloadPattern("Analytics Heavy (10/80/10)", 10, 80, 10),

    # Write-heavy patterns
    "write-30": WorkloadPattern("Write Heavy (50/20/30)", 50, 20, 30),
    "write-40": WorkloadPattern("Write Heavy (40/20/40)", 40, 20, 40),
    "write-50": WorkloadPattern("Write Heavy (30/20/50)", 30, 20, 50),
}


@dataclass
class QuerySpec:
    """Specification for a query"""
    query_type: QueryType
    endpoint: str
    params: Dict[str, Any]
    expected_latency_ms: float  # Expected p99 latency


class WorkloadGenerator:
    """
    Generates requests according to workload patterns
    """

    def __init__(
        self,
        pattern: WorkloadPattern,
        lookup_queries: List[QuerySpec],
        analytics_queries: List[QuerySpec],
        write_queries: List[QuerySpec],
        seed: int = 42
    ):
        """
        Initialize workload generator

        Args:
            pattern: Workload pattern to use
            lookup_queries: List of lookup query specs
            analytics_queries: List of analytics query specs
            write_queries: List of write query specs
            seed: Random seed for reproducibility
        """
        self.pattern = pattern
        self.lookup_queries = lookup_queries
        self.analytics_queries = analytics_queries
        self.write_queries = write_queries

        random.seed(seed)

        # Build weighted distribution
        self.query_distribution = []
        self.query_distribution.extend(
            [(QueryType.LOOKUP, q) for q in lookup_queries] * pattern.lookup_pct
        )
        self.query_distribution.extend(
            [(QueryType.ANALYTICS, q) for q in analytics_queries] * pattern.analytics_pct
        )
        self.query_distribution.extend(
            [(QueryType.WRITE, q) for q in write_queries] * pattern.write_pct
        )

        random.shuffle(self.query_distribution)

    def next_query(self) -> Tuple[QueryType, QuerySpec]:
        """Get next query based on workload pattern"""
        return random.choice(self.query_distribution)

    def generate_requests(self, count: int) -> List[Tuple[QueryType, QuerySpec]]:
        """Generate a sequence of requests"""
        return [self.next_query() for _ in range(count)]


class DatasetSelector:
    """
    Selects realistic test data for queries
    """

    def __init__(self, data_file: str = None):
        """
        Initialize dataset selector

        Args:
            data_file: Optional file with real identifiers
        """
        # Sample Mode-S identifiers (aircraft)
        self.mode_s_ids = [
            "A12345", "A67890", "B12345", "C98765", "D11111",
            "E22222", "F33333", "G44444", "H55555", "I66666",
        ]

        # Sample MMSI identifiers (ships)
        self.mmsi_ids = [
            "366123456", "366234567", "366345678", "235987654", "235876543",
            "311234567", "311345678", "303456789", "257123456", "257234567",
        ]

        # Sample countries
        self.countries = [
            "USA", "China", "Russia", "United Kingdom", "France",
            "Germany", "Japan", "India", "Italy", "Canada",
        ]

        # Sample tail numbers
        self.tail_numbers = [
            "N12345", "N67890", "G-ABCD", "D-EFGH", "F-IJKL",
        ]

    def random_mode_s(self) -> str:
        """Get random Mode-S identifier"""
        return random.choice(self.mode_s_ids)

    def random_mmsi(self) -> str:
        """Get random MMSI identifier"""
        return random.choice(self.mmsi_ids)

    def random_country(self) -> str:
        """Get random country"""
        return random.choice(self.countries)

    def random_tail_number(self) -> str:
        """Get random tail number"""
        return random.choice(self.tail_numbers)


def create_default_queries(dataset: DatasetSelector) -> Tuple[List[QuerySpec], List[QuerySpec], List[QuerySpec]]:
    """
    Create default query specifications

    Returns:
        (lookup_queries, analytics_queries, write_queries)
    """

    # Lookup queries (S1-S2)
    lookup_queries = [
        QuerySpec(
            query_type=QueryType.LOOKUP,
            endpoint="/api/aircraft/mode_s/{mode_s}",
            params={"mode_s": dataset.random_mode_s()},
            expected_latency_ms=10.0,
        ),
        QuerySpec(
            query_type=QueryType.LOOKUP,
            endpoint="/api/ship/mmsi/{mmsi}",
            params={"mmsi": dataset.random_mmsi()},
            expected_latency_ms=10.0,
        ),
    ]

    # Analytics queries (S3-S10)
    analytics_queries = [
        QuerySpec(
            query_type=QueryType.ANALYTICS,
            endpoint="/api/aircraft/country/{country}",
            params={"country": dataset.random_country()},
            expected_latency_ms=50.0,  # Two-hop
        ),
        QuerySpec(
            query_type=QueryType.ANALYTICS,
            endpoint="/api/cross-domain/country/{country}",
            params={"country": dataset.random_country()},
            expected_latency_ms=100.0,  # Three-hop
        ),
        QuerySpec(
            query_type=QueryType.ANALYTICS,
            endpoint="/api/activity/mmsi/{mmsi}",
            params={"mmsi": dataset.random_mmsi()},
            expected_latency_ms=30.0,  # Activity history
        ),
    ]

    # Write queries (S7-S8)
    write_queries = [
        QuerySpec(
            query_type=QueryType.WRITE,
            endpoint="/api/activity/log",
            params={
                "track_id": f"BENCH-{random.randint(1000, 9999)}",
                "event_type": "activity_detected",
                "domain": "AIR",
                "mode_s": dataset.random_mode_s(),
                "activity_type": "benchmark_test",
            },
            expected_latency_ms=50.0,
        ),
    ]

    return lookup_queries, analytics_queries, write_queries


def print_workload_summary(pattern: WorkloadPattern, total_requests: int = 1000):
    """Print workload summary"""
    print(f"\n{'='*70}")
    print(f"Workload Pattern: {pattern.name}")
    print(f"{'='*70}")
    print(f"Lookup:     {pattern.lookup_pct:3d}% ({int(total_requests * pattern.lookup_pct / 100):,} requests)")
    print(f"Analytics:  {pattern.analytics_pct:3d}% ({int(total_requests * pattern.analytics_pct / 100):,} requests)")
    print(f"Write:      {pattern.write_pct:3d}% ({int(total_requests * pattern.write_pct / 100):,} requests)")
    print(f"Total:      100% ({total_requests:,} requests)")
    print(f"{'='*70}\n")


# Example usage
if __name__ == '__main__':
    dataset = DatasetSelector()
    lookup_queries, analytics_queries, write_queries = create_default_queries(dataset)

    # Test each workload pattern
    for pattern_name, pattern in WORKLOAD_PATTERNS.items():
        print_workload_summary(pattern, total_requests=10000)

        generator = WorkloadGenerator(
            pattern=pattern,
            lookup_queries=lookup_queries,
            analytics_queries=analytics_queries,
            write_queries=write_queries,
        )

        # Generate sample requests
        requests = generator.generate_requests(100)

        # Count query types
        counts = {QueryType.LOOKUP: 0, QueryType.ANALYTICS: 0, QueryType.WRITE: 0}
        for query_type, _ in requests:
            counts[query_type] += 1

        print(f"Sample (100 requests): Lookup={counts[QueryType.LOOKUP]}, "
              f"Analytics={counts[QueryType.ANALYTICS]}, Write={counts[QueryType.WRITE]}")
        print()
