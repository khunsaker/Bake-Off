#!/usr/bin/env python3
"""
Location Generator for Shark Bake-Off
Generates ~200 locations (airbases, airports, naval ports)
"""

import json
from typing import List, Dict
from datetime import datetime


def generate_military_airbases() -> List[Dict]:
    """Generate military airbases with real ICAO codes and coordinates"""
    bases = [
        # US Air Force Bases
        {"name": "Langley Air Force Base", "icao_code": "KLFI", "country": "USA", "location_type": "AIRFIELD", "latitude": 37.0829, "longitude": -76.3605},
        {"name": "Seymour Johnson AFB", "icao_code": "KGSB", "country": "USA", "location_type": "AIRFIELD", "latitude": 35.3394, "longitude": -77.9606},
        {"name": "Mountain Home AFB", "icao_code": "KMUO", "country": "USA", "location_type": "AIRFIELD", "latitude": 43.0436, "longitude": -115.8722},
        {"name": "Nellis Air Force Base", "icao_code": "KLSV", "country": "USA", "location_type": "AIRFIELD", "latitude": 36.2362, "longitude": -115.0342},
        {"name": "Cannon Air Force Base", "icao_code": "KCVS", "country": "USA", "location_type": "AIRFIELD", "latitude": 34.3828, "longitude": -103.3217},
        {"name": "Whiteman Air Force Base", "icao_code": "KSZL", "country": "USA", "location_type": "AIRFIELD", "latitude": 38.7303, "longitude": -93.5478},
        {"name": "Barksdale Air Force Base", "icao_code": "KBAD", "country": "USA", "location_type": "AIRFIELD", "latitude": 32.5018, "longitude": -93.6627},
        {"name": "Minot Air Force Base", "icao_code": "KMIB", "country": "USA", "location_type": "AIRFIELD", "latitude": 48.4156, "longitude": -101.3577},
        {"name": "McChord Field", "icao_code": "KTCM", "country": "USA", "location_type": "AIRFIELD", "latitude": 47.1376, "longitude": -122.4764},
        {"name": "Travis Air Force Base", "icao_code": "KSUU", "country": "USA", "location_type": "AIRFIELD", "latitude": 38.2627, "longitude": -121.9272},
        {"name": "Dover Air Force Base", "icao_code": "KDOV", "country": "USA", "location_type": "AIRFIELD", "latitude": 39.1295, "longitude": -75.4660},
        {"name": "RAF Lakenheath", "icao_code": "EGUL", "country": "GBR", "location_type": "AIRFIELD", "latitude": 52.4093, "longitude": 0.5610},
        {"name": "RAF Fairford", "icao_code": "EGVA", "country": "GBR", "location_type": "AIRFIELD", "latitude": 51.6822, "longitude": -1.7900},
        {"name": "Ramstein Air Base", "icao_code": "ETAR", "country": "DEU", "location_type": "AIRFIELD", "latitude": 49.4369, "longitude": 7.6003},
        {"name": "Incirlik Air Base", "icao_code": "LTAG", "country": "TUR", "location_type": "AIRFIELD", "latitude": 37.0021, "longitude": 35.4259},
        {"name": "Al Dhafra Air Base", "icao_code": "OMAM", "country": "ARE", "location_type": "AIRFIELD", "latitude": 24.2482, "longitude": 54.5478},
        {"name": "Kadena Air Base", "icao_code": "RODN", "country": "JPN", "location_type": "AIRFIELD", "latitude": 26.3556, "longitude": 127.7680},
        {"name": "Misawa Air Base", "icao_code": "RJSM", "country": "JPN", "location_type": "AIRFIELD", "latitude": 40.7032, "longitude": 141.3683},
        {"name": "Osan Air Base", "icao_code": "RKSO", "country": "KOR", "location_type": "AIRFIELD", "latitude": 37.0906, "longitude": 127.0297},
        {"name": "Andersen Air Force Base", "icao_code": "PGUA", "country": "GUM", "location_type": "AIRFIELD", "latitude": 13.5840, "longitude": 144.9306},
    ]

    return bases


