# Database Loaders

This directory contains scripts to load generated test data into PostgreSQL, Neo4j, and Memgraph.

## Prerequisites

### 1. Generate Test Data

Run all data generators first:

```bash
cd ../generators
python3 generate_organizations.py
python3 generate_locations.py
python3 generate_aircraft_instances.py
python3 generate_ship_instances.py
python3 generate_activity_log.py
python3 generate_relationships.py
```

This creates ~28 MB of JSON data in `../sample/`.

### 2. Start Databases

Start all databases using Docker Compose:

```bash
cd ../../infrastructure/docker
docker-compose up -d
```

Wait for databases to be ready:
```bash
# Check PostgreSQL
docker exec shark-postgres pg_isready

# Check Neo4j
curl http://localhost:7474

# Check Memgraph
curl http://localhost:3000
```

### 3. Install Python Dependencies

```bash
pip install psycopg2-binary neo4j
```

## Loading Data

### PostgreSQL

Load data into PostgreSQL:

```bash
python3 load_postgresql.py
```

**Expected Output**:
```
PostgreSQL Data Loader
============================================================

Connecting to PostgreSQL...
  Host: localhost:5432
  Database: sharkdb
  ✓ Connected

Loading organizations...
  Loaded 147 organizations

Loading locations...
  Loaded 77 locations

Loading aircraft instances...
  Loaded 5,560 aircraft

Loading ship instances...
  Loaded 492 ships

Loading activity log...
  Loaded 18,083 activities

Loading relationships...
  Loaded 25,811 relationships

============================================================
LOAD COMPLETE
============================================================

Database: sharkdb
  Organizations: 147
  Locations: 77
  Aircraft: 5,560
  Ships: 492
  Activities: 18,083
  Relationships: 25,811
  TOTAL RECORDS: 50,170
```

**Load Time**: ~30-60 seconds

**Verify**:
```bash
docker exec -it shark-postgres psql -U shark -d sharkdb -c "
SELECT 'Organizations' as table, COUNT(*) FROM organizations
UNION ALL SELECT 'Locations', COUNT(*) FROM locations
UNION ALL SELECT 'Aircraft', COUNT(*) FROM air_instance_lookup
UNION ALL SELECT 'Ships', COUNT(*) FROM ship_instance_lookup
UNION ALL SELECT 'Activities', COUNT(*) FROM track_activity_log
UNION ALL SELECT 'Relationships', COUNT(*) FROM kb_relationships;
"
```

### Neo4j

Load data into Neo4j:

```bash
python3 load_neo4j.py
```

**Optional**: Clear existing data first:
```bash
python3 load_neo4j.py --clear
```

**Expected Output**:
```
Neo4j Data Loader
============================================================

Connecting to Neo4j...
  URI: bolt://localhost:7687
  ✓ Connected

Creating constraints and indexes...
  ✓ Constraints and indexes created

Loading organizations...
  Loaded 147 organizations

Loading locations...
  Loaded 77 locations

Loading aircraft instances...
    Loaded 5,000 aircraft...
  Loaded 5,560 aircraft

Loading ship instances...
  Loaded 492 ships

Creating OPERATED_BY relationships...
  Created 6,052 OPERATED_BY relationships

Creating location relationships...
  Created 6,052 location relationships

Creating activity-based relationships...
    Created 1,819 SEEN_WITH relationships
    Created 2,538 VISITED relationships
    Created 9,350 REFUELED_BY relationships

============================================================
LOAD COMPLETE
============================================================

Nodes:
  Aircraft: 5,560
  Organization: 147
  Location: 77
  Ship: 492

Relationships:
  REFUELED_BY: 9,350
  OPERATED_BY: 6,052
  BASED_AT: 5,560
  VISITED: 2,538
  SEEN_WITH: 1,819
  HOME_PORT: 492

TOTAL: 6,276 nodes, 25,811 relationships
```

**Load Time**: ~2-5 minutes

