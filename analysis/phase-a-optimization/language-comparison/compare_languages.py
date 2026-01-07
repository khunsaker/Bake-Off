#!/usr/bin/env python3
"""
Language Performance Comparison Tool
Shark Bake-Off: Phase A Optimization

Compares performance of different language implementations.
"""

import argparse
import json
import csv
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict
import sys

@dataclass
class LanguageResult:
    """Result from a language implementation"""
    language: str
    runtime: str  # "native", "jvm", "interpreted"
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    p999_latency_ms: float
    mean_latency_ms: float
    throughput_qps: float
    memory_mb: int = 0  # Peak memory usage (manual measurement)
    startup_time_sec: float = 0.0  # Time to first request
    code_loc: int = 0  # Lines of code
    dev_time_days: float = 0.0  # Estimated development time

    def performance_vs_baseline(self, baseline: 'LanguageResult') -> Dict[str, float]:
        """Calculate performance metrics compared to baseline"""
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

    def overall_score(self, baseline: 'LanguageResult') -> float:
        """Calculate overall score (0-100) weighted by multiple factors"""
        # Performance score (50% weight)
        perf_vs_baseline = self.performance_vs_baseline(baseline)
        p99_overhead = perf_vs_baseline['p99_overhead_pct']

        if p99_overhead <= 0:
            perf_score = 100  # Better than baseline
        elif p99_overhead < 20:
            perf_score = 90 - (p99_overhead * 2)  # 90-50
        elif p99_overhead < 50:
            perf_score = 50 - ((p99_overhead - 20) * 1)  # 50-20
        else:
            perf_score = max(0, 20 - ((p99_overhead - 50) * 0.5))  # 20-0

        # Development speed score (30% weight)
        if self.dev_time_days == 0:
            dev_score = 50  # Unknown
        else:
            # Assume 1 day = 100 points, 5+ days = 0 points
            dev_score = max(0, min(100, 100 - (self.dev_time_days - 1) * 25))

        # Code maintainability score (20% weight)
        # Lower LOC = better (simpler to maintain)
        if self.code_loc == 0:
            maint_score = 50
        elif baseline.code_loc == 0:
            maint_score = 50
        else:
            loc_ratio = self.code_loc / baseline.code_loc
            if loc_ratio <= 0.8:
                maint_score = 100  # Much simpler
            elif loc_ratio <= 1.0:
                maint_score = 80
            elif loc_ratio <= 1.2:
                maint_score = 60
            else:
                maint_score = max(0, 60 - (loc_ratio - 1.2) * 100)

        # Weighted overall score
        overall = (perf_score * 0.5) + (dev_score * 0.3) + (maint_score * 0.2)
        return overall