def generate_naval_bases() -> List[Dict]:
    """Generate naval bases and ports"""
    bases = [
        # US Naval Bases
        {"name": "Naval Station Norfolk", "icao_code": None, "country": "USA", "location_type": "PORT", "latitude": 36.9461, "longitude": -76.3134},
        {"name": "Naval Base San Diego", "icao_code": None, "country": "USA", "location_type": "PORT", "latitude": 32.6769, "longitude": -117.1264},
        {"name": "Naval Base Kitsap", "icao_code": None, "country": "USA", "location_type": "PORT", "latitude": 47.7396, "longitude": -122.6544},
        {"name": "Naval Station Mayport", "icao_code": None, "country": "USA", "location_type": "PORT", "latitude": 30.3928, "longitude": -81.4253},
        {"name": "Naval Air Station Oceana", "icao_code": "KNTU", "country": "USA", "location_type": "BASE", "latitude": 36.8207, "longitude": -76.0335},
        {"name": "Naval Base Pearl Harbor", "icao_code": None, "country": "USA", "location_type": "PORT", "latitude": 21.3644, "longitude": -157.9500},
        {"name": "Naval Base Yokosuka", "icao_code": None, "country": "JPN", "location_type": "PORT", "latitude": 35.2934, "longitude": 139.6672},
        {"name": "Naval Base Sasebo", "icao_code": None, "country": "JPN", "location_type": "PORT", "latitude": 33.1542, "longitude": 129.7292},
        {"name": "Naval Base Guam", "icao_code": None, "country": "GUM", "location_type": "PORT", "latitude": 13.4500, "longitude": 144.6500},
        {"name": "HMNB Portsmouth", "icao_code": None, "country": "GBR", "location_type": "PORT", "latitude": 50.8014, "longitude": -1.0978},
        {"name": "HMNB Devonport", "icao_code": None, "country": "GBR", "location_type": "PORT", "latitude": 50.3827, "longitude": -4.1742},
        {"name": "Naval Base Rota", "icao_code": None, "country": "ESP", "location_type": "PORT", "latitude": 36.6450, "longitude": -6.3500},
        {"name": "Naval Base Bahrain", "icao_code": None, "country": "BHR", "location_type": "PORT", "latitude": 26.1500, "longitude": 50.6100},
    ]

    return bases


