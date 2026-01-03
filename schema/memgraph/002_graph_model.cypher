// =============================================================================
// Shark Bake-Off: Memgraph Graph Model
// Version: 1.0
// Description: Graph model documentation for Memgraph
// Note: Node/relationship structure identical to Neo4j, query syntax compatible
// =============================================================================

// =============================================================================
// NODE LABELS AND PROPERTIES
// (Same structure as Neo4j - see neo4j/002_graph_model.cypher for full docs)
// =============================================================================

// Key Node Types:
// :Aircraft - Aircraft instances with Mode-S, tail number, operational envelope
// :Ship - Ship instances with MMSI, SCONUM, IMO, physical characteristics
// :Organization - Operators, manufacturers, military branches
// :Location - Airfields, ports, bases with coordinates
// :Platform - Aircraft/ship class definitions
// :Activity - Event records for Activity Framework

// =============================================================================
// RELATIONSHIP TYPES
// (Same as Neo4j)
// =============================================================================

// Operational: OPERATED_BY, BASED_AT, HOME_PORT
// Platform: INSTANCE_OF
// Hierarchy: PART_OF, HEADQUARTERED_AT
// Activity: PARTICIPATED_IN, OCCURRED_AT
// Co-occurrence: SEEN_WITH, CO_LOCATED_WITH
// Historical: VISITED, LANDED_AT
// Cross-Domain: EMBARKED_ON, OPERATES

// =============================================================================
// MEMGRAPH-SPECIFIC FEATURES
// =============================================================================

// Triggers (Real-time processing)
// Memgraph supports triggers for real-time graph updates
// Useful for Activity Framework knowledge generation

// Example: Auto-create SEEN_WITH relationships when tracks are co-located
// CREATE TRIGGER seen_with_trigger
// ON CREATE BEFORE COMMIT EXECUTE
// CALL module.create_seen_with_relationship(createdVertices);

// =============================================================================
// MAGE PROCEDURES (Memgraph Advanced Graph Extensions)
// =============================================================================

// Community Detection
// CALL community_detection.louvain() YIELD node, community_id
// RETURN node, community_id;

// PageRank for importance scoring
// CALL pagerank.get() YIELD node, rank
// RETURN node, rank
// ORDER BY rank DESC;

// Shortest Path (built-in, no procedure needed)
// MATCH path = shortestPath((a:Aircraft {mode_s: $mode_s})-[*..5]-(o:Organization))
// RETURN path;

// All shortest paths
// MATCH path = allShortestPaths((a:Aircraft)-[*..5]-(o:Organization))
// RETURN path;

// =============================================================================
// SAMPLE BENCHMARK QUERIES (Memgraph optimized)
// =============================================================================

// S1: Simple identifier lookup
MATCH (a:Aircraft {mode_s: $mode_s})
RETURN a.shark_name, a.platform, a.affiliation, a.nationality, a.operator;

// S2: Multi-identifier disambiguation
MATCH (a:Aircraft)
WHERE a.mode_s = $mode_s OR a.tail_number = $tail_number
RETURN a.shark_name, a.platform, a.affiliation;

// S3: Two-hop relationship query
MATCH (a:Aircraft)-[:OPERATED_BY]->(o:Organization)-[:HEADQUARTERED_AT]->(l:Location)
WHERE l.country = $country
RETURN a.shark_name, o.name, l.name;

// S6: Co-occurrence with operator context (3-hop)
MATCH (a:Aircraft)-[:SEEN_WITH]->(b:Aircraft),
      (a)-[:OPERATED_BY]->(o1:Organization),
      (b)-[:OPERATED_BY]->(o2:Organization)
WHERE o1 <> o2
RETURN a.mode_s, b.mode_s, o1.name, o2.name;

// S11: Port visit history
MATCH (s:Ship)-[v:VISITED]->(p:Location {location_type: 'PORT'})
RETURN s.shark_name, p.name, v.timestamp, v.duration_hours
ORDER BY v.timestamp DESC;

// S12: Activity pattern detection
MATCH (s:Ship)-[:PARTICIPATED_IN]->(a:Activity {activity_type: 'UNUSUAL_MOVEMENT'}),
      (s)-[:OPERATED_BY]->(o:Organization)
RETURN s.shark_name, o.name, a.event_timestamp, a.properties;

// =============================================================================
// STREAMING QUERIES (Memgraph specialty)
// =============================================================================

// Memgraph excels at streaming/real-time scenarios
// Can process Kafka streams directly with CALL mg.kafka_stream()

// Example: Process incoming track updates
// CREATE STREAM track_updates
// TRANSFORM transform.track_to_graph
// CONSUME FROM KAFKA "localhost:9092" TOPICS track_updates;

// =============================================================================
// PERFORMANCE NOTES
// =============================================================================

// 1. Memgraph is in-memory by default (faster queries, higher memory usage)
// 2. No need for warm-up queries like Neo4j
// 3. Edge property indexes are fully supported
// 4. Triggers enable real-time graph updates
// 5. Native Kafka integration for streaming updates
