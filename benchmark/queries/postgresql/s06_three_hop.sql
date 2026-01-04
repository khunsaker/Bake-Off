-- =============================================================================
-- S6: Three-Hop Co-Occurrence Query
-- Query: Find aircraft seen together where operators are different
-- Expected p99: 100-200ms+ (complex multi-JOIN with filtering)
-- =============================================================================

-- Find co-located aircraft with different operators
SELECT
    a1.mode_s AS aircraft_1_mode_s,
    a1.shark_name AS aircraft_1_name,
    o1.name AS aircraft_1_operator,
    a2.mode_s AS aircraft_2_mode_s,
    a2.shark_name AS aircraft_2_name,
    o2.name AS aircraft_2_operator,
    r.properties->>'timestamp' AS seen_together_time,
    r.properties->>'location' AS location
FROM kb_relationships r
INNER JOIN air_instance_lookup a1 ON r.source_domain = 'AIR' AND r.source_id = a1.id
INNER JOIN air_instance_lookup a2 ON r.target_domain = 'AIR' AND r.target_id = a2.id
INNER JOIN kb_relationships r1 ON r1.source_domain = 'AIR' AND r1.source_id = a1.id AND r1.relationship_type = 'OPERATED_BY'
INNER JOIN organizations o1 ON r1.target_domain = 'ORGANIZATION' AND r1.target_id = o1.id
INNER JOIN kb_relationships r2 ON r2.source_domain = 'AIR' AND r2.source_id = a2.id AND r2.relationship_type = 'OPERATED_BY'
INNER JOIN organizations o2 ON r2.target_domain = 'ORGANIZATION' AND r2.target_id = o2.id
WHERE r.relationship_type = 'SEEN_WITH'
  AND o1.id <> o2.id;

-- Performance notes:
-- - 6 JOINs with complex filtering
-- - JSONB property extraction (->>) adds overhead
-- - Multiple composite index lookups
-- - Expected latency: 100-300ms at scale
-- - May exceed p99 threshold at 1,000 qps
-- - Query plan likely uses hash joins (memory intensive)

-- Simplified version (if we denormalize operator into aircraft table):
-- Still requires self-join + relationship join
SELECT
    a1.mode_s AS aircraft_1_mode_s,
    a1.shark_name AS aircraft_1_name,
    a1.operator AS aircraft_1_operator,
    a2.mode_s AS aircraft_2_mode_s,
    a2.shark_name AS aircraft_2_name,
    a2.operator AS aircraft_2_operator
FROM track_activity_log tal
INNER JOIN air_instance_lookup a1 ON tal.mode_s = a1.mode_s
CROSS JOIN LATERAL unnest(tal.associated_track_ids) AS assoc_track
INNER JOIN track_activity_log tal2 ON tal2.track_id = assoc_track
INNER JOIN air_instance_lookup a2 ON tal2.mode_s = a2.mode_s
WHERE tal.event_type = 'co_located'
  AND a1.operator <> a2.operator;

-- Performance notes for simplified version:
-- - Requires denormalization of co-occurrence into activity log
-- - unnest() on array can be expensive
-- - Still 3+ JOINs with filtering
-- - Expected latency: 50-150ms at scale
-- - Better than relationship table approach, but still slow
