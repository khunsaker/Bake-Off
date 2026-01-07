#!/usr/bin/env python3
"""
Head-to-Head Comparison Runner
Shark Bake-Off: Phase B Comparison

Automates comprehensive comparison of optimally configured databases.
"""

import argparse
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

@dataclass
class ComparisonConfig:
    """Configuration for comparison test"""
    database: str
    base_url: str
    optimal_config_applied: bool = False

@dataclass
class WorkloadResult:
    """Result from a workload pattern test"""
    database: str
    workload_pattern: str
    requests: int
    concurrency: int
    p50_ms: float
    p75_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    p999_ms: float
    mean_ms: float
    throughput_qps: float
    success_count: int
    fail_count: int
    test_duration_sec: float


class ComparisonRunner:
    """Runs head-to-head database comparison"""

    # All 14 workload patterns
    WORKLOAD_PATTERNS = [
        "lookup-95",
        "lookup-90",
        "lookup-80",
        "balanced-70",
        "balanced-60",
        "balanced-50",
        "analytics-40",
        "analytics-30",
        "analytics-20",
        "analytics-10",
        "traversal-light",
        "traversal-heavy",
        "mixed-realistic",
        "write-heavy"
    ]

    # Concurrency levels to test
    CONCURRENCY_LEVELS = [1, 5, 10, 20, 50, 100]

    def __init__(self, databases: List[str], output_dir: Path = None):
        self.databases = databases
        self.base_dir = Path(__file__).parent
        self.output_dir = output_dir or (self.base_dir / "results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Benchmark harness location
        self.harness_dir = self.base_dir.parent.parent / "benchmark" / "harness"

        # Database configurations
        self.configs = {
            "postgresql": ComparisonConfig("postgresql", "http://localhost:8080"),
            "neo4j": ComparisonConfig("neo4j", "http://localhost:8080"),
            "memgraph": ComparisonConfig("memgraph", "http://localhost:8080")
        }

        # Results storage
        self.workload_results: Dict[str, List[WorkloadResult]] = {db: [] for db in databases}
        self.concurrency_results: Dict[str, List[WorkloadResult]] = {db: [] for db in databases}

    def verify_optimal_config(self, database: str) -> bool:
        """Verify optimal configuration is applied"""
        print(f"\n{'='*80}")
        print(f"CONFIGURATION VERIFICATION: {database.upper()}")
        print(f"{'='*80}")
        print(f"\nPlease verify that {database} is configured with optimal settings from Phase A.")
        print(f"Expected configuration: optimized.conf (or your selected variant)")
        print(f"\nReference: ../phase-a-optimization/{database}/configs/")

        response = input(f"\nIs {database} configured with optimal settings? (yes/no): ")
        return response.lower() in ['yes', 'y']

    def run_warmup(self, base_url: str, database: str):
        """Run warm-up workload"""
        print(f"\n[{database}] Running warm-up (5000 requests)...")

        cmd = [
            "python3", "runner.py",
            base_url,
            "--pattern", "balanced-50",
            "--requests", "5000",
            "--concurrency", "10"
        ]

        start = time.time()
        subprocess.run(cmd, cwd=self.harness_dir, check=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        duration = time.time() - start

        print(f"[{database}] Warm-up completed in {duration:.1f}s")

    def run_workload_test(self, database: str, base_url: str, workload: str,
                         requests: int = 50000, concurrency: int = 20) -> WorkloadResult:
        """Run a single workload test"""
        print(f"\n[{database}] Testing workload: {workload} (concurrency={concurrency})")

        # Create output file path
        db_output_dir = self.output_dir / database
        db_output_dir.mkdir(parents=True, exist_ok=True)
        output_prefix = db_output_dir / f"{workload}_c{concurrency}"

        cmd = [
            "python3", "runner.py",
            base_url,
            "--pattern", workload,
            "--requests", str(requests),
            "--concurrency", str(concurrency),
            "--output", str(output_prefix)
        ]

        start = time.time()
        subprocess.run(cmd, cwd=self.harness_dir, check=True)
        duration = time.time() - start

        # Find and parse result file
        result_files = list(output_prefix.parent.glob(f"{workload}_c{concurrency}*.csv"))
        if not result_files:
            raise FileNotFoundError(f"No result file found for {workload}")

        result_file = max(result_files, key=lambda p: p.stat().st_mtime)

        # Parse results
        result = self._parse_result_file(result_file, database, workload, concurrency, duration)

        print(f"[{database}] {workload}: p99={result.p99_ms:.2f}ms, "
              f"throughput={result.throughput_qps:.1f} req/s")

        return result

    def _parse_result_file(self, result_file: Path, database: str, workload: str,
                          concurrency: int, duration: float) -> WorkloadResult:
        """Parse benchmark result CSV file"""
        import csv

        total_requests = 0
        success_count = 0
        fail_count = 0

        # Weighted averages
        p50_weighted = 0
        p75_weighted = 0
        p90_weighted = 0
        p95_weighted = 0
        p99_weighted = 0
        p999_weighted = 0
        mean_weighted = 0

        with open(result_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'total_requests' in row:
                    count = int(row['total_requests'])
                    total_requests += count
                    success_count += int(row.get('successful', count))
                    fail_count += int(row.get('failed', 0))

                    p50_weighted += float(row.get('p50_ms', 0)) * count
                    p75_weighted += float(row.get('p75_ms', 0)) * count
                    p90_weighted += float(row.get('p90_ms', 0)) * count
                    p95_weighted += float(row.get('p95_ms', 0)) * count
                    p99_weighted += float(row.get('p99_ms', 0)) * count
                    p999_weighted += float(row.get('p999_ms', 0)) * count
                    mean_weighted += float(row.get('mean_ms', 0)) * count

        if total_requests == 0:
            raise ValueError(f"No results in {result_file}")

        return WorkloadResult(
            database=database,
            workload_pattern=workload,
            requests=total_requests,
            concurrency=concurrency,
            p50_ms=p50_weighted / total_requests,
            p75_ms=p75_weighted / total_requests,
            p90_ms=p90_weighted / total_requests,
            p95_ms=p95_weighted / total_requests,
            p99_ms=p99_weighted / total_requests,
            p999_ms=p999_weighted / total_requests,
            mean_ms=mean_weighted / total_requests,
            throughput_qps=total_requests / duration if duration > 0 else 0,
            success_count=success_count,
            fail_count=fail_count,
            test_duration_sec=duration
        )

    def run_workload_comparison(self, workloads: List[str], requests: int, concurrency: int):
        """Run workload pattern comparison for all databases"""
        print(f"\n{'='*80}")
        print(f"WORKLOAD PATTERN COMPARISON")
        print(f"{'='*80}")
        print(f"\nTesting {len(workloads)} workload patterns across {len(self.databases)} databases")
        print(f"Requests per test: {requests:,}")
        print(f"Concurrency: {concurrency}")
        print()

        for database in self.databases:
            print(f"\n{'='*80}")
            print(f"DATABASE: {database.upper()}")
            print(f"{'='*80}")

            # Verify config
            if not self.verify_optimal_config(database):
                print(f"⚠ Warning: Proceeding without verified optimal configuration")

            # Warm-up
            config = self.configs[database]
            self.run_warmup(config.base_url, database)

            # Run all workload tests
            for workload in workloads:
                try:
                    result = self.run_workload_test(database, config.base_url, workload,
                                                   requests, concurrency)
                    self.workload_results[database].append(result)

                    # Brief pause between tests
                    time.sleep(5)

                except Exception as e:
                    print(f"✗ Error testing {workload}: {e}")

            # Save database results
            self._save_database_results(database, "workload")

    def run_concurrency_comparison(self, concurrency_levels: List[int], requests: int):
        """Run concurrency scaling comparison"""
        print(f"\n{'='*80}")
        print(f"CONCURRENCY SCALING COMPARISON")
        print(f"{'='*80}")
        print(f"\nTesting {len(concurrency_levels)} concurrency levels across {len(self.databases)} databases")
        print(f"Workload pattern: balanced-50")
        print(f"Requests per test: {requests:,}")
        print()

        for database in self.databases:
            print(f"\n{'='*80}")
            print(f"DATABASE: {database.upper()}")
            print(f"{'='*80}")

            config = self.configs[database]
            self.run_warmup(config.base_url, database)

            for concurrency in concurrency_levels:
                try:
                    result = self.run_workload_test(database, config.base_url,
                                                   "balanced-50", requests, concurrency)
                    self.concurrency_results[database].append(result)

                    time.sleep(5)

                except Exception as e:
                    print(f"✗ Error testing concurrency {concurrency}: {e}")

            # Save database results
            self._save_database_results(database, "concurrency")

    def _save_database_results(self, database: str, test_type: str):
        """Save results for a database"""
        db_output_dir = self.output_dir / database
        summary_file = db_output_dir / f"{test_type}_summary.json"

        if test_type == "workload":
            results = self.workload_results[database]
        else:
            results = self.concurrency_results[database]

        data = {
            'database': database,
            'test_type': test_type,
            'timestamp': datetime.now().isoformat(),
            'results': [asdict(r) for r in results]
        }

        with open(summary_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✓ Results saved: {summary_file}")

    def print_summary(self):
        """Print comparison summary"""
        print(f"\n{'='*80}")
        print("COMPARISON SUMMARY")
        print(f"{'='*80}\n")

        if self.workload_results and any(self.workload_results.values()):
            print("WORKLOAD PATTERN WINNERS:\n")
            print(f"{'Pattern':<20} {'Winner':<15} {'p99 Latency':<15} {'Throughput':<15}")
            print(f"{'-'*65}")

            # Group results by workload
            workloads_tested = set()
            for results in self.workload_results.values():
                workloads_tested.update(r.workload_pattern for r in results)

            for workload in sorted(workloads_tested):
                # Find results for this workload across all databases
                workload_results = []
                for database in self.databases:
                    db_results = [r for r in self.workload_results[database]
                                 if r.workload_pattern == workload]
                    if db_results:
                        workload_results.extend(db_results)

                if workload_results:
                    # Find winner (lowest p99)
                    winner = min(workload_results, key=lambda x: x.p99_ms)
                    print(f"{workload:<20} {winner.database:<15} "
                          f"{winner.p99_ms:>10.2f} ms  {winner.throughput_qps:>10.1f} req/s")

        if self.concurrency_results and any(self.concurrency_results.values()):
            print(f"\n\nCONCURRENCY SCALING:\n")
            print(f"{'Database':<15} {'Concurrency':<15} {'p99 Latency':<15} {'Throughput':<15}")
            print(f"{'-'*60}")

            for database in sorted(self.databases):
                for result in sorted(self.concurrency_results[database],
                                   key=lambda x: x.concurrency):
                    print(f"{database:<15} {result.concurrency:<15} "
                          f"{result.p99_ms:>10.2f} ms  {result.throughput_qps:>10.1f} req/s")

        print(f"\n{'='*80}\n")
        print(f"Detailed results saved to: {self.output_dir}")
        print(f"Run analyze_crossover.py for crossover analysis")


def main():
    parser = argparse.ArgumentParser(description="Run Phase B head-to-head comparison")
    parser.add_argument("--databases", nargs="+",
                       default=["postgresql", "neo4j", "memgraph"],
                       help="Databases to compare")
    parser.add_argument("--workloads", nargs="+",
                       help="Workload patterns to test (default: all 14)")
    parser.add_argument("--concurrency", type=str,
                       help="Concurrency levels to test (comma-separated, e.g., '1,5,10,20')")
    parser.add_argument("--requests", type=int, default=50000,
                       help="Requests per test (default: 50000)")
    parser.add_argument("--test-type", choices=["workload", "concurrency", "both"],
                       default="both",
                       help="Type of test to run")
    parser.add_argument("--output", type=Path, default=None,
                       help="Output directory for results")

    args = parser.parse_args()

    # Parse workloads
    if args.workloads and args.workloads[0] == "all":
        workloads = ComparisonRunner.WORKLOAD_PATTERNS
    elif args.workloads:
        workloads = args.workloads
    else:
        workloads = ComparisonRunner.WORKLOAD_PATTERNS

    # Parse concurrency levels
    if args.concurrency:
        concurrency_levels = [int(x.strip()) for x in args.concurrency.split(',')]
    else:
        concurrency_levels = ComparisonRunner.CONCURRENCY_LEVELS

    # Create runner
    runner = ComparisonRunner(args.databases, args.output)

    print(f"\n{'='*80}")
    print("SHARK BAKE-OFF: PHASE B HEAD-TO-HEAD COMPARISON")
    print(f"{'='*80}\n")
    print(f"Databases: {', '.join(args.databases)}")
    print(f"Test type: {args.test_type}")
    print(f"Requests per test: {args.requests:,}")

    if args.test_type in ["workload", "both"]:
        print(f"Workload patterns: {len(workloads)}")

    if args.test_type in ["concurrency", "both"]:
        print(f"Concurrency levels: {concurrency_levels}")

    print()

    # Run tests
    try:
        if args.test_type in ["workload", "both"]:
            runner.run_workload_comparison(workloads, args.requests, concurrency=20)

        if args.test_type in ["concurrency", "both"]:
            runner.run_concurrency_comparison(concurrency_levels, args.requests)

        # Print summary
        runner.print_summary()

        print("\n✓ Phase B comparison complete!")
        print("\nNext steps:")
        print("  1. Run: python analyze_crossover.py")
        print("  2. Run: python visualize_results.py")
        print("  3. Review: RESULTS_SUMMARY.md")

    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        print("Partial results have been saved")
        sys.exit(1)


if __name__ == "__main__":
    main()
