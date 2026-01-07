# Phase A Optimization - Quick Start

Get started with database optimization testing in 10 minutes!

## Prerequisites

- Docker and docker-compose running
- All three databases loaded with data (PostgreSQL, Neo4j, Memgraph)
- Rust implementation running on http://localhost:8080
- Python 3.8+ with dependencies installed

## Step 1: Review Optimization Guides (5 min)

Read the optimization guide for your target database:

```bash
# PostgreSQL
cat postgresql/OPTIMIZATION_GUIDE.md

# Neo4j
cat neo4j/OPTIMIZATION_GUIDE.md

# Memgraph
cat memgraph/OPTIMIZATION_GUIDE.md
```

## Step 2: Test Configuration Variants (Variable Time)

Use the automated test framework:

```bash
# Test all PostgreSQL configurations
python3 test_configs.py postgresql

# Test specific configs only
python3 test_configs.py postgresql --configs default optimized

# Test Neo4j
python3 test_configs.py neo4j

# Test Memgraph
python3 test_configs.py memgraph
```

### Manual Configuration Steps

The test framework will prompt you to manually apply configurations. Follow these steps:

#### PostgreSQL

```bash
# 1. Copy config to container
docker cp postgresql/configs/optimized.conf shark-postgres:/etc/postgresql/postgresql.conf

# 2. Restart
docker restart shark-postgres

# 3. Verify
docker exec shark-postgres psql -U shark -d sharkdb -c "SHOW shared_buffers;"
```

#### Neo4j

```bash
# 1. Update docker-compose.yml to mount config
# Add under neo4j service:
#   volumes:
#     - ./analysis/phase-a-optimization/neo4j/configs/optimized.conf:/var/lib/neo4j/conf/neo4j.conf

# 2. Restart
docker-compose restart neo4j

# 3. Verify
docker exec shark-neo4j cypher-shell -u neo4j -p sharkbakeoff \
  "CALL dbms.listConfig() YIELD name, value WHERE name CONTAINS 'memory' RETURN name, value;"
```

#### Memgraph

```bash
# 1. Update docker-compose.yml command section
# See memgraph/configs/optimized.sh for flags to add

# 2. Restart
docker-compose restart memgraph

# 3. Verify
docker exec shark-memgraph mgconsole --host 127.0.0.1 --port 7687 \
  --username memgraph --password sharkbakeoff \
  -e "SHOW CONFIG;"
```

## Step 3: Review Results

Results are automatically saved to:

```bash
# Results directory structure
postgresql/results/
  - default_YYYYMMDD_HHMMSS.csv
  - optimized_YYYYMMDD_HHMMSS.csv
  - extreme_YYYYMMDD_HHMMSS.csv
  - summary.json

neo4j/results/
  - [same structure]

memgraph/results/
  - [same structure]
```

View summary:

```bash
cat postgresql/results/summary.json | jq
```

## Step 4: Compare Configurations

The test framework automatically compares configurations to baseline:

```bash
python3 test_configs.py postgresql --compare-to-baseline
```

Example output:

```
================================================================================
COMPARISON: default vs optimized
================================================================================

Throughput:         245.3 → 387.6 req/s (+58.0%) ↑

Latency Changes:
  p50:              18.45 → 12.23 ms (-33.7%) ↑
  p95:              45.67 → 28.34 ms (-37.9%) ↑
  p99:              78.90 → 42.11 ms (-46.6%) ↑
  mean:             22.34 → 14.67 ms (-34.3%) ↑

================================================================================
✓ SIGNIFICANT IMPROVEMENT (p99 latency reduced by >5%)
================================================================================
```

## Step 5: Select Optimal Configuration

Based on test results, choose the best configuration variant for each database:

| Database   | Recommended Config | Expected Improvement |
|------------|-------------------|----------------------|
| PostgreSQL | aggressive        | 33-47% latency reduction |
| Neo4j      | aggressive        | 40-50% latency reduction |
| Memgraph   | aggressive        | 38-50% latency reduction |

## Common Issues

### "Database not ready"

**Solution**: Wait longer for database startup

```bash
# Check database status
docker ps
docker logs shark-postgres  # or shark-neo4j, shark-memgraph
```

### "Config file not found"

**Solution**: Ensure you're in the correct directory

```bash
cd /path/to/Shark-Bake-Off-project/analysis/phase-a-optimization
python3 test_configs.py postgresql
```

### "Permission denied"

**Solution**: Make script executable

```bash
chmod +x test_configs.py
```

### "Import error: requests"

**Solution**: Install Python dependencies

```bash
pip install requests
```

## Next Steps

After completing Phase A optimization for all databases:

1. **Document findings** in each database's results directory
2. **Select optimal configurations** for Phase B (head-to-head comparison)
3. **Proceed to ORM overhead analysis** (see `orm-overhead/README.md`)
4. **Proceed to language comparison** (see `language-comparison/README.md`)

## Advanced Usage

### Custom Benchmark Parameters

Edit `test_configs.py` to adjust:

```python
self.warmup_requests = 5000          # Warm-up request count
self.warmup_pattern = "lookup-95"    # Warm-up workload pattern
self.benchmark_requests = 50000      # Benchmark request count
self.benchmark_pattern = "balanced-50"  # Benchmark workload
self.concurrency = 20                # Concurrent connections
```

### Test Single Configuration

```bash
# Test only the optimized config
python3 test_configs.py postgresql --configs optimized
```

### Custom Workload Pattern

```bash
# Edit runner command in test_configs.py
self.benchmark_pattern = "analytics-30"  # For graph-heavy workload
```

## Validation Checklist

Before moving to Phase B:

- [ ] All three databases tested with all configuration variants
- [ ] Results show >10% improvement from default to optimized
- [ ] Optimal configuration selected for each database
- [ ] Results documented in `RESULTS_SUMMARY.md`
- [ ] No errors or failed requests in benchmark runs
- [ ] Database-specific tuning guides reviewed and understood

## Timeline

- **PostgreSQL optimization**: 2-4 hours
- **Neo4j optimization**: 2-4 hours
- **Memgraph optimization**: 1-2 hours
- **Total Phase A**: 1-2 days (including analysis)

## References

- [Phase A README](README.md) - Full optimization approach
- [PostgreSQL Optimization Guide](postgresql/OPTIMIZATION_GUIDE.md)
- [Neo4j Optimization Guide](neo4j/OPTIMIZATION_GUIDE.md)
- [Memgraph Optimization Guide](memgraph/OPTIMIZATION_GUIDE.md)
- [Benchmark Harness](../../benchmark/harness/README.md)
