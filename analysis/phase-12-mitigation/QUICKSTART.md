# Phase 12: Mitigation - Quick Start

Test and validate mitigation strategies to meet performance thresholds.

## When to Use This Phase

**ONLY if Phase C winner has:**
- ✗ FAIL status (exceeds p99 thresholds)
- ⚠ CONDITIONAL_PASS status (needs caching/optimization)

**SKIP if:**
- ✓ PASS status (meets all thresholds) → Go directly to Phase 13

## Quick Mitigation Test (30 minutes)

### Strategy 1: Redis Caching (Most Common)

**Step 1: Start Redis (2 min)**

```bash
# Start Redis container
docker run -d \
  --name shark-redis \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru

# Verify running
docker ps | grep shark-redis
```

**Step 2: Configure Rust API for Caching (3 min)**

```bash
cd implementations/rust

# Update .env file
echo "REDIS_URL=redis://localhost:6379" >> .env
echo "CACHE_TTL_SECONDS=300" >> .env

# Rebuild and restart
cargo build --release
cargo run --release &
```

**Step 3: Run Mitigation Test (20 min)**

```bash
cd analysis/phase-12-mitigation

# Run baseline (if not already done)
python test_mitigation.py \
  --strategy redis-caching \
  --base-url http://localhost:8080
```

**Expected Output:**

```
================================================================================
BASELINE TEST (Before Mitigation)
================================================================================

Running benchmark to establish baseline...

Baseline Results:
  Identifier Lookup p99: 45.67ms (threshold: 100ms)
  Two-Hop Traversal p99: 189.23ms (threshold: 300ms)
  Three-Hop Traversal p99: 523.45ms (threshold: 500ms)

================================================================================
MITIGATION SETUP REQUIRED
================================================================================

Before continuing, ensure:
  1. Redis is running (docker run -d -p 6379:6379 redis:7-alpine)
  2. Rust API has REDIS_URL configured
  3. Rust API restarted with caching enabled

Press Enter when mitigation is ready...

================================================================================
MITIGATION TEST: REDIS-CACHING
================================================================================

Running warm-up to populate cache...
Warm-up complete.

Running mitigation benchmark...

Mitigation Results:
  Identifier Lookup p99: 18.34ms (threshold: 100ms)
  Two-Hop Traversal p99: 89.12ms (threshold: 300ms)
  Three-Hop Traversal p99: 298.67ms (threshold: 500ms)

================================================================================
MITIGATION COMPARISON: REDIS-CACHING
================================================================================

Query Type                Baseline p99    Mitigated p99   Improvement  Threshold   Status
------------------------------------------------------------------------------------------
Identifier Lookup              45.67 ms        18.34 ms     +59.8%       100 ms     ✓ PASS
Two-Hop Traversal             189.23 ms        89.12 ms     +52.9%       300 ms     ✓ PASS
Three-Hop Traversal           523.45 ms       298.67 ms     +42.9%       500 ms     ✓ PASS

==========================================================================================
✓ SUCCESS: All thresholds met with mitigation!
==========================================================================================

✓ Report generated: redis_caching/MITIGATION_REPORT.md
```

**Step 4: Review Report (5 min)**

```bash
cat redis_caching/MITIGATION_REPORT.md
```

If successful (all ✓ PASS):
- ✅ Update FINAL_DECISION.md with caching details
- ✅ Proceed to Phase 13 (Final Report)

If unsuccessful (any ✗ FAIL):
- → Try Strategy 2 (Query Optimization)

---

## Strategy 2: Query Optimization

**Only if Redis caching insufficient**

### PostgreSQL Optimization

```bash
# Connect to PostgreSQL
docker exec -it shark-postgres psql -U shark -d sharkdb

# Find slow queries
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 10
ORDER BY mean_exec_time DESC
LIMIT 10;

# Add covering indexes
CREATE INDEX idx_air_mode_s_covering
ON air_instance_lookup (mode_s)
INCLUDE (shark_name, platform, affiliation, nationality);

# Reindex
REINDEX TABLE air_instance_lookup;
VACUUM ANALYZE;

# Exit
\q
```

### Neo4j Optimization

```bash
# Connect to Neo4j
docker exec -it shark-neo4j cypher-shell -u neo4j -p sharkbakeoff

# Update statistics
CALL db.stats.collect();

# Check index usage
SHOW INDEXES;

# Exit
:exit
```

### Test Optimization

```bash
cd analysis/phase-12-mitigation

python test_mitigation.py \
  --strategy query-optimization \
  --base-url http://localhost:8080
```

---

## Strategy 3: Hybrid Architecture

**Only if single database cannot meet all requirements**

### Option A: PostgreSQL (queries) + Neo4j (curation)

**Advantages:**
- PostgreSQL: Fast lookups
- Neo4j: Self-service curation
- Best of both worlds

**Complexity:** High

**Quick Test:**

```bash
# 1. Ensure both databases running
docker ps | grep shark-postgres
docker ps | grep shark-neo4j

# 2. Configure Rust API for hybrid
# Edit implementations/rust/src/main.rs to route:
# - /api/query/* → PostgreSQL
# - /api/curate/* → Neo4j

# 3. Rebuild and test
cd implementations/rust
cargo build --release
cargo run --release &

cd ../../analysis/phase-12-mitigation
python test_mitigation.py \
  --strategy hybrid \
  --base-url http://localhost:8080
```

