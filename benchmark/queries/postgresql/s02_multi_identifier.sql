-- =============================================================================
-- S2: Multi-Identifier Disambiguation
-- Query: Find aircraft by any known identifier (Mode-S OR Tail Number)
-- Expected p99: < 15ms (multiple index lookups)
-- =============================================================================

-- Air domain: Find by Mode-S or Tail Number
SELECT
    shark_name,
    platform,
    affiliation,
    nationality,
    operator,
    mode_s,
    tail_number
FROM air_instance_lookup
WHERE mode_s = $1 OR tail_number = $2;

-- Maritime domain: Find by MMSI, SCONUM, or IMO
SELECT
    shark_name,
    platform,
    affiliation,
    nationality,
    operator,
    mmsi,
    sconum,
    imo_number
FROM ship_instance_lookup
WHERE mmsi = $1 OR sconum = $2 OR imo_number = $3;

-- Performance notes:
-- - Uses bitmap index scan combining multiple indexes
-- - OR conditions can prevent index-only scans
-- - May require heap access for disambiguation
-- - Expected latency: 5-15ms at scale
