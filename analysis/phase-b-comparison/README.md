# Phase B: Head-to-Head Comparison

**Goal**: Compare optimally configured databases under various workloads to identify the best choice and crossover points.

## Objectives

1. **Head-to-Head Performance**: Compare optimized PostgreSQL, Neo4j, and Memgraph
2. **Workload Sensitivity**: Test all 14 workload patterns (lookup-heavy to write-heavy)
3. **Crossover Analysis**: Identify when one database outperforms another
4. **Scalability Testing**: Test under varying concurrency levels
5. **Final Ranking**: Determine winner based on comprehensive testing

## Prerequisites

**From Phase A:**
- ✅ Optimal configuration identified for each database
- ✅ Databases configured with optimal settings
- ✅ Baseline performance established

## Approach

### 1. Apply Optimal Configurations

Use the best configurations from Phase A:

**PostgreSQL:**
- Configuration: `optimized.conf` (or selected variant)
- Expected p99: ~42ms (based on Phase A)

**Neo4j:**
- Configuration: `optimized.conf` (or selected variant)
- Expected p99: ~18ms (based on Phase A)

**Memgraph:**
- Configuration: `optimized.sh` (or selected variant)
- Expected p99: ~12ms (based on Phase A)

### 2. Test Workload Patterns

All 14 workload patterns from benchmark harness:

| Pattern | Description | Identifier % | Two-Hop % | Three-Hop % | Expected Winner |
|---------|-------------|--------------|-----------|-------------|-----------------|
| lookup-95 | Lookup Heavy | 95 | 4 | 1 | TBD |
| lookup-90 | Lookup Focused | 90 | 8 | 2 | TBD |
| lookup-80 | Lookup Majority | 80 | 15 | 5 | TBD |
| balanced-70 | Balanced (70/25/5) | 70 | 25 | 5 | TBD |
| balanced-60 | Balanced (60/30/10) | 60 | 30 | 10 | TBD |
| balanced-50 | Balanced (50/40/10) | 50 | 40 | 10 | TBD |
| analytics-40 | Analytics Light | 40 | 50 | 10 | TBD |
| analytics-30 | Analytics Moderate | 30 | 60 | 10 | TBD |
| analytics-20 | Analytics Heavy | 20 | 70 | 10 | TBD |
| analytics-10 | Analytics Extreme | 10 | 80 | 10 | TBD |
| traversal-light | Traversal Light | 30 | 40 | 30 | TBD |
| traversal-heavy | Traversal Heavy | 20 | 30 | 50 | TBD |
| mixed-realistic | Realistic Mix | 60 | 35 | 5 | TBD |
| write-heavy | Write Heavy | 40 | 20 | 10 | TBD |

### 3. Test Concurrency Levels

Test each database at multiple concurrency levels:

| Concurrency | Use Case |
|-------------|----------|
| 1 | Single-threaded baseline |
| 5 | Light load |
| 10 | Moderate load |
| 20 | Standard benchmark load |
| 50 | High load |
| 100 | Stress test |

### 4. Metrics to Capture

**Performance Metrics:**
- Latency percentiles: p50, p75, p90, p95, p99, p99.9
- Throughput: Requests per second
- Error rate: Failed requests
- Latency distribution: HDR histogram

**Resource Metrics:**
- CPU utilization (%)
- Memory usage (MB)
- Disk I/O (if applicable)
- Network throughput

## Testing Methodology

### Test Protocol

For each database:

1. **Ensure optimal configuration applied**
2. **Restart database** (fresh state)
3. **Warm-up**: 5,000 requests with balanced-50 pattern
4. **For each workload pattern:**
   - Run 50,000 requests at concurrency 20
   - Capture metrics
   - Wait 30 seconds between tests
5. **For concurrency testing:**
   - Use balanced-50 pattern
   - Test at concurrency levels: 1, 5, 10, 20, 50, 100
   - Run 50,000 requests each
