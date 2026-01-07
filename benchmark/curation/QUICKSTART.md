# Curation Testing Quick Start

Get curation testing running in 5 minutes!

## Prerequisites

- PostgreSQL with loaded data
- Neo4j with loaded data
- Python 3.8+

## Step 1: Install Dependencies (1 min)

```bash
cd benchmark/curation
pip install -r requirements.txt
```

## Step 2: Verify Data Loaded (1 min)

```bash
# Check PostgreSQL
psql -h localhost -U shark -d sharkdb -c "SELECT COUNT(*) FROM air_instance_lookup;"

# Check Neo4j
# Open http://localhost:7474/browser/
# Run: MATCH (a:Aircraft) RETURN count(a)
```

Both should return >0 entities.

## Step 3: Run Automated Tests (2 min)

```bash
python curation_tests.py
```

Expected output:
```
================================================================================
Shark Bake-Off: Curation Testing
================================================================================

Running PostgreSQL Curation Tests...

✓ PASS | CT1-PG | Property Update Latency
  Latency: 0.05s | Steps: 2 | Self-service: Yes

✓ PASS | CT2-PG | Node Creation Latency
  Latency: 0.03s | Steps: 2 | Self-service: Yes

✓ PASS | CT4-PG | Schema Addition (Property)
  Latency: 0.12s | Steps: 4 | Self-service: No
  Notes: Requires ALTER TABLE (DDL). Not self-service for curators.

✓ PASS | CT6-PG | Batch Import (1000 entities)
  Latency: 2.34s | Steps: 2 | Self-service: Yes


Running Neo4j Curation Tests...

✓ PASS | CT1-NEO4J | Property Update Latency
  Latency: 0.03s | Steps: 1 | Self-service: Yes
  Notes: Can be done via Bloom UI without writing Cypher.

✓ PASS | CT2-NEO4J | Node Creation Latency
  Latency: 0.02s | Steps: 1 | Self-service: Yes
  Notes: Can create via Bloom UI with point-and-click.

✓ PASS | CT3-NEO4J | Relationship Creation
  Latency: 0.04s | Steps: 1 | Self-service: Yes
  Notes: Can create via Bloom UI by dragging nodes.

✓ PASS | CT4-NEO4J | Schema Addition (Property)
  Latency: 0.02s | Steps: 1 | Self-service: Yes
  Notes: No schema change needed! Fully self-service.

✓ PASS | CT5-NEO4J | Schema Addition (Relationship Type)
  Latency: 0.03s | Steps: 1 | Self-service: Yes
  Notes: No schema change needed! Fully self-service.

✓ PASS | CT6-NEO4J | Batch Import (1000 entities)
  Latency: 1.89s | Steps: 1 | Self-service: Yes

KEY FINDINGS:
PostgreSQL: Self-service operations: 3/4
Neo4j:      Self-service operations: 6/6
```

## Step 4: Manual Visualization Assessment (Optional, 30 min)

Follow [CT7_VISUALIZATION_ASSESSMENT.md](CT7_VISUALIZATION_ASSESSMENT.md) for hands-on curator testing of:

1. **Neo4j Bloom**: http://localhost:7474/browser/ → Open Bloom
2. **Memgraph Lab**: http://localhost:3000/
3. **PostgreSQL**: pgAdmin or DBeaver

## Key Findings

### Self-Service Capability

**PostgreSQL**: ⚠️ **Cannot add properties or relationship types without DBA**
- Requires ALTER TABLE for new properties
- Requires schema migration for new relationship types
- **Days of delay** for schema changes

**Neo4j**: ✅ **100% self-service**
- Just SET new properties
- Just CREATE new relationship types
- **Seconds** to add new schema elements

### Latency

Both meet targets (< 5 minutes):
- PostgreSQL: < 1 second
- Neo4j: < 1 second

### Visualization

Expected from industry experience:
- Neo4j Bloom: **Excellent** (4-5 / 5)
- Memgraph Lab: **Good** (3.5-4 / 5)
- PostgreSQL: **Poor for graphs** (2-2.5 / 5)

## Decision Impact

Curation capability is **20% of evaluation weight**.

**Expected scores**:
- Neo4j: **95%** (19/20 points)
- PostgreSQL: **45%** (9/20 points)

**Gap**: **10% of total project score** from curation alone.

## When Curation Matters

If performance testing shows both databases meet thresholds:
- PostgreSQL: PASS
- Neo4j: CONDITIONAL PASS (with caching)

Then **curation capability becomes the tiebreaker** in favor of Neo4j.

## Quick Commands

### Run specific database

```python
# Edit curation_tests.py, comment out unwanted tests

# Or run just PostgreSQL
python -c "
from curation_tests import PostgreSQLCurationTester
tester = PostgreSQLCurationTester({
    'host': 'localhost',
    'port': 5432,
    'database': 'sharkdb',
    'user': 'shark',
    'password': 'sharkbakeoff'
})
tester.log_result(tester.ct1_property_update())
tester.log_result(tester.ct2_node_creation())
tester.close()
"
```

### Run with custom connection

```python
# PostgreSQL
pg_tester = PostgreSQLCurationTester({
    'host': 'your-host',
    'port': 5432,
    'database': 'your-db',
    'user': 'your-user',
    'password': 'your-password'
})

# Neo4j
neo4j_tester = Neo4jCurationTester({
    'uri': 'bolt://your-host:7687',
    'user': 'neo4j',
    'password': 'your-password'
})
```

## Troubleshooting

### "No test data available"

Load data first:
```bash
cd ../../data/migration
python load_postgres.py
python load_neo4j.py
```

### Connection refused

```bash
# Check PostgreSQL
pg_isready -h localhost -p 5432

# Check Neo4j
curl http://localhost:7474/
```

### Permission denied

PostgreSQL tests need:
- CREATE, ALTER, INSERT, UPDATE, DELETE permissions

Neo4j tests need:
- CREATE, DELETE permissions for nodes and relationships

## Next Steps

- [Full Documentation](README.md)
- [CT7 Visualization Assessment](CT7_VISUALIZATION_ASSESSMENT.md)
- [Curation Requirements (Plan)](../../SHARK-BAKEOFF-PLAN.md#curation-requirements)

## Summary

**PostgreSQL fails the self-service requirement** - curators cannot add properties or relationship types without DBA intervention (days of delay).

**Neo4j passes all curation requirements** - fully self-service, immediate schema evolution, excellent visualization tools.

This **10-point gap** (out of 100) from curation alone may outweigh performance differences if both databases meet "fast enough" thresholds.
