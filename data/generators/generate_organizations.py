#!/usr/bin/env python3
"""
Organization Generator for Shark Bake-Off
Generates ~500 organizations (military, commercial airlines, shipping companies)
"""

import json
from typing import List, Dict
from datetime import datetime


def generate_military_organizations() -> List[Dict]:
    """Generate military organizations with hierarchy"""
    orgs = []

    # US Military
    us_military = [
        {"name": "US Department of Defense", "org_type": "MILITARY", "country": "USA", "parent": None},
        {"name": "US Air Force", "org_type": "MILITARY", "country": "USA", "parent": "US Department of Defense"},
        {"name": "US Navy", "org_type": "MILITARY", "country": "USA", "parent": "US Department of Defense"},
        {"name": "US Marine Corps", "org_type": "MILITARY", "country": "USA", "parent": "US Department of Defense"},
        {"name": "US Army", "org_type": "MILITARY", "country": "USA", "parent": "US Department of Defense"},
        {"name": "US Coast Guard", "org_type": "MILITARY", "country": "USA", "parent": "US Department of Homeland Security"},

        # USAF Wings
        {"name": "1st Fighter Wing", "org_type": "MILITARY", "country": "USA", "parent": "US Air Force"},
        {"name": "4th Fighter Wing", "org_type": "MILITARY", "country": "USA", "parent": "US Air Force"},
        {"name": "20th Fighter Wing", "org_type": "MILITARY", "country": "USA", "parent": "US Air Force"},
        {"name": "27th Special Operations Wing", "org_type": "MILITARY", "country": "USA", "parent": "US Air Force"},
        {"name": "48th Fighter Wing", "org_type": "MILITARY", "country": "USA", "parent": "US Air Force"},
        {"name": "366th Fighter Wing", "org_type": "MILITARY", "country": "USA", "parent": "US Air Force"},
        {"name": "509th Bomb Wing", "org_type": "MILITARY", "country": "USA", "parent": "US Air Force"},
        {"name": "62nd Airlift Wing", "org_type": "MILITARY", "country": "USA", "parent": "US Air Force"},

        # US Navy
        {"name": "US Fleet Forces Command", "org_type": "MILITARY", "country": "USA", "parent": "US Navy"},
        {"name": "US Pacific Fleet", "org_type": "MILITARY", "country": "USA", "parent": "US Navy"},
        {"name": "Carrier Strike Group 1", "org_type": "MILITARY", "country": "USA", "parent": "US Pacific Fleet"},
        {"name": "Carrier Strike Group 3", "org_type": "MILITARY", "country": "USA", "parent": "US Pacific Fleet"},
        {"name": "Carrier Strike Group 5", "org_type": "MILITARY", "country": "USA", "parent": "US Pacific Fleet"},
        {"name": "Carrier Strike Group 9", "org_type": "MILITARY", "country": "USA", "parent": "US Pacific Fleet"},
        {"name": "Destroyer Squadron 15", "org_type": "MILITARY", "country": "USA", "parent": "US Pacific Fleet"},
        {"name": "VFA-41 Black Aces", "org_type": "MILITARY", "country": "USA", "parent": "US Navy"},
        {"name": "VFA-115 Eagles", "org_type": "MILITARY", "country": "USA", "parent": "US Navy"},
    ]

    # Allied Forces
    allied = [
        {"name": "Royal Air Force", "org_type": "MILITARY", "country": "GBR", "parent": None},
        {"name": "RAF Lakenheath", "org_type": "MILITARY", "country": "GBR", "parent": "Royal Air Force"},
        {"name": "Royal Navy", "org_type": "MILITARY", "country": "GBR", "parent": None},
        {"name": "French Air and Space Force", "org_type": "MILITARY", "country": "FRA", "parent": None},
        {"name": "French Navy", "org_type": "MILITARY", "country": "FRA", "parent": None},
        {"name": "German Air Force", "org_type": "MILITARY", "country": "DEU", "parent": None},
        {"name": "Israeli Air Force", "org_type": "MILITARY", "country": "ISR", "parent": None},
        {"name": "Japan Air Self-Defense Force", "org_type": "MILITARY", "country": "JPN", "parent": None},
        {"name": "Japan Maritime Self-Defense Force", "org_type": "MILITARY", "country": "JPN", "parent": None},
        {"name": "Republic of Korea Air Force", "org_type": "MILITARY", "country": "KOR", "parent": None},
        {"name": "Royal Australian Air Force", "org_type": "MILITARY", "country": "AUS", "parent": None},
        {"name": "Royal Australian Navy", "org_type": "MILITARY", "country": "AUS", "parent": None},
        {"name": "Royal Saudi Air Force", "org_type": "MILITARY", "country": "SAU", "parent": None},
        {"name": "Italian Air Force", "org_type": "MILITARY", "country": "ITA", "parent": None},
        {"name": "Spanish Air Force", "org_type": "MILITARY", "country": "ESP", "parent": None},
    ]

    orgs.extend(us_military)
    orgs.extend(allied)

    return orgs


