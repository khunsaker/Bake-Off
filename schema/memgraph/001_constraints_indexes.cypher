// =============================================================================
// Shark Bake-Off: Memgraph Schema
// Version: 1.0
// Description: Graph schema with constraints and indexes for KB curation
// Note: Memgraph uses different syntax from Neo4j for constraints/indexes
// =============================================================================

// =============================================================================
// CONSTRAINTS (Uniqueness)
// Note: Memgraph constraint syntax differs from Neo4j
// =============================================================================

// AIR DOMAIN CONSTRAINTS
CREATE CONSTRAINT ON (a:Aircraft) ASSERT a.mode_s IS UNIQUE;
CREATE CONSTRAINT ON (a:Aircraft) ASSERT a.tail_number IS UNIQUE;
CREATE CONSTRAINT ON (a:Aircraft) ASSERT EXISTS (a.shark_name);

// MARITIME DOMAIN CONSTRAINTS
CREATE CONSTRAINT ON (s:Ship) ASSERT s.mmsi IS UNIQUE;
CREATE CONSTRAINT ON (s:Ship) ASSERT s.sconum IS UNIQUE;
CREATE CONSTRAINT ON (s:Ship) ASSERT s.imo_number IS UNIQUE;
CREATE CONSTRAINT ON (s:Ship) ASSERT EXISTS (s.shark_name);

// ORGANIZATION CONSTRAINTS
CREATE CONSTRAINT ON (o:Organization) ASSERT o.name IS UNIQUE;

// LOCATION CONSTRAINTS
CREATE CONSTRAINT ON (l:Location) ASSERT l.icao_code IS UNIQUE;

// PLATFORM CONSTRAINTS
CREATE CONSTRAINT ON (p:Platform) ASSERT p.name IS UNIQUE;

// =============================================================================
// INDEXES (Label-Property indexes for fast lookups)
// Note: Memgraph automatically creates indexes for constraint properties
// =============================================================================

// AIR DOMAIN INDEXES
// Primary lookup indexes (beyond constraint-created ones)
CREATE INDEX ON :Aircraft(icao_type_code);
CREATE INDEX ON :Aircraft(affiliation);
CREATE INDEX ON :Aircraft(nationality);
CREATE INDEX ON :Aircraft(operator);
CREATE INDEX ON :Aircraft(air_type);

// Curation workflow indexes
CREATE INDEX ON :Aircraft(curator_modified);
CREATE INDEX ON :Aircraft(curator_locked);
CREATE INDEX ON :Aircraft(source);

// PostgreSQL reference for hybrid queries
CREATE INDEX ON :Aircraft(pg_id);

// MARITIME DOMAIN INDEXES
CREATE INDEX ON :Ship(call_sign);
CREATE INDEX ON :Ship(affiliation);
CREATE INDEX ON :Ship(nationality);
CREATE INDEX ON :Ship(ship_type);
CREATE INDEX ON :Ship(ship_class);

// Curation workflow indexes
CREATE INDEX ON :Ship(curator_modified);
CREATE INDEX ON :Ship(curator_locked);
CREATE INDEX ON :Ship(source);

// PostgreSQL reference for hybrid queries
CREATE INDEX ON :Ship(pg_id);

// ORGANIZATION INDEXES
CREATE INDEX ON :Organization(org_type);
CREATE INDEX ON :Organization(country);

// LOCATION INDEXES
CREATE INDEX ON :Location(location_type);
CREATE INDEX ON :Location(country);

// PLATFORM INDEXES
CREATE INDEX ON :Platform(category);

// ACTIVITY INDEXES
CREATE INDEX ON :Activity(activity_type);
CREATE INDEX ON :Activity(event_timestamp);

// =============================================================================
// EDGE TYPE INDEXES (Memgraph supports edge indexes)
// =============================================================================

// Relationship property indexes for temporal queries
CREATE INDEX ON :SEEN_WITH(timestamp);
CREATE INDEX ON :VISITED(timestamp);
CREATE INDEX ON :LANDED_AT(timestamp);
CREATE INDEX ON :PARTICIPATED_IN(timestamp);
