# Phase 12: Mitigation (Conditional)

**Goal**: If the selected database fails or conditionally passes thresholds, implement and test mitigation strategies to achieve compliance.

**Status**: CONDITIONAL - Only execute if Phase C winner needs mitigation

## When to Execute This Phase

Execute Phase 12 if the winner from Phase C has:

- ✗ **FAIL** status - Exceeds p99 thresholds, mitigation required
- ⚠ **CONDITIONAL_PASS** status - Needs caching/optimization to meet thresholds
- ✓ **PASS** status - Skip this phase, proceed to Phase 13

## Mitigation Strategies

### Strategy 1: Redis Caching (Primary)

**Goal**: Reduce latency by caching hot queries

**Applicable When:**
- Winner has acceptable base performance (within 20% of thresholds)
- Workload has high cache hit potential (>80% identical lookups)
- Latency reduction needed: 20-50%

**Implementation:**
- Cache identifier lookups (S1) - TTL: 5-15 minutes
- Cache hot graph traversals (S3, S4) - TTL: 2-5 minutes
- Use Redis with LRU eviction policy
- Monitor cache hit rate (target: >80%)

**Expected Improvement:** 30-50% latency reduction for cached queries

**Risk:** Cache invalidation complexity, stale data

---

### Strategy 2: Query Optimization (Secondary)

**Goal**: Optimize slow queries to reduce database load

**Applicable When:**
- Specific queries significantly slower than others
- Index improvements possible
- Query rewrite opportunities exist

**Implementation:**
- Profile slow queries (EXPLAIN/PROFILE)
- Add covering indexes if missing
- Rewrite inefficient queries
- Optimize join order (PostgreSQL)
- Use query hints if needed

**Expected Improvement:** 10-30% latency reduction

**Risk:** Schema changes may break existing code

---

### Strategy 3: Hybrid Architecture (Fallback)

**Goal**: Use multiple databases for different purposes

**Applicable When:**
- No single database meets all requirements
- PostgreSQL fast for lookups, Neo4j good for curation
- Performance + curation trade-off unresolved

**Implementation:**
- **Option A**: PostgreSQL (queries) + Neo4j Community (curation UI)
- **Option B**: Memgraph (queries) + PostgreSQL (reporting)
- Sync mechanism between databases (Kafka, ETL)

**Expected Improvement:** Combines strengths of both databases

**Risk:** High complexity, data consistency challenges

---

### Strategy 4: Threshold Relaxation (Last Resort)

**Goal**: Adjust thresholds based on real-world requirements

**Applicable When:**
- All mitigation strategies fail
- Current thresholds too aggressive
- Business can accept higher latency

**Implementation:**
- Document why current thresholds unrealistic
- Propose revised thresholds with justification
- Get stakeholder approval
- Re-assess with new thresholds

**Expected Improvement:** Database passes with relaxed thresholds

**Risk:** May not meet user expectations

---

## Mitigation Decision Tree

```
START: Winner from Phase C fails/conditional pass thresholds

├─ Is winner within 20% of p99 thresholds?
│  ├─ YES → Try Strategy 1 (Redis Caching)
│  │  └─ Test with caching
│  │     ├─ Passes thresholds? → SUCCESS, use caching
│  │     └─ Still fails? → Try Strategy 2 (Query Optimization)
│  │
│  └─ NO (>20% over threshold) → Consider Strategy 3 (Hybrid) or Strategy 4 (Relax)

├─ After Strategy 2: Query Optimization
│  ├─ Passes thresholds? → SUCCESS, deploy optimizations
│  └─ Still fails? → Try Strategy 3 (Hybrid)

├─ After Strategy 3: Hybrid Architecture
│  ├─ Acceptable complexity? → SUCCESS, implement hybrid
│  └─ Too complex? → Strategy 4 (Threshold Relaxation)

└─ Strategy 4: Threshold Relaxation
   └─ Get stakeholder approval → Update decision, proceed to Phase 13
```

---

## Testing Protocol

### 1. Baseline Measurement

Before mitigation, establish baseline:

