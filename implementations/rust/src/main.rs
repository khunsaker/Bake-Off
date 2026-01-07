mod config;
mod error;
mod models;
mod repository;
mod postgres_repository;
mod neo4j_repository;
mod memgraph_repository;
mod cache;
mod handlers;
mod kafka;

use axum::{
    routing::{get, post},
    Router,
};
use std::sync::Arc;
use tower_http::trace::TraceLayer;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use crate::config::{Config, DatabaseType};
use crate::handlers::AppState;
use crate::repository::Repository;
use crate::postgres_repository::PostgresRepository;
use crate::neo4j_repository::Neo4jRepository;
use crate::memgraph_repository::MemgraphRepository;
use crate::cache::CachedRepository;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "shark_bakeoff_rust=info,tower_http=info".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    // Load configuration
    let config = Config::from_env()?;
    tracing::info!("Starting Shark Bake-Off Rust API");
    tracing::info!("Database type: {:?}", config.database_type);

    // Create repository based on database type
    let repo: Arc<dyn Repository> = match config.database_type {
        DatabaseType::PostgreSQL => {
            tracing::info!("Initializing PostgreSQL connection pool");
            let pg_config = config.postgres_url.parse::<tokio_postgres::Config>()?;
            let mgr = deadpool_postgres::Manager::new(pg_config, tokio_postgres::NoTls);
            let pool = deadpool_postgres::Pool::builder(mgr)
                .max_size(16)
                .build()?;

            // Test connection
            let client = pool.get().await?;
            client.query_one("SELECT 1", &[]).await?;
            tracing::info!("PostgreSQL connection successful");

            Arc::new(PostgresRepository::new(pool))
        }
        DatabaseType::Neo4j => {
            tracing::info!("Initializing Neo4j connection");
            let graph = neo4rs::Graph::new(
                &config.neo4j_url,
                &config.neo4j_user,
                &config.neo4j_password,
            )
            .await?;

            // Test connection
            let mut result = graph.execute(neo4rs::query("RETURN 1")).await?;
            result.next().await?;
            tracing::info!("Neo4j connection successful");

            Arc::new(Neo4jRepository::new(graph))
        }
        DatabaseType::Memgraph => {
            tracing::info!("Initializing Memgraph connection");
            // Memgraph typically doesn't require authentication by default
            let graph = neo4rs::Graph::new(
                &config.memgraph_url,
                "",
                "",
            )
            .await?;

            // Test connection
            let mut result = graph.execute(neo4rs::query("RETURN 1")).await?;
            result.next().await?;
            tracing::info!("Memgraph connection successful");

            Arc::new(MemgraphRepository::new(graph))
        }
    };

    // Wrap repository with cache if enabled
    let repo: Arc<dyn Repository> = if config.cache_enabled {
        tracing::info!("Initializing Redis cache");
        let redis_config = deadpool_redis::Config::from_url(&config.redis_url);
        let cache_pool = redis_config.create_pool(Some(deadpool_redis::Runtime::Tokio1))?;

        // Test Redis connection
        let mut conn = cache_pool.get().await?;
        redis::cmd("PING").query_async::<_, String>(&mut conn).await?;
        tracing::info!("Redis connection successful");

        Arc::new(CachedRepository::new(repo, cache_pool, true))
    } else {
        tracing::info!("Cache disabled");
        repo
    };

    // Initialize Kafka producer if enabled
    let kafka_producer = if config.kafka_enabled {
        tracing::info!("Initializing Kafka producer");
        match kafka::ActivityProducer::new(&config.kafka_brokers, &config.kafka_topic) {
            Ok(producer) => {
                tracing::info!("Kafka producer initialized successfully");
                Some(Arc::new(producer))
            }
            Err(e) => {
                tracing::warn!("Failed to initialize Kafka producer: {}. Activity logging disabled.", e);
                None
            }
        }
    } else {
        tracing::info!("Kafka disabled");
        None
    };

    // Create application state
    let state = Arc::new(AppState {
        repo,
        database_type: format!("{:?}", config.database_type),
        kafka_producer,
    });

    // Build router
    let app = Router::new()
        .route("/", get(handlers::root))
        .route("/health", get(handlers::health))
        .route("/api/aircraft/mode_s/:mode_s", get(handlers::get_aircraft_by_mode_s))
        .route("/api/ship/mmsi/:mmsi", get(handlers::get_ship_by_mmsi))
        .route("/api/aircraft/country/:country", get(handlers::get_aircraft_by_country))
        .route("/api/cross-domain/country/:country", get(handlers::get_cross_domain_by_country))
        .route("/api/activity/mmsi/:mmsi", get(handlers::get_activity_history))
        .route("/api/activity/log", post(handlers::log_activity))
        .with_state(state)
        .layer(TraceLayer::new_for_http());

    // Start server
    let addr = format!("{}:{}", config.server_host, config.server_port);
    tracing::info!("Server listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
