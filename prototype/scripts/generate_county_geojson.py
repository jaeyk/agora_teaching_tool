#!/usr/bin/env python3
"""Convert raw_data/counties.gpkg to prototype/data/counties.geojson.

This script attempts to import geopandas. If missing, it prints instructions
for installing geopandas and exits with a non-zero code.
"""
import sys
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'raw_data'
OUT = ROOT / 'prototype' / 'data'
OUT.mkdir(parents=True, exist_ok=True)


def main():
    gpkg = RAW / 'counties.gpkg'
    out = OUT / 'counties.geojson'
    if not gpkg.exists():
        print(f"Missing {gpkg}")
        sys.exit(1)
    try:
        import geopandas as gpd
    except Exception:
        print("geopandas not installed. To install, run:\n  pip install geopandas fiona rtree shapely\n")
        sys.exit(2)

    print(f"Reading {gpkg}...")
    gdf = gpd.read_file(str(gpkg))
    # ensure GEOID is string and zero-padded
    if 'GEOID' in gdf.columns:
        gdf['GEOID'] = gdf['GEOID'].astype(str).str.zfill(5)

    print(f"Writing {out} ({len(gdf)} features)...")
    gdf.to_file(str(out), driver='GeoJSON')
    print("Done.")


if __name__ == '__main__':
    main()
