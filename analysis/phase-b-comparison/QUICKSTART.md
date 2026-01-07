# Phase B Comparison - Quick Start

Run head-to-head database comparison in under 30 minutes!

## Prerequisites

- ✅ Phase A complete (optimal configurations identified)
- ✅ All databases configured with optimal settings
- ✅ Rust implementation running on http://localhost:8080
- ✅ Python dependencies installed

## Step 1: Verify Optimal Configurations (5 min)

Ensure each database is running with its optimal configuration from Phase A:

### PostgreSQL

```bash
# Verify configuration applied
docker exec shark-postgres psql -U shark -d sharkdb \
  -c "SHOW shared_buffers; SHOW effective_cache_size;"

# Should show optimized values (e.g., 4GB, 12GB)
```

### Neo4j

```bash
# Verify configuration
docker exec shark-neo4j cypher-shell -u neo4j -p sharkbakeoff \
  "CALL dbms.listConfig() YIELD name, value
   WHERE name CONTAINS 'memory'
   RETURN name, value;"

# Should show optimized heap and page cache
```

### Memgraph

```bash
# Verify configuration
docker logs shark-memgraph 2>&1 | grep -i "memory-limit"

# Should show optimized memory limit
```

## Step 2: Run Quick Comparison (10-15 min)

### Option A: Quick Test (3 workloads)

```bash
cd analysis/phase-b-comparison

python run_comparison.py \
  --databases postgresql neo4j memgraph \
  --workloads lookup-95 balanced-50 analytics-20 \
  --requests 10000 \
  --test-type workload
```

**Time:** ~10-15 minutes

### Option B: Full Comparison (All 14 workloads)

```bash
python run_comparison.py \
  --databases postgresql neo4j memgraph \
  --workloads all \
  --requests 50000 \
  --test-type workload
```

**Time:** ~2-3 hours

### Option C: Concurrency Testing Only

```bash
python run_comparison.py \
  --databases postgresql neo4j memgraph \
  --concurrency 1,5,10,20,50 \
  --requests 50000 \
  --test-type concurrency
```

**Time:** ~1 hour

### Option D: Full Suite (Recommended)

```bash
python run_comparison.py \
  --databases postgresql neo4j memgraph \
  --workloads all \
  --concurrency 1,5,10,20,50,100 \
  --requests 50000 \
  --test-type both
```

**Time:** ~4-5 hours (can run overnight)

## Step 3: Analyze Results (5 min)

### Crossover Analysis

```bash
python analyze_crossover.py --export results/CROSSOVER_ANALYSIS.md
```

Expected output:

```
================================================================================
WORKLOAD CROSSOVER ANALYSIS
================================================================================

Lookup-Heavy Workloads:
--------------------------------------------------------------------------------
Pattern                   Winner          p99 (ms)     Margin
--------------------------------------------------------------------------------
lookup-95                 memgraph            4.23       45.2%
lookup-90                 memgraph            5.67       38.1%
lookup-80                 neo4j               8.12       22.5%

...

================================================================================
OVERALL WINNER ANALYSIS
================================================================================

Database         Wins       Win Rate
----------------------------------------
memgraph         9          64.3%
neo4j            4          28.6%
postgresql       1          7.1%
```

### View Summary

```bash
cat results/CROSSOVER_ANALYSIS.md
```

## Step 4: Review Results

Results are saved in `results/`:

```bash
results/
├── postgresql/
│   ├── workload_summary.json       # All workload results
│   ├── concurrency_summary.json    # Concurrency results
│   ├── lookup-95_c20_*.csv         # Individual test results
│   └── ...
├── neo4j/
│   └── ...
├── memgraph/
│   └── ...
└── CROSSOVER_ANALYSIS.md           # Analysis report
```

## Expected Results

Based on database characteristics:

### Lookup-Heavy Workloads (90%+ identifier lookups)

**Expected Winner:** Memgraph
- In-memory advantage
- Fastest single-record lookups

### Balanced Workloads (50/40/10 mix)

**Expected Winner:** Memgraph or Neo4j
- Graph traversal efficiency
- No join overhead

### Analytics-Heavy (70%+ graph traversals)

