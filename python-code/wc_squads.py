from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup

rwc_dates = {
    1987: '22 May 1987',
    1991: '3 October 1991',
    1995: '25 May 1995',
    1999: '1 October 1999',
    2003: '10 October 2003',
    2007: '7 September 2007',
    2011: '9 September 2011',
    2015: '18 September 2015',
    2019: '20 September 2019'
}

team_choices = {
    2019: [
        "Ireland",
        "Japan",
        "Russia",
        "Samoa",
        "Scotland",
        "Canada",
        "Italy",
        "Namibia",
        "New Zealand",
        "South Africa",
        "Argentina",
        "England",
        "France",
        "Tonga",
        "United States",
        "Australia",
        "Fiji",
        "Georgia",
        "Uruguay",
        "Wales",
    ],
    2015: [
        "Australia",
        "England",
        "Fiji",
        "Uruguay",
        "Wales",
        "Japan",
        "Samoa",
        "Scotland",
        "South Africa",
        "United States",
        "Argentina",
        "Georgia",
        "Namibia",
        "New Zealand",
        "Tonga",
        "Canada",
        "France",
        "Ireland",
        "Italy",
        "Romania"
    ],
    2011: [
        "Canada",
        "France",
        "Japan",
        "New Zealand",
        "Tonga",
        "Argentina",
        "England",
        "Georgia",
        "Romania",
        "Scotland",
        "Australia",
        "Ireland",
        "Italy",
        "Russia",
        "United States",
        "Fiji",
        "Namibia",
        "Samoa",
        "South Africa",
        "Wales",
    ],
    2007: [
        "England",
        "Samoa",
        "South Africa",
        "Tonga",
        "United States",
        'none',
        "Australia",
        'none',
        "Canada",
        "Fiji",
        "Japan",
        'none',
        "Wales",
        "Italy",
        "New Zealand",
        "Portugal",
        "Romania",
        "Scotland",
        "Argentina",
        "France",
        'none',
        "Georgia",
        "Ireland",
        "Namibia",
    ],
    2003: [
        "Australia",
        "Ireland",
        "Argentina",
        "Romania",
        "Namibia",
        "France",
        "Scotland",
        "Fiji",
        "United States",
        "Japan",
        "England",
        "South Africa",
        "Samoa",
        "Uruguay",
        "Georgia",
        "New Zealand",
        "Wales",
        "Italy",
        "Canada",
        "Tonga",
    ],
    1999: [
        "Scotland",
        "South Africa",
        "Spain",
        "Uruguay",
        "England",
        "Italy",
        "New Zealand",
        "Tonga",
        "Fiji",
        "Namibia",
        "France",
        "Canada",
        "Wales",
        "Argentina",
        "Samoa",
        "Japan",
        "Ireland",
        "United States",
        "Australia",
        "Romania",
    ],
    1995: [
        "Australia",
        "Canada",
        "Romania",
        "South Africa",
        "Argentina",
        "England",
        "Italy",
        "Western Samoa",
        "Ireland",
        "Japan",
        "New Zealand",
        "Wales",
        "France",
        "Ivory Coast",
        "Scotland",
        "Tonga",
    ],
    1991: [
        "England",
        "Italy",
        "New Zealand",
        "United States",
        "Ireland",
        "Japan",
        "Scotland",
        "Zimbabwe",
        "Argentina",
        "Australia",
        "Wales",
        "Western Samoa",
        "Canada",
        "Fiji",
        "France",
        "Romania",
    ],
    1987: [
        "Australia",
        "United States",
        "England",
        "Japan",
        "Wales",
        "Canada",
        "Ireland",
        "Tonga",
        "New Zealand",
        "Fiji",
        "Italy",
        "Argentina",
        "France",
        "Scotland",
        "Romania",
        "Zimbabwe",
    ]
}

squad_dfs = {}
rwc_years = set(range(1987, 2020, 4))

