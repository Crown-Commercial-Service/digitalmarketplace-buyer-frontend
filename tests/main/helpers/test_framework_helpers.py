import mock
import pytest

from dmapiclient import HTTPError
from dmutils.api_stubs import framework

from app.main.helpers.framework_helpers import get_framework_or_500, get_latest_live_framework, get_lots_by_slug
from ...helpers import BaseApplicationTest, CustomAbortException


class TestBuildSearchQueryHelpers(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)

        self.available_frameworks = self._get_frameworks_list_fixture_data().get('frameworks')

    def test_get_latest_live_framework(self):
        latest_framework_when_fixture_updated = 'g-cloud-9'  # fixture set in base class
        latest_framework_data = get_latest_live_framework(self.available_frameworks, 'g-cloud')
        assert latest_framework_data['slug'] == latest_framework_when_fixture_updated

    def test_get_lots_by_slug(self):
        g_cloud_9_data = next((f for f in self.available_frameworks if f['slug'] == 'g-cloud-9'))
        lots_by_slug = get_lots_by_slug(g_cloud_9_data)
        assert lots_by_slug['cloud-hosting'] == g_cloud_9_data['lots'][0]
        assert lots_by_slug['cloud-software'] == g_cloud_9_data['lots'][1]
        assert lots_by_slug['cloud-support'] == g_cloud_9_data['lots'][2]


class TestGetFrameworkOr500():
    def test_returns_framework(self):
        data_api_client_mock = mock.Mock()
        data_api_client_mock.get_framework.return_value = framework()

        assert get_framework_or_500(data_api_client_mock, 'g-cloud-7')['slug'] == 'g-cloud-7'

    @mock.patch('app.main.helpers.framework_helpers.abort')
    def test_aborts_with_500_if_framework_not_found(self, abort):
        data_api_client_mock = mock.Mock()
        data_api_client_mock.get_framework.side_effect = HTTPError(mock.Mock(status_code=404), 'Framework not found')
        abort.side_effect = CustomAbortException()

        with pytest.raises(CustomAbortException):
            get_framework_or_500(data_api_client_mock, 'g-cloud-7')

        assert abort.call_args_list == [
            mock.call(500, 'Framework not found: g-cloud-7')
        ]

    def test_raises_original_error_if_not_404(self):
        data_api_client_mock = mock.Mock()
        data_api_client_mock.get_framework.side_effect = HTTPError(mock.Mock(status_code=400), 'Original exception')

        with pytest.raises(HTTPError) as original_exception:
            get_framework_or_500(data_api_client_mock, 'g-cloud-7')

        assert original_exception.value.message == 'Original exception'
        assert original_exception.value.status_code == 400

    @mock.patch('app.main.helpers.framework_helpers.abort')
    def test_calls_logger_if_provided(self, abort):
        data_api_client_mock = mock.Mock()
        logger_mock = mock.Mock()
        data_api_client_mock.get_framework.side_effect = HTTPError(mock.Mock(status_code=404), 'An error from the API')

        get_framework_or_500(data_api_client_mock, 'g-cloud-7', logger_mock)

        assert logger_mock.error.call_args_list == [
            mock.call(
                'Framework not found. Error: {error}, framework_slug: {framework_slug}',
                extra={'error': 'An error from the API (status: 404)', 'framework_slug': 'g-cloud-7'},
            )
        ]
