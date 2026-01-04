#!/usr/bin/env python3
"""
Ship Instance Generator for Shark Bake-Off
Generates ~492 ship instances with fictional identifiers
"""

import json
import random
from typing import List, Dict, Set
from datetime import datetime, timedelta


def generate_mmsi(country: str, used_mmsi: Set[str]) -> str:
    """Generate unique MMSI (9-digit Maritime Mobile Service Identity)"""
    # MMSI format: MID (Maritime Identification Digits) + ship number
    # MID codes: USA=366-369, GBR=232-235, JPN=431-440, etc.

    mid_ranges = {
        'USA': (366, 369),
        'GBR': (232, 235),
        'FRA': (226, 228),
        'DEU': (211, 218),
        'JPN': (431, 440),
        'CHN': (412, 414),
        'KOR': (440, 441),
        'AUS': (503, 503),
        'NLD': (244, 246),
        'BEL': (205, 206),
        'NOR': (257, 259),
        'DNK': (219, 220),
        'SGP': (563, 566),
        'HKG': (477, 477),
        'GRC': (237, 241),
        'ITA': (247, 247),
        'ESP': (224, 225),
    }

    while True:
        if country in mid_ranges:
            mid_start, mid_end = mid_ranges[country]
            mid = random.randint(mid_start, mid_end)
        else:
            # Default: use 999 for unknown
            mid = 999

        # Ship number: 6 digits
        ship_num = random.randint(100000, 999999)
        mmsi = f"{mid}{ship_num:06d}"

        if mmsi not in used_mmsi:
            used_mmsi.add(mmsi)
            return mmsi


def generate_sconum(ship_class: str, index: int) -> str:
    """Generate Ship Control Number for military vessels"""
    # Format: Class abbreviation + hull number
    # E.g., CVN-68, DDG-51, SSN-774

    class_prefixes = {
        'Nimitz': 'CVN',
        'Gerald R. Ford': 'CVN',
        'Arleigh Burke': 'DDG',
        'Ticonderoga': 'CG',
        'Virginia': 'SSN',
        'Ohio': 'SSBN',
        'Freedom': 'LCS',
        'Independence': 'LCS',
        'America': 'LHA',
        'Wasp': 'LHD',
        'Type 45': 'D',
        'Type 26': 'F',
        'Legend': 'WMSL'
    }

    # Hull number starting points (realistic)
    hull_starts = {
        'CVN': 68,
        'DDG': 51,
        'CG': 47,
        'SSN': 774,
        'SSBN': 726,
        'LCS': 1,
        'LHA': 6,
        'LHD': 1,
        'D': 32,
        'F': 26,
        'WMSL': 750
    }

    prefix = class_prefixes.get(ship_class, 'UNK')
    hull_start = hull_starts.get(prefix, 1)
    hull_number = hull_start + index

    return f"{prefix}-{hull_number}"


def generate_imo_number(used_imo: Set[str]) -> str:
    """Generate IMO ship identification number for commercial vessels"""
    # IMO format: IMO + 7 digits
    while True:
        imo = f"IMO{random.randint(1000000, 9999999)}"
        if imo not in used_imo:
            used_imo.add(imo)
            return imo


def generate_call_sign(country: str, used_callsigns: Set[str]) -> str:
    """Generate radio call sign"""
    # Format varies by country, typically 4-6 characters

    country_prefixes = {
        'USA': ['W', 'K', 'N'],
        'GBR': ['G', 'M'],
        'FRA': ['F'],
        'DEU': ['D'],
        'JPN': ['J'],
        'CHN': ['B'],
        'KOR': ['H'],
        'AUS': ['V'],
    }

    while True:
        if country in country_prefixes:
            prefix = random.choice(country_prefixes[country])
            call = f"{prefix}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"
        else:
            call = f"{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{random.randint(100, 999):03d}"

        if call not in used_callsigns:
            used_callsigns.add(call)
            return call


