#!/usr/bin/env python3
"""
Simple Python API for quick testing
Shark Bake-Off - Demonstration
"""

from flask import Flask, jsonify
import psycopg2
from neo4j import GraphDatabase
import os

app = Flask(__name__)

# Database connections
def get_postgres_conn():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="sharkdb",
        user="shark",
        password="sharkbakeoff"
    )

def get_neo4j_driver():
    return GraphDatabase.driver(
        "bolt://localhost:17687",
        auth=("neo4j", "sharkbakeoff")
    )

def get_memgraph_driver():
    return GraphDatabase.driver(
        "bolt://localhost:7689",
        auth=None
    )

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "shark-api-python"})

@app.route('/api/aircraft/mode_s/<mode_s>')
def get_aircraft_postgres(mode_s):
    """Get aircraft by mode_s from PostgreSQL"""
    conn = get_postgres_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT mode_s, shark_name, platform, affiliation, nationality
        FROM air_instance_lookup
        WHERE mode_s = %s
    """, (mode_s,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return jsonify({
            "mode_s": row[0],
            "shark_name": row[1],
            "platform": row[2],
            "affiliation": row[3],
            "nationality": row[4]
        })
    return jsonify({"error": "not found"}), 404

@app.route('/api/aircraft/neo4j/mode_s/<mode_s>')
def get_aircraft_neo4j(mode_s):
    """Get aircraft by mode_s from Neo4j"""
    driver = get_neo4j_driver()

    with driver.session() as session:
        result = session.run("""
            MATCH (a:Aircraft {mode_s: $mode_s})
            RETURN a.mode_s as mode_s, a.shark_name as shark_name,
                   a.platform as platform, a.affiliation as affiliation,
                   a.nationality as nationality
        """, mode_s=mode_s)

        record = result.single()
        if record:
            return jsonify({
                "mode_s": record["mode_s"],
                "shark_name": record["shark_name"],
                "platform": record["platform"],
                "affiliation": record["affiliation"],
                "nationality": record["nationality"]
            })

    driver.close()
    return jsonify({"error": "not found"}), 404

@app.route('/api/aircraft/memgraph/mode_s/<mode_s>')
def get_aircraft_memgraph(mode_s):
    """Get aircraft by mode_s from Memgraph"""
    driver = get_memgraph_driver()

    with driver.session() as session:
        result = session.run("""
            MATCH (a:Aircraft {mode_s: $mode_s})
            RETURN a.mode_s as mode_s, a.shark_name as shark_name,
                   a.platform as platform, a.affiliation as affiliation,
                   a.nationality as nationality
        """, mode_s=mode_s)

        record = result.single()
        if record:
            return jsonify({
                "mode_s": record["mode_s"],
                "shark_name": record["shark_name"],
                "platform": record["platform"],
                "affiliation": record["affiliation"],
                "nationality": record["nationality"]
            })

    driver.close()
    return jsonify({"error": "not found"}), 404

@app.route('/api/ship/mmsi/<mmsi>')
def get_ship_postgres(mmsi):
    """Get ship by MMSI from PostgreSQL"""
    conn = get_postgres_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT mmsi, shark_name, platform, affiliation, nationality
        FROM ship_instance_lookup
        WHERE mmsi = %s
    """, (mmsi,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return jsonify({
            "mmsi": row[0],
            "shark_name": row[1],
            "platform": row[2],
            "affiliation": row[3],
            "nationality": row[4]
        })
    return jsonify({"error": "not found"}), 404

@app.route('/api/ship/neo4j/mmsi/<mmsi>')
def get_ship_neo4j(mmsi):
    """Get ship by MMSI from Neo4j"""
    driver = get_neo4j_driver()

    with driver.session() as session:
        result = session.run("""
            MATCH (s:Ship {mmsi: $mmsi})
            RETURN s.mmsi as mmsi, s.shark_name as shark_name,
                   s.platform as platform, s.affiliation as affiliation,
                   s.nationality as nationality
        """, mmsi=mmsi)

        record = result.single()
        if record:
            return jsonify({
                "mmsi": record["mmsi"],
                "shark_name": record["shark_name"],
                "platform": record["platform"],
                "affiliation": record["affiliation"],
                "nationality": record["nationality"]
            })

    driver.close()
    return jsonify({"error": "not found"}), 404

@app.route('/api/ship/memgraph/mmsi/<mmsi>')
def get_ship_memgraph(mmsi):
    """Get ship by MMSI from Memgraph"""
    driver = get_memgraph_driver()

    with driver.session() as session:
        result = session.run("""
            MATCH (s:Ship {mmsi: $mmsi})
            RETURN s.mmsi as mmsi, s.shark_name as shark_name,
                   s.platform as platform, s.affiliation as affiliation,
                   s.nationality as nationality
        """, mmsi=mmsi)

        record = result.single()
        if record:
            return jsonify({
                "mmsi": record["mmsi"],
                "shark_name": record["shark_name"],
                "platform": record["platform"],
                "affiliation": record["affiliation"],
                "nationality": record["nationality"]
            })

    driver.close()
    return jsonify({"error": "not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
