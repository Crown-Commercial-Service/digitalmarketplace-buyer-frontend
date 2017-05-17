import json
from ...helpers import BaseApplicationTest

import mock


class TestStatus(BaseApplicationTest):

    def setup_method(self, method):
        super(TestStatus, self).setup_method(method)

        self._data_api_client = mock.patch(
            'app.status.views.data_api_client'
        ).start()
        self._search_api_client = mock.patch(
            'app.status.views.search_api_client'
        ).start()

    def teardown_method(self, method):
        self._data_api_client.stop()
        self._search_api_client.stop()

    @mock.patch('app.status.views.data_api_client')
    def test_should_return_200_from_elb_status_check(self, data_api_client):
        status_response = self.client.get('/_status?ignore-dependencies')
        assert status_response.status_code == 200
        assert data_api_client.called is False

    def test_status_ok(self):
        self._data_api_client.get_status.return_value = {
            'status': 'ok'
        }

        self._search_api_client.get_status.return_value = {
            'status': 'ok'
        }

        status_response = self.client.get('/_status')
        assert status_response.status_code == 200

        json_data = json.loads(status_response.get_data().decode('utf-8'))
        assert "{}".format(json_data['api_status']['status']) == "ok"
        assert "{}".format(json_data['search_api_status']['status']) == "ok"

    def test_status_error_in_one_upstream_api(self):
        self._data_api_client.get_status.return_value = {
            'status': 'error',
            'app_version': None,
            'message': 'Cannot connect to Database'
        }

        self._search_api_client.get_status.return_value = {
            'status': 'ok'
        }

        response = self.client.get('/_status')
        assert response.status_code == 500

        json_data = json.loads(response.get_data().decode('utf-8'))

        assert "{}".format(json_data['status']) == "error"
        assert "{}".format(json_data['api_status']['status']) == "error"
        assert "{}".format(json_data['search_api_status']['status']) == "ok"

    def test_status_no_response_in_one_upstream_api(self):

        self._data_api_client.get_status.return_value = {
            'status': 'ok'
        }

        self._search_api_client.get_status.return_value = None

        response = self.client.get('/_status')
        assert response.status_code == 500

        json_data = json.loads(response.get_data().decode('utf-8'))

        assert "{}".format(json_data['status']) == "error"
        assert "{}".format(json_data['api_status']['status']) == "ok"
        assert json_data.get('search_api_status') is None

    def test_status_error_in_two_upstream_apis(self):

        self._data_api_client.get_status.return_value = {
            'status': 'error',
            'app_version': None,
            'message': 'Cannot connect to Database'
        }

        self._search_api_client.get_status.return_value = {
            'status': 'error',
            'app_version': None,
            'message': 'Cannot connect to elasticsearch'
        }

        response = self.client.get('/_status')
        assert response.status_code == 500

        json_data = json.loads(response.get_data().decode('utf-8'))

        assert "{}".format(json_data['status']) == "error"
        assert "{}".format(json_data['api_status']['status']) == "error"
        assert "{}".format(json_data['search_api_status']['status']) == "error"

    @mock.patch('app.status.views.current_app')
    def test_status_ip_logged_if_x_forwarded_for_header_present(self, current_app):
        self._data_api_client.get_status.return_value = {
            'status': 'ok'
        }

        self._search_api_client.get_status.return_value = {
            'status': 'ok'
        }

        current_app.config = {'VERSION': '1'}

        status_response = self.client.get(
            '/_status',
            headers={'X-Forwarded-For': '0.0.0.0, 0.0.0.0, 0.0.0.0, 127.0.0.23'}
        )
        assert status_response.status_code == 200

        current_app.logger.info.assert_called_once_with(
            "_status.check: buyer app status page requested by {ip_address}",
            extra={'ip_address': '127.0.0.23'}
        )

        json_data = json.loads(status_response.get_data().decode('utf-8'))
        assert json_data['remote_address'] == "127.0.0.23"

    @mock.patch('app.status.views.current_app')
    @mock.patch('app.status.views.request')
    def test_status_remote_addr_logged_if_x_forwarded_for_header_not_present(self, request, current_app):
        self._data_api_client.get_status.return_value = {
            'status': 'ok'
        }

        self._search_api_client.get_status.return_value = {
            'status': 'ok'
        }

        current_app.config = {'VERSION': '1'}

        request.remote_addr = '127.0.0.24'
        status_response = self.client.get(
            '/_status',
            headers={}
        )
        assert status_response.status_code == 200

        current_app.logger.info.assert_called_once_with(
            "_status.check: buyer app status page requested by {ip_address}",
            extra={'ip_address': '127.0.0.24'}
        )

        json_data = json.loads(status_response.get_data().decode('utf-8'))
        assert json_data['remote_address'] == "127.0.0.24"

    @mock.patch('app.status.views.current_app')
    @mock.patch('app.status.views.request')
    def test_status_untrackable_logged_if_x_forwarded_for_and_remote_addr_not_present(self, request, current_app):
        self._data_api_client.get_status.return_value = {
            'status': 'ok'
        }

        self._search_api_client.get_status.return_value = {
            'status': 'ok'
        }

        current_app.config = {'VERSION': '1'}

        request.remote_addr = None
        status_response = self.client.get(
            '/_status',
            headers={}
        )
        assert status_response.status_code == 200

        current_app.logger.info.assert_called_once_with(
            "_status.check: buyer app status page requested by {ip_address}",
            extra={'ip_address': 'untrackable'}
        )

        json_data = json.loads(status_response.get_data().decode('utf-8'))
        assert json_data['remote_address'] == "untrackable"
