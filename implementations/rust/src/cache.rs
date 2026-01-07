use async_trait::async_trait;
use redis::AsyncCommands;
use deadpool_redis::{Pool, Connection};
use serde::{Serialize, de::DeserializeOwned};
use crate::error::{AppError, Result};
use crate::models::{AircraftLookup, ShipLookup, TwoHopResult, ThreeHopResult, ActivityHistory};
use crate::repository::Repository;
use std::sync::Arc;

const DEFAULT_TTL: usize = 300; // 5 minutes

pub struct CachedRepository {
    repo: Arc<dyn Repository>,
    cache_pool: Pool,
    enabled: bool,
}

impl CachedRepository {
    pub fn new(repo: Arc<dyn Repository>, cache_pool: Pool, enabled: bool) -> Self {
        Self {
            repo,
            cache_pool,
            enabled,
        }
    }

    async fn get_connection(&self) -> Result<Connection> {
        self.cache_pool
            .get()
            .await
            .map_err(|e| AppError::Cache(e.to_string()))
    }

    async fn get_cached<T>(&self, key: &str) -> Result<Option<T>>
    where
        T: DeserializeOwned,
    {
        if !self.enabled {
            return Ok(None);
        }

        let mut conn = self.get_connection().await?;
        let value: Option<String> = conn.get(key).await?;

        match value {
            Some(json_str) => {
                let deserialized: T = serde_json::from_str(&json_str)
                    .map_err(|e| AppError::Cache(format!("Deserialization error: {}", e)))?;
                Ok(Some(deserialized))
            }
            None => Ok(None),
        }
    }

    async fn set_cached<T>(&self, key: &str, value: &T, ttl: usize) -> Result<()>
    where
        T: Serialize,
    {
        if !self.enabled {
            return Ok(());
        }

        let mut conn = self.get_connection().await?;
        let json_str = serde_json::to_string(value)
            .map_err(|e| AppError::Cache(format!("Serialization error: {}", e)))?;

        conn.set_ex(key, json_str, ttl).await?;
        Ok(())
    }
}

#[async_trait]
impl Repository for CachedRepository {
    async fn lookup_aircraft_by_mode_s(&self, mode_s: &str) -> Result<Option<AircraftLookup>> {
        let cache_key = format!("aircraft:mode_s:{}", mode_s);

        // Try cache first
        if let Some(cached) = self.get_cached::<AircraftLookup>(&cache_key).await? {
            return Ok(Some(cached));
        }

        // Cache miss - query database
        let result = self.repo.lookup_aircraft_by_mode_s(mode_s).await?;

        // Store in cache if found
        if let Some(ref aircraft) = result {
            self.set_cached(&cache_key, aircraft, DEFAULT_TTL).await?;
        }

        Ok(result)
    }

    async fn lookup_ship_by_mmsi(&self, mmsi: &str) -> Result<Option<ShipLookup>> {
        let cache_key = format!("ship:mmsi:{}", mmsi);

        // Try cache first
        if let Some(cached) = self.get_cached::<ShipLookup>(&cache_key).await? {
            return Ok(Some(cached));
        }

        // Cache miss - query database
        let result = self.repo.lookup_ship_by_mmsi(mmsi).await?;

        // Store in cache if found
        if let Some(ref ship) = result {
            self.set_cached(&cache_key, ship, DEFAULT_TTL).await?;
        }

        Ok(result)
    }

    async fn two_hop_aircraft_by_country(&self, country: &str) -> Result<Vec<TwoHopResult>> {
        let cache_key = format!("two_hop:country:{}", country);

        // Try cache first
        if let Some(cached) = self.get_cached::<Vec<TwoHopResult>>(&cache_key).await? {
            return Ok(cached);
        }

        // Cache miss - query database
        let result = self.repo.two_hop_aircraft_by_country(country).await?;

        // Store in cache
        self.set_cached(&cache_key, &result, DEFAULT_TTL).await?;

        Ok(result)
    }

    async fn three_hop_cross_domain(&self, country: &str) -> Result<Vec<ThreeHopResult>> {
        let cache_key = format!("three_hop:country:{}", country);

        // Try cache first
        if let Some(cached) = self.get_cached::<Vec<ThreeHopResult>>(&cache_key).await? {
            return Ok(cached);
        }

        // Cache miss - query database
        let result = self.repo.three_hop_cross_domain(country).await?;

        // Store in cache
        self.set_cached(&cache_key, &result, DEFAULT_TTL).await?;

        Ok(result)
    }

    async fn activity_history(&self, mmsi: &str) -> Result<Vec<ActivityHistory>> {
        let cache_key = format!("activity:mmsi:{}", mmsi);

        // Try cache first
        if let Some(cached) = self.get_cached::<Vec<ActivityHistory>>(&cache_key).await? {
            return Ok(cached);
        }

        // Cache miss - query database
        let result = self.repo.activity_history(mmsi).await?;

        // Store in cache
        self.set_cached(&cache_key, &result, DEFAULT_TTL).await?;

        Ok(result)
    }

    async fn health_check(&self) -> Result<bool> {
        // Health check shouldn't be cached
        self.repo.health_check().await
    }
}
