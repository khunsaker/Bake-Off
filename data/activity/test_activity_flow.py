#!/usr/bin/env python3
"""
End-to-end test for Activity Storage system
Tests: Producer -> Kafka -> Consumer -> PostgreSQL
"""

import json
import time
import sys
import psycopg2
from datetime import datetime, timedelta
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient
from kafka.errors import KafkaError

# Test configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_TOPIC = 'activity-events'
POSTGRES_DSN = 'postgresql://shark:sharkbakeoff@localhost:5432/sharkdb'
TEST_TRACK_ID_PREFIX = f'TEST-{int(time.time())}'

def log_test(message, status='INFO'):
    """Log test message"""
    symbols = {'INFO': 'ℹ', 'PASS': '✓', 'FAIL': '✗', 'WARN': '⚠'}
    print(f"{symbols.get(status, 'ℹ')} [{status}] {message}")

def test_kafka_connection():
    """Test 1: Verify Kafka is accessible"""
    log_test("Testing Kafka connection...", "INFO")
    try:
        admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        topics = admin.list_topics()

        if KAFKA_TOPIC in topics:
            log_test(f"Kafka topic '{KAFKA_TOPIC}' exists", "PASS")
        else:
            log_test(f"Kafka topic '{KAFKA_TOPIC}' not found", "FAIL")
            return False

        admin.close()
        log_test("Kafka connection successful", "PASS")
        return True
    except Exception as e:
        log_test(f"Kafka connection failed: {e}", "FAIL")
        return False

def test_postgres_connection():
    """Test 2: Verify PostgreSQL is accessible"""
    log_test("Testing PostgreSQL connection...", "INFO")
    try:
        conn = psycopg2.connect(POSTGRES_DSN)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'track_activity_log'
            );
        """)
        table_exists = cursor.fetchone()[0]

        if table_exists:
            log_test("Table 'track_activity_log' exists", "PASS")
        else:
            log_test("Table 'track_activity_log' not found", "FAIL")
            conn.close()
            return False

        conn.close()
        log_test("PostgreSQL connection successful", "PASS")
        return True
    except Exception as e:
        log_test(f"PostgreSQL connection failed: {e}", "FAIL")
        return False

def test_produce_events(num_events=10):
    """Test 3: Produce test events to Kafka"""
    log_test(f"Producing {num_events} test events to Kafka...", "INFO")

    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        )

        test_ids = []
        for i in range(num_events):
            track_id = f"{TEST_TRACK_ID_PREFIX}-{i:03d}"
            test_ids.append(track_id)

            event = {
                'track_id': track_id,
                'domain': 'AIR' if i % 2 == 0 else 'MARITIME',
                'event_type': 'test_event',
                'activity_type': 'e2e_test',
                'mode_s': f'T{i:05d}' if i % 2 == 0 else None,
                'mmsi': f'99{i:07d}' if i % 2 == 1 else None,
                'event_timestamp': datetime.utcnow().isoformat() + 'Z',
                'latitude': 35.0 + (i * 0.1),
                'longitude': -118.0 + (i * 0.1),
                'properties': {'test': True, 'sequence': i},
                'associated_track_ids': [],
                'associated_kb_ids': [],
            }

            future = producer.send(KAFKA_TOPIC, value=event)
            future.get(timeout=10)  # Wait for confirmation

        producer.flush()
        producer.close()

        log_test(f"Successfully produced {num_events} events", "PASS")
        return test_ids

    except Exception as e:
        log_test(f"Failed to produce events: {e}", "FAIL")
        return None

def test_consume_and_verify(test_ids, timeout_seconds=30):
    """Test 4: Wait for events to be consumed and written to PostgreSQL"""
    log_test(f"Waiting for events to be written to PostgreSQL (timeout: {timeout_seconds}s)...", "INFO")

    if not test_ids:
        log_test("No test IDs to verify", "FAIL")
        return False

    start_time = time.time()
    found_count = 0

    try:
        conn = psycopg2.connect(POSTGRES_DSN)
        cursor = conn.cursor()

        while time.time() - start_time < timeout_seconds:
            # Check how many test events have been written
            cursor.execute("""
                SELECT COUNT(*)
                FROM track_activity_log
                WHERE track_id LIKE %s
            """, (f"{TEST_TRACK_ID_PREFIX}%",))

            found_count = cursor.fetchone()[0]

            if found_count >= len(test_ids):
                log_test(f"All {len(test_ids)} events written to PostgreSQL", "PASS")

                # Verify event details
                cursor.execute("""
                    SELECT track_id, domain, event_type, activity_type
                    FROM track_activity_log
                    WHERE track_id LIKE %s
                    ORDER BY track_id
                """, (f"{TEST_TRACK_ID_PREFIX}%",))

                results = cursor.fetchall()
                log_test(f"Sample events:", "INFO")
                for row in results[:3]:
                    log_test(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]}", "INFO")

                conn.close()
                return True

            time.sleep(1)

        log_test(f"Timeout: Only {found_count}/{len(test_ids)} events found after {timeout_seconds}s", "FAIL")
        log_test("Consumer may not be running or is experiencing delays", "WARN")
        conn.close()
        return False

    except Exception as e:
        log_test(f"Failed to verify events in PostgreSQL: {e}", "FAIL")
        return False

def cleanup_test_data():
    """Clean up test data from PostgreSQL"""
    log_test("Cleaning up test data...", "INFO")
    try:
        conn = psycopg2.connect(POSTGRES_DSN)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM track_activity_log
            WHERE track_id LIKE %s
        """, (f"{TEST_TRACK_ID_PREFIX}%",))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        log_test(f"Deleted {deleted_count} test records", "PASS")
        return True
    except Exception as e:
        log_test(f"Failed to clean up test data: {e}", "WARN")
        return False

def main():
    """Run end-to-end test"""
    print("="*60)
    print("Activity Storage End-to-End Test")
    print("="*60)
    print()

    # Test 1: Kafka connection
    if not test_kafka_connection():
        log_test("Kafka is not accessible. Please start Kafka and create topics.", "FAIL")
        sys.exit(1)
    print()

    # Test 2: PostgreSQL connection
    if not test_postgres_connection():
        log_test("PostgreSQL is not accessible or schema not initialized.", "FAIL")
        sys.exit(1)
    print()

    # Test 3: Produce events
    test_ids = test_produce_events(num_events=10)
    if not test_ids:
        log_test("Failed to produce test events", "FAIL")
        sys.exit(1)
    print()

    # Test 4: Wait for consumption
    log_test("Waiting for consumer to process events...", "INFO")
    log_test("(Make sure consumer.py is running!)", "WARN")
    print()

    if not test_consume_and_verify(test_ids, timeout_seconds=30):
        log_test("End-to-end test FAILED", "FAIL")
        log_test("", "INFO")
        log_test("Troubleshooting:", "INFO")
        log_test("1. Is the consumer running? (python consumer.py)", "INFO")
        log_test("2. Check consumer logs for errors", "INFO")
        log_test("3. Verify Kafka consumer group status", "INFO")
        cleanup_test_data()
        sys.exit(1)
    print()

    # Cleanup
    cleanup_test_data()
    print()

    print("="*60)
    log_test("End-to-end test PASSED", "PASS")
    print("="*60)
    print()
    log_test("Activity Storage system is working correctly!", "PASS")
    log_test("Producer -> Kafka -> Consumer -> PostgreSQL flow verified", "INFO")

if __name__ == '__main__':
    main()
