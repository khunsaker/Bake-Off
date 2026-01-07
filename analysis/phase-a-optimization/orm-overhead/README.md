# ORM Overhead Analysis

Quantify the performance cost of ORM/OGM abstraction layers vs raw database drivers.

## Objective

Measure the performance overhead introduced by Object-Relational Mapping (ORM) and Object-Graph Mapping (OGM) libraries compared to raw database drivers.

**Why this matters:**
- ORMs add developer convenience but may impact performance
- Quantify the trade-off: developer productivity vs query latency
- Inform decision on whether ORM overhead is acceptable for production

## Approach

For each database, we'll compare:

### PostgreSQL

| Implementation | Type | Language | Description |
|---------------|------|----------|-------------|
| tokio-postgres | Raw Driver | Rust | Direct SQL, connection pooling (baseline) |
| SQLx | Compile-time ORM | Rust | Compile-time checked queries |
| Diesel | ORM | Rust | Full ORM with query builder |
| SQLAlchemy | ORM | Python | Popular Python ORM |

### Neo4j

| Implementation | Type | Language | Description |
|---------------|------|----------|-------------|
| neo4rs | Raw Driver | Rust | Direct Cypher, connection pooling (baseline) |
| Neo4j OGM | OGM | Java | Object-graph mapper |
| Neomodel | OGM | Python | Python OGM for Neo4j |

### Memgraph

| Implementation | Type | Language | Description |
|---------------|------|----------|-------------|
| mgclient (Rust) | Raw Driver | Rust | Direct Cypher via Bolt protocol (baseline) |
| (Compare to Neo4j drivers) | - | - | Same Bolt protocol, similar overhead expected |

## Metrics

For each implementation, measure:

1. **Latency overhead**: p50, p95, p99 compared to baseline
2. **Throughput impact**: Requests/sec compared to baseline
3. **Memory overhead**: RAM usage compared to baseline
4. **Code complexity**: Lines of code for common operations

## Test Queries

Use the same benchmark queries (S1-S10) for all implementations:

- **S1**: Single entity lookup by ID (identifier lookup)
- **S3**: Two-hop relationship traversal
- **S4**: Three-hop relationship traversal
- **S7**: Aggregate query (count)

## Expected Results

Based on industry knowledge:

| Database   | ORM Type | Expected Overhead |
|-----------|----------|-------------------|
| PostgreSQL | SQLx (Rust) | 5-10% (compile-time) |
| PostgreSQL | Diesel (Rust) | 10-20% (runtime query building) |
| PostgreSQL | SQLAlchemy (Python) | 30-50% (Python overhead + ORM) |
| Neo4j | Neo4j OGM (Java) | 15-30% (object mapping) |
| Neo4j | Neomodel (Python) | 40-60% (Python + OGM) |

## Implementation Status

### Current Implementation (Baseline)

✅ **Rust with Raw Drivers** (already implemented in `implementations/rust/`)
- PostgreSQL: tokio-postgres
- Neo4j: neo4rs
- Memgraph: compatible with Neo4j driver (Bolt protocol)

### To Implement

#### PostgreSQL - SQLx

```rust
use sqlx::postgres::PgPool;

#[derive(sqlx::FromRow)]
struct Aircraft {
    id: i32,
    mode_s: String,
    shark_name: String,
    platform: String,
}

async fn get_aircraft_by_mode_s(pool: &PgPool, mode_s: &str) -> Result<Aircraft> {
    sqlx::query_as!(
        Aircraft,
        "SELECT id, mode_s, shark_name, platform FROM air_instance_lookup WHERE mode_s = $1",
        mode_s
    )
    .fetch_one(pool)
    .await
}
```

**Pros**: Compile-time SQL checking, minimal overhead
**Cons**: Less flexible than raw SQL

#### PostgreSQL - Diesel

```rust
use diesel::prelude::*;

#[derive(Queryable)]
struct Aircraft {
    id: i32,
    mode_s: String,
    shark_name: String,
    platform: String,
}

fn get_aircraft_by_mode_s(conn: &PgConnection, mode_s_value: &str) -> Result<Aircraft> {
    use crate::schema::air_instance_lookup::dsl::*;

    air_instance_lookup
        .filter(mode_s.eq(mode_s_value))
        .first::<Aircraft>(conn)
}
```

**Pros**: Full ORM features, type-safe
**Cons**: More overhead than raw SQL, learning curve

#### Neo4j OGM (Java)

```java
@NodeEntity
public class Aircraft {
    @Id
    private Long id;

    @Property("mode_s")
    private String modeS;

    @Property("shark_name")
    private String sharkName;

    @Relationship(type = "OPERATED_BY")
    private Organization operator;
}

// Usage
Session session = sessionFactory.openSession();
Aircraft aircraft = session.load(Aircraft.class, modeS);
```

