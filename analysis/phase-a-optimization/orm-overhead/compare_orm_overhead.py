#!/usr/bin/env python3
"""
ORM Overhead Comparison Tool
Shark Bake-Off: Phase A Optimization

Compares performance of raw drivers vs ORM/OGM implementations.
"""

import argparse
import json
import csv
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
import sys

@dataclass
class ImplementationResult:
    """Result from a specific implementation"""
    database: str
    implementation: str
    language: str
    type: str  # "raw", "orm", "ogm"
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    mean_latency_ms: float
    throughput_qps: float
    code_loc: int = 0  # Lines of code (manual input)

    def overhead_vs_baseline(self, baseline: 'ImplementationResult') -> Dict[str, float]:
        """Calculate overhead percentage compared to baseline"""
        return {
            'p50_overhead_pct': self._pct_change(baseline.p50_latency_ms, self.p50_latency_ms),
            'p95_overhead_pct': self._pct_change(baseline.p95_latency_ms, self.p95_latency_ms),
            'p99_overhead_pct': self._pct_change(baseline.p99_latency_ms, self.p99_latency_ms),
            'mean_overhead_pct': self._pct_change(baseline.mean_latency_ms, self.mean_latency_ms),
            'throughput_change_pct': self._pct_change(baseline.throughput_qps, self.throughput_qps),
        }

    @staticmethod
    def _pct_change(baseline, value):
        if baseline == 0:
            return 0
        return ((value - baseline) / baseline) * 100


