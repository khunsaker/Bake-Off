# PostgreSQL Optimization Guide

Comprehensive guide to tuning PostgreSQL for Shark Bake-Off benchmark workloads.

## Current Configuration (Baseline)

From `docker-compose.yml`:
- Image: `postgres:16-alpine`
- Default PostgreSQL configuration
- No custom tuning

## System Resources

Assumed environment (adjust for your hardware):
- **CPU**: 4-8 cores
- **RAM**: 16 GB
- **Storage**: SSD
- **Network**: 1 Gbps

## Optimization Strategy

### 1. Memory Configuration

PostgreSQL performance heavily depends on memory settings.

#### shared_buffers

**Purpose**: Cache for database pages

**Default**: ~128 MB
**Recommended**: 25% of system RAM
**For 16 GB RAM**: 4 GB

```sql
ALTER SYSTEM SET shared_buffers = '4GB';
```

**Rationale**: Reduces disk I/O by caching frequently accessed data in memory.

#### effective_cache_size

**Purpose**: Hint to query planner about available OS cache

**Default**: ~4 GB
**Recommended**: 50-75% of system RAM
**For 16 GB RAM**: 12 GB

```sql
ALTER SYSTEM SET effective_cache_size = '12GB';
```

**Rationale**: Helps planner choose index scans over sequential scans.

#### work_mem

**Purpose**: Memory for sort and hash operations

**Default**: 4 MB
**Recommended**: 64-128 MB (depends on connections)
**Calculation**: (Total RAM * 0.25) / max_connections

```sql
ALTER SYSTEM SET work_mem = '64MB';
```

**Warning**: This is per-operation! A complex query may use multiple work_mem allocations.

#### maintenance_work_mem

**Purpose**: Memory for VACUUM, CREATE INDEX, etc.

**Default**: 64 MB
**Recommended**: 1-2 GB

```sql
ALTER SYSTEM SET maintenance_work_mem = '1GB';
```

---

### 2. Query Planning

#### random_page_cost

**Purpose**: Estimated cost of random disk I/O

**Default**: 4.0 (assumes spinning disks)
**For SSD**: 1.1-1.5

```sql
ALTER SYSTEM SET random_page_cost = 1.1;
```

**Rationale**: SSDs have much faster random access than sequential. Lower value encourages index usage.

#### effective_io_concurrency

**Purpose**: Number of concurrent I/O operations

**Default**: 1
**For SSD**: 200

```sql
ALTER SYSTEM SET effective_io_concurrency = 200;
```

**Rationale**: SSDs can handle many concurrent operations.

#### default_statistics_target

**Purpose**: Sample size for ANALYZE

**Default**: 100
**Recommended**: 500 (for complex queries)

```sql
ALTER SYSTEM SET default_statistics_target = 500;
```

**Rationale**: Better query plans for complex joins.

---

### 3. Parallelism

#### max_parallel_workers_per_gather

**Purpose**: Parallel workers per query operation

**Default**: 2
**Recommended**: 4 (for 8-core system)

```sql
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
```

#### max_parallel_workers

**Purpose**: Total parallel workers

**Default**: 8
**Recommended**: Number of cores

```sql
ALTER SYSTEM SET max_parallel_workers = 8;
```

#### max_worker_processes

**Purpose**: Background worker processes

**Default**: 8
**Recommended**: Number of cores + 4

```sql
ALTER SYSTEM SET max_worker_processes = 12;
```

---

### 4. Connection Management

#### max_connections

**Purpose**: Maximum concurrent connections

**Default**: 100
**Benchmark Need**: 20-50 (using connection pooling)

```sql
ALTER SYSTEM SET max_connections = 200;
```

**Note**: Higher max_connections reduces memory available for each connection.

---

### 5. Write-Ahead Log (WAL)

#### wal_buffers

**Purpose**: Buffer for WAL writes

**Default**: -1 (auto)
**Recommended**: 16 MB

```sql
ALTER SYSTEM SET wal_buffers = '16MB';
```

#### checkpoint_completion_target

**Purpose**: Spread out checkpoint writes

**Default**: 0.5
**Recommended**: 0.9

```sql
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
```

---

## Configuration Variants

### Variant 1: Default (Baseline)

```conf
# docker-compose default
# No custom configuration
# Use for baseline comparison
```

**Use Case**: Baseline measurement

---

### Variant 2: Conservative Optimization

Modest improvements, production-safe.

```conf
shared_buffers = 2GB
effective_cache_size = 8GB
work_mem = 32MB
maintenance_work_mem = 512MB

random_page_cost = 1.1
effective_io_concurrency = 200

max_parallel_workers_per_gather = 2
max_worker_processes = 8

max_connections = 200
```

**Use Case**: Safe production settings

---

### Variant 3: Aggressive Optimization

Maximum performance, may need more resources.

```conf
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 1GB

random_page_cost = 1.1
effective_io_concurrency = 200
default_statistics_target = 500

max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_worker_processes = 12

max_connections = 200

wal_buffers = 16MB
checkpoint_completion_target = 0.9
```

**Use Case**: Dedicated database server

---

### Variant 4: Extreme (Benchmark-Specific)

Tuned specifically for benchmark workload.

```conf
# Memory (assumes 16GB RAM)
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 128MB
maintenance_work_mem = 2GB

# SSD optimization
random_page_cost = 1.1
effective_io_concurrency = 200
seq_page_cost = 1.0

# Query planning
default_statistics_target = 1000
enable_seqscan = on
enable_indexscan = on
enable_bitmapscan = on

# Parallelism (8-core system)
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_worker_processes = 12
parallel_tuple_cost = 0.01
parallel_setup_cost = 100

# Connections
max_connections = 200

# WAL
wal_buffers = 32MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB
min_wal_size = 1GB

# Logging (disable for benchmark)
log_statement = 'none'
log_duration = off
```

