# Shark Bake-Off: Rust Implementation

High-performance Rust implementation of the Shark Bake-Off benchmark API. This implementation establishes the performance ceiling for the benchmark.

## Architecture

- **Web Framework**: Axum (built on tokio and hyper)
- **PostgreSQL**: tokio-postgres with deadpool connection pooling
- **Neo4j/Memgraph**: neo4rs (native Bolt protocol driver)
- **Cache**: Redis with deadpool-redis
- **Async Runtime**: Tokio
- **Logging**: tracing + tracing-subscriber

## Features

- ✅ High-performance async I/O with tokio
- ✅ Connection pooling for all databases
- ✅ Redis caching layer (optional)
- ✅ Structured logging with tracing
- ✅ Proper error handling with typed errors
- ✅ Zero-copy parsing where possible
- ✅ Support for PostgreSQL, Neo4j, and Memgraph

## Prerequisites

- Rust 1.70+ (2021 edition)
- PostgreSQL 14+ (if using PostgreSQL backend)
- Neo4j 5.x (if using Neo4j backend)
- Memgraph 2.x (if using Memgraph backend)
- Redis 6+ (if caching enabled)

## Installation

### 1. Install Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### 2. Clone and Setup

```bash
cd implementations/rust
cp .env.example .env
# Edit .env with your database configuration
```

### 3. Build

```bash
# Development build
cargo build

# Optimized release build (for benchmarking)
cargo build --release
```

## Configuration

All configuration is done via environment variables (`.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVER_HOST` | Server bind address | `0.0.0.0` |
| `SERVER_PORT` | Server port | `8080` |
| `DATABASE_TYPE` | Database to use (`postgres`, `neo4j`, `memgraph`) | `postgres` |
| `POSTGRES_URL` | PostgreSQL connection URL | `postgresql://postgres:postgres@localhost:5432/shark_bakeoff` |
| `NEO4J_URL` | Neo4j Bolt URL | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `password` |
| `MEMGRAPH_URL` | Memgraph Bolt URL | `bolt://localhost:7689` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `CACHE_ENABLED` | Enable Redis caching | `true` |
| `RUST_LOG` | Logging level | `shark_bakeoff_rust=info` |

## Running

### Development Mode

```bash
cargo run
```

### Production Mode (Optimized)

```bash
cargo run --release
```

The server will start on `http://localhost:8080`

## API Endpoints

### Health Check
```bash
GET /health
```

### S1: Simple Identifier Lookup

**Aircraft by Mode-S:**
```bash
GET /api/aircraft/mode_s/{mode_s}
```

**Ship by MMSI:**
```bash
GET /api/ship/mmsi/{mmsi}
```

### S3: Two-Hop Traversal

**Aircraft by operator HQ country:**
```bash
GET /api/aircraft/country/{country}
```

### S6: Three-Hop Cross-Domain

**All entities by country:**
```bash
GET /api/cross-domain/country/{country}
```

### S11: Activity History

**Ship port visit history:**
```bash
GET /api/activity/mmsi/{mmsi}
```

## Performance Optimization

This implementation includes several optimizations for maximum performance:

### Release Profile

The `Cargo.toml` includes aggressive optimization settings:
- `opt-level = 3`: Maximum optimization
- `lto = "fat"`: Link-time optimization
- `codegen-units = 1`: Better optimization at cost of compile time
- `strip = true`: Remove debug symbols

### Connection Pooling

- PostgreSQL: 16 connections (configurable)
- Neo4j/Memgraph: Connection pooling via neo4rs
- Redis: Connection pooling via deadpool-redis

### Async Architecture

- Fully async using Tokio runtime
- Non-blocking I/O for all operations
- Efficient task scheduling
- Zero-copy where possible

### Caching Strategy

- Redis cache with 5-minute TTL
- Serialization via serde_json
- Cache key namespacing by query type
- Optional disable via `CACHE_ENABLED=false`

## Testing

```bash
# Run unit tests
cargo test

# Run with logging
RUST_LOG=debug cargo test -- --nocapture
```

## Benchmarking

### Using cargo bench (micro-benchmarks)

```bash
cargo bench
```

### Load Testing with wrk

```bash
# Simple lookup test
wrk -t4 -c100 -d30s http://localhost:8080/api/aircraft/mode_s/A12345

# Mixed workload
wrk -t8 -c200 -d60s -s benchmark_script.lua http://localhost:8080
```

### Expected Performance

On modern hardware (e.g., AWS c5.2xlarge):

| Query Type | p50 | p95 | p99 | Throughput |
|------------|-----|-----|-----|------------|
| S1 (cached) | <1ms | 2ms | 5ms | 50k+ qps |
| S1 (uncached) | 2-5ms | 10ms | 20ms | 10k+ qps |
| S3 (two-hop) | 5-10ms | 30ms | 50ms | 5k+ qps |
| S6 (three-hop) | 10-20ms | 50ms | 100ms | 2k+ qps |

*These are target metrics - actual results depend on database configuration and hardware.*

## Troubleshooting

### Build Issues

**neo4rs compilation fails:**
```bash
# Ensure you have OpenSSL development headers
# Ubuntu/Debian:
sudo apt-get install libssl-dev pkg-config

# macOS:
brew install openssl
```

### Runtime Issues

**Connection refused:**
- Verify database is running
- Check connection URLs in `.env`
- Verify firewall rules

**Slow performance:**
- Ensure using `--release` build
- Check database indexes are created
- Verify connection pool sizes
- Monitor database performance

## Project Structure

```
src/
├── main.rs                    # Application entry point
├── config.rs                  # Configuration management
├── error.rs                   # Error types and handling
├── models.rs                  # Data models
├── repository.rs              # Repository trait
├── postgres_repository.rs     # PostgreSQL implementation
├── neo4j_repository.rs        # Neo4j implementation
├── memgraph_repository.rs     # Memgraph implementation
├── cache.rs                   # Redis caching layer
└── handlers.rs                # HTTP request handlers
```

## Development

### Code Formatting

```bash
cargo fmt
```

### Linting

```bash
cargo clippy
```

### Watch Mode (auto-rebuild on changes)

```bash
cargo install cargo-watch
cargo watch -x run
```

## Performance Notes

### Why Rust?

Rust was chosen to establish the performance ceiling for this benchmark:

1. **Zero-cost abstractions**: High-level code compiles to efficient machine code
2. **Memory safety**: No garbage collector pauses
3. **Async efficiency**: Tokio is one of the fastest async runtimes
4. **Native compilation**: Direct to machine code, no JVM/interpreter overhead

### Performance Comparison Context

Expected performance relative to other implementations:

- **Rust**: 100% (baseline - fastest)
- **Go**: 70-90% (excellent performance, easier development)
- **Java**: 60-80% (JVM warmup required, excellent steady-state)
- **Python**: 20-40% (interpreter overhead, async complexity)

*These are rough estimates - actual results may vary.*

## Contributing

When making changes:
1. Run `cargo fmt` and `cargo clippy`
2. Add tests for new functionality
3. Update documentation as needed
4. Test with all three database types

## License

See project root for license information.
