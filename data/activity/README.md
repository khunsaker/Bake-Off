# Activity Storage & Message Queue

This directory contains the Activity Storage system for the Shark Bake-Off benchmark. Activity events are streamed from API services through Kafka and batch-written to PostgreSQL for knowledge generation.

## Architecture

```
┌─────────────────┐
│   API Services  │ (Rust, Python, Go, Java)
│                 │
│  - Lookups      │
│  - Queries      │
│  - Activity     │
└────────┬────────┘
         │ Activity Events
         ▼
┌─────────────────┐
│     Kafka       │
│                 │
│  Topic:         │
│  activity-events│
└────────┬────────┘
         │ Batch Consume
         ▼
┌─────────────────┐
│  Activity       │
│  Consumer       │
│  (Python)       │
│                 │
│  - Batch 100    │
│  - Timeout 5s   │
└────────┬────────┘
         │ Batch Insert
         ▼
┌─────────────────┐
│  PostgreSQL     │
│                 │
│  track_activity │
│  _log table     │
└─────────────────┘
```

## Components

### 1. Kafka Topics

**activity-events**
- Partitions: 3
- Replication: 1 (dev/test)
- Retention: 7 days
- Compression: Snappy

**activity-events-dlq**
- Dead Letter Queue for failed messages
- Retention: 30 days

### 2. Activity Consumer (`consumer.py`)

Python consumer that:
- Subscribes to `activity-events` topic
- Batches messages (100 or 5 seconds)
- Batch inserts to PostgreSQL
- Commits Kafka offsets on success

#### Running the Consumer

```bash
# Install dependencies
pip install -r requirements.txt

# Run consumer
python consumer.py
```

#### Configuration (Environment Variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka brokers |
| `KAFKA_TOPIC` | `activity-events` | Topic to consume |
| `KAFKA_GROUP_ID` | `activity-consumer-group` | Consumer group |
| `POSTGRES_DSN` | See below | PostgreSQL connection |
| `BATCH_SIZE` | `100` | Messages per batch |
| `BATCH_TIMEOUT` | `5.0` | Seconds before flush |

Default PostgreSQL DSN:
```
postgresql://shark:sharkbakeoff@localhost:5432/sharkdb
```

### 3. Activity Producer (`producer.py`)

Python library for publishing activity events to Kafka.

#### Usage Example

```python
from producer import get_producer

producer = get_producer()

producer.send_event(
    track_id='T-12345',
    event_type='activity_detected',
    domain='AIR',
    mode_s='A12345',
    activity_type='air_refueling',
    latitude=35.123,
    longitude=-118.456,
    properties={'altitude_ft': 25000, 'speed_kts': 350}
)

producer.flush()
```

## Event Schema

Activity events follow this JSON schema:

```json
{
  "track_id": "string",           // External track ID
  "domain": "AIR|MARITIME",       // Domain
  "event_type": "string",         // Event type
  "activity_type": "string?",     // Specific activity
  "kb_object_id": "integer?",     // KB lookup table ID
  "mode_s": "string?",            // Aircraft identifier
  "mmsi": "string?",              // Ship identifier
  "event_timestamp": "ISO8601",   // UTC timestamp
  "latitude": "float?",           // Latitude
  "longitude": "float?",          // Longitude
  "properties": {},               // Flexible JSON
  "associated_track_ids": [],     // Related tracks
  "associated_kb_ids": []         // Related KB objects
}
```

## Event Types

| Event Type | Description | Use Case |
|------------|-------------|----------|
| `identified` | Track identified with KB object | Link live track to KB |
| `updated` | KB object updated | Curation change notification |
| `activity_detected` | Specific activity observed | Knowledge generation |

## Activity Types

| Activity Type | Domain | Description |
|---------------|--------|-------------|
| `air_refueling` | AIR | In-flight refueling detected |
| `formation_flight` | AIR | Multiple aircraft in formation |
| `port_call` | MARITIME | Ship entering/leaving port |
| `refueling_stop` | MARITIME | Ship at fuel dock |
| `convoy` | MARITIME | Ships traveling together |
| `rendezvous` | BOTH | Two entities meeting |

## Database Schema

### PostgreSQL Table: `track_activity_log`

```sql
CREATE TABLE track_activity_log (
    id BIGSERIAL PRIMARY KEY,
    track_id VARCHAR(50) NOT NULL,
    domain VARCHAR(20) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    activity_type VARCHAR(100),
    kb_object_id BIGINT,
    mode_s VARCHAR(8),
    mmsi VARCHAR(9),
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    properties JSONB,
    associated_track_ids TEXT[],
    associated_kb_ids BIGINT[]
);
```

### Indexes

- Time-series: `(event_timestamp DESC)`
- Track lookup: `(track_id, event_timestamp DESC)`
- Domain filter: `(domain, event_timestamp DESC)`
- Activity type: `(activity_type, event_timestamp DESC)`
- Identifiers: `(mode_s)`, `(mmsi)`
- Properties: GIN index on `properties` JSONB

## Setup Instructions

### 1. Start Infrastructure

```bash
# From project root
cd infrastructure/docker
docker-compose up -d kafka zookeeper postgres
```

### 2. Create Kafka Topics

```bash
cd infrastructure/kafka
chmod +x create-topics.sh
./create-topics.sh
```

### 3. Initialize Database Schema

```bash
# Apply PostgreSQL schema
psql -h localhost -U shark -d sharkdb -f schema/postgresql/001_create_tables.sql
```

