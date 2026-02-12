from flask import Flask, jsonify, request, send_from_directory
import pandas as pd
import os
import re
import json

HERE = os.path.abspath(os.path.dirname(__file__))
RAW = os.path.join(HERE, '..', 'raw_data')

app = Flask(__name__, static_folder='static')


def parse_point(value):
    if pd.isna(value):
        return None, None
    m = re.search(r"POINT\s*\(([\-0-9\.]+)\s+([\-0-9\.]+)\)", str(value))
    if not m:
        return None, None
    return float(m.group(2)), float(m.group(1))


def safe_int(value, default=0):
    try:
        if value in (None, '', 'nan'):
            return default
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default=0.0):
    try:
        if value in (None, '', 'nan'):
            return default
        return float(value)
    except Exception:
        return default


def build_org_type_map(civic_df):
    work = civic_df.copy()
    work = work[(work['fips'].notna()) & (work['fips'] != 'NA')]
    work['fips'] = work['fips'].astype(str).str.zfill(5)
    work['n_num'] = pd.to_numeric(work['n'], errors='coerce').fillna(0)

    grouped = (
        work.groupby(['fips', 'class'], as_index=False)['n_num']
        .sum()
        .rename(columns={'n_num': 'count'})
    )

    out = {}
    for fips, grp in grouped.groupby('fips'):
        sorted_grp = grp.sort_values('count', ascending=False)
        out[fips] = [
            {'class': str(row['class']), 'count': int(row['count'])}
            for _, row in sorted_grp.iterrows()
        ]
    return out


def load_rucc_lookup():
    # Optional RUCC mapping file. If absent, caller should fall back.
    # Primary source expected from user:
    # County_Classifications.csv with columns:
    # - FIPStxt
    # - RuralUrbanContinuumCode2013
    candidate_paths = [
        os.path.join(RAW, 'County_Classifications.csv'),
        '/Users/jaeyeonkim/Documents/map_civic_opportunity/raw_data/County_Classifications.csv',
        os.path.join(RAW, 'rucc_county.csv'),
    ]

    rucc_path = next((p for p in candidate_paths if os.path.exists(p)), None)
    if not rucc_path:
        return {}, None

    try:
        rucc = pd.read_csv(rucc_path, dtype=str)
    except UnicodeDecodeError:
        rucc = pd.read_csv(rucc_path, dtype=str, encoding='latin-1')
    except Exception:
        return {}, None

    cols = {c.lower(): c for c in rucc.columns}
    fips_col = cols.get('fipstxt') or cols.get('fips') or cols.get('geoid')
    code_col = (
        cols.get('ruralurbancontinuumcode2013')
        or cols.get('rucc_2023')
        or cols.get('rucc_2013')
        or cols.get('rucc')
        or cols.get('code')
    )
    if not fips_col or not code_col:
        return {}, None

    rucc[fips_col] = rucc[fips_col].astype(str).str.zfill(5)
    rucc['rucc_code'] = pd.to_numeric(rucc[code_col], errors='coerce')
    rucc = rucc.dropna(subset=['rucc_code'])

    out = {}
    for _, row in rucc.iterrows():
        out[str(row[fips_col]).zfill(5)] = int(row['rucc_code'])
    return out, rucc_path


def classify_urbanicity(cnty_df):
    rucc_lookup, rucc_source_path = load_rucc_lookup()
    if rucc_lookup:
        # RUCC-based 3-way collapse:
        # 1-3 Urban (metro), 4-7 Suburban (nonmetro adjacent/smaller towns), 8-9 Rural.
        def from_rucc(fips):
            code = rucc_lookup.get(str(fips).zfill(5))
            if code is None:
                return None
            if code <= 3:
                return 'Urban'
            if code <= 7:
                return 'Suburban'
            return 'Rural'

        labels = cnty_df['FIPS'].apply(from_rucc)
        if labels.notna().sum() > 0:
            return labels.fillna('Suburban'), f'RUCC ({rucc_source_path})'

    # Fallback: population tertiles when RUCC file is unavailable.
    pop_quantiles = cnty_df['population'].quantile([0.33, 0.67]).to_dict()
    q1 = pop_quantiles.get(0.33, 30000)
    q2 = pop_quantiles.get(0.67, 120000)

    def from_population(pop):
        if pop <= q1:
            return 'Rural'
        if pop <= q2:
            return 'Suburban'
        return 'Urban'

    return cnty_df['population'].apply(from_population), 'Population tertiles (fallback)'


