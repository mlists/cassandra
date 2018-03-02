"""Cassandra a prediction system for FRC games based on trueskill.
"""

from data_store import DataStore


class Cassandra:

    def __init__(self, key, years):
        """Initialise Cassandra
        Args:
            key: String of TBA key.
            years: List of the years in which to cache results.
        """

        self.years = years
        self.key = key
        self.data_store = DataStore(new_data_store=False, years=self.years)
