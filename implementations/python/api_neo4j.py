#!/usr/bin/env python3
"""Neo4j API - Port 8081"""

from flask import Flask, jsonify
from neo4j import GraphDatabase

app = Flask(__name__)

def get_driver():
    return GraphDatabase.driver(
        "bolt://localhost:17687",
        auth=("neo4j", "sharkbakeoff")
    )

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'database': 'neo4j'})

@app.route('/api/aircraft/mode_s/<mode_s>')
def get_aircraft_mode_s(mode_s):
    """Get aircraft by mode_s identifier"""
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (a:Aircraft {mode_s: $mode_s})
            RETURN a.mode_s as mode_s, a.shark_name as shark_name,
                   a.platform as platform, a.affiliation as affiliation,
                   a.nationality as nationality
        """, mode_s=mode_s)

        record = result.single()
        if record:
            return jsonify(dict(record))

    return jsonify({'error': 'Not found'}), 404

@app.route('/api/ships/mmsi/<mmsi>')
def get_ship_mmsi(mmsi):
    """Get ship by MMSI identifier"""
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Ship {mmsi: $mmsi})
            RETURN s.mmsi as mmsi, s.shark_name as shark_name,
                   s.vessel_type as vessel_type, s.affiliation as affiliation,
                   s.nationality as nationality
        """, mmsi=mmsi)

        record = result.single()
        if record:
            return jsonify(dict(record))

    return jsonify({'error': 'Not found'}), 404

@app.route('/api/aircraft/country/<country>')
def get_aircraft_by_country(country):
    """Get aircraft by country (two-hop traversal)"""
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (a:Aircraft {nationality: $country})
            OPTIONAL MATCH (a)-[r]-()
            RETURN a.mode_s as mode_s, a.shark_name as shark_name,
                   a.platform as platform, a.affiliation as affiliation,
                   a.nationality as nationality,
                   count(r) as relationship_count
            LIMIT 100
        """, country=country)

        records = [dict(record) for record in result]
        return jsonify(records)

@app.route('/api/log', methods=['POST'])
def log_activity():
    """Log activity (write operation)"""
    return jsonify({'status': 'logged'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=False)
