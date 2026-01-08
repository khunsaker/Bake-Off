#!/usr/bin/env python3
"""
Analyze comprehensive benchmark results
Extract detailed latency data and create comparison report
"""

import json
import glob
from pathlib import Path
from collections import defaultdict
import statistics

def extract_latency(status_str):
    """Extract numeric latency from status string like '45.67ms (threshold <=10.00ms): ✗'"""
    try:
        return float(status_str.split('ms')[0])
    except:
        return None

def analyze_results():
    """Analyze all evaluation results and create detailed comparison"""

    results_dir = Path('/tmp/bakeoff-results')
    eval_files = list(results_dir.glob('*20260107*-evaluation.json'))

    # Organize by database and query type
    db_stats = defaultdict(lambda: defaultdict(list))

    for eval_file in eval_files:
        # Parse filename to get database name
        filename = eval_file.name
        if filename.startswith('postgresql'):
            db = 'postgresql'
        elif filename.startswith('neo4j'):
            db = 'neo4j'
        elif filename.startswith('memgraph'):
            db = 'memgraph'
        else:
            continue

        # Load evaluation data
        with open(eval_file, 'r') as f:
            data = json.load(f)

        # Extract latencies for each query
        for eval_item in data.get('evaluations', []):
            query_name = eval_item['query_name']

            # Extract p50, p95, p99
            p50 = extract_latency(eval_item.get('p50_status', ''))
            p95 = extract_latency(eval_item.get('p95_status', ''))
            p99 = extract_latency(eval_item.get('p99_status', ''))

            if p50:
                db_stats[db][query_name + '_p50'].append(p50)
            if p95:
                db_stats[db][query_name + '_p95'].append(p95)
            if p99:
                db_stats[db][query_name + '_p99'].append(p99)

    # Calculate averages
    db_averages = {}
    for db, stats in db_stats.items():
        db_averages[db] = {}
        for metric, values in stats.items():
            if values:
                db_averages[db][metric] = {
                    'min': min(values),
                    'max': max(values),
                    'avg': statistics.mean(values),
                    'median': statistics.median(values),
                    'count': len(values)
                }

    return db_averages

def print_comparison_report(db_averages):
    """Print formatted comparison report"""

    print("=" * 100)
    print("DETAILED LATENCY COMPARISON - ALL BENCHMARKS")
    print("=" * 100)
    print()

    # Query types
    query_types = ['mode_s', 'mmsi', 'country', 'log']
    percentiles = ['p50', 'p95', 'p99']

    for query in query_types:
        print(f"\n{'='*100}")
        print(f"QUERY: {query.upper()}")
        print(f"{'='*100}\n")

        for pct in percentiles:
            metric = f"{query}_{pct}"
            print(f"  {pct.upper()} Latency:")
            print(f"  {'Database':<20} {'Min':<12} {'Avg':<12} {'Median':<12} {'Max':<12} {'Samples':<10}")
            print(f"  {'-'*80}")

            for db in ['postgresql', 'neo4j', 'memgraph']:
                if metric in db_averages.get(db, {}):
                    stats = db_averages[db][metric]
                    print(f"  {db.capitalize():<20} "
                          f"{stats['min']:>6.2f}ms     "
                          f"{stats['avg']:>6.2f}ms     "
                          f"{stats['median']:>6.2f}ms     "
                          f"{stats['max']:>6.2f}ms     "
                          f"{stats['count']:<10}")
            print()

    # Overall summary
    print("\n" + "="*100)
    print("OVERALL SUMMARY")
    print("="*100 + "\n")

    for db in ['postgresql', 'neo4j', 'memgraph']:
        print(f"\n{db.upper()}:")

        # Average of all p99 metrics
        all_p99 = [stats['avg'] for key, stats in db_averages.get(db, {}).items() if key.endswith('_p99')]
        if all_p99:
            print(f"  Average p99 across all queries: {statistics.mean(all_p99):.2f}ms")

        # Average of identifier lookups (mode_s, mmsi)
        id_lookups = [
            db_averages.get(db, {}).get('mode_s_p99', {}).get('avg'),
            db_averages.get(db, {}).get('mmsi_p99', {}).get('avg')
        ]
        id_lookups = [x for x in id_lookups if x]
        if id_lookups:
            print(f"  Average p99 for identifier lookups: {statistics.mean(id_lookups):.2f}ms")

        # Traversal performance
        traversal = db_averages.get(db, {}).get('country_p99', {}).get('avg')
        if traversal:
            print(f"  Average p99 for traversals: {traversal:.2f}ms")

def save_detailed_json(db_averages):
    """Save detailed analysis to JSON"""
    output_file = Path('/tmp/bakeoff-results/detailed_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(db_averages, f, indent=2)
    print(f"\n\nDetailed analysis saved to: {output_file}")

if __name__ == '__main__':
    db_averages = analyze_results()
    print_comparison_report(db_averages)
    save_detailed_json(db_averages)