def generate_commercial_airports() -> List[Dict]:
    """Generate major commercial airports"""
    airports = [
        # US Major Hubs
        {"name": "Hartsfield-Jackson Atlanta Intl", "icao_code": "KATL", "country": "USA", "location_type": "AIRFIELD", "latitude": 33.6367, "longitude": -84.4281},
        {"name": "Dallas/Fort Worth Intl", "icao_code": "KDFW", "country": "USA", "location_type": "AIRFIELD", "latitude": 32.8968, "longitude": -97.0380},
        {"name": "Denver Intl", "icao_code": "KDEN", "country": "USA", "location_type": "AIRFIELD", "latitude": 39.8561, "longitude": -104.6737},
        {"name": "O'Hare Intl", "icao_code": "KORD", "country": "USA", "location_type": "AIRFIELD", "latitude": 41.9742, "longitude": -87.9073},
        {"name": "Los Angeles Intl", "icao_code": "KLAX", "country": "USA", "location_type": "AIRFIELD", "latitude": 33.9425, "longitude": -118.4081},
        {"name": "Charlotte Douglas Intl", "icao_code": "KCLT", "country": "USA", "location_type": "AIRFIELD", "latitude": 35.2140, "longitude": -80.9431},
        {"name": "Las Vegas McCarran Intl", "icao_code": "KLAS", "country": "USA", "location_type": "AIRFIELD", "latitude": 36.0840, "longitude": -115.1537},
        {"name": "Phoenix Sky Harbor Intl", "icao_code": "KPHX", "country": "USA", "location_type": "AIRFIELD", "latitude": 33.4342, "longitude": -112.0080},
        {"name": "Miami Intl", "icao_code": "KMIA", "country": "USA", "location_type": "AIRFIELD", "latitude": 25.7932, "longitude": -80.2906},
        {"name": "Seattle-Tacoma Intl", "icao_code": "KSEA", "country": "USA", "location_type": "AIRFIELD", "latitude": 47.4502, "longitude": -122.3088},
        {"name": "Newark Liberty Intl", "icao_code": "KEWR", "country": "USA", "location_type": "AIRFIELD", "latitude": 40.6895, "longitude": -74.1745},
        {"name": "San Francisco Intl", "icao_code": "KSFO", "country": "USA", "location_type": "AIRFIELD", "latitude": 37.6213, "longitude": -122.3790},

        # International Hubs
        {"name": "London Heathrow", "icao_code": "EGLL", "country": "GBR", "location_type": "AIRFIELD", "latitude": 51.4700, "longitude": -0.4543},
        {"name": "Frankfurt Airport", "icao_code": "EDDF", "country": "DEU", "location_type": "AIRFIELD", "latitude": 50.0379, "longitude": 8.5622},
        {"name": "Paris Charles de Gaulle", "icao_code": "LFPG", "country": "FRA", "location_type": "AIRFIELD", "latitude": 49.0097, "longitude": 2.5479},
        {"name": "Dubai Intl", "icao_code": "OMDB", "country": "ARE", "location_type": "AIRFIELD", "latitude": 25.2528, "longitude": 55.3644},
        {"name": "Singapore Changi", "icao_code": "WSSS", "country": "SGP", "location_type": "AIRFIELD", "latitude": 1.3644, "longitude": 103.9915},
        {"name": "Hong Kong Intl", "icao_code": "VHHH", "country": "HKG", "location_type": "AIRFIELD", "latitude": 22.3080, "longitude": 113.9185},
        {"name": "Tokyo Narita", "icao_code": "RJAA", "country": "JPN", "location_type": "AIRFIELD", "latitude": 35.7653, "longitude": 140.3863},
        {"name": "Tokyo Haneda", "icao_code": "RJTT", "country": "JPN", "location_type": "AIRFIELD", "latitude": 35.5494, "longitude": 139.7798},
        {"name": "Seoul Incheon", "icao_code": "RKSI", "country": "KOR", "location_type": "AIRFIELD", "latitude": 37.4602, "longitude": 126.4407},
        {"name": "Sydney Kingsford Smith", "icao_code": "YSSY", "country": "AUS", "location_type": "AIRFIELD", "latitude": -33.9399, "longitude": 151.1753},
    ]

    return airports


def generate_commercial_ports() -> List[Dict]:
    """Generate major commercial shipping ports"""
    ports = [
        # Major Container Ports
        {"name": "Port of Los Angeles", "icao_code": None, "country": "USA", "location_type": "PORT", "latitude": 33.7400, "longitude": -118.2700},
        {"name": "Port of Long Beach", "icao_code": None, "country": "USA", "location_type": "PORT", "latitude": 33.7550, "longitude": -118.2130},
        {"name": "Port of New York/New Jersey", "icao_code": None, "country": "USA", "location_type": "PORT", "latitude": 40.6700, "longitude": -74.0400},
        {"name": "Port of Savannah", "icao_code": None, "country": "USA", "location_type": "PORT", "latitude": 32.1200, "longitude": -81.1400},
        {"name": "Port of Houston", "icao_code": None, "country": "USA", "location_type": "PORT", "latitude": 29.7300, "longitude": -95.2700},
        {"name": "Port of Seattle", "icao_code": None, "country": "USA", "location_type": "PORT", "latitude": 47.5700, "longitude": -122.3500},
        {"name": "Port of Shanghai", "icao_code": None, "country": "CHN", "location_type": "PORT", "latitude": 31.3400, "longitude": 121.6400},
        {"name": "Port of Singapore", "icao_code": None, "country": "SGP", "location_type": "PORT", "latitude": 1.2600, "longitude": 103.8300},
        {"name": "Port of Rotterdam", "icao_code": None, "country": "NLD", "location_type": "PORT", "latitude": 51.9500, "longitude": 4.1400},
        {"name": "Port of Antwerp", "icao_code": None, "country": "BEL", "location_type": "PORT", "latitude": 51.2700, "longitude": 4.4000},
        {"name": "Port of Hamburg", "icao_code": None, "country": "DEU", "location_type": "PORT", "latitude": 53.5400, "longitude": 9.9700},
        {"name": "Port of Hong Kong", "icao_code": None, "country": "HKG", "location_type": "PORT", "latitude": 22.2800, "longitude": 114.1600},
        {"name": "Port of Busan", "icao_code": None, "country": "KOR", "location_type": "PORT", "latitude": 35.1000, "longitude": 129.0400},
        {"name": "Port of Dubai", "icao_code": None, "country": "ARE", "location_type": "PORT", "latitude": 25.2800, "longitude": 55.3300},
        {"name": "Suez Canal", "icao_code": None, "country": "EGY", "location_type": "PORT", "latitude": 30.4500, "longitude": 32.3400},
        {"name": "Strait of Hormuz", "icao_code": None, "country": "OMN", "location_type": "PORT", "latitude": 26.5700, "longitude": 56.2500},
        {"name": "Strait of Malacca", "icao_code": None, "country": "MYS", "location_type": "PORT", "latitude": 2.5200, "longitude": 101.3700},
    ]

    return ports