**Pros**: Object-oriented, familiar to Java developers
**Cons**: Overhead from object mapping, lazy loading

## Testing Procedure

### 1. Implement ORM Variants

For each database, create alternate implementations using ORMs.

**Directory structure:**
```
implementations/
  rust-raw/           # Baseline (already exists)
  rust-sqlx/          # PostgreSQL with SQLx
  rust-diesel/        # PostgreSQL with Diesel
  python-sqlalchemy/  # PostgreSQL with SQLAlchemy
  java-neo4j-ogm/     # Neo4j with OGM
  python-neomodel/    # Neo4j with Neomodel
```

### 2. Run Benchmarks

For each implementation:

```bash
# Start the implementation on a different port
# e.g., Rust + SQLx on :8081

cd benchmark/harness
python runner.py http://localhost:8081 \
  --pattern balanced-50 \
  --requests 50000 \
  --concurrency 20 \
  --output ../../analysis/phase-a-optimization/orm-overhead/results/postgres-sqlx
```

### 3. Compare Results

Use the comparison script:

```bash
cd analysis/phase-a-optimization/orm-overhead
python compare_orm_overhead.py
```

## Deliverables

1. **Performance comparison table**:

| Database | Implementation | p99 Latency | Overhead % | Throughput | Code LOC |
|----------|---------------|-------------|------------|------------|----------|
| PostgreSQL | Raw (tokio-postgres) | 42ms | 0% (baseline) | 387 req/s | 150 |
| PostgreSQL | SQLx | 46ms | +9.5% | 365 req/s | 120 |
| PostgreSQL | Diesel | 52ms | +23.8% | 325 req/s | 200 |
| PostgreSQL | SQLAlchemy | 68ms | +61.9% | 250 req/s | 80 |
| Neo4j | Raw (neo4rs) | 18ms | 0% (baseline) | 520 req/s | 130 |
| Neo4j | Neo4j OGM | 24ms | +33.3% | 410 req/s | 250 |
| Neo4j | Neomodel | 32ms | +77.8% | 310 req/s | 100 |

2. **Recommendation matrix**:

| Scenario | Recommended | Rationale |
|----------|-------------|-----------|
| High performance required | Raw drivers | Minimal overhead |
| Rapid development | ORM (Diesel, Neo4j OGM) | Developer productivity |
| Code maintainability | SQLx | Compile-time safety + low overhead |
| Prototyping | Python ORMs | Fastest to develop |

3. **Decision criteria**:

```
IF overhead < 10%:
    ✓ ORM is acceptable for production

IF overhead 10-25%:
    ⚠ ORM acceptable if developer productivity gain is significant

IF overhead > 25%:
    ✗ Use raw drivers for critical paths
    ✓ ORM for admin/reporting queries
```

## When ORM Overhead is Acceptable

Based on the Shark Bake-Off requirements:

**Acceptable:**
- Admin interfaces (curator tools)
- Batch operations (data import)
- Reporting queries (analytics)
- Non-critical paths

**Not Acceptable:**
- Real-time query API (S1-S10 benchmark queries)
- High-frequency identifier lookups
- Graph traversal operations

## Implementation Priority

**High Priority:**
1. ✅ Rust + Raw Drivers (baseline - already done)
2. Rust + SQLx (low overhead, practical alternative)
3. Python + SQLAlchemy (common production choice)

**Medium Priority:**
4. Rust + Diesel (full ORM comparison)
5. Java + Neo4j OGM (official OGM)

**Low Priority:**
6. Python + Neomodel (high overhead expected)

## Simplified Testing (If Time Constrained)

If implementing multiple ORMs is not feasible, use **microbenchmarks**:

```python
# Measure just the ORM overhead, not full HTTP stack
import timeit

# Raw query
def raw_query():
    cursor.execute("SELECT * FROM air_instance_lookup WHERE mode_s = %s", (mode_s,))
    return cursor.fetchone()

# ORM query
def orm_query():
    return session.query(Aircraft).filter_by(mode_s=mode_s).first()

raw_time = timeit.timeit(raw_query, number=1000)
orm_time = timeit.timeit(orm_query, number=1000)

overhead_pct = ((orm_time - raw_time) / raw_time) * 100
print(f"ORM overhead: {overhead_pct:.1f}%")
```

## References

- [SQLx Documentation](https://github.com/launchbadge/sqlx)
- [Diesel Documentation](https://diesel.rs/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [Neo4j OGM Documentation](https://neo4j.com/docs/ogm-manual/current/)
- [Neomodel Documentation](https://neomodel.readthedocs.io/)

## Decision Impact

ORM overhead analysis contributes to:

- **Implementation recommendation**: Which driver/ORM to use in production
- **Architecture decision**: Hybrid approach (raw for critical, ORM for admin)
- **Cost-benefit analysis**: Developer time vs performance

**Weight in final decision**: ~5-10% (informative, not primary driver)
