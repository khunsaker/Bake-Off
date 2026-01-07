# Memgraph Optimization Guide

Comprehensive guide to tuning Memgraph for Shark Bake-Off benchmark workloads.

## Current Configuration (Baseline)

From `docker-compose.yml`:
- Image: `memgraph/memgraph-platform:latest`
- Default Memgraph configuration
- In-memory graph database (no persistent storage optimization needed)

## System Resources

Assumed environment (adjust for your hardware):
- **CPU**: 4-8 cores
- **RAM**: 16 GB (all available for Memgraph)
- **Storage**: Disk only for persistence (WAL, snapshots)
- **Network**: 1 Gbps

## Key Differences from Neo4j

### In-Memory Architecture

**Memgraph**: Entire graph stored in RAM (no page cache)
**Neo4j**: Disk-based with page cache

**Implication**: Memgraph requires sufficient RAM to hold entire dataset + working memory.

### MVCC (Multi-Version Concurrency Control)

**Memgraph**: Supports true concurrent reads and writes without locks
**Neo4j**: Lock-based concurrency

**Implication**: Better concurrent write performance in Memgraph.

### Query Execution

**Memgraph**: Built-in query parallelism for complex queries
**Neo4j**: Sequential execution (mostly)

**Implication**: Potential performance advantage for multi-hop traversals.

---

## Optimization Strategy

### 1. Memory Configuration

Memgraph is **fully in-memory**, so memory sizing is critical.

#### Memory Requirements

**Formula:**
```
Total RAM needed = Graph data + Indexes + Working memory + OS overhead
```

**Components:**
- **Graph data**: Nodes + Relationships + Properties
- **Indexes**: Index structures (smaller than graph)
- **Working memory**: Query execution, transactions
- **OS overhead**: ~1-2 GB

#### Memory Limits

**Configuration:**
```
--memory-limit=12GB
```

**Recommendation**: 75% of total RAM (for 16GB system = 12GB)

**Rationale**: Leave 4GB for OS and other processes.

#### Memory Warning Threshold

**Configuration:**
```
--memory-warning-threshold=10GB
```

**Recommendation**: 85% of memory limit

**Rationale**: Get warnings before hitting hard limit.

---

### 2. Query Execution

#### Parallel Execution

**Purpose**: Parallelize complex queries across CPU cores

**Configuration:**
```
--query-execution-timeout-sec=120
--query-max-plans=1000
```

**Rationale**: Allow complex queries to explore multiple execution plans.

#### Query Caching

**Purpose**: Cache compiled query plans

**Configuration:**
```
--query-plan-cache-size=10000
```

**Recommendation**: 10000 (benchmark has limited distinct queries)

#### Query Timeout

**Configuration:**
```
--query-execution-timeout-sec=120
```

**Recommendation**: 120 seconds for complex analytics queries

---

### 3. Storage Configuration

Even though Memgraph is in-memory, it persists data to disk via **WAL** (Write-Ahead Log) and **snapshots**.

#### WAL (Write-Ahead Log)

**Purpose**: Durability for writes

**Configuration:**
```
--storage-wal-enabled=true
--storage-snapshot-interval-sec=300
```

**Recommendation**: Enable WAL, but increase snapshot interval to reduce I/O overhead.

**Rationale**: Benchmark is read-heavy. Less frequent snapshots = less overhead.

#### Snapshot Configuration

**Configuration:**
```
--storage-snapshot-on-exit=true
--storage-recover-on-startup=true
```

**Recommendation**: Enable for data persistence between restarts.

---

### 4. Concurrency

#### Worker Threads

**Purpose**: Handle concurrent Bolt connections

**Configuration:**
```
--bolt-num-workers=16
```

**Recommendation**: CPU cores × 2 (for 8-core system = 16)

**Rationale**: Handle 20-50 concurrent benchmark connections.

#### Session Idle Timeout

**Configuration:**
```
--bolt-session-inactivity-timeout=3600
```

**Recommendation**: 1 hour (avoid premature disconnections during benchmark)

---

### 5. Index Configuration

Memgraph uses **label+property indexes** similar to Neo4j.

#### Index Types