def get_flags(html_table):
    flags = []
    for row in html_table.find('tbody').find_all('tr'):
        heads = row.find_all('th')
        if heads:
            print('Found header row')
            continue
        club_col = row.find_all('td')[-1]
        flag_span = club_col.find('span', attrs={'class':'flagicon'})
        flag_id = None
        if flag_span:
            flag_id = flag_span.find('a').attrs.get('title')
        flags.append(flag_id)
    return flags

for y in rwc_years:
    try:
        html = requests.get(f'http://en.wikipedia.org/wiki/{y}_Rugby_World_Cup_squads')
        tabs = pd.read_html(html.text, attrs={'class': 'sortable'})
        flags_per_tab = []
        soup = BeautifulSoup(html.text)
        tables = soup.find_all("table", { "class" : "sortable" })
        for t in tables:
            flags_per_tab.append(get_flags(t))
        for i, sqd in enumerate(tabs):
            sqd['flag'] = flags_per_tab[i]
        squad_dfs[y] = tabs
        print(f'Successfully fetched HTML for {y}')
    except Exception as err:
        print(f'Error fetching HTML for {y}')

for squads in squad_dfs.values():
    for sq in squads:
        sq.rename(columns={
            'Franchise / Province': 'club',
            'Franchise / province': 'club',
            'Club/province': 'club',
            'Date of birth (Age)': 'dob',
            'Date of birth (age)': 'dob',
            'Caps': 'caps',
            'Player': 'player',
            'Position': 'position',
        }, inplace=True)

for year, squads in squad_dfs.items():
    for sq in squads:
        if 'club' in sq.columns:
            sq['year'] = year
            sq['start_date'] = datetime.strptime(rwc_dates[year], "%d %B %Y")

for year, squads in squad_dfs.items():
    print(year)
    idx = 0
    for sq in squads:
        if 'club' in sq.columns and 'country' not in sq.columns:
            sq['country'] = team_choices[year][idx]
            idx += 1

squads_list = []
for squads in squad_dfs.values():
    for s in squads:
        if 'club' in s.columns:
            squads_list.append(s)

all_squads = pd.concat(squads_list)
all_squads = all_squads[all_squads.country != 'none']

all_squads['dob'] = all_squads['dob'].str.split('(', expand=True)[0].str.strip()
all_squads['dob_dt'] = pd.to_datetime(all_squads['dob'], format="%d %B %Y", errors='coerce')
mask = all_squads.dob_dt.isnull()
all_squads.loc[mask, 'dob_dt'] = pd.to_datetime(
    all_squads[mask]['dob'], format='%B %d, %Y', errors='coerce'
)
all_squads['days_old'] = (all_squads['start_date'] - all_squads['dob_dt']).apply(lambda x: x.days)
all_squads.replace(
    {
        'First five-eighth': 'Fly-half',
        'Half-back': 'Scrum-half',
        'Loose forward': 'Back row',
        'Flanker': 'Back row',
        'Number 8': 'Back row'
    },
    inplace=True
)

all_squads.to_csv('wc_squads_processed.csv', index=False)


url_tests_86 = (
    "http://stats.espnscrum.com/statsguru/rugby/stats/index.html"
    "?class=1;page={};spanmin1=1+Jan+1983;spanval1=span;template=results;type=team;view=year"
)
match_tabs = []
pg_no = 0
while True:
    pg_no += 1
    tab = pd.read_html(url_tests_86.format(pg_no), attrs={'class': 'engineTable'})
    if len(tab) < 3:
        break
    match_tabs.append(tab[1])
    print(f'Got page {pg_no} of results')

all_matches = pd.concat(match_tabs)
all_matches.rename(columns={
    'Team': 'team',
    'Mat': 'total_matches',
    'Won': 'won',
    'Lost': 'lost',
    'Draw': 'draw',
    '%': 'win_perc',
    'For': 'pts_for',
    'Aga': 'pts_against',
    'Diff': 'pts_diff',
    'Tries': 'tries',
    'Conv': 'conversion',
    'Pens': 'pen_goal',
    'Drop': 'drop_goal',
    'Year': 'year',
    'Unnamed: 14': 'to_drop',
}, inplace=True)
all_matches.drop('to_drop', axis=1, inplace=True)
all_matches.to_csv('all_matches_83_19.csv', index=False)
