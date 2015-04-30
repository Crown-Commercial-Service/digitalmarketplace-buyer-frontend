import json
from flask import jsonify
from ..helpers import BaseApplicationTest

import mock
from nose.tools import assert_equal, assert_in


class TestStatus(BaseApplicationTest):

    def test_status_ok(self):
        with self.app.test_request_context():
            api_response = jsonify(
                status='ok'
            )
            api_response.status_code = 200

            _api_response = mock.patch(
                'app.status.utils.return_response_from_api_status_call',
                return_value=api_response
            ).start()

            status_response = self.client.get('/_status')
            assert_equal(200, status_response.status_code)

            json_data = json.loads(status_response.get_data())
            assert_equal("ok",
                         "{}".format(json_data['api_status']['status']))
            assert_equal("ok",
                         "{}".format(json_data['search_api_status']['status']))

            _api_response.stop()

    def test_status_api_responses_return_500(self):
        with self.app.test_request_context():
            api_response = jsonify(
                status='error'
            )
            api_response.status_code = 500

            _api_response = mock.patch(
                'app.status.utils.return_response_from_api_status_call',
                return_value=api_response
            ).start()

            status_response = self.client.get('/_status')
            assert_equal(500, status_response.status_code)

            json_data = json.loads(status_response.get_data())
            assert_equal("error",
                         "{}".format(json_data['api_status']['status']))
            assert_equal("error",
                         "{}".format(json_data['search_api_status']['status']))
            assert_in("Error connecting to",
                      "{}".format(json_data['message']))

            _api_response.stop()

    def test_status_api_responses_are_none(self):
        with self.app.test_request_context():

            _api_response = mock.patch(
                'app.status.utils.return_response_from_api_status_call',
                return_value=None
            ).start()

            status_response = self.client.get('/_status')
            assert_equal(500, status_response.status_code)

            json_data = json.loads(status_response.get_data())
            assert_equal(None, json_data['api_status'])
            assert_equal(None, json_data['search_api_status'])

            assert_in("Error connecting to",
                      "{}".format(json_data['message']))

            _api_response.stop()