def assign_operator_ship(platform: Dict, organizations: List[Dict]) -> Dict:
    """Assign appropriate operator based on ship type"""
    category = platform['category']
    affiliation = platform['affiliation']

    if affiliation == 'MILITARY':
        # Military ships to navy/coast guard
        if 'Coast Guard' in category:
            candidates = [o for o in organizations
                         if o['org_type'] == 'MILITARY'
                         and 'Coast Guard' in o['name']]
        else:
            candidates = [o for o in organizations
                         if o['org_type'] == 'MILITARY'
                         and 'Navy' in o['name']]

        if not candidates:
            candidates = [o for o in organizations if o['org_type'] == 'MILITARY']

    else:
        # Commercial ships to shipping companies
        if 'Container' in category:
            candidates = [o for o in organizations
                         if o['org_type'] == 'CIVILIAN'
                         and any(x in o['name'] for x in ['Line', 'Shipping', 'Marine', 'Maritime'])]
        elif 'Tanker' in category:
            candidates = [o for o in organizations
                         if o['org_type'] == 'CIVILIAN'
                         and any(x in o['name'] for x in ['nav', 'Frontline', 'Teekay', 'Holdings', 'Seaways', 'gas'])]
        elif 'Gas Carrier' in category:
            candidates = [o for o in organizations
                         if o['org_type'] == 'CIVILIAN'
                         and any(x in o['name'] for x in ['Gas', 'Qatargas', 'Maran'])]
        elif 'Bulk' in category:
            candidates = [o for o in organizations
                         if o['org_type'] == 'CIVILIAN'
                         and any(x in o['name'] for x in ['Bulk', 'Star', 'Scorpio', 'Seanergy'])]
        elif 'Cruise' in category:
            candidates = [o for o in organizations
                         if o['org_type'] == 'CIVILIAN'
                         and any(x in o['name'] for x in ['Cruise', 'Carnival', 'Royal', 'Norwegian', 'MSC'])]
        else:
            candidates = [o for o in organizations if o['org_type'] == 'CIVILIAN']

    if not candidates:
        candidates = [o for o in organizations if o['org_type'] == 'CIVILIAN']

    return random.choice(candidates)


def assign_home_port(operator: Dict, platform: Dict, locations: List[Dict]) -> Dict:
    """Assign home port based on operator and ship type"""
    country = operator['country']
    affiliation = platform['affiliation']

    if affiliation == 'MILITARY':
        # Military ships to naval bases
        candidates = [l for l in locations
                     if l['location_type'] in ['PORT', 'BASE']
                     and l['country'] == country
                     and 'Naval' in l['name']]

        if not candidates:
            # Fallback to any port in country
            candidates = [l for l in locations
                         if l['location_type'] == 'PORT'
                         and l['country'] == country]

    else:
        # Commercial ships to major ports
        candidates = [l for l in locations
                     if l['location_type'] == 'PORT'
                     and l['country'] == country
                     and 'Port of' in l['name']]

        if not candidates:
            candidates = [l for l in locations
                         if l['location_type'] == 'PORT'
                         and l['country'] == country]

    if not candidates:
        # Final fallback: any port
        candidates = [l for l in locations if l['location_type'] == 'PORT']

    return random.choice(candidates) if candidates else None


def generate_physical_characteristics(platform: Dict) -> Dict:
    """Generate physical characteristics with slight variation"""
    variation = 0.02  # ±2% for ships (less than aircraft)

    chars = {}
    for key in ['length_meters', 'beam_meters', 'draft_meters', 'displacement_tons']:
        if key in platform and platform[key]:
            base_value = platform[key]
            chars[key] = round(base_value * random.uniform(1.0 - variation, 1.0 + variation), 2)

    return chars


def generate_operational_envelope_ship(platform: Dict) -> Dict:
    """Generate operational envelope for ships"""
    variation = 0.05

    envelope = {}
    for key in ['max_speed_kts', 'typical_speed_kts']:
        if key in platform and platform[key]:
            base_value = platform[key]
            envelope[key] = int(base_value * random.uniform(1.0 - variation, 1.0))

    return envelope


def simulate_curation_ship(index: int) -> Dict:
    """Simulate curator modifications"""
    curator_modified = random.random() < 0.10
    curator_locked = random.random() < 0.05 if curator_modified else False

    return {
        'curator_modified': curator_modified,
        'curator_locked': curator_locked,
        'curator_id': f"curator_{random.randint(1, 5)}" if curator_modified else None
    }


