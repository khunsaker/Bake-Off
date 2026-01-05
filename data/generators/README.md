# Data Generators

This directory contains Python scripts to generate realistic test data for the Shark Bake-Off benchmark.

## Generated Dataset Summary

### Entities (6,052 total)

| Type | Count | File Size | Description |
|------|-------|-----------|-------------|
| **Aircraft** | 5,560 | 5.0 MB | Commercial, military, general aviation |
| **Ships** | 492 | 446 KB | Naval vessels, cargo ships, tankers |
| **Organizations** | 147 | 26 KB | Military units, airlines, shipping companies |
| **Locations** | 77 | 18 KB | Air bases, airports, naval ports |
| **Platforms** | 51 | 23 KB | Aircraft types (26) + Ship classes (25) |

### Activities (18,083 events over 90 days)

| Type | Count | Percentage | Description |
|------|-------|------------|-------------|
| **AIR_REFUELING** | 9,664 | 53.4% | Tanker operations with receivers |
| **CO_OCCURRENCE** | 5,881 | 32.5% | Aircraft seen together (4,516 ground truth, 1,365 noise) |
| **PORT_CALL** | 2,538 | 14.0% | Ship port visits with duration |

**File**: `activity_log.json` (10 MB)

### Relationships (25,811 total)

| Type | Count | Percentage | Description |
|------|-------|------------|-------------|
| **REFUELED_BY** | 9,350 | 36.2% | Receiver → Tanker relationships |
| **OPERATED_BY** | 6,052 | 23.4% | Aircraft/Ships → Organizations |
| **BASED_AT** | 5,560 | 21.5% | Aircraft → Home Airfields |
| **VISITED** | 2,538 | 9.8% | Ships → Ports (from activities) |
| **SEEN_WITH** | 1,819 | 7.0% | Aircraft → Aircraft co-occurrence |
| **HOME_PORT** | 492 | 1.9% | Ships → Home Ports |

**File**: `relationships.json` (12 MB)

### Ground Truth Patterns

For validation and testing of knowledge generation queries:

- **455 aircraft pairs** that frequently fly together (squadron mates, tanker-fighter pairs)
- **43 ship pairs** that travel together (carrier groups, escorts)
- **101 squadron/operator groups** identified

**File**: `ground_truth_patterns.json` (22 KB)

## Data Generation Scripts

### 1. Reference Data Generators

Run these first to create base reference data:

```bash
python3 generate_organizations.py  # Creates 147 organizations
python3 generate_locations.py      # Creates 77 locations
```

**Platforms** (pre-created):
- `platforms_aircraft.json` - 26 aircraft types with real specs
- `platforms_maritime.json` - 25 ship classes with real specs

### 2. Instance Generators

Generate entity instances with fictional identifiers:

```bash
python3 generate_aircraft_instances.py  # Creates 5,560 aircraft (4-5 min)
python3 generate_ship_instances.py      # Creates 492 ships (30 sec)
```

**Aircraft Features**:
- Unique Mode-S codes (hex format: A1B2C3)
- Country-appropriate tail numbers (N12345 for USA, G-ABCD for UK, etc.)
- Realistic operator assignments based on aircraft type
- Home base assignments
- Operational envelope variations (±5% from platform specs)
- 10% curator-modified, 0.5% curator-locked

**Ship Features**:
- Unique MMSI (9-digit, country-specific MID codes)
- SCONUM for military vessels (CVN-68, DDG-51, etc.)
- IMO numbers for commercial vessels
- Call signs
- Physical characteristics (±2% variation)
- 10% curator-modified

### 3. Activity and Relationship Generators

Generate temporal data and graph relationships:

```bash
python3 generate_activity_log.py     # Creates 18,083 activities (1-2 min)
python3 generate_relationships.py    # Creates 25,811 relationships (30 sec)
```

**Activity Log Features**:
- 90 days of historical data
- Realistic patterns (squadron formations, tanker ops, port visits)
- Ground truth pairs for validation
- Random noise for realism (1,365 random co-occurrences)

**Relationship Features**:
- Operational relationships (OPERATED_BY, BASED_AT)
- Activity-derived relationships (SEEN_WITH, VISITED, REFUELED_BY)
- Temporal properties (valid_from, valid_to)
- Confidence scores based on occurrence frequency

## Data Distribution

### Aircraft by Category

