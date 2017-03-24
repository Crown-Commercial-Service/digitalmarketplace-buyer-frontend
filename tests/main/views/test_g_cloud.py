import mock
import pytest
from ...helpers import BaseApplicationTest


class TestGCloudIndexResults(BaseApplicationTest):
    def setup_method(self, method):
        super(TestGCloudIndexResults, self).setup_method(method)

        self._search_api_client = mock.patch('app.main.views.g_cloud.search_api_client').start()

        self.search_results = self._get_search_results_fixture_data()

    def teardown_method(self, method):
        self._search_api_client.stop()

    @pytest.mark.parametrize('feature_flag_gcloud9, search_box_visible', ((True, False), (False, True)))
    def test_renders_correct_search_links(self, feature_flag_gcloud9, search_box_visible):
        self.app.config['FEATURE_FLAGS_GCLOUD9'] = feature_flag_gcloud9
        self._search_api_client.search_services.return_value = self.search_results

        res = self.client.get('/g-cloud')
        assert res.status_code == 200
        assert ('form action="/g-cloud/search' in res.get_data(as_text=True)) == search_box_visible
        assert '/g-cloud/search?lot=saas' in res.get_data(as_text=True)
        assert '/g-cloud/search?lot=scs' in res.get_data(as_text=True)
        assert '/g-cloud/search?lot=paas' in res.get_data(as_text=True)
        assert '/g-cloud/search?lot=iaas' in res.get_data(as_text=True)
