import mock
from nose.tools import assert_equal, assert_true
from ...helpers import BaseApplicationTest


class TestSearchResults(BaseApplicationTest):
    def setup(self):
        super(TestSearchResults, self).setup()

        self._search_api_client = mock.patch(
            'app.main.views.search_api_client'
        ).start()

        self.search_results = self._get_search_results_fixture_data()

    def teardown(self):
        self._search_api_client.stop()

    def test_search_page_results_service_links(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/search?q=email')
        assert_equal(200, res.status_code)
        assert_true(
            '<a href="/services/5-G3-0279-010">CDN VDMS</a>'
            in res.get_data(as_text=True))
