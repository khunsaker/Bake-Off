#!/usr/bin/env python3
"""
Curation Testing for Shark Bake-Off
Tests operational curation workflows across PostgreSQL and Neo4j
"""

import time
import psycopg2
from neo4j import GraphDatabase
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import string


class DatabaseType(Enum):
    """Database type"""
    POSTGRESQL = "postgresql"
    NEO4J = "neo4j"
    MEMGRAPH = "memgraph"


@dataclass
class CurationTestResult:
    """Result of a curation test"""
    test_id: str
    test_name: str
    database: DatabaseType
    success: bool
    latency_seconds: float
    steps_required: int
    complexity: str  # 'simple', 'moderate', 'complex'
    self_service: bool  # Can curator do it without DBA?
    notes: str


class CurationTester:
    """
    Base class for curation testing
    """

    def __init__(self, database_type: DatabaseType, connection_params: Dict):
        self.database_type = database_type
        self.connection_params = connection_params
        self.results: List[CurationTestResult] = []

    def log_result(self, result: CurationTestResult):
        """Log a test result"""
        self.results.append(result)
        status = "✓ PASS" if result.success else "✗ FAIL"
        print(f"{status} | {result.test_id} | {result.test_name}")
        print(f"  Latency: {result.latency_seconds:.2f}s | Steps: {result.steps_required} | "
              f"Self-service: {'Yes' if result.self_service else 'No'}")
        if result.notes:
            print(f"  Notes: {result.notes}")
        print()


