// Memgraph uses the same Bolt protocol and Cypher syntax as Neo4j
// This is essentially a type alias to Neo4jRepository for clarity

use async_trait::async_trait;
use neo4rs::Graph;
use crate::error::Result;
use crate::models::{AircraftLookup, ShipLookup, TwoHopResult, ThreeHopResult, ActivityHistory};
use crate::repository::Repository;
use crate::neo4j_repository::Neo4jRepository;

pub struct MemgraphRepository {
    inner: Neo4jRepository,
}

impl MemgraphRepository {
    pub fn new(graph: Graph) -> Self {
        Self {
            inner: Neo4jRepository::new(graph),
        }
    }
}

#[async_trait]
impl Repository for MemgraphRepository {
    async fn lookup_aircraft_by_mode_s(&self, mode_s: &str) -> Result<Option<AircraftLookup>> {
        self.inner.lookup_aircraft_by_mode_s(mode_s).await
    }

    async fn lookup_ship_by_mmsi(&self, mmsi: &str) -> Result<Option<ShipLookup>> {
        self.inner.lookup_ship_by_mmsi(mmsi).await
    }

    async fn two_hop_aircraft_by_country(&self, country: &str) -> Result<Vec<TwoHopResult>> {
        self.inner.two_hop_aircraft_by_country(country).await
    }

    async fn three_hop_cross_domain(&self, country: &str) -> Result<Vec<ThreeHopResult>> {
        self.inner.three_hop_cross_domain(country).await
    }

    async fn activity_history(&self, mmsi: &str) -> Result<Vec<ActivityHistory>> {
        self.inner.activity_history(mmsi).await
    }

    async fn health_check(&self) -> Result<bool> {
        self.inner.health_check().await
    }
}
