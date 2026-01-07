#!/usr/bin/env python3
"""
Activity Event Consumer for Shark Bake-Off
Consumes activity events from Kafka and batch writes to PostgreSQL
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any
import logging

from kafka import KafkaConsumer
from kafka.errors import KafkaError
import psycopg2
from psycopg2.extras import execute_batch
from psycopg2.pool import SimpleConnectionPool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ActivityConsumer:
    """Kafka consumer that batch writes activity events to PostgreSQL"""

    def __init__(
        self,
        kafka_bootstrap_servers: str,
        kafka_topic: str,
        kafka_group_id: str,
        postgres_dsn: str,
        batch_size: int = 100,
        batch_timeout_seconds: float = 5.0,
    ):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topic = kafka_topic
        self.kafka_group_id = kafka_group_id
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds

        # Initialize PostgreSQL connection pool
        logger.info(f"Initializing PostgreSQL connection pool")
        self.pg_pool = SimpleConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=postgres_dsn
        )

        # Initialize Kafka consumer
        logger.info(f"Initializing Kafka consumer for topic: {kafka_topic}")
        self.consumer = KafkaConsumer(
            kafka_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            group_id=kafka_group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            max_poll_records=batch_size,
        )

        self.batch: List[Dict[str, Any]] = []
        self.last_commit_time = time.time()

        logger.info("Activity consumer initialized successfully")

    def close(self):
        """Close connections"""
        logger.info("Closing consumer...")
        self.consumer.close()
        self.pg_pool.closeall()
        logger.info("Consumer closed")

    def process_batch(self):
        """Write batch of events to PostgreSQL"""
        if not self.batch:
            return

        conn = None
        try:
            conn = self.pg_pool.getconn()
            cursor = conn.cursor()

            # Prepare batch insert
            insert_query = """
                INSERT INTO track_activity_log (
                    track_id,
                    domain,
                    event_type,
                    activity_type,
                    kb_object_id,
                    mode_s,
                    mmsi,
                    event_timestamp,
                    latitude,
                    longitude,
                    properties,
                    associated_track_ids,
                    associated_kb_ids
                ) VALUES (
                    %(track_id)s,
                    %(domain)s,
                    %(event_type)s,
                    %(activity_type)s,
                    %(kb_object_id)s,
                    %(mode_s)s,
                    %(mmsi)s,
                    %(event_timestamp)s,
                    %(latitude)s,
                    %(longitude)s,
                    %(properties)s,
                    %(associated_track_ids)s,
                    %(associated_kb_ids)s
                )
            """

            # Prepare records for insertion
            records = []
            for event in self.batch:
                # Parse timestamp
                timestamp_str = event.get('event_timestamp')
                if timestamp_str:
                    try:
                        event_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        event_timestamp = datetime.utcnow()
                else:
                    event_timestamp = datetime.utcnow()

                record = {
                    'track_id': event.get('track_id'),
                    'domain': event.get('domain', 'AIR'),
                    'event_type': event.get('event_type', 'activity_detected'),
                    'activity_type': event.get('activity_type'),
                    'kb_object_id': event.get('kb_object_id'),
                    'mode_s': event.get('mode_s'),
                    'mmsi': event.get('mmsi'),
                    'event_timestamp': event_timestamp,
                    'latitude': event.get('latitude'),
                    'longitude': event.get('longitude'),
                    'properties': json.dumps(event.get('properties', {})),
                    'associated_track_ids': event.get('associated_track_ids', []),
                    'associated_kb_ids': event.get('associated_kb_ids', []),
                }
                records.append(record)

            # Batch insert
            execute_batch(cursor, insert_query, records, page_size=100)
            conn.commit()

            logger.info(f"✓ Wrote batch of {len(records)} events to PostgreSQL")

        except Exception as e:
            logger.error(f"✗ Error writing batch to PostgreSQL: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise

        finally:
            if conn:
                self.pg_pool.putconn(conn)
            self.batch.clear()
            self.last_commit_time = time.time()

    def commit_offsets(self):
        """Commit Kafka offsets"""
        try:
            self.consumer.commit()
            logger.debug("Kafka offsets committed")
        except KafkaError as e:
            logger.error(f"Error committing Kafka offsets: {e}")

    def should_flush_batch(self) -> bool:
        """Determine if batch should be flushed"""
        if len(self.batch) >= self.batch_size:
            return True

        time_since_last_commit = time.time() - self.last_commit_time
        if time_since_last_commit >= self.batch_timeout_seconds and self.batch:
            return True

        return False

    def run(self):
        """Main consumer loop"""
        logger.info("Starting activity consumer...")
        logger.info(f"Batch size: {self.batch_size}, Timeout: {self.batch_timeout_seconds}s")

        try:
            for message in self.consumer:
                try:
                    event = message.value
                    self.batch.append(event)

                    if self.should_flush_batch():
                        self.process_batch()
                        self.commit_offsets()

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Continue processing other messages

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            # Flush remaining batch
            if self.batch:
                logger.info(f"Flushing remaining {len(self.batch)} events...")
                self.process_batch()
                self.commit_offsets()
            self.close()


def main():
    """Main entry point"""
    # Configuration from environment
    kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    kafka_topic = os.getenv('KAFKA_TOPIC', 'activity-events')
    kafka_group_id = os.getenv('KAFKA_GROUP_ID', 'activity-consumer-group')

    postgres_dsn = os.getenv(
        'POSTGRES_DSN',
        'postgresql://shark:sharkbakeoff@localhost:5432/sharkdb'
    )

    batch_size = int(os.getenv('BATCH_SIZE', '100'))
    batch_timeout = float(os.getenv('BATCH_TIMEOUT', '5.0'))

    logger.info("="*60)
    logger.info("Shark Bake-Off: Activity Event Consumer")
    logger.info("="*60)
    logger.info(f"Kafka: {kafka_bootstrap_servers}")
    logger.info(f"Topic: {kafka_topic}")
    logger.info(f"Group: {kafka_group_id}")
    logger.info(f"PostgreSQL: {postgres_dsn.split('@')[1] if '@' in postgres_dsn else postgres_dsn}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Batch timeout: {batch_timeout}s")
    logger.info("="*60)

    consumer = ActivityConsumer(
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        kafka_topic=kafka_topic,
        kafka_group_id=kafka_group_id,
        postgres_dsn=postgres_dsn,
        batch_size=batch_size,
        batch_timeout_seconds=batch_timeout,
    )

    consumer.run()


if __name__ == '__main__':
    main()
