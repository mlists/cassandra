"""Cassandra a prediction system for FRC games based on trueskill.
"""

from data_store import DataStore
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
        matches = {}
        base_url = "https://www.thebluealliance.com/api/v3"
        header = {"X-TBA-Auth-Key": self.key}

        # fetch events by year and order chronologically
        for year in years:
            r = requests.get(base_url + "/events/" + str(year) + "/simple", headers=header).json()

            # sort by date and don't include offseason events
            a = sorted(r, key=lambda b: b["start_date"])
            a = [i["key"] for i in a if i["event_type"] < 99]

            events[str(year)] = a

        # fetch matches by year and event
        for year in years:
            for event in events[str(year)]:
                r = requests.get(base_url + "/event/" + event + "/matches/simple", headers=header).json()

                matches[event] = r

        # save to cache
        store = DataStore(new_data_store=True, year_events=events)

        for year in years:
            for event in events[str(year)]:
                event_matches = matches[event]
                store.add_event_matches(str(year), event, event_matches)
