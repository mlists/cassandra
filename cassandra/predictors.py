from .data_store import DataStore
from trueskill import Rating, rate, global_env
import collections
import itertools
import math


class TrueSkillPredictor(object):

    def __init__(self, datastore: DataStore):
        self.datastore = datastore
        # Create the storage for all the TrueSkills
        # Keep them separated year-by-year - we assume that
        # team skills change from year to year.
        self.skills = collections.defaultdict(Rating)
        for year in self.datastore.data.keys():
            # Now process any historical matches already in the datastore
            for event_id in self.datastore.data[year]:
                print(event_id)
                matches = self.datastore.data[year][event_id]['matches']
                if matches is None:
                    break
                for match in matches:
                    self.update(match)

    def predict(self, blue_alliance: list, red_alliance: list):
        """Returns the likelihood of each alliance winning."""
        red = [self.skills[team] for team in red_alliance]
        blue = [self.skills[team] for team in blue_alliance]
        delta_mu = sum(r.mu for r in blue) - sum(r.mu for r in red)
        sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(blue, red))
        size = len(blue) + len(red)
        ts = global_env()
        denom = math.sqrt(size * (ts.beta ** 2) + sum_sigma)
        p = ts.cdf(delta_mu / denom)
        return (p, 1-p)

    def update(self, match_key: str):
        year = int(match_key[0:4])
        event = match_key.split('_')[0]
        # First add the match - update trueskills
        # Then iterate over all matches in the event so far until convergence
        innovation = self._update(match_key)
        # for current_match in self.datastore.data[year][event]['matches']:
        #     if current_match == match_key:
        #         break
        #     self._update(current_match)

    def _update(self, match_key: str):
        year = int(match_key[0:4])
        event = match_key.split('_')[0]

        alliances = (self.datastore.data[year][event]
                     ['matches'][match_key].alliances)
        red = alliances['red']['team_keys']
        blue = alliances['blue']['team_keys']

        red_ratings = [self.skills[team] for team in red]
        blue_ratings = [self.skills[team] for team in blue]
        # Calculating both ranks accounts for drawn matches
        ranks = [(alliances['red']['score'] < alliances['blue']['score'])*1,
                 (alliances['blue']['score'] < alliances['red']['score'])*1]
        new_red, new_blue = rate([red_ratings, blue_ratings], ranks=ranks)
        for team, rating in zip(red+blue, new_red+new_blue):
            self.skills[team] = rating
        # Return the "innovation" how much things changed because of the update
        return 0.0
