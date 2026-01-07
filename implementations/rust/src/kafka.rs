use rdkafka::config::ClientConfig;
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::util::Timeout;
use serde::{Deserialize, Serialize};
use std::time::Duration;
use chrono::Utc;
use crate::error::{AppError, Result};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActivityEvent {
    pub track_id: String,
    pub domain: String,
    pub event_type: String,
    pub activity_type: Option<String>,
    pub kb_object_id: Option<i64>,
    pub mode_s: Option<String>,
    pub mmsi: Option<String>,
    pub event_timestamp: String,
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub properties: serde_json::Value,
    pub associated_track_ids: Vec<String>,
    pub associated_kb_ids: Vec<i64>,
}

pub struct ActivityProducer {
    producer: FutureProducer,
    topic: String,
}

impl ActivityProducer {
    pub fn new(brokers: &str, topic: &str) -> Result<Self> {
        let producer: FutureProducer = ClientConfig::new()
            .set("bootstrap.servers", brokers)
            .set("message.timeout.ms", "5000")
            .set("compression.type", "snappy")
            .set("acks", "all")
            .set("retries", "3")
            .create()
            .map_err(|e| AppError::Internal(format!("Failed to create Kafka producer: {}", e)))?;

        Ok(Self {
            producer,
            topic: topic.to_string(),
        })
    }

    pub async fn send_event(&self, event: ActivityEvent) -> Result<()> {
        let payload = serde_json::to_string(&event)
            .map_err(|e| AppError::Internal(format!("Failed to serialize event: {}", e)))?;

        let record = FutureRecord::to(&self.topic)
            .key(&event.track_id)
            .payload(&payload);

        self.producer
            .send(record, Timeout::After(Duration::from_secs(5)))
            .await
            .map_err(|(err, _)| AppError::Internal(format!("Failed to send Kafka message: {}", err)))?;

        Ok(())
    }

    pub async fn send_activity(
        &self,
        track_id: String,
        event_type: String,
        domain: String,
        mode_s: Option<String>,
        mmsi: Option<String>,
        activity_type: Option<String>,
        kb_object_id: Option<i64>,
        latitude: Option<f64>,
        longitude: Option<f64>,
        properties: Option<serde_json::Value>,
    ) -> Result<()> {
        let event = ActivityEvent {
            track_id,
            domain,
            event_type,
            activity_type,
            kb_object_id,
            mode_s,
            mmsi,
            event_timestamp: Utc::now().to_rfc3339(),
            latitude,
            longitude,
            properties: properties.unwrap_or(serde_json::json!({})),
            associated_track_ids: vec![],
            associated_kb_ids: vec![],
        };

        self.send_event(event).await
    }
}

impl Drop for ActivityProducer {
    fn drop(&mut self) {
        // Flush any remaining messages
        self.producer.flush(Timeout::After(Duration::from_secs(5)));
    }
}
