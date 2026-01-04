// =============================================================================
// S1: Simple Identifier Lookup
// Query: Find aircraft by Mode-S identifier
// Expected p99: < 10ms (unique constraint index)
// =============================================================================

// Air domain lookup by Mode-S
MATCH (a:Aircraft {mode_s: $mode_s})
RETURN a.shark_name AS shark_name,
       a.platform AS platform,
       a.affiliation AS affiliation,
       a.nationality AS nationality,
       a.operator AS operator,
       a.air_type AS air_type,
       a.air_model AS air_model;

// Maritime domain lookup by MMSI
MATCH (s:Ship {mmsi: $mmsi})
RETURN s.shark_name AS shark_name,
       s.platform AS platform,
       s.affiliation AS affiliation,
       s.nationality AS nationality,
       s.operator AS operator,
       s.ship_type AS ship_type,
       s.ship_class AS ship_class;

// Performance notes:
// - Uses unique constraint index on mode_s/mmsi
// - Single node lookup with property access
// - Expected latency: 1-5ms at scale
// - Comparable to PostgreSQL for simple lookups
