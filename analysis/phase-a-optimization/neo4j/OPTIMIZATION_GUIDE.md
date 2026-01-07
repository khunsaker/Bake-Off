# Neo4j Optimization Guide

Comprehensive guide to tuning Neo4j for Shark Bake-Off benchmark workloads.

## Current Configuration (Baseline)

From `docker-compose.yml`:
- Image: `neo4j:5.15-community`
- Default Neo4j configuration
- No custom tuning

## System Resources

Assumed environment (adjust for your hardware):
- **CPU**: 4-8 cores
- **RAM**: 16 GB
- **Storage**: SSD
- **Network**: 1 Gbps

## Optimization Strategy

### 1. Memory Configuration

Neo4j uses two primary memory pools: **heap memory** (Java objects, query execution) and **page cache** (graph data on disk).

#### Heap Memory

**Purpose**: Query execution, transaction state, Java objects

**Default**: Auto-calculated (typically ~512MB - 1GB)
**Recommended**: 25% of RAM (for 16GB system)
**For 16 GB RAM**: 4 GB

**Configuration:**
```conf
dbms.memory.heap.initial_size=4G
dbms.memory.heap.max_size=4G
```

**Rationale**:
- Larger heap = more complex queries can execute
- Too large = garbage collection pauses
- Rule of thumb: 25% of RAM, max 31GB (compressed oops)

#### Page Cache

**Purpose**: Caching graph data (nodes, relationships, properties) from disk

**Default**: Auto-calculated (typically 50% of remaining RAM)
**Recommended**: 50% of RAM (for 16GB system)
**For 16 GB RAM**: 8 GB

**Configuration:**
```conf
dbms.memory.pagecache.size=8G
```

**Rationale**:
- Larger page cache = fewer disk reads
- Graph data stays hot in memory
- Most important setting for read-heavy workloads

#### Memory Formula

For a system with **T** GB total RAM:
- **Heap**: T × 0.25 (25%)
- **Page Cache**: T × 0.50 (50%)
- **OS + Other**: T × 0.25 (25%)

**Example (16 GB RAM):**
- Heap: 4 GB
- Page Cache: 8 GB
- OS: 4 GB

---

### 2. Query Optimization

#### Query Cache

**Purpose**: Cache parsed Cypher queries

**Default**: 1000 queries
**Recommended**: 10000 queries (for repeated benchmark queries)

**Configuration:**
```conf
dbms.query_cache_size=10000
```

**Rationale**: Benchmark workload has limited distinct queries (S1-S10). Cache all of them.

#### Transaction State

**Purpose**: Memory for concurrent transactions

**Default**: Auto
**Recommended**: 8 GB (for high concurrency)

**Configuration:**
```conf
dbms.memory.transaction.total.max=8G
```

**Rationale**: Allow many concurrent read transactions during benchmark.

---

### 3. Index Configuration

Neo4j uses **native index structures** optimized for graph traversal.

#### Index Providers

**Default**: `range-1.0` (range indexes)
**For Lookups**: `text-2.0` (full-text) or `point-1.0` (geospatial)
**For Exact Match**: `range-1.0` (default, optimal for equality)

**Already configured in schema:**
```cypher
CREATE INDEX air_mode_s_idx FOR (a:Aircraft) ON (a.mode_s);
CREATE INDEX ship_mmsi_idx FOR (s:Ship) ON (s.mmsi);
CREATE INDEX org_name_idx FOR (o:Organization) ON (o.name);
```

**Verification:**
```cypher
SHOW INDEXES;
```

#### Composite Indexes

**Purpose**: Speed up multi-property queries

**Example (if needed):**
```cypher
CREATE INDEX aircraft_composite
FOR (a:Aircraft)
ON (a.nationality, a.air_type);
```

**Benchmark Note**: Current schema has single-property lookups. Composite indexes not needed.

---

### 4. Cypher Query Optimization

#### Query Planning

**Purpose**: Generate optimal query execution plans

**Default**: Cost-based optimizer (CBO)
**Tuning**: Ensure indexes are used

**Verification:**
```cypher
EXPLAIN MATCH (a:Aircraft {mode_s: 'A12345'}) RETURN a;
```

**Look for**: `NodeIndexSeek` (good) vs `NodeByLabelScan` (bad)

#### Eager Evaluation

**Purpose**: Control when query results are materialized

**Default**: Lazy evaluation (stream results)
**For Aggregations**: Eager (must collect all)

**Best Practice**: Avoid `DISTINCT`, `ORDER BY`, `COLLECT` unless necessary.