**Use Case**: Maximum performance testing

---

## Index Optimization

### Existing Indexes

Review current indexes:

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('air_instance_lookup', 'ship_instance_lookup', 'kb_relationships')
ORDER BY tablename, indexname;
```

### Covering Indexes

Ensure covering indexes for hot queries:

```sql
-- Already in schema:
CREATE INDEX idx_air_mode_s_covering ON air_instance_lookup (mode_s)
    INCLUDE (shark_name, platform, affiliation, nationality, operator, air_type, air_model);
```

**Benefit**: Index-only scans (no heap access)

### Index Validation

Check index usage:

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### Missing Indexes

Check for missing indexes:

```sql
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE tablename = 'air_instance_lookup'
ORDER BY n_distinct DESC;
```

---

## Query-Specific Optimization

### S1: Identifier Lookups

**Query:**
```sql
SELECT * FROM air_instance_lookup WHERE mode_s = 'A12345';
```

**Optimization:**
- Covering index (already in place)
- Ensure index-only scan

**Verify:**
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT shark_name, platform FROM air_instance_lookup WHERE mode_s = 'A12345';
```

**Target**: Index-only scan, <5ms

---

### S3: Two-Hop Traversal

**Query:**
```sql
SELECT a.shark_name, o.name, l.name
FROM air_instance_lookup a
JOIN kb_relationships r1 ON r1.source_id = a.id
JOIN organizations o ON r1.target_id = o.id
JOIN kb_relationships r2 ON r2.source_id = o.id
JOIN locations l ON r2.target_id = l.id
WHERE r1.relationship_type = 'OPERATED_BY'
  AND r2.relationship_type = 'HEADQUARTERED_AT'
  AND l.country = 'USA';
```

**Optimization:**
- Composite indexes on kb_relationships
- Hash join for large result sets

**Verify:**
```sql
EXPLAIN (ANALYZE, BUFFERS) [full query];
```

**Target**: Hash join, <50ms

---

## Maintenance

### VACUUM and ANALYZE

**Schedule:**
```sql
-- Autovacuum (should be enabled)
ALTER SYSTEM SET autovacuum = on;
ALTER SYSTEM SET autovacuum_max_workers = 3;

-- Manual for benchmark preparation
VACUUM ANALYZE air_instance_lookup;
VACUUM ANALYZE ship_instance_lookup;
VACUUM ANALYZE kb_relationships;
```

### REINDEX

**When**: After bulk data load

```sql
REINDEX TABLE air_instance_lookup;
REINDEX TABLE ship_instance_lookup;
REINDEX TABLE kb_relationships;
```

---

## Monitoring

### Key Metrics

```sql
-- Cache hit ratio (target: >99%)
SELECT
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) AS cache_hit_ratio
FROM pg_statio_user_tables;

-- Index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Slow queries
SELECT
    query,
    calls,
    total_time / calls AS avg_time,
    max_time,
    stddev_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

### pg_stat_statements

**Enable:**
```sql
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.track = all;
```

**Restart required**

---

## Testing Protocol

### 1. Apply Configuration

```bash
# Copy config file
docker cp optimized.conf shark-postgres:/etc/postgresql/postgresql.conf

# Reload (for most settings)
docker exec shark-postgres psql -U shark -d sharkdb -c "SELECT pg_reload_conf();"

# Restart (for some settings like shared_buffers)
docker restart shark-postgres
```

### 2. Warm-up

```bash
cd ../../benchmark/harness
python runner.py http://localhost:8080 --pattern lookup-95 --requests 5000
```

### 3. Benchmark

```bash
python runner.py http://localhost:8080 \
  --pattern balanced-50 \
  --requests 50000 \
  --concurrency 20 \
  --output ../analysis/phase-a-optimization/postgresql/results/optimized
```

### 4. Compare

```bash
python compare_results.py \
  baseline.csv \
  optimized.csv
```

---

## Expected Improvements

| Query Type | Baseline (p99) | Optimized (p99) | Improvement |
|------------|----------------|-----------------|-------------|
| Identifier Lookup | 15ms | 8ms | 47% |
| Two-Hop Traversal | 80ms | 50ms | 38% |
| Three-Hop Traversal | 150ms | 100ms | 33% |

---

## Troubleshooting

### Out of Memory Errors

**Symptom**: Queries fail with OOM
**Solution**: Reduce work_mem, increase max_connections

### Slow Index Scans

**Symptom**: Index scans slower than expected
**Solution**: REINDEX, increase random_page_cost slightly

### High CPU Usage

**Symptom**: CPU at 100%
**Solution**: Reduce max_parallel_workers_per_gather

### Slow Writes

**Symptom**: INSERT/UPDATE slow
**Solution**: Increase wal_buffers, adjust checkpoint settings

---

## Production Recommendations

Based on benchmark results:

1. **Use Variant 3** (Aggressive Optimization) as starting point
2. **Monitor** cache hit ratio, index usage, slow queries
3. **Adjust** work_mem based on actual query complexity
4. **Enable** pg_stat_statements for ongoing monitoring
5. **Schedule** VACUUM ANALYZE regularly

---

## References

- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [PostgreSQL Configuration](https://www.postgresql.org/docs/current/runtime-config.html)
- [pgtune](https://pgtune.leopard.in.ua/) - Configuration generator