def load_data():
    cnty = pd.read_csv(os.path.join(RAW, 'cnty_counts_cov.csv'), dtype=str, engine='python')
    civic = pd.read_csv(os.path.join(RAW, 'cnty_civic_type_dashboard.csv'), dtype=str, engine='python')
    counties = pd.read_csv(os.path.join(RAW, 'counties.csv'), dtype=str, engine='python', on_bad_lines='skip')

    cnty.columns = [c.strip() for c in cnty.columns]
    civic.columns = [c.strip() for c in civic.columns]
    counties.columns = [c.strip() for c in counties.columns]

    cnty['FIPS'] = cnty['FIPS'].astype(str).str.zfill(5)
    cnty['population'] = cnty['TotalPopulation'].apply(safe_int)
    cnty['score'] = cnty['civic_opp_sum_normalized'].apply(safe_float)
    cnty['civic_org_sum_num'] = cnty['civic_org_sum'].apply(safe_int)
    cnty['n_num'] = cnty['n'].apply(safe_int)
    cnty['membership_sum_num'] = cnty['membership_sum'].apply(safe_float)
    cnty['volunteer_sum_num'] = cnty['volunteer_sum'].apply(safe_float)
    cnty['events_sum_num'] = cnty['events_sum'].apply(safe_float)
    cnty['take_action_sum_num'] = cnty['take_action_sum'].apply(safe_float)

    lat_lons = cnty['Geolocation'].apply(parse_point)
    cnty['lat'] = lat_lons.apply(lambda x: x[0])
    cnty['lon'] = lat_lons.apply(lambda x: x[1])

    # lookup maps
    name_map = {}
    st_map = {}
    lookup_path = os.path.join(HERE, 'data', 'county_lookup.json')
    lookup_dict = {}

    if os.path.exists(lookup_path):
        try:
            with open(lookup_path, 'r') as fh:
                lookup_dict = json.load(fh)
            for geoid, info in lookup_dict.items():
                f = str(geoid).zfill(5)
                name_map[f] = info.get('name')
                st_map[f] = info.get('state')
        except Exception:
            lookup_dict = {}

    if not name_map:
        for _, row in counties.iterrows():
            geoid = row.get('GEOID')
            if pd.notna(geoid):
                f = str(geoid).zfill(5)
                name_map[f] = row.get('NAME')
                st_map[f] = row.get('STUSPS')

    cnty['county_name'] = cnty['FIPS'].map(name_map)
    cnty['state_abbr'] = cnty['FIPS'].map(st_map)
    cnty['state_abbr'] = cnty['state_abbr'].fillna(cnty['state'])
    cnty = cnty[cnty['county_name'].notna()].copy()

    cnty['urbanicity'], urbanicity_source = classify_urbanicity(cnty)

    # Rankings
    cnty['national_rank'] = cnty['score'].rank(ascending=False, method='min').astype(int)
    cnty['national_percentile'] = (cnty['score'].rank(pct=True) * 100).round(1)

    cnty['state_rank'] = cnty.groupby('state_abbr')['score'].rank(ascending=False, method='min').astype(int)

    org_map = build_org_type_map(civic)

    # state summary table
    state_rows = []
    for state, grp in cnty.groupby('state_abbr'):
        by_class = grp.groupby('urbanicity')['score'].mean().to_dict()
        class_counts = grp['urbanicity'].value_counts().to_dict()

        top = grp.sort_values('score', ascending=False).iloc[0]
        bottom = grp.sort_values('score', ascending=True).iloc[0]

        state_rows.append({
            'state': state,
            'county_count': int(len(grp)),
            'avg_score': round(float(grp['score'].mean()), 2),
            'urban_avg': round(float(by_class.get('Urban', 0.0)), 2),
            'suburban_avg': round(float(by_class.get('Suburban', 0.0)), 2),
            'rural_avg': round(float(by_class.get('Rural', 0.0)), 2),
            'urban_count': int(class_counts.get('Urban', 0)),
            'suburban_count': int(class_counts.get('Suburban', 0)),
            'rural_count': int(class_counts.get('Rural', 0)),
            'top_county': str(top['county_name']),
            'top_county_fips': str(top['FIPS']),
            'top_score': round(float(top['score']), 2),
            'bottom_county': str(bottom['county_name']),
            'bottom_county_fips': str(bottom['FIPS']),
            'bottom_score': round(float(bottom['score']), 2),
        })

    state_df = pd.DataFrame(state_rows).sort_values('state').reset_index(drop=True)

    return cnty, state_df, org_map, lookup_dict, urbanicity_source


