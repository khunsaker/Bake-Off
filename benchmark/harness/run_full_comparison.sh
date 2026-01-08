#!/bin/bash
#
# Full Database Comparison - Shark Bake-Off
# Runs benchmarks across PostgreSQL, Neo4j, and Memgraph
#

set -e

echo "================================================================================"
echo "SHARK BAKE-OFF: FULL DATABASE COMPARISON"
echo "================================================================================"
echo ""

# Configuration
API_URL="http://localhost:8080"
REQUESTS=2000
CONCURRENCY=20
OUTPUT_DIR="/tmp/shark-bakeoff-results"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Patterns to test (subset for quick comparison)
PATTERNS=(
    "lookup-95"     # 95% identifier lookups
    "balanced-50"   # 50% lookups, 40% 2-hop, 10% 3-hop
    "analytics-20"  # 20% lookups, 64% 2-hop, 16% 3-hop
)

# Test PostgreSQL
echo "================================================================================"
echo "TESTING POSTGRESQL"
echo "================================================================================"
echo ""

for pattern in "${PATTERNS[@]}"; do
    echo "→ Running pattern: $pattern (${REQUESTS} requests, ${CONCURRENCY} concurrent)"

    python3 runner.py "$API_URL" \
        --pattern "$pattern" \
        --requests "$REQUESTS" \
        --concurrency "$CONCURRENCY" \
        --output "$OUTPUT_DIR/postgresql_${pattern}" \
        2>&1 | grep -E "(p50:|p95:|p99:|Result:|OVERALL)" || true

    echo ""
done

echo "✓ PostgreSQL testing complete"
echo ""

# Test Neo4j
echo "================================================================================"
echo "TESTING NEO4J"
echo "================================================================================"
echo ""

for pattern in "${PATTERNS[@]}"; do
    echo "→ Running pattern: $pattern (${REQUESTS} requests, ${CONCURRENCY} concurrent)"

    # Use Neo4j-specific endpoints
    python3 runner.py "${API_URL}/neo4j" \
        --pattern "$pattern" \
        --requests "$REQUESTS" \
        --concurrency "$CONCURRENCY" \
        --output "$OUTPUT_DIR/neo4j_${pattern}" \
        2>&1 | grep -E "(p50:|p95:|p99:|Result:|OVERALL)" || true

    echo ""
done

echo "✓ Neo4j testing complete"
echo ""

# Test Memgraph
echo "================================================================================"
echo "TESTING MEMGRAPH"
echo "================================================================================"
echo ""

for pattern in "${PATTERNS[@]}"; do
    echo "→ Running pattern: $pattern (${REQUESTS} requests, ${CONCURRENCY} concurrent)"

    # Use Memgraph-specific endpoints
    python3 runner.py "${API_URL}/memgraph" \
        --pattern "$pattern" \
        --requests "$REQUESTS" \
        --concurrency "$CONCURRENCY" \
        --output "$OUTPUT_DIR/memgraph_${pattern}" \
        2>&1 | grep -E "(p50:|p95:|p99:|Result:|OVERALL)" || true

    echo ""
done

echo "✓ Memgraph testing complete"
echo ""

# Summary
echo "================================================================================"
echo "BENCHMARKING COMPLETE"
echo "================================================================================"
echo ""
echo "Results saved to: $OUTPUT_DIR"
echo ""
echo "Files generated:"
ls -lh "$OUTPUT_DIR"/*.json 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "Next steps:"
echo "  1. Review results: cat $OUTPUT_DIR/postgresql_lookup-95-evaluation.json"
echo "  2. Compare databases: python3 ../../analysis/phase-b-comparison/analyze_crossover.py"
echo "  3. Generate decision: python3 ../../analysis/phase-c-decision/calculate_scores.py"
echo ""
