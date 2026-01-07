use std::env;

#[derive(Debug, Clone)]
pub struct Config {
    pub server_host: String,
    pub server_port: u16,
    pub database_type: DatabaseType,
    pub postgres_url: String,
    pub neo4j_url: String,
    pub neo4j_user: String,
    pub neo4j_password: String,
    pub memgraph_url: String,
    pub redis_url: String,
    pub cache_enabled: bool,
    pub kafka_brokers: String,
    pub kafka_topic: String,
    pub kafka_enabled: bool,
}

#[derive(Debug, Clone, PartialEq)]
pub enum DatabaseType {
    PostgreSQL,
    Neo4j,
    Memgraph,
}

impl Config {
    pub fn from_env() -> Result<Self, Box<dyn std::error::Error>> {
        dotenv::dotenv().ok();

        let database_type = match env::var("DATABASE_TYPE")
            .unwrap_or_else(|_| "postgres".to_string())
            .to_lowercase()
            .as_str()
        {
            "neo4j" => DatabaseType::Neo4j,
            "memgraph" => DatabaseType::Memgraph,
            _ => DatabaseType::PostgreSQL,
        };

        Ok(Config {
            server_host: env::var("SERVER_HOST").unwrap_or_else(|_| "0.0.0.0".to_string()),
            server_port: env::var("SERVER_PORT")
                .unwrap_or_else(|_| "8080".to_string())
                .parse()?,
            database_type,
            postgres_url: env::var("POSTGRES_URL")
                .unwrap_or_else(|_| "postgresql://postgres:postgres@localhost:5432/shark_bakeoff".to_string()),
            neo4j_url: env::var("NEO4J_URL")
                .unwrap_or_else(|_| "bolt://localhost:7687".to_string()),
            neo4j_user: env::var("NEO4J_USER")
                .unwrap_or_else(|_| "neo4j".to_string()),
            neo4j_password: env::var("NEO4J_PASSWORD")
                .unwrap_or_else(|_| "password".to_string()),
            memgraph_url: env::var("MEMGRAPH_URL")
                .unwrap_or_else(|_| "bolt://localhost:7689".to_string()),
            redis_url: env::var("REDIS_URL")
                .unwrap_or_else(|_| "redis://localhost:6379".to_string()),
            cache_enabled: env::var("CACHE_ENABLED")
                .unwrap_or_else(|_| "true".to_string())
                .parse()
                .unwrap_or(true),
            kafka_brokers: env::var("KAFKA_BROKERS")
                .unwrap_or_else(|_| "localhost:9092".to_string()),
            kafka_topic: env::var("KAFKA_TOPIC")
                .unwrap_or_else(|_| "activity-events".to_string()),
            kafka_enabled: env::var("KAFKA_ENABLED")
                .unwrap_or_else(|_| "true".to_string())
                .parse()
                .unwrap_or(true),
        })
    }
}
