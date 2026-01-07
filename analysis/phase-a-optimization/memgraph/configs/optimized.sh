#!/bin/bash
# Memgraph Optimized Configuration
# Shark Bake-Off: Aggressive Optimization Variant
# Target: 16GB RAM, 8-core CPU, in-memory optimized

# Usage:
# Update docker-compose.yml memgraph service with these command flags

cat <<'EOF'
# Add to docker-compose.yml under memgraph service:
#
# services:
#   memgraph:
#     image: memgraph/memgraph-platform:latest
#     command:

# ============================================================================
# MEMORY SETTINGS (75% of 16GB RAM)
# ============================================================================
--memory-limit=12GB
--memory-warning-threshold=10GB

# ============================================================================
# QUERY OPTIMIZATION
# ============================================================================
--query-execution-timeout-sec=120
--query-plan-cache-size=10000
--query-max-plans=1000

# ============================================================================
# CONCURRENCY (8-CORE SYSTEM)
# ============================================================================
--bolt-num-workers=16
--bolt-session-inactivity-timeout=3600

# ============================================================================
# STORAGE CONFIGURATION
# ============================================================================
--storage-wal-enabled=true
--storage-snapshot-interval-sec=600
--storage-snapshot-on-exit=true
--storage-recover-on-startup=true
--storage-properties-on-edges=true

# ============================================================================
# ISOLATION LEVEL
# ============================================================================
--isolation-level=SNAPSHOT_ISOLATION

# ============================================================================
# LOGGING (REDUCED FOR BENCHMARK)
# ============================================================================
--log-level=WARNING
--log-file=/var/log/memgraph/memgraph.log

# ============================================================================
# BOLT CONNECTOR
# ============================================================================
--bolt-port=7687
--bolt-address=0.0.0.0

# ============================================================================
# PERFORMANCE
# ============================================================================
--cartesian-product-enabled=false

EOF
