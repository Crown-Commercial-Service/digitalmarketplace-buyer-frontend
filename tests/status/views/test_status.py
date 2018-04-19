import json

import mock

from ...helpers import BaseApplicationTest


class TestStatus(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)

        self.data_api_client_patch = mock.patch('app.status.views.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.search_api_client_patch = mock.patch('app.status.views.search_api_client', autospec=True)
        self.search_api_client = self.search_api_client_patch.start()

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        self.search_api_client_patch.stop()

    def test_should_return_200_from_elb_status_check(self):
        status_response = self.client.get('/_status?ignore-dependencies')
        assert status_response.status_code == 200
        assert self.data_api_client.called is False

    def test_status_ok(self):
        self.data_api_client.get_status.return_value = {
            'status': 'ok'
        }

        self.search_api_client.get_status.return_value = {
            'status': 'ok'
        }

        status_response = self.client.get('/_status')
        assert status_response.status_code == 200

        json_data = json.loads(status_response.get_data().decode('utf-8'))
        assert "{}".format(json_data['api_status']['status']) == "ok"
        assert "{}".format(json_data['search_api_status']['status']) == "ok"

    def test_status_error_in_one_upstream_api(self):
        self.data_api_client.get_status.return_value = {
            'status': 'error',
            'app_version': None,
            'message': 'Cannot connect to Database'
        }

        self.search_api_client.get_status.return_value = {
            'status': 'ok'
        }

        response = self.client.get('/_status')
        assert response.status_code == 500

        json_data = json.loads(response.get_data().decode('utf-8'))

        assert "{}".format(json_data['status']) == "error"
        assert "{}".format(json_data['api_status']['status']) == "error"
        assert "{}".format(json_data['search_api_status']['status']) == "ok"

    def test_status_no_response_in_one_upstream_api(self):

        self.data_api_client.get_status.return_value = {
            'status': 'ok'
        }

        self.search_api_client.get_status.return_value = None

        response = self.client.get('/_status')
        assert response.status_code == 500

        json_data = json.loads(response.get_data().decode('utf-8'))

        assert "{}".format(json_data['status']) == "error"
        assert "{}".format(json_data['api_status']['status']) == "ok"
        assert json_data.get('search_api_status') == {'status': 'n/a'}

    def test_status_error_in_two_upstream_apis(self):

        self.data_api_client.get_status.return_value = {
            'status': 'error',
            'app_version': None,
            'message': 'Cannot connect to Database'
        }

        self.search_api_client.get_status.return_value = {
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
