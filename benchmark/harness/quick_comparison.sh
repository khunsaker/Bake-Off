#!/bin/bash
#
# Quick 3-Database Comparison
# Runs a single pattern across all databases
#

API_URL="http://localhost:8080"
PATTERN="lookup-95"
REQUESTS=1000
CONCURRENCY=10

echo "============================================================"
echo "QUICK COMPARISON: ${PATTERN} pattern"
echo "Requests: ${REQUESTS}, Concurrency: ${CONCURRENCY}"
echo "============================================================"
echo ""

# Test PostgreSQL
echo "→ Testing PostgreSQL..."
python3 runner.py "$API_URL" \
    --pattern "$PATTERN" \
    --requests "$REQUESTS" \
    --concurrency "$CONCURRENCY" \
    --output /tmp/compare_postgresql 2>&1 | tail -15

echo ""
echo "→ Testing Neo4j..."
# For Neo4j, we need to use the neo4j-specific endpoints
# The runner will use /api/aircraft/neo4j/mode_s/ endpoints
python3 runner.py "$API_URL" \
    --pattern "$PATTERN" \
    --requests "$REQUESTS" \
    --concurrency "$CONCURRENCY" \
    --db-prefix "neo4j" \
    --output /tmp/compare_neo4j 2>&1 | tail -15

echo ""
echo "→ Testing Memgraph..."
python3 runner.py "$API_URL" \
    --pattern "$PATTERN" \
    --requests "$REQUESTS" \
    --concurrency "$CONCURRENCY" \
    --db-prefix "memgraph" \
    --output /tmp/compare_memgraph 2>&1 | tail -15

echo ""
echo "============================================================"
echo "COMPARISON COMPLETE"
echo "============================================================"
echo ""
echo "Results:"
echo "  PostgreSQL: /tmp/compare_postgresql-evaluation.json"
echo "  Neo4j: /tmp/compare_neo4j-evaluation.json"
echo "  Memgraph: /tmp/compare_memgraph-evaluation.json"
echo ""
