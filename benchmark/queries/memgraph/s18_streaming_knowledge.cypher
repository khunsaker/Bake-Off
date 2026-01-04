// =============================================================================
// S18: Real-Time Streaming Knowledge Generation (Memgraph Specialty)
// Query: Process Kafka stream to create relationships in real-time
// Expected p99: < 10ms per event (streaming ingestion)
// =============================================================================

// Create a Kafka stream consumer for track updates
// This is Memgraph's killer feature for real-time knowledge base
CREATE STREAM track_updates
TOPICS tracks
TRANSFORM track_processor.transform
CONSUMER_GROUP shark_kb
BATCH_SIZE 100;

// The transform function (implemented in Python/C++ via MAGE):
// - Receives track position update from Kafka
// - Looks up existing Aircraft/Ship node by identifier
// - Creates/updates SEEN_WITH relationships for co-located entities
// - All in real-time as data arrives

// Example trigger for automatic relationship creation
CREATE TRIGGER auto_create_seen_with
ON CREATE BEFORE COMMIT EXECUTE
CALL relationship_generator.create_co_occurrence($createdVertices, $createdEdges);

// Performance notes:
// - No batch ETL required
// - Relationships created within milliseconds of track update
// - Enables real-time knowledge generation
// - This is where Memgraph excels vs Neo4j

// Query to monitor streaming performance
CALL mg.kafka_stream_status('track_updates')
YIELD stream_name, status, topics, consumer_group, batch_size, messages_consumed
RETURN stream_name, status, messages_consumed;

// =============================================================================
// Real-Time Pattern Detection
// =============================================================================

// Once relationships are streaming in, queries run on live data:

// Find aircraft co-located RIGHT NOW (based on last 5 min of data)
MATCH (a1:Aircraft)-[seen:SEEN_WITH]->(a2:Aircraft)
WHERE seen.timestamp >= localDateTime() - duration({minutes: 5})
  AND a1.mode_s < a2.mode_s  // Avoid duplicates
MATCH (a1)-[:OPERATED_BY]->(o1:Organization)
MATCH (a2)-[:OPERATED_BY]->(o2:Organization)
WHERE o1.country <> o2.country
RETURN a1.mode_s AS aircraft_1,
       a1.shark_name AS name_1,
       o1.name AS operator_1,
       a2.mode_s AS aircraft_2,
       a2.shark_name AS name_2,
       o2.name AS operator_2,
       seen.location AS location,
       seen.timestamp AS when_seen
ORDER BY seen.timestamp DESC
LIMIT 20;

// Performance notes:
// - Query runs on data that arrived seconds ago
// - No latency from batch processing
// - Expected query time: 10-30ms
// - Total latency (Kafka → Query result): < 100ms

// =============================================================================
// Anomaly Detection (Real-Time)
// =============================================================================

// Detect unusual co-occurrence patterns as they happen
MATCH (a:Aircraft {mode_s: $mode_s})-[seen:SEEN_WITH]->(other:Aircraft)
WHERE seen.timestamp >= localDateTime() - duration({hours: 1})
MATCH (a)-[:OPERATED_BY]->(o1:Organization)
MATCH (other)-[:OPERATED_BY]->(o2:Organization)
WITH a, other, o1, o2, COUNT(seen) AS co_occurrence_count
WHERE o1.affiliation = 'MILITARY'
  AND o2.affiliation = 'CIVILIAN'
  AND co_occurrence_count >= 3  // Multiple sightings in 1 hour
RETURN a.mode_s AS military_aircraft,
       other.mode_s AS civilian_aircraft,
       other.shark_name AS civilian_name,
       o2.name AS civilian_operator,
       co_occurrence_count AS sightings
ORDER BY co_occurrence_count DESC;

// This query enables real-time alerting for:
// - Unusual military-civilian interactions
// - Aircraft following patterns
// - Suspicious co-locations
// All with < 100ms total latency from event to alert

// =============================================================================
// Comparison to Batch Approaches
// =============================================================================

// PostgreSQL approach:
// 1. Track data → Kafka → Batch job (5-10 min)
// 2. ETL to track_activity_log table
// 3. Query activity log with complex JOINs
// Total latency: 5-10 minutes + query time (50-100ms)

// Neo4j approach:
// 1. Track data → Kafka → Batch job (1-5 min)
// 2. Cypher MERGE statements
// 3. Query graph
// Total latency: 1-5 minutes + query time (20-50ms)

// Memgraph approach:
// 1. Track data → Kafka → Memgraph stream (< 1 sec)
// 2. Query graph
// Total latency: < 1 second + query time (10-30ms)

// Memgraph enables true real-time knowledge base
