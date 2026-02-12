#!/usr/bin/env python3
"""Build static JSON for Quarto Civic Quest page.

Output:
- prototype/data/civic_quest_data.json

Optional RUCC file:
- raw_data/rucc_county.csv
  Supported columns: FIPS/geoid and RUCC_2023/RUCC_2013/rucc/code.
"""

from pathlib import Path
import json
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "raw_data"
PROTOTYPE_DATA = ROOT / "prototype" / "data"
PROTOTYPE_DATA.mkdir(parents=True, exist_ok=True)


def parse_point(value):
    if pd.isna(value):
        return None, None
    m = re.search(r"POINT\s*\(([\-0-9\.]+)\s+([\-0-9\.]+)\)", str(value))
    if not m:
        return None, None
    return float(m.group(2)), float(m.group(1))


def safe_int(value, default=0):
    try:
        if value in (None, "", "nan"):
            return default
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default=0.0):
    try:
        if value in (None, "", "nan"):
            return default
        return float(value)
    except Exception:
        return default


def load_rucc_lookup():
    candidate_paths = [
        RAW / "County_Classifications.csv",
        Path("/Users/jaeyeonkim/Documents/map_civic_opportunity/raw_data/County_Classifications.csv"),
        RAW / "rucc_county.csv",
    ]
    rucc_path = next((p for p in candidate_paths if p.exists()), None)
    if rucc_path is None:
        return {}, None

    try:
        rucc = pd.read_csv(rucc_path, dtype=str)
    except UnicodeDecodeError:
        rucc = pd.read_csv(rucc_path, dtype=str, encoding="latin-1")
    cols = {c.lower(): c for c in rucc.columns}
    fips_col = cols.get("fipstxt") or cols.get("fips") or cols.get("geoid")
    code_col = (
        cols.get("ruralurbancontinuumcode2013")
        or cols.get("rucc_2023")
        or cols.get("rucc_2013")
        or cols.get("rucc")
        or cols.get("code")
    )
    if not fips_col or not code_col:
        return {}, None

    rucc[fips_col] = rucc[fips_col].astype(str).str.zfill(5)
    rucc["rucc_code"] = pd.to_numeric(rucc[code_col], errors="coerce")
    rucc = rucc.dropna(subset=["rucc_code"])
    return ({str(r[fips_col]).zfill(5): int(r["rucc_code"]) for _, r in rucc.iterrows()}, str(rucc_path))


def classify_urbanicity(cnty_df):
    rucc_lookup, rucc_source_path = load_rucc_lookup()
    if rucc_lookup:
        def from_rucc(fips):
            code = rucc_lookup.get(str(fips).zfill(5))
            if code is None:
                return None
            if code <= 3:
                return "Urban"
            if code <= 7:
                return "Suburban"
            return "Rural"

        labels = cnty_df["FIPS"].apply(from_rucc)
        if labels.notna().sum() > 0:
            return labels.fillna("Suburban"), f"RUCC ({rucc_source_path})"

    q = cnty_df["population"].quantile([0.33, 0.67]).to_dict()
    q1 = q.get(0.33, 30000)
    q2 = q.get(0.67, 120000)

    def from_population(pop):
        if pop <= q1:
            return "Rural"
        if pop <= q2:
            return "Suburban"
        return "Urban"

    return cnty_df["population"].apply(from_population), "Population tertiles (fallback)"


def build_org_map(civic_df):
    work = civic_df.copy()
    work = work[(work["fips"].notna()) & (work["fips"] != "NA")]
    work["fips"] = work["fips"].astype(str).str.zfill(5)
    work["n_num"] = pd.to_numeric(work["n"], errors="coerce").fillna(0)

    grouped = work.groupby(["fips", "class"], as_index=False)["n_num"].sum()
    out = {}
    for fips, grp in grouped.groupby("fips"):
        top = grp.sort_values("n_num", ascending=False).head(5)
        out[fips] = [
            {"class": str(r["class"]), "count": int(r["n_num"]) }
            for _, r in top.iterrows()
        ]
    return out


