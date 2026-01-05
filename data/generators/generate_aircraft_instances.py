#!/usr/bin/env python3
"""
Aircraft Instance Generator for Shark Bake-Off
Generates 5,560 aircraft instances with fictional identifiers
"""

import json
import random
from typing import List, Dict, Set
from datetime import datetime, timedelta


def generate_mode_s(used_codes: Set[str]) -> str:
    """Generate unique Mode-S code (6-character hex)"""
    while True:
        # Mode-S codes are 24-bit (6 hex chars)
        # US allocations typically start with A (0xA00000-0xAFFFFF)
        code = f"{random.randint(0xA00000, 0xAFFFFF):06X}"
        if code not in used_codes:
            used_codes.add(code)
            return code


def generate_tail_number(country: str, platform_code: str, used_tails: Set[str]) -> str:
    """Generate country-appropriate tail number"""
    while True:
        if country == "USA":
            # US N-numbers: N + 1-5 digits/letters
            tail = f"N{random.randint(10000, 99999)}"
        elif country == "GBR":
            # UK: G-XXXX
            tail = f"G-{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{random.randint(100, 999):03d}"
        elif country == "DEU":
            # Germany: D-XXXX
            tail = f"D-{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{random.randint(100, 999):03d}"
        elif country == "FRA":
            # France: F-XXXX
            tail = f"F-{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{random.randint(100, 999):03d}"
        elif country == "JPN":
            # Japan: JA####
            tail = f"JA{random.randint(1000, 9999)}"
        elif country == "AUS":
            # Australia: VH-XXX
            tail = f"VH-{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{random.randint(10, 99):02d}"
        else:
            # Generic format
            tail = f"{country[:2]}-{random.randint(1000, 9999)}"

        if tail not in used_tails:
            used_tails.add(tail)
            return tail


def assign_operator(platform: Dict, organizations: List[Dict]) -> Dict:
    """Assign appropriate operator based on platform category"""
    category = platform['category']

    if 'Military' in category:
        # Military aircraft
        if 'Fighter' in category or 'Bomber' in category:
            # Fighters/bombers go to fighter wings
            candidates = [o for o in organizations
                         if o['org_type'] == 'MILITARY'
                         and ('Wing' in o['name'] or 'Squadron' in o['name'] or 'Force' in o['name'])]
        elif 'Transport' in category or 'Tanker' in category:
            # Transports/tankers to airlift wings
            candidates = [o for o in organizations
                         if o['org_type'] == 'MILITARY'
                         and ('Wing' in o['name'] or 'Force' in o['name'])]
        elif 'ISR' in category:
            # ISR to specialized units
            candidates = [o for o in organizations
                         if o['org_type'] == 'MILITARY'
                         and 'Force' in o['name']]
        else:
            # Generic military
            candidates = [o for o in organizations if o['org_type'] == 'MILITARY']

    elif 'Commercial' in category:
        # Commercial aircraft to airlines
        candidates = [o for o in organizations
                     if o['org_type'] == 'CIVILIAN'
                     and ('Air' in o['name'] or 'Airline' in o['name'])]

    elif 'Business' in category:
        # Business jets to corporate operators or NetJets-type
        candidates = [o for o in organizations
                     if o['org_type'] == 'CIVILIAN'
                     and any(x in o['name'] for x in ['Aviation', 'Jet', 'Corp', 'Flight'])]
        if not candidates:
            candidates = [o for o in organizations if o['org_type'] == 'CIVILIAN']

    elif 'General Aviation' in category:
        # General aviation to flight schools, corporate
        candidates = [o for o in organizations
                     if o['org_type'] == 'CIVILIAN'
                     and any(x in o['name'] for x in ['School', 'Flight', 'Aviation', 'Corp'])]
        if not candidates:
            candidates = [o for o in organizations if o['org_type'] == 'CIVILIAN']

    else:
        # Fallback: any civilian
        candidates = [o for o in organizations if o['org_type'] == 'CIVILIAN']

    if not candidates:
        candidates = organizations

    return random.choice(candidates)


def assign_home_base(operator: Dict, platform: Dict, locations: List[Dict]) -> Dict:
    """Assign home base based on operator and platform type"""
    country = operator['country']
    category = platform['category']

    if 'Military' in category:
        # Military aircraft to military airfields
        candidates = [l for l in locations
                     if l['location_type'] == 'AIRFIELD'
                     and l['country'] == country
                     and ('AFB' in l['name'] or 'Air Force' in l['name'] or 'RAF' in l['name'] or 'Air Base' in l['name'])]

        if not candidates:
            # Fallback to any military base in country
            candidates = [l for l in locations
                         if l['country'] == country
                         and l['location_type'] in ['AIRFIELD', 'BASE']]

    elif 'Commercial' in category:
        # Commercial to major airports
        candidates = [l for l in locations
                     if l['location_type'] == 'AIRFIELD'
                     and l['country'] == country
                     and 'Intl' in l['name']]

        if not candidates:
            # Fallback to any airport in country
            candidates = [l for l in locations
                         if l['location_type'] == 'AIRFIELD'
                         and l['country'] == country]

    else:
        # General aviation / business jets to any airport
        candidates = [l for l in locations
                     if l['location_type'] == 'AIRFIELD'
                     and l['country'] == country]

    if not candidates:
        # Final fallback: any airfield
        candidates = [l for l in locations if l['location_type'] == 'AIRFIELD']

    return random.choice(candidates) if candidates else None


