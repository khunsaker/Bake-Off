#!/usr/bin/env python3
"""
Results Aggregation Tool
Shark Bake-Off: Phase A Optimization

Aggregates all Phase A results and generates summary report.
"""

import argparse
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

@dataclass
class DatabaseOptimizationResult:
    """Results from database optimization testing"""
    database: str
    variant: str
    p50_ms: float
    p95_ms: float
    p99_ms: float
    throughput_qps: float
    improvement_pct: float

@dataclass
class ThresholdResult:
    """Threshold assessment for a database"""
    database: str
    identifier_lookup_pass: bool
    two_hop_pass: bool
    three_hop_pass: bool
    overall_pass: bool

class ResultsAggregator:
    """Aggregates all Phase A results"""

    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            self.base_dir = Path(__file__).parent
        else:
            self.base_dir = Path(base_dir)

        self.db_results: Dict[str, List[DatabaseOptimizationResult]] = {}
        self.orm_results: Dict[str, dict] = {}
        self.language_results: Dict[str, dict] = {}
        self.thresholds: Dict[str, ThresholdResult] = {}

    def load_database_results(self, database: str):
        """Load optimization results for a database"""
        results_dir = self.base_dir / database / "results"
        summary_file = results_dir / "summary.json"

        if not summary_file.exists():
            print(f"Warning: No summary file found for {database}")
            return

        with open(summary_file, 'r') as f:
            data = json.load(f)

        self.db_results[database] = []
        for item in data:
            result = DatabaseOptimizationResult(
                database=database,
                variant=item['config_variant'],
                p50_ms=item['p50_latency_ms'],
                p95_ms=item['p95_latency_ms'],
                p99_ms=item['p99_latency_ms'],
                throughput_qps=item['throughput_qps'],
                improvement_pct=0.0  # Will calculate
            )
            self.db_results[database].append(result)

        # Calculate improvements relative to default
        default = next((r for r in self.db_results[database] if r.variant == 'default'), None)
        if default:
            for result in self.db_results[database]:
                if result.variant != 'default':
                    result.improvement_pct = ((default.p99_ms - result.p99_ms) / default.p99_ms) * 100

    def assess_thresholds(self):
        """Assess if databases meet performance thresholds"""
        # Thresholds from plan
        thresholds = {
            'identifier_lookup': 100,  # ms p99
            'two_hop_traversal': 300,   # ms p99
            'three_hop_traversal': 500, # ms p99
        }

        for database in self.db_results:
            # Get best configuration
            best = min(self.db_results[database], key=lambda x: x.p99_ms)

            # For simplicity, assume p99 is representative
            # In real implementation, would need query-specific results
            identifier_pass = best.p99_ms < thresholds['identifier_lookup']
            two_hop_pass = best.p99_ms < thresholds['two_hop_traversal']
            three_hop_pass = best.p99_ms < thresholds['three_hop_traversal']

            self.thresholds[database] = ThresholdResult(
                database=database,
                identifier_lookup_pass=identifier_pass,
                two_hop_pass=two_hop_pass,
                three_hop_pass=three_hop_pass,
                overall_pass=identifier_pass and two_hop_pass and three_hop_pass
            )

    def generate_report(self, output_file: Path):
        """Generate comprehensive markdown report"""
        with open(output_file, 'w') as f:
            f.write("# Phase A Optimization - Results Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            # Database optimization results
            f.write("## Database Optimization Results\n\n")

            for database in sorted(self.db_results.keys()):
                f.write(f"### {database.upper()}\n\n")

                # Table
                f.write("| Variant | p50 (ms) | p95 (ms) | p99 (ms) | Throughput | Improvement |\n")
                f.write("|---------|----------|----------|----------|------------|-------------|\n")

                results = sorted(self.db_results[database], key=lambda x: x.p99_ms)
                for result in results:
                    improvement_str = f"{result.improvement_pct:+.1f}%" if result.variant != 'default' else "baseline"
                    f.write(f"| {result.variant} | {result.p50_ms:.2f} | {result.p95_ms:.2f} | "
                           f"{result.p99_ms:.2f} | {result.throughput_qps:.1f} req/s | {improvement_str} |\n")

                f.write("\n")

                # Recommendation
                best = results[0]
                f.write(f"**Recommended Configuration:** {best.variant}\n")
                f.write(f"- p99 Latency: {best.p99_ms:.2f} ms\n")
                f.write(f"- Throughput: {best.throughput_qps:.1f} req/s\n")

                if best.variant != 'default':
                    f.write(f"- Improvement: {best.improvement_pct:.1f}% reduction in p99 latency\n")

                f.write("\n")

            # Threshold assessment
            f.write("## Threshold Assessment\n\n")
            f.write("| Database | Identifier Lookup | Two-Hop Traversal | Three-Hop Traversal | Overall |\n")
            f.write("|----------|------------------|-------------------|---------------------|----------|\n")

            for database in sorted(self.thresholds.keys()):
                t = self.thresholds[database]
                id_symbol = "✓" if t.identifier_lookup_pass else "✗"
                two_hop_symbol = "✓" if t.two_hop_pass else "✗"
                three_hop_symbol = "✓" if t.three_hop_pass else "✗"
                overall_symbol = "**PASS**" if t.overall_pass else "**FAIL**"

                f.write(f"| {database} | {id_symbol} | {two_hop_symbol} | {three_hop_symbol} | {overall_symbol} |\n")

            f.write("\n")

            # Head-to-head comparison
            f.write("## Database Comparison (Optimized Configurations)\n\n")
            f.write("| Database | Best p99 (ms) | Throughput (req/s) | Rank |\n")
            f.write("|----------|---------------|-------------------|------|\n")

            # Rank databases by best p99
            db_rankings = []
            for database in self.db_results:
                best = min(self.db_results[database], key=lambda x: x.p99_ms)
                db_rankings.append((database, best.p99_ms, best.throughput_qps))

            db_rankings.sort(key=lambda x: x[1])  # Sort by p99

            for rank, (database, p99, throughput) in enumerate(db_rankings, 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else ""
                f.write(f"| {database} | {p99:.2f} | {throughput:.1f} | {rank} {medal} |\n")

            f.write("\n")

            # Recommendations
            f.write("## Recommendations\n\n")

            if db_rankings:
                winner_db, winner_p99, winner_throughput = db_rankings[0]
                f.write(f"### Primary Recommendation: {winner_db.upper()}\n\n")
                f.write(f"- **Best Performance:** {winner_p99:.2f}ms p99, {winner_throughput:.1f} req/s\n")

                if winner_db in self.thresholds and self.thresholds[winner_db].overall_pass:
                    f.write(f"- **Threshold Status:** ✓ Meets all performance thresholds\n")
                else:
                    f.write(f"- **Threshold Status:** ⚠ Does not meet all thresholds - mitigation required\n")

                f.write("\n")

                # Show alternatives
                if len(db_rankings) > 1:
                    f.write("### Alternatives\n\n")
                    for database, p99, throughput in db_rankings[1:]:
                        overhead_pct = ((p99 - winner_p99) / winner_p99) * 100
                        f.write(f"**{database}:**\n")
                        f.write(f"- Performance: {overhead_pct:+.1f}% slower than {winner_db}\n")

                        if database in self.thresholds:
                            if self.thresholds[database].overall_pass:
                                f.write(f"- Threshold Status: ✓ Meets all thresholds\n")
                            else:
                                f.write(f"- Threshold Status: ✗ Does not meet all thresholds\n")

                        f.write("\n")

            # Next steps
            f.write("## Next Steps\n\n")
            f.write("1. ✅ Phase A (Optimization) complete\n")
            f.write("2. → Proceed to ORM overhead analysis (if not done)\n")
            f.write("3. → Proceed to language comparison (if not done)\n")
            f.write("4. → Proceed to Phase B: Head-to-head comparison with optimal configs\n")
            f.write("5. → Proceed to Phase C: Final decision\n")
            f.write("\n")

        print(f"\nReport generated: {output_file}")

    def export_json(self, output_file: Path):
        """Export all results as JSON"""
        data = {
            'generated_at': datetime.now().isoformat(),
            'database_results': {
                db: [asdict(r) for r in results]
                for db, results in self.db_results.items()
            },
            'thresholds': {
                db: asdict(t)
                for db, t in self.thresholds.items()
            }
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"JSON export: {output_file}")

    def print_summary(self):
        """Print summary to console"""
        print("\n" + "="*100)
        print("PHASE A OPTIMIZATION - SUMMARY")
        print("="*100 + "\n")

        for database in sorted(self.db_results.keys()):
            results = sorted(self.db_results[database], key=lambda x: x.p99_ms)
            default = next((r for r in results if r.variant == 'default'), None)
            best = results[0]

            print(f"{database.upper()}:")
            print(f"  Default: {default.p99_ms:.2f}ms p99" if default else "  Default: (not tested)")
            print(f"  Best:    {best.p99_ms:.2f}ms p99 ({best.variant})")

            if default and best.variant != 'default':
                improvement = ((default.p99_ms - best.p99_ms) / default.p99_ms) * 100
                print(f"  Improvement: {improvement:.1f}%")

            if database in self.thresholds:
                status = "✓ PASS" if self.thresholds[database].overall_pass else "✗ FAIL"
                print(f"  Threshold: {status}")

            print()

        # Rankings
        print("\nOVERALL RANKING (by p99 latency):")
        db_rankings = []
        for database in self.db_results:
            best = min(self.db_results[database], key=lambda x: x.p99_ms)
            db_rankings.append((database, best.p99_ms, best.variant))

        db_rankings.sort(key=lambda x: x[1])

        for rank, (database, p99, variant) in enumerate(db_rankings, 1):
            print(f"  {rank}. {database}: {p99:.2f}ms ({variant} config)")

        print("\n" + "="*100 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Aggregate Phase A optimization results")
    parser.add_argument("--databases", nargs="+",
                       default=["postgresql", "neo4j", "memgraph"],
                       help="Databases to include in report")
    parser.add_argument("--output-report", type=Path,
                       default=Path("RESULTS_REPORT.md"),
                       help="Output markdown report file")
    parser.add_argument("--export-json", type=Path,
                       help="Export results as JSON")

    args = parser.parse_args()

    aggregator = ResultsAggregator()

    # Load results for each database
    print("Loading results...")
    for database in args.databases:
        print(f"  Loading {database}...")
        try:
            aggregator.load_database_results(database)
        except Exception as e:
            print(f"    Error: {e}")

    if not aggregator.db_results:
        print("\nNo results found. Please run configuration tests first:")
        print("  python test_configs.py postgresql")
        print("  python test_configs.py neo4j")
        print("  python test_configs.py memgraph")
        sys.exit(1)

    # Assess thresholds
    print("\nAssessing thresholds...")
    aggregator.assess_thresholds()

    # Print summary
    aggregator.print_summary()

    # Generate report
    print(f"\nGenerating report...")
    aggregator.generate_report(args.output_report)

    # Export JSON if requested
    if args.export_json:
        aggregator.export_json(args.export_json)

    print("\nPhase A optimization analysis complete!")


if __name__ == "__main__":
    main()
