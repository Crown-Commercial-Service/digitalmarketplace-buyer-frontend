# coding: utf-8
from __future__ import unicode_literals

from app.api_client.error import HTTPError
from app.helpers.login_helpers import generate_buyer_creation_token
from dmapiclient.audit import AuditTypes
from dmutils.email import generate_token, EmailError
from dmutils.forms import FakeCsrf
from ...helpers import BaseApplicationTest
from lxml import html
import mock
import pytest
from flask import session
import flask_featureflags as feature

EMAIL_SENT_MESSAGE = "send a link"

USER_CREATION_EMAIL_ERROR = "Failed to send user creation email."
PASSWORD_RESET_EMAIL_ERROR = "Failed to send password reset."

TOKEN_CREATED_BEFORE_PASSWORD_LAST_CHANGED_ERROR = "This password reset link is invalid."
USER_LINK_EXPIRED_ERROR = "The link you used to create an account may have expired."


def has_validation_errors(data, field_name):
    document = html.fromstring(data)

    form_field = document.xpath('//input[@name="{}"]'.format(field_name))
    return 'invalid' in form_field[0].classes or 'invalid' in form_field[0].getparent().classes


class TestLogin(BaseApplicationTest):

    def setup(self):
        super(TestLogin, self).setup()

        data_api_client_config = {'authenticate_user.return_value': self.user(
            123, "email@email.com", 1234, 'name', 'name'
        )}

        self._data_api_client = mock.patch(
            'app.main.views.login.data_api_client', **data_api_client_config
        )
        self.data_api_client_mock = self._data_api_client.start()

    def teardown(self):
        self._data_api_client.stop()

    def test_should_show_login_page(self):
        res = self.client.get(self.expand_path('/login'))
        assert res.status_code == 200
        assert 'private' in res.headers['Cache-Control']
        assert "Sign in to the Marketplace" in res.get_data(as_text=True)

    @mock.patch('app.main.views.login.data_api_client')
    def test_redirect_on_buyer_login(self, data_api_client):
        with self.app.app_context():
            data_api_client.authenticate_user.return_value = self.user(123, "email@email.com", None, None, 'Name')
            res = self.client.post(self.url_for('main.process_login'), data={
                'email_address': 'valid@email.com',
                'password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            })
            assert res.status_code == 302
            assert res.location == 'http://localhost/2/buyer-dashboard'
            assert 'Secure;' in res.headers['Set-Cookie']

    @mock.patch('app.main.views.login.data_api_client')
    def test_redirect_on_supplier_login(self, data_api_client):
        with self.app.app_context():
            data_api_client.authenticate_user.return_value = self.user(
                123,
                'email@email.com',
                None,
                None,
                'Name',
                role='supplier'
            )
            res = self.client.post(self.url_for('main.process_login'), data={
                'email_address': 'valid@email.com',
                'password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            })
            assert res.status_code == 302
            assert res.location == 'http://localhost' + \
                                   self.expand_path('/2/opportunities')
            assert 'Secure;' in res.headers['Set-Cookie']

    def test_should_redirect_logged_in_buyer(self):
        self.login_as_buyer()
        res = self.client.get(self.url_for('main.render_login'))
        assert res.status_code == 302
        assert res.location == 'http://localhost/2/buyer-dashboard'

    def test_should_strip_whitespace_surrounding_login_email_address_field(self):
        self.client.post(self.expand_path('/login'), data={
            'email_address': '  valid@email.com  ',
            'password': '1234567890',
            'csrf_token': FakeCsrf.valid_token,
        })
        self.data_api_client_mock.authenticate_user.assert_called_with('valid@email.com', '1234567890')

    def test_should_not_strip_whitespace_surrounding_login_password_field(self):
        self.client.post(self.expand_path('/login'), data={
            'email_address': 'valid@email.com',
            'password': '  1234567890  ',
            'csrf_token': FakeCsrf.valid_token,
        })
        self.data_api_client_mock.authenticate_user.assert_called_with(
            'valid@email.com', '  1234567890  ')

    @mock.patch('app.main.views.login.data_api_client')
    def test_ok_next_url_redirects_buyer_on_login(self, data_api_client):
        with self.app.app_context():
            data_api_client.authenticate_user.return_value = self.user(123, "email@email.com", None, None, 'Name')
            data = {
                'email_address': 'valid@email.com',
                'password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            }
            res = self.client.post(self.expand_path('/login?next={}'.format(self.expand_path('/bar-foo'))), data=data)
            assert res.status_code == 302
            assert res.location == 'http://localhost' + self.expand_path('/bar-foo')

    @mock.patch('app.main.views.login.data_api_client')
    def test_bad_next_url_redirects_user(self, data_api_client):
        with self.app.app_context():
            data_api_client.authenticate_user.return_value = self.user(123, "email@email.com", None, None, 'Name')
            data = {
                'email_address': 'valid@email.com',
                'password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            }
            res = self.client.post(self.expand_path('/login?next=http://badness.com'), data=data)
        assert res.status_code == 302
        assert res.location == 'http://localhost/2/buyer-dashboard'

    def test_should_have_cookie_on_redirect(self):
        with self.app.app_context():
            self.app.config['SESSION_COOKIE_DOMAIN'] = '127.0.0.1'
            self.app.config['SESSION_COOKIE_SECURE'] = True
            res = self.client.post(self.expand_path('/login'), data={
                'email_address': 'valid@email.com',
                'password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            })
            cookie_value = self.get_cookie_by_name(res, 'dm_session')
            assert cookie_value['dm_session'] is not None
            assert cookie_value["Domain"] == "127.0.0.1"

    def test_should_redirect_to_login_on_logout(self):
        res = self.client.get(self.expand_path('/logout'))
        assert res.status_code == 302
        assert res.location == 'http://localhost' + self.expand_path('/login')

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_return_a_403_for_invalid_login(self, data_api_client):
        data_api_client.authenticate_user.return_value = None

        res = self.client.post(self.expand_path('/login'), data={
            'email_address': 'valid@email.com',
            'password': '1234567890',
            'csrf_token': FakeCsrf.valid_token,
        })
        assert self.strip_all_whitespace("Make sure you've entered the right email address and password") \
            in self.strip_all_whitespace(res.get_data(as_text=True))
        assert res.status_code == 403

    def test_should_be_validation_error_if_no_email_or_password(self):
        res = self.client.post(self.expand_path('/login'), data={'csrf_token': FakeCsrf.valid_token})
        data = res.get_data(as_text=True)
        assert res.status_code == 400

        assert has_validation_errors(data, 'email_address')
        assert has_validation_errors(data, 'password')

    def test_should_be_validation_error_if_invalid_email(self):
        res = self.client.post(self.expand_path('/login'), data={
            'email_address': 'invalid',
            'password': '1234567890',
            'csrf_token': FakeCsrf.valid_token,
        })
        data = res.get_data(as_text=True)
        assert res.status_code == 400
        assert has_validation_errors(data, 'email_address')
        assert not has_validation_errors(data, 'password')

    def test_valid_email_formats(self):
        cases = [
            'good@example.com',
            'good-email@example.com',
            'good-email+plus@example.com',
            'good@subdomain.example.com',
            'good@hyphenated-subdomain.example.com',
        ]
        for address in cases:
            res = self.client.post(self.expand_path('/login'), data={
                'email_address': address,
                'password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            })
            data = res.get_data(as_text=True)
            assert res.status_code == 302, address

    def test_invalid_email_formats(self):
        cases = [
            '',
            'bad',
            'bad@@example.com',
            'bad @example.com',
            'bad@.com',
            'bad.example.com',
            '@',
            '@example.com',
            'bad@',
            'bad@example.com,bad2@example.com',
            'bad@example.com bad2@example.com',
            'bad@example.com,other.example.com',
        ]
        for address in cases:
            res = self.client.post(self.expand_path('/login'), data={
                'email_address': address,
                'password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            })
            data = res.get_data(as_text=True)
            assert res.status_code == 400, address
            assert has_validation_errors(data, 'email_address'), address


class TestLoginFormsNotAutofillable(BaseApplicationTest):
    def _forms_and_inputs_not_autofillable(self, url, expected_title):
        response = self.client.get(url)
        assert response.status_code == 200

        document = html.fromstring(response.get_data(as_text=True))

        page_title = document.xpath('//h1/text()')[0].strip()
        assert expected_title == page_title

        forms = document.xpath('//main[@id="content"]//form')

        for form in forms:
            assert form.get('autocomplete') == "off"
            non_hidden_inputs = form.xpath('//input[@type!="hidden"]')

            for input in non_hidden_inputs:
                if input.get('type') != 'submit':
                    assert input.get('autocomplete') == "off"

    def test_login_form_and_inputs_not_autofillable(self):
        self._forms_and_inputs_not_autofillable(
            self.expand_path('/login'),
            "Sign in to the Marketplace"
        )

    @pytest.mark.skip
    def test_request_password_reset_form_and_inputs_not_autofillable(self):
        self._forms_and_inputs_not_autofillable(
            self.expand_path('/reset-password'),
            "Reset password"
        )

    @pytest.mark.skip
    @mock.patch('app.main.views.login.data_api_client')
    def test_reset_password_form_and_inputs_not_autofillable(
            self, data_api_client
    ):
        data_api_client.get_user.return_value = self.user(
            123, "email@email.com", 1234, 'email', 'name'
        )

        with self.app.app_context():
            token = generate_token(
                {
                    "user": 123,
                    "email": 'email@email.com',
                },
                self.app.config['SECRET_KEY'],
                self.app.config['RESET_PASSWORD_SALT'])

            url = self.expand_path('/reset-password/{}').format(token)

        self._forms_and_inputs_not_autofillable(
            url,
            "Reset password",
        )


class TestBuyerRoleRequired(BaseApplicationTest):
    def test_login_required_for_buyer_pages(self):
        with self.app.app_context():
            res = self.client.get(self.expand_path('/buyers'))
            assert res.status_code == 302
            assert res.location.startswith('http://localhost' + self.expand_path('/login?next=%2F'))

    def test_supplier_cannot_access_buyer_pages(self):
        with self.app.app_context():
            self.login_as_supplier()
            res = self.client.get(self.expand_path('/buyers'))
            assert res.status_code == 302
            assert res.location.startswith('http://localhost' + self.expand_path('/login?next=%2F'))
            self.assert_flashes('buyer-role-required', expected_category='error')

    @pytest.mark.skip
    @mock.patch('app.buyers.views.buyers.render_component')
    def test_buyer_pages_ok_if_logged_in_as_buyer(self, render_component):
        props = {
            "team": {
                "currentUserName": "My Team",
                "teamName": "My Team name",
                "members": [],
                "teamBriefs": {
                    "all": [],
                    "draft": [],
                    "live": [],
                    "closed": []
                },
                "briefs": {
                    "all": [],
                    "draft": [],
                    "live": [],
                    "closed": []
                }
            }
        }
        render_component.return_value.get_props.return_value = props

        with self.app.app_context():
            self.login_as_buyer()
            res = self.client.get(self.expand_path('/buyers'))
            page_text = res.get_data(as_text=True)
            assert res.status_code == 200
            assert 'private' in res.headers['Cache-Control']
            if feature.is_active('TEAM_VIEW'):
                assert 'My Team' in page_text
                assert 'My Team name' in page_text


class TestTermsUpdate(BaseApplicationTest):

    payload = {
        'csrf_token': FakeCsrf.valid_token,
        'accept_terms': 'y',
    }

    def test_page_load(self):
        with self.app.app_context():
            self.login_as_buyer()
            res = self.client.get(self.url_for('main.terms_updated'))
            assert res.status_code == 200
            assert 'terms' in res.get_data(as_text=True)

    def test_login_required(self):
        with self.app.app_context():
            # Not logged in
            res = self.client.get(self.url_for('main.terms_updated'))
            assert res.status_code == 302

    @mock.patch('app.main.views.login.terms_of_use')
    @mock.patch('app.main.views.login.data_api_client')
    def test_submit(self, data_api_client, terms_of_use):
        with self.app.app_context():
            self.login_as_buyer(user_id=42)
            res = self.client.post(self.url_for('main.accept_updated_terms'), data=self.payload)
            data_api_client.update_user.assert_called_once_with(42, fields=mock.ANY)
            terms_of_use.set_session_flag.assert_called_once_with(False)
            assert res.status_code == 302

    @mock.patch('app.main.views.login.data_api_client')
    def test_submit_requires_login(self, data_api_client):
        with self.app.app_context():
            # Not logged in
            res = self.client.post(self.url_for('main.accept_updated_terms'), data=self.payload)
            data_api_client.update_user.assert_not_called()
            assert res.status_code == 302
            assert res.location.startswith(self.url_for('main.render_login', _external=True))

    @mock.patch('app.main.views.login.data_api_client')
    def test_submit_without_accepting(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data = dict(self.payload)
            data.pop('accept_terms')
            res = self.client.post(self.url_for('main.accept_updated_terms'), data=data)
            data_api_client.update_user.assert_not_called()
            assert res.status_code == 400
