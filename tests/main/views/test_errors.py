# coding=utf-8
import mock
import pytest
from wtforms import ValidationError
from werkzeug.exceptions import BadRequest, ServiceUnavailable, InternalServerError

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

        html = res.get_data(as_text=True)
        assert (
            "Check you’ve entered the correct web address"
            " or start again on the Digital Marketplace homepage." in html
        )
        assert (
            "If you can’t find what you’re looking for, contact us at "
            '<a class="govuk-link" href="mailto:cloud_digital@crowncommercial.gov.uk?'
            'subject=Digital%20Marketplace%20feedback" title="Please '
            'send feedback to cloud_digital@crowncommercial.gov.uk">'
            "cloud_digital@crowncommercial.gov.uk</a>" in html
        )

    def test_410(self):
        res = self.client.get('/digital-services/framework')
        assert res.status_code == 410
        assert "Page no longer available" in res.get_data(as_text=True)
        assert "The page you requested is no longer available on the Digital Marketplace." \
            in res.get_data(as_text=True)

    @pytest.mark.parametrize(
        'exception, expected_status_code', [
            (InternalServerError, 500), (ServiceUnavailable, 503)
        ]
    )
    def test_500(self, exception, expected_status_code):
        self.app.config['DEBUG'] = False
        self.search_api_client.search.side_effect = exception()

        res = self.client.get('/g-cloud/search?q=email')
        assert res.status_code == expected_status_code
        assert "Sorry, we’re experiencing technical difficulties" in res.get_data(as_text=True)
        assert "Try again later." in res.get_data(as_text=True)

    def test_non_csrf_400(self):
        self.search_api_client.search.side_effect = BadRequest()

        res = self.client.get('/g-cloud/search?q=email')

        assert res.status_code == 400
        assert "Sorry, there was a problem with your request" in res.get_data(as_text=True)
        assert "Please do not attempt the same request again." in res.get_data(as_text=True)

    @mock.patch('flask_wtf.csrf.validate_csrf', autospec=True)
    def test_csrf_handler_redirects_to_login(self, validate_csrf):
        self.login_as_buyer()
        with self.app.app_context():
            self.app.config['WTF_CSRF_ENABLED'] = True
            self.client.set_cookie(
                "localhost",
                self.app.config['DM_COOKIE_PROBE_COOKIE_NAME'],
                self.app.config['DM_COOKIE_PROBE_COOKIE_VALUE'],
            )

            # This will raise a CSRFError for us when the form is validated
            validate_csrf.side_effect = ValidationError('The CSRF session token is missing.')

            res = self.client.post(
                '/buyers/direct-award/g-cloud-9/save-search', data={'some': 'data'},
            )

            self.assert_flashes("Your session has expired. Please log in again.", expected_category="error")
            assert res.status_code == 302

            # POST requests will not preserve the request path on redirect
            assert res.location == 'http://localhost/user/login'
            assert validate_csrf.call_args_list == [mock.call(None)]
