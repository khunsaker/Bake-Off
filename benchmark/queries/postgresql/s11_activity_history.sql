-- =============================================================================
-- S11: Port Visit History
-- Query: Find ship's port visit history with temporal ordering
-- Expected p99: 20-40ms (time-series query with JOINs)
-- =============================================================================

-- Find port visits for a specific ship
SELECT
    s.shark_name AS ship_name,
    s.mmsi,
    l.name AS port_name,
    l.country AS port_country,
    tal.event_timestamp AS visit_time,
    tal.properties->>'duration_hours' AS duration_hours,
    tal.properties->>'purpose' AS visit_purpose
FROM track_activity_log tal
INNER JOIN ship_instance_lookup s ON tal.mmsi = s.mmsi
INNER JOIN locations l ON l.id = (tal.properties->>'location_id')::BIGINT
WHERE tal.event_type = 'port_call'
  AND s.mmsi = $1
ORDER BY tal.event_timestamp DESC
LIMIT 50;

-- Performance notes:
-- - Index on (mmsi, event_timestamp DESC)
-- - JSONB property extraction (->>) adds overhead
-- - JOIN to locations requires index lookup
-- - Expected latency: 20-50ms at scale
-- - Time-series partitioning could improve performance

-- Variant: Find all ships that visited a specific port
SELECT
    s.shark_name AS ship_name,
    s.mmsi,
    s.ship_type,
    s.operator,
    tal.event_timestamp AS visit_time,
    tal.properties->>'duration_hours' AS duration_hours
FROM track_activity_log tal
INNER JOIN ship_instance_lookup s ON tal.mmsi = s.mmsi
WHERE tal.event_type = 'port_call'
  AND tal.properties->>'port_name' = $1
ORDER BY tal.event_timestamp DESC
LIMIT 100;

-- Performance notes:
-- - Requires GIN index on properties JSONB
-- - Property lookup can be slow without proper indexing
-- - Expected latency: 30-60ms at scale