**Benchmark Queries**: Already optimized (no unnecessary eager operations)

---

### 5. Parallelism and Concurrency

#### Bolt Threads

**Purpose**: Handle concurrent client connections

**Default**: Auto (based on CPU cores)
**Recommended**: CPU cores × 2
**For 8-core system**: 16

**Configuration:**
```conf
dbms.threads.worker_count=16
```

**Rationale**: Handle 20-50 concurrent benchmark connections.

#### Cypher Parallelism

**Purpose**: Parallelize single query execution

**Default**: Disabled for most queries
**Tuning**: Use `CALL { ... } IN TRANSACTIONS` for batch operations

**Benchmark Note**: Parallel Cypher not needed for simple lookups.

---

### 6. Connection Management

#### Bolt Connector

**Purpose**: Handle client connections

**Default**: Enabled on port 7687
**Max Connections**: Unlimited (constrained by threads)

**Configuration:**
```conf
dbms.connector.bolt.enabled=true
dbms.connector.bolt.listen_address=0.0.0.0:7687
```

**Connection Pooling**: Use driver-side pooling (already in Rust implementation).

---

### 7. Write-Ahead Log (Transaction Log)

#### Transaction Log Rotation

**Purpose**: Manage transaction log size

**Default**: 256 MB rotation threshold
**Recommended**: 1 GB (fewer rotations)

**Configuration:**
```conf
dbms.tx_log.rotation.size=1G
```

**Rationale**: Reduce overhead from log rotation during benchmark.

#### Checkpoint Interval

**Purpose**: Flush changes to disk

**Default**: 15 minutes or 100MB of logs
**Recommended**: Default is fine for benchmark

---

## Configuration Variants

### Variant 1: Default (Baseline)

```conf
# No custom configuration
# Use for baseline comparison
```

**Use Case**: Baseline measurement

---

### Variant 2: Conservative Optimization

Modest improvements, production-safe.

```conf
# Memory (16GB RAM system)
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=2G
dbms.memory.pagecache.size=6G

# Query
dbms.query_cache_size=5000

# Concurrency
dbms.threads.worker_count=8

# Transaction log
dbms.tx_log.rotation.size=512M
```

**Use Case**: Safe production settings

---

### Variant 3: Aggressive Optimization

Maximum performance, dedicated database server.

```conf
# Memory (16GB RAM system)
dbms.memory.heap.initial_size=4G
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=8G

# Query
dbms.query_cache_size=10000
dbms.memory.transaction.total.max=8G

# Concurrency
dbms.threads.worker_count=16

# Transaction log
dbms.tx_log.rotation.size=1G

# Performance
dbms.transaction.timeout=120s
dbms.lock.acquisition.timeout=60s
```

**Use Case**: Dedicated database server, benchmark-optimized

---

### Variant 4: Extreme (Benchmark-Specific)

Tuned specifically for benchmark workload.

```conf
# Memory (16GB RAM system)
dbms.memory.heap.initial_size=4G
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=10G

# Query optimization
dbms.query_cache_size=10000
dbms.memory.transaction.total.max=10G

# Cypher optimization
cypher.lenient_create_relationship=false
cypher.hints_error=true

# Concurrency (8-core system)
dbms.threads.worker_count=16

# Transaction log
dbms.tx_log.rotation.size=1G
dbms.checkpoint.interval.time=30m

# Logging (disable for benchmark)
dbms.logs.query.enabled=false
dbms.logs.query.threshold=0

# Statistics
dbms.index_sampling.background_enabled=true
dbms.index_sampling.sample_size_limit=1000000
```

**Use Case**: Maximum performance testing

---

## Index Optimization

### Existing Indexes

Review current indexes:

```cypher
SHOW INDEXES YIELD
  name, type, entityType, labelsOrTypes, properties, state,
  populationPercent, size, provider
RETURN *;
```

### Index Usage Statistics

Check which indexes are used:

```cypher
CALL db.stats.retrieve('QUERIES') YIELD data
UNWIND data AS query
RETURN query.query AS cypher,
       query.count AS executions,
       query.elapsedTimeMillis AS total_time
ORDER BY query.count DESC
LIMIT 10;
```

### Warming Indexes

Ensure indexes are hot in page cache:

```cypher
// Warm up Aircraft index
MATCH (a:Aircraft) WHERE a.mode_s IS NOT NULL RETURN count(a);

// Warm up Ship index
MATCH (s:Ship) WHERE s.mmsi IS NOT NULL RETURN count(s);

// Warm up relationship indexes
MATCH ()-[r:OPERATED_BY]->() RETURN count(r);
```

