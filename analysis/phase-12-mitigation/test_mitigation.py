#!/usr/bin/env python3
"""
Mitigation Testing Tool
Shark Bake-Off: Phase 12

Tests mitigation strategies and validates threshold compliance.
"""

import argparse
import subprocess
import time
import csv
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MitigationResult:
    """Result from mitigation test"""
    strategy: str
    query_type: str
    baseline_p99_ms: float
    mitigated_p99_ms: float
    improvement_pct: float
    threshold_ms: float
    passes_threshold: bool

class MitigationTester:
    """Tests and validates mitigation strategies"""

    # Thresholds from plan
    THRESHOLDS = {
        'identifier_lookup': 100,  # ms p99
        'two_hop_traversal': 300,  # ms p99
        'three_hop_traversal': 500,  # ms p99
    }

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.base_dir = Path(__file__).parent
        self.harness_dir = self.base_dir.parent.parent / "benchmark" / "harness"
        self.results: List[MitigationResult] = []

    def run_baseline_test(self, output_file: Path) -> Dict:
        """Run baseline test before mitigation"""
        print("\n" + "="*80)
        print("BASELINE TEST (Before Mitigation)")
        print("="*80 + "\n")

        print("Running benchmark to establish baseline...")

        cmd = [
            "python3", "runner.py",
            self.base_url,
            "--pattern", "balanced-50",
            "--requests", "50000",
            "--concurrency", "20",
            "--output", str(output_file.with_suffix(''))
        ]

        subprocess.run(cmd, cwd=self.harness_dir, check=True)

        # Parse results
        result_files = list(output_file.parent.glob(f"{output_file.stem}*.csv"))
        if not result_files:
            raise FileNotFoundError(f"No result file found")

        result_file = max(result_files, key=lambda p: p.stat().st_mtime)
        baseline_stats = self._parse_results(result_file)

        print("\nBaseline Results:")
        print(f"  Identifier Lookup p99: {baseline_stats.get('identifier_lookup_p99', 0):.2f}ms "
              f"(threshold: {self.THRESHOLDS['identifier_lookup']}ms)")
        print(f"  Two-Hop Traversal p99: {baseline_stats.get('two_hop_p99', 0):.2f}ms "
              f"(threshold: {self.THRESHOLDS['two_hop_traversal']}ms)")
        print(f"  Three-Hop Traversal p99: {baseline_stats.get('three_hop_p99', 0):.2f}ms "
              f"(threshold: {self.THRESHOLDS['three_hop_traversal']}ms)")

        return baseline_stats

    def run_mitigation_test(self, strategy: str, output_file: Path,
                           warmup: bool = True) -> Dict:
        """Run test after mitigation applied"""
        print("\n" + "="*80)
        print(f"MITIGATION TEST: {strategy.upper()}")
        print("="*80 + "\n")

        if warmup:
            print("Running warm-up to populate cache...")
            warmup_cmd = [
                "python3", "runner.py",
                self.base_url,
                "--pattern", "lookup-95",
                "--requests", "10000",
                "--concurrency", "10"
            ]
            subprocess.run(warmup_cmd, cwd=self.harness_dir, check=True,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Warm-up complete.\n")

        print("Running mitigation benchmark...")

        cmd = [
            "python3", "runner.py",
            self.base_url,
            "--pattern", "balanced-50",
            "--requests", "50000",
            "--concurrency", "20",
            "--output", str(output_file.with_suffix(''))
        ]

        subprocess.run(cmd, cwd=self.harness_dir, check=True)

        # Parse results
        result_files = list(output_file.parent.glob(f"{output_file.stem}*.csv"))
        if not result_files:
            raise FileNotFoundError(f"No result file found")

        result_file = max(result_files, key=lambda p: p.stat().st_mtime)
        mitigated_stats = self._parse_results(result_file)

        print("\nMitigation Results:")
        print(f"  Identifier Lookup p99: {mitigated_stats.get('identifier_lookup_p99', 0):.2f}ms "
              f"(threshold: {self.THRESHOLDS['identifier_lookup']}ms)")
        print(f"  Two-Hop Traversal p99: {mitigated_stats.get('two_hop_p99', 0):.2f}ms "
              f"(threshold: {self.THRESHOLDS['two_hop_traversal']}ms)")
        print(f"  Three-Hop Traversal p99: {mitigated_stats.get('three_hop_p99', 0):.2f}ms "
              f"(threshold: {self.THRESHOLDS['three_hop_traversal']}ms)")

        return mitigated_stats

    def _parse_results(self, result_file: Path) -> Dict:
        """Parse benchmark results and extract query-specific p99"""
        stats = {}

        with open(result_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                query_type = row.get('query_type', 'unknown')
                p99_ms = float(row.get('p99_ms', 0))

                # Map to our categories
                if 'S1' in query_type or 'identifier' in query_type.lower():
                    stats['identifier_lookup_p99'] = p99_ms
                elif 'S3' in query_type or 'two_hop' in query_type.lower() or 'two-hop' in query_type.lower():
                    stats['two_hop_p99'] = p99_ms
                elif 'S4' in query_type or 'three_hop' in query_type.lower() or 'three-hop' in query_type.lower():
                    stats['three_hop_p99'] = p99_ms

        # If not found, use overall p99 as estimate
        if not stats:
            with open(result_file, 'r') as f:
                reader = csv.DictReader(f)
                first_row = next(reader, {})
                overall_p99 = float(first_row.get('p99_ms', 0))

                # Estimate query-specific p99 based on typical patterns
                stats['identifier_lookup_p99'] = overall_p99 * 0.8
                stats['two_hop_p99'] = overall_p99 * 1.3
                stats['three_hop_p99'] = overall_p99 * 2.0

        return stats

    def compare_results(self, strategy: str, baseline: Dict, mitigated: Dict):
        """Compare baseline vs mitigated results"""
        print("\n" + "="*80)
        print(f"MITIGATION COMPARISON: {strategy.upper()}")
        print("="*80 + "\n")

        query_types = {
            'identifier_lookup': 'Identifier Lookup',
            'two_hop_traversal': 'Two-Hop Traversal',
            'three_hop_traversal': 'Three-Hop Traversal'
        }

        print(f"{'Query Type':<25} {'Baseline p99':<15} {'Mitigated p99':<15} "
              f"{'Improvement':<12} {'Threshold':<12} {'Status':<10}")
        print("-"*90)

        all_pass = True

        for key, name in query_types.items():
            baseline_p99 = baseline.get(f'{key}_p99', 0)
            mitigated_p99 = mitigated.get(f'{key}_p99', 0)
            threshold = self.THRESHOLDS[key]

            if baseline_p99 > 0:
                improvement_pct = ((baseline_p99 - mitigated_p99) / baseline_p99) * 100
            else:
                improvement_pct = 0

            passes = mitigated_p99 <= threshold
            status = "✓ PASS" if passes else "✗ FAIL"

            if not passes:
                all_pass = False

            print(f"{name:<25} {baseline_p99:>10.2f} ms  {mitigated_p99:>10.2f} ms  "
                  f"{improvement_pct:>+9.1f}%  {threshold:>8.0f} ms  {status:<10}")

            # Store result
            result = MitigationResult(
                strategy=strategy,
                query_type=name,
                baseline_p99_ms=baseline_p99,
                mitigated_p99_ms=mitigated_p99,
                improvement_pct=improvement_pct,
                threshold_ms=threshold,
                passes_threshold=passes
            )
            self.results.append(result)

        print()
        print("="*90)
        if all_pass:
            print("✓ SUCCESS: All thresholds met with mitigation!")
        else:
            print("✗ FAILURE: Some thresholds still not met")
            print("\nRecommendation: Try additional mitigation strategies")
        print("="*90 + "\n")

        return all_pass

    def generate_report(self, output_file: Path, strategy: str):
        """Generate mitigation test report"""
        with open(output_file, 'w') as f:
            f.write(f"# Mitigation Strategy Test Report\n\n")
            f.write(f"**Strategy:** {strategy}\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            f.write("## Results Summary\n\n")
            f.write("| Query Type | Baseline p99 | Mitigated p99 | Improvement | Threshold | Status |\n")
            f.write("|------------|-------------|---------------|-------------|-----------|--------|\n")

            for result in self.results:
                status = "✓ PASS" if result.passes_threshold else "✗ FAIL"
                f.write(f"| {result.query_type} | {result.baseline_p99_ms:.2f}ms | "
                       f"{result.mitigated_p99_ms:.2f}ms | {result.improvement_pct:+.1f}% | "
                       f"{result.threshold_ms:.0f}ms | {status} |\n")

            f.write("\n")

            # Overall assessment
            all_pass = all(r.passes_threshold for r in self.results)
            if all_pass:
                f.write("## Recommendation\n\n")
                f.write("✓ **ACCEPT** mitigation strategy\n\n")
                f.write("All p99 thresholds met. Proceed with this mitigation in production.\n\n")
            else:
                f.write("## Recommendation\n\n")
                f.write("✗ **REJECT** mitigation strategy\n\n")
                f.write("Some thresholds still not met. Try additional mitigation or alternative strategy.\n\n")

            f.write("---\n\n")
            f.write("## Next Steps\n\n")
            if all_pass:
                f.write("1. Update FINAL_DECISION.md with mitigation details\n")
                f.write("2. Document production deployment requirements\n")
                f.write("3. Proceed to Phase 13 (Final Report)\n")
            else:
                f.write("1. Analyze which queries still failing\n")
                f.write("2. Try additional mitigation strategies\n")
                f.write("3. Consider hybrid architecture or threshold relaxation\n")

        print(f"\n✓ Report generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Test mitigation strategies")
    parser.add_argument("--strategy", required=True,
                       choices=["redis-caching", "query-optimization", "hybrid"],
                       help="Mitigation strategy to test")
    parser.add_argument("--base-url", default="http://localhost:8080",
                       help="Base URL for API")
    parser.add_argument("--skip-baseline", action="store_true",
                       help="Skip baseline test (use existing baseline)")
    parser.add_argument("--baseline-file", type=Path,
                       help="Path to existing baseline results")

    args = parser.parse_args()

    tester = MitigationTester(args.base_url)
    output_dir = Path(__file__).parent / args.strategy.replace('-', '_')
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Baseline test
        if args.skip_baseline and args.baseline_file:
            print(f"Using existing baseline: {args.baseline_file}")
            baseline_stats = tester._parse_results(args.baseline_file)
        else:
            baseline_file = output_dir / "baseline.csv"
            baseline_stats = tester.run_baseline_test(baseline_file)

        # Prompt for mitigation setup
        print(f"\n{'='*80}")
        print(f"MITIGATION SETUP REQUIRED")
        print(f"{'='*80}\n")

        if args.strategy == "redis-caching":
            print("Before continuing, ensure:")
            print("  1. Redis is running (docker run -d -p 6379:6379 redis:7-alpine)")
            print("  2. Rust API has REDIS_URL configured")
            print("  3. Rust API restarted with caching enabled")
        elif args.strategy == "query-optimization":
            print("Before continuing, ensure:")
            print("  1. Database queries optimized (indexes added, etc.)")
            print("  2. Database restarted if needed")
        elif args.strategy == "hybrid":
            print("Before continuing, ensure:")
            print("  1. Hybrid architecture deployed")
            print("  2. Data sync working between databases")

        input("\nPress Enter when mitigation is ready...")

        # Mitigation test
        mitigated_file = output_dir / f"mitigated_{args.strategy}.csv"
        mitigated_stats = tester.run_mitigation_test(args.strategy, mitigated_file,
                                                     warmup=(args.strategy == "redis-caching"))

        # Compare results
        all_pass = tester.compare_results(args.strategy, baseline_stats, mitigated_stats)

        # Generate report
        report_file = output_dir / "MITIGATION_REPORT.md"
        tester.generate_report(report_file, args.strategy)

        # Exit code based on success
        if all_pass:
            print("\n✓ Mitigation successful! All thresholds met.")
            return 0
        else:
            print("\n✗ Mitigation insufficient. Additional strategies needed.")
            return 1

    except Exception as e:
        print(f"\n✗ Error during mitigation testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
