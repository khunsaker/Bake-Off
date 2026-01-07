use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use std::sync::Arc;
use crate::error::Result;
use crate::models::{HealthCheck, ErrorResponse};
use crate::repository::Repository;
use crate::kafka::ActivityProducer;

pub struct AppState {
    pub repo: Arc<dyn Repository>,
    pub database_type: String,
    pub kafka_producer: Option<Arc<ActivityProducer>>,
}

// Health check endpoint
pub async fn health(State(state): State<Arc<AppState>>) -> Result<impl IntoResponse> {
    state.repo.health_check().await?;

    Ok(Json(HealthCheck {
        status: "healthy".to_string(),
        database: state.database_type.clone(),
    }))
}

// S1: Aircraft lookup by Mode-S
pub async fn get_aircraft_by_mode_s(
    State(state): State<Arc<AppState>>,
    Path(mode_s): Path<String>,
) -> Result<impl IntoResponse> {
    match state.repo.lookup_aircraft_by_mode_s(&mode_s).await? {
        Some(aircraft) => Ok((StatusCode::OK, Json(aircraft))),
        None => Ok((
            StatusCode::NOT_FOUND,
            Json(crate::models::AircraftLookup {
                shark_name: String::new(),
                platform: None,
                affiliation: None,
                nationality: None,
                operator: None,
                air_type: None,
                air_model: None,
            }),
        )),
    }
}

// S1: Ship lookup by MMSI
pub async fn get_ship_by_mmsi(
    State(state): State<Arc<AppState>>,
    Path(mmsi): Path<String>,
) -> Result<impl IntoResponse> {
    match state.repo.lookup_ship_by_mmsi(&mmsi).await? {
        Some(ship) => Ok((StatusCode::OK, Json(ship))),
        None => Ok((
            StatusCode::NOT_FOUND,
            Json(crate::models::ShipLookup {
                shark_name: String::new(),
                platform: None,
                affiliation: None,
                nationality: None,
                operator: None,
                ship_type: None,
                ship_class: None,
            }),
        )),
    }
}

// S3: Two-hop traversal - Aircraft by operator HQ country
pub async fn get_aircraft_by_country(
    State(state): State<Arc<AppState>>,
    Path(country): Path<String>,
) -> Result<impl IntoResponse> {
    let results = state.repo.two_hop_aircraft_by_country(&country).await?;
    Ok(Json(results))
}

// S6: Three-hop cross-domain query
pub async fn get_cross_domain_by_country(
    State(state): State<Arc<AppState>>,
    Path(country): Path<String>,
) -> Result<impl IntoResponse> {
    let results = state.repo.three_hop_cross_domain(&country).await?;
    Ok(Json(results))
}

// S11: Activity history for a ship
pub async fn get_activity_history(
    State(state): State<Arc<AppState>>,
    Path(mmsi): Path<String>,
) -> Result<impl IntoResponse> {
    let results = state.repo.activity_history(&mmsi).await?;
    Ok(Json(results))
}

// Root endpoint
pub async fn root() -> &'static str {
    "Shark Bake-Off Rust API - Performance Testing"
}

// Activity logging endpoint
#[derive(serde::Deserialize)]
pub struct LogActivityRequest {
    pub track_id: String,
    pub event_type: String,
    pub domain: String,
    pub mode_s: Option<String>,
    pub mmsi: Option<String>,
    pub activity_type: Option<String>,
    pub kb_object_id: Option<i64>,
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub properties: Option<serde_json::Value>,
}

pub async fn log_activity(
    State(state): State<Arc<AppState>>,
    Json(req): Json<LogActivityRequest>,
) -> Result<impl IntoResponse> {
    if let Some(producer) = &state.kafka_producer {
        producer
            .send_activity(
                req.track_id,
                req.event_type,
                req.domain,
                req.mode_s,
                req.mmsi,
                req.activity_type,
                req.kb_object_id,
                req.latitude,
                req.longitude,
                req.properties,
            )
            .await?;

        Ok((StatusCode::ACCEPTED, Json(serde_json::json!({"status": "queued"}))))
    } else {
        Ok((
            StatusCode::SERVICE_UNAVAILABLE,
            Json(serde_json::json!({"status": "kafka_disabled"})),
        ))
    }
}
