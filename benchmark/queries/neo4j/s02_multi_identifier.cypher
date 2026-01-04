// =============================================================================
// S2: Multi-Identifier Disambiguation
// Query: Find aircraft by any known identifier
// Expected p99: < 10ms (indexed OR conditions)
// =============================================================================

// Air domain: Find by Mode-S or Tail Number
MATCH (a:Aircraft)
WHERE a.mode_s = $mode_s OR a.tail_number = $tail_number
RETURN a.shark_name AS shark_name,
       a.platform AS platform,
       a.affiliation AS affiliation,
       a.nationality AS nationality,
       a.operator AS operator,
       a.mode_s AS mode_s,
       a.tail_number AS tail_number;

// Maritime domain: Find by MMSI, SCONUM, or IMO
MATCH (s:Ship)
WHERE s.mmsi = $mmsi OR s.sconum = $sconum OR s.imo_number = $imo_number
RETURN s.shark_name AS shark_name,
       s.platform AS platform,
       s.affiliation AS affiliation,
       s.nationality AS nationality,
       s.operator AS operator,
       s.mmsi AS mmsi,
       s.sconum AS sconum,
       s.imo_number AS imo_number;

// Performance notes:
// - Uses index on each identifier property
// - OR conditions evaluated efficiently with index union
// - Expected latency: 2-10ms at scale
// - Comparable to PostgreSQL for this scenario
