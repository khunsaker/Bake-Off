-- =============================================================================
-- Shark Bake-Off: PostgreSQL Schema
-- Version: 1.0
-- Description: Denormalized lookup tables optimized for identifier queries
-- =============================================================================

-- =============================================================================
-- AIR DOMAIN
-- =============================================================================

-- Main aircraft lookup table (denormalized for fast lookups)
CREATE TABLE air_instance_lookup (
    id BIGSERIAL PRIMARY KEY,

    -- Unique identifiers
    mode_s VARCHAR(8),                      -- Primary lookup key (hex, e.g., 'A1B2C3')
    tail_number VARCHAR(20),                -- Registration number (e.g., 'N12345')
    icao_type_code VARCHAR(4),              -- ICAO aircraft type (e.g., 'B738')

    -- Core properties
    shark_name VARCHAR(255) NOT NULL,       -- Display name
    platform VARCHAR(255),                  -- Platform name (e.g., 'F-15E Strike Eagle')
    affiliation VARCHAR(100),               -- Military/civilian affiliation
    nationality VARCHAR(100),               -- Country of registration/operation
    operator VARCHAR(255),                  -- Operating organization

    -- Aircraft classification
    air_type VARCHAR(255),                  -- Type category (Fighter, Bomber, etc.)
    air_model VARCHAR(255),                 -- Specific model variant
    air_role VARCHAR(100),                  -- Primary role

    -- Operational envelope (for AI sanity checking)
    max_altitude_ft INTEGER,                -- Maximum altitude in feet
    min_altitude_ft INTEGER,                -- Minimum operational altitude
    max_speed_kts INTEGER,                  -- Maximum speed in knots
    min_speed_kts INTEGER,                  -- Stall speed / minimum
    typical_cruise_altitude_ft INTEGER,     -- Normal cruise altitude
    typical_cruise_speed_kts INTEGER,       -- Normal cruise speed

    -- Metadata
    neo4j_node_id BIGINT,                   -- Reference to Neo4j node (for hybrid)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Data lineage
    source VARCHAR(100),                    -- Data source
    source_timestamp TIMESTAMPTZ,           -- When source provided data
    curator_modified BOOLEAN DEFAULT FALSE, -- Has curator touched this?
    curator_id VARCHAR(50),                 -- Who modified it
    curator_locked BOOLEAN DEFAULT FALSE    -- Prevent source overwrites
);

-- =============================================================================
-- MARITIME DOMAIN
-- =============================================================================

-- Main ship lookup table (denormalized for fast lookups)
CREATE TABLE ship_instance_lookup (
    id BIGSERIAL PRIMARY KEY,

    -- Unique identifiers
    mmsi VARCHAR(9),                        -- Maritime Mobile Service Identity
    sconum VARCHAR(20),                     -- Ship Control Number (military)
    imo_number VARCHAR(10),                 -- IMO ship identification number
    call_sign VARCHAR(10),                  -- Radio call sign

    -- Core properties
    shark_name VARCHAR(255) NOT NULL,       -- Display name
    platform VARCHAR(255),                  -- Platform name (e.g., 'Arleigh Burke-class')
    affiliation VARCHAR(100),               -- Military/civilian affiliation
    nationality VARCHAR(100),               -- Flag state
    operator VARCHAR(255),                  -- Operating organization

    -- Ship classification
    ship_type VARCHAR(255),                 -- Type category (Destroyer, Carrier, etc.)
    ship_class VARCHAR(255),                -- Class name
    ship_role VARCHAR(100),                 -- Primary role

    -- Physical characteristics
    length_meters DECIMAL(10,2),            -- Length overall
    beam_meters DECIMAL(10,2),              -- Width
    draft_meters DECIMAL(10,2),             -- Draft
    displacement_tons INTEGER,              -- Displacement

    -- Operational envelope
    max_speed_kts INTEGER,                  -- Maximum speed
    typical_speed_kts INTEGER,              -- Cruise speed

    -- Metadata
    neo4j_node_id BIGINT,                   -- Reference to Neo4j node
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Data lineage
    source VARCHAR(100),
    source_timestamp TIMESTAMPTZ,
    curator_modified BOOLEAN DEFAULT FALSE,
    curator_id VARCHAR(50),
    curator_locked BOOLEAN DEFAULT FALSE
);

