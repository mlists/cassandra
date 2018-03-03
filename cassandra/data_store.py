import pickle
import glob
import logging
import os
import requests
import tbapy

from collections import OrderedDict
from datetime import datetime, timedelta
from typing import List
from tbapy.models import Match


class DataStore(object):

    CACHE_FILE_EXTENSION = '-event_matches.p'

    def __init__(self, cache_directory: str='cache', tba_auth_key: str=None,
                 years: list=[], empty: bool=False):
        """Initialise the DataStore class.

        Args:
            cache_directory: Path to directory the data store's cache files
            will be saved in. Defaults to `./cache/`.
            tba_auth_key: Authorisation key for fetching data from TheBlueAlliance.com.
            year_events: For a new data store being created, the keys of this
            dictionary correspond to the years we will be storing matches for,
            and the values the events within those years. List of events must
            be ordered by start date (ie in chronological order).
        """
        self.tba_auth_key = tba_auth_key

        # First we need to monkey patch the tbapy.TBA class so we can
        # use the last-modified header
        def _new_tba_get(self, url):
            resp = self.session.get(self.URL_PRE + url, headers={'X-TBA-Auth-Key': self.auth_key,
                                    'If-Modified-Since': self.last_modified})
            if resp.status_code == 200:
                self.last_modified_response = resp.headers['Last-Modified']
                return resp.json()
            else:
                return {}
        tbapy.TBA._get = _new_tba_get

        self.tba = tbapy.TBA(self.tba_auth_key)
        self.tba.last_modified = ''  # e.g. 'Thu, 01 Mar 2018 17:21:48 GMT'
        self.tba.last_modified_response = ''
        self.tba.session = requests.Session()

        if not years:
            n = datetime.now()
            t = n.timetuple()
            years = range(2008, t[0])

        self.empty = empty

        self.cache_directory = cache_directory.rstrip('/')
        if not os.path.exists(self.cache_directory):
            os.makedirs(cache_directory)

        self.data = OrderedDict()
        year_events = {}
        # fetch events by year and order chronologically
        for year in years:
            self.last_modified = ''
            r = self.tba.events(year, simple=True)

            # sort by date and don't include offseason events
            events_sorted = sorted(r, key=lambda b: b["start_date"])
            events_dict = {ev['key']: ev for ev in events_sorted}
            a = [i["key"] for i in events_sorted if i["event_type"] < 99]

            year_events[year] = a

            cache_file = ''.join([self.cache_directory, '/', str(year),
                                  self.CACHE_FILE_EXTENSION])
            if os.path.exists(cache_file) and not self.empty:
                year_odict = pickle.load(open(cache_file, 'rb'))
                self.data[year] = year_odict
                for event_code in year_events[year]:
                    if event_code not in self.data[year].keys():
                        self.data[year][event_code] = {'last_modified': '',
                                                       'info': events_dict[event_code],
                                                       'matches': OrderedDict()}
            else:
                year_odict = OrderedDict()
                for event_code in year_events[year]:
                    year_odict[event_code] = {'last_modified': '',
                                              'info': events_dict[event_code],
                                              'matches': OrderedDict()}
                self.data[year] = year_odict

        if self.empty:
            return

        # fetch matches by year and event
        for year in years:
            write_to_cache = False
            for event in year_events[year]:
                last_modified, matches = self.fetch_event_matches(year, event)
                print("Fetching: %s" % event)
                if matches:
                    self.add_event_matches(year=year, event_code=event, matches=matches,
                                           last_modified=last_modified)
                    write_to_cache = True
            if write_to_cache:
                self.write_cache(year, self.data[year])

    def add_event_matches(self, year: int, event_code: str, matches: List, last_modified: str):
        """ Add matches to our data store.

        The matches are added to both this program instance's copy of the
        data store (in this_instance.data), and written to the disk's cached
        copy.

        Args:
            year: The year the matches need to be added to.
            event_code: The event code corresponding to the event the matches
                belong to.
            matches: The list of matches to add to the data store.
            last_modified: the last modified time of the match list being added
                to the data store.

        """
        if event_code not in self.data[year].keys():
            logging.warning("Event %s (year %s) is not an event in the data"
                            "store, but matches for it are being added."
                            % (event_code, year))
        event_metadata = self.data[year][event_code]['info']
        self.data[year][event_code] = {'last_modified': last_modified,
                                       'info': event_metadata, 'matches': matches}
        self.write_cache(year, self.data[year])

    def add_single_match(self, year: int, event_code: str, match: Match):
        """ Add a single match to the datastore.

        Args:
            year: The year the matche needs to be added to.
            event_code: The event code corresponding to the event the matches
                belong to.
            match: the match to add to the datastore.
            last_modified: the last modified time of the match being added
                to the data store.

        """
        self.data[year][event_code]['matches'][match['key']] = match

    def get_year_events(self, year: int) -> List[str]:
        """ Get the list of event codes for a year from the data store.

        Args:
            year: The year to get the list of events for.

        Returns:
            The list of events from that year, in chronological order.
        """
        return self.data[year].keys()

    def get_event_matches(self, event_year: int, event_code: str) -> List:
        """ Get the list of matches associated with event_code.

        Args:
            year: The year that event_code is part of.
            event_code: The event code of the event we want that matches from.

        Returns:
            List of matches associated with event_code. `[]` if event_code was
            supplied to constructor, but no matches have been added.
        """
        event_match_data = self.data[event_year][event_code]['matches']
        # Always return a list,  but return an empty one if no matches have
        # been added to this event.
        return [] if event_match_data is None else event_match_data

    def fetch_event_matches(self, event_year: int, event_code: str) -> List:
        """ Fetch event matches from TBA. """

        event_start = datetime.strptime(
                self.data[event_year][event_code]['info']['start_date'], '%Y-%m-%d')
        event_end = datetime.strptime(
                self.data[event_year][event_code]['info']['end_date'], '%Y-%m-%d')
        one_day = timedelta(days=1)
        now = datetime.now()
        current_entry = self.data[event_year][event_code]['matches']
        if (event_start-one_day < now < event_end+one_day
           or (not current_entry and event_start-one_day < now)):
            self.tba.last_modified = self.data[event_year][event_code]['last_modified']
            matches = self.tba.event_matches(event_code)
            matches_odict = self.sort_by_match_number(matches)
            return (self.tba.last_modified_response, matches_odict) if matches else ('', None)
        return ('', None)

    def write_cache(self, year: int, value):
        """ Write value to the cache for year. """
        if self.empty:
            return
        cache_file = ''.join([self.cache_directory, '/', str(year),
                              self.CACHE_FILE_EXTENSION])
        pickle.dump(value, open(cache_file, 'wb'))

    @staticmethod
    def sort_by_match_number(matches):
        """ Sort matches (which is a list of dictionares representing a
        Blue Alliance API event response) by match number.

        Returns:
            Ordered dict of matches sorted by match / set number. """

        comp_levels = OrderedDict([('qm', []), ('ef', []), ('qf', []), ('sf', []), ('f', [])])

        for match in matches:
            comp_levels[match['comp_level']].append(match)
        sorted_matches = []
        for level in comp_levels.values():
            sorted_matches += sorted(level, key=lambda x: (x['match_number'], x['set_number']))
        matches_odict = OrderedDict([(match['key'], match) for match in sorted_matches])

        return matches_odict
