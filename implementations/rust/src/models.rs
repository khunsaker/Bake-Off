use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AircraftLookup {
    pub shark_name: String,
    pub platform: Option<String>,
    pub affiliation: Option<String>,
    pub nationality: Option<String>,
    pub operator: Option<String>,
    pub air_type: Option<String>,
    pub air_model: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShipLookup {
    pub shark_name: String,
    pub platform: Option<String>,
    pub affiliation: Option<String>,
    pub nationality: Option<String>,
    pub operator: Option<String>,
    pub ship_type: Option<String>,
    pub ship_class: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TwoHopResult {
    pub aircraft_name: String,
    pub aircraft_platform: Option<String>,
    pub operator_name: String,
    pub headquarters_location: String,
    pub country: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThreeHopResult {
    pub entity_name: String,
    pub entity_type: String,
    pub operator_name: String,
    pub parent_org: Option<String>,
    pub country: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActivityHistory {
    pub timestamp: DateTime<Utc>,
    pub location_name: String,
    pub duration_hours: Option<f64>,
    pub purpose: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthCheck {
    pub status: String,
    pub database: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ErrorResponse {
    pub error: String,
}
