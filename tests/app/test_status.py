import json
from ..helpers import BaseApplicationTest

import mock
from nose.tools import assert_equal, assert_false


class TestStatus(BaseApplicationTest):

    def setup(self):
        super(TestStatus, self).setup()

        self._data_api_client = mock.patch(
            'app.status.views.data_api_client'
        ).start()

    def teardown(self):
        self._data_api_client.stop()

    @mock.patch('app.status.views.data_api_client')
    def test_should_return_200_from_elb_status_check(self, data_api_client):
        status_response = self.client.get(self.expand_path('/_status?ignore-dependencies'))
        assert_equal(200, status_response.status_code)
        assert_false(data_api_client.called)

    def test_status_ok(self):
        self._data_api_client.get_status.return_value = {
            'status': 'ok'
        }

        status_response = self.client.get(self.expand_path('/_status'))
        assert_equal(200, status_response.status_code)

        json_data = json.loads(status_response.get_data().decode('utf-8'))
        assert_equal(
            "ok", "{}".format(json_data['api_status']['status']))

    def test_status_error_in_one_upstream_api(self):
        self._data_api_client.get_status.return_value = {
            'status': 'error',
            'app_version': None,
            'message': 'Cannot connect to Database'
        }

        response = self.client.get(self.expand_path('/_status'))
        assert_equal(500, response.status_code)

        json_data = json.loads(response.get_data().decode('utf-8'))

        assert_equal("error", "{}".format(json_data['status']))
        assert_equal("error", "{}".format(json_data['api_status']['status']))

    def test_status_no_response_in_one_upstream_api(self):

        self._data_api_client.get_status.return_value = None

        response = self.client.get(self.expand_path('/_status'))
        assert_equal(500, response.status_code)

        json_data = json.loads(response.get_data().decode('utf-8'))

        assert_equal("error", "{}".format(json_data['status']))
        assert_equal(None, json_data.get('api_status'))
