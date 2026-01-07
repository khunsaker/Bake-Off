#!/bin/bash
# Memgraph Default Configuration
# Shark Bake-Off: Baseline (No Custom Tuning)
# Use for baseline comparison

cat <<'EOF'
# Add to docker-compose.yml under memgraph service:
#
# services:
#   memgraph:
#     image: memgraph/memgraph-platform:latest
#     command:

# ============================================================================
# DEFAULT BEHAVIOR
# ============================================================================
#
# This file documents the default Memgraph configuration from docker-compose.yml
# Image: memgraph/memgraph-platform:latest
#
# Default settings:
#
# Memory:
#   - Memory limit: Auto-detected (typically 90% of available RAM)
#   - Warning threshold: 80% of limit
#
# Concurrency:
#   - Bolt workers: Auto (based on CPU cores, typically 8)
#
# Query:
#   - Query timeout: 600 seconds
#   - Query cache: 1000 plans
#
# Storage:
#   - WAL enabled: true
#   - Snapshot interval: 300 seconds (5 minutes)
#
# Logging:
#   - Log level: INFO

# ============================================================================
# MINIMAL CONFIGURATION FOR DOCKER
# ============================================================================

# Only these settings are required for docker-compose:

# Memory (conservative for baseline)
--memory-limit=8GB

# Bolt workers (default for 8-core)
--bolt-num-workers=8

# Storage
--storage-wal-enabled=true
--storage-properties-on-edges=true

# Logging
--log-level=INFO

# ============================================================================
# USAGE
# ============================================================================
#
# To test with default configuration:
# 1. Use minimal flags in docker-compose.yml
# 2. Let Memgraph use its built-in defaults for most settings
# 3. Run benchmark for baseline measurement
#
# Command:
#   docker-compose restart memgraph
#   cd benchmark/harness
#   python runner.py http://localhost:8080 \
#     --pattern balanced-50 \
#     --requests 50000 \
#     --concurrency 20 \
#     --output ../analysis/phase-a-optimization/memgraph/results/default

EOF