```bash
cd ../../benchmark/harness
python runner.py http://localhost:8080 \
  --pattern balanced-50 \
  --requests 50000 \
  --concurrency 20 \
  --output ../../analysis/phase-12-mitigation/baseline_before_mitigation.csv
```

**Record:**
- p99 latency for each query type
- Threshold gap (how much over threshold)
- Cache hit rate: 0% (no caching yet)

---

### 2. Strategy 1: Redis Caching

**Implementation Steps:**

```bash
# 1. Start Redis
docker run -d --name shark-redis -p 6379:6379 redis:7-alpine

# 2. Update Rust app to enable Redis caching
# Edit implementations/rust/.env:
REDIS_URL=redis://localhost:6379
CACHE_TTL_SECONDS=300

# 3. Rebuild and restart Rust API
cd implementations/rust
cargo build --release
cargo run --release

# 4. Warm up cache
cd ../../benchmark/harness
python runner.py http://localhost:8080 \
  --pattern lookup-95 \
  --requests 10000 \
  --concurrency 10

# 5. Test with cache warm
python runner.py http://localhost:8080 \
  --pattern balanced-50 \
  --requests 50000 \
  --concurrency 20 \
  --output ../../analysis/phase-12-mitigation/caching/with_redis_cache.csv
```

**Success Criteria:**
- p99 latency < threshold for all query types
- Cache hit rate > 80%
- Latency reduction > 30%

**If Successful:**
- ✅ Document caching configuration
- ✅ Update decision document
- ✅ Proceed to Phase 13

**If Unsuccessful:**
- → Try Strategy 2 (Query Optimization)

---

### 3. Strategy 2: Query Optimization

**For PostgreSQL:**

```sql
-- Identify slow queries
SELECT query, calls, mean_exec_time, max_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 10
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Add covering indexes
CREATE INDEX IF NOT EXISTS idx_covering_example
ON air_instance_lookup (mode_s)
INCLUDE (shark_name, platform, affiliation);

-- Reindex
REINDEX TABLE air_instance_lookup;
VACUUM ANALYZE air_instance_lookup;
```

**For Neo4j:**

```cypher
// Check slow queries
CALL dbms.listQueries() YIELD query, elapsedTimeMillis
WHERE elapsedTimeMillis > 10
RETURN query, elapsedTimeMillis
ORDER BY elapsedTimeMillis DESC;

// Optimize with query hints
MATCH (a:Aircraft {mode_s: $mode_s})
USING INDEX a:Aircraft(mode_s)
RETURN a;

// Update statistics
CALL db.stats.collect();
```

**For Memgraph:**

```cypher
// Profile slow query
PROFILE MATCH (a:Aircraft {mode_s: $mode_s})
RETURN a;

// Add index if missing
CREATE INDEX ON :Aircraft(mode_s);

// Verify index usage
SHOW INDEX INFO;
```

**Re-test after optimization:**

```bash
python runner.py http://localhost:8080 \
  --pattern balanced-50 \
  --requests 50000 \
  --concurrency 20 \
  --output ../../analysis/phase-12-mitigation/query-optimization/after_optimization.csv
```

---

### 4. Strategy 3: Hybrid Architecture

**Option A: PostgreSQL (queries) + Neo4j (curation)**

```
Architecture:
┌─────────────────────────────────────────────┐
│  Application Layer                          │
├─────────────────────────────────────────────┤
│  Rust API (8080)                            │
│  ├─ /api/query/* → PostgreSQL (fast lookup)│
│  └─ /api/curate/* → Neo4j (graph UI)       │
├─────────────────────────────────────────────┤
│  Data Layer                                 │
│  ├─ PostgreSQL (primary query store)       │
│  └─ Neo4j Community (curation interface)   │
├─────────────────────────────────────────────┤
│  Sync Layer                                 │
│  └─ Kafka CDC → Both databases             │
└─────────────────────────────────────────────┘
```

**Implementation:**
1. Keep PostgreSQL for query API
2. Add Neo4j Community Edition for curation
3. Implement bidirectional sync via Kafka
4. Route queries based on use case

**Complexity:** High
**Cost:** Medium (two databases to maintain)
**Benefit:** Best of both worlds