cnty_df, state_df, ORG_MAP, LOOKUP, URBANICITY_SOURCE = load_data()


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/data/<path:filename>')
def data_file(filename):
    return send_from_directory('data', filename)


@app.route('/api/states')
def states():
    return jsonify({
        'states': sorted(state_df['state'].tolist()),
        'urbanicity_source': URBANICITY_SOURCE,
    })


@app.route('/api/search')
def search():
    q = request.args.get('q', '').strip().lower()
    if not q:
        return jsonify([])

    results = []
    for _, row in cnty_df.iterrows():
        fips = str(row['FIPS']).zfill(5)
        name = str(row['county_name'])
        state = str(row['state_abbr'])
        display = f"{name}, {state}"
        if q in name.lower() or q in state.lower() or q in fips:
            results.append({
                'fips': fips,
                'display': display,
                'population': int(row['population']),
                'urbanicity': str(row['urbanicity']),
                'lat': row['lat'],
                'lon': row['lon'],
                'state': state,
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

    r = row.iloc[0]

    peers = cnty_df[
        (cnty_df['state_abbr'] == r['state_abbr'])
        & (cnty_df['urbanicity'] == r['urbanicity'])
        & (cnty_df['FIPS'] != f)
    ].copy()
    peers['gap'] = (peers['score'] - r['score']).abs()
    peer_rows = peers.sort_values('gap').head(5)

    org_types = ORG_MAP.get(f, [])
    top_org_types = org_types[:3]

    data = {
        'fips': f,
        'name': str(r['county_name']),
        'state': str(r['state_abbr']),
        'population': int(r['population']),
        'urbanicity': str(r['urbanicity']),
        'score': round(float(r['score']), 2),
        'state_rank': int(r['state_rank']),
        'national_rank': int(r['national_rank']),
        'national_percentile': float(r['national_percentile']),
        'lat': r['lat'],
        'lon': r['lon'],
        'metrics': {
            'civic_org_sum': float(r['civic_org_sum_num']),
            'volunteer_sum': float(r['volunteer_sum_num']),
            'events_sum': float(r['events_sum_num']),
            'membership_sum': float(r['membership_sum_num']),
            'take_action_sum': float(r['take_action_sum_num']),
            'total_nonprofits': float(r['n_num']),
        },
        'top_org_types': top_org_types,
        'org_types': org_types,
        'peers': [
            {
                'fips': str(p['FIPS']),
                'name': str(p['county_name']),
                'state': str(p['state_abbr']),
                'score': round(float(p['score']), 2),
                'urbanicity': str(p['urbanicity']),
            }
            for _, p in peer_rows.iterrows()
        ],
    }
    return jsonify(data)


@app.route('/api/state/<state_code>')
def state_profile(state_code):
    state = str(state_code).upper()
    state_row = state_df[state_df['state'] == state]
    if state_row.empty:
        return jsonify({'error': 'state not found'}), 404

    summary = state_row.iloc[0].to_dict()

    counties = cnty_df[cnty_df['state_abbr'] == state].copy()
    top_counties = counties.sort_values('score', ascending=False).head(8)

    payload = {
        'summary': summary,
        'top_counties': [
            {
                'fips': str(r['FIPS']),
                'name': str(r['county_name']),
                'score': round(float(r['score']), 2),
                'urbanicity': str(r['urbanicity']),
            }
            for _, r in top_counties.iterrows()
        ],
    }
    return jsonify(payload)


@app.route('/api/compare/state')
def compare_state():
    state_a = request.args.get('state_a', '').upper()
    state_b = request.args.get('state_b', '').upper()

    a = state_df[state_df['state'] == state_a]
    b = state_df[state_df['state'] == state_b]
    if a.empty or b.empty:
        return jsonify({'error': 'state not found'}), 404

    arow = a.iloc[0].to_dict()
    brow = b.iloc[0].to_dict()

    result = {
        'state_a': arow,
        'state_b': brow,
        'gaps': {
            'avg_score_gap': round(arow['avg_score'] - brow['avg_score'], 2),
            'urban_gap': round(arow['urban_avg'] - brow['urban_avg'], 2),
            'suburban_gap': round(arow['suburban_avg'] - brow['suburban_avg'], 2),
            'rural_gap': round(arow['rural_avg'] - brow['rural_avg'], 2),
        },
    }
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