class PostgreSQLCurationTester(CurationTester):
    """PostgreSQL-specific curation tests"""

    def __init__(self, connection_params: Dict):
        super().__init__(DatabaseType.POSTGRESQL, connection_params)
        self.conn = psycopg2.connect(**connection_params)

    def close(self):
        self.conn.close()

    def ct1_property_update(self) -> CurationTestResult:
        """
        CT1: Property update latency
        Test: Update a property and measure time until visible via API
        """
        test_id = "CT1-PG"
        start_time = time.time()

        try:
            cursor = self.conn.cursor()

            # Step 1: Select a random aircraft
            cursor.execute("SELECT id, mode_s FROM air_instance_lookup LIMIT 1")
            result = cursor.fetchone()
            if not result:
                return CurationTestResult(
                    test_id=test_id,
                    test_name="Property Update Latency",
                    database=self.database_type,
                    success=False,
                    latency_seconds=0.0,
                    steps_required=0,
                    complexity='simple',
                    self_service=False,
                    notes="No test data available"
                )

            aircraft_id, mode_s = result

            # Step 2: Update a property
            new_operator = f"TEST_OPERATOR_{random.randint(1000, 9999)}"
            cursor.execute(
                "UPDATE air_instance_lookup SET operator = %s, updated_at = NOW() WHERE id = %s",
                (new_operator, aircraft_id)
            )
            self.conn.commit()

            update_time = time.time()

            # Step 3: Verify via query (simulating API read)
            cursor.execute(
                "SELECT operator FROM air_instance_lookup WHERE id = %s",
                (aircraft_id,)
            )
            updated_operator = cursor.fetchone()[0]

            query_time = time.time()

            success = updated_operator == new_operator
            total_latency = query_time - start_time

            return CurationTestResult(
                test_id=test_id,
                test_name="Property Update Latency",
                database=self.database_type,
                success=success,
                latency_seconds=total_latency,
                steps_required=2,  # Update + Commit
                complexity='simple',
                self_service=True,  # Can update via SQL or app
                notes=f"Update visible immediately (transaction-based). Cache invalidation may add latency in production."
            )

        except Exception as e:
            return CurationTestResult(
                test_id=test_id,
                test_name="Property Update Latency",
                database=self.database_type,
                success=False,
                latency_seconds=time.time() - start_time,
                steps_required=2,
                complexity='simple',
                self_service=True,
                notes=f"Error: {str(e)}"
            )

    def ct2_node_creation(self) -> CurationTestResult:
        """
        CT2: Node creation latency
        Test: Create a new node and measure time until queryable
        """
        test_id = "CT2-PG"
        start_time = time.time()

        try:
            cursor = self.conn.cursor()

            # Step 1: Insert new aircraft
            new_mode_s = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            cursor.execute("""
                INSERT INTO air_instance_lookup (mode_s, shark_name, platform, nationality)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (new_mode_s, f"TEST_AIRCRAFT_{new_mode_s}", "Test Platform", "USA"))

            new_id = cursor.fetchone()[0]
            self.conn.commit()

            insert_time = time.time()

            # Step 2: Query back immediately
            cursor.execute("SELECT shark_name FROM air_instance_lookup WHERE id = %s", (new_id,))
            result = cursor.fetchone()

            query_time = time.time()

            success = result is not None
            total_latency = query_time - start_time

            # Cleanup
            cursor.execute("DELETE FROM air_instance_lookup WHERE id = %s", (new_id,))
            self.conn.commit()

            return CurationTestResult(
                test_id=test_id,
                test_name="Node Creation Latency",
                database=self.database_type,
                success=success,
                latency_seconds=total_latency,
                steps_required=2,  # Insert + Commit
                complexity='simple',
                self_service=True,
                notes="Immediate queryability after commit. ACID guarantees ensure consistency."
            )

        except Exception as e:
            return CurationTestResult(
                test_id=test_id,
                test_name="Node Creation Latency",
                database=self.database_type,
                success=False,
                latency_seconds=time.time() - start_time,
                steps_required=2,
                complexity='simple',
                self_service=True,
                notes=f"Error: {str(e)}"
            )

    def ct4_schema_add_property(self) -> CurationTestResult:
        """
        CT4: Schema addition (property)
        Test: Add a new property to an existing table
        """
        test_id = "CT4-PG"
        start_time = time.time()

        steps = 0

        try:
            cursor = self.conn.cursor()

            # Step 1: Create new column (requires ALTER TABLE)
            steps += 1
            new_column = f"test_property_{random.randint(1000, 9999)}"

            cursor.execute(f"""
                ALTER TABLE air_instance_lookup
                ADD COLUMN IF NOT EXISTS {new_column} VARCHAR(100)
            """)
            self.conn.commit()
            steps += 1

            # Step 2: Use the new column
            cursor.execute(f"""
                UPDATE air_instance_lookup
                SET {new_column} = 'test_value'
                WHERE id = (SELECT id FROM air_instance_lookup LIMIT 1)
            """)
            self.conn.commit()
            steps += 1

            # Step 3: Verify
            cursor.execute(f"SELECT {new_column} FROM air_instance_lookup WHERE {new_column} = 'test_value'")
            result = cursor.fetchone()

            # Step 4: Cleanup
            cursor.execute(f"ALTER TABLE air_instance_lookup DROP COLUMN IF EXISTS {new_column}")
            self.conn.commit()
            steps += 1

            success = result is not None
            total_latency = time.time() - start_time

            return CurationTestResult(
                test_id=test_id,
                test_name="Schema Addition (Property)",
                database=self.database_type,
                success=success,
                latency_seconds=total_latency,
                steps_required=steps,
                complexity='moderate',
                self_service=False,  # Requires DBA or migration
                notes="Requires ALTER TABLE (DDL). May lock table. Needs migration script for production. Not self-service for curators."
            )

        except Exception as e:
            return CurationTestResult(
                test_id=test_id,
                test_name="Schema Addition (Property)",
                database=self.database_type,
                success=False,
                latency_seconds=time.time() - start_time,
                steps_required=steps,
                complexity='moderate',
                self_service=False,
                notes=f"Error: {str(e)}"
            )

    def ct6_batch_import(self, batch_size: int = 1000) -> CurationTestResult:
        """
        CT6: Batch import
        Test: Import 1000 entities with relationships
        """
        test_id = "CT6-PG"
        start_time = time.time()

        try:
            cursor = self.conn.cursor()

            # Generate test data
            test_data = []
            for i in range(batch_size):
                mode_s = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                test_data.append((
                    mode_s,
                    f"BATCH_TEST_{i}",
                    "Test Platform",
                    "USA"
                ))

            # Batch insert
            cursor.executemany("""
                INSERT INTO air_instance_lookup (mode_s, shark_name, platform, nationality)
                VALUES (%s, %s, %s, %s)
            """, test_data)

            self.conn.commit()

            total_latency = time.time() - start_time

            # Verify count
            cursor.execute("SELECT COUNT(*) FROM air_instance_lookup WHERE shark_name LIKE 'BATCH_TEST_%'")
            count = cursor.fetchone()[0]

            success = count == batch_size

            # Cleanup
            cursor.execute("DELETE FROM air_instance_lookup WHERE shark_name LIKE 'BATCH_TEST_%'")
            self.conn.commit()

            throughput = batch_size / total_latency

            return CurationTestResult(
                test_id=test_id,
                test_name=f"Batch Import ({batch_size} entities)",
                database=self.database_type,
                success=success,
                latency_seconds=total_latency,
                steps_required=2,  # Insert + Commit
                complexity='simple',
                self_service=True,
                notes=f"Throughput: {throughput:.0f} entities/sec. COPY command would be faster for large batches."
            )

        except Exception as e:
            return CurationTestResult(
                test_id=test_id,
                test_name=f"Batch Import ({batch_size} entities)",
                database=self.database_type,
                success=False,
                latency_seconds=time.time() - start_time,
                steps_required=2,
                complexity='simple',
                self_service=True,
                notes=f"Error: {str(e)}"
            )


class Neo4jCurationTester(CurationTester):
    """Neo4j-specific curation tests"""

    def __init__(self, connection_params: Dict):
        super().__init__(DatabaseType.NEO4J, connection_params)
        self.driver = GraphDatabase.driver(
            connection_params['uri'],
            auth=(connection_params['user'], connection_params['password'])
        )

    def close(self):
        self.driver.close()

    def ct1_property_update(self) -> CurationTestResult:
        """CT1: Property update latency for Neo4j"""
        test_id = "CT1-NEO4J"
        start_time = time.time()

        try:
            with self.driver.session() as session:
                # Step 1: Get a random aircraft
                result = session.run("MATCH (a:Aircraft) RETURN a.mode_s AS mode_s LIMIT 1")
                record = result.single()
                if not record:
                    return CurationTestResult(
                        test_id=test_id,
                        test_name="Property Update Latency",
                        database=self.database_type,
                        success=False,
                        latency_seconds=0.0,
                        steps_required=0,
                        complexity='simple',
                        self_service=True,
                        notes="No test data available"
                    )

                mode_s = record['mode_s']

                # Step 2: Update property
                new_operator = f"TEST_OPERATOR_{random.randint(1000, 9999)}"
                session.run("""
                    MATCH (a:Aircraft {mode_s: $mode_s})
                    SET a.operator = $new_operator
                """, mode_s=mode_s, new_operator=new_operator)

                update_time = time.time()

                # Step 3: Verify
                result = session.run("""
                    MATCH (a:Aircraft {mode_s: $mode_s})
                    RETURN a.operator AS operator
                """, mode_s=mode_s)

                record = result.single()
                query_time = time.time()

                success = record and record['operator'] == new_operator
                total_latency = query_time - start_time

                return CurationTestResult(
                    test_id=test_id,
                    test_name="Property Update Latency",
                    database=self.database_type,
                    success=success,
                    latency_seconds=total_latency,
                    steps_required=1,  # Single Cypher query
                    complexity='simple',
                    self_service=True,
                    notes="Immediate visibility. Can be done via Bloom UI without writing Cypher."
                )

        except Exception as e:
            return CurationTestResult(
                test_id=test_id,
                test_name="Property Update Latency",
                database=self.database_type,
                success=False,
                latency_seconds=time.time() - start_time,
                steps_required=1,
                complexity='simple',
                self_service=True,
                notes=f"Error: {str(e)}"
            )

    def ct2_node_creation(self) -> CurationTestResult:
        """CT2: Node creation latency for Neo4j"""
        test_id = "CT2-NEO4J"
        start_time = time.time()

        try:
            with self.driver.session() as session:
                # Step 1: Create node
                new_mode_s = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                session.run("""
                    CREATE (a:Aircraft {
                        mode_s: $mode_s,
                        shark_name: $name,
                        platform: 'Test Platform',
                        nationality: 'USA'
                    })
                """, mode_s=new_mode_s, name=f"TEST_AIRCRAFT_{new_mode_s}")

                create_time = time.time()

                # Step 2: Query back
                result = session.run("""
                    MATCH (a:Aircraft {mode_s: $mode_s})
                    RETURN a.shark_name AS name
                """, mode_s=new_mode_s)

                record = result.single()
                query_time = time.time()

                success = record is not None

                # Cleanup
                session.run("MATCH (a:Aircraft {mode_s: $mode_s}) DELETE a", mode_s=new_mode_s)

                total_latency = query_time - start_time

                return CurationTestResult(
                    test_id=test_id,
                    test_name="Node Creation Latency",
                    database=self.database_type,
                    success=success,
                    latency_seconds=total_latency,
                    steps_required=1,  # Single CREATE statement
                    complexity='simple',
                    self_service=True,
                    notes="Immediate queryability. Can create via Bloom UI with point-and-click."
                )

        except Exception as e:
            return CurationTestResult(
                test_id=test_id,
                test_name="Node Creation Latency",
                database=self.database_type,
                success=False,
                latency_seconds=time.time() - start_time,
                steps_required=1,
                complexity='simple',
                self_service=True,
                notes=f"Error: {str(e)}"
            )

    def ct3_relationship_creation(self) -> CurationTestResult:
        """CT3: Relationship creation test"""
        test_id = "CT3-NEO4J"
        start_time = time.time()

        try:
            with self.driver.session() as session:
                # Step 1: Get two aircraft
                result = session.run("MATCH (a:Aircraft) RETURN a.mode_s AS mode_s LIMIT 2")
                records = list(result)
                if len(records) < 2:
                    return CurationTestResult(
                        test_id=test_id,
                        test_name="Relationship Creation",
                        database=self.database_type,
                        success=False,
                        latency_seconds=0.0,
                        steps_required=0,
                        complexity='simple',
                        self_service=True,
                        notes="Insufficient test data"
                    )

                mode_s1 = records[0]['mode_s']
                mode_s2 = records[1]['mode_s']

                # Step 2: Create relationship
                session.run("""
                    MATCH (a1:Aircraft {mode_s: $mode_s1})
                    MATCH (a2:Aircraft {mode_s: $mode_s2})
                    CREATE (a1)-[r:TEST_RELATIONSHIP {
                        created_at: datetime(),
                        test: true
                    }]->(a2)
                """, mode_s1=mode_s1, mode_s2=mode_s2)

                create_time = time.time()

                # Step 3: Verify relationship exists
                result = session.run("""
                    MATCH (a1:Aircraft {mode_s: $mode_s1})-[r:TEST_RELATIONSHIP]->(a2:Aircraft {mode_s: $mode_s2})
                    RETURN count(r) AS count
                """, mode_s1=mode_s1, mode_s2=mode_s2)

                count = result.single()['count']
                query_time = time.time()

                success = count > 0

                # Cleanup
                session.run("""
                    MATCH (a1:Aircraft {mode_s: $mode_s1})-[r:TEST_RELATIONSHIP]->(a2:Aircraft {mode_s: $mode_s2})
                    DELETE r
                """, mode_s1=mode_s1, mode_s2=mode_s2)

                total_latency = query_time - start_time

                return CurationTestResult(
                    test_id=test_id,
                    test_name="Relationship Creation",
                    database=self.database_type,
                    success=success,
                    latency_seconds=total_latency,
                    steps_required=1,  # Single CREATE statement
                    complexity='simple',
                    self_service=True,
                    notes="Relationships are first-class citizens. Can create via Bloom UI by dragging nodes."
                )

        except Exception as e:
            return CurationTestResult(
                test_id=test_id,
                test_name="Relationship Creation",
                database=self.database_type,
                success=False,
                latency_seconds=time.time() - start_time,
                steps_required=1,
                complexity='simple',
                self_service=True,
                notes=f"Error: {str(e)}"
            )

    def ct4_schema_add_property(self) -> CurationTestResult:
        """CT4: Schema addition (property) for Neo4j"""
        test_id = "CT4-NEO4J"
        start_time = time.time()

        try:
            with self.driver.session() as session:
                # Neo4j is schemaless - just add property
                new_property = f"test_property_{random.randint(1000, 9999)}"

                # Step 1: Add property to a node (no schema change needed!)
                session.run(f"""
                    MATCH (a:Aircraft)
                    WITH a LIMIT 1
                    SET a.{new_property} = 'test_value'
                """)

                add_time = time.time()

                # Step 2: Verify
                result = session.run(f"""
                    MATCH (a:Aircraft)
                    WHERE a.{new_property} = 'test_value'
                    RETURN count(a) AS count
                """)

                count = result.single()['count']

                # Cleanup
                session.run(f"""
                    MATCH (a:Aircraft)
                    WHERE a.{new_property} IS NOT NULL
                    REMOVE a.{new_property}
                """)

                total_latency = time.time() - start_time
                success = count > 0

                return CurationTestResult(
                    test_id=test_id,
                    test_name="Schema Addition (Property)",
                    database=self.database_type,
                    success=success,
                    latency_seconds=total_latency,
                    steps_required=1,  # Just SET the property
                    complexity='simple',
                    self_service=True,
                    notes="No schema change needed! Just SET property. Immediate availability. Fully self-service."
                )

        except Exception as e:
            return CurationTestResult(
                test_id=test_id,
                test_name="Schema Addition (Property)",
                database=self.database_type,
                success=False,
                latency_seconds=time.time() - start_time,
                steps_required=1,
                complexity='simple',
                self_service=True,
                notes=f"Error: {str(e)}"
            )

    def ct5_schema_add_relationship_type(self) -> CurationTestResult:
        """CT5: Schema addition (relationship type)"""
        test_id = "CT5-NEO4J"
        start_time = time.time()

        try:
            with self.driver.session() as session:
                # Get two nodes
                result = session.run("MATCH (a:Aircraft) RETURN a.mode_s AS mode_s LIMIT 2")
                records = list(result)
                if len(records) < 2:
                    return CurationTestResult(
                        test_id=test_id,
                        test_name="Schema Addition (Relationship Type)",
                        database=self.database_type,
                        success=False,
                        latency_seconds=0.0,
                        steps_required=0,
                        complexity='simple',
                        self_service=True,
                        notes="Insufficient test data"
                    )

                mode_s1, mode_s2 = records[0]['mode_s'], records[1]['mode_s']

                # Step 1: Create new relationship type (no schema needed!)
                new_rel_type = f"TEST_REL_{random.randint(1000, 9999)}"

                session.run(f"""
                    MATCH (a1:Aircraft {{mode_s: $mode_s1}})
                    MATCH (a2:Aircraft {{mode_s: $mode_s2}})
                    CREATE (a1)-[r:{new_rel_type} {{created_at: datetime()}}]->(a2)
                """, mode_s1=mode_s1, mode_s2=mode_s2)

                create_time = time.time()

                # Step 2: Verify
                result = session.run(f"""
                    MATCH (a1)-[r:{new_rel_type}]->(a2)
                    RETURN count(r) AS count
                """)

                count = result.single()['count']

                # Cleanup
                session.run(f"MATCH ()-[r:{new_rel_type}]->() DELETE r")

                total_latency = time.time() - start_time
                success = count > 0

                return CurationTestResult(
                    test_id=test_id,
                    test_name="Schema Addition (Relationship Type)",
                    database=self.database_type,
                    success=success,
                    latency_seconds=total_latency,
                    steps_required=1,  # Just CREATE with new type
                    complexity='simple',
                    self_service=True,
                    notes="No schema change needed! Just CREATE with new type. Immediate availability. Fully self-service."
                )

        except Exception as e:
            return CurationTestResult(
                test_id=test_id,
                test_name="Schema Addition (Relationship Type)",
                database=self.database_type,
                success=False,
                latency_seconds=time.time() - start_time,
                steps_required=1,
                complexity='simple',
                self_service=True,
                notes=f"Error: {str(e)}"
            )

    def ct6_batch_import(self, batch_size: int = 1000) -> CurationTestResult:
        """CT6: Batch import for Neo4j"""
        test_id = "CT6-NEO4J"
        start_time = time.time()

        try:
            with self.driver.session() as session:
                # Generate test data
                test_data = []
                for i in range(batch_size):
                    mode_s = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    test_data.append({
                        'mode_s': mode_s,
                        'name': f"BATCH_TEST_{i}",
                        'platform': 'Test Platform',
                        'nationality': 'USA'
                    })

                # Batch create using UNWIND
                session.run("""
                    UNWIND $data AS item
                    CREATE (a:Aircraft {
                        mode_s: item.mode_s,
                        shark_name: item.name,
                        platform: item.platform,
                        nationality: item.nationality
                    })
                """, data=test_data)

                create_time = time.time()

                # Verify count
                result = session.run("""
                    MATCH (a:Aircraft)
                    WHERE a.shark_name STARTS WITH 'BATCH_TEST_'
                    RETURN count(a) AS count
                """)

                count = result.single()['count']

                # Cleanup
                session.run("""
                    MATCH (a:Aircraft)
                    WHERE a.shark_name STARTS WITH 'BATCH_TEST_'
                    DELETE a
                """)

                total_latency = time.time() - start_time
                success = count == batch_size
                throughput = batch_size / total_latency

                return CurationTestResult(
                    test_id=test_id,
                    test_name=f"Batch Import ({batch_size} entities)",
                    database=self.database_type,
                    success=success,
                    latency_seconds=total_latency,
                    steps_required=1,  # Single UNWIND statement
                    complexity='simple',
                    self_service=True,
                    notes=f"Throughput: {throughput:.0f} entities/sec. LOAD CSV or APOC for larger batches."
                )

        except Exception as e:
            return CurationTestResult(
                test_id=test_id,
                test_name=f"Batch Import ({batch_size} entities)",
                database=self.database_type,
                success=False,
                latency_seconds=time.time() - start_time,
                steps_required=1,
                complexity='simple',
                self_service=True,
                notes=f"Error: {str(e)}"
            )


def print_summary(results: List[CurationTestResult]):
    """Print summary of curation tests"""
    from tabulate import tabulate

    print("\n" + "="*80)
    print("CURATION TEST SUMMARY")
    print("="*80 + "\n")

    # Group by database
    pg_results = [r for r in results if r.database == DatabaseType.POSTGRESQL]
    neo4j_results = [r for r in results if r.database == DatabaseType.NEO4J]

    # Prepare comparison table
    rows = []
    test_ids = sorted(set(r.test_id.split('-')[0] for r in results))

    for test_id in test_ids:
        pg_result = next((r for r in pg_results if r.test_id.startswith(test_id)), None)
        neo4j_result = next((r for r in neo4j_results if r.test_id.startswith(test_id)), None)

        test_name = pg_result.test_name if pg_result else neo4j_result.test_name

        rows.append([
            test_id,
            test_name,
            f"{pg_result.latency_seconds:.2f}s" if pg_result else "N/A",
            f"{pg_result.steps_required}" if pg_result else "N/A",
            "Yes" if pg_result and pg_result.self_service else "No",
            f"{neo4j_result.latency_seconds:.2f}s" if neo4j_result else "N/A",
            f"{neo4j_result.steps_required}" if neo4j_result else "N/A",
            "Yes" if neo4j_result and neo4j_result.self_service else "No",
        ])

    headers = ["Test", "Name", "PG Time", "PG Steps", "PG Self-Svc", "Neo4j Time", "Neo4j Steps", "Neo4j Self-Svc"]
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    # Key findings
    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)

    pg_self_service = sum(1 for r in pg_results if r.self_service)
    neo4j_self_service = sum(1 for r in neo4j_results if r.self_service)

    print(f"\nPostgreSQL:")
    print(f"  Self-service operations: {pg_self_service}/{len(pg_results)}")
    print(f"  Average latency: {sum(r.latency_seconds for r in pg_results)/len(pg_results):.2f}s")

    print(f"\nNeo4j:")
    print(f"  Self-service operations: {neo4j_self_service}/{len(neo4j_results)}")
    print(f"  Average latency: {sum(r.latency_seconds for r in neo4j_results)/len(neo4j_results):.2f}s")

    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    # Example usage
    import sys

    print("="*80)
    print("Shark Bake-Off: Curation Testing")
    print("="*80 + "\n")

    # PostgreSQL tests
    print("Running PostgreSQL Curation Tests...\n")
    pg_tester = PostgreSQLCurationTester({
        'host': 'localhost',
        'port': 5432,
        'database': 'sharkdb',
        'user': 'shark',
        'password': 'sharkbakeoff'
    })

    try:
        pg_tester.log_result(pg_tester.ct1_property_update())
        pg_tester.log_result(pg_tester.ct2_node_creation())
        pg_tester.log_result(pg_tester.ct4_schema_add_property())
        pg_tester.log_result(pg_tester.ct6_batch_import(batch_size=1000))
    finally:
        pg_tester.close()

    # Neo4j tests
    print("\nRunning Neo4j Curation Tests...\n")
    neo4j_tester = Neo4jCurationTester({
        'uri': 'bolt://localhost:7687',
        'user': 'neo4j',
        'password': 'sharkbakeoff'
    })

    try:
        neo4j_tester.log_result(neo4j_tester.ct1_property_update())
        neo4j_tester.log_result(neo4j_tester.ct2_node_creation())
        neo4j_tester.log_result(neo4j_tester.ct3_relationship_creation())
        neo4j_tester.log_result(neo4j_tester.ct4_schema_add_property())
        neo4j_tester.log_result(neo4j_tester.ct5_schema_add_relationship_type())
        neo4j_tester.log_result(neo4j_tester.ct6_batch_import(batch_size=1000))
    finally:
        neo4j_tester.close()

    # Print summary
    all_results = pg_tester.results + neo4j_tester.results
    print_summary(all_results)
