// =============================================================================
// S15: Knowledge Generation - Relationship Growth Analysis
// Query: Analyze relationship patterns and generate new knowledge
// Expected p99: 50-100ms (complex graph analytics)
// =============================================================================

// Find aircraft that frequently co-occur and suggest relationship patterns
MATCH (a1:Aircraft)-[seen:SEEN_WITH]->(a2:Aircraft)
WHERE seen.timestamp >= datetime() - duration({days: 7})
WITH a1, a2, COUNT(seen) AS co_occurrence_count,
     COLLECT(seen.location) AS locations
WHERE co_occurrence_count >= 3  // Threshold for pattern
MATCH (a1)-[:OPERATED_BY]->(o1:Organization)
MATCH (a2)-[:OPERATED_BY]->(o2:Organization)
RETURN a1.shark_name AS aircraft_1,
       a2.shark_name AS aircraft_2,
       o1.name AS operator_1,
       o2.name AS operator_2,
       co_occurrence_count,
       locations,
       CASE
         WHEN o1 = o2 THEN 'SAME_OPERATOR'
         WHEN o1.country = o2.country THEN 'SAME_COUNTRY'
         ELSE 'CROSS_BORDER'
       END AS relationship_type
ORDER BY co_occurrence_count DESC
LIMIT 100;

// Performance notes:
// - Temporal filtering on relationships
// - Aggregation across multiple entities
// - Conditional logic for classification
// - Expected latency: 50-150ms
// - This query is impractical in PostgreSQL

// Variant: Predict likely co-occurrences based on historical patterns
MATCH (a1:Aircraft)-[seen:SEEN_WITH]->(a2:Aircraft)
WHERE seen.timestamp >= datetime() - duration({days: 30})
WITH a1, a2, COUNT(seen) AS historical_count,
     AVG(duration.inSeconds(seen.timestamp, datetime()).seconds) AS avg_recency
MATCH (a1)-[:BASED_AT]->(l1:Location)
MATCH (a2)-[:BASED_AT]->(l2:Location)
WITH a1, a2, historical_count, avg_recency,
     point.distance(
       point({latitude: l1.latitude, longitude: l1.longitude}),
       point({latitude: l2.latitude, longitude: l2.longitude})
     ) AS distance_km
WHERE distance_km < 500000  // Within 500km
RETURN a1.mode_s AS aircraft_1_mode_s,
       a2.mode_s AS aircraft_2_mode_s,
       historical_count,
       avg_recency / 86400 AS avg_days_since_last_seen,
       distance_km / 1000 AS base_distance_km,
       (historical_count * 1000.0 / (distance_km + 1)) AS likelihood_score
ORDER BY likelihood_score DESC
LIMIT 50;

// Performance notes:
// - Geospatial calculations using point.distance()
// - Complex scoring algorithm
// - Expected latency: 100-200ms
// - Requires APOC or native geospatial support

// Variant: Generate new relationships from activity patterns
// This would be a write query in production
MATCH (s:Ship)-[v:VISITED]->(p:Location)
WITH s, p, COUNT(v) AS visit_count
WHERE visit_count >= 5
MERGE (s)-[r:FREQUENT_VISITOR]->(p)
SET r.visit_count = visit_count,
    r.last_updated = datetime(),
    r.confidence = CASE
      WHEN visit_count >= 10 THEN 0.95
      WHEN visit_count >= 7 THEN 0.85
      ELSE 0.75
    END
RETURN s.shark_name AS ship_name,
       p.name AS port_name,
       r.visit_count AS visits,
       r.confidence AS confidence;

// Performance notes:
// - MERGE creates relationship if not exists
// - Conditional logic for confidence scoring
// - This is knowledge generation in action
// - Expected latency: 50-100ms per ship-port pair
