import mock
import pytest
from ...helpers import BaseApplicationTest

from app import data_api_client


class TestGCloudIndexResults(BaseApplicationTest):
    def setup_method(self, method):
        super(TestGCloudIndexResults, self).setup_method(method)

        self._search_api_client = mock.patch('app.main.views.g_cloud.search_api_client').start()

        self.search_results = self._get_search_results_fixture_data()

    def teardown_method(self, method):
        self._search_api_client.stop()

    def test_renders_correct_search_links(self):
        self._search_api_client.search_services.return_value = self.search_results

        res = self.client.get('/g-cloud')
        assert res.status_code == 200
        assert 'form action="/g-cloud/search' in res.get_data(as_text=True)
        assert '/g-cloud/search?lot=' in res.get_data(as_text=True)  # at least one link into a specific lot
