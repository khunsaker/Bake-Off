#!/usr/bin/env python3
"""
PostgreSQL Data Loader for Shark Bake-Off
Loads generated JSON data into PostgreSQL database
"""

import json
import psycopg2
from psycopg2.extras import execute_batch
import sys
from datetime import datetime


def load_organizations(conn, data_dir: str):
    """Load organizations table"""
    print("\nLoading organizations...")

    with open(f'{data_dir}/organizations.json') as f:
        orgs = json.load(f)

    cur = conn.cursor()

    # Get parent_org_id by looking up parent name
    org_id_map = {o['name']: o['id'] for o in orgs}

    insert_sql = """
        INSERT INTO organizations (id, name, org_type, country, parent_org_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """

    rows = []
    for org in orgs:
        parent_id = org_id_map.get(org['parent']) if org['parent'] else None
        rows.append((
            org['id'],
            org['name'],
            org['org_type'],
            org['country'],
            parent_id,
            org['created_at']
        ))

    execute_batch(cur, insert_sql, rows, page_size=1000)
    conn.commit()

    print(f"  Loaded {len(rows)} organizations")


def load_locations(conn, data_dir: str):
    """Load locations table"""
    print("\nLoading locations...")

    with open(f'{data_dir}/locations.json') as f:
        locs = json.load(f)

    cur = conn.cursor()

    insert_sql = """
        INSERT INTO locations (id, name, location_type, icao_code, country, latitude, longitude, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """

    rows = []
    for loc in locs:
        rows.append((
            loc['id'],
            loc['name'],
            loc['location_type'],
            loc.get('icao_code'),
            loc['country'],
            loc['latitude'],
            loc['longitude'],
            loc['created_at']
        ))

    execute_batch(cur, insert_sql, rows, page_size=1000)
    conn.commit()

    print(f"  Loaded {len(rows)} locations")


def load_aircraft(conn, data_dir: str):
    """Load aircraft into air_instance_lookup"""
    print("\nLoading aircraft instances...")

    with open(f'{data_dir}/aircraft_instances.json') as f:
        aircraft = json.load(f)

    cur = conn.cursor()

    insert_sql = """
        INSERT INTO air_instance_lookup (
            id, mode_s, tail_number, icao_type_code, shark_name, platform,
            affiliation, nationality, operator,
            air_type, air_model, air_role,
            max_altitude_ft, min_altitude_ft, max_speed_kts, min_speed_kts,
            typical_cruise_altitude_ft, typical_cruise_speed_kts,
            neo4j_node_id, created_at, updated_at,
            source, source_timestamp, curator_modified, curator_id, curator_locked
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (id) DO NOTHING
    """

    rows = []
    for ac in aircraft:
        rows.append((
            ac['id'],
            ac['mode_s'],
            ac['tail_number'],
            ac['icao_type_code'],
            ac['shark_name'],
            ac['platform'],
            ac['affiliation'],
            ac['nationality'],
            ac['operator'],
            ac['air_type'],
            ac['air_model'],
            ac['air_role'],
            ac.get('max_altitude_ft'),
            ac.get('min_altitude_ft'),
            ac.get('max_speed_kts'),
            ac.get('min_speed_kts'),
            ac.get('typical_cruise_altitude_ft'),
            ac.get('typical_cruise_speed_kts'),
            None,  # neo4j_node_id (will be populated after Neo4j load)
            ac['created_at'],
            ac['updated_at'],
            ac.get('source'),
            ac.get('source_timestamp'),
            ac.get('curator_modified', False),
            ac.get('curator_id'),
            ac.get('curator_locked', False)
        ))

    execute_batch(cur, insert_sql, rows, page_size=1000)
    conn.commit()

    print(f"  Loaded {len(rows)} aircraft")


def load_ships(conn, data_dir: str):
    """Load ships into ship_instance_lookup"""
    print("\nLoading ship instances...")

    with open(f'{data_dir}/ship_instances.json') as f:
        ships = json.load(f)

    cur = conn.cursor()

    insert_sql = """
        INSERT INTO ship_instance_lookup (
            id, mmsi, sconum, imo_number, call_sign, shark_name, platform,
            affiliation, nationality, operator,
            ship_type, ship_class, ship_role,
            length_meters, beam_meters, draft_meters, displacement_tons,
            max_speed_kts, typical_speed_kts,
            neo4j_node_id, created_at, updated_at,
            source, source_timestamp, curator_modified, curator_id, curator_locked
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (id) DO NOTHING
    """

    rows = []
    for ship in ships:
        rows.append((
            ship['id'],
            ship['mmsi'],
            ship.get('sconum'),
            ship.get('imo_number'),
            ship['call_sign'],
            ship['shark_name'],
            ship['platform'],
            ship['affiliation'],
            ship['nationality'],
            ship['operator'],
            ship['ship_type'],
            ship['ship_class'],
            ship['ship_role'],
            ship.get('length_meters'),
            ship.get('beam_meters'),
            ship.get('draft_meters'),
            ship.get('displacement_tons'),
            ship.get('max_speed_kts'),
            ship.get('typical_speed_kts'),
            None,  # neo4j_node_id
            ship['created_at'],
            ship['updated_at'],
            ship.get('source'),
            ship.get('source_timestamp'),
            ship.get('curator_modified', False),
            ship.get('curator_id'),
            ship.get('curator_locked', False)
        ))

    execute_batch(cur, insert_sql, rows, page_size=1000)
    conn.commit()

    print(f"  Loaded {len(rows)} ships")


