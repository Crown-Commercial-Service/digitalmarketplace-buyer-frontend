import mock

from lxml import html

from ...helpers import BaseApplicationTest


class TestGCloudIndexResults(BaseApplicationTest):
    def setup_method(self, method):
        super().setup_method(method)

        self._search_api_client_patch = mock.patch('app.main.views.g_cloud.search_api_client', autospec=True)
        self._search_api_client = self._search_api_client_patch.start()

        self.search_results = self._get_search_results_fixture_data()

    def teardown_method(self, method):
        self._search_api_client_patch.stop()
        super().teardown_method(method)

    def test_renders_correct_search_links(self):
        self._search_api_client.search.return_value = self.search_results

        res = self.client.get("/buyers/direct-award/g-cloud/choose-lot")
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        assert doc.xpath("//form[@action=$u]", u="/g-cloud/search")
        # at least one link into a specific lot
        assert doc.xpath("//a[starts-with(@href, $u)]", u="/g-cloud/search?lot=")
