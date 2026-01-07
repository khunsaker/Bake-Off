# Curation Testing Suite

Comprehensive testing of operational curation workflows for the Shark Bake-Off benchmark.

## Overview

This suite evaluates the **curation capability dimension** (20% weight) from the evaluation criteria. It tests how easy it is for curators to:

1. Update entity properties
2. Create new entities
3. Manage relationships
4. Evolve the schema
5. Perform batch operations
6. Visualize and explore the knowledge graph

## Why Curation Matters

From the plan:

> **Current pain points:**
> - Update delay: 30+ minutes after approval
> - Relationship CRUD: Not possible in app
> - Schema changes: Requires PG Admin + DBA (days of delay)
> - Cache invalidation: Slow, unpredictable

The curation capability assessment determines whether a database can meet the "**Curator preference**" requirement and support the rapid,self-service workflow curators need.

## Test Scenarios

### Automated Tests (CT1-CT6)

| ID | Test | Description | Key Metric |
|----|------|-------------|------------|
| **CT1** | Property Update Latency | Time until property change is visible | < 5 minutes (target: < 1 minute) |
| **CT2** | Node Creation Latency | Time until new entity is queryable | < 5 minutes |
| **CT3** | Relationship Creation | Create relationship, verify exists | Functional + latency |
| **CT4** | Schema Addition (Property) | Add new property without DBA | Self-service capability |
| **CT5** | Schema Addition (Relationship) | Add new relationship type | Self-service capability |
| **CT6** | Batch Import | Import 1,000 entities with relationships | Time + throughput |

### Manual Assessment (CT7)

| ID | Test | Description | Key Metric |
|----|------|-------------|------------|
| **CT7** | Visualization Quality | Curator subjective assessment | Rating (1-5) |

## Installation

```bash
cd benchmark/curation
pip install -r requirements.txt
```

## Running Tests

### Full Test Suite

```bash
python curation_tests.py
```

This runs all automated tests (CT1-CT6) for both PostgreSQL and Neo4j.

### Individual Database Tests

Edit `curation_tests.py` and comment out the database you don't want to test.

### Expected Output

```
================================================================================
Shark Bake-Off: Curation Testing
================================================================================

Running PostgreSQL Curation Tests...

✓ PASS | CT1-PG | Property Update Latency
  Latency: 0.05s | Steps: 2 | Self-service: Yes
  Notes: Update visible immediately (transaction-based). Cache invalidation may add latency in production.

✓ PASS | CT2-PG | Node Creation Latency
  Latency: 0.03s | Steps: 2 | Self-service: Yes
  Notes: Immediate queryability after commit. ACID guarantees ensure consistency.

✓ PASS | CT4-PG | Schema Addition (Property)
  Latency: 0.12s | Steps: 4 | Self-service: No
  Notes: Requires ALTER TABLE (DDL). May lock table. Needs migration script for production. Not self-service for curators.

✓ PASS | CT6-PG | Batch Import (1000 entities)
  Latency: 2.34s | Steps: 2 | Self-service: Yes
  Notes: Throughput: 427 entities/sec. COPY command would be faster for large batches.


Running Neo4j Curation Tests...

✓ PASS | CT1-NEO4J | Property Update Latency
  Latency: 0.03s | Steps: 1 | Self-service: Yes
  Notes: Immediate visibility. Can be done via Bloom UI without writing Cypher.

✓ PASS | CT2-NEO4J | Node Creation Latency
  Latency: 0.02s | Steps: 1 | Self-service: Yes
  Notes: Immediate queryability. Can create via Bloom UI with point-and-click.

✓ PASS | CT3-NEO4J | Relationship Creation
  Latency: 0.04s | Steps: 1 | Self-service: Yes
  Notes: Relationships are first-class citizens. Can create via Bloom UI by dragging nodes.

✓ PASS | CT4-NEO4J | Schema Addition (Property)
  Latency: 0.02s | Steps: 1 | Self-service: Yes
  Notes: No schema change needed! Just SET property. Immediate availability. Fully self-service.

✓ PASS | CT5-NEO4J | Schema Addition (Relationship Type)
  Latency: 0.03s | Steps: 1 | Self-service: Yes
  Notes: No schema change needed! Just CREATE with new type. Immediate availability. Fully self-service.

✓ PASS | CT6-NEO4J | Batch Import (1000 entities)
  Latency: 1.89s | Steps: 1 | Self-service: Yes
  Notes: Throughput: 529 entities/sec. LOAD CSV or APOC for larger batches.


================================================================================
CURATION TEST SUMMARY
================================================================================

+-------+------------------------------------+---------+----------+--------------+-----------+-------------+----------------+
| Test  | Name                               | PG Time | PG Steps | PG Self-Svc  | Neo4j Time| Neo4j Steps | Neo4j Self-Svc |
+=======+====================================+=========+==========+==============+===========+=============+================+
| CT1   | Property Update Latency            | 0.05s   | 2        | Yes          | 0.03s     | 1           | Yes            |
+-------+------------------------------------+---------+----------+--------------+-----------+-------------+----------------+
| CT2   | Node Creation Latency              | 0.03s   | 2        | Yes          | 0.02s     | 1           | Yes            |
+-------+------------------------------------+---------+----------+--------------+-----------+-------------+----------------+
| CT3   | Relationship Creation              | N/A     | N/A      | No           | 0.04s     | 1           | Yes            |
+-------+------------------------------------+---------+----------+--------------+-----------+-------------+----------------+
| CT4   | Schema Addition (Property)         | 0.12s   | 4        | No           | 0.02s     | 1           | Yes            |
+-------+------------------------------------+---------+----------+--------------+-----------+-------------+----------------+
| CT5   | Schema Addition (Relationship Type)| N/A     | N/A      | No           | 0.03s     | 1           | Yes            |
+-------+------------------------------------+---------+----------+--------------+-----------+-------------+----------------+
| CT6   | Batch Import (1000 entities)       | 2.34s   | 2        | Yes          | 1.89s     | 1           | Yes            |
+-------+------------------------------------+---------+----------+--------------+-----------+-------------+----------------+

================================================================================
KEY FINDINGS
================================================================================

PostgreSQL:
  Self-service operations: 3/4
  Average latency: 0.64s

Neo4j:
  Self-service operations: 6/6
  Average latency: 0.34s

================================================================================
```