def generate_data_lineage_ship() -> Dict:
    """Generate data lineage for ships"""
    sources = ['ais_feed_1', 'ais_feed_2', 'lloyd_registry', 'manual_entry', 'naval_registry']

    return {
        'source': random.choice(sources),
        'source_timestamp': (datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat() + 'Z'
    }


def main():
    """Generate ship instances"""
    print("Loading reference data...")

    # Load platforms
    with open('../sample/platforms_maritime.json') as f:
        platforms_data = json.load(f)
        platforms = platforms_data['ship_classes']

    # Load organizations
    with open('../sample/organizations.json') as f:
        organizations = json.load(f)

    # Load locations
    with open('../sample/locations.json') as f:
        locations = json.load(f)

    print(f"Loaded {len(platforms)} ship classes")
    print(f"Loaded {len(organizations)} organizations")
    print(f"Loaded {len(locations)} locations")

    # Track used identifiers
    used_mmsi = set()
    used_imo = set()
    used_callsigns = set()

    ship_instances = []
    instance_id = 1

    print("\nGenerating ship instances...")

    for platform in platforms:
        count = platform['expected_instances']
        print(f"  {platform['ship_class']}: {platform['platform']} ({count} instances)")

        for i in range(count):
            # Assign operator and port
            operator = assign_operator_ship(platform, organizations)
            home_port = assign_home_port(operator, platform, locations)

            # Generate identifiers
            mmsi = generate_mmsi(operator['country'], used_mmsi)

            if platform['affiliation'] == 'MILITARY':
                sconum = generate_sconum(platform['ship_class'], i)
                imo_number = None
            else:
                sconum = None
                imo_number = generate_imo_number(used_imo)

            call_sign = generate_call_sign(operator['country'], used_callsigns)

            # Generate characteristics
            physical = generate_physical_characteristics(platform)
            envelope = generate_operational_envelope_ship(platform)

            # Curation simulation
            curation = simulate_curation_ship(instance_id)

            # Data lineage
            lineage = generate_data_lineage_ship()

            # Create instance
            instance = {
                'id': instance_id,
                'mmsi': mmsi,
                'sconum': sconum,
                'imo_number': imo_number,
                'call_sign': call_sign,
                'shark_name': f"{platform['platform']} {sconum if sconum else imo_number}",
                'platform': platform['platform'],
                'affiliation': platform['affiliation'],
                'nationality': operator['country'],
                'operator': operator['name'],
                'operator_id': operator['id'],
                'ship_type': platform['ship_type'],
                'ship_class': platform['ship_class'],
                'ship_role': platform['ship_role'],

                # Physical characteristics
                **physical,

                # Operational envelope
                **envelope,

                # Home port
                'home_port': home_port['name'] if home_port else None,
                'home_port_id': home_port['id'] if home_port else None,

                # Data lineage
                **lineage,
                **curation,

                # Metadata
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'updated_at': datetime.utcnow().isoformat() + 'Z'
            }

            ship_instances.append(instance)
            instance_id += 1

    print(f"\nGenerated {len(ship_instances)} ship instances")

    # Statistics
    military = sum(1 for s in ship_instances if s['affiliation'] == 'MILITARY')
    civilian = sum(1 for s in ship_instances if s['affiliation'] == 'CIVILIAN')
    curator_modified_count = sum(1 for s in ship_instances if s['curator_modified'])
    curator_locked_count = sum(1 for s in ship_instances if s['curator_locked'])

    print(f"  Military: {military} ({military/len(ship_instances)*100:.1f}%)")
    print(f"  Civilian: {civilian} ({civilian/len(ship_instances)*100:.1f}%)")
    print(f"  Curator modified: {curator_modified_count} ({curator_modified_count/len(ship_instances)*100:.1f}%)")
    print(f"  Curator locked: {curator_locked_count} ({curator_locked_count/len(ship_instances)*100:.1f}%)")

    # Write to file
    output_file = '../sample/ship_instances.json'
    with open(output_file, 'w') as f:
        json.dump(ship_instances, f, indent=2)

    print(f"\nWrote {len(ship_instances)} instances -> {output_file}")
    print(f"File size: {len(json.dumps(ship_instances)) / 1024 / 1024:.1f} MB")

    # Print samples
    print("\nSample instances:")
    for instance in ship_instances[:5]:
        identifier = instance['sconum'] if instance['sconum'] else instance['imo_number']
        print(f"  {instance['mmsi']} / {identifier}: {instance['shark_name']}")
        print(f"    Operator: {instance['operator']} ({instance['nationality']})")
        print(f"    Home port: {instance['home_port']}")
        print(f"    Type: {instance['ship_type']}, Class: {instance['ship_class']}")


if __name__ == '__main__':
    main()