6. **Collect resource metrics** throughout

### Automated Testing Script

```bash
# Run full Phase B comparison
python run_comparison.py \
  --databases postgresql neo4j memgraph \
  --workloads all \
  --concurrency 1,5,10,20,50,100 \
  --requests 50000 \
  --output results/
```

## Expected Results

### By Workload Type

**Lookup-Heavy (95% identifier lookups):**
- Expected winner: Memgraph (in-memory advantage)
- Runner-up: Neo4j (optimized indexes)
- PostgreSQL: Acceptable but slower

**Balanced (50/40/10 mix):**
- Expected winner: Neo4j or Memgraph (graph traversal efficiency)
- PostgreSQL: Competitive if well-indexed

**Analytics-Heavy (20/70/10 - heavy graph traversal):**
- Expected winner: Memgraph (in-memory graph)
- Runner-up: Neo4j (native graph storage)
- PostgreSQL: Significantly slower (join overhead)

**Write-Heavy:**
- Expected winner: TBD (depends on transaction overhead)
- PostgreSQL: Strong ACID, mature WAL
- Memgraph: MVCC advantage
- Neo4j: Lock-based concurrency

### By Concurrency Level

**Low Concurrency (1-5):**
- All databases should perform well
- Minimal difference

**Medium Concurrency (10-20):**
- Connection pooling effectiveness matters
- Expect differences to emerge

**High Concurrency (50-100):**
- Scalability differences become pronounced
- Thread/worker pool limits tested

## Crossover Analysis

### Crossover Points to Identify

**1. Workload Crossover**
- At what % of graph traversals does graph DB overtake PostgreSQL?
- Example: "PostgreSQL better when <30% graph queries, Neo4j better when >30%"

**2. Concurrency Crossover**
- At what concurrency does each database hit limits?
- Example: "PostgreSQL scales to 50 concurrent, Neo4j to 100"

**3. Data Size Crossover**
- At what dataset size does in-memory (Memgraph) become impractical?
- At what size does PostgreSQL disk I/O become bottleneck?

### Visualization

Create charts showing:
- **Latency vs Workload Pattern** (all databases on same chart)
- **Throughput vs Concurrency** (scalability curves)
- **Winner by Workload** (heat map)

## Decision Matrix

### Scoring System

Each database gets scored on:

1. **Performance (60% weight)**
   - p99 latency across all workloads: 30%
   - Throughput: 15%
   - Scalability (concurrency handling): 15%

2. **Curation Capability (20% weight)**
   - Self-service schema evolution: 10%
   - Visualization tools: 10%

3. **Operational Considerations (20% weight)**
   - Resource efficiency: 5%
   - Stability under load: 5%
   - Configuration complexity: 5%
   - Ecosystem maturity: 5%

### Threshold Pass/Fail

From the plan, databases must meet:

| Query Type | Target p50 | Acceptable p95 | Maximum p99 |
|------------|-----------|----------------|-------------|
| Identifier Lookup | 10ms | 50ms | 100ms |
| Two-Hop Traversal | 50ms | 150ms | 300ms |
| Three-Hop Traversal | 100ms | 300ms | 500ms |

**Result Categories:**
- ✓ **PASS**: All thresholds met
- ⚠ **CONDITIONAL PASS**: p99 met, p50/p95 borderline (caching may help)
- ✗ **FAIL**: p99 thresholds exceeded

## Deliverables

### 1. Workload Performance Matrix

| Database | lookup-95 | balanced-50 | analytics-20 | ... | Overall Rank |
|----------|-----------|-------------|--------------|-----|--------------|
| PostgreSQL | p99: Xms | p99: Xms | p99: Xms | ... | 3 |
| Neo4j | p99: Xms | p99: Xms | p99: Xms | ... | 2 |
| Memgraph | p99: Xms | p99: Xms | p99: Xms | ... | 1 |

### 2. Crossover Analysis Report

