#!/usr/bin/env python3
"""
Relationship Generator for Shark Bake-Off
Generates graph relationships from entities and activities
"""

import json
from typing import List, Dict, Set
from datetime import datetime
from collections import defaultdict


def generate_operational_relationships(aircraft: List[Dict], ships: List[Dict], organizations: List[Dict]) -> List[Dict]:
    """Generate OPERATED_BY relationships"""
    print("\nGenerating OPERATED_BY relationships...")

    relationships = []
    rel_id = 1

    # Aircraft → Organizations
    for ac in aircraft:
        rel = {
            'id': rel_id,
            'source_domain': 'AIR',
            'source_id': ac['id'],
            'target_domain': 'ORGANIZATION',
            'target_id': ac['operator_id'],
            'relationship_type': 'OPERATED_BY',
            'properties': {
                'since': ac['created_at'],
                'primary_operator': True
            },
            'valid_from': ac['created_at'],
            'valid_to': None,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'source': ac.get('source', 'generator'),
            'confidence': 1.0
        }
        relationships.append(rel)
        rel_id += 1

    # Ships → Organizations
    for ship in ships:
        rel = {
            'id': rel_id,
            'source_domain': 'MARITIME',
            'source_id': ship['id'],
            'target_domain': 'ORGANIZATION',
            'target_id': ship['operator_id'],
            'relationship_type': 'OPERATED_BY',
            'properties': {
                'since': ship['created_at'],
                'primary_operator': True
            },
            'valid_from': ship['created_at'],
            'valid_to': None,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'source': ship.get('source', 'generator'),
            'confidence': 1.0
        }
        relationships.append(rel)
        rel_id += 1

    print(f"  Generated {len(relationships)} OPERATED_BY relationships")
    return relationships


def generate_location_relationships(aircraft: List[Dict], ships: List[Dict]) -> List[Dict]:
    """Generate BASED_AT and HOME_PORT relationships"""
    print("\nGenerating location relationships...")

    relationships = []
    rel_id = 1

    # Aircraft → Home Bases (BASED_AT)
    for ac in aircraft:
        if ac.get('home_base_id'):
            rel = {
                'id': rel_id,
                'source_domain': 'AIR',
                'source_id': ac['id'],
                'target_domain': 'LOCATION',
                'target_id': ac['home_base_id'],
                'relationship_type': 'BASED_AT',
                'properties': {
                    'icao_code': ac.get('home_base_icao'),
                    'primary_base': True
                },
                'valid_from': ac['created_at'],
                'valid_to': None,
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'source': 'generator',
                'confidence': 1.0
            }
            relationships.append(rel)
            rel_id += 1

    # Ships → Home Ports (HOME_PORT)
    for ship in ships:
        if ship.get('home_port_id'):
            rel = {
                'id': rel_id,
                'source_domain': 'MARITIME',
                'source_id': ship['id'],
                'target_domain': 'LOCATION',
                'target_id': ship['home_port_id'],
                'relationship_type': 'HOME_PORT',
                'properties': {
                    'primary_port': True
                },
                'valid_from': ship['created_at'],
                'valid_to': None,
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'source': 'generator',
                'confidence': 1.0
            }
            relationships.append(rel)
            rel_id += 1

    print(f"  Generated {len(relationships)} location relationships")
    return relationships


def generate_co_occurrence_relationships(activities: List[Dict]) -> List[Dict]:
    """Generate SEEN_WITH relationships from co-occurrence activities"""
    print("\nGenerating SEEN_WITH relationships from co-occurrence activities...")

    relationships = []
    rel_id = 1

    # Track unique pairs to avoid duplicates
    seen_pairs = set()

    # Group by pairs and aggregate
    pair_events = defaultdict(list)

    for activity in activities:
        if activity['activity_type'] == 'CO_OCCURRENCE':
            kb_ids = activity.get('associated_kb_ids', [])
            if len(kb_ids) == 2:
                # Create canonical pair (smaller ID first)
                pair = tuple(sorted(kb_ids))
                pair_events[pair].append(activity)

    # Create relationships from aggregated pairs
    for (id1, id2), events in pair_events.items():
        # Sort events by time
        events.sort(key=lambda x: x['event_timestamp'])

        # Is this a ground truth pair?
        is_ground_truth = any(e['properties'].get('ground_truth', False) for e in events)

        rel = {
            'id': rel_id,
            'source_domain': 'AIR',
            'source_id': id1,
            'target_domain': 'AIR',
            'target_id': id2,
            'relationship_type': 'SEEN_WITH',
            'properties': {
                'occurrence_count': len(events),
                'first_seen': events[0]['event_timestamp'],
                'last_seen': events[-1]['event_timestamp'],
                'ground_truth': is_ground_truth,
                'locations': list(set(e['properties'].get('location_name') for e in events if e['properties'].get('location_name')))
            },
            'valid_from': events[0]['event_timestamp'],
            'valid_to': None,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'source': 'activity_log',
            'confidence': min(1.0, len(events) / 10.0)  # Higher confidence with more sightings
        }
        relationships.append(rel)
        rel_id += 1

    print(f"  Generated {len(relationships)} SEEN_WITH relationships")
    print(f"    Ground truth pairs: {sum(1 for r in relationships if r['properties'].get('ground_truth'))}")
    print(f"    Random pairs: {sum(1 for r in relationships if not r['properties'].get('ground_truth'))}")

    return relationships


