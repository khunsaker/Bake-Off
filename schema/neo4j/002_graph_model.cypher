// =============================================================================
// Shark Bake-Off: Neo4j Graph Model
// Version: 1.0
// Description: Sample data structure showing node labels, properties, and relationships
// =============================================================================

// =============================================================================
// NODE LABELS AND PROPERTIES
// =============================================================================

// Aircraft Node
// Labels: :Aircraft, optionally :Military or :Civilian
// (:Aircraft {
//     mode_s: "A1B2C3",              -- Primary identifier (hex)
//     tail_number: "N12345",          -- Registration number
//     icao_type_code: "B738",         -- ICAO aircraft type
//     shark_name: "Boeing 737-800",   -- Display name
//     platform: "F-15E Strike Eagle", -- Platform name
//     affiliation: "MILITARY",        -- Military/civilian
//     nationality: "USA",             -- Country
//     operator: "USAF",               -- Operating organization
//     air_type: "Fighter",            -- Type category
//     air_model: "F-15E",             -- Specific model
//     air_role: "Strike",             -- Primary role
//
//     -- Operational envelope (AI sanity checking)
//     max_altitude_ft: 60000,
//     min_altitude_ft: 0,
//     max_speed_kts: 1650,
//     min_speed_kts: 130,
//     typical_cruise_altitude_ft: 35000,
//     typical_cruise_speed_kts: 570,
//
//     -- Data lineage
//     source: "external_feed_1",
//     source_timestamp: datetime(),
//     curator_modified: false,
//     curator_id: null,
//     curator_locked: false,
//
//     -- Cross-reference
//     pg_id: 12345,                   -- PostgreSQL ID for hybrid
//     created_at: datetime(),
//     updated_at: datetime()
// })

// Ship Node
// Labels: :Ship, optionally :Military or :Civilian
// (:Ship {
//     mmsi: "123456789",              -- Maritime Mobile Service Identity
//     sconum: "SCO12345",             -- Ship Control Number (military)
//     imo_number: "IMO1234567",       -- IMO identification
//     call_sign: "ABCD",              -- Radio call sign
//     shark_name: "USS Enterprise",   -- Display name
//     platform: "Nimitz-class",       -- Platform name
//     affiliation: "MILITARY",
//     nationality: "USA",
//     operator: "US Navy",
//     ship_type: "Aircraft Carrier",
//     ship_class: "Nimitz",
//     ship_role: "Power Projection",
//
//     -- Physical characteristics
//     length_meters: 332.8,
//     beam_meters: 76.8,
//     draft_meters: 11.3,
//     displacement_tons: 100000,
//
//     -- Operational envelope
//     max_speed_kts: 30,
//     typical_speed_kts: 20,
//
//     -- Data lineage (same as Aircraft)
//     source: "ais_feed",
//     curator_modified: false,
//     curator_locked: false,
//     pg_id: 67890
// })

// Organization Node
// (:Organization {
//     name: "US Navy",
//     org_type: "MILITARY",
//     country: "USA"
// })

// Location Node
// Labels: :Location, optionally :Airfield, :Port, :Base
// (:Location {
//     name: "Naval Station Norfolk",
//     location_type: "PORT",
//     icao_code: null,                -- For airfields only
//     country: "USA",
//     latitude: 36.9461,
//     longitude: -76.3134
// })

// Platform Node (aircraft/ship class definitions)
// (:Platform {
//     name: "F-15E Strike Eagle",
//     category: "AIR",                -- AIR or MARITIME
//     manufacturer: "Boeing",
//
//     -- Operational envelope (canonical values)
//     max_altitude_ft: 60000,
//     max_speed_kts: 1650,
//     min_speed_kts: 130
// })

// Activity Node (for Activity Framework)
// (:Activity {
//     activity_type: "PORT_CALL",
//     event_timestamp: datetime(),
//     properties: { duration_hours: 48 }
// })

// =============================================================================
// RELATIONSHIP TYPES
// =============================================================================

// Operational Relationships
// (:Aircraft)-[:OPERATED_BY]->(:Organization)
// (:Ship)-[:OPERATED_BY]->(:Organization)
// (:Aircraft)-[:BASED_AT]->(:Location)
// (:Ship)-[:HOME_PORT]->(:Location)

// Platform/Type Relationships
// (:Aircraft)-[:INSTANCE_OF]->(:Platform)
// (:Ship)-[:INSTANCE_OF]->(:Platform)

// Organizational Hierarchy
// (:Organization)-[:PART_OF]->(:Organization)
// (:Organization)-[:HEADQUARTERED_AT]->(:Location)

// Activity Framework Relationships
// (:Aircraft)-[:PARTICIPATED_IN]->(:Activity)
// (:Ship)-[:PARTICIPATED_IN]->(:Activity)
// (:Activity)-[:OCCURRED_AT]->(:Location)

// Co-occurrence Relationships (Knowledge Generation)
// (:Aircraft)-[:SEEN_WITH {timestamp: datetime(), location: point()}]->(:Aircraft)
// (:Ship)-[:SEEN_WITH {timestamp: datetime(), location: point()}]->(:Ship)
// (:Aircraft)-[:CO_LOCATED_WITH]->(:Ship)

// Historical Relationships
// (:Ship)-[:VISITED {timestamp: datetime(), duration_hours: int}]->(:Location)
// (:Aircraft)-[:LANDED_AT {timestamp: datetime()}]->(:Location)

// Cross-Domain Relationships
// (:Aircraft)-[:EMBARKED_ON]->(:Ship)  -- Aircraft carriers
// (:Organization)-[:OPERATES]->(:Location)

// =============================================================================
// SAMPLE MULTI-HOP QUERY PATTERNS
// =============================================================================

// S3: Find all aircraft operated by organizations based in a specific country
// MATCH (a:Aircraft)-[:OPERATED_BY]->(o:Organization)-[:HEADQUARTERED_AT]->(l:Location)
// WHERE l.country = 'USA'
// RETURN a.shark_name, o.name, l.name

// S6: Find co-located entities and their operators
// MATCH (a:Aircraft)-[:SEEN_WITH]->(b:Aircraft)
// MATCH (a)-[:OPERATED_BY]->(o1:Organization)
// MATCH (b)-[:OPERATED_BY]->(o2:Organization)
// WHERE o1 <> o2
// RETURN a.mode_s, b.mode_s, o1.name, o2.name

// S11: Port visit history with duration
// MATCH (s:Ship)-[v:VISITED]->(p:Location)
// WHERE p.location_type = 'PORT'
// RETURN s.shark_name, p.name, v.timestamp, v.duration_hours
// ORDER BY v.timestamp DESC

// S12: Activity pattern detection
// MATCH (s:Ship)-[:PARTICIPATED_IN]->(a:Activity)
// WHERE a.activity_type = 'UNUSUAL_MOVEMENT'
// MATCH (s)-[:OPERATED_BY]->(o:Organization)
// RETURN s.shark_name, o.name, a.event_timestamp, a.properties

// =============================================================================
// APOC PROCEDURES FOR ADVANCED QUERIES
// =============================================================================

// Variable-length path queries (requires APOC)
// CALL apoc.path.expandConfig(startNode, {
//     relationshipFilter: "OPERATED_BY|PART_OF",
//     minLevel: 1,
//     maxLevel: 3
// }) YIELD path
// RETURN path

// Shortest path between entities
// MATCH path = shortestPath((a:Aircraft {mode_s: $mode_s})-[*..5]-(o:Organization {name: $orgName}))
// RETURN path