**Workload Crossover:**
```
PostgreSQL wins when:
  - Workload is >80% identifier lookups
  - Dataset will grow beyond available RAM
  - Strong ACID guarantees critical

Neo4j wins when:
  - Workload is 30-70% graph traversals
  - Curation capability is critical
  - Enterprise support needed

Memgraph wins when:
  - Workload is >50% graph traversals
  - Dataset fits in RAM (current + 3-year growth)
  - Maximum performance required
```

### 3. Scalability Curves

Charts showing throughput vs concurrency for each database.

### 4. Final Recommendation

**Winner:** [Database]

**Rationale:**
- Performance: [X]/100 points
- Curation: [X]/100 points
- Operations: [X]/100 points
- **Total: [X]/100 points**

**Meets all thresholds:** ✓ / ⚠ / ✗

**Alternative if winner fails:** [Database with mitigation strategy]

## Directory Structure

```
phase-b-comparison/
├── README.md                          # This file
├── QUICKSTART.md                      # Quick start guide
├── run_comparison.py                  # Automated comparison script
├── analyze_crossover.py               # Crossover analysis tool
├── visualize_results.py               # Charting tool
├── results/
│   ├── postgresql/
│   │   ├── lookup-95.csv
│   │   ├── balanced-50.csv
│   │   ├── analytics-20.csv
│   │   ├── concurrency-*.csv
│   │   └── summary.json
│   ├── neo4j/
│   │   └── [same structure]
│   ├── memgraph/
│   │   └── [same structure]
│   └── comparison/
│       ├── workload_matrix.csv
│       ├── crossover_analysis.md
│       ├── charts/
│       │   ├── latency_by_workload.png
│       │   ├── throughput_by_concurrency.png
│       │   └── winner_heatmap.png
│       └── FINAL_RANKING.md
└── RESULTS_SUMMARY.md                 # Final summary template
```

## Workflow

### Week 1: Workload Testing

**Day 1-2:** PostgreSQL
- Apply optimal config
- Run all 14 workload patterns
- Collect results

**Day 3-4:** Neo4j
- Apply optimal config
- Run all 14 workload patterns
- Collect results

**Day 5:** Memgraph
- Apply optimal config
- Run all 14 workload patterns
- Collect results

### Week 2: Concurrency & Analysis

**Day 1:** Concurrency testing (all databases)

**Day 2-3:** Analysis
- Aggregate results
- Crossover analysis
- Generate charts

**Day 4-5:** Decision
- Score databases
- Write final recommendation
- Prepare for Phase C

## Success Criteria

Phase B is successful when:

1. ✅ All databases tested with optimal configurations
2. ✅ All 14 workload patterns tested
3. ✅ Concurrency testing complete
4. ✅ Crossover points identified
5. ✅ Clear winner emerges (or tie with clear trade-offs)
6. ✅ Threshold assessment complete
7. ✅ Results documented and reproducible

## Common Issues

### "Database X slower than Phase A"

**Cause**: Different workload pattern or configuration not applied
**Solution**: Verify optimal config loaded, compare same workload

### "Inconsistent results between runs"

**Cause**: Insufficient warm-up, background processes
**Solution**: Increase warm-up requests, isolate test environment

### "All databases fail thresholds"

**Cause**: Unrealistic thresholds or infrastructure limits
**Solution**: Review thresholds, check hardware resources, consider mitigation

## References

- [Phase A Results](../phase-a-optimization/RESULTS_SUMMARY.md) - Optimal configurations
- [Benchmark Harness](../../benchmark/harness/README.md) - Workload patterns
- [Thresholds](../../benchmark/harness/thresholds.py) - Performance thresholds
- [Curation Testing](../../benchmark/curation/README.md) - Curation scores

## Next Phase

After Phase B completion, proceed to:

**Phase C: Decision**
- Weight all factors (performance, curation, operations)
- Make final database selection
- Document rationale and trade-offs
