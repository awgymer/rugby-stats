from bs4 import BeautifulSoup
from bs4 import element
import requests
import pandas as pd
import numpy as np
from datetime import datetime

ROOT_ESPN = 'http://stats.espnscrum.com'
TEST_RESULT_URL = ROOT_ESPN + '/scrum/rugby/records/team/match_results.html?id={};type=year'


def scrape_scores(from_yr=1871, to_yr=datetime.today().year):
    test_res = []
    for y in range(from_yr, to_yr):
        r = requests.get(TEST_RESULT_URL.format(y))
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find("table", {"class": "engineTable"})
        if table is None:
            print(f'No records in {y}')
            continue
        df = pd.read_html(str(table))[0]
        links = []
        for l in [tr.find_all('td')[-1].find('a') for tr in table.tbody.find_all('tr')]:
            links.append(l if l is None else l.get('href'))
        df['match_link'] = links
        test_res.append(df)

    all_res = pd.concat(test_res)
    all_res.columns = [
        'home', 'home_pts', 'away_pts',
        'away', 'home_ht_pts', 'away_ht_pts',
        'na', 'series', 'ground', 'date', 'match', 'match_link'
    ]
    all_res['year'] = all_res['date'].map(lambda x: str(x).split(' ')[-1])
    #filter out G from pre-1890 results
    all_res['home_pts'] = all_res['home_pts'].astype(str).str.extract('(\d+)').astype(int)
    all_res['away_pts'] = all_res['away_pts'].astype(str).str.extract('(\d+)').astype(int)

    #Add winning/losing score
    all_res['winning_score'] = all_res[['home_pts', 'away_pts']].max(axis=1)
    all_res['losing_score'] = all_res[['home_pts', 'away_pts']].min(axis=1)
    all_res.reset_index(inplace=True)
    all_res.drop(['na', 'match', 'index'], inplace=True, axis=1)
    return all_res
    #all_res.to_csv('test_scores.csv')