def generate_operational_envelope(platform: Dict) -> Dict:
    """Generate operational envelope with slight variation from platform specs"""
    # Add ±5% variation to represent individual aircraft differences
    variation = 0.05

    envelope = {}
    for key in ['max_altitude_ft', 'min_altitude_ft', 'max_speed_kts', 'min_speed_kts',
                'typical_cruise_altitude_ft', 'typical_cruise_speed_kts']:
        if key in platform and platform[key]:
            base_value = platform[key]
            if 'min' in key.lower():
                # Min values can be slightly higher
                envelope[key] = int(base_value * random.uniform(1.0, 1.0 + variation))
            else:
                # Max values can be slightly lower due to age/maintenance
                envelope[key] = int(base_value * random.uniform(1.0 - variation, 1.0))

    return envelope


def simulate_curation(index: int, total: int) -> Dict:
    """Simulate curator modifications for realism"""
    # 10% of records are curator-modified
    # 5% of records are curator-locked

    curator_modified = random.random() < 0.10
    curator_locked = random.random() < 0.05 if curator_modified else False

    curation = {
        'curator_modified': curator_modified,
        'curator_locked': curator_locked,
        'curator_id': f"curator_{random.randint(1, 5)}" if curator_modified else None
    }

    return curation


def generate_data_lineage() -> Dict:
    """Generate data lineage fields"""
    sources = ['adsb_feed_1', 'adsb_feed_2', 'external_registry', 'manual_entry', 'faa_registry']

    return {
        'source': random.choice(sources),
        'source_timestamp': (datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat() + 'Z'
    }


def main():
    """Generate aircraft instances"""
    print("Loading reference data...")

    # Load platforms
    with open('../sample/platforms_aircraft.json') as f:
        platforms_data = json.load(f)
        platforms = platforms_data['aircraft_types']

    # Load organizations
    with open('../sample/organizations.json') as f:
        organizations = json.load(f)

    # Load locations
    with open('../sample/locations.json') as f:
        locations = json.load(f)

    print(f"Loaded {len(platforms)} platform types")
    print(f"Loaded {len(organizations)} organizations")
    print(f"Loaded {len(locations)} locations")

    # Track used identifiers
    used_mode_s = set()
    used_tails = set()

    aircraft_instances = []
    instance_id = 1

    print("\nGenerating aircraft instances...")

    for platform in platforms:
        count = platform['expected_instances']
        print(f"  {platform['icao_type_code']}: {platform['platform']} ({count} instances)")

        for i in range(count):
            # Assign operator and base
            operator = assign_operator(platform, organizations)
            home_base = assign_home_base(operator, platform, locations)

            # Generate identifiers
            mode_s = generate_mode_s(used_mode_s)
            tail_number = generate_tail_number(operator['country'], platform['icao_type_code'], used_tails)

            # Generate envelope
            envelope = generate_operational_envelope(platform)

            # Curation simulation
            curation = simulate_curation(instance_id, 5560)

            # Data lineage
            lineage = generate_data_lineage()

            # Create instance
            instance = {
                'id': instance_id,
                'mode_s': mode_s,
                'tail_number': tail_number,
                'icao_type_code': platform['icao_type_code'],
                'shark_name': f"{platform['platform']} ({tail_number})",
                'platform': platform['platform'],
                'affiliation': 'MILITARY' if 'Military' in platform['category'] else 'CIVILIAN',
                'nationality': operator['country'],
                'operator': operator['name'],
                'operator_id': operator['id'],
                'air_type': platform['air_type'],
                'air_model': platform.get('air_model', platform['icao_type_code']),
                'air_role': platform['air_role'],

                # Operational envelope
                **envelope,

                # Home base
                'home_base': home_base['name'] if home_base else None,
                'home_base_id': home_base['id'] if home_base else None,
                'home_base_icao': home_base.get('icao_code') if home_base else None,

                # Data lineage
                **lineage,
                **curation,

                # Metadata
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'updated_at': datetime.utcnow().isoformat() + 'Z'
            }

            aircraft_instances.append(instance)
            instance_id += 1

    print(f"\nGenerated {len(aircraft_instances)} aircraft instances")

    # Statistics
    curator_modified_count = sum(1 for a in aircraft_instances if a['curator_modified'])
    curator_locked_count = sum(1 for a in aircraft_instances if a['curator_locked'])

    print(f"  Curator modified: {curator_modified_count} ({curator_modified_count/len(aircraft_instances)*100:.1f}%)")
    print(f"  Curator locked: {curator_locked_count} ({curator_locked_count/len(aircraft_instances)*100:.1f}%)")

    # Write to file
    output_file = '../sample/aircraft_instances.json'
    with open(output_file, 'w') as f:
        json.dump(aircraft_instances, f, indent=2)

    print(f"\nWrote {len(aircraft_instances)} instances -> {output_file}")
    print(f"File size: {len(json.dumps(aircraft_instances)) / 1024 / 1024:.1f} MB")

    # Print samples
    print("\nSample instances:")
    for instance in aircraft_instances[:5]:
        print(f"  {instance['mode_s']} / {instance['tail_number']}: {instance['shark_name']}")
        print(f"    Operator: {instance['operator']} ({instance['nationality']})")
        print(f"    Base: {instance['home_base']} ({instance['home_base_icao']})")
        print(f"    Curation: modified={instance['curator_modified']}, locked={instance['curator_locked']}")


if __name__ == '__main__':
    main()
