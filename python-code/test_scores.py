import datetime as dt
import csv
import json

with open('test_scores.csv', 'r') as in_f:
    reader = csv.DictReader(in_f)
    out = [{
        'id': row[''],
        'home': row['home'],
        'away': row['away'],
        'home_pts': int(row['home_pts']),
        'away_pts': int(row['away_pts']),
        'winning_score': int(row['winning_score']),
        'losing_score': int(row['losing_score']),
        'location': row['ground'],
        'date': row['date'],
        'year': row['year'],
        'series': [s.strip() for s in row['series'].split('/')],
    } for row in reader]

def date_to_json(o):
    if isinstance(o, (dt.date, dt.datetime)):
        return o.isoformat()

for d in out:
    try:
        d['date'] = dt.datetime.strptime(d['date'], '%d %b %Y').date()
    except Exception as err:
        print(d['id'])
        try:
            d['date'] = dt.datetime.strptime(d['date'], '%b %Y').date()
        except Exception as err:
            try:
                d['date'] = dt.datetime.strptime(d['date'], '%Y').date()
            except Exception as err:
                print('Problem with date: {}'.format(d['date']))

outj = json.dumps(out, default=date_to_json)

with open('test_scores.json', 'w') as out_j:
    json.dump(out, out_j, default=date_to_json)
