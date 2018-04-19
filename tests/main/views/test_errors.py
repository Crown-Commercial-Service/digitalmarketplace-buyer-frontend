# coding=utf-8
import mock

from dmapiclient import HTTPError

from ...helpers import BaseApplicationTest


class TestErrors(BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)
        self.search_api_client_patch = mock.patch('app.main.views.g_cloud.search_api_client', autospec=True)
        self.search_api_client = self.search_api_client_patch.start()

    def teardown_method(self, method):
        self.search_api_client_patch.stop()
        super().teardown_method(method)

    def test_404(self):
        res = self.client.get('/g-cloud/service/1234')
        assert res.status_code == 404
        assert "Check you've entered the correct web " \
            "address or start again on the Digital Marketplace homepage." \
            in res.get_data(as_text=True)
        assert "If you can't find what you're looking for, email " \
            "<a href=\"mailto:enquiries@digitalmarketplace.service.gov.uk?" \
            "subject=Digital%20Marketplace%20feedback\" title=\"Please " \
            "send feedback to enquiries@digitalmarketplace.service.gov.uk\">" \
            "enquiries@digitalmarketplace.service.gov.uk</a>" \
            in res.get_data(as_text=True)

    def test_410(self):
        res = self.client.get('/digital-services/framework')
        assert res.status_code == 410
        assert "Check you've entered the correct web " \
            "address or start again on the Digital Marketplace homepage." \
            in res.get_data(as_text=True)
        assert "If you can't find what you're looking for, email " \
            "<a href=\"mailto:enquiries@digitalmarketplace.service.gov.uk?" \
            "subject=Digital%20Marketplace%20feedback\" title=\"Please " \
            "send feedback to enquiries@digitalmarketplace.service.gov.uk\">" \
            "enquiries@digitalmarketplace.service.gov.uk</a>" \
            in res.get_data(as_text=True)

    def test_500(self):
        self.app.config['DEBUG'] = False

        api_response = mock.Mock()
        api_response.status_code = 503
        self.search_api_client.search.side_effect = HTTPError(api_response)

        res = self.client.get('/g-cloud/search?q=email')
        assert res.status_code == 503
        assert "Sorry, we're experiencing technical difficulties" in res.get_data(as_text=True)
        assert "Try again later." in res.get_data(as_text=True)
