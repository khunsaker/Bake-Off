#!/usr/bin/env python3
"""
Decision Document Generator
Shark Bake-Off: Phase C Decision

Generates final decision document from scores.
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict

class DecisionGenerator:
    """Generates final decision documentation"""

    def __init__(self, scores_file: Path):
        self.scores_file = scores_file
        self.scores = {}
        self.winner = None
        self.runner_up = None

    def load_scores(self):
        """Load final scores"""
        with open(self.scores_file, 'r') as f:
            data = json.load(f)
            self.scores = data['final_scores']

        # Identify winner and runner-up
        ranked = sorted(self.scores.items(), key=lambda x: x[1]['rank'])
        self.winner = ranked[0][0]
        if len(ranked) > 1:
            self.runner_up = ranked[1][0]

        print(f"Winner: {self.winner}")
        print(f"Runner-up: {self.runner_up if self.runner_up else 'N/A'}\n")

    def generate_decision_document(self, output_file: Path):
        """Generate comprehensive decision document"""
        winner_data = self.scores[self.winner]

        with open(output_file, 'w') as f:
            self._write_header(f)
            self._write_executive_summary(f, winner_data)
            self._write_scoring_breakdown(f)
            self._write_threshold_assessment(f)
            self._write_trade_off_analysis(f)
            self._write_final_recommendation(f, winner_data)
            self._write_implementation_plan(f)
            self._write_risk_mitigation(f, winner_data)
            self._write_appendix(f)

        print(f"✓ Decision document generated: {output_file}")

    def _write_header(self, f):
        """Write document header"""
        f.write("# Shark Bake-Off: Final Database Decision\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write("**Phase:** C - Final Decision\n")
        f.write("**Status:** FINAL\n\n")
        f.write("---\n\n")

    def _write_executive_summary(self, f, winner_data):
        """Write executive summary"""
        f.write("## Executive Summary\n\n")
        f.write(f"### Selected Database: **{self.winner.upper()}**\n\n")
        f.write(f"**Total Score:** {winner_data['total_score']:.1f}/100 points\n\n")
        f.write(f"**Threshold Status:** {winner_data['threshold_status']}\n\n")
        f.write(f"**Recommendation:** {winner_data['recommendation']}\n\n")

        # Key reasons
        f.write("**Key Selection Factors:**\n\n")

        perf = winner_data['performance']
        curation = winner_data['curation']

        f.write(f"1. **Performance Excellence**\n")
        f.write(f"   - p99 Latency: {perf['p99_latency_ms']:.2f}ms\n")
        f.write(f"   - Throughput: {perf['throughput_qps']:.1f} requests/second\n")
        f.write(f"   - Performance Score: {perf['total_performance']:.1f}/60 points\n\n")

        f.write(f"2. **Curation Capability**\n")
        f.write(f"   - Self-Service: {curation['self_service_operations']}/6 operations\n")
        f.write(f"   - Visualization: {curation['visualization_rating']:.1f}/5 rating\n")
        f.write(f"   - Curation Score: {curation['total_curation']:.1f}/20 points\n\n")

        f.write(f"3. **Operational Readiness**\n")
        operational = winner_data['operational']
        f.write(f"   - Operational Score: {operational['total_operational']:.1f}/20 points\n\n")

        f.write("---\n\n")

    def _write_scoring_breakdown(self, f):
        """Write detailed scoring breakdown"""
        f.write("## Scoring Breakdown\n\n")

        # Overall scores table
        f.write("### Final Scores\n\n")
        f.write("| Database | Performance (/60) | Curation (/20) | Operational (/20) | **Total (/100)** | Rank |\n")
        f.write("|----------|-------------------|----------------|-------------------|------------------|------|\n")

        for database in sorted(self.scores.keys(), key=lambda x: self.scores[x]['rank']):
            data = self.scores[database]
            perf = data['performance']['total_performance']
            curation = data['curation']['total_curation']
            operational = data['operational']['total_operational']
            total = data['total_score']
            rank = data['rank']

            f.write(f"| {database} | {perf:.1f} | {curation:.1f} | {operational:.1f} | "
                   f"**{total:.1f}** | #{rank} |\n")

        f.write("\n")

        # Performance details
        f.write("### Performance Details\n\n")
        f.write("| Database | p99 Latency | Throughput | Max Concurrency | Latency Score | Throughput Score | Scalability Score |\n")
        f.write("|----------|-------------|------------|-----------------|---------------|------------------|-------------------|\n")

        for database in self.scores.keys():
            perf = self.scores[database]['performance']
            f.write(f"| {database} | {perf['p99_latency_ms']:.2f}ms | "
                   f"{perf['throughput_qps']:.1f} req/s | {perf['max_concurrency']} | "
                   f"{perf['latency_score']:.1f}/30 | {perf['throughput_score']:.1f}/15 | "
                   f"{perf['scalability_score']:.1f}/15 |\n")

        f.write("\n")

        # Curation details
        f.write("### Curation Details\n\n")
        f.write("| Database | Self-Service Ops | Visualization Rating | Self-Service Score | Viz Score |\n")
        f.write("|----------|-----------------|---------------------|-------------------|----------|\n")

        for database in self.scores.keys():
            curation = self.scores[database]['curation']
            f.write(f"| {database} | {curation['self_service_operations']}/6 | "
                   f"{curation['visualization_rating']:.1f}/5 | "
                   f"{curation['self_service_score']:.1f}/10 | "
                   f"{curation['visualization_score']:.1f}/10 |\n")

        f.write("\n---\n\n")

    def _write_threshold_assessment(self, f):
        """Write threshold assessment"""
        f.write("## Threshold Assessment\n\n")

        f.write("**Performance Thresholds (from plan):**\n\n")
        f.write("| Query Type | Target p50 | Acceptable p95 | Maximum p99 |\n")
        f.write("|------------|-----------|----------------|-------------|\n")
        f.write("| Identifier Lookup | 10ms | 50ms | **100ms** |\n")
        f.write("| Two-Hop Traversal | 50ms | 150ms | **300ms** |\n")
        f.write("| Three-Hop Traversal | 100ms | 300ms | **500ms** |\n\n")

        f.write("### Results by Database\n\n")
        f.write("| Database | Threshold Status | Notes |\n")
        f.write("|----------|-----------------|-------|\n")

        for database in self.scores.keys():
            status = self.scores[database]['threshold_status']
            if status == "PASS":
                note = "✓ Meets all p99 thresholds"
            elif status == "CONDITIONAL_PASS":
                note = "⚠ Meets thresholds with caching/optimization"
            else:
                note = "✗ Exceeds p99 thresholds"

            f.write(f"| {database} | {status} | {note} |\n")

        f.write("\n---\n\n")

    def _write_trade_off_analysis(self, f):
        """Write trade-off analysis"""
        f.write("## Trade-off Analysis\n\n")

        if self.runner_up:
            winner_data = self.scores[self.winner]
            runner_up_data = self.scores[self.runner_up]

            f.write(f"### {self.winner.upper()} vs {self.runner_up.upper()}\n\n")

            # Performance comparison
            perf_diff = winner_data['performance']['total_performance'] - \
                       runner_up_data['performance']['total_performance']
            f.write(f"**Performance:** {self.winner} leads by {abs(perf_diff):.1f} points\n\n")

            # Curation comparison
            curation_diff = winner_data['curation']['total_curation'] - \
                          runner_up_data['curation']['total_curation']
            f.write(f"**Curation:** {self.winner if curation_diff > 0 else self.runner_up} "
                   f"leads by {abs(curation_diff):.1f} points\n\n")

            # When to consider runner-up
            f.write(f"### When to Consider {self.runner_up.upper()}\n\n")
            f.write(f"Consider {self.runner_up} if:\n\n")
            f.write(f"- [Specific scenario 1]\n")
            f.write(f"- [Specific scenario 2]\n")
            f.write(f"- [Specific scenario 3]\n\n")

        f.write("---\n\n")

    def _write_final_recommendation(self, f, winner_data):
        """Write final recommendation"""
        f.write("## Final Recommendation\n\n")

        f.write(f"### PRIMARY: {self.winner.upper()}\n\n")

        f.write("**Rationale:**\n\n")
        f.write(f"1. **Highest Overall Score:** {winner_data['total_score']:.1f}/100 points\n")
        f.write(f"2. **Threshold Compliance:** {winner_data['threshold_status']}\n")

        perf = winner_data['performance']
        curation = winner_data['curation']

        if perf['total_performance'] >= 45:  # >75% of max
            f.write(f"3. **Excellent Performance:** {perf['p99_latency_ms']:.2f}ms p99 latency\n")

        if curation['total_curation'] >= 15:  # >75% of max
            f.write(f"4. **Strong Curation Capability:** {curation['self_service_operations']}/6 self-service operations\n")

        f.write("\n**Best For:**\n\n")
        f.write("- Primary query API (real-time lookups and traversals)\n")
        f.write("- Curator self-service operations\n")
        f.write("- Knowledge graph exploration and visualization\n\n")

        f.write("**Limitations:**\n\n")
        f.write("- [Limitation 1 - e.g., dataset growth constraints for Memgraph]\n")
        f.write("- [Limitation 2]\n\n")

        # Alternative recommendation
        if self.runner_up:
            f.write(f"### ALTERNATIVE: {self.runner_up.upper()}\n\n")
            runner_up_data = self.scores[self.runner_up]
            f.write(f"**Score:** {runner_up_data['total_score']:.1f}/100 points\n\n")
            f.write("**When to Use:** [Scenarios where runner-up is preferable]\n\n")

        f.write("---\n\n")

    def _write_implementation_plan(self, f):
        """Write implementation plan"""
        f.write("## Implementation Plan\n\n")

        f.write(f"### Phase 1: {self.winner.upper()} Deployment (Weeks 1-2)\n\n")
        f.write("**Tasks:**\n\n")
        f.write("1. Provision production infrastructure\n")
        f.write("2. Apply optimal configuration from Phase A\n")
        f.write("3. Load production dataset\n")
        f.write("4. Verify performance meets thresholds\n")
        f.write("5. Configure monitoring and alerting\n\n")

        f.write("### Phase 2: Integration (Weeks 3-4)\n\n")
        f.write("**Tasks:**\n\n")
        f.write("1. Integrate with Rust API\n")
        f.write("2. Configure connection pooling\n")
        f.write("3. Set up Redis caching layer\n")
        f.write("4. Implement Kafka activity logging\n")
        f.write("5. End-to-end testing\n\n")

        f.write("### Phase 3: Curation Tools (Weeks 5-6)\n\n")
        f.write("**Tasks:**\n\n")
        f.write("1. Set up curation UI (Bloom/Lab/pgAdmin)\n")
        f.write("2. Configure curator access and permissions\n")
        f.write("3. Train curators on tools\n")
        f.write("4. Validate self-service workflows\n\n")

        f.write("### Phase 4: Production Launch (Week 7)\n\n")
        f.write("**Tasks:**\n\n")
        f.write("1. Final load testing\n")
        f.write("2. Security review\n")
        f.write("3. Backup and disaster recovery setup\n")
        f.write("4. Go-live\n\n")

        f.write("---\n\n")

    def _write_risk_mitigation(self, f, winner_data):
        """Write risk mitigation strategies"""
        f.write("## Risk Mitigation\n\n")

        status = winner_data['threshold_status']

        if status == "FAIL":
            f.write("### CRITICAL: Threshold Failure Mitigation Required\n\n")
            f.write("Winner does not meet p99 thresholds. **Proceed to Phase 12 (Mitigation)**.\n\n")
            f.write("**Mitigation Options:**\n\n")
            f.write("1. **Redis Caching:** Cache hot queries to reduce latency\n")
            f.write("2. **Query Optimization:** Further optimize slow queries\n")
            f.write("3. **Hybrid Approach:** Use PostgreSQL for lookups, Neo4j for curation\n\n")

        elif status == "CONDITIONAL_PASS":
            f.write("### Conditional Pass Mitigation\n\n")
            f.write("Winner meets thresholds with optimization/caching.\n\n")
            f.write("**Required Mitigation:**\n\n")
            f.write("1. Implement Redis caching for hot queries\n")
            f.write("2. Monitor p99 latency closely in production\n")
            f.write("3. Have fallback plan if caching insufficient\n\n")

        f.write("### General Risks\n\n")

        f.write("#### Risk: Dataset Growth Beyond Capacity\n\n")
        f.write("**Probability:** Medium  \n")
        f.write("**Impact:** High  \n")
        f.write("**Mitigation:**\n")
        f.write("- Monitor dataset size monthly\n")
        f.write("- Plan migration if approaching limits\n")
        f.write("- Consider hybrid architecture\n\n")

        f.write("#### Risk: Performance Degradation Under Load\n\n")
        f.write("**Probability:** Low  \n")
        f.write("**Impact:** High  \n")
        f.write("**Mitigation:**\n")
        f.write("- Continuous monitoring of p99 latency\n")
        f.write("- Auto-scaling if supported\n")
        f.write("- Have runner-up database ready as fallback\n\n")

        f.write("---\n\n")

    def _write_appendix(self, f):
        """Write appendix"""
        f.write("## Appendix\n\n")

        f.write("### A. Testing Methodology\n\n")
        f.write("- Phase A: Database optimization with 4 configuration variants\n")
        f.write("- Phase B: Head-to-head comparison across 14 workload patterns\n")
        f.write("- Curation Testing: Self-service and visualization assessment\n")
        f.write("- Requests per test: 50,000\n")
        f.write("- Concurrency tested: 1, 5, 10, 20, 50, 100\n\n")

        f.write("### B. Evaluation Weights\n\n")
        f.write("- Performance: 60% (p99 latency 30%, throughput 15%, scalability 15%)\n")
        f.write("- Curation: 20% (self-service 10%, visualization 10%)\n")
        f.write("- Operational: 20% (efficiency 5%, stability 5%, complexity 5%, ecosystem 5%)\n\n")

        f.write("### C. References\n\n")
        f.write("- [Shark Bake-Off Plan](../../SHARK-BAKEOFF-PLAN.md)\n")
        f.write("- [Phase A Results](../phase-a-optimization/RESULTS_SUMMARY.md)\n")
        f.write("- [Phase B Results](../phase-b-comparison/RESULTS_SUMMARY.md)\n")
        f.write("- [Curation Testing](../../benchmark/curation/README.md)\n\n")

        f.write("---\n\n")
        f.write(f"**Document Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("**Approval Status:** [ ] Pending [ ] Approved\n")


def main():
    parser = argparse.ArgumentParser(description="Generate final decision document")
    parser.add_argument("--scores", type=Path, default=Path("final_scores.json"),
                       help="Final scores JSON file")
    parser.add_argument("--output", type=Path, default=Path("FINAL_DECISION.md"),
                       help="Output decision document")

    args = parser.parse_args()

    if not args.scores.exists():
        print(f"Error: Scores file not found: {args.scores}")
        print("\nRun calculate_scores.py first to generate scores")
        return 1

    generator = DecisionGenerator(args.scores)

    try:
        generator.load_scores()
        generator.generate_decision_document(args.output)

        print("\n✓ Decision document generation complete!")
        print(f"\nReview: {args.output}")
        print("\nNext steps:")
        print("  1. Review decision document")
        print("  2. Get stakeholder approval")
        print("  3. Proceed to implementation (or Phase 12 if mitigation needed)")

    except Exception as e:
        print(f"\n✗ Error generating decision: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