**Label Index**: Automatically created for each label
**Label+Property Index**: Manually created for specific lookups

**Already configured in schema:**
```cypher
CREATE INDEX ON :Aircraft(mode_s);
CREATE INDEX ON :Ship(mmsi);
CREATE INDEX ON :Organization(name);
CREATE INDEX ON :Location(country);
```

#### Index Usage

**Verification:**
```cypher
SHOW INDEX INFO;
```

**Query Plan:**
```cypher
EXPLAIN MATCH (a:Aircraft {mode_s: 'A12345'}) RETURN a;
```

**Look for**: `ScanAllByLabelPropertyValue` (index usage)

---

### 6. Transaction Configuration

#### Isolation Level

**Default**: Snapshot Isolation (MVCC)
**Alternative**: Read Committed

**Configuration:**
```
--isolation-level=SNAPSHOT_ISOLATION
```

**Recommendation**: Keep default (Snapshot Isolation) for consistent reads.

#### Transaction Timeout

**Configuration:**
```
--storage-properties-on-edges=true
```

**Recommendation**: Enable (needed for relationship properties).

---

## Configuration Variants

### Variant 1: Default (Baseline)

```bash
# Minimal flags
--memory-limit=8GB
--bolt-num-workers=8
```

**Use Case**: Baseline measurement

---

### Variant 2: Conservative Optimization

Modest improvements, production-safe.

```bash
# Memory (16GB RAM system)
--memory-limit=10GB
--memory-warning-threshold=8GB

# Query
--query-execution-timeout-sec=120
--query-plan-cache-size=5000

# Concurrency
--bolt-num-workers=8

# Storage
--storage-wal-enabled=true
--storage-snapshot-interval-sec=600
--storage-properties-on-edges=true

# Isolation
--isolation-level=SNAPSHOT_ISOLATION
```

**Use Case**: Safe production settings

---

### Variant 3: Aggressive Optimization

Maximum performance, dedicated server.

```bash
# Memory (16GB RAM system - aggressive)
--memory-limit=12GB
--memory-warning-threshold=10GB

# Query optimization
--query-execution-timeout-sec=120
--query-plan-cache-size=10000
--query-max-plans=1000

# Concurrency (8-core system)
--bolt-num-workers=16

# Storage (reduce I/O overhead)
--storage-wal-enabled=true
--storage-snapshot-interval-sec=600
--storage-snapshot-on-exit=true
--storage-recover-on-startup=true
--storage-properties-on-edges=true

# Isolation
--isolation-level=SNAPSHOT_ISOLATION

# Logging (reduced)
--log-level=WARNING
```

**Use Case**: Dedicated database server

---

### Variant 4: Extreme (Benchmark-Specific)

Tuned specifically for benchmark workload.

```bash
# Memory (16GB RAM - maximum for in-memory)
--memory-limit=14GB
--memory-warning-threshold=12GB

# Query optimization (aggressive caching)
--query-execution-timeout-sec=300
--query-plan-cache-size=10000
--query-max-plans=1000

# Concurrency (maximum parallelism)
--bolt-num-workers=20
--bolt-session-inactivity-timeout=7200

# Storage (minimize I/O for read-heavy benchmark)
--storage-wal-enabled=true
--storage-snapshot-interval-sec=3600
--storage-snapshot-on-exit=true
--storage-recover-on-startup=true
--storage-properties-on-edges=true

# Isolation (snapshot for consistency)
--isolation-level=SNAPSHOT_ISOLATION

# Logging (minimal for performance)
--log-level=ERROR

# Experimental
--cartesian-product-enabled=false
```

**Use Case**: Maximum performance testing

---

## Query Optimization

### Cypher Query Patterns

Memgraph uses Cypher (same as Neo4j), so query patterns are similar.

#### S1: Identifier Lookups

**Query:**
```cypher
MATCH (a:Aircraft {mode_s: 'A12345'})
RETURN a.shark_name, a.platform, a.affiliation, a.nationality;
```

**Optimization:**
- Index on `mode_s` (already exists)
- In-memory lookup = very fast

**Target**: <3ms (faster than Neo4j due to in-memory)

---

#### S3: Two-Hop Traversal