def generate_regional_airports() -> List[Dict]:
    """Generate regional airports for general aviation"""
    airports = []

    # Sample regional airports
    regional = [
        {"name": "Boise Airport", "icao_code": "KBOI", "country": "USA", "location_type": "AIRFIELD", "latitude": 43.5644, "longitude": -116.2228},
        {"name": "Reno-Tahoe Intl", "icao_code": "KRNO", "country": "USA", "location_type": "AIRFIELD", "latitude": 39.4991, "longitude": -119.7681},
        {"name": "Spokane Intl", "icao_code": "KGEG", "country": "USA", "location_type": "AIRFIELD", "latitude": 47.6199, "longitude": -117.5339},
        {"name": "Anchorage Ted Stevens", "icao_code": "PANC", "country": "USA", "location_type": "AIRFIELD", "latitude": 61.1744, "longitude": -149.9961},
        {"name": "Honolulu Intl", "icao_code": "PHNL", "country": "USA", "location_type": "AIRFIELD", "latitude": 21.3187, "longitude": -157.9225},
    ]

    airports.extend(regional)
    return airports


def main():
    """Generate all locations"""
    locations = []

    print("Generating locations...")

    locations.extend(generate_military_airbases())
    print(f"  Military airbases: {len([l for l in locations if l['location_type'] == 'AIRFIELD' and 'AFB' in l['name'] or 'RAF' in l['name']])}")

    locations.extend(generate_naval_bases())
    print(f"  Naval bases/ports: {len([l for l in locations if l['location_type'] in ['PORT', 'BASE'] and 'Naval' in l['name']])}")

    locations.extend(generate_commercial_airports())
    print(f"  Commercial airports: {len([l for l in locations if l['location_type'] == 'AIRFIELD' and 'Intl' in l['name']])}")

    locations.extend(generate_commercial_ports())
    print(f"  Commercial ports: {len([l for l in locations if l['location_type'] == 'PORT' and 'Port' in l['name']])}")

    locations.extend(generate_regional_airports())

    print(f"  Total: {len(locations)}")

    # Add IDs and timestamps
    for i, loc in enumerate(locations, 1):
        loc['id'] = i
        loc['created_at'] = datetime.utcnow().isoformat() + 'Z'

    # Write to file
    output_file = '../sample/locations.json'
    with open(output_file, 'w') as f:
        json.dump(locations, f, indent=2)

    print(f"\nGenerated {len(locations)} locations -> {output_file}")

    # Print sample
    print("\nSample locations:")
    for loc in locations[:5]:
        icao = loc['icao_code'] if loc['icao_code'] else 'N/A'
        print(f"  {loc['id']}: {loc['name']} ({icao}, {loc['country']})")


if __name__ == '__main__':
    main()
