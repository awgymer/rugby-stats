import logging
import json
import csv
from copy import deepcopy
from argparse import ArgumentParser

import pandas as pd
import numpy as np


log = logging.getLogger('GeoJSON Tools')
ch = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s | %(name)s | %(levelname)7s | %(message)s",
    "%Y-%m-%d %H:%M:%S"
)
ch.setFormatter(formatter)
log.addHandler(ch)


COUNTRY_GRPS = {
    'Arabian Gulf': [
        'Bahrain', 'Kuwait', 'Oman', 'Qatar', 'Saudi Arabia',
        'United Arab Emirates', 'Egypt', 'Lebanon', 'Jordan'],
    'USSR': [
        'Armenia', 'Azerbaijan', 'Belarus', 'Estonia', 'Georgia',
        'Kazakhstan', 'Kyrgyzstan', 'Latvia', 'Lithuania', 'Moldova',
        'Russia', 'Tajikistan', 'Turkmenistan', 'Ukraine', 'Uzbekistan'],
    'Yugoslavia': [
        'Bosnia and Herzegovina', 'Croatia', 'Kosovo',
        'Montenegro', 'Macedonia', 'Republic of Serbia', 'Slovenia'],
    'Czechoslovakia': ['Czechia', 'Slovakia'],
    'Ireland': ['Northern Ireland', 'Ireland'],
    'Serbia': ['Republic of Serbia'],
    'Tanzania': ['United Republic of Tanzania'],
    'England': ['United Kingdom']
}


def get_parser():
    parser = ArgumentParser(
        description=('Tools for working with GeoJSONs and rugby data')
    )
    parser.add_argument(
        '--verbosity', '-v', action='count', default=0,
        help='Set the logging level'
    )
    subparsers = parser.add_subparsers(title='program', dest='program')

    mk_geo = subparsers.add_parser(
        'makegeo',
        help='Make a custom GeoJSON that only uses Map Units where necessary'
    )
    mk_geo.add_argument(
        'sovgeojson', type=str,
        help='GeoJSON of sovereign states'
    )
    mk_geo.add_argument(
        'mapunitgeojson', type=str,
        help='GeoJSON of map units'
    )
    mk_geo.add_argument(
        'teamcsv', type=str,
        help='CSV with teams and geo ids'
    )
    mk_geo.add_argument(
        'outgeojson', type=str,
        help='JSON to write new compound GeoJSON to'
    )
    mk_geo.add_argument(
        '-g', '--geocol', type=str, default='geo_id',
        help='Name of column containing team geoid'
    )

    add_geos = subparsers.add_parser(
        'add-geo-ids',
        help='Add GeoJSON feature ids to a CSV of team data using a geo_id column')
    add_geos.add_argument(
        'geojson', type=str,
        help='GeoJSON to map team geo ids to'
    )
    add_geos.add_argument(
        'teamcsv', type=str,
        help='CSV with teams and geo ids'
    )
    add_geos.add_argument(
        'outcsv', type=str,
        help='CSV to write updated data to'
    )
    add_geos.add_argument(
        '-g', '--geocol', type=str, default='geo_id',
        help='Name of column containing team geoid'
    )
    return parser


def geo_units_from_sov(team, refs):
    return _geo_units_from_refs(team, refs, 'SOVEREIGNT')


def geo_units_from_geounit(team, refs):
    return _geo_units_from_refs(team, refs, 'GEOUNIT')


def _geo_units_from_refs(team, refs, key):
    geo_unit = refs[refs[key] == team]
    return list(geo_unit.GU_A3)


def add_geo_ids(args):
    with open(args.geojson, 'r') as geoj:
        geojson = json.load(geoj)

    geodf = pd.DataFrame([f['properties'] for f in geojson['features']])

    with open(args.teamcsv, 'r') as tm_csv:
        reader = csv.DictReader(tm_csv)
        new_rows = []
        excl_from_sov = set()
        for row in reader:
            teams = COUNTRY_GRPS.get(
                row[args.geocol],
                [row[args.geocol]]
            )
            geounits = set()
            for tm in teams:
                gus = geo_units_from_sov(tm, geodf)
                if not gus:
                    gus = geo_units_from_geounit(tm, geodf)
                    excl_from_sov.update(gus)
                geounits.update(gus)
            new_rows.append({**row, 'geounits': geounits})
    for n in new_rows:
        if len(n['geounits']) > 1:
            # Hardcoded fix for Northern Ireland
            if not n[args.geocol] == 'Ireland':
                n['geounits'] = n['geounits'] - excl_from_sov
        n['geounits'] = ','.join(n['geounits'])
    with open(args.outcsv, 'w') as outcsv:
        fieldnames = list(new_rows[0].keys())
        writer = csv.DictWriter(outcsv, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_rows)


def mk_geojson(args):
    with open(args.sovgeojson, 'r') as sgeo:
        sovgeo = json.load(sgeo)

    with open(args.mapunitgeojson, 'r') as mgeo:
        mugeo = json.load(mgeo)

    sovdf = pd.DataFrame([f['properties'] for f in sovgeo['features']])
    mudf = pd.DataFrame([f['properties'] for f in mugeo['features']])
    tmdf = pd.read_csv(args.teamcsv)

    exp_geo = set()
    for g in set(tmdf[args.geocol]):
        exp_geo.update(COUNTRY_GRPS.get(g, [g]))

    use_mus = set()
    for g in exp_geo:
        if g not in sovdf.SOVEREIGNT.values:
            try:
                sov = mudf[mudf['GEOUNIT'] == g].SOVEREIGNT.iloc[0]
            except IndexError:
                log.warning('No Geounit or Sovereignty found for %s', g)
                continue
            use_mus.add(sov)
    log.info(
        'Sovereignties have dependencies with international teams: %s',
        ','.join(use_mus)
    )

    new_feats = []
    for f in sovgeo['features']:
        if f['properties']['SOVEREIGNT'] not in use_mus:
            f_ = deepcopy(f)
            f_['id'] = f_['properties']['GU_A3']
            new_feats.append(f_)

    for f in mugeo['features']:
        if f['properties']['SOVEREIGNT'] in use_mus:
            f_ = deepcopy(f)
            f_['id'] = f_['properties']['GU_A3']
            new_feats.append(f_)

    new_geo = {}
    new_geo['type'] = 'FeatureCollection'
    new_geo['features'] = new_feats

    with open(args.outgeojson, 'w') as outgeo:
        json.dump(new_geo, outgeo)


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    log.setLevel(max([50-args.verbosity*10, 10]))
    print(f'Logging at {logging.getLevelName(log.level)} level')
    if args.program == 'makegeo':
        mk_geojson(args)
    elif args.program == 'add-geo-ids':
        add_geo_ids(args)
