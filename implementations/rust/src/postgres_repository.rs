use async_trait::async_trait;
use deadpool_postgres::{Client, Pool};
use crate::error::{AppError, Result};
use crate::models::{AircraftLookup, ShipLookup, TwoHopResult, ThreeHopResult, ActivityHistory};
use crate::repository::Repository;

pub struct PostgresRepository {
    pool: Pool,
}

impl PostgresRepository {
    pub fn new(pool: Pool) -> Self {
        Self { pool }
    }

    async fn get_client(&self) -> Result<Client> {
        self.pool
            .get()
            .await
            .map_err(|e| AppError::Database(e.to_string()))
    }
}

#[async_trait]
impl Repository for PostgresRepository {
    async fn lookup_aircraft_by_mode_s(&self, mode_s: &str) -> Result<Option<AircraftLookup>> {
        let client = self.get_client().await?;

        let query = r#"
            SELECT
                shark_name,
                platform,
                affiliation,
                nationality,
                operator,
                air_type,
                air_model
            FROM air_instance_lookup
            WHERE mode_s = $1
        "#;

        let row = client.query_opt(query, &[&mode_s]).await?;

        match row {
            Some(row) => Ok(Some(AircraftLookup {
                shark_name: row.get("shark_name"),
                platform: row.get("platform"),
                affiliation: row.get("affiliation"),
                nationality: row.get("nationality"),
                operator: row.get("operator"),
                air_type: row.get("air_type"),
                air_model: row.get("air_model"),
            })),
            None => Ok(None),
        }
    }

    async fn lookup_ship_by_mmsi(&self, mmsi: &str) -> Result<Option<ShipLookup>> {
        let client = self.get_client().await?;

        let query = r#"
            SELECT
                shark_name,
                platform,
                affiliation,
                nationality,
                operator,
                ship_type,
                ship_class
            FROM ship_instance_lookup
            WHERE mmsi = $1
        "#;

        let row = client.query_opt(query, &[&mmsi]).await?;

        match row {
            Some(row) => Ok(Some(ShipLookup {
                shark_name: row.get("shark_name"),
                platform: row.get("platform"),
                affiliation: row.get("affiliation"),
                nationality: row.get("nationality"),
                operator: row.get("operator"),
                ship_type: row.get("ship_type"),
                ship_class: row.get("ship_class"),
            })),
            None => Ok(None),
        }
    }

    async fn two_hop_aircraft_by_country(&self, country: &str) -> Result<Vec<TwoHopResult>> {
        let client = self.get_client().await?;

        // Using the kb_relationships approach for proper graph traversal
        let query = r#"
            SELECT
                a.shark_name AS aircraft_name,
                a.platform AS aircraft_platform,
                o.name AS operator_name,
                l.name AS headquarters_location,
                l.country
            FROM air_instance_lookup a
            INNER JOIN kb_relationships r1 ON r1.source_domain = 'AIR' AND r1.source_id = a.id
            INNER JOIN organizations o ON r1.target_domain = 'ORGANIZATION' AND r1.target_id = o.id
            INNER JOIN kb_relationships r2 ON r2.source_domain = 'ORGANIZATION' AND r2.source_id = o.id
            INNER JOIN locations l ON r2.target_domain = 'LOCATION' AND r2.target_id = l.id
            WHERE r1.relationship_type = 'OPERATED_BY'
              AND r2.relationship_type = 'HEADQUARTERED_AT'
              AND l.country = $1
            LIMIT 100
        "#;

        let rows = client.query(query, &[&country]).await?;

        Ok(rows
            .iter()
            .map(|row| TwoHopResult {
                aircraft_name: row.get("aircraft_name"),
                aircraft_platform: row.get("aircraft_platform"),
                operator_name: row.get("operator_name"),
                headquarters_location: row.get("headquarters_location"),
                country: row.get("country"),
            })
            .collect())
    }

    async fn three_hop_cross_domain(&self, country: &str) -> Result<Vec<ThreeHopResult>> {
        let client = self.get_client().await?;

        // Complex query joining air and maritime domains through organizations
        let query = r#"
            WITH entities AS (
                SELECT
                    a.shark_name AS entity_name,
                    'Aircraft' AS entity_type,
                    a.operator,
                    a.id
                FROM air_instance_lookup a
                UNION ALL
                SELECT
                    s.shark_name AS entity_name,
                    'Ship' AS entity_type,
                    s.operator,
                    s.id
                FROM ship_instance_lookup s
            )
            SELECT
                e.entity_name,
                e.entity_type,
                o.name AS operator_name,
                po.name AS parent_org,
                l.country
            FROM entities e
            INNER JOIN organizations o ON e.operator = o.name
            LEFT JOIN organizations po ON o.parent_org_id = po.id
            INNER JOIN locations l ON o.country = l.country
            WHERE l.country = $1
            LIMIT 100
        "#;

        let rows = client.query(query, &[&country]).await?;

        Ok(rows
            .iter()
            .map(|row| ThreeHopResult {
                entity_name: row.get("entity_name"),
                entity_type: row.get("entity_type"),
                operator_name: row.get("operator_name"),
                parent_org: row.get("parent_org"),
                country: row.get("country"),
            })
            .collect())
    }

    async fn activity_history(&self, mmsi: &str) -> Result<Vec<ActivityHistory>> {
        let client = self.get_client().await?;

        let query = r#"
            SELECT
                timestamp,
                location_name,
                duration_hours,
                purpose
            FROM track_activity_log
            WHERE mmsi = $1
            ORDER BY timestamp DESC
            LIMIT 100
        "#;

        let rows = client.query(query, &[&mmsi]).await?;

        Ok(rows
            .iter()
            .map(|row| ActivityHistory {
                timestamp: row.get("timestamp"),
                location_name: row.get("location_name"),
                duration_hours: row.get("duration_hours"),
                purpose: row.get("purpose"),
            })
            .collect())
    }

    async fn health_check(&self) -> Result<bool> {
        let client = self.get_client().await?;
        client.query_one("SELECT 1", &[]).await?;
        Ok(true)
    }
}
