"""Cassandra a prediction system for FRC games based on trueskill.

Steps:
    1 Load games from cache.
    2 Get list of events from TBA.
    3 Iterate through events, download and cache matches if not in cache.
"""

import data_store
import requests


class Cassandra:

    def __init__(self, key, years):
        """Initialise Cassandra
        Args:
            key: String of TBA key.
            years: List of the years in which to cache results.
        """

        self.years = years
        self.key = key

        # cache previous results
        events = {}
        base_url = "https://www.thebluealliance.com/api/v3"
        header = {"X-TBA-Auth-Key": self.key}
        for year in years:
            r = requests.get(base_url + "/events/" + str(year) + "/simple", headers=header)
            r = r.json()
            events[str(year)] = r

        print(events["2010"])