def main():
    cnty = pd.read_csv(RAW / "cnty_counts_cov.csv", dtype=str, engine="python")
    civic = pd.read_csv(RAW / "cnty_civic_type_dashboard.csv", dtype=str, engine="python")

    lookup = {}
    lookup_path = PROTOTYPE_DATA / "county_lookup.json"
    if lookup_path.exists():
        with open(lookup_path, "r") as f:
            lookup = json.load(f)

    cnty["FIPS"] = cnty["FIPS"].astype(str).str.zfill(5)
    cnty["population"] = cnty["TotalPopulation"].apply(safe_int)
    cnty["score"] = cnty["civic_opp_sum_normalized"].apply(safe_float)
    cnty["n_num"] = cnty["n"].apply(safe_int)
    cnty["civic_org_sum_num"] = cnty["civic_org_sum"].apply(safe_int)
    cnty["membership_sum_num"] = cnty["membership_sum"].apply(safe_float)
    cnty["volunteer_sum_num"] = cnty["volunteer_sum"].apply(safe_float)
    cnty["events_sum_num"] = cnty["events_sum"].apply(safe_float)
    cnty["take_action_sum_num"] = cnty["take_action_sum"].apply(safe_float)

    lat_lons = cnty["Geolocation"].apply(parse_point)
    cnty["lat"] = lat_lons.apply(lambda x: x[0])
    cnty["lon"] = lat_lons.apply(lambda x: x[1])

    cnty["county_name"] = cnty["FIPS"].apply(lambda f: (lookup.get(f, {}) or {}).get("name"))
    cnty["state_abbr"] = cnty["FIPS"].apply(lambda f: (lookup.get(f, {}) or {}).get("state"))
    cnty["state_abbr"] = cnty["state_abbr"].fillna(cnty["state"])
    cnty = cnty[cnty["county_name"].notna()].copy()

    cnty["urbanicity"], urbanicity_source = classify_urbanicity(cnty)

    cnty["state_rank"] = cnty.groupby("state_abbr")["score"].rank(ascending=False, method="min").astype(int)
    cnty["national_rank"] = cnty["score"].rank(ascending=False, method="min").astype(int)
    cnty["national_percentile"] = (cnty["score"].rank(pct=True) * 100).round(1)

    org_map = build_org_map(civic)

    county_rows = []
    for _, r in cnty.iterrows():
        county_rows.append({
            "fips": str(r["FIPS"]),
            "name": str(r["county_name"]),
            "state": str(r["state_abbr"]),
            "population": int(r["population"]),
            "score": round(float(r["score"]), 2),
            "urbanicity": str(r["urbanicity"]),
            "state_rank": int(r["state_rank"]),
            "national_rank": int(r["national_rank"]),
            "national_percentile": float(r["national_percentile"]),
            "lat": r["lat"],
            "lon": r["lon"],
            "metrics": {
                "membership": float(r["membership_sum_num"]),
                "volunteer": float(r["volunteer_sum_num"]),
                "events": float(r["events_sum_num"]),
                "take_action": float(r["take_action_sum_num"]),
                "civic_orgs": float(r["civic_org_sum_num"]),
                "nonprofits": float(r["n_num"]),
            },
            "org_types": org_map.get(str(r["FIPS"]), []),
        })

    # peers: 5 nearest scores in same state + urbanicity
    county_df = pd.DataFrame(county_rows)
    county_df["score_num"] = county_df["score"].astype(float)
    peers_map = {}
    for _, row in county_df.iterrows():
        mask = (
            (county_df["state"] == row["state"])
            & (county_df["urbanicity"] == row["urbanicity"])
            & (county_df["fips"] != row["fips"])
        )
        peers = county_df[mask].copy()
        peers["gap"] = (peers["score_num"] - row["score_num"]).abs()
        peers = peers.sort_values("gap").head(5)
        peers_map[row["fips"]] = [
            {
                "fips": str(p["fips"]),
                "name": str(p["name"]),
                "state": str(p["state"]),
                "score": round(float(p["score"]), 2),
                "urbanicity": str(p["urbanicity"]),
            }
            for _, p in peers.iterrows()
        ]

    for row in county_rows:
        row["peers"] = peers_map.get(row["fips"], [])

    state_rows = []
    for st, grp in county_df.groupby("state"):
        by_class = grp.groupby("urbanicity")["score_num"].mean().to_dict()
        cls_counts = grp["urbanicity"].value_counts().to_dict()
        top = grp.sort_values("score_num", ascending=False).iloc[0]
        state_rows.append({
            "state": st,
            "county_count": int(len(grp)),
            "avg_score": round(float(grp["score_num"].mean()), 2),
            "urban_avg": round(float(by_class.get("Urban", 0.0)), 2),
            "suburban_avg": round(float(by_class.get("Suburban", 0.0)), 2),
            "rural_avg": round(float(by_class.get("Rural", 0.0)), 2),
            "urban_count": int(cls_counts.get("Urban", 0)),
            "suburban_count": int(cls_counts.get("Suburban", 0)),
            "rural_count": int(cls_counts.get("Rural", 0)),
            "top_county": str(top["name"]),
            "top_county_score": round(float(top["score_num"]), 2),
        })

    payload = {
        "metadata": {
            "urbanicity_source": urbanicity_source,
            "county_count": len(county_rows),
            "state_count": len(state_rows),
        },
        "states": sorted(state_rows, key=lambda x: x["state"]),
        "counties": county_rows,
    }

    out_paths = [
        PROTOTYPE_DATA / "civic_quest_data.json",
        ROOT / "data" / "civic_quest_data.json",
    ]
    for path in out_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(payload, f)

    print(
        f"Wrote {len(out_paths)} files with {len(county_rows)} counties and {len(state_rows)} states: "
        + ", ".join(str(p) for p in out_paths)
    )


if __name__ == "__main__":
    main()
