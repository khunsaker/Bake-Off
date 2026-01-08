#!/usr/bin/env python3
"""PostgreSQL API - Port 8080"""

from flask import Flask, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='sharkdb',
        user='shark',
        password='sharkbakeoff'
    )

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'database': 'postgresql'})

@app.route('/api/aircraft/mode_s/<mode_s>')
def get_aircraft_mode_s(mode_s):
    """Get aircraft by mode_s identifier"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT mode_s, shark_name, platform, affiliation, nationality
        FROM aircraft WHERE mode_s = %s
    """, (mode_s,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return jsonify(dict(result))
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/ships/mmsi/<mmsi>')
def get_ship_mmsi(mmsi):
    """Get ship by MMSI identifier"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT mmsi, shark_name, vessel_type, affiliation, nationality
        FROM ships WHERE mmsi = %s
    """, (mmsi,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return jsonify(dict(result))
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/aircraft/country/<country>')
def get_aircraft_by_country(country):
    """Get aircraft by country (two-hop traversal simulation)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.mode_s, a.shark_name, a.platform, a.affiliation, a.nationality,
               COUNT(r.id) as relationship_count
        FROM aircraft a
        LEFT JOIN relationships r ON r.entity1_id = a.id OR r.entity2_id = a.id
        WHERE a.nationality = %s
        GROUP BY a.id, a.mode_s, a.shark_name, a.platform, a.affiliation, a.nationality
        LIMIT 100
    """, (country,))
    results = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([dict(r) for r in results])

@app.route('/api/log', methods=['POST'])
def log_activity():
    """Log activity (write operation)"""
    return jsonify({'status': 'logged'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
