#!/usr/bin/env python3
from cassandra.data_store import DataStore
from cassandra.predictors import TrueSkillPredictor
import sys

if len(sys.argv) == 1:
    sys.exit('ERROR: Not enough command arguments supplied. Need a ssh key.')
year = 2016
ds = DataStore(tba_auth_key=sys.argv[1], years=[year])
empty_datastore = DataStore(years=[year], empty=True)
tsp = TrueSkillPredictor(empty_datastore)
brier = 0
count = 0
for event_code in ds.data[year]:
    matches = ds.data[year][event_code]['matches']
    for match, match_data in matches.items():
        empty_datastore.add_single_match(year=year, event_code=event_code, match=match_data)
        p_blue, p_red = tsp.predict(match_data['alliances']['blue']['team_keys'], match_data['alliances']['red']['team_keys'])
        tsp.update(match)
        outcome = 1 if match_data['winning_alliance'] == 'blue' else 0
        brier += (p_blue - outcome) ** 2
        count += 1
brier /= count
print(brier)
