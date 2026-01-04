// =============================================================================
// S11: Port Visit History
// Query: Find ship's port visit history with temporal ordering
// Expected p99: < 15ms (native traversal with relationship properties)
// =============================================================================

// Find port visits for a specific ship
MATCH (s:Ship {mmsi: $mmsi})-[v:VISITED]->(p:Location)
WHERE p.location_type = 'PORT'
RETURN s.shark_name AS ship_name,
       s.mmsi AS mmsi,
       p.name AS port_name,
       p.country AS port_country,
       v.timestamp AS visit_time,
       v.duration_hours AS duration_hours,
       v.purpose AS visit_purpose
ORDER BY v.timestamp DESC
LIMIT 50;

// Performance notes:
// - Direct relationship traversal from ship node
// - Relationship properties accessed directly (no JSONB extraction)
// - Index on v.timestamp for ordering
// - Expected latency: 5-20ms at scale
// - 2-3x faster than PostgreSQL

// Variant: Find all ships that visited a specific port
MATCH (s:Ship)-[v:VISITED]->(p:Location {name: $port_name})
RETURN s.shark_name AS ship_name,
       s.mmsi AS mmsi,
       s.ship_type AS ship_type,
       s.operator AS operator,
       v.timestamp AS visit_time,
       v.duration_hours AS duration_hours
ORDER BY v.timestamp DESC
LIMIT 100;

// Variant: Find ships with unusual port visit patterns
MATCH (s:Ship)-[v:VISITED]->(p:Location)
WHERE p.country = $suspicious_country
  AND v.duration_hours < 2  // Quick turnaround
WITH s, COUNT(v) AS visit_count
WHERE visit_count > 5  // Multiple quick visits
MATCH (s)-[recent:VISITED]->(p:Location)
WHERE recent.timestamp >= datetime() - duration({days: 30})
RETURN s.shark_name AS ship_name,
       s.operator AS operator,
       visit_count,
       COLLECT(p.name) AS recent_ports
ORDER BY visit_count DESC;

// Performance notes for pattern detection:
// - Aggregation (COUNT, COLLECT) is efficient in Neo4j
// - Temporal filtering on relationship properties
// - Expected latency: 30-50ms for aggregation queries
