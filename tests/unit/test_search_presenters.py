import os
import json
import unittest

from Mock import mock


def _get_fixture_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


class TestSearchResults(unittest.TestCase):

    def setUp(self):
        self.fixture = _get_fixture_data()['services']
        self.service = Service(self.fixture)

    def tearDown(self):
        pass

    def test_search_results_is_set(self):
        search_results = SearchResults(self.fixture)
        self.assert

