# coding: utf-8
from __future__ import unicode_literals

from app.api_client.error import HTTPError
from app.helpers.form_helpers import FakeCsrf
from dmapiclient.audit import AuditTypes
from dmutils.email import generate_token, EmailError
from ...helpers import BaseApplicationTest
from lxml import html
import mock
import pytest

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
        assert "Log in with your buyer account" in res.get_data(as_text=True)

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_redirect_to_search_on_buyer_login(self, data_api_client):
        with self.app.app_context():
            data_api_client.authenticate_user.return_value = self.user(123, "email@email.com", None, None, 'Name')
            res = self.client.post(self.expand_path('/login'), data={
                'email_address': 'valid@email.com',
                'password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            })
            assert res.status_code == 302
            assert res.location == 'http://localhost' + self.expand_path('/search/suppliers')
            assert 'Secure;' in res.headers['Set-Cookie']

    def test_should_redirect_logged_in_buyer_to_search(self):
        self.login_as_buyer()
        res = self.client.get(self.expand_path('/login'))
        assert res.status_code == 302
        assert res.location == 'http://localhost' + self.expand_path('/search/suppliers')

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
    def test_bad_next_url_takes_buyer_user_to_search(self, data_api_client):
        with self.app.app_context():
            data_api_client.authenticate_user.return_value = self.user(123, "email@email.com", None, None, 'Name')
            data = {
                'email_address': 'valid@email.com',
                'password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            }
            res = self.client.post(self.expand_path('/login?next=http://badness.com'), data=data)
        assert res.status_code == 302
        assert res.location == 'http://localhost' + self.expand_path('/search/suppliers')

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
            assert cookie_value['Secure; HttpOnly; Path'] == '/'
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
        res = self.client.post(self.expand_path('/login'), data={})
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


class TestResetPassword(BaseApplicationTest):

    _user = None

    def setup(self):
        super(TestResetPassword, self).setup()

        data_api_client_config = {'get_user.return_value': self.user(
            123, "email@email.com", 1234, 'name', 'Name'
        )}

        self._user = {
            "user": 123,
            "email": 'email@email.com',
        }

        self._data_api_client = mock.patch(
            'app.main.views.login.data_api_client', **data_api_client_config
        )
        self.data_api_client_mock = self._data_api_client.start()

    def teardown(self):
        self._data_api_client.stop()

    def test_email_should_not_be_empty(self):
        res = self.client.post(self.expand_path('/reset-password'), data={'csrf_token': FakeCsrf.valid_token})
        data = res.get_data(as_text=True)
        assert res.status_code == 400
        assert has_validation_errors(data, 'email_address')

    def test_email_should_be_valid(self):
        res = self.client.post(self.expand_path('/reset-password'), data={
            'email_address': 'invalid',
            'csrf_token': FakeCsrf.valid_token,
        })
        data = res.get_data(as_text=True)
        assert res.status_code == 400
        assert has_validation_errors(data, 'email_address')

    @mock.patch('app.main.views.login.send_email')
    def test_redirect_to_same_page_on_success(self, send_email):
        res = self.client.post(self.expand_path('/reset-password'), data={
            'email_address': 'email@email.com',
            'csrf_token': FakeCsrf.valid_token,
        })
        assert res.status_code == 302
        assert res.location == 'http://localhost' + self.expand_path('/reset-password')

    @mock.patch('app.main.views.login.send_email')
    def test_show_email_sent_message_on_success(self, send_email):
        res = self.client.post(self.expand_path('/reset-password'), data={
            'email_address': 'email@email.com',
            'csrf_token': FakeCsrf.valid_token,
        }, follow_redirects=True)
        assert res.status_code == 200
        content = self.strip_all_whitespace(res.get_data(as_text=True))
        assert self.strip_all_whitespace(EMAIL_SENT_MESSAGE) in content

    @mock.patch('app.main.views.login.send_email')
    def test_should_strip_whitespace_surrounding_reset_password_email_address_field(self, send_email):
        self.client.post(self.expand_path('/reset-password'), data={
            'email_address': ' email@email.com',
            'csrf_token': FakeCsrf.valid_token,
        })
        self.data_api_client_mock.get_user.assert_called_with(email_address='email@email.com')

    def test_email_should_be_decoded_from_token(self):
        with self.app.app_context():
            token = generate_token(
                self._user,
                self.app.config['SECRET_KEY'],
                self.app.config['RESET_PASSWORD_SALT'])
            url = self.expand_path('/reset-password/{}').format(token)

        res = self.client.get(url)
        assert res.status_code == 200
        assert "Reset password for email@email.com" in res.get_data(as_text=True)
        assert 'private' in res.headers['Cache-Control']

    def test_password_should_not_be_empty(self):
        with self.app.app_context():
            token = generate_token(
                self._user,
                self.app.config['SECRET_KEY'],
                self.app.config['RESET_PASSWORD_SALT'])
            url = self.expand_path('/reset-password/{}').format(token)

            res = self.client.post(url, data={
                'password': '',
                'confirm_password': '',
                'csrf_token': FakeCsrf.valid_token,
            })
            data = res.get_data(as_text=True)
            assert res.status_code == 400
            assert has_validation_errors(data, 'password')
            assert has_validation_errors(data, 'confirm_password')

    def test_password_should_be_over_ten_chars_long(self):
        with self.app.app_context():
            token = generate_token(
                self._user,
                self.app.config['SECRET_KEY'],
                self.app.config['RESET_PASSWORD_SALT'])
            url = self.expand_path('/reset-password/{}').format(token)

            res = self.client.post(url, data={
                'password': '123456789',
                'confirm_password': '123456789',
                'csrf_token': FakeCsrf.valid_token,
            })
            data = res.get_data(as_text=True)
            assert res.status_code == 400
            assert has_validation_errors(data, 'password')

    def test_password_should_be_under_51_chars_long(self):
        with self.app.app_context():
            token = generate_token(
                self._user,
                self.app.config['SECRET_KEY'],
                self.app.config['RESET_PASSWORD_SALT'])
            url = self.expand_path('/reset-password/{}').format(token)

            res = self.client.post(url, data={
                'password':
                    '123456789012345678901234567890123456789012345678901',
                'confirm_password':
                    '123456789012345678901234567890123456789012345678901',
                'csrf_token': FakeCsrf.valid_token,
            })
            data = res.get_data(as_text=True)
            assert res.status_code == 400
            assert has_validation_errors(data, 'password')

    def test_passwords_should_match(self):
        with self.app.app_context():
            token = generate_token(
                self._user,
                self.app.config['SECRET_KEY'],
                self.app.config['RESET_PASSWORD_SALT'])
            url = self.expand_path('/reset-password/{}').format(token)

            res = self.client.post(url, data={
                'password': '1234567890',
                'confirm_password': '0123456789',
                'csrf_token': FakeCsrf.valid_token,
            })
            assert res.status_code == 400

            assert not has_validation_errors(res.get_data(as_text=True), 'password')
            assert has_validation_errors(res.get_data(as_text=True), 'confirm_password')

    def test_redirect_to_login_page_on_success(self):
        with self.app.app_context():
            token = generate_token(
                self._user,
                self.app.config['SECRET_KEY'],
                self.app.config['RESET_PASSWORD_SALT'])
            url = self.expand_path('/reset-password/{}').format(token)

            res = self.client.post(url, data={
                'password': '1234567890',
                'confirm_password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            })
            assert res.status_code == 302
            assert res.location == 'http://localhost' + self.expand_path('/login')

    def test_should_not_strip_whitespace_surrounding_reset_password_password_field(self):
        with self.app.app_context():
            token = generate_token(
                self._user,
                self.app.config['SECRET_KEY'],
                self.app.config['RESET_PASSWORD_SALT'])
            url = self.expand_path('/reset-password/{}').format(token)

            res = self.client.post(url, data={
                'password': '  1234567890',
                'confirm_password': '  1234567890',
                'csrf_token': FakeCsrf.valid_token,
            })
            assert res.status_code == 302
            self.data_api_client_mock.update_user_password.assert_called_with(
                self._user.get('user'), '  1234567890', self._user.get('email'))

    @mock.patch('app.main.views.login.data_api_client')
    def test_token_created_before_last_updated_password_cannot_be_used(
            self, data_api_client
    ):
        with self.app.app_context():
            data_api_client.get_user.return_value = self.user(
                123, "email@email.com", 1234, 'email', 'Name', is_token_valid=False
            )
            token = generate_token(
                self._user,
                self.app.config['SECRET_KEY'],
                self.app.config['RESET_PASSWORD_SALT'])
            url = self.expand_path('/reset-password/{}').format(token)

            res = self.client.post(url, data={
                'password': '1234567890',
                'confirm_password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            }, follow_redirects=True)

            assert res.status_code == 200
            assert TOKEN_CREATED_BEFORE_PASSWORD_LAST_CHANGED_ERROR in res.get_data(as_text=True)

    @mock.patch('app.main.views.login.send_email')
    def test_should_call_send_email_with_correct_params(
            self, send_email
    ):
        with self.app.app_context():

            self.app.config['DM_MANDRILL_API_KEY'] = "API KEY"
            self.app.config['RESET_PASSWORD_EMAIL_SUBJECT'] = "SUBJECT"
            self.app.config['RESET_PASSWORD_EMAIL_FROM'] = "EMAIL FROM"
            self.app.config['RESET_PASSWORD_EMAIL_NAME'] = "EMAIL NAME"

            res = self.client.post(
                self.expand_path('/reset-password'),
                data={
                    'email_address': 'email@email.com',
                    'csrf_token': FakeCsrf.valid_token,
                }
            )

            assert res.status_code == 302
            send_email.assert_called_once_with(
                "email@email.com",
                mock.ANY,
                "SUBJECT",
                "EMAIL FROM",
                "EMAIL NAME",
            )

    @mock.patch('app.main.views.login.send_email')
    def test_should_be_an_error_if_send_email_fails(
            self, send_email
    ):
        with self.app.app_context():

            send_email.side_effect = EmailError('API is down')

            res = self.client.post(
                self.expand_path('/reset-password'),
                data={
                    'email_address': 'email@email.com',
                    'csrf_token': FakeCsrf.valid_token,
                }
            )

            assert res.status_code == 503
            assert PASSWORD_RESET_EMAIL_ERROR in res.get_data(as_text=True)


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
            "Log in with your buyer account"
        )

    def test_request_password_reset_form_and_inputs_not_autofillable(self):
        self._forms_and_inputs_not_autofillable(
            self.expand_path('/reset-password'),
            "Reset password"
        )

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


class TestBuyersCreation(BaseApplicationTest):
    def test_should_get_create_buyer_form_ok(self):
        res = self.client.get(self.expand_path('/buyers/create'))
        assert res.status_code == 200
        assert 'Create a buyer account' in res.get_data(as_text=True)
        assert 'private' in res.headers['Cache-Control']

    @mock.patch('app.main.views.login.send_email')
    @mock.patch('app.main.views.login.data_api_client')
    def test_should_be_able_to_submit_valid_email_address(self, data_api_client, send_email):
        res = self.client.post(
            self.expand_path('/buyers/create'),
            data={
                'email_address': 'valid@test.gov.au',
                'government_emp_checkbox': 'checked',
                'csrf_token': FakeCsrf.valid_token,
            },
            follow_redirects=True
        )
        assert res.status_code == 200
        assert 'Activate your account' in res.get_data(as_text=True)

    @mock.patch('app.main.views.login.send_email')
    @mock.patch('app.main.views.login.data_api_client')
    def test_require_acknowledgement_of_requirements(self, data_api_client, send_email):
        res = self.client.post(
            self.expand_path('/buyers/create'),
            data={
                'email_address': 'valid@test.gov.au',
                # government_emp_checkbox unchecked
                'csrf_token': FakeCsrf.valid_token,
            },
            follow_redirects=True
        )

        assert res.status_code == 400
        data = res.get_data(as_text=True)
        print data
        assert has_validation_errors(data, 'government_emp_checkbox')

    def test_should_raise_validation_error_for_invalid_email_address(self):
        res = self.client.post(
            self.expand_path('/buyers/create'),
            data={
                'email_address': 'not-an-email-address',
                'government_emp_checkbox': 'checked',
                'csrf_token': FakeCsrf.valid_token,
            },
            follow_redirects=True
        )
        assert res.status_code == 400
        data = res.get_data(as_text=True)

        assert 'Create a buyer account' in data
        assert has_validation_errors(data, 'email_address')

    def test_should_raise_validation_error_for_empty_email_address(self):
        res = self.client.post(
            self.expand_path('/buyers/create'),
            data={'csrf_token': FakeCsrf.valid_token},
            follow_redirects=True
        )
        assert res.status_code == 400
        data = res.get_data(as_text=True)
        assert 'Create a buyer account' in data
        assert has_validation_errors(data, 'email_address')

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_show_error_page_for_unrecognised_email_domain(self, data_api_client):
        data_api_client.is_email_address_with_valid_buyer_domain.return_value = False
        res = self.client.post(
            self.expand_path('/buyers/create'),
            data={
                'email_address': 'valid@test.gov.uk',
                'government_emp_checkbox': 'checked',
                'csrf_token': FakeCsrf.valid_token,
            },
            follow_redirects=True
        )
        assert res.status_code == 400
        data = res.get_data(as_text=True)
        assert "government email address" in data

    @mock.patch('app.main.views.login.data_api_client')
    @mock.patch('app.main.views.login.send_email')
    def test_should_503_if_email_fails_to_send(self, send_email, data_api_client):
        data_api_client.is_email_address_with_valid_buyer_domain.return_value = True
        send_email.side_effect = EmailError("Arrrgh")
        res = self.client.post(
            self.expand_path('/buyers/create'),
            data={
                'email_address': 'valid@test.gov.uk',
                'government_emp_checkbox': 'checked',
                'csrf_token': FakeCsrf.valid_token,
            },
            follow_redirects=True
        )
        assert res.status_code == 503
        assert USER_CREATION_EMAIL_ERROR in res.get_data(as_text=True)

    @mock.patch('app.main.views.login.send_email')
    @mock.patch('app.main.views.login.data_api_client')
    def test_should_create_audit_event_when_email_sent(self, data_api_client, send_email):
        res = self.client.post(
            self.expand_path('/buyers/create'),
            data={
                'email_address': 'valid@test.gov.uk',
                'government_emp_checkbox': 'checked',
                'csrf_token': FakeCsrf.valid_token,
            },
            follow_redirects=True
        )
        assert res.status_code == 200
        data_api_client.create_audit_event.assert_called_with(audit_type=AuditTypes.invite_user,
                                                              data={'invitedEmail': 'valid@test.gov.uk'})


class TestCreateUser(BaseApplicationTest):
    def _generate_token(self, email_address='test@email.com'):
        return generate_token(
            {
                'email_address': email_address
            },
            self.app.config['SHARED_EMAIL_KEY'],
            self.app.config['INVITE_EMAIL_SALT']
        )

    def test_should_be_an_error_for_invalid_token(self):
        token = "1234"
        res = self.client.get(
            self.expand_path('/create-user/{}').format(token)
        )
        assert res.status_code == 400

    def test_should_be_an_error_for_missing_token(self):
        res = self.client.get(self.expand_path('/create-user'))
        assert res.status_code == 404

    def test_should_be_an_error_for_missing_token_trailing_slash(self):
        res = self.client.get(self.expand_path('/create-user/'))
        assert res.status_code == 301
        assert res.location == 'http://localhost' + self.expand_path('/create-user')

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_be_an_error_for_invalid_token_contents(self, data_api_client):
        token = generate_token(
            {
                'this_is_not_expected': 1234
            },
            self.app.config['SHARED_EMAIL_KEY'],
            self.app.config['INVITE_EMAIL_SALT']
        )

        res = self.client.get(
            self.expand_path('/create-user/{}').format(token)
        )
        assert res.status_code == 400
        assert data_api_client.get_user.called is False

    def test_should_be_a_bad_request_if_token_expired(self):
        res = self.client.get(
            self.expand_path('create-user/12345')
        )

        assert res.status_code >= 400

    def test_should_be_an_error_if_invalid_token_on_submit(self):
        res = self.client.post(
            self.expand_path('/create-user/invalidtoken'),
            data={
                'password': '123456789',
                'name': 'name',
                'email_address': 'valid@test.com'}
        )

        assert res.status_code == 400
        assert USER_LINK_EXPIRED_ERROR in res.get_data(as_text=True)
        assert (
            '<input type="submit" class="button-save"  value="Create contributor account" />'
            not in res.get_data(as_text=True)
        )

    def test_should_be_an_error_if_missing_name_and_password(self):
        token = self._generate_token()
        res = self.client.post(
            self.expand_path('/create-user/{}').format(token),
            data={}
        )

        assert res.status_code == 400
        assert has_validation_errors(res.get_data(as_text=True), 'name')
        assert has_validation_errors(res.get_data(as_text=True), 'password')

    def test_should_be_an_error_if_too_short_name_and_password(self):
        token = self._generate_token()
        res = self.client.post(
            self.expand_path('/create-user/{}').format(token),
            data={
                'password': "123456789",
                'name': ""
            }
        )

        assert res.status_code == 400
        assert has_validation_errors(res.get_data(as_text=True), 'name')
        assert has_validation_errors(res.get_data(as_text=True), 'password')

    def test_should_be_an_error_if_too_long_name_and_password(self):
        with self.app.app_context():

            token = self._generate_token()
            twofiftysix = "a" * 256
            fiftyone = "a" * 51

            res = self.client.post(
                self.expand_path('/create-user/{}').format(token),
                data={
                    'password': fiftyone,
                    'name': twofiftysix
                }
            )

            assert res.status_code == 400
            for message in ["Create account", "test@email.com"]:
                assert message in res.get_data(as_text=True)

            assert has_validation_errors(res.get_data(as_text=True), 'name')
            assert has_validation_errors(res.get_data(as_text=True), 'password')

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_return_an_error_if_user_exists_and_is_a_buyer(self, data_api_client):
        data_api_client.get_user.return_value = self.user(123, 'test@email.com', None, None, 'Users name')

        token = self._generate_token()
        res = self.client.get(
            self.expand_path('/create-user/{}').format(token)
        )

        assert res.status_code == 400
        assert "Account already exists" in res.get_data(as_text=True)

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_return_an_error_with_admin_message_if_user_is_an_admin(self, data_api_client):
        data_api_client.get_user.return_value = self.user(123, 'test@email.com', None, None, 'Users name', role='admin')

        token = self._generate_token()
        res = self.client.get(
            self.expand_path('/create-user/{}').format(token)
        )

        assert res.status_code == 400
        assert "Account already exists" in res.get_data(as_text=True)

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_return_an_error_with_locked_message_if_user_is_locked(self, data_api_client):
        data_api_client.get_user.return_value = self.user(
            123,
            'test@email.com',
            None,
            None,
            'Users name',
            locked=True
        )

        token = self._generate_token()
        res = self.client.get(
            self.expand_path('/create-user/{}').format(token)
        )

        assert res.status_code == 400
        assert "account is locked" in res.get_data(as_text=True)

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_return_an_error_with_inactive_message_if_user_is_not_active(self, data_api_client):
        data_api_client.get_user.return_value = self.user(
            123,
            'test@email.com',
            None,
            None,
            'Users name',
            active=False
        )

        token = self._generate_token()
        res = self.client.get(
            self.expand_path('/create-user/{}').format(token)
        )

        assert res.status_code == 400
        assert "Your account has been deactivated" in res.get_data(as_text=True)

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_return_an_error_if_user_is_already_registered(self, data_api_client):
        data_api_client.get_user.return_value = self.user(
            123,
            'test@email.com',
            None,
            None,
            'Users name'
        )

        token = self._generate_token()
        res = self.client.get(
            self.expand_path('/create-user/{}').format(token),
            follow_redirects=True
        )

        assert res.status_code == 400
        assert "Account already exists" in res.get_data(as_text=True)

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_return_an_error_if_already_registered_as_a_supplier(self, data_api_client):
        self.login_as_supplier()
        data_api_client.get_user.return_value = self.user(
            999,
            'test@email.com',
            1234,
            'Supplier',
            'Different users name'
        )

        token = self._generate_token()
        res = self.client.get(
            self.expand_path('/create-user/{}').format(token)
        )

        assert res.status_code == 400
        assert "Your email address is already registered as an account with ‘Supplier’." in res.get_data(as_text=True)

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_return_an_error_if_user_is_already_logged_in(self, data_api_client):
        self.login_as_supplier()
        data_api_client.get_user.return_value = self.user(
            123,
            'email@email.com',
            None,
            None,
            'Users name'
        )

        token = self._generate_token()
        res = self.client.get(
            self.expand_path('/create-user/{}').format(token)
        )

        assert res.status_code == 400
        assert "Account already exists" in res.get_data(as_text=True)
        assert 'private' in res.headers['Cache-Control']

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_create_user_if_user_does_not_exist(self, data_api_client):
        data_api_client.get_user.return_value = None

        token = self._generate_token()
        res = self.client.post(
            self.expand_path('/create-user/{}').format(token),
            data={
                'password': 'validpassword',
                'name': 'valid name',
                'phone_number': '020-7930-4832',
                'csrf_token': FakeCsrf.valid_token,
            }
        )

        assert res.status_code == 302
        assert res.location == 'http://localhost' + self.expand_path('/')

        data_api_client.create_user.assert_called_once_with({
            'role': 'buyer',
            'password': 'validpassword',
            'emailAddress': 'test@email.com',
            'phoneNumber': '020-7930-4832',
            'name': 'valid name'
        })

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_return_an_error_if_user_exists(self, data_api_client):
        data_api_client.create_user.side_effect = HTTPError(mock.Mock(status_code=409))

        token = self._generate_token()
        res = self.client.post(
            self.expand_path('/create-user/{}').format(token),
            data={
                'password': 'validpassword',
                'phone_number': '020-7930-4832',
                'name': 'valid name',
                'csrf_token': FakeCsrf.valid_token,
            }
        )

        assert res.status_code == 400

        data_api_client.create_user.assert_called_once_with({
            'role': 'buyer',
            'password': 'validpassword',
            'emailAddress': 'test@email.com',
            'phoneNumber': '020-7930-4832',
            'name': 'valid name'
        })

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_create_user_if_no_phone_number(self, data_api_client):

        token = self._generate_token()
        res = self.client.post(
            self.expand_path('/create-user/{}').format(token),
            data={
                'password': 'validpassword',
                'name': 'valid name',
                'phone_number': None,
                'csrf_token': FakeCsrf.valid_token,
            }
        )

        assert res.status_code == 302
        assert res.location == 'http://localhost' + self.expand_path('/')

        data_api_client.create_user.assert_called_once_with({
            'role': 'buyer',
            'password': 'validpassword',
            'emailAddress': 'test@email.com',
            'phoneNumber': '',
            'name': 'valid name'
        })

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_return_an_error_if_bad_phone_number(self, data_api_client):

        token = self._generate_token()
        res = self.client.post(
            self.expand_path('/create-user/{}').format(token),
            data={
                'password': 'validpassword',
                'name': 'valid name',
                'phone_number': 'Not a number'
            }
        )

        assert res.status_code == 400

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_strip_whitespace_surrounding_create_user_name_field(self, data_api_client):
        data_api_client.get_user.return_value = None
        token = self._generate_token()
        res = self.client.post(
            self.expand_path('/create-user/{}').format(token),
            data={
                'password': 'validpassword',
                'name': '  valid name  ',
                'phone_number': '020-7930-4832',
                'csrf_token': FakeCsrf.valid_token,
            }
        )
        assert res.status_code == 302
        data_api_client.create_user.assert_called_once_with({
            'role': mock.ANY,
            'password': 'validpassword',
            'emailAddress': mock.ANY,
            'phoneNumber': '020-7930-4832',
            'name': 'valid name'
        })

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_not_strip_whitespace_surrounding_create_user_password_field(self, data_api_client):
        data_api_client.get_user.return_value = None
        token = self._generate_token()
        res = self.client.post(
            self.expand_path('/create-user/{}').format(token),
            data={
                'password': '  validpassword  ',
                'name': 'valid name  ',
                'phone_number': '020-7930-4832',
                'csrf_token': FakeCsrf.valid_token,
            }
        )
        assert res.status_code == 302
        data_api_client.create_user.assert_called_once_with({
            'role': mock.ANY,
            'password': '  validpassword  ',
            'emailAddress': mock.ANY,
            'name': 'valid name',
            'phoneNumber': '020-7930-4832',
        })

    @mock.patch('app.main.views.login.data_api_client')
    def test_should_be_a_503_if_api_fails(self, data_api_client):
        with self.app.app_context():

            data_api_client.create_user.side_effect = HTTPError("bad email")

            token = self._generate_token()
            res = self.client.post(
                self.expand_path('/create-user/{}').format(token),
                data={
                    'password': 'validpassword',
                    'name': 'valid name',
                    'csrf_token': FakeCsrf.valid_token,
                }
            )
            assert res.status_code == 503


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

    @mock.patch('app.buyers.views.buyers.data_api_client')
    def test_buyer_pages_ok_if_logged_in_as_buyer(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            res = self.client.get(self.expand_path('/buyers'))
            page_text = res.get_data(as_text=True)
            assert res.status_code == 200
            assert 'private' in res.headers['Cache-Control']
            assert 'buyer@email.com' in page_text
            assert 'Some Buyer' in page_text