**Query:**
```cypher
MATCH (a:Aircraft)-[:OPERATED_BY]->(o:Organization)-[:HEADQUARTERED_AT]->(l:Location)
WHERE a.mode_s = 'A12345' AND l.country = 'USA'
RETURN a.shark_name, o.name, l.name;
```

**Optimization:**
- Index on `a.mode_s` and `l.country`
- In-memory traversal (no disk I/O)
- Potential parallel execution

**Target**: <15ms (faster than Neo4j)

---

#### S4: Three-Hop Traversal

**Query:**
```cypher
MATCH (a:Aircraft)-[:OPERATED_BY]->(o:Organization)-[:PART_OF]->(p:Organization)-[:HEADQUARTERED_AT]->(l:Location)
WHERE a.mode_s = 'A12345'
RETURN a.shark_name, o.name, p.name, l.name;
```

**Optimization:**
- Same as S3
- Memgraph's parallel execution may help

**Target**: <35ms

---

## Index Optimization

### Existing Indexes

Review current indexes:

```cypher
SHOW INDEX INFO;
```

Expected output:
```
+---------------+----------+-----------+
| index type    | label    | property  |
+---------------+----------+-----------+
| label+property| Aircraft | mode_s    |
| label+property| Ship     | mmsi      |
| label+property| Org      | name      |
| label+property| Location | country   |
+---------------+----------+-----------+
```

### Composite Indexes

Memgraph supports **composite indexes** (multi-property):

```cypher
CREATE INDEX ON :Aircraft(nationality, air_type);
```

**Benchmark Note**: Current queries use single-property lookups. Not needed yet.

---

## Monitoring

### Memory Usage

```cypher
SHOW STORAGE INFO;
```

Returns:
- Nodes count
- Relationships count
- Memory usage
- Disk usage (WAL + snapshots)

### Query Performance

Enable query logging:

```bash
--log-level=TRACE
--log-file=/var/log/memgraph/memgraph.log
```

**Note**: Disable during benchmark for best performance.

### Active Transactions

```cypher
SHOW TRANSACTIONS;
```

Returns:
- Transaction ID
- Username
- Query text
- Elapsed time

---

## Testing Protocol

### 1. Apply Configuration

**Via Docker Compose:**

Edit `docker-compose.yml`:

```yaml
services:
  memgraph:
    image: memgraph/memgraph-platform:latest
    ports:
      - "7688:7687"
      - "3000:3000"
    command:
      - "--memory-limit=12GB"
      - "--memory-warning-threshold=10GB"
      - "--query-plan-cache-size=10000"
      - "--bolt-num-workers=16"
      - "--storage-wal-enabled=true"
      - "--storage-snapshot-interval-sec=600"
      - "--storage-properties-on-edges=true"
      - "--log-level=WARNING"
```

**Restart:**
```bash
docker-compose restart memgraph
```

**Verify:**
```cypher
SHOW CONFIG;
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
  --output ../analysis/phase-a-optimization/memgraph/results/optimized
```

### 4. Compare

```bash
python compare_results.py \
  baseline.csv \
  optimized.csv
```

---

## Expected Improvements

Based on Memgraph's in-memory architecture:

| Query Type | Baseline (p99) | Optimized (p99) | Improvement | vs Neo4j |
|------------|----------------|-----------------|-------------|----------|
| Identifier Lookup | 8ms | 4ms | 50% | 33% faster |
| Two-Hop Traversal | 20ms | 12ms | 40% | 33% faster |
| Three-Hop Traversal | 40ms | 25ms | 38% | 29% faster |

**Key Advantage**: No disk I/O = more consistent latency (lower p99-p50 gap).

---

## Troubleshooting

### Out of Memory Errors

**Symptom**: `OutOfMemoryException`

**Solution**: Reduce memory limit or increase available RAM

```bash
--memory-limit=10GB
```

**Check memory usage:**
```cypher
SHOW STORAGE INFO;
```

### Slow Queries

**Symptom**: Queries slower than expected

**Solution**:
1. Check index usage: `EXPLAIN` query
2. Ensure indexes exist: `SHOW INDEX INFO`
3. Verify in-memory: `SHOW STORAGE INFO` (all data should be in RAM)

