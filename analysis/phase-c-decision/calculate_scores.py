#!/usr/bin/env python3
"""
Final Scoring Calculator
Shark Bake-Off: Phase C Decision

Calculates weighted scores for final database decision.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class ThresholdStatus(Enum):
    PASS = "PASS"
    CONDITIONAL_PASS = "CONDITIONAL_PASS"
    FAIL = "FAIL"

@dataclass
class PerformanceScores:
    """Performance dimension scores"""
    database: str
    p99_latency_ms: float
    throughput_qps: float
    max_concurrency: int
    latency_score: float  # /30
    throughput_score: float  # /15
    scalability_score: float  # /15
    total_performance: float  # /60

@dataclass
class CurationScores:
    """Curation dimension scores"""
    database: str
    self_service_operations: int  # out of 6
    visualization_rating: float  # out of 5
    self_service_score: float  # /10
    visualization_score: float  # /10
    total_curation: float  # /20

@dataclass
class OperationalScores:
    """Operational dimension scores"""
    database: str
    resource_efficiency_score: float  # /5
    stability_score: float  # /5
    config_complexity_score: float  # /5
    ecosystem_score: float  # /5
    total_operational: float  # /20

@dataclass
class FinalScore:
    """Final consolidated score"""
    database: str
    performance: PerformanceScores
    curation: CurationScores
    operational: OperationalScores
    total_score: float  # /100
    rank: int
    threshold_status: ThresholdStatus
    recommendation: str


class ScoreCalculator:
    """Calculates final weighted scores"""

    # Scoring thresholds (from plan)
    THRESHOLDS = {
        'identifier_lookup_p99': 100,  # ms
        'two_hop_p99': 300,  # ms
        'three_hop_p99': 500,  # ms
    }

    def __init__(self):
        self.databases: List[str] = []
        self.raw_results: Dict = {}
        self.performance_scores: Dict[str, PerformanceScores] = {}
        self.curation_scores: Dict[str, CurationScores] = {}
        self.operational_scores: Dict[str, OperationalScores] = {}
        self.final_scores: Dict[str, FinalScore] = {}

    def load_consolidated_results(self, results_file: Path):
        """Load consolidated results from all phases"""
        with open(results_file, 'r') as f:
            self.raw_results = json.load(f)

        self.databases = list(self.raw_results.keys())
        print(f"Loaded results for: {', '.join(self.databases)}\n")

    def calculate_performance_scores(self):
        """Calculate performance dimension scores (60 points max)"""
        print("="*80)
        print("CALCULATING PERFORMANCE SCORES (60 points max)")
        print("="*80 + "\n")

        # Extract best values for normalization
        best_p99 = min(self.raw_results[db]['performance']['best_p99_ms']
                      for db in self.databases)
        best_throughput = max(self.raw_results[db]['performance']['best_throughput_qps']
                             for db in self.databases)

        for database in self.databases:
            perf = self.raw_results[database]['performance']

            # Latency score (30 points) - lower is better
            p99_ms = perf['best_p99_ms']
            latency_score = 30 * (best_p99 / p99_ms)

            # Throughput score (15 points) - higher is better
            throughput_qps = perf['best_throughput_qps']
            throughput_score = 15 * (throughput_qps / best_throughput)

            # Scalability score (15 points) - based on max concurrency
            max_concurrency = perf.get('max_concurrency', 20)
            if max_concurrency >= 100:
                scalability_score = 15
            elif max_concurrency >= 50:
                scalability_score = 12
            elif max_concurrency >= 20:
                scalability_score = 9
            else:
                scalability_score = 6

            score = PerformanceScores(
                database=database,
                p99_latency_ms=p99_ms,
                throughput_qps=throughput_qps,
                max_concurrency=max_concurrency,
                latency_score=latency_score,
                throughput_score=throughput_score,
                scalability_score=scalability_score,
                total_performance=latency_score + throughput_score + scalability_score
            )

            self.performance_scores[database] = score

            print(f"{database.upper()}:")
            print(f"  p99 Latency: {p99_ms:.2f}ms → {latency_score:.1f}/30 points")
            print(f"  Throughput: {throughput_qps:.1f} req/s → {throughput_score:.1f}/15 points")
            print(f"  Scalability: up to {max_concurrency} concurrent → {scalability_score:.1f}/15 points")
            print(f"  TOTAL PERFORMANCE: {score.total_performance:.1f}/60 points\n")

    def calculate_curation_scores(self):
        """Calculate curation dimension scores (20 points max)"""
        print("="*80)
        print("CALCULATING CURATION SCORES (20 points max)")
        print("="*80 + "\n")

        for database in self.databases:
            curation = self.raw_results[database]['curation']

            # Self-service score (10 points)
            self_service_ops = curation['self_service_operations']  # out of 6
            if self_service_ops == 6:
                self_service_score = 10
            elif self_service_ops >= 4:
                self_service_score = 7
            elif self_service_ops == 3:
                self_service_score = 4
            else:
                self_service_score = 0

            # Visualization score (10 points)
            viz_rating = curation['visualization_rating']  # out of 5
            if viz_rating >= 4.5:
                viz_score = 10
            elif viz_rating >= 3.5:
                viz_score = 8
            elif viz_rating >= 2.5:
                viz_score = 5
            else:
                viz_score = 2

            score = CurationScores(
                database=database,
                self_service_operations=self_service_ops,
                visualization_rating=viz_rating,
                self_service_score=self_service_score,
                visualization_score=viz_score,
                total_curation=self_service_score + viz_score
            )

            self.curation_scores[database] = score

            print(f"{database.upper()}:")
            print(f"  Self-Service: {self_service_ops}/6 operations → {self_service_score:.1f}/10 points")
            print(f"  Visualization: {viz_rating:.1f}/5 rating → {viz_score:.1f}/10 points")
            print(f"  TOTAL CURATION: {score.total_curation:.1f}/20 points\n")

    def calculate_operational_scores(self):
        """Calculate operational dimension scores (20 points max)"""
        print("="*80)
        print("CALCULATING OPERATIONAL SCORES (20 points max)")
        print("="*80 + "\n")

        for database in self.databases:
            operational = self.raw_results[database]['operational']

            # Resource efficiency (5 points)
            memory_mb = operational.get('peak_memory_mb', 100)
            if memory_mb < 100:
                resource_score = 5
            elif memory_mb < 200:
                resource_score = 3
            else:
                resource_score = 1

            # Stability (5 points)
            error_rate = operational.get('error_rate_pct', 0)
            if error_rate == 0:
                stability_score = 5
            elif error_rate < 1:
                stability_score = 3
            else:
                stability_score = 0

            # Configuration complexity (5 points)
            config_params = operational.get('config_parameters', 10)
            if config_params < 10:
                config_score = 5
            elif config_params < 20:
                config_score = 3
            else:
                config_score = 1

            # Ecosystem maturity (5 points)
            # Hard-coded based on known maturity
            ecosystem_scores = {
                'postgresql': 5,  # Very mature
                'neo4j': 4,  # Mature
                'memgraph': 3  # Emerging
            }
            ecosystem_score = ecosystem_scores.get(database.lower(), 3)

            score = OperationalScores(
                database=database,
                resource_efficiency_score=resource_score,
                stability_score=stability_score,
                config_complexity_score=config_score,
                ecosystem_score=ecosystem_score,
                total_operational=resource_score + stability_score + config_score + ecosystem_score
            )

            self.operational_scores[database] = score

            print(f"{database.upper()}:")
            print(f"  Resource Efficiency: {memory_mb}MB peak → {resource_score:.1f}/5 points")
            print(f"  Stability: {error_rate:.2f}% errors → {stability_score:.1f}/5 points")
            print(f"  Config Complexity: {config_params} params → {config_score:.1f}/5 points")
            print(f"  Ecosystem Maturity: → {ecosystem_score:.1f}/5 points")
            print(f"  TOTAL OPERATIONAL: {score.total_operational:.1f}/20 points\n")

    def assess_thresholds(self, database: str) -> ThresholdStatus:
        """Assess threshold compliance for a database"""
        perf = self.raw_results[database]['performance']

        # Get query-specific p99 values
        identifier_p99 = perf.get('identifier_lookup_p99', perf['best_p99_ms'])
        two_hop_p99 = perf.get('two_hop_p99', perf['best_p99_ms'] * 1.5)
        three_hop_p99 = perf.get('three_hop_p99', perf['best_p99_ms'] * 2.5)

        # Check thresholds
        identifier_pass = identifier_p99 <= self.THRESHOLDS['identifier_lookup_p99']
        two_hop_pass = two_hop_p99 <= self.THRESHOLDS['two_hop_p99']
        three_hop_pass = three_hop_p99 <= self.THRESHOLDS['three_hop_p99']

        if identifier_pass and two_hop_pass and three_hop_pass:
            return ThresholdStatus.PASS
        elif three_hop_p99 <= self.THRESHOLDS['three_hop_p99'] * 1.2:
            # Within 20% of threshold - conditional pass
            return ThresholdStatus.CONDITIONAL_PASS
        else:
            return ThresholdStatus.FAIL

    def calculate_final_scores(self):
        """Calculate final consolidated scores and rank databases"""
        print("="*80)
        print("FINAL SCORES")
        print("="*80 + "\n")

        for database in self.databases:
            perf = self.performance_scores[database]
            curation = self.curation_scores[database]
            operational = self.operational_scores[database]

            total_score = (
                perf.total_performance +
                curation.total_curation +
                operational.total_operational
            )

            threshold_status = self.assess_thresholds(database)

            final = FinalScore(
                database=database,
                performance=perf,
                curation=curation,
                operational=operational,
                total_score=total_score,
                rank=0,  # Will be set after sorting
                threshold_status=threshold_status,
                recommendation=""  # Will be set based on rank and status
            )

            self.final_scores[database] = final

        # Rank databases
        sorted_dbs = sorted(
            self.final_scores.items(),
            key=lambda x: (
                x[1].threshold_status != ThresholdStatus.FAIL,  # PASS/CONDITIONAL first
                x[1].total_score
            ),
            reverse=True
        )

        for rank, (database, score) in enumerate(sorted_dbs, 1):
            score.rank = rank

            # Set recommendation
            if rank == 1:
                if score.threshold_status == ThresholdStatus.PASS:
                    score.recommendation = "RECOMMENDED - Winner, meets all thresholds"
                elif score.threshold_status == ThresholdStatus.CONDITIONAL_PASS:
                    score.recommendation = "RECOMMENDED - Winner, requires caching/optimization"
                else:
                    score.recommendation = "CONDITIONAL - Winner but fails thresholds, mitigation required"
            elif rank == 2:
                score.recommendation = "ALTERNATIVE - Second choice"
            else:
                score.recommendation = "NOT RECOMMENDED - Third choice"

        # Print summary
        self._print_final_summary()

    def _print_final_summary(self):
        """Print final score summary"""
        print(f"{'Database':<15} {'Performance':<15} {'Curation':<12} {'Operational':<12} {'TOTAL':<10} {'Threshold':<18} {'Rank':<6}")
        print("-"*100)

        for database in sorted(self.final_scores.keys(), key=lambda x: self.final_scores[x].rank):
            score = self.final_scores[database]
            print(f"{database:<15} "
                  f"{score.performance.total_performance:>7.1f}/60     "
                  f"{score.curation.total_curation:>6.1f}/20   "
                  f"{score.operational.total_operational:>6.1f}/20    "
                  f"{score.total_score:>7.1f}/100  "
                  f"{score.threshold_status.value:<18} "
                  f"#{score.rank}")

        print()

        # Print winner
        winner = min(self.final_scores.values(), key=lambda x: x.rank)
        print(f"\n🏆 WINNER: {winner.database.upper()}")
        print(f"   Total Score: {winner.total_score:.1f}/100")
        print(f"   Threshold Status: {winner.threshold_status.value}")
        print(f"   Recommendation: {winner.recommendation}")
        print()

    def export_scores(self, output_file: Path):
        """Export scores to JSON"""
        data = {
            'final_scores': {
                db: {
                    'total_score': score.total_score,
                    'rank': score.rank,
                    'threshold_status': score.threshold_status.value,
                    'recommendation': score.recommendation,
                    'performance': asdict(score.performance),
                    'curation': asdict(score.curation),
                    'operational': asdict(score.operational)
                }
                for db, score in self.final_scores.items()
            }
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nScores exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Calculate final database scores")
    parser.add_argument("--input", type=Path, required=True,
                       help="Consolidated results JSON file")
    parser.add_argument("--output", type=Path, default=Path("final_scores.json"),
                       help="Output file for scores")

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        print("\nRun aggregate_all_results.py first to create consolidated results")
        return 1

    calculator = ScoreCalculator()

    try:
        calculator.load_consolidated_results(args.input)
        calculator.calculate_performance_scores()
        calculator.calculate_curation_scores()
        calculator.calculate_operational_scores()
        calculator.calculate_final_scores()
        calculator.export_scores(args.output)

        print("\n✓ Score calculation complete!")
        print("\nNext steps:")
        print(f"  1. Review scores in {args.output}")
        print("  2. Run: python generate_decision.py")

    except Exception as e:
        print(f"\n✗ Error during calculation: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
