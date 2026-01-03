// =============================================================================
// Shark Bake-Off: Neo4j Schema
// Version: 1.0
// Description: Graph schema with constraints and indexes for KB curation
// =============================================================================

// =============================================================================
// CONSTRAINTS (Uniqueness and existence)
// =============================================================================

// AIR DOMAIN CONSTRAINTS
// Mode-S is the primary identifier - must be unique when present
CREATE CONSTRAINT air_mode_s_unique IF NOT EXISTS
FOR (a:Aircraft) REQUIRE a.mode_s IS UNIQUE;

// Tail number uniqueness
CREATE CONSTRAINT air_tail_unique IF NOT EXISTS
FOR (a:Aircraft) REQUIRE a.tail_number IS UNIQUE;

// Every aircraft must have a shark_name
CREATE CONSTRAINT air_name_exists IF NOT EXISTS
FOR (a:Aircraft) REQUIRE a.shark_name IS NOT NULL;

// MARITIME DOMAIN CONSTRAINTS
// MMSI is the primary identifier
CREATE CONSTRAINT ship_mmsi_unique IF NOT EXISTS
FOR (s:Ship) REQUIRE s.mmsi IS UNIQUE;

// SCONUM uniqueness (military ships)
CREATE CONSTRAINT ship_sconum_unique IF NOT EXISTS
FOR (s:Ship) REQUIRE s.sconum IS UNIQUE;

// IMO number uniqueness
CREATE CONSTRAINT ship_imo_unique IF NOT EXISTS
FOR (s:Ship) REQUIRE s.imo_number IS UNIQUE;

// Every ship must have a shark_name
CREATE CONSTRAINT ship_name_exists IF NOT EXISTS
FOR (s:Ship) REQUIRE s.shark_name IS NOT NULL;

// ORGANIZATION CONSTRAINTS
CREATE CONSTRAINT org_name_unique IF NOT EXISTS
FOR (o:Organization) REQUIRE o.name IS UNIQUE;

// LOCATION CONSTRAINTS
CREATE CONSTRAINT loc_icao_unique IF NOT EXISTS
FOR (l:Location) REQUIRE l.icao_code IS UNIQUE;

// PLATFORM TYPE CONSTRAINTS
CREATE CONSTRAINT platform_name_unique IF NOT EXISTS
FOR (p:Platform) REQUIRE p.name IS UNIQUE;

// =============================================================================
// INDEXES (Performance optimization for lookups)
// =============================================================================

// AIR DOMAIN INDEXES
// Primary lookup indexes
CREATE INDEX air_mode_s_idx IF NOT EXISTS FOR (a:Aircraft) ON (a.mode_s);
CREATE INDEX air_tail_idx IF NOT EXISTS FOR (a:Aircraft) ON (a.tail_number);
CREATE INDEX air_icao_type_idx IF NOT EXISTS FOR (a:Aircraft) ON (a.icao_type_code);

// Property indexes for filtering
CREATE INDEX air_affiliation_idx IF NOT EXISTS FOR (a:Aircraft) ON (a.affiliation);
CREATE INDEX air_nationality_idx IF NOT EXISTS FOR (a:Aircraft) ON (a.nationality);
CREATE INDEX air_operator_idx IF NOT EXISTS FOR (a:Aircraft) ON (a.operator);
CREATE INDEX air_type_idx IF NOT EXISTS FOR (a:Aircraft) ON (a.air_type);

// Curation workflow indexes
CREATE INDEX air_curator_modified_idx IF NOT EXISTS FOR (a:Aircraft) ON (a.curator_modified);
CREATE INDEX air_curator_locked_idx IF NOT EXISTS FOR (a:Aircraft) ON (a.curator_locked);
CREATE INDEX air_source_idx IF NOT EXISTS FOR (a:Aircraft) ON (a.source);

// PostgreSQL reference for hybrid queries
CREATE INDEX air_pg_id_idx IF NOT EXISTS FOR (a:Aircraft) ON (a.pg_id);

// MARITIME DOMAIN INDEXES
// Primary lookup indexes
CREATE INDEX ship_mmsi_idx IF NOT EXISTS FOR (s:Ship) ON (s.mmsi);
CREATE INDEX ship_sconum_idx IF NOT EXISTS FOR (s:Ship) ON (s.sconum);
CREATE INDEX ship_imo_idx IF NOT EXISTS FOR (s:Ship) ON (s.imo_number);
CREATE INDEX ship_callsign_idx IF NOT EXISTS FOR (s:Ship) ON (s.call_sign);

// Property indexes for filtering
CREATE INDEX ship_affiliation_idx IF NOT EXISTS FOR (s:Ship) ON (s.affiliation);
CREATE INDEX ship_nationality_idx IF NOT EXISTS FOR (s:Ship) ON (s.nationality);
CREATE INDEX ship_type_idx IF NOT EXISTS FOR (s:Ship) ON (s.ship_type);
CREATE INDEX ship_class_idx IF NOT EXISTS FOR (s:Ship) ON (s.ship_class);

// Curation workflow indexes
CREATE INDEX ship_curator_modified_idx IF NOT EXISTS FOR (s:Ship) ON (s.curator_modified);
CREATE INDEX ship_curator_locked_idx IF NOT EXISTS FOR (s:Ship) ON (s.curator_locked);
CREATE INDEX ship_source_idx IF NOT EXISTS FOR (s:Ship) ON (s.source);

// PostgreSQL reference for hybrid queries
CREATE INDEX ship_pg_id_idx IF NOT EXISTS FOR (s:Ship) ON (s.pg_id);

// ORGANIZATION INDEXES
CREATE INDEX org_type_idx IF NOT EXISTS FOR (o:Organization) ON (o.org_type);
CREATE INDEX org_country_idx IF NOT EXISTS FOR (o:Organization) ON (o.country);

// LOCATION INDEXES
CREATE INDEX loc_type_idx IF NOT EXISTS FOR (l:Location) ON (l.location_type);
CREATE INDEX loc_country_idx IF NOT EXISTS FOR (l:Location) ON (l.country);
CREATE INDEX loc_icao_idx IF NOT EXISTS FOR (l:Location) ON (l.icao_code);

// PLATFORM INDEXES
CREATE INDEX platform_category_idx IF NOT EXISTS FOR (p:Platform) ON (p.category);

// ACTIVITY INDEXES (for Activity Framework support)
CREATE INDEX activity_type_idx IF NOT EXISTS FOR (a:Activity) ON (a.activity_type);
CREATE INDEX activity_timestamp_idx IF NOT EXISTS FOR (a:Activity) ON (a.event_timestamp);

// =============================================================================
// FULL-TEXT INDEXES (for fuzzy search - separate evaluation per requirements)
// =============================================================================

// Aircraft full-text search
CREATE FULLTEXT INDEX air_fulltext IF NOT EXISTS
FOR (a:Aircraft)
ON EACH [a.shark_name, a.platform, a.operator];

// Ship full-text search
CREATE FULLTEXT INDEX ship_fulltext IF NOT EXISTS
FOR (s:Ship)
ON EACH [s.shark_name, s.platform, s.operator];

// Organization full-text search
CREATE FULLTEXT INDEX org_fulltext IF NOT EXISTS
FOR (o:Organization)
ON EACH [o.name];

// Location full-text search
CREATE FULLTEXT INDEX loc_fulltext IF NOT EXISTS
FOR (l:Location)
ON EACH [l.name];
