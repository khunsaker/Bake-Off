// =============================================================================
// S1: Simple Identifier Lookup (Memgraph)
// Query: Find aircraft by Mode-S identifier
// Expected p99: < 5ms (in-memory, unique constraint index)
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
// - Memgraph is in-memory by default (faster than Neo4j disk-based)
// - Uses unique constraint index on mode_s/mmsi
// - No warm-up required (unlike Neo4j)
// - Expected latency: 0.5-3ms at scale
// - Fastest of all three databases for simple lookups