**Verify** (Neo4j Browser at http://localhost:7474):
```cypher
// Count nodes by label
MATCH (n) RETURN labels(n)[0] AS label, COUNT(n) AS count ORDER BY count DESC

// Count relationships by type
MATCH ()-[r]->() RETURN type(r) AS type, COUNT(r) AS count ORDER BY count DESC

// Sample query: Find aircraft with their operators
MATCH (a:Aircraft)-[:OPERATED_BY]->(o:Organization)
RETURN a.mode_s, a.shark_name, o.name
LIMIT 10
```

### Memgraph

Load data into Memgraph:

```bash
python3 load_memgraph.py
```

**Optional**: Clear existing data first:
```bash
python3 load_memgraph.py --clear
```

**Expected Output**: (Same format as Neo4j)

**Load Time**: ~1-3 minutes (faster than Neo4j due to in-memory storage)

**Verify** (Memgraph Lab at http://localhost:3000):
```cypher
// Count nodes by label
MATCH (n) RETURN labels(n)[0] AS label, COUNT(n) AS count ORDER BY count DESC

// Count relationships by type
MATCH ()-[r]->() RETURN type(r) AS type, COUNT(r) AS count ORDER BY count DESC
```

## Data Loaded

### Entities

| Database | Organizations | Locations | Aircraft | Ships | **Total** |
|----------|--------------|-----------|----------|-------|-----------|
| **PostgreSQL** | 147 | 77 | 5,560 | 492 | **6,276** |
| **Neo4j** | 147 | 77 | 5,560 | 492 | **6,276** |
| **Memgraph** | 147 | 77 | 5,560 | 492 | **6,276** |

### Activities (PostgreSQL only)

- **18,083 activity records** in `track_activity_log`

### Relationships

| Database | Count | Notes |
|----------|-------|-------|
| **PostgreSQL** | 25,811 | In `kb_relationships` table |
| **Neo4j** | 25,811 | As graph edges |
| **Memgraph** | 25,811 | As graph edges |

**Breakdown**:
- REFUELED_BY: 9,350
- OPERATED_BY: 6,052
- BASED_AT: 5,560
- VISITED: 2,538
- SEEN_WITH: 1,819
- HOME_PORT: 492

## Troubleshooting

### PostgreSQL Connection Error

```
✗ Database error: could not connect to server
```

**Solution**: Ensure PostgreSQL is running and accessible:
```bash
docker ps | grep shark-postgres
docker logs shark-postgres
```

### Neo4j/Memgraph Authentication Error

```
✗ Error: Failed to establish connection
```

**Solution**: Check credentials match docker-compose.yml:
- Neo4j: `neo4j` / `sharkbakeoff`
- Memgraph: No auth required by default

### File Not Found Error

```
✗ File not found: ../sample/aircraft_instances.json
```

**Solution**: Run data generators first (see Prerequisites above)

### Memory Issues (Neo4j/Memgraph)

If loading fails with memory errors, increase Docker memory limits:

```bash
# Edit docker-compose.yml to add:
services:
  neo4j:
    environment:
      - NEO4J_dbms_memory_heap_max__size=4G
```

## Loader Implementation Details

### PostgreSQL Loader (`load_postgresql.py`)

- Uses `psycopg2` with `execute_batch` for performance
- Loads 1,000 rows per batch
- Handles JSONB for activity properties
- Creates foreign key relationships

### Neo4j Loader (`load_neo4j.py`)

- Uses `neo4j` Python driver
- Creates constraints/indexes from schema file
- Loads nodes in batches of 1,000
- Uses `UNWIND` for bulk inserts
- Converts ISO timestamps to Neo4j `datetime()`

### Memgraph Loader (`load_memgraph.py`)

- Nearly identical to Neo4j loader
- Uses port 7688 instead of 7687
- Uses `LocalDateTime()` instead of `datetime()`
- No authentication required
- Optimized for in-memory storage

## Performance Comparison

| Database | Load Time | Memory Usage |
|----------|-----------|--------------|
| PostgreSQL | 30-60s | ~500 MB |
| Neo4j | 2-5 min | ~2 GB |
| Memgraph | 1-3 min | ~3 GB (in-memory) |

## Next Steps

After loading data:

1. **Run benchmark queries** (from `benchmark/queries/`)
2. **Test performance** with Locust or custom harness
3. **Compare query latencies** across databases
4. **Validate ground truth patterns** for knowledge generation queries

## Reloading Data

To reload data (e.g., after regenerating):

```bash
# PostgreSQL: Truncate tables
docker exec -it shark-postgres psql -U shark -d sharkdb -c "
TRUNCATE organizations, locations, air_instance_lookup,
         ship_instance_lookup, track_activity_log, kb_relationships CASCADE;
"

# Neo4j: Use --clear flag
python3 load_neo4j.py --clear

# Memgraph: Use --clear flag
python3 load_memgraph.py --clear
```

Then run loaders again.
