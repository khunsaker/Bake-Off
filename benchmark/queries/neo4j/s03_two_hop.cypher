// =============================================================================
// S3: Two-Hop Relationship Query
// Query: Find all aircraft operated by organizations headquartered in a country
// Expected p99: < 20ms (native graph traversal)
// =============================================================================

// Find aircraft by operator's HQ country
MATCH (a:Aircraft)-[:OPERATED_BY]->(o:Organization)-[:HEADQUARTERED_AT]->(l:Location)
WHERE l.country = $country
RETURN a.shark_name AS aircraft_name,
       a.platform AS aircraft_platform,
       o.name AS operator_name,
       l.name AS headquarters_location,
       l.country AS country;

// Performance notes:
// - Native graph traversal (no JOINs)
// - Pattern match optimized by query planner
// - Index seek on l.country, then traverse backwards
// - Expected latency: 10-30ms at scale
// - 2-3x faster than PostgreSQL for same query
// - Query expressiveness: natural vs complex SQL

// Variant: Include operator country in output
MATCH (a:Aircraft)-[:OPERATED_BY]->(o:Organization)-[:HEADQUARTERED_AT]->(l:Location)
WHERE l.country = $country
RETURN a.shark_name AS aircraft_name,
       a.mode_s AS mode_s,
       o.name AS operator_name,
       o.country AS operator_country,
       l.name AS hq_location;

// Variant: Maritime domain equivalent
MATCH (s:Ship)-[:OPERATED_BY]->(o:Organization)-[:HEADQUARTERED_AT]->(l:Location)
WHERE l.country = $country
RETURN s.shark_name AS ship_name,
       s.mmsi AS mmsi,
       s.ship_type AS ship_type,
       o.name AS operator_name,
       l.name AS hq_location;
