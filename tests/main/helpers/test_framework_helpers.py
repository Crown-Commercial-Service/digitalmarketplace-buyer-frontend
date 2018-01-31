from app import data_api_client
from app.main.helpers import framework_helpers

from ...helpers import BaseApplicationTest


class TestBuildSearchQueryHelpers(BaseApplicationTest):
    def test_get_latest_live_framework(self):
        latest_framework_when_fixture_updated = 'g-cloud-9'  # fixture set in base class

        latest_framework_data = framework_helpers.get_latest_live_framework(
            data_api_client.find_frameworks().get('frameworks'),
            'g-cloud'
        )
        assert latest_framework_data['slug'] == latest_framework_when_fixture_updated

    def test_get_lots_by_slug(self):
        g_cloud_9_data = next((f for f in data_api_client.find_frameworks().get('frameworks')
                               if f['slug'] == 'g-cloud-9'))
        lots_by_slug = framework_helpers.get_lots_by_slug(g_cloud_9_data)
        assert lots_by_slug['cloud-hosting'] == g_cloud_9_data['lots'][0]
        assert lots_by_slug['cloud-software'] == g_cloud_9_data['lots'][1]
        assert lots_by_slug['cloud-support'] == g_cloud_9_data['lots'][2]
