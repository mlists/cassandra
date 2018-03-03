from .data_store import DataStore
from trueskill import Rating, rate


class TrueSkillPredictor(object):

    def __init__(self, datastore: DataStore):
        self.datastore = datastore
        # Create the storage for all the TrueSkills
        # Keep them separated year-by-year - we assume that
        # team skills change from year to year.
        self.skills = {}
        for year in self.datastore.data.keys():
            self.skills[year] = {}
            # Now process any historical matches already in the datastore
            for event_id in self.datastore.data[year]:
                print(event_id)
                matches = self.datastore.data[year][event_id]['matches']
                for match in matches:
                    self.update(match)

    def predict(self, blue_alliance: list, red_alliance: list):
        """Returns the likelihood of each alliance winning."""
        return (0.5, 0.5)

    def update(self, match_key: str):
        # First add the match - update trueskills
        # Then iterate over all matches in the event so far until convergence
        innovation = self._update(match_key)

    def _update(self, match_key: str):
        year = int(match_key[0:4])
        event = match_key.split('_')[0]

        alliances = self.datastore.data[year][event]['matches'][match_key].alliances
        red = alliances['red']['team_keys']
        blue = alliances['blue']['team_keys']
        for key in red+blue:
            if not self.skills[year].get(key):
                self.skills[year][key] = Rating()

        red_ratings = [self.skills[year][team] for team in red]
        blue_ratings = [self.skills[year][team] for team in blue]
        # Calculating both ranks accounts for drawn matches
        ranks = [alliances['red']['score'] < alliances['blue']['score'], 
                alliances['blue']['score'] < alliances['red']['score']]
        new_red, new_blue = rate([red_ratings, blue_ratings], ranks=ranks)
        # Return the "innovation" how much things changed because of the update
        return 0.0