**Expected Winner:** Memgraph
- In-memory graph traversal
- No disk I/O

### Write-Heavy

**Expected Winner:** TBD (test-dependent)
- PostgreSQL: Mature WAL
- Memgraph: MVCC advantage
- Neo4j: Lock-based

## Troubleshooting

### "Database not responding"

**Solution:** Check database health

```bash
docker ps
docker logs shark-postgres
docker logs shark-neo4j
docker logs shark-memgraph
```

### "Inconsistent results"

**Solution:** Increase warm-up

```bash
# Edit run_comparison.py
# Change warm-up requests from 5000 to 10000
```

### "Out of memory" (Memgraph)

**Solution:** Reduce data size or adjust memory limit

```bash
# Check memory usage
docker stats shark-memgraph

# Adjust memory limit in docker-compose.yml
```

### "Tests taking too long"

**Solution:** Use Quick Test (Option A)

```bash
python run_comparison.py \
  --workloads lookup-95 balanced-50 analytics-20 \
  --requests 10000
```

## Quick Commands

### Test Single Database

```bash
# Test only PostgreSQL
python run_comparison.py --databases postgresql --workloads lookup-95 balanced-50
```

### Test Single Workload

```bash
# Test only balanced-50 across all databases
python run_comparison.py --workloads balanced-50
```

### Resume Interrupted Test

Results are saved after each test. Just re-run the same command - it will generate new timestamps.

## Interpreting Results

### Performance Margin

- **< 10%**: Negligible difference
- **10-25%**: Noticeable difference
- **25-50%**: Significant difference
- **> 50%**: Dominant winner

### Winner Determination

Database wins a workload if it has the **lowest p99 latency**.

### Crossover Point

Point where database preference changes:

Example:
```
lookup-95:  Memgraph wins (4.2ms vs 7.8ms) → 46% margin
balanced-50: Neo4j wins    (18ms vs 22ms)  → 18% margin
analytics-20: Memgraph wins (12ms vs 35ms) → 65% margin
```

**Crossover:** Between 95% lookup and 50% balanced, Memgraph advantage shrinks from 46% to 18%.

## Next Steps

After completing Phase B:

1. **Review** crossover analysis report
2. **Identify** overall winner
3. **Document** trade-offs and edge cases
4. **Proceed to Phase C** (Final Decision)

## Advanced: Custom Analysis

### Extract Specific Metrics

```python
import json

# Load results
with open('results/memgraph/workload_summary.json', 'r') as f:
    data = json.load(f)

# Get p99 for lookup-95
for result in data['results']:
    if result['workload_pattern'] == 'lookup-95':
        print(f"p99: {result['p99_ms']}ms")
```

### Compare Two Databases

```bash
# Compare PostgreSQL vs Neo4j only
python run_comparison.py --databases postgresql neo4j
```

## Validation Checklist

Before moving to Phase C:

- [ ] All databases tested with optimal configurations
- [ ] Workload comparison complete (at least 3 patterns)
- [ ] Crossover analysis generated
- [ ] Overall winner identified
- [ ] Results documented
- [ ] No unexpected errors or failures

## Timeline

- **Quick Test:** 15 minutes
- **Medium Test (6 workloads):** 1-2 hours
- **Full Test (14 workloads + concurrency):** 4-5 hours

## Summary

**Minimum Test for Phase B:**
```bash
# 1. Verify configs (5 min)
# 2. Run quick comparison (15 min)
python run_comparison.py --workloads lookup-95 balanced-50 analytics-20 --requests 10000

# 3. Analyze (2 min)
python analyze_crossover.py --export results/CROSSOVER_ANALYSIS.md

# 4. Review results (5 min)
cat results/CROSSOVER_ANALYSIS.md
```

**Total Time:** 30 minutes

**Recommended Full Test:**
```bash
# Run overnight
python run_comparison.py --workloads all --concurrency 1,5,10,20,50,100 --test-type both
```

**Total Time:** 4-5 hours (unattended)

## References

- [Phase B README](README.md) - Full methodology
- [Phase A Results](../phase-a-optimization/RESULTS_SUMMARY.md) - Optimal configurations
- [Benchmark Harness](../../benchmark/harness/README.md) - Workload definitions
