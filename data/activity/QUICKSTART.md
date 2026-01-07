# Activity Storage Quick Start

Get the activity logging system up and running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ (for consumer)
- PostgreSQL client (psql)

## Step 1: Start Infrastructure (2 min)

```bash
cd infrastructure/docker
docker-compose up -d
```

This starts:
- Kafka + Zookeeper
- PostgreSQL
- Neo4j
- Memgraph
- Redis
- Prometheus + Grafana

## Step 2: Create Kafka Topics (30 sec)

```bash
cd ../../infrastructure/kafka
./create-topics.sh
```

Expected output:
```
Creating Kafka topics on localhost:9092...
Kafka is ready!
Creating topic: activity-events
✓ Kafka topics ready for activity logging
```

## Step 3: Initialize Database (30 sec)

```bash
cd ../../schema/postgresql
psql -h localhost -U shark -d sharkdb -f 001_create_tables.sql
# Password: sharkbakeoff
```

## Step 4: Start Activity Consumer (1 min)

```bash
cd ../../data/activity

# Install dependencies
pip install -r requirements.txt

# Start consumer
python consumer.py
```

Expected output:
```
============================================================
Shark Bake-Off: Activity Event Consumer
============================================================
Kafka: localhost:9092
Topic: activity-events
PostgreSQL: localhost:5432/sharkdb
Batch size: 100
============================================================
2025-01-06 14:30:15 - INFO - Activity consumer initialized successfully
2025-01-06 14:30:15 - INFO - Starting activity consumer...
```

## Step 5: Test the System (1 min)

### Terminal 1: Keep consumer running

### Terminal 2: Send a test event

```bash
cd data/activity
python producer.py
```

Output:
```
Test event sent successfully
```

### Terminal 3: Verify the event was written

```bash
psql -h localhost -U shark -d sharkdb -c \
  "SELECT track_id, event_type, domain, event_timestamp FROM track_activity_log ORDER BY id DESC LIMIT 1;"
```

Expected result:
```
 track_id  |  event_type  | domain |      event_timestamp
-----------+--------------+--------+---------------------------
 TEST-001  | test_event   | AIR    | 2025-01-06 14:30:20.123456
```

## Step 6: Test via API (if running Rust implementation)

### Start Rust API

```bash
cd implementations/rust
cargo run --release
```

### Send activity via API

```bash
curl -X POST http://localhost:8080/api/activity/log \
  -H "Content-Type: application/json" \
  -d '{
    "track_id": "API-TEST-001",
    "event_type": "activity_detected",
    "domain": "AIR",
    "mode_s": "A12345",
    "activity_type": "air_refueling",
    "latitude": 35.5,
    "longitude": -118.5,
    "properties": {"altitude_ft": 25000}
  }'
```

Expected response:
```json
{"status":"queued"}
```

### Verify in database

```bash
psql -h localhost -U shark -d sharkdb -c \
  "SELECT * FROM track_activity_log WHERE track_id='API-TEST-001';"
```

## Monitoring

### Watch consumer logs

Consumer logs will show batch writes:
```
2025-01-06 14:32:15 - INFO - ✓ Wrote batch of 100 events to PostgreSQL
```

### Check Kafka consumer lag

```bash
docker exec shark-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group activity-consumer-group
```

### Query activity stats

```bash
psql -h localhost -U shark -d sharkdb
```

```sql
-- Total events
SELECT COUNT(*) FROM track_activity_log;

-- Events by domain
SELECT domain, COUNT(*) FROM track_activity_log GROUP BY domain;

-- Recent events
SELECT track_id, event_type, event_timestamp
FROM track_activity_log
ORDER BY event_timestamp DESC
LIMIT 10;
```

## Stopping the System

```bash
# Stop consumer (Ctrl+C in terminal)

# Stop infrastructure
cd infrastructure/docker
docker-compose down

# Or keep data volumes:
docker-compose down --volumes  # WARNING: Deletes all data!
```

## Troubleshooting

### "Can't connect to Kafka"

```bash
# Check Kafka is running
docker ps | grep kafka

# Check Kafka logs
docker logs shark-kafka
```

### "Can't connect to PostgreSQL"

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -U shark -d sharkdb -c "SELECT 1;"
```

### Consumer not processing events

1. Check consumer logs for errors
2. Verify Kafka topic exists:
   ```bash
   docker exec shark-kafka kafka-topics --list --bootstrap-server localhost:9092
   ```
3. Check consumer group status:
   ```bash
   docker exec shark-kafka kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --describe --group activity-consumer-group
   ```

## Next Steps

- [Full Documentation](README.md)
- [Shark Bake-Off Plan](../../SHARK-BAKEOFF-PLAN.md)
- [API Implementations](../../implementations/)
- [Benchmark Queries](../../benchmark/queries/)
