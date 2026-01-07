

# Shark Bake-Off Benchmark Harness

Comprehensive benchmarking toolkit for evaluating database performance across PostgreSQL, Neo4j, and Memgraph implementations.

## Features

- ✅ **HDR Histogram** - High-accuracy latency measurements
- ✅ **Parametric Workloads** - 14 pre-defined workload patterns
- ✅ **Threshold Evaluation** - Automatic pass/fail against "fast enough" criteria
- ✅ **Concurrent Testing** - Configurable concurrency for load simulation
- ✅ **Multiple Output Formats** - JSON, CSV, console reports
- ✅ **Progress Tracking** - Real-time progress bars
- ✅ **Locust Integration** - Web-based load testing

## Architecture

```
┌──────────────────┐
│  Benchmark       │
│  Runner          │
│  (runner.py)     │
└────────┬─────────┘
         │
         ├──> Workload Generator
         │    (workload.py)
         │
         ├──> Metrics Collector
         │    (metrics.py - HDR Histogram)
         │
         ├──> HTTP Executor
         │    (ThreadPoolExecutor)
         │
         └──> Threshold Evaluator
              (thresholds.py)
```

## Installation

```bash
cd benchmark/harness
pip install -r requirements.txt
```

## Quick Start

### 1. Basic Benchmark

```bash
# Run balanced workload against localhost
python runner.py http://localhost:8080 --pattern balanced-50 --requests 10000
```

### 2. With Result Export

```bash
python runner.py http://localhost:8080 \
  --pattern lookup-90 \
  --requests 50000 \
  --cache \
  --output results/run1
```

This creates:
- `results/run1.json` - Detailed metrics
- `results/run1.csv` - Metrics in CSV format
- `results/run1-evaluation.json` - Threshold evaluation

### 3. High-Load Stress Test

```bash
python runner.py http://localhost:8080 \
  --pattern lookup-95 \
  --requests 100000 \
  --concurrency 50
```

## Workload Patterns

### Lookup-Heavy (Simulates High-Frequency Lookups)

| Pattern | Distribution | Use Case |
|---------|--------------|----------|
| `lookup-95` | 95% lookup / 4% analytics / 1% write | Extreme read-heavy |
| `lookup-90` | 90% lookup / 8% analytics / 2% write | Heavy read workload |
| `lookup-85` | 85% lookup / 12% analytics / 3% write | Moderate read-heavy |
| `lookup-80` | 80% lookup / 15% analytics / 5% write | Balanced read-heavy |
| `lookup-75` | 75% lookup / 20% analytics / 5% write | Mixed read-heavy |

### Balanced (Realistic Mixed Usage)

| Pattern | Distribution | Use Case |
|---------|--------------|----------|
| `balanced-60` | 60% lookup / 35% analytics / 5% write | Lookup-favored |
| `balanced-50` | 50% lookup / 40% analytics / 10% write | Even split |
| `balanced-40` | 40% lookup / 45% analytics / 15% write | Analytics-favored |

### Analytics-Heavy (Complex Query Patterns)

| Pattern | Distribution | Use Case |
|---------|--------------|----------|
| `analytics-30` | 30% lookup / 60% analytics / 10% write | Analytics-focused |
| `analytics-20` | 20% lookup / 70% analytics / 10% write | Heavy analytics |
| `analytics-10` | 10% lookup / 80% analytics / 10% write | Extreme analytics |

### Write-Heavy (Update-Intensive)

| Pattern | Distribution | Use Case |
|---------|--------------|----------|
| `write-30` | 50% lookup / 20% analytics / 30% write | Moderate writes |
| `write-40` | 40% lookup / 20% analytics / 40% write | Heavy writes |
| `write-50` | 30% lookup / 20% analytics / 50% write | Extreme writes |

## Query Types

### Lookups (S1-S2)
- Aircraft by Mode-S
- Ship by MMSI
- **Threshold**: p99 < 100ms

### Analytics (S3-S10)
- Two-hop: Aircraft by country (p99 < 300ms)
- Three-hop: Cross-domain queries (p99 < 500ms)
- Activity history (p99 < 300ms)

