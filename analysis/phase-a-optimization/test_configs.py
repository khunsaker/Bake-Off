#!/usr/bin/env python3
"""
Configuration Testing Framework
Shark Bake-Off: Phase A Optimization

Automates testing of different database configurations:
1. Apply configuration variant
2. Restart database
3. Run warm-up
4. Run benchmark
5. Collect and compare results
"""

import argparse
import subprocess
import time
import json
import csv
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import sys

@dataclass
class ConfigTestResult:
    """Result from testing a configuration variant"""
    database: str
    config_variant: str
    warmup_time_seconds: float
    benchmark_time_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    throughput_qps: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    p999_latency_ms: float
    mean_latency_ms: float

    def to_dict(self) -> Dict:
        return asdict(self)


class ConfigTester:
    """Automates configuration testing for a database"""

    def __init__(self, database: str, base_url: str = "http://localhost:8080"):
        self.database = database.lower()
        self.base_url = base_url
        self.base_dir = Path(__file__).parent
        self.db_dir = self.base_dir / self.database
        self.results_dir = self.db_dir / "results"
        self.configs_dir = self.db_dir / "configs"

        # Ensure directories exist
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Benchmark harness location
        self.harness_dir = self.base_dir.parent.parent / "benchmark" / "harness"

        # Default benchmark parameters
        self.warmup_requests = 5000
        self.warmup_pattern = "lookup-95"
        self.benchmark_requests = 50000
        self.benchmark_pattern = "balanced-50"
        self.concurrency = 20

    def test_configuration(self, config_variant: str) -> ConfigTestResult:
        """Test a specific configuration variant"""
        print(f"\n{'='*80}")
        print(f"Testing {self.database.upper()} - {config_variant} configuration")
        print(f"{'='*80}\n")

        # Step 1: Apply configuration
        print(f"[1/5] Applying {config_variant} configuration...")
        self._apply_configuration(config_variant)

        # Step 2: Restart database
        print(f"[2/5] Restarting {self.database} container...")
        self._restart_database()

        # Step 3: Wait for database to be ready
        print(f"[3/5] Waiting for database to be ready...")
        self._wait_for_database()

        # Step 4: Run warm-up
        print(f"[4/5] Running warm-up ({self.warmup_requests} requests)...")
        warmup_start = time.time()
        self._run_warmup()
        warmup_duration = time.time() - warmup_start
        print(f"  Warm-up completed in {warmup_duration:.1f}s")

        # Step 5: Run benchmark
        print(f"[5/5] Running benchmark ({self.benchmark_requests} requests)...")
        benchmark_start = time.time()
        result_file = self._run_benchmark(config_variant)
        benchmark_duration = time.time() - benchmark_start
        print(f"  Benchmark completed in {benchmark_duration:.1f}s")

        # Parse results
        result = self._parse_results(
            config_variant,
            result_file,
            warmup_duration,
            benchmark_duration
        )

        # Display summary
        self._display_result(result)

        return result

    def _apply_configuration(self, config_variant: str):
        """Apply configuration variant (database-specific)"""
        config_file = self.configs_dir / f"{config_variant}.conf"

        if self.database == "postgresql":
            # PostgreSQL: Copy config to container
            if not config_file.exists():
                raise FileNotFoundError(f"Config file not found: {config_file}")

            print(f"  Config file: {config_file}")
            print(f"  Note: For PostgreSQL, you must manually apply the config:")
            print(f"        docker cp {config_file} shark-postgres:/etc/postgresql/postgresql.conf")
            print(f"        docker restart shark-postgres")

        elif self.database == "neo4j":
            # Neo4j: Update docker-compose or use environment variables
            if not config_file.exists():
                raise FileNotFoundError(f"Config file not found: {config_file}")

            print(f"  Config file: {config_file}")
            print(f"  Note: For Neo4j, you must manually update docker-compose.yml to mount:")
            print(f"        volumes:")
            print(f"          - {config_file}:/var/lib/neo4j/conf/neo4j.conf")

        elif self.database == "memgraph":
            # Memgraph: Use command-line flags in docker-compose
            config_script = self.configs_dir / f"{config_variant}.sh"
            if not config_script.exists():
                raise FileNotFoundError(f"Config script not found: {config_script}")

            print(f"  Config script: {config_script}")
            print(f"  Note: For Memgraph, you must manually update docker-compose.yml command section")
            print(f"        See {config_script} for flags to add")

        else:
            raise ValueError(f"Unknown database: {self.database}")

        input("\n  Press Enter after applying configuration...")

    def _restart_database(self):
        """Restart database container"""
        container_name = f"shark-{self.database}"

        print(f"  Restarting container: {container_name}")
        subprocess.run(["docker", "restart", container_name], check=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print(f"  Container restarted")

    def _wait_for_database(self, max_wait_seconds: int = 60):
        """Wait for database to be ready"""
        print(f"  Waiting up to {max_wait_seconds}s for database...")

        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            try:
                # Try a simple health check via API
                import requests
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"  Database ready!")
                    return
            except:
                pass

            time.sleep(2)

        raise TimeoutError(f"Database not ready after {max_wait_seconds}s")

    def _run_warmup(self):
        """Run warm-up workload"""
        cmd = [
            "python3", "runner.py",
            self.base_url,
            "--pattern", self.warmup_pattern,
            "--requests", str(self.warmup_requests),
            "--concurrency", str(self.concurrency)
        ]

        subprocess.run(cmd, cwd=self.harness_dir, check=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _run_benchmark(self, config_variant: str) -> Path:
        """Run full benchmark and return results file path"""
        output_prefix = self.results_dir / config_variant

        cmd = [
            "python3", "runner.py",
            self.base_url,
            "--pattern", self.benchmark_pattern,
            "--requests", str(self.benchmark_requests),
            "--concurrency", str(self.concurrency),
            "--output", str(output_prefix)
        ]

        subprocess.run(cmd, cwd=self.harness_dir, check=True)

        # Find the generated CSV file
        result_files = list(output_prefix.parent.glob(f"{config_variant}*.csv"))
        if not result_files:
            raise FileNotFoundError(f"No result files found with prefix: {output_prefix}")

        # Return the most recent file
        return max(result_files, key=lambda p: p.stat().st_mtime)

    def _parse_results(self, config_variant: str, result_file: Path,
                      warmup_duration: float, benchmark_duration: float) -> ConfigTestResult:
        """Parse benchmark results from CSV"""
        # Read the summary from the CSV file
        # Expected format from benchmark harness:
        # Query Type, Total Requests, Successful, Failed, p50, p95, p99, p999, mean

        total_requests = 0
        successful = 0
        failed = 0

        # Weighted average of latencies (by request count)
        p50_weighted = 0
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
                    successful += int(row.get('successful', count))
                    failed += int(row.get('failed', 0))

                    # Weight by request count
                    p50_weighted += float(row.get('p50_ms', 0)) * count
                    p95_weighted += float(row.get('p95_ms', 0)) * count
                    p99_weighted += float(row.get('p99_ms', 0)) * count
                    p999_weighted += float(row.get('p999_ms', 0)) * count
                    mean_weighted += float(row.get('mean_ms', 0)) * count

        # Calculate weighted averages
        if total_requests > 0:
            p50_ms = p50_weighted / total_requests
            p95_ms = p95_weighted / total_requests
            p99_ms = p99_weighted / total_requests
            p999_ms = p999_weighted / total_requests
            mean_ms = mean_weighted / total_requests
        else:
            p50_ms = p95_ms = p99_ms = p999_ms = mean_ms = 0

        throughput = total_requests / benchmark_duration if benchmark_duration > 0 else 0

        return ConfigTestResult(
            database=self.database,
            config_variant=config_variant,
            warmup_time_seconds=warmup_duration,
            benchmark_time_seconds=benchmark_duration,
            total_requests=total_requests,
            successful_requests=successful,
            failed_requests=failed,
            throughput_qps=throughput,
            p50_latency_ms=p50_ms,
            p95_latency_ms=p95_ms,
            p99_latency_ms=p99_ms,
            p999_latency_ms=p999_ms,
            mean_latency_ms=mean_ms
        )

    def _display_result(self, result: ConfigTestResult):
        """Display formatted result"""
        print(f"\n{'='*80}")
        print(f"RESULT: {result.database.upper()} - {result.config_variant}")
        print(f"{'='*80}")
        print(f"Total Requests:     {result.total_requests:,}")
        print(f"Successful:         {result.successful_requests:,}")
        print(f"Failed:             {result.failed_requests:,}")
        print(f"Throughput:         {result.throughput_qps:.1f} req/s")
        print(f"\nLatency Percentiles:")
        print(f"  p50:              {result.p50_latency_ms:.2f} ms")
        print(f"  p95:              {result.p95_latency_ms:.2f} ms")
        print(f"  p99:              {result.p99_latency_ms:.2f} ms")
        print(f"  p99.9:            {result.p999_latency_ms:.2f} ms")
        print(f"  mean:             {result.mean_latency_ms:.2f} ms")
        print(f"{'='*80}\n")

    def compare_results(self, baseline: ConfigTestResult,
                       optimized: ConfigTestResult):
        """Compare two configuration results"""
        print(f"\n{'='*80}")
        print(f"COMPARISON: {baseline.config_variant} vs {optimized.config_variant}")
        print(f"{'='*80}\n")

        def pct_change(old, new):
            if old == 0:
                return 0
            return ((new - old) / old) * 100

        def improvement_symbol(pct, higher_is_better=True):
            threshold = 2.0  # 2% threshold for "significant"
            if abs(pct) < threshold:
                return "≈"  # Approximately equal
            if higher_is_better:
                return "↑" if pct > 0 else "↓"
            else:
                return "↓" if pct > 0 else "↑"

        # Throughput (higher is better)
        throughput_pct = pct_change(baseline.throughput_qps, optimized.throughput_qps)
        print(f"Throughput:         {baseline.throughput_qps:.1f} → {optimized.throughput_qps:.1f} req/s "
              f"({throughput_pct:+.1f}%) {improvement_symbol(throughput_pct, True)}")

        # Latencies (lower is better)
        p50_pct = pct_change(baseline.p50_latency_ms, optimized.p50_latency_ms)
        p95_pct = pct_change(baseline.p95_latency_ms, optimized.p95_latency_ms)
        p99_pct = pct_change(baseline.p99_latency_ms, optimized.p99_latency_ms)
        mean_pct = pct_change(baseline.mean_latency_ms, optimized.mean_latency_ms)

        print(f"\nLatency Changes:")
        print(f"  p50:              {baseline.p50_latency_ms:.2f} → {optimized.p50_latency_ms:.2f} ms "
              f"({p50_pct:+.1f}%) {improvement_symbol(p50_pct, False)}")
        print(f"  p95:              {baseline.p95_latency_ms:.2f} → {optimized.p95_latency_ms:.2f} ms "
              f"({p95_pct:+.1f}%) {improvement_symbol(p95_pct, False)}")
        print(f"  p99:              {baseline.p99_latency_ms:.2f} → {optimized.p99_latency_ms:.2f} ms "
              f"({p99_pct:+.1f}%) {improvement_symbol(p99_pct, False)}")
        print(f"  mean:             {baseline.mean_latency_ms:.2f} → {optimized.mean_latency_ms:.2f} ms "
              f"({mean_pct:+.1f}%) {improvement_symbol(mean_pct, False)}")

        # Overall assessment
        print(f"\n{'='*80}")
        if p99_pct < -5:
            print("✓ SIGNIFICANT IMPROVEMENT (p99 latency reduced by >5%)")
        elif p99_pct > 5:
            print("✗ REGRESSION (p99 latency increased by >5%)")
        else:
            print("≈ MARGINAL CHANGE (p99 latency within ±5%)")
        print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Test database configurations")
    parser.add_argument("database", choices=["postgresql", "neo4j", "memgraph"],
                       help="Database to test")
    parser.add_argument("--configs", nargs="+",
                       default=["default", "conservative", "optimized", "extreme"],
                       help="Configuration variants to test (default: all)")
    parser.add_argument("--base-url", default="http://localhost:8080",
                       help="Base URL for API (default: http://localhost:8080)")
    parser.add_argument("--compare-to-baseline", action="store_true",
                       help="Compare all configs to baseline (default)")

    args = parser.parse_args()

    tester = ConfigTester(args.database, args.base_url)

    results = []

    # Test each configuration
    for config in args.configs:
        try:
            result = tester.test_configuration(config)
            results.append(result)
        except Exception as e:
            print(f"\n✗ Error testing {config}: {e}\n")
            continue

    # Compare to baseline if requested
    if args.compare_to_baseline and len(results) > 1:
        baseline = results[0]  # First config is baseline
        for optimized in results[1:]:
            tester.compare_results(baseline, optimized)

    # Save results summary
    summary_file = tester.results_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump([r.to_dict() for r in results], f, indent=2)

    print(f"\nResults summary saved to: {summary_file}")


if __name__ == "__main__":
    main()
