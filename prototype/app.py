from flask import Flask, jsonify, request, send_from_directory
import pandas as pd
import os
import re
import json

HERE = os.path.abspath(os.path.dirname(__file__))
RAW = os.path.join(HERE, '..', 'raw_data')

app = Flask(__name__, static_folder='static')


def load_data():
    # load minimal datasets for the prototype
    cnty = pd.read_csv(os.path.join(RAW, 'cnty_counts_cov.csv'), dtype=str, engine='python')
    civic = pd.read_csv(os.path.join(RAW, 'cnty_civic_type_dashboard.csv'), dtype=str, engine='python')
    counties = pd.read_csv(os.path.join(RAW, 'counties.csv'), dtype=str, engine='python', on_bad_lines='skip')

    # normalize column names
    cnty.columns = [c.strip() for c in cnty.columns]
    civic.columns = [c.strip() for c in civic.columns]
    counties.columns = [c.strip() for c in counties.columns]

    # extract lat/lon from Geolocation (POINT (lon lat))
    def parse_point(s):
        if pd.isna(s):
            return None, None
        m = re.search(r"POINT \(([\-0-9\.]+)\s+([\-0-9\.]+)\)", s)
        if m:
            lon = float(m.group(1))
            lat = float(m.group(2))
            return lat, lon
        return None, None

    cnty['lat'] = None
    cnty['lon'] = None
    for i, row in cnty.iterrows():
        lat, lon = parse_point(row.get('Geolocation', ''))
        cnty.at[i, 'lat'] = lat
        cnty.at[i, 'lon'] = lon

    # map fips -> name/state using counties.csv (GEOID -> NAME)
    name_map = {}
    st_map = {}
    # try to use precomputed lookup (prototype/data/county_lookup.json) if present
    lookup_path = os.path.join(HERE, 'data', 'county_lookup.json')
    if os.path.exists(lookup_path):
        try:
            with open(lookup_path, 'r') as fh:
                lookup = json.load(fh)
            for geoid, info in lookup.items():
                name_map[str(geoid).zfill(5)] = info.get('name')
                st_map[str(geoid).zfill(5)] = info.get('state')
        except Exception:
            # fallback to parsing counties.csv
            pass

    if not name_map:
        for _, r in counties.iterrows():
            geoid = r.get('GEOID')
            if pd.notna(geoid):
                name_map[str(geoid).zfill(5)] = r.get('NAME')
                st_map[str(geoid).zfill(5)] = r.get('STUSPS')

    # also expose the raw lookup if available
    lookup_dict = {}
    lp = os.path.join(HERE, 'data', 'county_lookup.json')
    if os.path.exists(lp):
        try:
            with open(lp, 'r') as fh:
                lookup_dict = json.load(fh)
        except Exception:
            lookup_dict = {}

    return cnty, civic, name_map, st_map, lookup_dict


cnty_df, civic_df, NAME_MAP, ST_MAP, LOOKUP = load_data()


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/data/<path:filename>')
def data_file(filename):
    # serve files from prototype/data (geojson, lookup, etc.)
    return send_from_directory('data', filename)


@app.route('/api/search')
def search():
    q = request.args.get('q', '').strip().lower()
    if not q:
        return jsonify([])
    df = cnty_df
    # match by county name or state
    results = []
    for _, r in df.iterrows():
        fips = str(r['FIPS']).zfill(5)
        # prefer lookup data for display and coords
        lu = LOOKUP.get(fips, {})
        name = lu.get('name') or NAME_MAP.get(fips, '')
        state = lu.get('state') or r.get('state', '')
        display = f"{name}, {state}" if name else fips
        lat = lu.get('lat') or r.get('lat')
        lon = lu.get('lon') or r.get('lon')
        pop = lu.get('population') or r.get('TotalPopulation')
        try:
            pop = int(float(pop)) if pop not in (None, '', 'nan') else 0
        except Exception:
            pop = 0
        if q in (name or '').lower() or q in (state or '').lower() or q in fips:
            results.append({
                'fips': fips,
                'display': display,
                'population': pop,
                'lat': lat,
                'lon': lon
            })
        if len(results) >= 12:
            break
    return jsonify(results)


@app.route('/api/county/<fips>')
def county(fips):
    f = str(fips).zfill(5)
    row = cnty_df[cnty_df['FIPS'] == f]
    if row.empty:
        return jsonify({'error': 'not found'}), 404
    r = row.iloc[0].to_dict()

    # civic breakdown
    civ = civic_df[civic_df['fips'] == f]
    types = []
    if not civ.empty:
        grp = civ.groupby('class', as_index=False).agg({'n': lambda s: int(s.astype(float).sum())})
        for _, g in grp.iterrows():
            types.append({'class': g['class'], 'count': int(g['n'])})

    # prefer lookup values when available
    lu = LOOKUP.get(f, {})
    population = lu.get('population') or r.get('TotalPopulation')
    try:
        population = int(float(population)) if population not in (None, '', 'nan') else 0
    except Exception:
        population = 0

    data = {
        'fips': f,
        'name': lu.get('name') or NAME_MAP.get(f, ''),
        'state': lu.get('state') or ST_MAP.get(f, r.get('state')),
        'population': population,
        'metrics': {
            'civic_org_sum': float(r.get('civic_org_sum') or 0),
            'volunteer_sum': float(r.get('volunteer_sum') or 0),
            'events_sum': float(r.get('events_sum') or 0),
            'membership_sum': float(r.get('membership_sum') or 0),
        },
        'lat': lu.get('lat') or r.get('lat'),
        'lon': lu.get('lon') or r.get('lon'),
        'org_types': types
    }
    return jsonify(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
