import mock
import pytest

from ...helpers import BaseApplicationTest


class TestGCloudIndexResults(BaseApplicationTest):
    def setup_method(self, method):
        super().setup_method(method)

        self._search_api_client_patch = mock.patch('app.main.views.g_cloud.search_api_client', autospec=True)
        self._search_api_client = self._search_api_client_patch.start()

        self.search_results = self._get_search_results_fixture_data()

        self._search_api_client.search.return_value = self.search_results
        self._search_api_client.aggregate.return_value = \
            self._get_fixture_data('g9_aggregations_fixture.json')

    def teardown_method(self, method):
        self._search_api_client_patch.stop()
        super().teardown_method(method)

    @pytest.mark.parametrize('lot', ('cloud-support', 'cloud-software', 'cloud-hosting', ''))
    def test_posting_lot_redirects_to_search_with_lot(self, lot):
        res = self.client.post(
            "/buyers/direct-award/g-cloud/choose-lot",
            data={"lot": lot}
        )

        assert res.status_code == 302
        assert res.location.endswith("/g-cloud/search" + f"?lot={lot}" if lot else "")

        redirect = self.client.get(res.location)
        assert redirect.status_code == 200

    def test_invalid_framework_family_post(self):
        res = self.client.post(
            "/buyers/direct-award/shakespeare/choose-lot",
            data={"lot": "cloud-hosting"}
        )
        assert res.status_code == 404

    def test_invalid_framework_family_get(self):
        res = self.client.get("/buyers/direct-award/shakespeare/choose-lot")
        assert res.status_code == 404