def load_activities(conn, data_dir: str):
    """Load activities into track_activity_log"""
    print("\nLoading activity log...")

    with open(f'{data_dir}/activity_log.json') as f:
        activities = json.load(f)

    cur = conn.cursor()

    insert_sql = """
        INSERT INTO track_activity_log (
            track_id, domain, event_type, activity_type,
            kb_object_id, mode_s, mmsi,
            event_timestamp, latitude, longitude,
            properties, associated_track_ids, associated_kb_ids
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """

    rows = []
    for activity in activities:
        rows.append((
            activity['track_id'],
            activity['domain'],
            activity['event_type'],
            activity.get('activity_type'),
            activity.get('kb_object_id'),
            activity.get('mode_s'),
            activity.get('mmsi'),
            activity['event_timestamp'],
            activity.get('latitude'),
            activity.get('longitude'),
            json.dumps(activity.get('properties', {})),
            activity.get('associated_track_ids', []),
            activity.get('associated_kb_ids', [])
        ))

    execute_batch(cur, insert_sql, rows, page_size=1000)
    conn.commit()

    print(f"  Loaded {len(rows)} activities")


def load_relationships(conn, data_dir: str):
    """Load relationships into kb_relationships"""
    print("\nLoading relationships...")

    with open(f'{data_dir}/relationships.json') as f:
        rels = json.load(f)

    cur = conn.cursor()

    insert_sql = """
        INSERT INTO kb_relationships (
            id, source_domain, source_id, target_domain, target_id,
            relationship_type, properties,
            valid_from, valid_to, created_at, source, confidence
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """

    rows = []
    for rel in rels:
        rows.append((
            rel['id'],
            rel['source_domain'],
            rel['source_id'],
            rel['target_domain'],
            rel['target_id'],
            rel['relationship_type'],
            json.dumps(rel.get('properties', {})),
            rel.get('valid_from'),
            rel.get('valid_to'),
            rel['created_at'],
            rel.get('source'),
            rel.get('confidence')
        ))

    execute_batch(cur, insert_sql, rows, page_size=1000)
    conn.commit()

    print(f"  Loaded {len(rows)} relationships")


def main():
    """Load all data into PostgreSQL"""
    print("="*60)
    print("PostgreSQL Data Loader")
    print("="*60)

    # Connection parameters (from docker-compose.yml)
    conn_params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'sharkdb',
        'user': 'shark',
        'password': 'sharkbakeoff'
    }

    data_dir = '../sample'

    print("\nConnecting to PostgreSQL...")
    print(f"  Host: {conn_params['host']}:{conn_params['port']}")
    print(f"  Database: {conn_params['database']}")

    try:
        conn = psycopg2.connect(**conn_params)
        print("  ✓ Connected")

        # Load data in dependency order
        load_organizations(conn, data_dir)
        load_locations(conn, data_dir)
        load_aircraft(conn, data_dir)
        load_ships(conn, data_dir)
        load_activities(conn, data_dir)
        load_relationships(conn, data_dir)

        # Get counts
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM organizations")
        org_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM locations")
        loc_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM air_instance_lookup")
        air_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM ship_instance_lookup")
        ship_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM track_activity_log")
        activity_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM kb_relationships")
        rel_count = cur.fetchone()[0]

        print("\n" + "="*60)
        print("LOAD COMPLETE")
        print("="*60)
        print(f"\nDatabase: {conn_params['database']}")
        print(f"  Organizations: {org_count:,}")
        print(f"  Locations: {loc_count:,}")
        print(f"  Aircraft: {air_count:,}")
        print(f"  Ships: {ship_count:,}")
        print(f"  Activities: {activity_count:,}")
        print(f"  Relationships: {rel_count:,}")
        print(f"  TOTAL RECORDS: {org_count + loc_count + air_count + ship_count + activity_count + rel_count:,}")

        conn.close()

    except psycopg2.Error as e:
        print(f"\n✗ Database error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n✗ File not found: {e}")
        print("\nPlease run data generators first:")
        print("  cd ../generators")
        print("  python3 generate_organizations.py")
        print("  python3 generate_locations.py")
        print("  python3 generate_aircraft_instances.py")
        print("  python3 generate_ship_instances.py")
        print("  python3 generate_activity_log.py")
        print("  python3 generate_relationships.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
