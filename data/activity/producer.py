#!/usr/bin/env python3
"""
Activity Event Producer for Shark Bake-Off
Simple Kafka producer for publishing activity events
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class ActivityProducer:
    """Kafka producer for activity events"""

    def __init__(self, bootstrap_servers: str, topic: str = 'activity-events'):
        """
        Initialize Kafka producer

        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Kafka topic name
        """
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',  # Wait for all replicas
            retries=3,
            compression_type='snappy',
        )
        logger.info(f"Activity producer initialized for topic: {topic}")

    def send_event(
        self,
        track_id: str,
        event_type: str,
        domain: str = 'AIR',
        activity_type: Optional[str] = None,
        kb_object_id: Optional[int] = None,
        mode_s: Optional[str] = None,
        mmsi: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        properties: Optional[Dict[str, Any]] = None,
        associated_track_ids: Optional[List[str]] = None,
        associated_kb_ids: Optional[List[int]] = None,
    ) -> bool:
        """
        Send an activity event to Kafka

        Args:
            track_id: External track identifier
            event_type: Type of event (e.g., 'identified', 'updated', 'activity_detected')
            domain: Domain ('AIR' or 'MARITIME')
            activity_type: Specific activity type (e.g., 'air_refueling', 'port_call')
            kb_object_id: Associated KB object ID
            mode_s: Aircraft Mode-S identifier
            mmsi: Ship MMSI identifier
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            properties: Additional event properties
            associated_track_ids: Related track IDs
            associated_kb_ids: Related KB object IDs

        Returns:
            True if event sent successfully
        """
        event = {
            'track_id': track_id,
            'domain': domain,
            'event_type': event_type,
            'activity_type': activity_type,
            'kb_object_id': kb_object_id,
            'mode_s': mode_s,
            'mmsi': mmsi,
            'event_timestamp': datetime.utcnow().isoformat() + 'Z',
            'latitude': latitude,
            'longitude': longitude,
            'properties': properties or {},
            'associated_track_ids': associated_track_ids or [],
            'associated_kb_ids': associated_kb_ids or [],
        }

        try:
            # Send asynchronously
            future = self.producer.send(self.topic, value=event)

            # Can optionally wait for confirmation
            # future.get(timeout=10)

            logger.debug(f"Sent event: {event_type} for track {track_id}")
            return True

        except KafkaError as e:
            logger.error(f"Error sending event to Kafka: {e}")
            return False

    def flush(self):
        """Flush pending messages"""
        self.producer.flush()

    def close(self):
        """Close the producer"""
        self.producer.close()
        logger.info("Activity producer closed")


# Singleton instance for easy import
_producer_instance: Optional[ActivityProducer] = None


def get_producer(bootstrap_servers: Optional[str] = None) -> ActivityProducer:
    """
    Get or create singleton producer instance

    Args:
        bootstrap_servers: Kafka bootstrap servers (uses env var if not provided)

    Returns:
        ActivityProducer instance
    """
    global _producer_instance

    if _producer_instance is None:
        if bootstrap_servers is None:
            bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

        _producer_instance = ActivityProducer(bootstrap_servers)

    return _producer_instance


# Example usage
if __name__ == '__main__':
    import sys

    logging.basicConfig(level=logging.INFO)

    # Example: Send a test event
    producer = get_producer()

    producer.send_event(
        track_id='TEST-001',
        event_type='test_event',
        domain='AIR',
        mode_s='A12345',
        activity_type='test',
        properties={'test': True, 'message': 'Test event from producer'},
    )

    producer.flush()
    print("Test event sent successfully")
    producer.close()
