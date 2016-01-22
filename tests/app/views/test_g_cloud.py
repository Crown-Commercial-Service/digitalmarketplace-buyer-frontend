import mock
from nose.tools import assert_equal, assert_true
from ...helpers import BaseApplicationTest


class TestGCloudIndexResults(BaseApplicationTest):
    def setup(self):
        super(TestGCloudIndexResults, self).setup()

        self._search_api_client = mock.patch(
            'app.main.views.g_cloud.search_api_client'
        ).start()

        self.search_results = self._get_search_results_fixture_data()

    def teardown(self):
        self._search_api_client.stop()

    def test_renders_correct_search_links(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud')
        assert_equal(200, res.status_code)
        assert_true(
            'form action="/g-cloud/search'
            in res.get_data(as_text=True))
        assert_true(
            '/g-cloud/search?lot=saas'
            in res.get_data(as_text=True))
        assert_true(
            '/g-cloud/search?lot=scs'
            in res.get_data(as_text=True))
        assert_true(
            '/g-cloud/search?lot=paas'
            in res.get_data(as_text=True))
        assert_true(
            '/g-cloud/search?lot=iaas'
            in res.get_data(as_text=True))
