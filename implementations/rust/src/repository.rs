use async_trait::async_trait;
use crate::error::Result;
use crate::models::{AircraftLookup, ShipLookup, TwoHopResult, ThreeHopResult, ActivityHistory};

#[async_trait]
pub trait Repository: Send + Sync {
    /// S1: Simple identifier lookup - Aircraft by Mode-S
    async fn lookup_aircraft_by_mode_s(&self, mode_s: &str) -> Result<Option<AircraftLookup>>;

    /// S1: Simple identifier lookup - Ship by MMSI
    async fn lookup_ship_by_mmsi(&self, mmsi: &str) -> Result<Option<ShipLookup>>;

    /// S3: Two-hop traversal - Aircraft by operator HQ country
    async fn two_hop_aircraft_by_country(&self, country: &str) -> Result<Vec<TwoHopResult>>;

    /// S6: Three-hop traversal - Cross-domain organizational relationships
    async fn three_hop_cross_domain(&self, country: &str) -> Result<Vec<ThreeHopResult>>;

    /// S11: Activity history - Port visits for a ship
    async fn activity_history(&self, mmsi: &str) -> Result<Vec<ActivityHistory>>;

    /// Health check
    async fn health_check(&self) -> Result<bool>;
}