### Writes (S7-S8)
- Activity logging
- **Threshold**: p99 < 500ms

## Metrics Collected

### Latency Percentiles
- Min, Mean, Median (p50)
- p75, p90, p95, p99, p99.9, Max
- Standard Deviation

### Throughput
- Queries per second (QPS)
- Total requests
- Success/failure counts
- Error rates

### Accuracy
Uses **HDR Histogram** for:
- Accurate high-percentile measurements (p99, p99.9)
- Consistent low overhead
- Minimal memory footprint

## Threshold Evaluation

### Pass/Fail Criteria

Results are evaluated against thresholds from the plan:

| Query Type | p50 Target | p95 Acceptable | p99 Maximum |
|------------|-----------|----------------|-------------|
| Identifier Lookup | 10ms | 50ms | **100ms** |
| Two-Hop Traversal | 50ms | 150ms | **300ms** |
| Three-Hop Traversal | 100ms | 300ms | **500ms** |
| Six-Hop Traversal | 500ms | 1000ms | **2000ms** |
| Property Write | 50ms | 200ms | **500ms** |
| Relationship Write | 100ms | 300ms | **500ms** |

### Evaluation Results

- **PASS**: All thresholds met
- **CONDITIONAL PASS**: Passes with caching (80%+ hit rate required)
- **FAIL**: Does not meet thresholds

## Locust Load Testing

For web-based load testing and real-time monitoring:

```bash
cd ../locust

# Start Locust web UI
locust -f locustfile.py --host http://localhost:8080

# Open browser to http://localhost:8089
# Configure users and spawn rate
# Monitor real-time charts
```

### Locust User Classes

- `SharkBakeOffUser` - Default mixed workload (95/4/1)
- `LookupHeavyUser` - Lookup-heavy pattern
- `AnalyticsHeavyUser` - Analytics-heavy pattern
- `BalancedUser` - Balanced pattern

### Headless Locust

```bash
# Run without web UI
locust -f locustfile.py \
  --host http://localhost:8080 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless \
  --html report.html
```

## Output Formats

### Console Output

```
======================================================================
Benchmark Session: benchmark-Balanced (50/40/10)
Start Time: 2025-01-06T15:30:00.000Z
======================================================================

======================================================================
Metrics: mode_s
======================================================================
Total Requests:      5,000
Successful:          4,998
Failed:              2
Error Rate:          0.04%
Duration:            45.23s
Throughput:          110.52 qps

Latency (ms):
  Min:               1.23
  Mean:              8.45
  p50 (median):      7.89
  p75:               10.12
  p90:               14.56
  p95:               18.23
  p99:               25.67
  p99.9:             42.11
  Max:               58.34
  StdDev:            5.23
======================================================================
```

### JSON Export

```json
{
  "session_name": "benchmark-lookup-90",
  "start_time": "2025-01-06T15:30:00.000Z",
  "end_time": "2025-01-06T15:31:30.000Z",
  "metrics": [
    {
      "query_name": "mode_s",
      "total_requests": 9000,
      "successful_requests": 8995,
      "failed_requests": 5,
      "total_duration_sec": 90.5,
      "latency_stats": {
        "min": 1.2,
        "p50": 7.8,
        "p95": 18.2,
        "p99": 25.6,
        "max": 58.3,
        "mean": 8.4,
        "stddev": 5.2
      },
      "throughput_qps": 99.4,
      "error_rate": 0.0005
    }
  ]
}
```

### CSV Export

```csv
query_name,total_requests,successful_requests,failed_requests,duration_sec,throughput_qps,error_rate,latency_min_ms,latency_p50_ms,latency_p95_ms,latency_p99_ms,latency_max_ms,latency_mean_ms,latency_stddev_ms
mode_s,9000,8995,5,90.5,99.4,0.0005,1.2,7.8,18.2,25.6,58.3,8.4,5.2
```

## Advanced Usage

### Custom Test Data

```python
from workload import DatasetSelector

# Load custom identifiers
dataset = DatasetSelector(data_file='custom_ids.json')

# Or add manually
dataset.mode_s_ids.extend(['CUSTOM1', 'CUSTOM2'])
dataset.mmsi_ids.extend(['999111222', '999222333'])
```