def generate_commercial_airlines() -> List[Dict]:
    """Generate commercial airline organizations"""
    airlines = [
        # US Major Airlines
        {"name": "United Airlines", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "American Airlines", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "Delta Air Lines", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "Southwest Airlines", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "Alaska Airlines", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "JetBlue Airways", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "Spirit Airlines", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "Frontier Airlines", "org_type": "CIVILIAN", "country": "USA", "parent": None},

        # International Airlines
        {"name": "British Airways", "org_type": "CIVILIAN", "country": "GBR", "parent": None},
        {"name": "Lufthansa", "org_type": "CIVILIAN", "country": "DEU", "parent": None},
        {"name": "Air France", "org_type": "CIVILIAN", "country": "FRA", "parent": None},
        {"name": "Emirates", "org_type": "CIVILIAN", "country": "ARE", "parent": None},
        {"name": "Qatar Airways", "org_type": "CIVILIAN", "country": "QAT", "parent": None},
        {"name": "Singapore Airlines", "org_type": "CIVILIAN", "country": "SGP", "parent": None},
        {"name": "Cathay Pacific", "org_type": "CIVILIAN", "country": "HKG", "parent": None},
        {"name": "Japan Airlines", "org_type": "CIVILIAN", "country": "JPN", "parent": None},
        {"name": "ANA", "org_type": "CIVILIAN", "country": "JPN", "parent": None},
        {"name": "Korean Air", "org_type": "CIVILIAN", "country": "KOR", "parent": None},
        {"name": "Qantas", "org_type": "CIVILIAN", "country": "AUS", "parent": None},
        {"name": "Air Canada", "org_type": "CIVILIAN", "country": "CAN", "parent": None},

        # Cargo Airlines
        {"name": "FedEx Express", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "UPS Airlines", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "DHL Aviation", "org_type": "CIVILIAN", "country": "DEU", "parent": None},

        # Business Aviation
        {"name": "NetJets", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "Flexjet", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "VistaJet", "org_type": "CIVILIAN", "country": "MLT", "parent": None},
    ]

    return airlines


