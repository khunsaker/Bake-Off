#!/usr/bin/env python3
"""Quick test of comprehensive evaluation - just 3 patterns × 3 databases"""

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

DATABASES = {
    'postgresql': ('http://localhost:8080', 'PostgreSQL 16.1'),
    'neo4j': ('http://localhost:8081', 'Neo4j 5.15'),
    'memgraph': ('http://localhost:8082', 'Memgraph 2.14'),
}

# Just 3 patterns for quick test
PATTERNS = [
    ('lookup-95', 1000, 10, 'Lookup Heavy (95%)'),
    ('balanced-50', 1000, 10, 'Balanced (50/40/10)'),
    ('analytics-10', 500, 5, 'Analytics Heavy'),
]

def run_benchmark(db_name, base_url, pattern, requests, concurrency, description):
    """Run single benchmark"""
    output_dir = Path('/tmp/bakeoff-results')
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"{db_name}_{pattern}_{requests}req"

    print(f"\n→ Testing {db_name.upper()}: {description}")
    print(f"  URL: {base_url}, Requests: {requests}, Concurrency: {concurrency}")

    cmd = [
        'python3', 'runner.py', base_url,
        '--pattern', pattern,
        '--requests', str(requests),
        '--concurrency', str(concurrency),
        '--output', str(output_file)
    ]

    try:
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        elapsed = time.time() - start

        # Load evaluation
        eval_file = Path(f"{output_file}-evaluation.json")
        if eval_file.exists():
            with open(eval_file, 'r') as f:
                data = json.load(f)
            summary = data.get('summary', {})
            passed = summary.get('pass', 0)
            total = summary.get('total', 0)
            print(f"  ✓ Result: {passed}/{total} passed ({elapsed:.1f}s)\n")
            return {'success': True, 'data': data}
        else:
            print(f"  ✗ Error: No results file\n")
            return {'success': False}

    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return {'success': False}

def main():
    print("="*80)
    print("QUICK COMPREHENSIVE TEST (3 patterns × 3 databases)")
    print("="*80)
    print()

    all_results = {}

    # Test each pattern across all databases
    for pattern, requests, concurrency, description in PATTERNS:
        print(f"\n{'='*80}")
        print(f"PATTERN: {description}")
        print(f"{'='*80}")

        for db_name, (base_url, db_display) in DATABASES.items():
            result = run_benchmark(db_name, base_url, pattern, requests, concurrency, description)
            if db_name not in all_results:
                all_results[db_name] = []
            all_results[db_name].append(result)

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80 + "\n")

    for db_name, results in all_results.items():
        successful = sum(1 for r in results if r.get('success'))
        print(f"{db_name.upper()}: {successful}/{len(results)} patterns completed successfully")

    print("\n" + "="*80)
    print("Quick test complete!")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
