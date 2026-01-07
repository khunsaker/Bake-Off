#!/usr/bin/env python3
"""
Benchmark Runner for Shark Bake-Off
Orchestrates load testing, metrics collection, and evaluation
"""

import argparse
import time
import sys
import requests
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from metrics import BenchmarkSession
from workload import (
    WorkloadGenerator, WorkloadPattern, WORKLOAD_PATTERNS,
    DatasetSelector, create_default_queries, QueryType
)
from thresholds import (
    BenchmarkEvaluator, QueryCategory,
    THROUGHPUT_REQUIREMENTS
)


class BenchmarkRunner:
    """
    Orchestrates benchmark execution
    """

    def __init__(
        self,
        base_url: str,
        pattern: WorkloadPattern,
        total_requests: int = 10000,
        concurrency: int = 10,
        cache_enabled: bool = False,
    ):
        """
        Initialize benchmark runner

        Args:
            base_url: Base URL of API under test
            pattern: Workload pattern to use
            total_requests: Total number of requests to send
            concurrency: Number of concurrent workers
            cache_enabled: Whether caching is enabled on server
        """
        self.base_url = base_url.rstrip('/')
        self.pattern = pattern
        self.total_requests = total_requests
        self.concurrency = concurrency
        self.cache_enabled = cache_enabled

        # Initialize components
        self.session = BenchmarkSession(f"benchmark-{pattern.name}")
        self.dataset = DatasetSelector()

        # Create queries
        lookup_queries, analytics_queries, write_queries = create_default_queries(self.dataset)

        self.generator = WorkloadGenerator(
            pattern=pattern,
            lookup_queries=lookup_queries,
            analytics_queries=analytics_queries,
            write_queries=write_queries,
        )

    def execute_request(self, query_type: QueryType, query_spec) -> Dict:
        """
        Execute a single request

        Returns:
            Dict with timing and status info
        """
        start_time = time.time()
        success = False
        error = None

        try:
            # Build URL
            url = self.base_url + query_spec.endpoint
            for param, value in query_spec.params.items():
                url = url.replace(f"{{{param}}}", str(value))

            # Execute request
            if query_type == QueryType.WRITE:
                response = requests.post(url, json=query_spec.params, timeout=30)
            else:
                response = requests.get(url, timeout=30)

            # Check response
            if response.status_code in [200, 201, 202, 404]:  # 404 acceptable for test data
                success = True
            else:
                error = f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            error = "Timeout"
        except Exception as e:
            error = str(e)

        latency = time.time() - start_time

        return {
            'query_name': query_spec.endpoint.split('/')[-1].replace('{', '').replace('}', ''),
            'query_type': query_type,
            'latency': latency,
            'success': success,
            'error': error,
        }

    def run_benchmark(self):
        """Run the benchmark"""
        print(f"\n{'='*70}")
        print(f"Benchmark Runner")
        print(f"{'='*70}")
        print(f"Target:       {self.base_url}")
        print(f"Pattern:      {self.pattern.name}")
        print(f"Requests:     {self.total_requests:,}")
        print(f"Concurrency:  {self.concurrency}")
        print(f"Cache:        {'Enabled' if self.cache_enabled else 'Disabled'}")
        print(f"{'='*70}\n")

        # Verify server is accessible
        print("Checking server connectivity...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ Server is accessible\n")
            else:
                print(f"✗ Server returned {response.status_code}")
                sys.exit(1)
        except Exception as e:
            print(f"✗ Cannot connect to server: {e}")
            sys.exit(1)

        # Generate requests
        print(f"Generating {self.total_requests:,} requests...")
        requests_to_execute = self.generator.generate_requests(self.total_requests)
        print(f"✓ Generated {len(requests_to_execute):,} requests\n")

        # Execute requests with progress bar
        print("Executing benchmark...")
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            # Submit all requests
            futures = [
                executor.submit(self.execute_request, query_type, query_spec)
                for query_type, query_spec in requests_to_execute
            ]

            # Process results with progress bar
            with tqdm(total=len(futures), unit="req") as pbar:
                for future in as_completed(futures):
                    result = future.result()

                    # Record metrics
                    self.session.record_request(
                        query_name=result['query_name'],
                        latency_seconds=result['latency'],
                        success=result['success'],
                        error=result['error']
                    )

                    pbar.update(1)

        total_time = time.time() - start_time

        print(f"\n✓ Benchmark complete in {total_time:.2f}s")
        print(f"Overall throughput: {self.total_requests / total_time:.2f} qps\n")

        # Print metrics summary
        self.session.print_summary()

        return self.session.get_all_metrics()

    def evaluate_results(self, metrics_list: List):
        """Evaluate results against thresholds"""
        print("\n" + "="*70)
        print("Evaluating Results Against Thresholds")
        print("="*70 + "\n")

        # Define category mappings (simplified - extend as needed)
        category_map = {}
        for metrics in metrics_list:
            name = metrics.query_name
            if 'mode_s' in name or 'mmsi' in name:
                category_map[name] = QueryCategory.IDENTIFIER_LOOKUP
            elif 'country' in name and 'cross' not in name:
                category_map[name] = QueryCategory.TWO_HOP_TRAVERSAL
            elif 'cross-domain' in name:
                category_map[name] = QueryCategory.THREE_HOP_TRAVERSAL
            elif 'activity' in name and 'log' not in name:
                category_map[name] = QueryCategory.TWO_HOP_TRAVERSAL
            elif 'log' in name:
                category_map[name] = QueryCategory.PROPERTY_WRITE

        # Create evaluator
        evaluator = BenchmarkEvaluator(cache_enabled=self.cache_enabled)
        evaluator.evaluate_benchmark(metrics_list, category_map)
        evaluator.print_summary()

        return evaluator


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Shark Bake-Off Benchmark Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available workload patterns:
  lookup-95    Lookup Heavy (95/4/1)
  lookup-90    Lookup Heavy (90/8/2)
  lookup-85    Lookup Heavy (85/12/3)
  lookup-80    Lookup Medium (80/15/5)
  lookup-75    Lookup Medium (75/20/5)
  balanced-60  Balanced (60/35/5)
  balanced-50  Balanced (50/40/10)
  balanced-40  Balanced (40/45/15)
  analytics-30 Analytics Heavy (30/60/10)
  analytics-20 Analytics Heavy (20/70/10)
  analytics-10 Analytics Heavy (10/80/10)
  write-30     Write Heavy (50/20/30)
  write-40     Write Heavy (40/20/40)
  write-50     Write Heavy (30/20/50)

