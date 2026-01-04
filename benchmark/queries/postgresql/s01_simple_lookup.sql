-- =============================================================================
-- S1: Simple Identifier Lookup
-- Query: Find aircraft by Mode-S identifier
-- Expected p99: < 10ms (covering index, zero heap fetch)
-- =============================================================================

-- Air domain lookup by Mode-S
SELECT
    shark_name,
    platform,
    affiliation,
    nationality,
    operator,
    air_type,
    air_model
FROM air_instance_lookup
WHERE mode_s = $1;

-- Maritime domain lookup by MMSI
SELECT
    shark_name,
    platform,
    affiliation,
    nationality,
    operator,
    ship_type,
    ship_class
FROM ship_instance_lookup
WHERE mmsi = $1;

-- Performance notes:
-- - Uses idx_air_mode_s_covering (includes all returned columns)
-- - Should be index-only scan (no heap access)
-- - Expected latency: 1-5ms at scale
