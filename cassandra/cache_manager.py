import pickle
import glob

from collections import OrderedDict
from typing import Dict


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
                cache_file = ''.join([cache_directory, '/', str(year),
                                      self.CACHE_FILE_EXTENSION])
                pickle.dump(year_odict, open(cache_file, 'wb'))
        else:
            self.cache = OrderedDict()

            # Find the cache files. Must be of the form:
            # <year>-event_matches.p
            cache_file_pattern = ''.join([cache_directory, '/',
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
