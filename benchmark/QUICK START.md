# Benchmark Quick Start

Get benchmarking in 5 minutes!

## Prerequisites

- Python 3.8+
- Running API server (Rust, Python, Go, or Java implementation)
- Docker services (PostgreSQL, Neo4j, or Memgraph)

## Step 1: Install Dependencies (1 min)

```bash
cd benchmark/harness
pip install -r requirements.txt
```

## Step 2: Verify Server is Running (30 sec)

```bash
# Check health endpoint
curl http://localhost:8080/health

# Expected response:
# {"status":"healthy","database":"PostgreSQL"}
```

## Step 3: Run Your First Benchmark (2 min)

```bash
# Run balanced workload with 10,000 requests
python runner.py http://localhost:8080 --pattern balanced-50 --requests 10000
```

Expected output:
```
======================================================================
Benchmark Runner
======================================================================
Target:       http://localhost:8080
Pattern:      Balanced (50/40/10)
Requests:     10,000
Concurrency:  10
Cache:        Disabled
======================================================================

Checking server connectivity...
✓ Server is accessible

Generating 10,000 requests...
✓ Generated 10,000 requests

Executing benchmark...
100%|████████████████████████████████| 10000/10000 [01:30<00:00, 110.52req/s]

✓ Benchmark complete in 90.45s
Overall throughput: 110.52 qps
```

## Step 4: Review Results

The benchmark will print:
1. **Metrics Summary** - Latency percentiles and throughput
2. **Threshold Evaluation** - Pass/fail against targets
3. **Overall Recommendation** - What to do next

## Common Patterns

### Lookup-Heavy (Simulates Production Load)

```bash
python runner.py http://localhost:8080 --pattern lookup-90 --requests 50000
```

### Analytics-Heavy (Tests Complex Queries)

```bash
python runner.py http://localhost:8080 --pattern analytics-20 --requests 20000
```

### Stress Test

```bash
python runner.py http://localhost:8080 \
  --pattern lookup-95 \
  --requests 100000 \
  --concurrency 50
```

### With Caching

```bash
python runner.py http://localhost:8080 \
  --pattern balanced-50 \
  --cache \
  --requests 50000
```

## Export Results

```bash
python runner.py http://localhost:8080 \
  --pattern balanced-50 \
  --requests 50000 \
  --output results/run1
```

Creates:
- `results/run1.json` - Full metrics
- `results/run1.csv` - CSV format
- `results/run1-evaluation.json` - Pass/fail results

## Locust Web UI

For real-time monitoring:

```bash
cd ../locust
locust -f locustfile.py --host http://localhost:8080

# Open browser to http://localhost:8089
# Set users: 100
# Spawn rate: 10
# Click "Start Swarming"
```

## Compare Databases

```bash
# Test PostgreSQL
python runner.py http://localhost:8080 --pattern balanced-50 --requests 50000 --output pg

# Test Neo4j
python runner.py http://localhost:8081 --pattern balanced-50 --requests 50000 --output neo4j

# Test Memgraph
python runner.py http://localhost:8082 --pattern balanced-50 --requests 50000 --output memgraph

# Compare
python -c "
import pandas as pd
pg = pd.read_csv('pg.csv')
neo = pd.read_csv('neo4j.csv')
mem = pd.read_csv('memgraph.csv')
print('p99 Latencies (ms):')
print(f'PostgreSQL: {pg[\"latency_p99_ms\"].mean():.2f}')
print(f'Neo4j:      {neo[\"latency_p99_ms\"].mean():.2f}')
print(f'Memgraph:   {mem[\"latency_p99_ms\"].mean():.2f}')
"
```

## Troubleshooting

### "Cannot connect to server"

```bash
# Check server is running
curl http://localhost:8080/health

# Check port
lsof -i :8080
```

### "High error rate"

- Reduce concurrency: `--concurrency 5`
- Increase requests slowly
- Check server logs

### "Results vary widely"

- Run warm-up first (5000 requests)
- Increase request count for statistical significance
- Ensure server has stable resources

## Next Steps

- [Full Documentation](harness/README.md)
- [Workload Patterns](harness/README.md#workload-patterns)
- [Threshold Evaluation](harness/README.md#threshold-evaluation)
- [Locust Load Testing](harness/README.md#locust-load-testing)

## Quick Reference

### Common Commands

```bash
# Basic balanced test
python runner.py http://localhost:8080 -p balanced-50 -n 10000

# With output
python runner.py http://localhost:8080 -p balanced-50 -n 50000 -o results/test1

# High concurrency
python runner.py http://localhost:8080 -p lookup-95 -n 100000 -c 50

# With caching
python runner.py http://localhost:8080 -p balanced-50 -n 50000 --cache
```

### Available Patterns

- `lookup-95`, `lookup-90`, `lookup-85`, `lookup-80`, `lookup-75`
- `balanced-60`, `balanced-50`, `balanced-40`
- `analytics-30`, `analytics-20`, `analytics-10`
- `write-30`, `write-40`, `write-50`

### Key Metrics

- **p50** - Median latency (50th percentile)
- **p95** - 95th percentile latency
- **p99** - 99th percentile latency (most important)
- **QPS** - Queries per second (throughput)

### Thresholds

- Simple lookups: p99 < 100ms
- Two-hop queries: p99 < 300ms
- Three-hop queries: p99 < 500ms