-- =============================================================================
-- ACTIVITY LOGGING (for knowledge generation)
-- =============================================================================

CREATE TABLE track_activity_log (
    id BIGSERIAL PRIMARY KEY,

    -- Track identification
    track_id VARCHAR(50) NOT NULL,          -- External track ID
    domain VARCHAR(20) NOT NULL,            -- 'AIR' or 'MARITIME'

    -- Activity details
    event_type VARCHAR(50) NOT NULL,        -- 'identified', 'updated', 'activity_detected'
    activity_type VARCHAR(100),             -- 'air_refueling', 'port_call', etc.

    -- KB association
    kb_object_id BIGINT,                    -- ID in lookup table
    mode_s VARCHAR(8),                      -- Air identifier
    mmsi VARCHAR(9),                        -- Maritime identifier

    -- Temporal
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Location (optional)
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),

    -- Flexible payload
    properties JSONB,                       -- Additional event data

    -- Associated entities (for relationship creation)
    associated_track_ids TEXT[],            -- Other tracks involved
    associated_kb_ids BIGINT[]              -- Other KB objects involved
);

-- Partition activity log by time for efficient archival
-- (Partitioning setup would be added for production)

-- =============================================================================
-- RELATIONSHIP TABLES (for graph-like queries in PostgreSQL)
-- =============================================================================

-- Generic relationship table for multi-hop queries
CREATE TABLE kb_relationships (
    id BIGSERIAL PRIMARY KEY,

    -- Source entity
    source_domain VARCHAR(20) NOT NULL,     -- 'AIR', 'MARITIME', 'ORGANIZATION', etc.
    source_id BIGINT NOT NULL,

    -- Target entity
    target_domain VARCHAR(20) NOT NULL,
    target_id BIGINT NOT NULL,

    -- Relationship
    relationship_type VARCHAR(100) NOT NULL, -- 'OPERATED_BY', 'BASED_AT', 'SEEN_WITH', etc.

    -- Properties
    properties JSONB,

    -- Temporal (for time-bounded relationships)
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    source VARCHAR(100),                    -- Data source
    confidence DECIMAL(3,2)                 -- Confidence score 0.00-1.00
);

-- =============================================================================
-- SUPPORTING TABLES
-- =============================================================================