Examples:
  # Run lookup-heavy benchmark
  python runner.py http://localhost:8080 --pattern lookup-90 --requests 10000

  # Run balanced benchmark with caching
  python runner.py http://localhost:8080 --pattern balanced-50 --cache --requests 50000

  # High concurrency stress test
  python runner.py http://localhost:8080 --pattern lookup-95 --requests 100000 --concurrency 50
        """
    )

    parser.add_argument('url', help='Base URL of API to benchmark (e.g., http://localhost:8080)')
    parser.add_argument('--pattern', '-p', default='balanced-50',
                        choices=list(WORKLOAD_PATTERNS.keys()),
                        help='Workload pattern to use (default: balanced-50)')
    parser.add_argument('--requests', '-n', type=int, default=10000,
                        help='Total number of requests (default: 10000)')
    parser.add_argument('--concurrency', '-c', type=int, default=10,
                        help='Number of concurrent workers (default: 10)')
    parser.add_argument('--cache', action='store_true',
                        help='Caching is enabled on server')
    parser.add_argument('--output', '-o',
                        help='Output file prefix for results (JSON and CSV)')

    args = parser.parse_args()

    # Get pattern
    pattern = WORKLOAD_PATTERNS[args.pattern]

    # Create runner
    runner = BenchmarkRunner(
        base_url=args.url,
        pattern=pattern,
        total_requests=args.requests,
        concurrency=args.concurrency,
        cache_enabled=args.cache,
    )

    # Run benchmark
    metrics_list = runner.run_benchmark()

    # Evaluate results
    evaluator = runner.evaluate_results(metrics_list)

    # Export results if requested
    if args.output:
        runner.session.export_json(f"{args.output}.json")
        runner.session.export_csv(f"{args.output}.csv")
        evaluator.export_results(f"{args.output}-evaluation.json")

    print("\nBenchmark complete!")


if __name__ == '__main__':
    main()
