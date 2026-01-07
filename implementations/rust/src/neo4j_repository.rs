use async_trait::async_trait;
use neo4rs::{Graph, query};
use crate::error::{AppError, Result};
use crate::models::{AircraftLookup, ShipLookup, TwoHopResult, ThreeHopResult, ActivityHistory};
use crate::repository::Repository;
use chrono::{DateTime, Utc};

pub struct Neo4jRepository {
    graph: Graph,
}

impl Neo4jRepository {
    pub fn new(graph: Graph) -> Self {
        Self { graph }
    }
}

#[async_trait]
impl Repository for Neo4jRepository {
    async fn lookup_aircraft_by_mode_s(&self, mode_s: &str) -> Result<Option<AircraftLookup>> {
        let cypher = r#"
            MATCH (a:Aircraft {mode_s: $mode_s})
            RETURN a.shark_name AS shark_name,
                   a.platform AS platform,
                   a.affiliation AS affiliation,
                   a.nationality AS nationality,
                   a.operator AS operator,
                   a.air_type AS air_type,
                   a.air_model AS air_model
        "#;

        let mut result = self.graph.execute(query(cypher).param("mode_s", mode_s)).await?;

        if let Some(row) = result.next().await? {
            Ok(Some(AircraftLookup {
                shark_name: row.get::<String>("shark_name").unwrap_or_default(),
                platform: row.get::<Option<String>>("platform").ok().flatten(),
                affiliation: row.get::<Option<String>>("affiliation").ok().flatten(),
                nationality: row.get::<Option<String>>("nationality").ok().flatten(),
                operator: row.get::<Option<String>>("operator").ok().flatten(),
                air_type: row.get::<Option<String>>("air_type").ok().flatten(),
                air_model: row.get::<Option<String>>("air_model").ok().flatten(),
            }))
        } else {
            Ok(None)
        }
    }

    async fn lookup_ship_by_mmsi(&self, mmsi: &str) -> Result<Option<ShipLookup>> {
        let cypher = r#"
            MATCH (s:Ship {mmsi: $mmsi})
            RETURN s.shark_name AS shark_name,
                   s.platform AS platform,
                   s.affiliation AS affiliation,
                   s.nationality AS nationality,
                   s.operator AS operator,
                   s.ship_type AS ship_type,
                   s.ship_class AS ship_class
        "#;

        let mut result = self.graph.execute(query(cypher).param("mmsi", mmsi)).await?;

        if let Some(row) = result.next().await? {
            Ok(Some(ShipLookup {
                shark_name: row.get::<String>("shark_name").unwrap_or_default(),
                platform: row.get::<Option<String>>("platform").ok().flatten(),
                affiliation: row.get::<Option<String>>("affiliation").ok().flatten(),
                nationality: row.get::<Option<String>>("nationality").ok().flatten(),
                operator: row.get::<Option<String>>("operator").ok().flatten(),
                ship_type: row.get::<Option<String>>("ship_type").ok().flatten(),
                ship_class: row.get::<Option<String>>("ship_class").ok().flatten(),
            }))
        } else {
            Ok(None)
        }
    }

    async fn two_hop_aircraft_by_country(&self, country: &str) -> Result<Vec<TwoHopResult>> {
        let cypher = r#"
            MATCH (a:Aircraft)-[:OPERATED_BY]->(o:Organization)-[:HEADQUARTERED_AT]->(l:Location)
            WHERE l.country = $country
            RETURN a.shark_name AS aircraft_name,
                   a.platform AS aircraft_platform,
                   o.name AS operator_name,
                   l.name AS headquarters_location,
                   l.country AS country
            LIMIT 100
        "#;

        let mut result = self.graph.execute(query(cypher).param("country", country)).await?;
        let mut results = Vec::new();

        while let Some(row) = result.next().await? {
            results.push(TwoHopResult {
                aircraft_name: row.get::<String>("aircraft_name").unwrap_or_default(),
                aircraft_platform: row.get::<Option<String>>("aircraft_platform").ok().flatten(),
                operator_name: row.get::<String>("operator_name").unwrap_or_default(),
                headquarters_location: row.get::<String>("headquarters_location").unwrap_or_default(),
                country: row.get::<String>("country").unwrap_or_default(),
            });
        }

        Ok(results)
    }

    async fn three_hop_cross_domain(&self, country: &str) -> Result<Vec<ThreeHopResult>> {
        let cypher = r#"
            MATCH (entity)-[:OPERATED_BY]->(o:Organization)-[:PART_OF*0..1]->(parent:Organization)
            WHERE o.country = $country OR parent.country = $country
            RETURN
                entity.shark_name AS entity_name,
                labels(entity)[0] AS entity_type,
                o.name AS operator_name,
                parent.name AS parent_org,
                COALESCE(o.country, parent.country) AS country
            LIMIT 100
        "#;

        let mut result = self.graph.execute(query(cypher).param("country", country)).await?;
        let mut results = Vec::new();

        while let Some(row) = result.next().await? {
            results.push(ThreeHopResult {
                entity_name: row.get::<String>("entity_name").unwrap_or_default(),
                entity_type: row.get::<String>("entity_type").unwrap_or_default(),
                operator_name: row.get::<String>("operator_name").unwrap_or_default(),
                parent_org: row.get::<Option<String>>("parent_org").ok().flatten(),
                country: row.get::<String>("country").unwrap_or_default(),
            });
        }

        Ok(results)
    }

    async fn activity_history(&self, mmsi: &str) -> Result<Vec<ActivityHistory>> {
        let cypher = r#"
            MATCH (s:Ship {mmsi: $mmsi})-[v:VISITED]->(l:Location)
            RETURN v.timestamp AS timestamp,
                   l.name AS location_name,
                   v.duration_hours AS duration_hours,
                   v.purpose AS purpose
            ORDER BY v.timestamp DESC
            LIMIT 100
        "#;

        let mut result = self.graph.execute(query(cypher).param("mmsi", mmsi)).await?;
        let mut results = Vec::new();

        while let Some(row) = result.next().await? {
            // Parse timestamp - Neo4j returns it as a string in ISO format
            let timestamp_str = row.get::<String>("timestamp").unwrap_or_default();
            let timestamp = timestamp_str.parse::<DateTime<Utc>>()
                .unwrap_or_else(|_| Utc::now());

            results.push(ActivityHistory {
                timestamp,
                location_name: row.get::<String>("location_name").unwrap_or_default(),
                duration_hours: row.get::<Option<f64>>("duration_hours").ok().flatten(),
                purpose: row.get::<Option<String>>("purpose").ok().flatten(),
            });
        }

        Ok(results)
    }

    async fn health_check(&self) -> Result<bool> {
        let mut result = self.graph.execute(query("RETURN 1")).await?;
        Ok(result.next().await?.is_some())
    }
}