## Visualization Assessment (CT7)

Follow the [CT7 Visualization Assessment Guide](CT7_VISUALIZATION_ASSESSMENT.md) to perform manual curation workflow testing with:

- Neo4j Bloom
- Memgraph Lab
- PostgreSQL (pgAdmin/DBeaver)

This is a **subjective assessment** by actual curators and carries significant weight in the decision.

## Key Differences

### PostgreSQL

**Strengths:**
- ✅ Immediate visibility of updates (transactional)
- ✅ Familiar SQL for many users
- ✅ Good batch import performance
- ✅ Property updates are self-service

**Weaknesses:**
- ❌ **No relationship CRUD in application** (requires junction tables)
- ❌ **Schema changes require DBA/migration** (ALTER TABLE)
- ❌ Cannot add new relationship types without schema change
- ❌ Requires SQL knowledge
- ❌ No native graph visualization

**Critical Limitations:**
1. Adding a new property requires:
   - Write migration script
   - Test in dev
   - DBA review
   - Deploy to production
   - Potential table lock
   - **Time: Hours to days**

2. Creating relationships requires:
   - Insert into junction table
   - Understand foreign key constraints
   - No visual tools
   - **Curator frustration: High**

### Neo4j

**Strengths:**
- ✅ **Schemaless - add properties instantly**
- ✅ **Create relationships without schema change**
- ✅ Relationship CRUD fully supported
- ✅ Bloom UI for visual curation
- ✅ Immediate visibility
- ✅ **100% self-service for curators**

**Weaknesses:**
- ⚠️ Requires Cypher knowledge for complex operations
- ⚠️ Bloom requires Enterprise license (or workaround)

**Critical Advantages:**
1. Adding a new property:
   - Just SET it
   - Immediate availability
   - No schema change
   - **Time: Seconds**

2. Creating relationships:
   - Drag-and-drop in Bloom
   - Or simple Cypher: `CREATE (a)-[:NEW_REL]->(b)`
   - **Curator frustration: Low**

### Memgraph

Similar to Neo4j but:
- Different visualization tool (Memgraph Lab vs Bloom)
- May have different licensing
- Performance claims (testing will validate)

## Interpretation Guidelines

### Self-Service Score

**Critical Requirement**: Curators must be able to evolve the schema without DBA involvement.

| Score | Interpretation | Action |
|-------|----------------|--------|
| 6/6 (Neo4j/Memgraph) | ✓ Fully self-service | Meets requirement |
| 3/4 (PostgreSQL) | ⚠️ Limited self-service | Consider hybrid or reject |

