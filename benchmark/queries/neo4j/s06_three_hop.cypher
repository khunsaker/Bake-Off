// =============================================================================
// S6: Three-Hop Co-Occurrence Query
// Query: Find aircraft seen together where operators are different
// Expected p99: < 30ms (native graph traversal with filtering)
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
// - Pattern match across 3 relationship hops
// - No JOINs - native graph traversal
// - Expected latency: 15-40ms at scale
// - 3-5x faster than PostgreSQL for same query
// - Query is concise and expresses intent clearly

// Variant: Include timestamp and location from relationship properties
MATCH (a1:Aircraft)-[seen:SEEN_WITH]->(a2:Aircraft),
      (a1)-[:OPERATED_BY]->(o1:Organization),
      (a2)-[:OPERATED_BY]->(o2:Organization)
WHERE o1 <> o2
RETURN a1.mode_s AS aircraft_1_mode_s,
       a1.shark_name AS aircraft_1_name,
       o1.name AS aircraft_1_operator,
       a2.mode_s AS aircraft_2_mode_s,
       a2.shark_name AS aircraft_2_name,
       o2.name AS aircraft_2_operator,
       seen.timestamp AS seen_together_time,
       seen.location AS location
ORDER BY seen.timestamp DESC;

// Variant: Cross-domain (aircraft seen with ships)
MATCH (a:Aircraft)-[seen:CO_LOCATED_WITH]->(s:Ship),
      (a)-[:OPERATED_BY]->(o1:Organization),
      (s)-[:OPERATED_BY]->(o2:Organization)
WHERE o1.country <> o2.country
RETURN a.mode_s AS aircraft_mode_s,
       a.shark_name AS aircraft_name,
       o1.name AS aircraft_operator,
       s.mmsi AS ship_mmsi,
       s.shark_name AS ship_name,
       o2.name AS ship_operator,
       seen.timestamp AS co_located_time;

// Variant: Find all entities seen together in last 24 hours
MATCH (a1:Aircraft)-[seen:SEEN_WITH]->(a2:Aircraft),
      (a1)-[:OPERATED_BY]->(o1:Organization),
      (a2)-[:OPERATED_BY]->(o2:Organization)
WHERE seen.timestamp >= datetime() - duration({hours: 24})
  AND o1 <> o2
RETURN a1.mode_s, a1.shark_name, o1.name,
       a2.mode_s, a2.shark_name, o2.name,
       seen.timestamp
ORDER BY seen.timestamp DESC;