---

## Mitigation Decision Tree

```
START: Winner fails/conditional pass thresholds

1. Is winner within 20% of p99 thresholds?
   YES → Try Redis Caching (Strategy 1)
         ├─ All PASS? → SUCCESS, use caching
         └─ Any FAIL? → Try Query Optimization (Strategy 2)

   NO → Consider Hybrid (Strategy 3) or Threshold Relaxation

2. After Query Optimization:
   ├─ All PASS? → SUCCESS, deploy optimizations
   └─ Any FAIL? → Try Hybrid Architecture (Strategy 3)

3. After Hybrid:
   ├─ Acceptable complexity? → SUCCESS, implement hybrid
   └─ Too complex? → Threshold Relaxation (Strategy 4)

4. Threshold Relaxation:
   → Get stakeholder approval
   → Update decision
   → Proceed to Phase 13
```

---

## Expected Results by Strategy

### Redis Caching

**Best For:**
- Winner within 20% of thresholds
- High cache hit potential (>80% repeated queries)

**Expected Improvement:** 30-50% latency reduction

**Success Rate:** High (if workload has repeated queries)

### Query Optimization

**Best For:**
- Specific slow queries identified
- Index improvements possible

**Expected Improvement:** 10-30% latency reduction

**Success Rate:** Medium (depends on optimization opportunities)

### Hybrid Architecture

**Best For:**
- No single database meets all needs
- Performance vs curation trade-off

**Expected Improvement:** Combines strengths of both databases

**Success Rate:** Medium (high complexity trade-off)

---

## Cache Hit Rate Monitoring

If using Redis caching, monitor cache effectiveness:

```bash
# Connect to Redis
docker exec -it shark-redis redis-cli

# Check stats
INFO stats

# Look for:
# - keyspace_hits: Number of cache hits
# - keyspace_misses: Number of cache misses
#
# Hit rate = hits / (hits + misses)
# Target: >80%

# Exit
exit
```

**If hit rate < 80%:**
- Increase cache TTL
- Cache more query types
- Analyze query patterns

---

## Troubleshooting

### "Redis not helping enough"

**Problem:** Cache hit rate < 50%

**Solutions:**
1. Increase cache TTL (5-15 minutes)
2. Warm up cache before testing
3. Check if workload has high query diversity

### "Query optimization broke something"

**Problem:** Tests fail after optimization

**Solutions:**
1. Roll back changes
2. Test in staging environment first
3. Add indexes incrementally

### "Hybrid too complex"

**Problem:** Data consistency issues

**Solutions:**
1. Simplify to single database
2. Use managed sync service
3. Relax thresholds instead

---

## Validation Checklist

Before accepting mitigation:

- [ ] All p99 thresholds met (✓ PASS for all query types)
- [ ] Improvement quantified (>30% reduction)
- [ ] Cache hit rate >80% (if using caching)
- [ ] Production deployment plan documented
- [ ] Updated FINAL_DECISION.md
- [ ] Stakeholder approval obtained

---

## Quick Commands

### Test with existing baseline

```bash
python test_mitigation.py \
  --strategy redis-caching \
  --skip-baseline \
  --baseline-file baseline_before_mitigation.csv
```

### Redis commands

```bash
# Start Redis
docker run -d --name shark-redis -p 6379:6379 redis:7-alpine

# Check Redis
docker exec shark-redis redis-cli PING  # Should return "PONG"

# View cache keys
docker exec shark-redis redis-cli KEYS "*"

# Clear cache
docker exec shark-redis redis-cli FLUSHALL
```

---

## Timeline

**Strategy 1 (Redis Caching):**
- Setup: 5 minutes
- Testing: 20 minutes
- Validation: 5 minutes
- **Total: 30 minutes**

**Strategy 2 (Query Optimization):**
- Analysis: 1-2 hours
- Optimization: 2-4 hours
- Testing: 30 minutes
- **Total: 4-6 hours**

**Strategy 3 (Hybrid):**
- Design: 4 hours
- Implementation: 1-2 days
- Testing: 4 hours
- **Total: 2-3 days**

---

## Next Steps

### If Mitigation Successful (All ✓ PASS)

1. Update `FINAL_DECISION.md`:
   ```markdown
   ### Mitigation Applied: Redis Caching

   - Strategy: Redis caching with 5-minute TTL
   - Improvement: 30-50% latency reduction
   - Cache hit rate: 85%
   - All thresholds now met
   ```

2. Document production requirements:
   - Redis deployment specs
   - Cache TTL configuration
   - Monitoring setup

3. Proceed to Phase 13 (Final Report)

### If Mitigation Unsuccessful (Any ✗ FAIL)

1. Try next strategy in decision tree
2. If all strategies fail:
   - Consider threshold relaxation
   - Get stakeholder approval
   - Update decision with justification

---

## References

- [Phase 12 README](README.md) - Complete mitigation guide
- [Phase C Decision](../phase-c-decision/FINAL_DECISION.md) - Why mitigation needed
- [Redis Documentation](https://redis.io/docs/)
- [Query Optimization Guides](../phase-a-optimization/) - Database-specific guides
