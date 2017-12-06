import mock
from ...helpers import BaseApplicationTest


class TestGCloudIndexResults(BaseApplicationTest):
    def setup_method(self, method):
        super(TestGCloudIndexResults, self).setup_method(method)

        self._search_api_client_patch = mock.patch('app.main.views.g_cloud.search_api_client', autospec=True)
        self._search_api_client = self._search_api_client_patch.start()

        self.search_results = self._get_search_results_fixture_data()

    def teardown_method(self, method):
        self._search_api_client_patch.stop()

    def test_renders_correct_search_links(self):
        self._search_api_client.search.return_value = self.search_results

        res = self.client.get('/g-cloud')
        assert res.status_code == 200
        assert 'form action="/g-cloud/search' in res.get_data(as_text=True)
        assert '/g-cloud/search?lot=' in res.get_data(as_text=True)  # at least one link into a specific lot
