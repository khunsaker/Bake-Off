#!/usr/bin/env python3
"""
Neo4j Data Loader for Shark Bake-Off
Loads generated JSON data into Neo4j graph database
"""

import json
from neo4j import GraphDatabase
import sys
from datetime import datetime


class Neo4jLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Clear all nodes and relationships (for clean reload)"""
        print("\nClearing existing data...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("  ✓ Database cleared")

    def create_constraints_and_indexes(self):
        """Create constraints and indexes"""
        print("\nCreating constraints and indexes...")

        with self.driver.session() as session:
            # Run the constraint/index creation script
            with open('../../schema/neo4j/001_constraints_indexes.cypher') as f:
                cypher_script = f.read()

            # Split by semicolon and execute each statement
            statements = [s.strip() for s in cypher_script.split(';') if s.strip() and not s.strip().startswith('//')]

            for statement in statements:
                try:
                    session.run(statement)
                except Exception as e:
                    # Constraints may already exist, continue
                    pass

        print("  ✓ Constraints and indexes created")

    def load_organizations(self, data_dir: str):
        """Load organizations as nodes"""
        print("\nLoading organizations...")

        with open(f'{data_dir}/organizations.json') as f:
            orgs = json.load(f)

        with self.driver.session() as session:
            # Create organization nodes
            query = """
                UNWIND $orgs AS org
                CREATE (o:Organization {
                    id: org.id,
                    name: org.name,
                    org_type: org.org_type,
                    country: org.country,
                    created_at: datetime(org.created_at)
                })
            """
            session.run(query, orgs=orgs)

            # Create hierarchy relationships
            query = """
                MATCH (child:Organization), (parent:Organization)
                WHERE child.id = $child_id AND parent.name = $parent_name
                CREATE (child)-[:PART_OF]->(parent)
            """

            for org in orgs:
                if org['parent']:
                    session.run(query, child_id=org['id'], parent_name=org['parent'])

        print(f"  Loaded {len(orgs)} organizations")

    def load_locations(self, data_dir: str):
        """Load locations as nodes"""
        print("\nLoading locations...")

        with open(f'{data_dir}/locations.json') as f:
            locs = json.load(f)

        with self.driver.session() as session:
            query = """
                UNWIND $locs AS loc
                CREATE (l:Location {
                    id: loc.id,
                    name: loc.name,
                    location_type: loc.location_type,
                    icao_code: loc.icao_code,
                    country: loc.country,
                    latitude: loc.latitude,
                    longitude: loc.longitude,
                    created_at: datetime(loc.created_at)
                })
            """
            session.run(query, locs=locs)

        print(f"  Loaded {len(locs)} locations")

    def load_aircraft(self, data_dir: str):
        """Load aircraft as nodes"""
        print("\nLoading aircraft instances...")

        with open(f'{data_dir}/aircraft_instances.json') as f:
            aircraft = json.load(f)

        with self.driver.session() as session:
            # Load in batches of 1000
            batch_size = 1000
            for i in range(0, len(aircraft), batch_size):
                batch = aircraft[i:i+batch_size]

                query = """
                    UNWIND $aircraft AS ac
                    CREATE (a:Aircraft {
                        id: ac.id,
                        mode_s: ac.mode_s,
                        tail_number: ac.tail_number,
                        icao_type_code: ac.icao_type_code,
                        shark_name: ac.shark_name,
                        platform: ac.platform,
                        affiliation: ac.affiliation,
                        nationality: ac.nationality,
                        operator: ac.operator,
                        air_type: ac.air_type,
                        air_model: ac.air_model,
                        air_role: ac.air_role,
                        max_altitude_ft: ac.max_altitude_ft,
                        min_altitude_ft: ac.min_altitude_ft,
                        max_speed_kts: ac.max_speed_kts,
                        min_speed_kts: ac.min_speed_kts,
                        typical_cruise_altitude_ft: ac.typical_cruise_altitude_ft,
                        typical_cruise_speed_kts: ac.typical_cruise_speed_kts,
                        source: ac.source,
                        source_timestamp: datetime(ac.source_timestamp),
                        curator_modified: ac.curator_modified,
                        curator_id: ac.curator_id,
                        curator_locked: ac.curator_locked,
                        created_at: datetime(ac.created_at),
                        updated_at: datetime(ac.updated_at),
                        pg_id: ac.id
                    })
                """
                session.run(query, aircraft=batch)

                if (i + batch_size) % 5000 == 0:
                    print(f"    Loaded {i + batch_size:,} aircraft...")

        print(f"  Loaded {len(aircraft)} aircraft")

    def load_ships(self, data_dir: str):
        """Load ships as nodes"""
        print("\nLoading ship instances...")

        with open(f'{data_dir}/ship_instances.json') as f:
            ships = json.load(f)

        with self.driver.session() as session:
            query = """
                UNWIND $ships AS ship
                CREATE (s:Ship {
                    id: ship.id,
                    mmsi: ship.mmsi,
                    sconum: ship.sconum,
                    imo_number: ship.imo_number,
                    call_sign: ship.call_sign,
                    shark_name: ship.shark_name,
                    platform: ship.platform,
                    affiliation: ship.affiliation,
                    nationality: ship.nationality,
                    operator: ship.operator,
                    ship_type: ship.ship_type,
                    ship_class: ship.ship_class,
                    ship_role: ship.ship_role,
                    length_meters: ship.length_meters,
                    beam_meters: ship.beam_meters,
                    draft_meters: ship.draft_meters,
                    displacement_tons: ship.displacement_tons,
                    max_speed_kts: ship.max_speed_kts,
                    typical_speed_kts: ship.typical_speed_kts,
                    source: ship.source,
                    source_timestamp: datetime(ship.source_timestamp),
                    curator_modified: ship.curator_modified,
                    curator_id: ship.curator_id,
                    curator_locked: ship.curator_locked,
                    created_at: datetime(ship.created_at),
                    updated_at: datetime(ship.updated_at),
                    pg_id: ship.id
                })
            """
            session.run(query, ships=ships)

        print(f"  Loaded {len(ships)} ships")

    def load_operational_relationships(self, data_dir: str):
        """Create OPERATED_BY relationships"""
        print("\nCreating OPERATED_BY relationships...")

        with open(f'{data_dir}/aircraft_instances.json') as f:
            aircraft = json.load(f)

        with open(f'{data_dir}/ship_instances.json') as f:
            ships = json.load(f)

        with self.driver.session() as session:
            # Aircraft -> Organizations
            query = """
                UNWIND $items AS item
                MATCH (a:Aircraft {id: item.id})
                MATCH (o:Organization {id: item.operator_id})
                CREATE (a)-[:OPERATED_BY]->(o)
            """
            session.run(query, items=aircraft)

            # Ships -> Organizations
            query = """
                UNWIND $items AS item
                MATCH (s:Ship {id: item.id})
                MATCH (o:Organization {id: item.operator_id})
                CREATE (s)-[:OPERATED_BY]->(o)
            """
            session.run(query, items=ships)

        print(f"  Created {len(aircraft) + len(ships)} OPERATED_BY relationships")

    def load_location_relationships(self, data_dir: str):
        """Create BASED_AT and HOME_PORT relationships"""
        print("\nCreating location relationships...")

        with open(f'{data_dir}/aircraft_instances.json') as f:
            aircraft = json.load(f)

        with open(f'{data_dir}/ship_instances.json') as f:
            ships = json.load(f)

        with self.driver.session() as session:
            # Aircraft -> BASED_AT -> Locations
            aircraft_with_base = [a for a in aircraft if a.get('home_base_id')]
            query = """
                UNWIND $items AS item
                MATCH (a:Aircraft {id: item.id})
                MATCH (l:Location {id: item.home_base_id})
                CREATE (a)-[:BASED_AT]->(l)
            """
            session.run(query, items=aircraft_with_base)

            # Ships -> HOME_PORT -> Locations
            ships_with_port = [s for s in ships if s.get('home_port_id')]
            query = """
                UNWIND $items AS item
                MATCH (s:Ship {id: item.id})
                MATCH (l:Location {id: item.home_port_id})
                CREATE (s)-[:HOME_PORT]->(l)
            """
            session.run(query, items=ships_with_port)

        print(f"  Created {len(aircraft_with_base) + len(ships_with_port)} location relationships")

    def load_activity_relationships(self, data_dir: str):
        """Create relationships from activities (SEEN_WITH, VISITED, etc.)"""
        print("\nCreating activity-based relationships...")

        with open(f'{data_dir}/relationships.json') as f:
            rels = json.load(f)

        # Filter to relationship types we want in Neo4j
        graph_rels = [r for r in rels if r['relationship_type'] in ['SEEN_WITH', 'VISITED', 'REFUELED_BY']]

        with self.driver.session() as session:
            # SEEN_WITH (Aircraft <-> Aircraft)
            seen_with = [r for r in graph_rels if r['relationship_type'] == 'SEEN_WITH']
            if seen_with:
                query = """
                    UNWIND $rels AS rel
                    MATCH (a1:Aircraft {id: rel.source_id})
                    MATCH (a2:Aircraft {id: rel.target_id})
                    CREATE (a1)-[:SEEN_WITH {
                        occurrence_count: rel.properties.occurrence_count,
                        first_seen: datetime(rel.properties.first_seen),
                        last_seen: datetime(rel.properties.last_seen),
                        ground_truth: rel.properties.ground_truth,
                        confidence: rel.confidence
                    }]->(a2)
                """
                session.run(query, rels=seen_with)
                print(f"    Created {len(seen_with)} SEEN_WITH relationships")

            # VISITED (Ship -> Location)
            visited = [r for r in graph_rels if r['relationship_type'] == 'VISITED']
            if visited:
                # Load in batches
                batch_size = 1000
                for i in range(0, len(visited), batch_size):
                    batch = visited[i:i+batch_size]
                    query = """
                        UNWIND $rels AS rel
                        MATCH (s:Ship {id: rel.source_id})
                        MATCH (l:Location {id: rel.target_id})
                        CREATE (s)-[:VISITED {
                            timestamp: datetime(rel.properties.timestamp),
                            duration_hours: rel.properties.duration_hours,
                            purpose: rel.properties.purpose
                        }]->(l)
                    """
                    session.run(query, rels=batch)
                print(f"    Created {len(visited)} VISITED relationships")

            # REFUELED_BY (Aircraft -> Tanker)
            refueled = [r for r in graph_rels if r['relationship_type'] == 'REFUELED_BY']
            if refueled:
                # Load in batches
                batch_size = 1000
                for i in range(0, len(refueled), batch_size):
                    batch = refueled[i:i+batch_size]
                    query = """
                        UNWIND $rels AS rel
                        MATCH (receiver:Aircraft {id: rel.source_id})
                        MATCH (tanker:Aircraft {id: rel.target_id})
                        CREATE (receiver)-[:REFUELED_BY {
                            refuel_count: rel.properties.refuel_count,
                            total_fuel_transferred: rel.properties.total_fuel_transferred,
                            first_refuel: datetime(rel.properties.first_refuel),
                            last_refuel: datetime(rel.properties.last_refuel)
                        }]->(tanker)
                    """
                    session.run(query, rels=batch)
                print(f"    Created {len(refueled)} REFUELED_BY relationships")


def main():
    """Load all data into Neo4j"""
    print("="*60)
    print("Neo4j Data Loader")
    print("="*60)

    # Connection parameters (from docker-compose.yml)
    uri = "bolt://localhost:17687"
    user = "neo4j"
    password = "sharkbakeoff"

    data_dir = '../sample'

    print(f"\nConnecting to Neo4j...")
    print(f"  URI: {uri}")

    try:
        loader = Neo4jLoader(uri, user, password)
        print("  ✓ Connected")

        # Optional: clear existing data
        import sys
        if '--clear' in sys.argv:
            loader.clear_database()

        # Create schema
        loader.create_constraints_and_indexes()

        # Load data
        loader.load_organizations(data_dir)
        loader.load_locations(data_dir)
        loader.load_aircraft(data_dir)
        loader.load_ships(data_dir)

        # Create relationships
        loader.load_operational_relationships(data_dir)
        loader.load_location_relationships(data_dir)
        loader.load_activity_relationships(data_dir)

        # Get counts
        with loader.driver.session() as session:
            result = session.run("MATCH (n) RETURN labels(n)[0] AS label, COUNT(n) AS count")
            node_counts = {record['label']: record['count'] for record in result}

            result = session.run("MATCH ()-[r]->() RETURN type(r) AS type, COUNT(r) AS count")
            rel_counts = {record['type']: record['count'] for record in result}

        print("\n" + "="*60)
        print("LOAD COMPLETE")
        print("="*60)
        print("\nNodes:")
        for label, count in sorted(node_counts.items(), key=lambda x: -x[1]):
            print(f"  {label}: {count:,}")

        print("\nRelationships:")
        for rtype, count in sorted(rel_counts.items(), key=lambda x: -x[1]):
            print(f"  {rtype}: {count:,}")

        total_nodes = sum(node_counts.values())
        total_rels = sum(rel_counts.values())
        print(f"\nTOTAL: {total_nodes:,} nodes, {total_rels:,} relationships")

        loader.close()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
