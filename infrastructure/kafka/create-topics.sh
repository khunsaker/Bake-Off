#!/bin/bash
# Create Kafka topics for Shark Bake-Off activity logging

set -e

KAFKA_HOST="${KAFKA_HOST:-localhost:9092}"

echo "Creating Kafka topics on $KAFKA_HOST..."

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
timeout=60
elapsed=0
while ! docker exec shark-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 >/dev/null 2>&1; do
    sleep 2
    elapsed=$((elapsed + 2))
    if [ $elapsed -ge $timeout ]; then
        echo "ERROR: Kafka failed to start within ${timeout} seconds"
        exit 1
    fi
    echo "  Still waiting... (${elapsed}s)"
done

echo "Kafka is ready!"

# Create activity events topic
echo "Creating topic: activity-events"
docker exec shark-kafka kafka-topics \
    --create \
    --if-not-exists \
    --bootstrap-server localhost:9092 \
    --topic activity-events \
    --partitions 3 \
    --replication-factor 1 \
    --config retention.ms=604800000 \
    --config compression.type=snappy

# Create activity events DLQ (Dead Letter Queue)
echo "Creating topic: activity-events-dlq"
docker exec shark-kafka kafka-topics \
    --create \
    --if-not-exists \
    --bootstrap-server localhost:9092 \
    --topic activity-events-dlq \
    --partitions 1 \
    --replication-factor 1 \
    --config retention.ms=2592000000

# List topics
echo ""
echo "Topics created successfully:"
docker exec shark-kafka kafka-topics \
    --list \
    --bootstrap-server localhost:9092

echo ""
echo "Topic details:"
docker exec shark-kafka kafka-topics \
    --describe \
    --bootstrap-server localhost:9092 \
    --topic activity-events

echo ""
echo "✓ Kafka topics ready for activity logging"