class LanguageComparator:
    """Compares language implementations"""

    def __init__(self):
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        self.results: List[LanguageResult] = []

    def load_result(self, result_file: Path, language: str, runtime: str,
                   memory_mb: int = 0, startup_time_sec: float = 0.0,
                   code_loc: int = 0, dev_time_days: float = 0.0) -> LanguageResult:
        """Load a benchmark result file"""
        # Parse CSV from benchmark harness
        with open(result_file, 'r') as f:
            reader = csv.DictReader(f)

            # Aggregate results
            total_requests = 0
            p50_weighted = 0
            p95_weighted = 0
            p99_weighted = 0
            p999_weighted = 0
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
                    p999_weighted += float(row.get('p999_ms', 0)) * count
                    mean_weighted += float(row.get('mean_ms', 0)) * count

        if total_requests == 0:
            raise ValueError(f"No valid results in {result_file}")

        result = LanguageResult(
            language=language,
            runtime=runtime,
            p50_latency_ms=p50_weighted / total_requests,
            p95_latency_ms=p95_weighted / total_requests,
            p99_latency_ms=p99_weighted / total_requests,
            p999_latency_ms=p999_weighted / total_requests,
            mean_latency_ms=mean_weighted / total_requests,
            throughput_qps=total_requests / total_time if total_time > 0 else 0,
            memory_mb=memory_mb,
            startup_time_sec=startup_time_sec,
            code_loc=code_loc,
            dev_time_days=dev_time_days
        )

        self.results.append(result)
        return result

    def compare_all(self):
        """Compare all language implementations"""
        if not self.results:
            print("No results loaded. Please load benchmark results first.")
            return

        # Sort by p99 latency (best first)
        sorted_results = sorted(self.results, key=lambda x: x.p99_latency_ms)
        baseline = sorted_results[0]  # Best performer is baseline

        print(f"\n{'='*120}")
        print("LANGUAGE PERFORMANCE COMPARISON")
        print(f"{'='*120}\n")

        # Performance comparison
        print("PERFORMANCE METRICS")
        print(f"{'-'*120}")
        print(f"{'Language':<12} {'Runtime':<15} {'p50':<12} {'p95':<12} {'p99':<12} "
              f"{'vs Best':<12} {'Throughput':<15} {'vs Best':<10}")
        print(f"{'-'*120}")

        for result in sorted_results:
            if result == baseline:
                print(f"{result.language:<12} {result.runtime:<15} "
                      f"{result.p50_latency_ms:>8.2f} ms  {result.p95_latency_ms:>8.2f} ms  "
                      f"{result.p99_latency_ms:>8.2f} ms  {'(best)':<12} "
                      f"{result.throughput_qps:>10.1f} req/s  {'—':<10}")
            else:
                perf = result.performance_vs_baseline(baseline)
                p99_overhead = perf['p99_overhead_pct']
                throughput_change = perf['throughput_change_pct']

                overhead_symbol = '↑' if p99_overhead > 5 else '≈'
                throughput_symbol = '↓' if throughput_change < -5 else '≈'

                print(f"{result.language:<12} {result.runtime:<15} "
                      f"{result.p50_latency_ms:>8.2f} ms  {result.p95_latency_ms:>8.2f} ms  "
                      f"{result.p99_latency_ms:>8.2f} ms  {p99_overhead:>+9.1f}% {overhead_symbol} "
                      f"{result.throughput_qps:>10.1f} req/s  {throughput_change:>+8.1f}% {throughput_symbol}")

        # Resource usage
        print(f"\n\nRESOURCE USAGE")
        print(f"{'-'*120}")
        print(f"{'Language':<12} {'Memory (MB)':<15} {'Startup Time':<15} "
              f"{'Code LOC':<12} {'Dev Time (days)':<18}")
        print(f"{'-'*120}")

        for result in sorted_results:
            memory_str = f"{result.memory_mb} MB" if result.memory_mb > 0 else "—"
            startup_str = f"{result.startup_time_sec:.2f}s" if result.startup_time_sec > 0 else "—"
            loc_str = str(result.code_loc) if result.code_loc > 0 else "—"
            dev_str = f"{result.dev_time_days:.1f}" if result.dev_time_days > 0 else "—"

            print(f"{result.language:<12} {memory_str:<15} {startup_str:<15} "
                  f"{loc_str:<12} {dev_str:<18}")

        # Overall scores
        print(f"\n\nOVERALL SCORES (weighted)")
        print(f"{'-'*120}")
        print(f"{'Language':<12} {'Performance':<15} {'Dev Speed':<15} "
              f"{'Maintainability':<18} {'Overall':<12} {'Grade':<8}")
        print(f"{'-'*120}")

        for result in sorted_results:
            overall = result.overall_score(baseline)
            grade = self._score_to_grade(overall)

            # Component scores (simplified display)
            perf = result.performance_vs_baseline(baseline)
            p99_overhead = perf['p99_overhead_pct']

            if p99_overhead <= 0:
                perf_display = "Excellent"
            elif p99_overhead < 20:
                perf_display = "Very Good"
            elif p99_overhead < 50:
                perf_display = "Good"
            else:
                perf_display = "Fair"

            dev_display = self._dev_time_to_rating(result.dev_time_days)
            maint_display = self._loc_to_rating(result.code_loc, baseline.code_loc)

            print(f"{result.language:<12} {perf_display:<15} {dev_display:<15} "
                  f"{maint_display:<18} {overall:>7.1f}/100  {grade:<8}")

        # Recommendations
        self._print_recommendations(sorted_results, baseline)

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        else:
            return "C-"

    def _dev_time_to_rating(self, days: float) -> str:
        if days == 0:
            return "—"
        elif days <= 1.5:
            return "Excellent"
        elif days <= 2.5:
            return "Very Good"
        elif days <= 3.5:
            return "Good"
        else:
            return "Fair"

    def _loc_to_rating(self, loc: int, baseline_loc: int) -> str:
        if loc == 0 or baseline_loc == 0:
            return "—"

        ratio = loc / baseline_loc
        if ratio <= 0.7:
            return "Excellent"
        elif ratio <= 0.9:
            return "Very Good"
        elif ratio <= 1.1:
            return "Good"
        else:
            return "Fair"

    def _print_recommendations(self, sorted_results: List[LanguageResult],
                              baseline: LanguageResult):
        """Print recommendations for each language"""
        print(f"\n\n{'='*120}")
        print("RECOMMENDATIONS")
        print(f"{'='*120}\n")

        for result in sorted_results:
            perf = result.performance_vs_baseline(baseline)
            p99_overhead = perf['p99_overhead_pct']

            print(f"{result.language.upper()}:")

            if result == baseline:
                print(f"  ✓ BEST PERFORMANCE - Recommended for production critical paths")
                print(f"  Use for: Real-time query API, high-throughput services")
            elif p99_overhead < 15:
                print(f"  ✓ ACCEPTABLE - Good alternative to {baseline.language}")
                print(f"  Use for: General-purpose services, when {baseline.language} expertise limited")
            elif p99_overhead < 30:
                print(f"  ⚠ CONDITIONAL - Acceptable for non-critical paths")
                print(f"  Use for: Admin interfaces, batch jobs, internal tools")
            else:
                print(f"  ✗ NOT RECOMMENDED for critical paths")
                print(f"  Use for: Prototyping, analytics, data science workflows")

            print()

        # Overall recommendation
        print("\nFINAL RECOMMENDATION:")
        best = sorted_results[0]
        print(f"  Primary: {best.language} - Best performance ({best.p99_latency_ms:.2f}ms p99)")

        # Find best alternative
        if len(sorted_results) > 1:
            for alt in sorted_results[1:]:
                perf = alt.performance_vs_baseline(best)
                if perf['p99_overhead_pct'] < 20:
                    print(f"  Alternative: {alt.language} - Good balance of performance and productivity")
                    break

        print()

    def export_csv(self, output_file: Path):
        """Export comparison results to CSV"""
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Language', 'Runtime', 'p50 (ms)', 'p95 (ms)', 'p99 (ms)', 'p99.9 (ms)',
                'Mean (ms)', 'Throughput (req/s)', 'Memory (MB)', 'Startup (s)',
                'Code LOC', 'Dev Time (days)'
            ])

            for result in sorted(self.results, key=lambda x: x.p99_latency_ms):
                writer.writerow([
                    result.language,
                    result.runtime,
                    f"{result.p50_latency_ms:.2f}",
                    f"{result.p95_latency_ms:.2f}",
                    f"{result.p99_latency_ms:.2f}",
                    f"{result.p999_latency_ms:.2f}",
                    f"{result.mean_latency_ms:.2f}",
                    f"{result.throughput_qps:.1f}",
                    result.memory_mb,
                    f"{result.startup_time_sec:.2f}",
                    result.code_loc,
                    f"{result.dev_time_days:.1f}"
                ])

        print(f"Results exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Compare language implementations")
    parser.add_argument("--export-csv", type=Path,
                       help="Export results to CSV file")

    args = parser.parse_args()

    comparator = LanguageComparator()

    print("\n" + "="*120)
    print("Language Performance Comparison - Configuration")
    print("="*120)
    print("\nTo use this tool, you need benchmark results from different language implementations:")
    print("\n1. Implement API in each language (Rust, Go, Java, Python)")
    print("2. Run benchmarks for each implementation")
    print("3. Measure resource usage (memory, startup time)")
    print("4. Count lines of code and estimate development time")
    print("5. Update this script to load your results")
    print("\nExample:")
    print('  comparator.load_result(')
    print('      result_file=Path("results/rust.csv"),')
    print('      language="Rust",')
    print('      runtime="native",')
    print('      memory_mb=50,')
    print('      startup_time_sec=0.1,')
    print('      code_loc=1500,')
    print('      dev_time_days=4.0')
    print('  )')
    print("\n" + "="*120 + "\n")

    # Example usage (uncomment when you have results):
    """
    # Load Rust results (baseline)
    comparator.load_result(
        result_file=Path("results/rust.csv"),
        language="Rust",
        runtime="native",
        memory_mb=50,
        startup_time_sec=0.1,
        code_loc=1500,
        dev_time_days=4.0
    )

    # Load Go results
    comparator.load_result(
        result_file=Path("results/go.csv"),
        language="Go",
        runtime="native",
        memory_mb=80,
        startup_time_sec=0.2,
        code_loc=1200,
        dev_time_days=2.5
    )

    # Load Java results
    comparator.load_result(
        result_file=Path("results/java.csv"),
        language="Java",
        runtime="jvm",
        memory_mb=250,
        startup_time_sec=3.0,
        code_loc=1800,
        dev_time_days=3.5
    )

    # Load Python results
    comparator.load_result(
        result_file=Path("results/python.csv"),
        language="Python",
        runtime="interpreted",
        memory_mb=120,
        startup_time_sec=1.0,
        code_loc=800,
        dev_time_days=1.5
    )

    # Compare all
    comparator.compare_all()

    # Export if requested
    if args.export_csv:
        comparator.export_csv(args.export_csv)
    """


if __name__ == "__main__":
    main()