---

## Query-Specific Optimization

### S1: Identifier Lookups

**Query:**
```cypher
MATCH (a:Aircraft {mode_s: 'A12345'})
RETURN a.shark_name, a.platform, a.affiliation, a.nationality;
```

**Optimization:**
- Index on `mode_s` (already in place)
- Ensure property access is efficient (return only needed properties)

**Verify:**
```cypher
PROFILE MATCH (a:Aircraft {mode_s: 'A12345'})
RETURN a.shark_name, a.platform;
```

**Target**: `NodeIndexSeek`, <5ms

---

### S3: Two-Hop Traversal

**Query:**
```cypher
MATCH (a:Aircraft)-[:OPERATED_BY]->(o:Organization)-[:HEADQUARTERED_AT]->(l:Location)
WHERE a.mode_s = 'A12345' AND l.country = 'USA'
RETURN a.shark_name, o.name, l.name;
```

**Optimization:**
- Index on `a.mode_s` (start point)
- Index on `l.country` (filter)
- Relationship types are indexed automatically

**Verify:**
```cypher
PROFILE MATCH (a:Aircraft)-[:OPERATED_BY]->(o:Organization)-[:HEADQUARTERED_AT]->(l:Location)
WHERE a.mode_s = 'A12345' AND l.country = 'USA'
RETURN a.shark_name, o.name, l.name;
```

**Target**: `NodeIndexSeek` on both ends, <30ms

---

### S4: Three-Hop Traversal

**Query:**
```cypher
MATCH (a:Aircraft)-[:OPERATED_BY]->(o:Organization)-[:PART_OF]->(p:Organization)-[:HEADQUARTERED_AT]->(l:Location)
WHERE a.mode_s = 'A12345'
RETURN a.shark_name, o.name, p.name, l.name;
```

**Optimization:**
- Same as S3
- Ensure relationship cardinality is low (few `:PART_OF` per org)

**Verify:**
```cypher
PROFILE [full query];
```

**Target**: <60ms

---

## Cypher Best Practices

### Use Parameters

**Bad:**
```cypher
MATCH (a:Aircraft {mode_s: 'A12345'}) RETURN a;
```

**Good:**
```cypher
MATCH (a:Aircraft {mode_s: $mode_s}) RETURN a;
```

**Rationale**: Query plan is cached, only parameters change.

### Avoid OPTIONAL MATCH When Possible

**Bad:**
```cypher
MATCH (a:Aircraft {mode_s: $mode_s})
OPTIONAL MATCH (a)-[:OPERATED_BY]->(o)
RETURN a, o;
```

**Good (if relationship is required):**
```cypher
MATCH (a:Aircraft {mode_s: $mode_s})-[:OPERATED_BY]->(o)
RETURN a, o;
```

**Rationale**: `OPTIONAL MATCH` is more expensive.

### Use Direction When Known

**Bad:**
```cypher
MATCH (a:Aircraft)-[:OPERATED_BY]-(o:Organization)
```

**Good:**
```cypher
MATCH (a:Aircraft)-[:OPERATED_BY]->(o:Organization)
```

**Rationale**: Directed traversal is faster.

---

## Maintenance

### Update Statistics

**Schedule**: After data load, before benchmark

```cypher
// Update index statistics
CALL db.index.fulltext.awaitIndex('aircraft_fulltext');

// No explicit ANALYZE needed - Neo4j auto-updates statistics
```

### Compact Store

**When**: After large data modifications

```cypher
// Check store file sizes
CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Store file sizes')
YIELD attributes;
```

**Note**: Community Edition doesn't support online compaction. Use offline `neo4j-admin` if needed.

---

## Monitoring

### Key Metrics

```cypher
// Cache hit ratio (target: >90%)
CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Page cache')
YIELD attributes
RETURN attributes.HitRatio;

// Heap usage
CALL dbms.queryJmx('java.lang:type=Memory')
YIELD attributes
RETURN attributes.HeapMemoryUsage;

// Active transactions
CALL dbms.listTransactions()
YIELD transactionId, elapsedTime, username
RETURN count(*) AS active_transactions;
```

### Query Performance

Enable query logging (not during benchmark):

```conf
dbms.logs.query.enabled=true
dbms.logs.query.threshold=100ms
```

View slow queries:
```bash
tail -f /var/lib/neo4j/logs/query.log
```

