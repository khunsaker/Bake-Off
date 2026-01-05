// =============================================================================
// S6: Three-Hop Co-Occurrence Query (Memgraph)
// Query: Find aircraft seen together where operators are different
// Expected p99: < 20ms (in-memory graph traversal)
// =============================================================================

// Find co-located aircraft with different operators
MATCH (a1:Aircraft)-[:SEEN_WITH]->(a2:Aircraft),
      (a1)-[:OPERATED_BY]->(o1:Organization),
      (a2)-[:OPERATED_BY]->(o2:Organization)
WHERE o1 <> o2
RETURN a1.mode_s AS aircraft_1_mode_s,
       a1.shark_name AS aircraft_1_name,
       o1.name AS aircraft_1_operator,
       a2.mode_s AS aircraft_2_mode_s,
       a2.shark_name AS aircraft_2_name,
       o2.name AS aircraft_2_operator;

// Performance notes:
// - In-memory traversal (no disk I/O)
// - Pattern matching optimized by Memgraph query planner
// - Expected latency: 5-25ms at scale
// - Potentially faster than Neo4j for complex traversals
// - Query syntax identical to Neo4j (Cypher compatible)

// Variant: With relationship properties and temporal filtering
MATCH (a1:Aircraft)-[seen:SEEN_WITH]->(a2:Aircraft),
      (a1)-[:OPERATED_BY]->(o1:Organization),
      (a2)-[:OPERATED_BY]->(o2:Organization)
WHERE o1 <> o2
  AND seen.timestamp >= localDateTime() - duration({hours: 24})
RETURN a1.mode_s AS aircraft_1_mode_s,
       a1.shark_name AS aircraft_1_name,
       o1.name AS aircraft_1_operator,
       a2.mode_s AS aircraft_2_mode_s,
       a2.shark_name AS aircraft_2_name,
       o2.name AS aircraft_2_operator,
       seen.timestamp AS seen_together_time,
       seen.location AS location
ORDER BY seen.timestamp DESC;

// Performance notes:
// - Edge property indexes supported natively
// - Temporal filtering on relationship properties
// - Expected latency: 10-30ms with filtering

// Memgraph-specific: Real-time streaming from Kafka
// CREATE STREAM co_occurrence_stream
// TOPICS track_updates
// TRANSFORM module.create_seen_with_relationships
// CONSUMER_GROUP shark_kb;

// This allows real-time relationship creation as tracks are observed together
// No batch processing required - knowledge generated instantly