**PostgreSQL fails the self-service requirement** because:
- Cannot add properties without ALTER TABLE
- Cannot add relationship types without schema change
- Relationship management requires SQL knowledge

### Latency Scores

Both databases meet the latency targets:
- Target: < 5 minutes
- Both: < 1 second

**Winner**: Marginally Neo4j (fewer steps, simpler workflow)

### Visualization Score (CT7)

Expected results from plan context:
- **Neo4j Bloom**: 4.0-4.5 / 5.0 (Excellent)
- **Memgraph Lab**: 3.5-4.0 / 5.0 (Good)
- **PostgreSQL**: 2.0-2.5 / 5.0 (Poor for graph curation)

If Bloom scores >1.5 points higher, it becomes a decisive factor.

## Decision Impact

### Curation Capability Weight: 20%

From the plan's evaluation dimensions, curation capability is 20% of the total decision.

**Likely outcome**:
- **Neo4j/Memgraph**: 9-10 / 10 (Excellent)
- **PostgreSQL**: 4-5 / 10 (Poor)

**Contribution to overall score**:
- Neo4j: 20% × 0.95 = **19% / 20%**
- PostgreSQL: 20% × 0.45 = **9% / 20%**

**10% gap** in overall scoring from curation alone.

### When Curation Capability Matters Most

If the performance testing shows:
- PostgreSQL: Meets all thresholds (PASS)
- Neo4j: Borderline or requires caching (CONDITIONAL PASS)

Then the curation capability difference becomes the **tiebreaker**:

> "PostgreSQL is faster, but Neo4j enables the curation workflow we need. Given that both meet thresholds (with caching for Neo4j), we recommend Neo4j for superior curation capability."

## Hybrid Considerations

If PostgreSQL is chosen for performance:

**Option D3: PostgreSQL + Neo4j Hybrid**
- PostgreSQL for query performance
- Neo4j Community for curation (free Bloom alternative exists)
- Sync mechanism between them

**Curation impact**:
- Curators use Neo4j/Bloom for curation ✅
- Changes sync to PostgreSQL periodically
- Complexity: Medium
- Cost: Acceptable (Community Edition)

## Running Custom Tests

### Add New Curation Test

```python
def ct_new_test(self) -> CurationTestResult:
    """Your new curation test"""
    test_id = "CT-NEW"
    start_time = time.time()

    try:
        # Your test logic here
        success = True
        steps = 3

        return CurationTestResult(
            test_id=test_id,
            test_name="New Test Name",
            database=self.database_type,
            success=success,
            latency_seconds=time.time() - start_time,
            steps_required=steps,
            complexity='simple',  # or 'moderate', 'complex'
            self_service=True,  # Can curator do it?
            notes="Test notes here"
        )
    except Exception as e:
        return CurationTestResult(
            test_id=test_id,
            test_name="New Test Name",
            database=self.database_type,
            success=False,
            latency_seconds=time.time() - start_time,
            steps_required=0,
            complexity='simple',
            self_service=False,
            notes=f"Error: {str(e)}"
        )
```

### Test Against Memgraph

Create a `MemgraphCurationTester` class (similar to `Neo4jCurationTester` since Memgraph uses Cypher).

## Troubleshooting

### "No test data available"

Load sample data first:
```bash
cd data/migration
python load_neo4j.py
python load_postgres.py
```

### Connection errors

Verify services are running:
```bash
# Check PostgreSQL
psql -h localhost -U shark -d sharkdb -c "SELECT 1"

# Check Neo4j
curl http://localhost:7474/

# Check Memgraph
curl http://localhost:3000/
```

### Permission errors

PostgreSQL tests require:
- CREATE TABLE permission
- ALTER TABLE permission
- INSERT/UPDATE/DELETE permission

Neo4j tests require:
- CREATE/DELETE node permission
- CREATE/DELETE relationship permission

## References

- [Curation Requirements (Plan)](../../SHARK-BAKEOFF-PLAN.md#curation-requirements)
- [CT7 Visualization Assessment](CT7_VISUALIZATION_ASSESSMENT.md)
- [Schema Evolution Requirements (Plan)](../../SHARK-BAKEOFF-PLAN.md#schema-evolution-requirements)

## Contributing

When adding new curation tests:
1. Add method to appropriate tester class
2. Follow naming convention: `ctN_test_name`
3. Return `CurationTestResult` dataclass
4. Update this README with test description
5. Add to summary table

## License

See project root for license information.
