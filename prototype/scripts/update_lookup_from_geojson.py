#!/usr/bin/env python3
"""Update prototype/data/county_lookup.json using names/states from counties.geojson.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'prototype' / 'data'
LOOKUP = DATA / 'county_lookup.json'
GEO = DATA / 'counties.geojson'


def main():
    if not LOOKUP.exists():
        print(f"Missing {LOOKUP}")
        return
    if not GEO.exists():
        print(f"Missing {GEO}")
        return
    with open(LOOKUP, 'r') as fh:
        lookup = json.load(fh)
    with open(GEO, 'r') as fh:
        gj = json.load(fh)
    count = 0
    for feat in gj.get('features', []):
        props = feat.get('properties', {})
        geoid = props.get('GEOID') or props.get('geoid') or props.get('AFFGEOID')
        if not geoid:
            continue
        geoid = str(geoid).zfill(5)
        name = props.get('NAME') or props.get('name') or None
        state = props.get('STUSPS') or props.get('STUSPS') or props.get('STATE_NAME') or None
        if geoid in lookup:
            if name:
                lookup[geoid]['name'] = name
            if state:
                lookup[geoid]['state'] = state
            count += 1

    with open(LOOKUP, 'w') as fh:
        json.dump(lookup, fh, indent=2)
    print(f"Updated {LOOKUP} with names/states for {count} GEOIDs")


if __name__ == '__main__':
    main()
