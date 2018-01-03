import pickle
import glob

from collections import OrderedDict
from typing import Dict, List


class DataStore(object):

    CACHE_FILE_EXTENSION = '-event_matches.p'

    def __init__(self, cache_directory: str='cache',
                 new_data_store: bool=False, year_events: Dict[int, list]={}):
        """Initialise the DataStore class.

        Args:
            cache_directory: Path to directory the data store's cache files
            will be saved in. Defaults to `./cache/`.
            new_data_store: Set to True to create a new data store with the
            structure of year_events instead of using the one currently in
            cache_directory.
            year_events: For a new data store being created, the keys of this
            dictionary correspond to the years we will be storing matches for,
            and the values the events within those years. List of events must
            be ordered by start date.
        """

        self.cache_directory = cache_directory.rstrip('/')

        if new_data_store:
            year_odicts = [(year, OrderedDict(
                [(event_code, None) for event_code in events]))
                for year, events in year_events.items()]
            self.data = OrderedDict(sorted(year_odicts,
                                           key=lambda x: x[0]))

            # write the data to disk
            for year, year_odict in self.data.items():
                self.write_cache(year, year_odict)
        else:
            self.data = OrderedDict()

            # Find the data files. Must be of the form:
            # <year>-event_matches.p
            cache_file_pattern = ''.join([self.cache_directory, '/',
                                          '????',  # match year
                                          self.CACHE_FILE_EXTENSION])
            cache_files = glob.glob(cache_file_pattern)

            # Sort cache files by year
            def get_year(cache_fname): return int(
                    cache_fname.lstrip(self.cache_directory+'/')[:4])
            cache_files = sorted(cache_files, key=get_year)

            #
            for fname in cache_files:
                year_odict = pickle.load(open(fname, 'rb'))
                year = get_year(fname)
                self.data[year] = year_odict

    def add_event_matches(self, year: int, event_code: str, matches: List):
        """ Add matches to our data store.

        The matches are added to both this program instance's copy of the
        data store (in this_instance.data), and written to the disk's cached
        copy.

        Args:
            year: The year the matches need to be added to.
            event_code: The event code corresponding to the event the matches
            belong to.
            matches: The list of matches to add to the data store.

        """
        self.data[year][event_code] = matches
        self.write_cache(year, self.data[year])

    def write_cache(self, year: int, value):
        """ Write value to the cache for year. """

        cache_file = ''.join([self.cache_directory, '/', str(year),
                              self.CACHE_FILE_EXTENSION])
        pickle.dump(value, open(cache_file, 'wb'))