def generate_port_visit_relationships(activities: List[Dict], ships: List[Dict]) -> List[Dict]:
    """Generate VISITED relationships from port call activities"""
    print("\nGenerating VISITED relationships from port calls...")

    relationships = []
    rel_id = 1

    # Each port call becomes a VISITED relationship
    for activity in activities:
        if activity['activity_type'] == 'PORT_CALL':
            rel = {
                'id': rel_id,
                'source_domain': 'MARITIME',
                'source_id': activity['kb_object_id'],
                'target_domain': 'LOCATION',
                'target_id': activity['properties']['port_id'],
                'relationship_type': 'VISITED',
                'properties': {
                    'timestamp': activity['event_timestamp'],
                    'duration_hours': activity['properties']['duration_hours'],
                    'purpose': activity['properties']['purpose']
                },
                'valid_from': activity['event_timestamp'],
                'valid_to': None,
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'source': 'activity_log',
                'confidence': 1.0
            }
            relationships.append(rel)
            rel_id += 1

    print(f"  Generated {len(relationships)} VISITED relationships")

    return relationships


def generate_refueling_relationships(activities: List[Dict]) -> List[Dict]:
    """Generate REFUELED_BY relationships from aerial refueling activities"""
    print("\nGenerating REFUELED_BY relationships from aerial refueling...")

    relationships = []
    rel_id = 1

    # Group by receiver-tanker pairs
    refuel_pairs = defaultdict(list)

    for activity in activities:
        if activity['activity_type'] == 'AIR_REFUELING':
            receiver_id = activity['kb_object_id']
            tanker_id = activity['properties']['tanker_id']
            refuel_pairs[(receiver_id, tanker_id)].append(activity)

    # Create relationships from aggregated pairs
    for (receiver_id, tanker_id), events in refuel_pairs.items():
        events.sort(key=lambda x: x['event_timestamp'])

        total_fuel = sum(e['properties']['fuel_transferred'] for e in events)

        rel = {
            'id': rel_id,
            'source_domain': 'AIR',
            'source_id': receiver_id,
            'target_domain': 'AIR',
            'target_id': tanker_id,
            'relationship_type': 'REFUELED_BY',
            'properties': {
                'refuel_count': len(events),
                'total_fuel_transferred': total_fuel,
                'first_refuel': events[0]['event_timestamp'],
                'last_refuel': events[-1]['event_timestamp']
            },
            'valid_from': events[0]['event_timestamp'],
            'valid_to': None,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'source': 'activity_log',
            'confidence': 1.0
        }
        relationships.append(rel)
        rel_id += 1

    print(f"  Generated {len(relationships)} REFUELED_BY relationships")

    return relationships


def main():
    """Generate all relationships"""
    print("Loading reference data...")

    # Load aircraft
    with open('../sample/aircraft_instances.json') as f:
        aircraft = json.load(f)

    # Load ships
    with open('../sample/ship_instances.json') as f:
        ships = json.load(f)

    # Load organizations
    with open('../sample/organizations.json') as f:
        organizations = json.load(f)

    # Load activities
    with open('../sample/activity_log.json') as f:
        activities = json.load(f)

    print(f"Loaded {len(aircraft)} aircraft")
    print(f"Loaded {len(ships)} ships")
    print(f"Loaded {len(organizations)} organizations")
    print(f"Loaded {len(activities)} activities")

    all_relationships = []

    # Generate operational relationships
    all_relationships.extend(generate_operational_relationships(aircraft, ships, organizations))

    # Generate location relationships
    all_relationships.extend(generate_location_relationships(aircraft, ships))

    # Generate activity-based relationships
    all_relationships.extend(generate_co_occurrence_relationships(activities))

    all_relationships.extend(generate_port_visit_relationships(activities, ships))

    all_relationships.extend(generate_refueling_relationships(activities))

    # Reassign IDs sequentially
    for i, rel in enumerate(all_relationships, 1):
        rel['id'] = i

    print(f"\n{'='*60}")
    print(f"TOTAL RELATIONSHIPS GENERATED: {len(all_relationships)}")
    print(f"{'='*60}")

    # Statistics
    by_type = {}
    for rel in all_relationships:
        rtype = rel['relationship_type']
        by_type[rtype] = by_type.get(rtype, 0) + 1

    print("\nRelationship breakdown:")
    for rtype, count in sorted(by_type.items(), key=lambda x: -x[1]):
        pct = (count / len(all_relationships)) * 100
        print(f"  {rtype}: {count:6d} ({pct:5.1f}%)")

    # Write to file
    output_file = '../sample/relationships.json'
    with open(output_file, 'w') as f:
        json.dump(all_relationships, f, indent=2)

    print(f"\nWrote {len(all_relationships)} relationships -> {output_file}")
    print(f"File size: {len(json.dumps(all_relationships)) / 1024 / 1024:.1f} MB")

    # Sample relationships
    print("\nSample relationships:")
    for rel in all_relationships[:5]:
        print(f"  {rel['relationship_type']}: {rel['source_domain']}:{rel['source_id']} -> {rel['target_domain']}:{rel['target_id']}")
        if rel.get('properties'):
            print(f"    Properties: {list(rel['properties'].keys())}")


if __name__ == '__main__':
    main()
