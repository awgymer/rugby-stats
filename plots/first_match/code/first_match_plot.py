import logging
import json
import datetime
import pathlib
import os
from argparse import ArgumentParser

import plotly.io

import pandas as pd


log = logging.getLogger('Mapbox Plotter')
ch = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s | %(name)s | %(levelname)7s | %(message)s",
    "%Y-%m-%d %H:%M:%S"
)
ch.setFormatter(formatter)
log.addHandler(ch)


def get_parser():
    parser = ArgumentParser(
        description=('Tools for working with GeoJSONs and rugby data')
    )
    parser.add_argument(
        '--verbosity', '-v', action='count', default=0,
        help='Set the logging level'
    )
    parser.add_argument(
        '-f', '--format', default='png',
        choices=['png', 'webp', 'svg', 'html'],
        help='The format to save the plots to'
    )
    parser.add_argument(
        'geojson', type=str,
        help='GeoJSON of polygons for the plot'
    )
    parser.add_argument(
        'centroids', type=str,
        help='GeoJSON with polygon centroids'
    )
    parser.add_argument(
        'input_data', type=str,
        help='CSV of input data'
    )
    parser.add_argument(
        'min_year', type=int,
        help='First year to include in plot'
    )
    parser.add_argument(
        'max_year', type=int,
        help='Last year to include in plot'
    )
    parser.add_argument(
        'outdir', type=str,
        help='Filepath to output the plots to'
    )
    return parser


colorpal = [
    [0, 'rgba(204,204,204,1)'],
    [0.5, 'rgba(236,246,204,1)'],
    [0.53125, 'rgba(225,241,192,1)'],
    [0.5625, 'rgba(213,235,180,1)'],
    [0.59375, 'rgba(199,228,167,1)'],
    [0.625, 'rgba(183,221,153,1)'],
    [0.65625, 'rgba(165,213,139,1)'],
    [0.6875, 'rgba(145,204,125,1)'],
    [0.71875, 'rgba(121,195,111,1)'],
    [0.75, 'rgba(94,186,97,1)'],
    [0.78125, 'rgba(75,173,94,1)'],
    [0.8125, 'rgba(59,160,92,1)'],
    [0.84375, 'rgba(43,145,88,1)'],
    [0.875, 'rgba(26,131,83,1)'],
    [0.90625, 'rgba(6,116,77,1)'],
    [0.9375, 'rgba(0,100,69,1)'],
    [0.96875, 'rgba(0,85,61,1)'],
    [1.0, 'rgba(0,69,51,1)']
]


ONE_CENTROID_TEAMS = {
    'New Zealand': "NZL",
    'Ireland': "IRL",
    'China': "CHN",
    'USA': "USA",
    'England': "ENG",
    'France': "FXX",
    'Netherlands': "NLX",
}


def make_label(row):
    outcomes = {'A': 'W', 'B': 'L'}
    if pd.isna(row.years_played):
        return f'<b>{row.statename}</b><br>No international representative team'
    dt = datetime.datetime.fromtimestamp(row.ko_sec, tz=datetime.timezone.utc)
    return (
        f'<b>{row.team_name}</b><br>{dt.strftime("%d %b %Y")}<br>v {row.oppname}'
        f'<br>{outcomes.get(row.outcome, "D")}'
        f' {int(row.tm_score)} - {int(row.oppscore)}'
    )


def get_centroids(cjson):
    with open(cjson, 'r') as cj:
        centjson = json.load(cj)
    return {
        f['id']: f['geometry']['coordinates']
        for f in centjson['features']
    }


def main(args):
    with open(args.geojson, 'r') as geoj:
        geojson = json.load(geoj)

    centroids = get_centroids(args.centroids)

    df = pd.read_csv(args.input_data)

    df['label'] = df.apply(make_label, axis=1)

    years = range(args.min_year, args.max_year+1)

    layout = dict(
        mapbox={
            'style': 'white-bg',
            'zoom': 1.37,
            'center': {'lon': 6.45, 'lat': 29.3},
            'accesstoken': os.environ['MAPBOX_TOKEN']
        },
        coloraxis={'showscale': False}
    )

    outpath = pathlib.Path(args.outdir)

    for i, y in enumerate(years):
        dfsub = df[df.year == y]
        maptrace = dict(
            type='choroplethmapbox',
            geojson=geojson,
            locations=dfsub.geounit,
            z=dfsub.colorscale,
            zmin=-1,
            zmax=1,
            colorscale=colorpal,
            showscale=False,
            autocolorscale=False,
            reversescale=False,
            hovertext=dfsub.label,
            hoverinfo='text',
            below=''
        )

        dfdebs = dfsub[dfsub.years_played == 0]
        debuts = dfdebs.apply(
            lambda x: ONE_CENTROID_TEAMS.get(x.team_name, x.geounit),
            axis=1, result_type='reduce'
        ).unique()

        longitudes = []
        latitudes = []

        for d in debuts:
            lon, lat = centroids[d]
            longitudes.append(lon)
            latitudes.append(lat)

        centroid_trace = dict(
            type='scattermapbox',
            lon=longitudes,
            lat=latitudes,
            mode='markers',
            marker=dict(
                size=9,
                color="#FF00A7",
                showscale=False
            ),
            hoverinfo='skip',
            showlegend=False,
            below=''
        )

        title = dict(
            text=f'The Spread of Rugby Union: {y}',
            font={'size': 30},
            xref='paper',
            xanchor='left',
            x=0
        )
        subtitle_text = (
            "Tracking the first match for each international level men's team"
            " | Match is not necessarily a test match <br>"
            "Darker green represents older team"
            " | Pink dots represent debut nations"
        )
        debutants_text = f'Debuts: {", ".join(dfdebs.team_name.unique())}'
        credits_text = 'Graph: @awgymer | Data: https://www.world.rugby'

        subtitle = dict(
            showarrow=False,
            text=subtitle_text,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='bottom',
            x=0, y=1,
            align='left'
        )
        debutants = dict(
            showarrow=False,
            text=debutants_text,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='top',
            x=0, y=0,
            align='left',
            font={'size': 20}
        )
        credits = dict(
            showarrow=False,
            text=credits_text,
            xref='paper',
            yref='paper',
            xanchor='right',
            yanchor='top',
            x=1, y=0,
        )
        annotations = [subtitle, debutants, credits]
        layout['title'] = title
        layout['annotations'] = annotations
        traces = [maptrace, centroid_trace]
        fig = dict(data=traces, layout=layout)

        outfile = outpath.joinpath(f'{y}_plot.{args.format}')
        if args.format == 'html':
            plotly.io.write_html(
                fig, str(outfile), include_plotlyjs='directory'
            )
        elif args.format == 'svg':
            plotly.io.write_image(
                fig, str(outfile), args.format,
                width=1600, height=900
            )
        else:
            plotly.io.write_image(
                fig, str(outfile), args.format,
                width=1600, height=900, scale=4
            )
        log.info('Saved: %s', outfile)


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    log.setLevel(max([50-args.verbosity*10, 10]))
    print(f'Logging at {logging.getLevelName(log.level)} level')
    main(args)
