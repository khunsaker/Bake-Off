# Benchmark Query Definitions

This directory contains query implementations for all benchmark scenarios across PostgreSQL, Neo4j, and Memgraph.

## Query Categories

### Identifier Lookups (S1-S2)
- **S1**: Simple identifier lookup by Mode-S or MMSI
- **S2**: Multi-identifier disambiguation (multiple identifiers for same entity)

### Multi-Hop Queries (S3-S10)
- **S3**: Two-hop: Aircraft → Operator → HQ Location
- **S4**: Two-hop: Ship → Operator → Parent Organization
- **S5**: Two-hop: Aircraft → Platform → Manufacturer
- **S6**: Three-hop: Co-located aircraft with different operators
- **S7**: Three-hop: Ship → Home Port → Country → All ships
- **S8**: Three-hop: Cross-domain organizational relationships
- **S9**: Four-hop: Variable-length path queries
- **S10**: Complex multi-domain aggregation

### Activity Framework (S11-S14)
- **S11**: Port visit history with temporal ordering
- **S12**: Activity pattern detection
- **S13**: Co-traveling entity detection
- **S14**: Unusual activity correlation

### Knowledge Generation (S15-S18)
- **S15**: Relationship growth analysis
- **S16**: Predictive co-occurrence
- **S17**: Behavioral pattern clustering
- **S18**: Multi-domain knowledge graphs

## File Structure

```
queries/
├── postgresql/
│   ├── s01_simple_lookup.sql
│   ├── s02_multi_identifier.sql
│   ├── s03_two_hop.sql
│   └── ...
├── neo4j/
│   ├── s01_simple_lookup.cypher
│   ├── s02_multi_identifier.cypher
│   ├── s03_two_hop.cypher
│   └── ...
└── memgraph/
    ├── s01_simple_lookup.cypher
    ├── s02_multi_identifier.cypher
    ├── s03_two_hop.cypher
    └── ...
```

## Query Complexity Scores

| Scenario | PostgreSQL | Neo4j | Memgraph | Notes |
|----------|-----------|-------|----------|-------|
| S1 | Simple | Simple | Simple | Index lookup |
| S2 | Simple | Simple | Simple | OR condition |
| S3 | Moderate | Simple | Simple | 2 JOINs vs native traversal |
| S6 | Complex | Moderate | Moderate | 3+ JOINs vs pattern match |
| S9 | Very Complex | Simple | Simple | Recursive CTE vs variable-length |
| S15-S18 | Very Complex | Moderate | Moderate | Graph analytics required |

## Performance Expectations

Based on the plan's threshold of p99 < 100ms @ 1,000 qps:

- **S1-S2**: All databases should meet threshold (indexed lookups)
- **S3-S5**: PostgreSQL may struggle at scale (multiple JOINs)
- **S6-S10**: PostgreSQL likely exceeds threshold, graph DBs should pass
- **S11-S14**: Mixed results based on activity log size
- **S15-S18**: Graph DBs have significant advantage

## Query Expressiveness

Some queries are impractical in PostgreSQL:
- Variable-length paths (S9)
- Real-time relationship creation (S15-S16)
- Graph algorithms (S17)
- Multi-domain knowledge synthesis (S18)