def generate_shipping_companies() -> List[Dict]:
    """Generate shipping company organizations"""
    shipping = [
        # Container Shipping
        {"name": "Maersk Line", "org_type": "CIVILIAN", "country": "DNK", "parent": None},
        {"name": "Mediterranean Shipping Company", "org_type": "CIVILIAN", "country": "CHE", "parent": None},
        {"name": "CMA CGM", "org_type": "CIVILIAN", "country": "FRA", "parent": None},
        {"name": "COSCO Shipping", "org_type": "CIVILIAN", "country": "CHN", "parent": None},
        {"name": "Hapag-Lloyd", "org_type": "CIVILIAN", "country": "DEU", "parent": None},
        {"name": "Ocean Network Express", "org_type": "CIVILIAN", "country": "JPN", "parent": None},
        {"name": "Evergreen Marine", "org_type": "CIVILIAN", "country": "TWN", "parent": None},
        {"name": "Yang Ming Marine", "org_type": "CIVILIAN", "country": "TWN", "parent": None},

        # Oil Tankers
        {"name": "Euronav", "org_type": "CIVILIAN", "country": "BEL", "parent": None},
        {"name": "Frontline", "org_type": "CIVILIAN", "country": "NOR", "parent": None},
        {"name": "Teekay Corporation", "org_type": "CIVILIAN", "country": "CAN", "parent": None},
        {"name": "DHT Holdings", "org_type": "CIVILIAN", "country": "NOR", "parent": None},
        {"name": "International Seaways", "org_type": "CIVILIAN", "country": "USA", "parent": None},

        # LNG Carriers
        {"name": "Qatargas", "org_type": "CIVILIAN", "country": "QAT", "parent": None},
        {"name": "Maran Gas Maritime", "org_type": "CIVILIAN", "country": "GRC", "parent": None},
        {"name": "GasLog", "org_type": "CIVILIAN", "country": "GRC", "parent": None},

        # Bulk Carriers
        {"name": "Star Bulk Carriers", "org_type": "CIVILIAN", "country": "GRC", "parent": None},
        {"name": "Seanergy Maritime", "org_type": "CIVILIAN", "country": "GRC", "parent": None},
        {"name": "Scorpio Bulkers", "org_type": "CIVILIAN", "country": "MCO", "parent": None},

        # Cruise Lines
        {"name": "Carnival Cruise Line", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "Royal Caribbean", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "Norwegian Cruise Line", "org_type": "CIVILIAN", "country": "USA", "parent": None},
        {"name": "MSC Cruises", "org_type": "CIVILIAN", "country": "CHE", "parent": None},
    ]

    return shipping


def generate_general_aviation() -> List[Dict]:
    """Generate general aviation operators"""
    ga = []

    # Flight Schools
    for i in range(1, 51):
        ga.append({
            "name": f"Flight School {i}",
            "org_type": "CIVILIAN",
            "country": "USA",
            "parent": None
        })

    # Corporate Operators
    corporate = [
        "Coca-Cola Aviation",
        "Walmart Aviation",
        "Amazon Air Operations",
        "Google Aviation",
        "Apple Corporate Aviation",
        "Microsoft Flight Operations",
        "ExxonMobil Aviation",
        "Bank of America Flight",
        "Wells Fargo Aviation",
        "JPMorgan Aviation",
    ]

    for corp in corporate:
        ga.append({
            "name": corp,
            "org_type": "CIVILIAN",
            "country": "USA",
            "parent": None
        })

    return ga


def main():
    """Generate all organizations"""
    organizations = []

    print("Generating organizations...")

    organizations.extend(generate_military_organizations())
    print(f"  Military: {len([o for o in organizations if o['org_type'] == 'MILITARY'])}")

    organizations.extend(generate_commercial_airlines())
    organizations.extend(generate_shipping_companies())
    organizations.extend(generate_general_aviation())
    print(f"  Civilian: {len([o for o in organizations if o['org_type'] == 'CIVILIAN'])}")

    print(f"  Total: {len(organizations)}")

    # Add IDs and timestamps
    for i, org in enumerate(organizations, 1):
        org['id'] = i
        org['created_at'] = datetime.utcnow().isoformat() + 'Z'

    # Write to file
    output_file = '../sample/organizations.json'
    with open(output_file, 'w') as f:
        json.dump(organizations, f, indent=2)

    print(f"\nGenerated {len(organizations)} organizations -> {output_file}")

    # Print sample
    print("\nSample organizations:")
    for org in organizations[:5]:
        print(f"  {org['id']}: {org['name']} ({org['country']}, {org['org_type']})")


if __name__ == '__main__':
    main()
