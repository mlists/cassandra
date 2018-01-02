import pickle
import glob

from collections import OrderedDict
from typing import Dict, List


class CacheManager(object):

    CACHE_FILE_EXTENSION = '-event_matches.p'

    def __init__(self, cache_directory: str='cache', new_cache: bool=False,
                 year_events: Dict[int, list]={}):
        """Initialise the CacheManager class.

        Args:
            cache_directory: Path to directory the cache files will be saved
            in.
            new_cache: Set to True to create a new cache with the structure of
            year_events instead of using the current one.
            year_events: For a new cache being created, the keys of this
            dictionary correspond to the years we will be caching matches for,
            and the values the events within those years. List of events must
            be ordered by start date.
        """

        self.cache_directory = cache_directory.rstrip('/')

        if new_cache:
            year_odicts = [(year, OrderedDict(
                [(event_code, None) for event_code in events]))
                for year, events in year_events.items()]
            self.cache = OrderedDict(sorted(year_odicts,
                                     key=lambda x: x[0]))

            # write the cache to disk
            for year, year_odict in self.cache.items():
                self.write_cache(year, year_odict)
        else:
            self.cache = OrderedDict()

            # Find the cache files. Must be of the form:
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
                self.cache[year] = year_odict

    def add_event_matches(self, year: int, event_code: str, matches: List):
        """ Add matches to our cache.

        The matches are added to both this program instance's copy of the
        cache (in this_instance.cache), and written to the disk.

        Args:
            year: The year the matches need to be added to.
            event_code: The event code corresponding to the event the matches
            belong to.
            matches: The list of matches to add to the cache.

        """
        self.cache[year][event_code] = matches
        self.write_cache(year, self.cache[year])

    def write_cache(self, year: int, value):
        """ Write value to the cache for year. """

        cache_file = ''.join([self.cache_directory, '/', str(year),
                              self.CACHE_FILE_EXTENSION])
        pickle.dump(value, open(cache_file, 'wb'))
