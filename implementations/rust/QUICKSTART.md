# Quick Start Guide - Rust Implementation

## 1. Install Rust (if not already installed)

```bash
./install_rust.sh
source $HOME/.cargo/env
```

## 2. Setup Environment

```bash
cp .env.example .env
# Edit .env to configure your database connection
```

## 3. Build

```bash
# Development build
cargo build

# Or optimized release build (recommended for benchmarking)
cargo build --release
```

## 4. Run

```bash
# With PostgreSQL backend
DATABASE_TYPE=postgres cargo run --release

# With Neo4j backend
DATABASE_TYPE=neo4j cargo run --release

# With Memgraph backend
DATABASE_TYPE=memgraph cargo run --release
```

## 5. Test

```bash
# Health check
curl http://localhost:8080/health

# Lookup aircraft by Mode-S
curl http://localhost:8080/api/aircraft/mode_s/A12345

# Lookup ship by MMSI
curl http://localhost:8080/api/ship/mmsi/366123456

# Two-hop query
curl http://localhost:8080/api/aircraft/country/USA

# Three-hop cross-domain query
curl http://localhost:8080/api/cross-domain/country/USA

# Activity history
curl http://localhost:8080/api/activity/mmsi/366123456
```

## Performance Testing

### Using wrk (install with: apt-get install wrk or brew install wrk)

```bash
# Single endpoint load test
wrk -t4 -c100 -d30s http://localhost:8080/api/aircraft/mode_s/A12345

# Higher concurrency
wrk -t8 -c500 -d60s http://localhost:8080/api/aircraft/mode_s/A12345
```

### Metrics

The server logs request latency and throughput. Watch the console output for:
- Request count
- Response times
- Error rates

## Troubleshooting

**Compilation errors about OpenSSL:**
```bash
# Ubuntu/Debian
sudo apt-get install libssl-dev pkg-config

# macOS
brew install openssl
```

**Can't connect to database:**
- Verify the database is running
- Check `.env` configuration
- Test connection manually (psql, cypher-shell, etc.)

**Performance not meeting expectations:**
- Make sure you're using `--release` build
- Verify database indexes are created
- Check connection pool size (default: 16)
- Monitor database CPU/memory usage