**Test hybrid performance:**
- Query latency from PostgreSQL
- Curation workflow in Neo4j
- Verify data consistency between databases

---

## Deliverables

### 1. Mitigation Test Report

**Template:**

```markdown
# Mitigation Strategy Test Report

## Strategy Tested: [Redis Caching / Query Optimization / Hybrid]

### Baseline (Before Mitigation)
- p99 Identifier Lookup: [X]ms (threshold: 100ms) - [PASS/FAIL]
- p99 Two-Hop Traversal: [X]ms (threshold: 300ms) - [PASS/FAIL]
- p99 Three-Hop Traversal: [X]ms (threshold: 500ms) - [PASS/FAIL]

### After Mitigation
- p99 Identifier Lookup: [X]ms → [PASS/FAIL]
- p99 Two-Hop Traversal: [X]ms → [PASS/FAIL]
- p99 Three-Hop Traversal: [X]ms → [PASS/FAIL]

### Improvement
- Identifier Lookup: [X]% improvement
- Two-Hop Traversal: [X]% improvement
- Three-Hop Traversal: [X]% improvement

### Cache Metrics (if applicable)
- Cache hit rate: [X]%
- Cache size: [X] MB
- Eviction rate: [X]/sec

### Recommendation
- [ACCEPT / REJECT] mitigation strategy
- Rationale: [Why accept or reject]

### Next Steps
- [Proceed to Phase 13 / Try next strategy]
```

### 2. Updated Decision Document

Update `FINAL_DECISION.md` to include:
- Mitigation strategy selected
- Test results showing threshold compliance
- Updated risk assessment
- Implementation requirements (e.g., Redis deployment)

### 3. Deployment Guide

Document production deployment requirements:

**For Redis Caching:**
```yaml
# docker-compose.yml addition
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru

volumes:
  redis-data:
```

**For Query Optimization:**
- List of indexes to create
- Configuration changes
- Migration scripts

**For Hybrid:**
- Complete architecture diagram
- Sync mechanism details
- Deployment order and dependencies

---

## Success Criteria

Phase 12 is successful when:

1. ✅ Mitigation strategy implemented and tested
2. ✅ All p99 thresholds met (or relaxed with approval)
3. ✅ Performance improvement quantified
4. ✅ Production deployment plan documented
5. ✅ Updated decision document approved
6. ✅ Ready for Phase 13 (Final Report)

## Common Issues

### "Redis caching not helping enough"

**Possible Causes:**
- Low cache hit rate (<50%)
- Workload has high query diversity
- Cache TTL too short

**Solutions:**
- Increase cache TTL
- Cache more query types
- Try query optimization instead

### "Query optimization breaks existing functionality"

**Solutions:**
- Test in staging environment first
- Use non-breaking index additions
- Version database schema changes

### "Hybrid too complex to maintain"

**Solutions:**
- Simplify to single database
- Relax thresholds if business acceptable
- Use managed services to reduce operational burden

---

## Timeline

**Strategy 1 (Redis Caching):** 2-3 days
- Day 1: Implement caching in Rust app
- Day 2: Test and measure improvement
- Day 3: Document and update decision

**Strategy 2 (Query Optimization):** 3-5 days
- Day 1-2: Profile and optimize queries
- Day 3-4: Test improvements
- Day 5: Document changes

**Strategy 3 (Hybrid):** 1-2 weeks
- Week 1: Design and implement sync
- Week 2: Test data consistency and performance

**Strategy 4 (Threshold Relaxation):** 1-2 days
- Day 1: Document justification
- Day 2: Get stakeholder approval

---

## Next Phase

After successful mitigation:

**Phase 13: Final Report**
- Document complete project journey
- Include mitigation results
- Provide production deployment guide
- Executive summary for stakeholders

---

## References

- [Phase C Decision](../phase-c-decision/FINAL_DECISION.md) - Identified mitigation need
- [Redis Configuration](https://redis.io/docs/management/optimization/)
- [PostgreSQL Query Optimization](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Neo4j Query Tuning](https://neo4j.com/docs/cypher-manual/current/query-tuning/)
