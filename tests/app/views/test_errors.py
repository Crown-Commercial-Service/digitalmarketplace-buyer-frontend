# coding=utf-8

import mock
from nose.tools import assert_equal, assert_true
from dmapiclient import HTTPError
from ...helpers import BaseApplicationTest
import pytest


@pytest.mark.skipif(True, reason='gcloud out of scope')
@mock.patch('app.main.views.g_cloud.search_api_client')
class TestErrors(BaseApplicationTest):
    def test_404(self, search_api_mock):
        res = self.client.get('/g-cloud/service/1234')
        assert_equal(404, res.status_code)
        assert_true(
            "Check you've entered the correct web "
            "address or start again on the Digital Marketplace homepage."
            in res.get_data(as_text=True))
        assert_true(
            "If you can't find what you're looking for, email "
            "<a href=\"mailto:enquiries@digitalmarketplace.service.gov.uk?"
            "subject=Digital%20Marketplace%20feedback\" title=\"Please "
            "send feedback to enquiries@digitalmarketplace.service.gov.uk\">"
            "enquiries@digitalmarketplace.service.gov.uk</a>"
            in res.get_data(as_text=True))

    def test_500(self, search_api_mock):
        self.app.config['DEBUG'] = False

        api_response = mock.Mock()
        api_response.status_code = 503
        search_api_mock.search_services.side_effect = HTTPError(api_response)

        res = self.client.get('/g-cloud/search?q=email')
        assert_equal(503, res.status_code)
        assert_true(
            "Sorry, we're experiencing technical difficulties"
            in res.get_data(as_text=True))
        assert_true(
            "Try again later."
            in res.get_data(as_text=True))
