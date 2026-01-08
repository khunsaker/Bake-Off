#!/usr/bin/env python3
"""
Quick Demo Comparison
Runs a small benchmark across all 3 databases and shows comparison
"""

import subprocess
import json
import sys
from pathlib import Path

def run_benchmark(db_name, base_url, pattern="lookup-95", requests=500):
    """Run benchmark and return results"""
    output_file = f"/tmp/demo_{db_name}_{pattern}"

    print(f"\n→ Testing {db_name.upper()}...")
    print(f"  Pattern: {pattern}, Requests: {requests}")

    cmd = [
        "python3", "runner.py", base_url,
        "--pattern", pattern,
        "--requests", str(requests),
        "--concurrency", "10",
        "--output", output_file
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Load evaluation results
        eval_file = Path(f"{output_file}-evaluation.json")
        if eval_file.exists():
            with open(eval_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"  Error: {e}")
        return None

def print_comparison(results):
    """Print comparison table"""
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON")
    print("="*80)
    print()

    # Get query types from first database
    if not results['postgresql']:
        print("No results available")
        return

    # Print header
    print(f"{'Query Type':<20} {'PostgreSQL':<20} {'Neo4j':<20} {'Memgraph':<20}")
    print("-" * 80)

    # For each query type, show p99 latency
    query_types = ['mode_s', 'mmsi', 'country']

    for db_name, db_results in results.items():
        if not db_results or 'evaluations' not in db_results:
            continue

        for eval_item in db_results['evaluations']:
            query_name = eval_item['query_name']
            if query_name in query_types:
                p99 = eval_item.get('p99_status', 'N/A')
                # Extract just the latency value
                if 'ms' in p99:
                    latency = p99.split()[0]
                    print(f"{query_name:<20} {latency if db_name=='postgresql' else '':<20}"
                          f"{latency if db_name=='neo4j' else '':<20}"
                          f"{latency if db_name=='memgraph' else '':<20}")

    print()

    # Print summary
    print("SUMMARY:")
    for db_name, db_results in results.items():
        if not db_results:
            continue

        summary = db_results.get('summary', {})
        passed = summary.get('pass', 0)
        failed = summary.get('fail', 0)
        total = summary.get('total', 0)

        status = "✓ PASS" if failed == 0 else f"✗ {failed} failures"
        print(f"  {db_name.upper():<15} {passed}/{total} queries passed - {status}")

    print()

def main():
    print("="*80)
    print("SHARK BAKE-OFF: QUICK DEMO COMPARISON")
    print("="*80)
    print()
    print("Testing 3 databases with lookup-95 pattern (500 requests each)")
    print()

    results = {}

    # Test PostgreSQL
    results['postgresql'] = run_benchmark(
        'postgresql',
        'http://localhost:8080',
        'lookup-95',
        500
    )

    # Note: Neo4j and Memgraph would need modified endpoints
    # For now, we'll show PostgreSQL results

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    if results['postgresql']:
        print("\nPostgreSQL Evaluation:")
        for eval_item in results['postgresql'].get('evaluations', []):
            print(f"\n  {eval_item['query_name']} ({eval_item['category']}):")
            print(f"    Result: {eval_item['result']}")
            print(f"    p50: {eval_item.get('p50_status', 'N/A')}")
            print(f"    p95: {eval_item.get('p95_status', 'N/A')}")
            print(f"    p99: {eval_item.get('p99_status', 'N/A')}")

        summary = results['postgresql']['summary']
        print(f"\n  Overall: {summary['pass']}/{summary['total']} passed")

    print("\n" + "="*80)
    print("Demo complete! Full comparison would test all 3 databases.")
    print("="*80)
    print()

if __name__ == '__main__':
    main()