### Programmatic Benchmark

```python
from runner import BenchmarkRunner
from workload import WORKLOAD_PATTERNS

# Create runner
runner = BenchmarkRunner(
    base_url='http://localhost:8080',
    pattern=WORKLOAD_PATTERNS['lookup-90'],
    total_requests=50000,
    concurrency=20,
    cache_enabled=True
)

# Run benchmark
metrics = runner.run_benchmark()

# Evaluate
evaluator = runner.evaluate_results(metrics)
```

### Custom Workload Pattern

```python
from workload import WorkloadPattern, WorkloadGenerator

# Define custom pattern
custom_pattern = WorkloadPattern(
    name="Custom (70/25/5)",
    lookup_pct=70,
    analytics_pct=25,
    write_pct=5
)

# Use in generator
generator = WorkloadGenerator(
    pattern=custom_pattern,
    lookup_queries=lookup_queries,
    analytics_queries=analytics_queries,
    write_queries=write_queries
)
```

## Comparison Testing

### Test Multiple Implementations

```bash
# PostgreSQL
python runner.py http://localhost:8080 \
  --pattern balanced-50 \
  --requests 50000 \
  --output results/postgres-balanced

# Neo4j
python runner.py http://localhost:8081 \
  --pattern balanced-50 \
  --requests 50000 \
  --output results/neo4j-balanced

# Memgraph
python runner.py http://localhost:8082 \
  --pattern balanced-50 \
  --requests 50000 \
  --output results/memgraph-balanced
```

### Compare Results

```python
import pandas as pd

# Load results
pg = pd.read_csv('results/postgres-balanced.csv')
neo4j = pd.read_csv('results/neo4j-balanced.csv')
memgraph = pd.read_csv('results/memgraph-balanced.csv')

# Compare p99 latencies
comparison = pd.DataFrame({
    'PostgreSQL': pg['latency_p99_ms'],
    'Neo4j': neo4j['latency_p99_ms'],
    'Memgraph': memgraph['latency_p99_ms']
}, index=pg['query_name'])

print(comparison)
```

## Troubleshooting

### Connection Errors

```bash
# Check server is running
curl http://localhost:8080/health

# Test with single request
python runner.py http://localhost:8080 --requests 1
```

### High Error Rates

- Reduce concurrency (`--concurrency 5`)
- Increase timeout in `runner.py` (default: 30s)
- Check server logs for errors

### Memory Issues

- Reduce total requests
- Use smaller batches
- Run Locust for streaming results

### Inconsistent Results

- Warm up the cache first (run benchmark twice)
- Increase number of requests for statistical significance
- Use same seed for reproducibility

## Performance Tips

### For Best Accuracy

1. **Warm-up run**: First run warms JVM/caches
2. **Statistical significance**: >10,000 requests per query type
3. **Steady state**: Monitor server metrics (CPU, memory)
4. **Isolation**: Run on dedicated hardware

### Recommended Test Sequence

```bash
# 1. Warm-up
python runner.py http://localhost:8080 --pattern lookup-95 --requests 5000

# 2. Baseline (no cache)
python runner.py http://localhost:8080 --pattern balanced-50 --requests 50000 --output baseline

# 3. With cache
python runner.py http://localhost:8080 --pattern balanced-50 --requests 50000 --cache --output cached

# 4. Stress test
python runner.py http://localhost:8080 --pattern lookup-95 --requests 100000 --concurrency 50 --output stress
```

## Integration with Monitoring

### Prometheus

Metrics are exposed at `/metrics` endpoint (if implemented in API).

### Grafana

Import pre-built dashboards from `monitoring/grafana/dashboards/`.

## References

- [HDR Histogram Documentation](http://hdrhistogram.org/)
- [Locust Documentation](https://docs.locust.io/)
- [Shark Bake-Off Plan](../../SHARK-BAKEOFF-PLAN.md)
- [Query Definitions](../queries/README.md)

## Contributing

When adding new query types:

1. Add query spec to `workload.py`
2. Add threshold to `thresholds.py`
3. Update category mapping in `runner.py`
4. Add Locust task to `locustfile.py`

## License

See project root for license information.
