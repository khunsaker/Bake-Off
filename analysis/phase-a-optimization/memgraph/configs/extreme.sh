#!/bin/bash
# Memgraph Extreme Configuration
# Shark Bake-Off: Extreme Optimization Variant (Benchmark-Specific)
# Target: 16GB RAM, 8-core CPU, maximum performance

cat <<'EOF'
# Add to docker-compose.yml under memgraph service:
#
# services:
#   memgraph:
#     image: memgraph/memgraph-platform:latest
#     command:

# ============================================================================
# MEMORY SETTINGS (87.5% of 16GB RAM - aggressive)
# ============================================================================
--memory-limit=14GB
--memory-warning-threshold=12GB

# ============================================================================
# QUERY OPTIMIZATION (MAXIMUM CACHING)
# ============================================================================
--query-execution-timeout-sec=300
--query-plan-cache-size=10000
--query-max-plans=1000

# ============================================================================
# CONCURRENCY (MAXIMUM PARALLELISM)
# ============================================================================
--bolt-num-workers=20
--bolt-session-inactivity-timeout=7200

# ============================================================================
# STORAGE CONFIGURATION (MINIMIZE I/O)
# ============================================================================
--storage-wal-enabled=true
--storage-snapshot-interval-sec=3600
--storage-snapshot-on-exit=true
--storage-recover-on-startup=true
--storage-properties-on-edges=true

# ============================================================================
# ISOLATION LEVEL
# ============================================================================
--isolation-level=SNAPSHOT_ISOLATION

# ============================================================================
# LOGGING (MINIMAL FOR PERFORMANCE)
# ============================================================================
--log-level=ERROR
--log-file=/var/log/memgraph/memgraph.log

# ============================================================================
# BOLT CONNECTOR
# ============================================================================
--bolt-port=7687
--bolt-address=0.0.0.0

# ============================================================================
# PERFORMANCE (AGGRESSIVE)
# ============================================================================
--cartesian-product-enabled=false

EOF