class ORMOverheadAnalyzer:
    """Analyzes ORM overhead across different implementations"""

    def __init__(self):
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        self.results: List[ImplementationResult] = []

    def load_result(self, result_file: Path, database: str, implementation: str,
                   language: str, impl_type: str, code_loc: int = 0) -> ImplementationResult:
        """Load a benchmark result file"""
        # Parse CSV from benchmark harness
        with open(result_file, 'r') as f:
            reader = csv.DictReader(f)

            # Aggregate results across all query types
            total_requests = 0
            p50_weighted = 0
            p95_weighted = 0
            p99_weighted = 0
            mean_weighted = 0
            total_time = 0

            for row in reader:
                if 'total_requests' in row:
                    count = int(row['total_requests'])
                    total_requests += count
                    time_sec = float(row.get('total_time_sec', 1.0))
                    total_time += time_sec

                    p50_weighted += float(row.get('p50_ms', 0)) * count
                    p95_weighted += float(row.get('p95_ms', 0)) * count
                    p99_weighted += float(row.get('p99_ms', 0)) * count
                    mean_weighted += float(row.get('mean_ms', 0)) * count

        if total_requests == 0:
            raise ValueError(f"No valid results in {result_file}")

        p50_ms = p50_weighted / total_requests
        p95_ms = p95_weighted / total_requests
        p99_ms = p99_weighted / total_requests
        mean_ms = mean_weighted / total_requests
        throughput = total_requests / total_time if total_time > 0 else 0

        result = ImplementationResult(
            database=database,
            implementation=implementation,
            language=language,
            type=impl_type,
            p50_latency_ms=p50_ms,
            p95_latency_ms=p95_ms,
            p99_latency_ms=p99_ms,
            mean_latency_ms=mean_ms,
            throughput_qps=throughput,
            code_loc=code_loc
        )

        self.results.append(result)
        return result

    def compare_all(self):
        """Compare all implementations to their respective baselines"""
        # Group by database
        by_database = {}
        for result in self.results:
            if result.database not in by_database:
                by_database[result.database] = []
            by_database[result.database].append(result)

        print(f"\n{'='*100}")
        print("ORM/OGM OVERHEAD ANALYSIS")
        print(f"{'='*100}\n")

        for database, implementations in sorted(by_database.items()):
            # Find baseline (raw driver)
            baseline = next((impl for impl in implementations if impl.type == 'raw'), None)
            if not baseline:
                print(f"⚠ Warning: No baseline found for {database}")
                continue

            print(f"\n{database.upper()}")
            print(f"{'-'*100}")
            print(f"{'Implementation':<25} {'Type':<10} {'p99 Latency':<15} {'Overhead':<12} "
                  f"{'Throughput':<15} {'Change':<10}")
            print(f"{'-'*100}")

            # Sort: baseline first, then by overhead
            implementations_sorted = sorted(implementations,
                                          key=lambda x: (x.type != 'raw', x.p99_latency_ms))

            for impl in implementations_sorted:
                if impl == baseline:
                    # Baseline
                    print(f"{impl.implementation:<25} {impl.type:<10} {impl.p99_latency_ms:>10.2f} ms  "
                          f"{'(baseline)':<12} {impl.throughput_qps:>10.1f} req/s  {'—':<10}")
                else:
                    # Calculate overhead
                    overhead = impl.overhead_vs_baseline(baseline)
                    p99_overhead = overhead['p99_overhead_pct']
                    throughput_change = overhead['throughput_change_pct']

                    # Symbols
                    overhead_symbol = '↑' if p99_overhead > 5 else '≈' if p99_overhead > -5 else '↓'
                    throughput_symbol = '↓' if throughput_change < -5 else '≈' if throughput_change < 5 else '↑'

                    print(f"{impl.implementation:<25} {impl.type:<10} {impl.p99_latency_ms:>10.2f} ms  "
                          f"{p99_overhead:>+9.1f}% {overhead_symbol} {impl.throughput_qps:>10.1f} req/s  "
                          f"{throughput_change:>+8.1f}% {throughput_symbol}")

            print()

        # Summary recommendations
        self._print_recommendations(by_database)

    def _print_recommendations(self, by_database: Dict[str, List[ImplementationResult]]):
        """Print recommendations based on overhead analysis"""
        print(f"\n{'='*100}")
        print("RECOMMENDATIONS")
        print(f"{'='*100}\n")

        for database, implementations in sorted(by_database.items()):
            baseline = next((impl for impl in implementations if impl.type == 'raw'), None)
            if not baseline:
                continue

            print(f"{database.upper()}:")

            for impl in implementations:
                if impl == baseline:
                    continue

                overhead = impl.overhead_vs_baseline(baseline)
                p99_overhead = overhead['p99_overhead_pct']

                if p99_overhead < 10:
                    recommendation = "✓ ACCEPTABLE for production"
                    reason = "Minimal overhead (<10%)"
                elif p99_overhead < 25:
                    recommendation = "⚠ CONDITIONAL - acceptable if developer productivity gain is significant"
                    reason = "Moderate overhead (10-25%)"
                else:
                    recommendation = "✗ NOT RECOMMENDED for critical paths"
                    reason = f"High overhead (>{25}%)"

                print(f"  {impl.implementation}:")
                print(f"    {recommendation}")
                print(f"    Reason: {reason} (p99 overhead: {p99_overhead:+.1f}%)")
                print()

        # General guidelines
        print("\nGENERAL GUIDELINES:")
        print("  • Overhead < 10%:   ✓ Acceptable for all use cases")
        print("  • Overhead 10-25%:  ⚠ Acceptable for non-critical paths")
        print("  • Overhead > 25%:   ✗ Use raw drivers for critical paths")
        print()

    def export_csv(self, output_file: Path):
        """Export comparison results to CSV"""
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Database', 'Implementation', 'Language', 'Type',
                'p50 (ms)', 'p95 (ms)', 'p99 (ms)', 'Mean (ms)',
                'Throughput (req/s)', 'Code LOC'
            ])

            for result in sorted(self.results, key=lambda x: (x.database, x.type != 'raw', x.p99_latency_ms)):
                writer.writerow([
                    result.database,
                    result.implementation,
                    result.language,
                    result.type,
                    f"{result.p50_latency_ms:.2f}",
                    f"{result.p95_latency_ms:.2f}",
                    f"{result.p99_latency_ms:.2f}",
                    f"{result.mean_latency_ms:.2f}",
                    f"{result.throughput_qps:.1f}",
                    result.code_loc
                ])

        print(f"Results exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Compare ORM overhead")
    parser.add_argument("--export-csv", type=Path,
                       help="Export results to CSV file")

    args = parser.parse_args()

    analyzer = ORMOverheadAnalyzer()

    # Example: Load results
    # TODO: Update with actual result files when available

    print("\n" + "="*100)
    print("ORM Overhead Analysis - Configuration")
    print("="*100)
    print("\nTo use this tool, you need benchmark results from different implementations:")
    print("\n1. Run benchmarks for each implementation:")
    print("   - Rust + raw drivers (baseline)")
    print("   - Rust + SQLx (PostgreSQL)")
    print("   - Rust + Diesel (PostgreSQL)")
    print("   - Python + SQLAlchemy (PostgreSQL)")
    print("   - Java + Neo4j OGM")
    print("   - Python + Neomodel")
    print("\n2. Place result CSV files in: analysis/phase-a-optimization/orm-overhead/results/")
    print("\n3. Update this script to load your result files:")
    print("\nExample:")
    print('  analyzer.load_result(')
    print('      result_file=Path("results/postgres-raw.csv"),')
    print('      database="postgresql",')
    print('      implementation="tokio-postgres",')
    print('      language="rust",')
    print('      impl_type="raw",')
    print('      code_loc=150')
    print('  )')
    print("\n4. Uncomment the analyzer.compare_all() call below")
    print("\n" + "="*100 + "\n")

    # Example usage (uncomment when you have results):
    """
    # PostgreSQL
    analyzer.load_result(
        result_file=Path("results/postgres-raw.csv"),
        database="postgresql",
        implementation="tokio-postgres",
        language="rust",
        impl_type="raw",
        code_loc=150
    )

    analyzer.load_result(
        result_file=Path("results/postgres-sqlx.csv"),
        database="postgresql",
        implementation="SQLx",
        language="rust",
        impl_type="orm",
        code_loc=120
    )

    analyzer.load_result(
        result_file=Path("results/postgres-diesel.csv"),
        database="postgresql",
        implementation="Diesel",
        language="rust",
        impl_type="orm",
        code_loc=200
    )

    # Neo4j
    analyzer.load_result(
        result_file=Path("results/neo4j-raw.csv"),
        database="neo4j",
        implementation="neo4rs",
        language="rust",
        impl_type="raw",
        code_loc=130
    )

    analyzer.load_result(
        result_file=Path("results/neo4j-ogm.csv"),
        database="neo4j",
        implementation="Neo4j OGM",
        language="java",
        impl_type="ogm",
        code_loc=250
    )

    # Compare all
    analyzer.compare_all()

    # Export if requested
    if args.export_csv:
        analyzer.export_csv(args.export_csv)
    """


if __name__ == "__main__":
    main()
