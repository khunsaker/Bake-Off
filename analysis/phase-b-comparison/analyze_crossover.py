#!/usr/bin/env python3
"""
Crossover Point Analysis Tool
Shark Bake-Off: Phase B Comparison

Identifies crossover points where one database outperforms another.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import sys

@dataclass
class CrossoverPoint:
    """A crossover point where database preference changes"""
    metric: str  # "workload" or "concurrency"
    threshold: str  # Workload pattern or concurrency level
    winner: str
    runner_up: str
    winner_value: float  # p99 latency
    runner_up_value: float
    margin_pct: float  # Performance margin percentage


class CrossoverAnalyzer:
    """Analyzes crossover points in comparison results"""

    def __init__(self, results_dir: Path):
        self.results_dir = Path(results_dir)
        self.databases: List[str] = []
        self.workload_results: Dict[str, Dict] = {}
        self.concurrency_results: Dict[str, Dict] = {}
        self.crossover_points: List[CrossoverPoint] = []

    def load_results(self):
        """Load all database results"""
        print("Loading results...")

        for db_dir in self.results_dir.iterdir():
            if db_dir.is_dir():
                database = db_dir.name
                self.databases.append(database)

                # Load workload results
                workload_file = db_dir / "workload_summary.json"
                if workload_file.exists():
                    with open(workload_file, 'r') as f:
                        self.workload_results[database] = json.load(f)
                    print(f"  Loaded {database} workload results")

                # Load concurrency results
                concurrency_file = db_dir / "concurrency_summary.json"
                if concurrency_file.exists():
                    with open(concurrency_file, 'r') as f:
                        self.concurrency_results[database] = json.load(f)
                    print(f"  Loaded {database} concurrency results")

        if not self.databases:
            raise ValueError("No results found in " + str(self.results_dir))

        print(f"\nLoaded results for: {', '.join(self.databases)}\n")

    def analyze_workload_crossover(self):
        """Analyze crossover points by workload pattern"""
        print("="*80)
        print("WORKLOAD CROSSOVER ANALYSIS")
        print("="*80 + "\n")

        # Group results by workload pattern
        workload_patterns = set()
        for db_results in self.workload_results.values():
            for result in db_results['results']:
                workload_patterns.add(result['workload_pattern'])

        # Categorize workloads
        lookup_heavy = [w for w in workload_patterns if 'lookup' in w]
        balanced = [w for w in workload_patterns if 'balanced' in w or 'mixed' in w]
        analytics = [w for w in workload_patterns if 'analytics' in w or 'traversal' in w]
        write_heavy = [w for w in workload_patterns if 'write' in w]

        categories = {
            "Lookup-Heavy": sorted(lookup_heavy),
            "Balanced": sorted(balanced),
            "Analytics-Heavy": sorted(analytics),
            "Write-Heavy": sorted(write_heavy)
        }

        for category, workloads in categories.items():
            if not workloads:
                continue

            print(f"\n{category} Workloads:")
            print("-" * 80)
            print(f"{'Pattern':<25} {'Winner':<15} {'p99 (ms)':<12} {'Margin':<10}")
            print("-" * 80)

            for workload in workloads:
                # Get results for this workload from all databases
                db_results = []
                for database in self.databases:
                    if database not in self.workload_results:
                        continue

                    for result in self.workload_results[database]['results']:
                        if result['workload_pattern'] == workload:
                            db_results.append((database, result['p99_ms']))
                            break

                if len(db_results) < 2:
                    continue

                # Sort by p99 (best first)
                db_results.sort(key=lambda x: x[1])
                winner_db, winner_p99 = db_results[0]
                runner_up_db, runner_up_p99 = db_results[1]

                margin_pct = ((runner_up_p99 - winner_p99) / winner_p99) * 100

                print(f"{workload:<25} {winner_db:<15} {winner_p99:>8.2f}    "
                      f"{margin_pct:>6.1f}%")

                # Record crossover point
                self.crossover_points.append(CrossoverPoint(
                    metric="workload",
                    threshold=workload,
                    winner=winner_db,
                    runner_up=runner_up_db,
                    winner_value=winner_p99,
                    runner_up_value=runner_up_p99,
                    margin_pct=margin_pct
                ))

        # Summary by database
        self._print_workload_summary()

    def _print_workload_summary(self):
        """Print summary of which database wins which workload types"""
        print("\n" + "="*80)
        print("WORKLOAD WINNER SUMMARY")
        print("="*80 + "\n")

        # Count wins by database
        wins_by_db = defaultdict(lambda: defaultdict(int))

        for cp in self.crossover_points:
            if cp.metric == "workload":
                # Categorize workload
                if 'lookup' in cp.threshold:
                    category = "Lookup-Heavy"
                elif 'analytics' in cp.threshold or 'traversal' in cp.threshold:
                    category = "Analytics-Heavy"
                elif 'write' in cp.threshold:
                    category = "Write-Heavy"
                else:
                    category = "Balanced"

                wins_by_db[cp.winner][category] += 1

        # Print summary table
        categories = ["Lookup-Heavy", "Balanced", "Analytics-Heavy", "Write-Heavy"]
        print(f"{'Database':<15} " + " ".join(f"{c:<18}" for c in categories) + " Total")
        print("-" * 80)

        for database in sorted(self.databases):
            row = f"{database:<15} "
            total_wins = 0
            for category in categories:
                wins = wins_by_db[database][category]
                total_wins += wins
                row += f"{wins:<18} "
            row += f"{total_wins}"
            print(row)

        print()

    def analyze_concurrency_crossover(self):
        """Analyze crossover points by concurrency level"""
        if not self.concurrency_results:
            print("\nNo concurrency results to analyze")
            return

        print("\n" + "="*80)
        print("CONCURRENCY CROSSOVER ANALYSIS")
        print("="*80 + "\n")

        # Get all concurrency levels tested
        concurrency_levels = set()
        for db_results in self.concurrency_results.values():
            for result in db_results['results']:
                concurrency_levels.add(result['concurrency'])

        print(f"{'Concurrency':<15} {'Winner':<15} {'p99 (ms)':<12} {'Throughput':<15} {'Margin':<10}")
        print("-" * 80)

        for concurrency in sorted(concurrency_levels):
            # Get results for this concurrency from all databases
            db_results = []
            for database in self.databases:
                if database not in self.concurrency_results:
                    continue

                for result in self.concurrency_results[database]['results']:
                    if result['concurrency'] == concurrency:
                        db_results.append((
                            database,
                            result['p99_ms'],
                            result['throughput_qps']
                        ))
                        break

            if len(db_results) < 2:
                continue

            # Sort by p99 (best first)
            db_results.sort(key=lambda x: x[1])
            winner_db, winner_p99, winner_throughput = db_results[0]
            runner_up_db, runner_up_p99, runner_up_throughput = db_results[1]

            margin_pct = ((runner_up_p99 - winner_p99) / winner_p99) * 100

            print(f"{concurrency:<15} {winner_db:<15} {winner_p99:>8.2f}    "
                  f"{winner_throughput:>10.1f} req/s  {margin_pct:>6.1f}%")

        # Identify scalability limits
        self._analyze_scalability_limits()

    def _analyze_scalability_limits(self):
        """Identify at what concurrency each database hits limits"""
        print("\n" + "="*80)
        print("SCALABILITY LIMITS")
        print("="*80 + "\n")

        for database in sorted(self.databases):
            if database not in self.concurrency_results:
                continue

            results = self.concurrency_results[database]['results']
            results_sorted = sorted(results, key=lambda x: x['concurrency'])

            # Find concurrency where throughput stops increasing significantly
            prev_throughput = 0
            plateau_point = None

            for result in results_sorted:
                concurrency = result['concurrency']
                throughput = result['throughput_qps']

                if prev_throughput > 0:
                    increase_pct = ((throughput - prev_throughput) / prev_throughput) * 100
                    if increase_pct < 10:  # Less than 10% increase
                        plateau_point = concurrency
                        break

                prev_throughput = throughput

            if plateau_point:
                print(f"{database}: Throughput plateau at concurrency ~{plateau_point}")
            else:
                print(f"{database}: No plateau detected (scales well)")

        print()

    def identify_overall_winner(self) -> Tuple[str, Dict[str, int]]:
        """Identify overall winner across all tests"""
        print("="*80)
        print("OVERALL WINNER ANALYSIS")
        print("="*80 + "\n")

        # Count total wins
        wins = defaultdict(int)
        for cp in self.crossover_points:
            wins[cp.winner] += 1

        # Print results
        total_tests = len(self.crossover_points)
        print(f"{'Database':<15} {'Wins':<10} {'Win Rate':<10}")
        print("-" * 40)

        sorted_wins = sorted(wins.items(), key=lambda x: x[1], reverse=True)
        for database, win_count in sorted_wins:
            win_rate = (win_count / total_tests * 100) if total_tests > 0 else 0
            print(f"{database:<15} {win_count:<10} {win_rate:>6.1f}%")

        print()

        winner = sorted_wins[0][0] if sorted_wins else None
        return winner, dict(wins)

    def generate_recommendations(self, winner: str, wins: Dict[str, int]):
        """Generate recommendations based on crossover analysis"""
        print("="*80)
        print("RECOMMENDATIONS")
        print("="*80 + "\n")

        # Find what each database is best at
        db_strengths = defaultdict(list)

        for cp in self.crossover_points:
            if cp.metric == "workload":
                db_strengths[cp.winner].append(cp.threshold)

        # Print recommendations
        for database in sorted(self.databases):
            print(f"{database.upper()}:")

            if database == winner:
                print(f"  ✓ RECOMMENDED - Overall winner ({wins.get(database, 0)} test wins)")
            else:
                print(f"  Alternative - {wins.get(database, 0)} test wins")

            # Strengths
            if db_strengths[database]:
                print(f"\n  Strengths:")
                # Categorize
                lookup = [w for w in db_strengths[database] if 'lookup' in w]
                analytics = [w for w in db_strengths[database] if 'analytics' in w or 'traversal' in w]
                balanced = [w for w in db_strengths[database] if 'balanced' in w or 'mixed' in w]

                if lookup:
                    print(f"    - Best for lookup-heavy workloads ({len(lookup)} patterns)")
                if analytics:
                    print(f"    - Best for analytics/traversal workloads ({len(analytics)} patterns)")
                if balanced:
                    print(f"    - Best for balanced workloads ({len(balanced)} patterns)")

            print()

        # Use case recommendations
        print("\nUSE CASE RECOMMENDATIONS:\n")

        # Analyze which database dominates which category
        category_winners = defaultdict(lambda: defaultdict(int))
        for cp in self.crossover_points:
            if cp.metric == "workload":
                if 'lookup' in cp.threshold:
                    category_winners["Lookup-Heavy"][cp.winner] += 1
                elif 'analytics' in cp.threshold or 'traversal' in cp.threshold:
                    category_winners["Analytics-Heavy"][cp.winner] += 1
                elif 'balanced' in cp.threshold or 'mixed' in cp.threshold:
                    category_winners["Balanced"][cp.winner] += 1

        for category, db_wins in category_winners.items():
            if db_wins:
                best_db = max(db_wins.items(), key=lambda x: x[1])[0]
                print(f"{category} workloads → Use {best_db}")

        print()

    def export_report(self, output_file: Path):
        """Export crossover analysis to markdown"""
        with open(output_file, 'w') as f:
            f.write("# Phase B: Crossover Analysis Report\n\n")
            f.write("## Workload Crossover Points\n\n")

            # Group by winner
            by_winner = defaultdict(list)
            for cp in self.crossover_points:
                if cp.metric == "workload":
                    by_winner[cp.winner].append(cp)

            for winner in sorted(by_winner.keys()):
                f.write(f"### {winner.upper()} Wins\n\n")
                f.write("| Workload Pattern | p99 Latency | Margin vs Runner-up |\n")
                f.write("|-----------------|-------------|---------------------|\n")

                for cp in sorted(by_winner[winner], key=lambda x: x.threshold):
                    f.write(f"| {cp.threshold} | {cp.winner_value:.2f} ms | "
                           f"+{cp.margin_pct:.1f}% |\n")

                f.write("\n")

            f.write("\n## Overall Winner\n\n")

            wins = defaultdict(int)
            for cp in self.crossover_points:
                wins[cp.winner] += 1

            sorted_wins = sorted(wins.items(), key=lambda x: x[1], reverse=True)
            if sorted_wins:
                winner, win_count = sorted_wins[0]
                total = len(self.crossover_points)
                win_rate = (win_count / total * 100) if total > 0 else 0

                f.write(f"**Winner: {winner.upper()}**\n\n")
                f.write(f"- Wins: {win_count}/{total} tests ({win_rate:.1f}%)\n")
                f.write(f"- Performance advantage in majority of workload patterns\n\n")

        print(f"\nCrossover analysis exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Analyze crossover points from Phase B comparison")
    parser.add_argument("--results-dir", type=Path,
                       default=Path(__file__).parent / "results",
                       help="Directory containing comparison results")
    parser.add_argument("--export", type=Path,
                       help="Export report to markdown file")

    args = parser.parse_args()

    if not args.results_dir.exists():
        print(f"Error: Results directory not found: {args.results_dir}")
        print("\nRun comparison first:")
        print("  python run_comparison.py")
        sys.exit(1)

    analyzer = CrossoverAnalyzer(args.results_dir)

    try:
        analyzer.load_results()
        analyzer.analyze_workload_crossover()
        analyzer.analyze_concurrency_crossover()

        winner, wins = analyzer.identify_overall_winner()
        if winner:
            analyzer.generate_recommendations(winner, wins)

        if args.export:
            analyzer.export_report(args.export)

        print("\n✓ Crossover analysis complete!")

    except Exception as e:
        print(f"\n✗ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
