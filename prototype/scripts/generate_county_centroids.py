#!/usr/bin/env python3
"""Generate a cleaned county centroids CSV/JSON from provided raw CSVs.

This script reads `raw_data/cnty_counts_cov.csv` for centroids (Geolocation)
and `raw_data/counties.csv` for name/state lookups. It writes
`prototype/data/county_centroids.csv` and `prototype/data/county_lookup.json`.
"""
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "raw_data"
OUT_DIR = ROOT / "prototype" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_point(pt):
    if pd.isna(pt):
        return None, None
    m = re.search(r"POINT\s*\(([-0-9\.]+)\s+([-0-9\.]+)\)", str(pt))
    if not m:
        return None, None
    lon = float(m.group(1))
    lat = float(m.group(2))
    return lat, lon


def main():
    cov_path = RAW / "cnty_counts_cov.csv"
    cnt_path = RAW / "counties.csv"

    if not cov_path.exists():
        print(f"Missing {cov_path}", file=sys.stderr)
        sys.exit(1)

    print("Reading cnty_counts_cov.csv (centroids)...")
    df_cov = pd.read_csv(cov_path, dtype=str, engine="python", on_bad_lines="skip")

    # Normalize FIPS column
    fips_cols = [c for c in df_cov.columns if c.lower() in ("fips", "geoid")]
    if not fips_cols:
        print("No FIPS-like column found in cnty_counts_cov.csv", file=sys.stderr)
        sys.exit(1)
    fcol = fips_cols[0]
    df_cov["fips"] = df_cov[fcol].astype(str).str.zfill(5)

    # Try to get population column
    pop_cols = [c for c in df_cov.columns if c.lower() in ("totalpopulation", "population", "totpop")]
    pop_col = pop_cols[0] if pop_cols else None
    if pop_col:
        df_cov["population"] = pd.to_numeric(df_cov[pop_col], errors="coerce")
    else:
        df_cov["population"] = None

    # Parse Geolocation column
    geo_cols = [c for c in df_cov.columns if "geo" in c.lower() or "location" in c.lower()]
    geo_col = geo_cols[0] if geo_cols else None
    if geo_col is None:
        print("No Geolocation-like column found in cnty_counts_cov.csv; skipping lat/lon", file=sys.stderr)
        df_cov["lat"] = None
        df_cov["lon"] = None
    else:
        latlons = df_cov[geo_col].apply(parse_point)
        df_cov["lat"] = latlons.apply(lambda x: x[0])
        df_cov["lon"] = latlons.apply(lambda x: x[1])

    # Read counties.csv for NAME / STUSPS
    names = {}
    if cnt_path.exists():
        print("Reading counties.csv for name/state lookup (tolerant parser)")
        try:
            df_cnt = pd.read_csv(cnt_path, dtype=str, engine="python", on_bad_lines="skip")
            # find columns
            geoid_cols = [c for c in df_cnt.columns if c.lower() in ("geoid", "fips")]
            name_cols = [c for c in df_cnt.columns if c.lower() in ("name", "county_name")]
            state_cols = [c for c in df_cnt.columns if c.lower() in ("stusps", "state", "st")]
            if geoid_cols and name_cols:
                gcol = geoid_cols[0]
                ncol = name_cols[0]
                scol = state_cols[0] if state_cols else None
                for _, r in df_cnt.iterrows():
                    g = str(r.get(gcol)) if pd.notna(r.get(gcol)) else None
                    if not g:
                        continue
                    g = g.zfill(5)
                    names[g] = {
                        "name": r.get(ncol) if pd.notna(r.get(ncol)) else None,
                        "state": (r.get(scol) if scol and pd.notna(r.get(scol)) else None) if scol else None,
                    }
        except Exception as e:
            print("Failed to parse counties.csv:", e, file=sys.stderr)

    # Merge to produce output mapping
    out_rows = []
    for _, r in df_cov.iterrows():
        f = str(r.get("fips")) if pd.notna(r.get("fips")) else None
        if not f:
            continue
        name = None
        state = None
        if f in names:
            name = names[f].get("name")
            state = names[f].get("state")
        # Fallbacks
        if not name:
            # try columns that might contain county name in df_cov
            candidate_cols = [c for c in df_cov.columns if "county" in c.lower() or c.lower() == "name"]
            for c in candidate_cols:
                val = r.get(c)
                if pd.notna(val):
                    name = val
                    break
        if not name:
            name = f

        lat = r.get("lat")
        lon = r.get("lon")
        pop = r.get("population")

        try:
            lat = float(lat) if pd.notna(lat) else None
            lon = float(lon) if pd.notna(lon) else None
        except Exception:
            lat = None
            lon = None

        try:
            pop = int(float(pop)) if pop is not None and str(pop) != "nan" else None
        except Exception:
            pop = None

        out_rows.append({
            "fips": f,
            "name": name,
            "state": state,
            "lat": lat,
            "lon": lon,
            "population": pop,
        })

    out_df = pd.DataFrame(out_rows)
    out_csv = OUT_DIR / "county_centroids.csv"
    out_json = OUT_DIR / "county_lookup.json"
    out_df.to_csv(out_csv, index=False)
    lookup = {r["fips"]: {"name": r["name"], "state": r["state"], "lat": r["lat"], "lon": r["lon"], "population": r["population"]} for r in out_rows}
    with open(out_json, "w") as fh:
        json.dump(lookup, fh, indent=2)

    print(f"Wrote {out_csv} and {out_json} with {len(out_rows)} rows")


if __name__ == "__main__":
    main()