### Connection Timeouts

**Symptom**: Bolt connection timeouts

**Solution**: Increase worker threads or session timeout

```bash
--bolt-num-workers=20
--bolt-session-inactivity-timeout=7200
```

### Snapshot Overhead

**Symptom**: Periodic latency spikes

**Solution**: Increase snapshot interval

```bash
--storage-snapshot-interval-sec=3600
```

---

## Memgraph-Specific Advantages

### 1. In-Memory Performance

**Advantage**: No disk I/O for graph traversal
**Benefit**: Lower latency, more consistent performance

### 2. MVCC Concurrency

**Advantage**: Lock-free reads and writes
**Benefit**: Better concurrent performance under load

### 3. Query Parallelism

**Advantage**: Automatic query parallelization
**Benefit**: Faster complex queries (multi-hop traversals)

### 4. Simple Configuration

**Advantage**: Fewer tuning parameters than Neo4j or PostgreSQL
**Benefit**: Easier to optimize

---

## Memgraph vs Neo4j

### When Memgraph is Better

- **Dataset fits in RAM**: Memgraph's in-memory architecture shines
- **Concurrent writes**: MVCC provides better write concurrency
- **Latency consistency**: No disk I/O = more predictable performance

### When Neo4j is Better

- **Large datasets**: Neo4j's disk-based architecture handles graphs larger than RAM
- **Enterprise features**: Neo4j Enterprise has more mature tooling
- **Ecosystem**: Neo4j has larger community and more integrations

### Benchmark Context

**Dataset size**: ~100K nodes, ~500K relationships (~500MB)
**Fits in RAM**: Yes (easily)
**Expected winner**: Memgraph (in-memory advantage)

---

## Production Recommendations

Based on benchmark results:

1. **Use Variant 3** (Aggressive Optimization) as starting point
2. **Monitor** memory usage closely - ensure dataset + working memory < limit
3. **Plan for growth**: If dataset grows beyond available RAM, switch to Neo4j
4. **Snapshots**: Balance durability vs performance (longer intervals = better performance)
5. **Backup strategy**: Regular snapshots to disk for disaster recovery

---

## Limitations

### RAM Requirement

**Critical**: Entire graph must fit in RAM
**Risk**: If dataset grows beyond available RAM, Memgraph will fail

**Mitigation**: Monitor data growth, plan for Neo4j migration if needed.

### Persistence Overhead

**WAL writes**: Still have disk I/O for write durability
**Snapshots**: Periodic snapshots can cause latency spikes

**Mitigation**: Tune snapshot intervals, use fast SSD for WAL.

### Enterprise Features

**Community Edition**: Limited compared to Neo4j Enterprise
**No**: Read replicas, causal clustering, role-based access control

---

## Advanced Tuning

### Custom Procedures

Memgraph supports **custom procedures** (similar to Neo4j's APOC):

```cypher
CALL custom.procedure() YIELD result;
```

**Benchmark Note**: Not needed for current queries.

### Triggers

Memgraph supports **triggers** for data changes:

```cypher
CREATE TRIGGER audit_changes
ON CREATE AFTER COMMIT EXECUTE
...
```

**Benchmark Note**: Disable triggers during benchmark for best performance.

---

## Verification Checklist

Before running benchmark:

- [ ] Memory limit set appropriately (12-14GB for 16GB system)
- [ ] Indexes created and verified (`SHOW INDEX INFO`)
- [ ] Worker threads configured (16-20 for 8-core system)
- [ ] Snapshot interval increased (600-3600 seconds)
- [ ] Logging reduced (WARNING or ERROR level)
- [ ] Dataset loaded and fits in memory (`SHOW STORAGE INFO`)
- [ ] Warm-up run completed (caches hot)

---

## References

- [Memgraph Documentation](https://memgraph.com/docs)
- [Memgraph Configuration](https://memgraph.com/docs/memgraph/reference-guide/configuration)
- [Memgraph vs Neo4j](https://memgraph.com/memgraph-vs-neo4j)
- [Cypher Query Language](https://memgraph.com/docs/cypher-manual)
