#!/usr/bin/env python3
"""
Activity Log Generator for Shark Bake-Off
Generates 90 days of track activity with ground truth patterns
"""

import json
import random
from typing import List, Dict, Set, Tuple
from datetime import datetime, timedelta


class GroundTruthPatterns:
    """Track ground truth co-occurrence patterns for validation"""

    def __init__(self):
        self.aircraft_pairs = []  # Known aircraft that fly together
        self.ship_pairs = []      # Known ships that travel together
        self.squadron_groups = {} # Aircraft grouped by squadron
        self.carrier_aircraft = {} # Aircraft assigned to carriers


def identify_squadron_groups(aircraft: List[Dict]) -> Dict[str, List[Dict]]:
    """Group aircraft by operator (squadron) for realistic co-occurrence"""
    groups = {}

    for ac in aircraft:
        operator = ac['operator']
        if operator not in groups:
            groups[operator] = []
        groups[operator].append(ac)

    # Filter to groups with 3+ aircraft (realistic for formations)
    squadron_groups = {k: v for k, v in groups.items() if len(v) >= 3}

    print(f"  Identified {len(squadron_groups)} squadron/operator groups")

    return squadron_groups


def create_ground_truth_pairs(aircraft: List[Dict], ships: List[Dict]) -> GroundTruthPatterns:
    """Create ground truth co-occurrence patterns"""
    patterns = GroundTruthPatterns()

    # Squadron groups (aircraft from same unit fly together)
    patterns.squadron_groups = identify_squadron_groups(aircraft)

    # Select 50 aircraft pairs that will frequently co-occur
    for squadron, members in patterns.squadron_groups.items():
        if len(members) >= 2:
            # Pick 2-4 pairs per squadron
            num_pairs = min(random.randint(2, 4), len(members) // 2)
            for _ in range(num_pairs):
                pair = random.sample(members, 2)
                patterns.aircraft_pairs.append((pair[0], pair[1]))

    # Tanker-fighter pairs (refueling operations)
    tankers = [a for a in aircraft if 'Tanker' in a.get('air_type', '')]
    fighters = [a for a in aircraft if 'Fighter' in a.get('air_type', '')]

    for tanker in tankers[:30]:  # Top 30 tankers
        # Each tanker has 3-5 regular customers
        customers = random.sample(fighters, min(5, len(fighters)))
        for customer in customers:
            patterns.aircraft_pairs.append((tanker, customer))

    # Carrier groups (destroyers escort carriers)
    carriers = [s for s in ships if s['ship_type'] == 'Aircraft Carrier']
    destroyers = [s for s in ships if s['ship_type'] == 'Destroyer']

    for carrier in carriers:
        # Each carrier has 2-4 escorts
        num_escorts = random.randint(2, min(4, len(destroyers)))
        escorts = random.sample(destroyers, num_escorts)
        for escort in escorts:
            patterns.ship_pairs.append((carrier, escort))

    # Aircraft-carrier assignments (for embarked operations)
    for carrier in carriers:
        # Each carrier has 20-40 assigned aircraft
        num_aircraft = random.randint(20, 40)
        # Prefer Navy fighters and support aircraft
        navy_aircraft = [a for a in aircraft
                        if 'Navy' in a['operator']
                        and a['air_type'] in ['Fighter', 'ISR']]

        if len(navy_aircraft) >= num_aircraft:
            assigned = random.sample(navy_aircraft, num_aircraft)
            patterns.carrier_aircraft[carrier['id']] = assigned

    print(f"  Ground truth aircraft pairs: {len(patterns.aircraft_pairs)}")
    print(f"  Ground truth ship pairs: {len(patterns.ship_pairs)}")
    print(f"  Carrier aircraft assignments: {sum(len(v) for v in patterns.carrier_aircraft.values())}")

    return patterns


def generate_port_calls(ships: List[Dict], locations: List[Dict], days: int, patterns: GroundTruthPatterns) -> List[Dict]:
    """Generate port call activities for ships"""
    print(f"\n  Generating port calls for {len(ships)} ships over {days} days...")

    activities = []
    ports = [l for l in locations if l['location_type'] == 'PORT']

    # Each ship visits 2-8 ports over 90 days
    for ship in ships:
        num_visits = random.randint(2, 8)
        home_port_id = ship.get('home_port_id')

        # Start at home port
        current_date = datetime.utcnow() - timedelta(days=days)

        for visit_num in range(num_visits):
            # Select port (50% chance of home port, 50% other)
            if home_port_id and random.random() < 0.5:
                port = next((l for l in locations if l['id'] == home_port_id), random.choice(ports))
            else:
                port = random.choice(ports)

            # Duration: 2-48 hours for most, 2-7 days for longer stays
            if random.random() < 0.7:
                duration_hours = random.randint(2, 48)
            else:
                duration_hours = random.randint(48, 168)

            # Arrival time
            arrival = current_date + timedelta(days=random.randint(5, 15))

            activity = {
                'track_id': f"SHIP_{ship['id']}_{visit_num}",
                'domain': 'MARITIME',
                'event_type': 'port_call',
                'activity_type': 'PORT_CALL',
                'kb_object_id': ship['id'],
                'mmsi': ship['mmsi'],
                'event_timestamp': arrival.isoformat() + 'Z',
                'latitude': port['latitude'],
                'longitude': port['longitude'],
                'properties': {
                    'port_id': port['id'],
                    'port_name': port['name'],
                    'duration_hours': duration_hours,
                    'purpose': random.choice(['RESUPPLY', 'CREW_CHANGE', 'MAINTENANCE', 'CARGO_OPS', 'PATROL'])
                },
                'associated_track_ids': [],
                'associated_kb_ids': []
            }

            activities.append(activity)
            current_date = arrival + timedelta(hours=duration_hours)

    # Add ground truth: ships that travel together visit same ports
    for ship1, ship2 in patterns.ship_pairs[:20]:  # Top 20 pairs
        # They visit same port 2-3 times
        num_joint = random.randint(2, 3)
        for _ in range(num_joint):
            port = random.choice(ports)
            visit_time = datetime.utcnow() - timedelta(days=random.randint(1, days))

            for ship in [ship1, ship2]:
                activity = {
                    'track_id': f"SHIP_{ship['id']}_joint",
                    'domain': 'MARITIME',
                    'event_type': 'port_call',
                    'activity_type': 'PORT_CALL',
                    'kb_object_id': ship['id'],
                    'mmsi': ship['mmsi'],
                    'event_timestamp': visit_time.isoformat() + 'Z',
                    'latitude': port['latitude'],
                    'longitude': port['longitude'],
                    'properties': {
                        'port_id': port['id'],
                        'port_name': port['name'],
                        'duration_hours': random.randint(12, 72),
                        'purpose': 'FORMATION_OPS',
                        'ground_truth': True
                    },
                    'associated_track_ids': [f"SHIP_{ship1['id']}", f"SHIP_{ship2['id']}"],
                    'associated_kb_ids': [ship1['id'], ship2['id']]
                }
                activities.append(activity)

    print(f"    Generated {len(activities)} port call activities")
    return activities


def generate_aircraft_co_occurrence(aircraft: List[Dict], locations: List[Dict], days: int, patterns: GroundTruthPatterns) -> List[Dict]:
    """Generate aircraft co-occurrence events"""
    print(f"\n  Generating aircraft co-occurrence for {len(patterns.aircraft_pairs)} pairs...")

    activities = []
    airfields = [l for l in locations if l['location_type'] == 'AIRFIELD']

    # Ground truth pairs co-occur frequently
    for aircraft1, aircraft2 in patterns.aircraft_pairs:
        # Each pair has 5-15 co-occurrence events over 90 days
        num_events = random.randint(5, 15)

        for event_num in range(num_events):
            # Pick location (prefer their home bases)
            if random.random() < 0.6 and aircraft1.get('home_base_id'):
                location = next((l for l in locations if l['id'] == aircraft1['home_base_id']), random.choice(airfields))
            else:
                location = random.choice(airfields)

            event_time = datetime.utcnow() - timedelta(days=random.randint(1, days),
                                                       hours=random.randint(0, 23),
                                                       minutes=random.randint(0, 59))

            # Create co-occurrence event
            activity = {
                'track_id': f"AIR_{aircraft1['id']}_{aircraft2['id']}_{event_num}",
                'domain': 'AIR',
                'event_type': 'co_located',
                'activity_type': 'CO_OCCURRENCE',
                'kb_object_id': aircraft1['id'],
                'mode_s': aircraft1['mode_s'],
                'event_timestamp': event_time.isoformat() + 'Z',
                'latitude': location['latitude'] + random.uniform(-0.1, 0.1),
                'longitude': location['longitude'] + random.uniform(-0.1, 0.1),
                'properties': {
                    'location_id': location['id'],
                    'location_name': location['name'],
                    'activity': random.choice(['FORMATION_FLIGHT', 'TRAINING', 'PATROL', 'TRANSIT']),
                    'ground_truth': True
                },
                'associated_track_ids': [f"AIR_{aircraft1['id']}", f"AIR_{aircraft2['id']}"],
                'associated_kb_ids': [aircraft1['id'], aircraft2['id']]
            }

            activities.append(activity)

    # Random co-occurrences (noise in the data)
    num_random = len(patterns.aircraft_pairs) * 3  # 3x random vs ground truth

    for _ in range(num_random):
        pair = random.sample(aircraft, 2)
        location = random.choice(airfields)
        event_time = datetime.utcnow() - timedelta(days=random.randint(1, days),
                                                   hours=random.randint(0, 23))

        activity = {
            'track_id': f"AIR_{pair[0]['id']}_{pair[1]['id']}_random",
            'domain': 'AIR',
            'event_type': 'co_located',
            'activity_type': 'CO_OCCURRENCE',
            'kb_object_id': pair[0]['id'],
            'mode_s': pair[0]['mode_s'],
            'event_timestamp': event_time.isoformat() + 'Z',
            'latitude': location['latitude'] + random.uniform(-0.1, 0.1),
            'longitude': location['longitude'] + random.uniform(-0.1, 0.1),
            'properties': {
                'location_id': location['id'],
                'location_name': location['name'],
                'activity': 'TRANSIT',
                'ground_truth': False
            },
            'associated_track_ids': [f"AIR_{pair[0]['id']}", f"AIR_{pair[1]['id']}"],
            'associated_kb_ids': [pair[0]['id'], pair[1]['id']]
        }

        activities.append(activity)

    print(f"    Generated {len(activities)} aircraft co-occurrence events")
    print(f"    Ground truth: {sum(1 for a in activities if a['properties'].get('ground_truth'))} events")
    print(f"    Random noise: {sum(1 for a in activities if not a['properties'].get('ground_truth'))} events")

    return activities


def generate_aerial_refueling(aircraft: List[Dict], days: int) -> List[Dict]:
    """Generate aerial refueling events (tankers + receivers)"""
    print(f"\n  Generating aerial refueling events...")

    activities = []
    tankers = [a for a in aircraft if 'Tanker' in a.get('air_type', '')]
    receivers = [a for a in aircraft if a.get('air_type') in ['Fighter', 'Bomber', 'ISR']]

    # Each tanker does 10-30 refueling operations over 90 days
    for tanker in tankers:
        num_ops = random.randint(10, 30)

        for op_num in range(num_ops):
            # 1-4 receivers per operation
            num_receivers = random.randint(1, 4)
            op_receivers = random.sample(receivers, min(num_receivers, len(receivers)))

            event_time = datetime.utcnow() - timedelta(days=random.randint(1, days),
                                                       hours=random.randint(0, 23))

            # Random location (over ocean or land)
            lat = random.uniform(20.0, 50.0)
            lon = random.uniform(-130.0, -70.0)

            for receiver in op_receivers:
                activity = {
                    'track_id': f"REFUEL_{tanker['id']}_{receiver['id']}_{op_num}",
                    'domain': 'AIR',
                    'event_type': 'air_refueling',
                    'activity_type': 'AIR_REFUELING',
                    'kb_object_id': receiver['id'],
                    'mode_s': receiver['mode_s'],
                    'event_timestamp': event_time.isoformat() + 'Z',
                    'latitude': lat,
                    'longitude': lon,
                    'properties': {
                        'tanker_mode_s': tanker['mode_s'],
                        'tanker_id': tanker['id'],
                        'fuel_transferred': random.randint(5000, 20000),  # pounds
                        'duration_minutes': random.randint(10, 30)
                    },
                    'associated_track_ids': [f"AIR_{tanker['id']}", f"AIR_{receiver['id']}"],
                    'associated_kb_ids': [tanker['id'], receiver['id']]
                }

                activities.append(activity)

    print(f"    Generated {len(activities)} aerial refueling events")
    return activities


def generate_carrier_operations(ships: List[Dict], aircraft: List[Dict], days: int, patterns: GroundTruthPatterns) -> List[Dict]:
    """Generate carrier operations (aircraft embarked on carriers)"""
    print(f"\n  Generating carrier operations...")

    activities = []

    for carrier_id, assigned_aircraft in patterns.carrier_aircraft.items():
        # Each aircraft does 3-10 carrier ops over 90 days
        for ac in assigned_aircraft:
            num_ops = random.randint(3, 10)

            for op_num in range(num_ops):
                event_time = datetime.utcnow() - timedelta(days=random.randint(1, days),
                                                           hours=random.randint(0, 23))

                # Carrier location (at sea)
                lat = random.uniform(20.0, 40.0)
                lon = random.uniform(-180.0, 180.0)

                activity = {
                    'track_id': f"CARRIER_OPS_{carrier_id}_{ac['id']}_{op_num}",
                    'domain': 'CROSS',
                    'event_type': 'embarked_on',
                    'activity_type': 'CARRIER_OPERATIONS',
                    'kb_object_id': ac['id'],
                    'mode_s': ac['mode_s'],
                    'event_timestamp': event_time.isoformat() + 'Z',
                    'latitude': lat,
                    'longitude': lon,
                    'properties': {
                        'carrier_id': carrier_id,
                        'operation': random.choice(['LAUNCH', 'RECOVERY', 'TRAINING']),
                        'duration_hours': random.randint(2, 12)
                    },
                    'associated_track_ids': [f"SHIP_{carrier_id}", f"AIR_{ac['id']}"],
                    'associated_kb_ids': [carrier_id, ac['id']]
                }

                activities.append(activity)

    print(f"    Generated {len(activities)} carrier operations")
    return activities


def main():
    """Generate activity log"""
    print("Loading reference data...")

    # Load aircraft
    with open('../sample/aircraft_instances.json') as f:
        aircraft = json.load(f)

    # Load ships
    with open('../sample/ship_instances.json') as f:
        ships = json.load(f)

    # Load locations
    with open('../sample/locations.json') as f:
        locations = json.load(f)

    print(f"Loaded {len(aircraft)} aircraft")
    print(f"Loaded {len(ships)} ships")
    print(f"Loaded {len(locations)} locations")

    # Create ground truth patterns
    print("\nCreating ground truth patterns...")
    patterns = create_ground_truth_pairs(aircraft, ships)

    # Generate activities
    days = 90
    all_activities = []

    # Port calls
    all_activities.extend(generate_port_calls(ships, locations, days, patterns))

    # Aircraft co-occurrence
    all_activities.extend(generate_aircraft_co_occurrence(aircraft, locations, days, patterns))

    # Aerial refueling
    all_activities.extend(generate_aerial_refueling(aircraft, days))

    # Carrier operations
    all_activities.extend(generate_carrier_operations(ships, aircraft, days, patterns))

    # Sort by timestamp
    all_activities.sort(key=lambda x: x['event_timestamp'])

    print(f"\n{'='*60}")
    print(f"TOTAL ACTIVITIES GENERATED: {len(all_activities)}")
    print(f"{'='*60}")

    # Statistics
    by_type = {}
    for activity in all_activities:
        atype = activity['activity_type']
        by_type[atype] = by_type.get(atype, 0) + 1

    print("\nActivity breakdown:")
    for atype, count in sorted(by_type.items(), key=lambda x: -x[1]):
        pct = (count / len(all_activities)) * 100
        print(f"  {atype}: {count:6d} ({pct:5.1f}%)")

    # Write to file
    output_file = '../sample/activity_log.json'
    with open(output_file, 'w') as f:
        json.dump(all_activities, f, indent=2)

    print(f"\nWrote {len(all_activities)} activities -> {output_file}")
    print(f"File size: {len(json.dumps(all_activities)) / 1024 / 1024:.1f} MB")

    # Write ground truth patterns separately for validation
    ground_truth_file = '../sample/ground_truth_patterns.json'
    ground_truth_data = {
        'aircraft_pairs': [(a1['mode_s'], a2['mode_s']) for a1, a2 in patterns.aircraft_pairs],
        'ship_pairs': [(s1['mmsi'], s2['mmsi']) for s1, s2 in patterns.ship_pairs],
        'carrier_aircraft': {k: [a['mode_s'] for a in v] for k, v in patterns.carrier_aircraft.items()}
    }

    with open(ground_truth_file, 'w') as f:
        json.dump(ground_truth_data, f, indent=2)

    print(f"\nWrote ground truth patterns -> {ground_truth_file}")


if __name__ == '__main__':
    main()
