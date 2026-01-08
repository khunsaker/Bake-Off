#!/usr/bin/env python3
"""
Comprehensive Shark Bake-Off Evaluation
Runs full benchmark suite across all 3 databases
"""

import subprocess
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Database configurations
DATABASES = {
    'postgresql': {
        'base_url': 'http://localhost:8080',
        'name': 'PostgreSQL 16.1',
        'color': '\033[94m'  # Blue
    },
    'neo4j': {
        'base_url': 'http://localhost:8081',
        'name': 'Neo4j 5.15',
        'color': '\033[92m'  # Green
    },
    'memgraph': {
        'base_url': 'http://localhost:8082',
        'name': 'Memgraph 2.14',
        'color': '\033[93m'  # Yellow
    }
}

# Workload patterns to test (Phase B)
# Using actual patterns defined in workload.py
PATTERNS = [
    # Identifier-heavy patterns
    ('lookup-95', 10000, 20, 'Lookup Heavy (95%)'),
    ('lookup-90', 8000, 20, 'Lookup Heavy (90%)'),
    ('lookup-80', 8000, 20, 'Lookup Medium (80%)'),
    ('lookup-75', 5000, 20, 'Lookup Medium (75%)'),

    # Balanced patterns
    ('balanced-60', 8000, 20, 'Balanced (60/35/5)'),
    ('balanced-50', 10000, 20, 'Balanced (50/40/10)'),
    ('balanced-40', 5000, 20, 'Balanced (40/45/15)'),

    # Analytics-heavy patterns
    ('analytics-30', 3000, 15, 'Analytics Heavy (30/60/10)'),
    ('analytics-20', 2000, 10, 'Analytics Heavy (20/70/10)'),
    ('analytics-10', 1000, 10, 'Analytics Heavy (10/80/10)'),

    # Write-heavy patterns
    ('write-30', 5000, 20, 'Write Heavy (50/20/30)'),
    ('write-40', 3000, 15, 'Write Heavy (40/20/40)'),

    # Concurrency stress tests
    ('balanced-50', 5000, 50, 'High Concurrency (50 users)'),
    ('balanced-50', 3000, 100, 'Very High Concurrency (100 users)'),
]

RESET = '\033[0m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*80}")
    print(f"{text:^80}")
    print(f"{'='*80}\n")

def run_benchmark(db_name, db_config, pattern, requests, concurrency, description):
    """Run benchmark and return results"""
    output_dir = Path('/tmp/bakeoff-results')
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"{db_name}_{pattern}_c{concurrency}_{timestamp}"

    color = db_config['color']
    print(f"{color}→ Testing {db_config['name']}{RESET}")
    print(f"  Pattern: {description}")
    print(f"  Requests: {requests}, Concurrency: {concurrency}")

    cmd = [
        'python3', 'runner.py', db_config['base_url'],
        '--pattern', pattern,
        '--requests', str(requests),
        '--concurrency', str(concurrency),
        '--output', str(output_file)
    ]

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd='/home/kwhunsaker/Shark-Bake-Off-project/benchmark/harness'
        )

        elapsed = time.time() - start_time

        # Load evaluation results
        eval_file = Path(f"{output_file}-evaluation.json")
        if eval_file.exists():
            with open(eval_file, 'r') as f:
                data = json.load(f)

            # Extract summary
            summary = data.get('summary', {})
            passed = summary.get('pass', 0)
            total = summary.get('total', 0)

            status = '✓' if passed == total else '✗'
            print(f"  {status} Result: {passed}/{total} queries passed ({elapsed:.1f}s)")
            print()

            return {
                'success': True,
                'data': data,
                'file': str(output_file),
                'elapsed': elapsed
            }
        else:
            print(f"  ✗ Error: Evaluation file not found")
            print()
            return {'success': False}

    except subprocess.TimeoutExpired:
        print(f"  ✗ Error: Benchmark timed out (>10 minutes)")
        print()
        return {'success': False}
    except Exception as e:
        print(f"  ✗ Error: {e}")
        print()
        return {'success': False}

def aggregate_results(all_results):
    """Aggregate and score all results"""
    scores = {}

    for db_name in DATABASES.keys():
        total_tests = 0
        passed_tests = 0
        total_latency = 0
        latency_count = 0

        db_results = all_results.get(db_name, [])

        for result in db_results:
            if not result.get('success'):
                continue

            data = result.get('data', {})
            summary = data.get('summary', {})

            total_tests += summary.get('total', 0)
            passed_tests += summary.get('pass', 0)

            # Aggregate latencies
            for eval_item in data.get('evaluations', []):
                if 'p99' in eval_item:
                    # Extract numeric value from "12.3ms" format
                    p99_str = str(eval_item['p99'])
                    if 'ms' in p99_str:
                        try:
                            p99_val = float(p99_str.replace('ms', '').strip())
                            total_latency += p99_val
                            latency_count += 1
                        except:
                            pass

        avg_latency = total_latency / latency_count if latency_count > 0 else 0
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        scores[db_name] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'pass_rate': pass_rate,
            'avg_p99_latency': avg_latency,
            'results_count': len(db_results)
        }

    return scores

def print_summary(all_results, scores):
    """Print comprehensive summary"""
    print_header("COMPREHENSIVE EVALUATION SUMMARY")

    print(f"{'Database':<20} {'Tests Run':<12} {'Passed':<12} {'Pass Rate':<15} {'Avg p99 Latency':<20}")
    print("-" * 80)

    for db_name, db_config in DATABASES.items():
        score = scores.get(db_name, {})
        color = db_config['color']

        total = score.get('total_tests', 0)
        passed = score.get('passed_tests', 0)
        rate = score.get('pass_rate', 0)
        latency = score.get('avg_p99_latency', 0)

        print(f"{color}{db_config['name']:<20}{RESET} "
              f"{total:<12} {passed:<12} {rate:>6.1f}% {'':>8} {latency:>6.1f}ms")

    print()

    # Determine winner
    winner = max(scores.items(), key=lambda x: (x[1]['pass_rate'], -x[1]['avg_p99_latency']))
    winner_name = DATABASES[winner[0]]['name']
    winner_color = DATABASES[winner[0]]['color']

    print(f"{winner_color}Winner: {winner_name}{RESET}")
    print(f"  Pass Rate: {winner[1]['pass_rate']:.1f}%")
    print(f"  Avg p99 Latency: {winner[1]['avg_p99_latency']:.1f}ms")
    print()

def main():
    print_header("SHARK BAKE-OFF: COMPREHENSIVE EVALUATION")
    print("Testing 3 databases × 14 workload patterns")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Estimated time: 30-60 minutes")
    print("Results will be saved to: /tmp/bakeoff-results/")
    print()

    all_results = {db: [] for db in DATABASES.keys()}

    # Run all patterns across all databases
    for pattern, requests, concurrency, description in PATTERNS:
        print_header(f"PATTERN: {description} ({pattern})")

        for db_name, db_config in DATABASES.items():
            result = run_benchmark(
                db_name, db_config, pattern, requests, concurrency, description
            )
            all_results[db_name].append(result)

            # Small delay between tests
            time.sleep(2)

    # Aggregate and display results
    scores = aggregate_results(all_results)
    print_summary(all_results, scores)

    # Save consolidated results
    output_file = Path('/tmp/bakeoff-results/comprehensive_results.json')
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'databases': DATABASES,
            'patterns': PATTERNS,
            'scores': scores,
            'detailed_results': all_results
        }, f, indent=2, default=str)

    print(f"Detailed results saved to: {output_file}")
    print()
    print_header("EVALUATION COMPLETE")

if __name__ == '__main__':
    main()