---

## Testing Protocol

### 1. Apply Configuration

**Via Docker:**
```bash
# Create config file
cat > neo4j-optimized.conf <<EOF
dbms.memory.heap.initial_size=4G
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=8G
dbms.query_cache_size=10000
dbms.threads.worker_count=16
EOF

# Update docker-compose.yml to mount config
# volumes:
#   - ./neo4j-optimized.conf:/var/lib/neo4j/conf/neo4j.conf

# Restart Neo4j
docker restart shark-neo4j
```

**Verify:**
```cypher
CALL dbms.listConfig()
YIELD name, value
WHERE name CONTAINS 'memory' OR name CONTAINS 'query_cache'
RETURN name, value;
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
  --output ../analysis/phase-a-optimization/neo4j/results/optimized
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
| Identifier Lookup | 12ms | 6ms | 50% |
| Two-Hop Traversal | 30ms | 18ms | 40% |
| Three-Hop Traversal | 60ms | 35ms | 42% |

---

## Troubleshooting

### Out of Memory Errors

**Symptom**: `OutOfMemoryError: Java heap space`
**Solution**: Increase heap size, reduce query cache, or reduce concurrent transactions

```conf
dbms.memory.heap.max_size=6G
dbms.memory.transaction.total.max=6G
```

### Slow Queries

**Symptom**: Queries slower than expected
**Solution**:
1. Check index usage with `PROFILE`
2. Ensure indexes exist: `SHOW INDEXES`
3. Warm up page cache
4. Check page cache hit ratio (target >90%)

### High GC Pauses

**Symptom**: Long garbage collection pauses
**Solution**:
1. Increase heap size (up to 31GB max)
2. Tune GC settings (G1GC is default, optimal for most cases)
3. Reduce transaction memory

### Connection Timeouts

**Symptom**: Bolt connection timeouts under load
**Solution**: Increase worker threads

```conf
dbms.threads.worker_count=32
```

---

## Production Recommendations

Based on benchmark results:

1. **Use Variant 3** (Aggressive Optimization) as starting point
2. **Monitor** page cache hit ratio (target >90%), heap usage, query times
3. **Adjust** heap vs page cache based on workload (more complex queries = more heap)
4. **Enable** query logging in production for slow query detection
5. **Schedule** index warming after restarts
6. **Use** parameters in all Cypher queries for plan caching

---

## Neo4j-Specific Advantages

### Schema Flexibility

**No DDL required**: Add properties or relationship types instantly

```cypher
// Add new property (no ALTER needed)
MATCH (a:Aircraft {mode_s: 'A12345'})
SET a.new_property = 'value';

// Add new relationship type (no schema change)
MATCH (a:Aircraft), (b:Base)
WHERE a.mode_s = 'A12345' AND b.name = 'Edwards AFB'
CREATE (a)-[:STATIONED_AT]->(b);
```

**Self-service for curators**: No DBA intervention needed.

### Relationship Performance

**First-class relationships**: O(1) traversal via relationship pointers

**vs PostgreSQL**: Requires join tables, indexes on foreign keys, query planner optimization

### Visualization

**Neo4j Bloom**: Built-in graph visualization
**Neo4j Browser**: Interactive query and exploration

---

## Advanced Tuning (If Needed)

### JVM Tuning

**Garbage Collector**: Default G1GC is optimal for most cases

**If needed:**
```conf
dbms.jvm.additional=-XX:+UseG1GC
dbms.jvm.additional=-XX:MaxGCPauseMillis=200
dbms.jvm.additional=-XX:InitiatingHeapOccupancyPercent=45
```

### APOC Procedures

**If using APOC** for advanced algorithms:

```conf
dbms.security.procedures.unrestricted=apoc.*
dbms.security.procedures.whitelist=apoc.*
```

**Note**: Benchmark queries don't currently use APOC.

### Read Replicas (Enterprise Only)

**For extreme read scalability**:
- 1 primary (writes)
- 2-3 read replicas (queries)
- Load balance across replicas

**Not applicable**: Community Edition

---

## References

- [Neo4j Performance Tuning](https://neo4j.com/docs/operations-manual/current/performance/)
- [Neo4j Memory Configuration](https://neo4j.com/docs/operations-manual/current/performance/memory-configuration/)
- [Cypher Query Tuning](https://neo4j.com/docs/cypher-manual/current/query-tuning/)
- [Neo4j Indexing](https://neo4j.com/docs/cypher-manual/current/indexes-for-search-performance/)