-- Organizations (operators, manufacturers, etc.)
CREATE TABLE organizations (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    org_type VARCHAR(100),                  -- 'MILITARY', 'CIVILIAN', 'GOVERNMENT'
    country VARCHAR(100),
    parent_org_id BIGINT REFERENCES organizations(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Locations (airfields, ports, bases)
CREATE TABLE locations (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location_type VARCHAR(100),             -- 'AIRFIELD', 'PORT', 'BASE'
    icao_code VARCHAR(4),                   -- For airfields
    country VARCHAR(100),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- INDEXES (Covering indexes for zero-heap-fetch lookups)
-- =============================================================================

-- AIR DOMAIN INDEXES
-- Primary lookup by Mode-S (most common query path)
CREATE INDEX idx_air_mode_s_covering ON air_instance_lookup (mode_s)
    INCLUDE (shark_name, platform, affiliation, nationality, operator, air_type, air_model);

-- Secondary lookup by tail number
CREATE INDEX idx_air_tail_covering ON air_instance_lookup (tail_number)
    INCLUDE (shark_name, platform, affiliation, nationality, operator, mode_s);

-- ICAO type code lookup (for type-based queries)
CREATE INDEX idx_air_icao_type ON air_instance_lookup (icao_type_code);

-- Neo4j reference for hybrid queries
CREATE INDEX idx_air_neo4j_node ON air_instance_lookup (neo4j_node_id);

-- Curator workflow indexes
CREATE INDEX idx_air_curator_modified ON air_instance_lookup (curator_modified) WHERE curator_modified = TRUE;
CREATE INDEX idx_air_curator_locked ON air_instance_lookup (curator_locked) WHERE curator_locked = TRUE;

-- MARITIME DOMAIN INDEXES
-- Primary lookup by MMSI (most common for AIS data)
CREATE INDEX idx_ship_mmsi_covering ON ship_instance_lookup (mmsi)
    INCLUDE (shark_name, platform, affiliation, nationality, operator, ship_type, ship_class);

-- SCONUM lookup (military identifier)
CREATE INDEX idx_ship_sconum_covering ON ship_instance_lookup (sconum)
    INCLUDE (shark_name, platform, affiliation, nationality, operator, mmsi);

-- IMO number lookup (international identifier)
CREATE INDEX idx_ship_imo_covering ON ship_instance_lookup (imo_number)
    INCLUDE (shark_name, platform, affiliation, nationality, mmsi);

-- Call sign lookup
CREATE INDEX idx_ship_callsign ON ship_instance_lookup (call_sign);

-- Neo4j reference for hybrid queries
CREATE INDEX idx_ship_neo4j_node ON ship_instance_lookup (neo4j_node_id);

-- Curator workflow indexes
CREATE INDEX idx_ship_curator_modified ON ship_instance_lookup (curator_modified) WHERE curator_modified = TRUE;
CREATE INDEX idx_ship_curator_locked ON ship_instance_lookup (curator_locked) WHERE curator_locked = TRUE;

-- ACTIVITY LOG INDEXES
-- Time-series queries (most recent activities)
CREATE INDEX idx_activity_timestamp ON track_activity_log (event_timestamp DESC);

-- Track lookup with time ordering
CREATE INDEX idx_activity_track_time ON track_activity_log (track_id, event_timestamp DESC);

-- Domain filtering
CREATE INDEX idx_activity_domain ON track_activity_log (domain, event_timestamp DESC);

-- Activity type queries (for pattern analysis)
CREATE INDEX idx_activity_type ON track_activity_log (activity_type, event_timestamp DESC);

-- KB object association
CREATE INDEX idx_activity_kb_object ON track_activity_log (kb_object_id);

-- Identifier-specific lookups
CREATE INDEX idx_activity_mode_s ON track_activity_log (mode_s) WHERE mode_s IS NOT NULL;
CREATE INDEX idx_activity_mmsi ON track_activity_log (mmsi) WHERE mmsi IS NOT NULL;

-- JSONB index for flexible property queries
CREATE INDEX idx_activity_properties ON track_activity_log USING GIN (properties);

-- Associated entities (for relationship queries)
CREATE INDEX idx_activity_associated_tracks ON track_activity_log USING GIN (associated_track_ids);
CREATE INDEX idx_activity_associated_kb ON track_activity_log USING GIN (associated_kb_ids);

-- RELATIONSHIP TABLE INDEXES
-- Source entity lookup (for outbound traversal)
CREATE INDEX idx_rel_source ON kb_relationships (source_domain, source_id);

-- Target entity lookup (for inbound traversal)
CREATE INDEX idx_rel_target ON kb_relationships (target_domain, target_id);

-- Relationship type queries
CREATE INDEX idx_rel_type ON kb_relationships (relationship_type);

-- Combined index for graph-like traversal
CREATE INDEX idx_rel_traversal ON kb_relationships (source_domain, source_id, relationship_type);

-- Time-bounded relationship queries
CREATE INDEX idx_rel_temporal ON kb_relationships (valid_from, valid_to)
    WHERE valid_from IS NOT NULL OR valid_to IS NOT NULL;

-- SUPPORTING TABLE INDEXES
CREATE INDEX idx_org_name ON organizations (name);
CREATE INDEX idx_org_country ON organizations (country);
CREATE INDEX idx_org_parent ON organizations (parent_org_id);

CREATE INDEX idx_loc_name ON locations (name);
CREATE INDEX idx_loc_type ON locations (location_type);
CREATE INDEX idx_loc_icao ON locations (icao_code) WHERE icao_code IS NOT NULL;
CREATE INDEX idx_loc_country ON locations (country);

-- Geospatial index for location proximity queries
CREATE INDEX idx_loc_coords ON locations (latitude, longitude);
