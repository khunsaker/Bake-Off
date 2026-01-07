#!/bin/bash
# Memgraph Conservative Configuration
# Shark Bake-Off: Conservative Optimization Variant
# Target: 16GB RAM, 8-core CPU, production-safe settings

cat <<'EOF'
# Add to docker-compose.yml under memgraph service:
#
# services:
#   memgraph:
#     image: memgraph/memgraph-platform:latest
#     command:

# ============================================================================
# MEMORY SETTINGS (62.5% of 16GB RAM - conservative)
# ============================================================================
--memory-limit=10GB
--memory-warning-threshold=8GB

# ============================================================================
# QUERY OPTIMIZATION
# ============================================================================
--query-execution-timeout-sec=120
--query-plan-cache-size=5000

# ============================================================================
# CONCURRENCY
# ============================================================================
--bolt-num-workers=8
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
# LOGGING
# ============================================================================
--log-level=INFO
--log-file=/var/log/memgraph/memgraph.log

# ============================================================================
# BOLT CONNECTOR
# ============================================================================
--bolt-port=7687
--bolt-address=0.0.0.0

EOF