| Category | Count | Percentage |
|----------|-------|------------|
| Commercial Transport | 2,100 | 37.8% |
| General Aviation | 1,750 | 31.5% |
| Military Fighter | 620 | 11.2% |
| Military Transport | 350 | 6.3% |
| Business Jet | 350 | 6.3% |
| Military Tanker | 190 | 3.4% |
| Military ISR | 110 | 2.0% |
| Military Bomber | 90 | 1.6% |

### Ships by Category

| Category | Count | Percentage |
|----------|-------|------------|
| Commercial Container | 105 | 21.3% |
| Military Combatant | 124 | 25.2% |
| Commercial Tanker | 70 | 14.2% |
| Military: 194 (39.4%) | Civilian: 298 (60.6%) |

## Curation Simulation

To test curator workflow features:

- **10% of entities** have `curator_modified: true`
- **~0.5% of entities** have `curator_locked: true`
- **5 curator IDs** assigned randomly (curator_1 through curator_5)
- **Multiple data sources** simulated (adsb_feed_1, adsb_feed_2, ais_feed_1, manual_entry, registries)

## Usage

### Generate All Data (Full Pipeline)

```bash
# Navigate to generators directory
cd data/generators

# Generate reference data
python3 generate_organizations.py
python3 generate_locations.py

# Generate instances
python3 generate_aircraft_instances.py
python3 generate_ship_instances.py

# Generate activities and relationships
python3 generate_activity_log.py
python3 generate_relationships.py
```

**Total generation time**: ~5-7 minutes
**Total data size**: ~28 MB (JSON files)

### Load into Databases

(Loaders to be implemented)

```bash
python3 load_postgresql.py   # Load into PostgreSQL
python3 load_neo4j.py         # Load into Neo4j
python3 load_memgraph.py      # Load into Memgraph
```

## Data Quality

### Validation Checks

- ✅ All Mode-S codes are unique (5,560 unique values)
- ✅ All MMSI are unique (492 unique values)
- ✅ All tail numbers are unique
- ✅ All operators exist in organizations table
- ✅ All home bases/ports exist in locations table
- ✅ Operational envelopes within realistic ranges
- ✅ Relationships reference valid entity IDs

### Realism Features

- Real aircraft/ship specifications (F-15E: max speed 1,650kts @ 60,000ft)
- Realistic operator assignments (United Airlines operates 737s, not F-22s)
- Country-appropriate tail numbers (N-numbers for USA, G-prefix for UK)
- Squadron groupings (aircraft from same unit fly together)
- Carrier groups (destroyers escort carriers)
- Tanker-receiver patterns (KC-135s refuel fighters)

## Ground Truth for Testing

The `ground_truth_patterns.json` file contains known patterns that can be used to validate:

1. **Knowledge generation queries** (S15-S18):
   - Aircraft pairs should cluster correctly
   - Co-occurrence counts should match expectations

2. **Pattern detection**:
   - Squadron formations should be discoverable
   - Carrier groups should be identifiable
   - Tanker-receiver relationships should emerge

3. **Query correctness**:
   - Multi-hop queries should find expected paths
   - Relationship counts should match activity log

## File Formats

All files use JSON format with consistent structure:

### Entities
```json
{
  "id": 1,
  "mode_s": "A1B2C3",
  "tail_number": "N12345",
  "shark_name": "Boeing 737-800 (N12345)",
  "operator": "United Airlines",
  "operator_id": 42,
  "home_base_id": 15,
  "curator_modified": false,
  "curator_locked": false,
  "created_at": "2026-01-04T12:00:00Z"
}
```

### Relationships
```json
{
  "id": 1,
  "source_domain": "AIR",
  "source_id": 1,
  "target_domain": "ORGANIZATION",
  "target_id": 42,
  "relationship_type": "OPERATED_BY",
  "properties": {"since": "2026-01-04T12:00:00Z"},
  "confidence": 1.0
}
```

### Activities
```json
{
  "track_id": "AIR_1_2_5",
  "domain": "AIR",
  "event_type": "co_located",
  "activity_type": "CO_OCCURRENCE",
  "kb_object_id": 1,
  "mode_s": "A1B2C3",
  "event_timestamp": "2025-12-15T14:30:00Z",
  "properties": {"activity": "FORMATION_FLIGHT"},
  "associated_kb_ids": [1, 2]
}
```

## Notes

- **No real identifiers**: All Mode-S, MMSI, tail numbers, and IMO numbers are fictional
- **Real specs**: Aircraft and ship specifications are accurate for their types
- **90-day window**: Activities span from 90 days ago to present
- **Deterministic with randomness**: Run scripts multiple times to get different datasets
- **Memory usage**: Aircraft instance generation peaks at ~500MB RAM