### 4. Start Activity Consumer

```bash
cd data/activity
pip install -r requirements.txt
python consumer.py
```

### 5. Verify Setup

```bash
# Check Kafka topics
docker exec shark-kafka kafka-topics --list --bootstrap-server localhost:9092

# Check consumer group
docker exec shark-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group activity-consumer-group

# Check PostgreSQL table
psql -h localhost -U shark -d sharkdb -c "SELECT COUNT(*) FROM track_activity_log;"
```

## Testing

### Send Test Event (Python)

```bash
cd data/activity
python producer.py
```

### Send Test Event (curl)

```bash
curl -X POST http://localhost:8080/api/activity/log \
  -H "Content-Type: application/json" \
  -d '{
    "track_id": "TEST-001",
    "event_type": "activity_detected",
    "domain": "AIR",
    "mode_s": "A12345",
    "activity_type": "test",
    "latitude": 35.5,
    "longitude": -118.5,
    "properties": {"test": true}
  }'
```

### Verify Event Written

```bash
# Check Kafka
docker exec shark-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic activity-events \
  --from-beginning \
  --max-messages 1

# Check PostgreSQL
psql -h localhost -U shark -d sharkdb -c \
  "SELECT * FROM track_activity_log ORDER BY id DESC LIMIT 1;"
```

## Performance Characteristics

### Consumer

- **Batch size**: 100 messages
- **Batch timeout**: 5 seconds
- **Throughput**: ~10,000 events/sec (single consumer)
- **Latency**: 0-5 seconds (depends on batch)

### Kafka

- **Partitions**: 3 (supports 3 parallel consumers)
- **Compression**: Snappy (~60% reduction)
- **Max throughput**: ~50,000 events/sec

### PostgreSQL

- **Bulk insert**: ~20,000 rows/sec
- **Index overhead**: ~30% write penalty
- **JSONB performance**: Excellent for flexible properties

## Monitoring

### Kafka Metrics

```bash
# Consumer lag
docker exec shark-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group activity-consumer-group

# Topic status
docker exec shark-kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe --topic activity-events
```

### Consumer Logs

Consumer outputs structured logs:
```
2025-01-06 14:30:15 - INFO - Activity consumer initialized successfully
2025-01-06 14:30:20 - INFO - ✓ Wrote batch of 100 events to PostgreSQL
```

### PostgreSQL Monitoring

```sql
-- Event counts by domain
SELECT domain, COUNT(*)
FROM track_activity_log
GROUP BY domain;

-- Events per minute (last hour)
SELECT
    date_trunc('minute', event_timestamp) AS minute,
    COUNT(*) AS events
FROM track_activity_log
WHERE event_timestamp > NOW() - INTERVAL '1 hour'
GROUP BY minute
ORDER BY minute DESC;

-- Top activity types
SELECT activity_type, COUNT(*)
FROM track_activity_log
WHERE activity_type IS NOT NULL
GROUP BY activity_type
ORDER BY COUNT(*) DESC
LIMIT 10;
```

## Troubleshooting

### Consumer Not Processing Messages

1. **Check Kafka connectivity**:
   ```bash
   docker logs shark-kafka
   ```

2. **Check consumer group**:
   ```bash
   docker exec shark-kafka kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --describe --group activity-consumer-group
   ```

3. **Check PostgreSQL connectivity**:
   ```bash
   psql -h localhost -U shark -d sharkdb -c "SELECT 1;"
   ```

### High Consumer Lag

- Increase number of consumer instances (up to 3 for 3 partitions)
- Increase batch size
- Check PostgreSQL write performance
- Verify network latency

### Failed Writes

- Check consumer logs for errors
- Verify table schema matches event structure
- Check PostgreSQL disk space
- Verify JSONB fields are valid JSON

## Production Considerations

### Scaling

- **Horizontal**: Add consumers (max = partition count)
- **Vertical**: Increase batch size for higher throughput
- **Partitioning**: Use time-based partitioning on PostgreSQL table

### Reliability

- **Kafka**: Increase replication factor to 3
- **Consumer**: Run multiple instances for high availability
- **PostgreSQL**: Use connection pooling, read replicas

### Data Retention

```sql
-- Delete old activity logs (>90 days)
DELETE FROM track_activity_log
WHERE event_timestamp < NOW() - INTERVAL '90 days';

-- Or use partitioning and DROP old partitions
```

## API Endpoints

### Log Activity (POST)

```
POST /api/activity/log
Content-Type: application/json

{
  "track_id": "string",
  "event_type": "string",
  "domain": "AIR|MARITIME",
  "mode_s": "string?",
  "mmsi": "string?",
  "activity_type": "string?",
  "kb_object_id": "integer?",
  "latitude": "float?",
  "longitude": "float?",
  "properties": {}
}

Response: 202 Accepted
{
  "status": "queued"
}
```

### Get Activity History (GET)

```
GET /api/activity/mmsi/{mmsi}

Response: 200 OK
[
  {
    "timestamp": "2025-01-06T14:30:00Z",
    "location_name": "Port of Los Angeles",
    "duration_hours": 24.5,
    "purpose": "refueling"
  }
]
```

## References

- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [kafka-python Library](https://kafka-python.readthedocs.io/)
- [PostgreSQL JSONB](https://www.postgresql.org/docs/current/datatype-json.html)
- [Shark Bake-Off Plan](../../SHARK-BAKEOFF-PLAN.md)
