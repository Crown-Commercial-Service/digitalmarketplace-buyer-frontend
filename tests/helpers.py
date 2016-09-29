from __future__ import absolute_import

import os
import json
import re

from app import create_app, data_api_client
from app.helpers.terms_helpers import TermsManager
from flask_featureflags import FeatureFlag

from dmutils.forms import FakeCsrf
from datetime import datetime, timedelta
from flask import url_for
from mock import patch
from werkzeug.http import parse_cookie

from dmutils.formats import DATETIME_FORMAT


class BaseApplicationTest(object):
    def setup(self):
        self.app = create_app('test')
        self.client = self.app.test_client()
        self.terms_manager = TermsManager()
        self.terms_manager.init_app(self.app, ['2016-09-02 11:00.html'])
        feature_flags = FeatureFlag(self.app)
        self.get_user_patch = None

    def expand_path(self, path):
        return self.app.config['URL_PREFIX'] + path

    def url_for(self, handler_name, _external=False, **kwargs):
        with self.app.app_context():
            return url_for(handler_name, _external=_external, **kwargs)

    def teardown(self):
        self.teardown_login()

    @staticmethod
    def user(id, email_address, supplier_code, supplier_name, name, is_token_valid=True, locked=False, active=True,
             role='buyer', terms_accepted_date=None):

        now = datetime.utcnow()

        hours_offset = -1 if is_token_valid else 1
        password_changed_date = now + timedelta(hours=hours_offset)

        if terms_accepted_date is None:
            terms_accepted_date = now

        user = {
            "id": id,
            "emailAddress": email_address,
            "name": name,
            "role": role,
            "locked": locked,
            'active': active,
            'passwordChangedAt': password_changed_date.strftime(DATETIME_FORMAT),
            'termsAcceptedAt': terms_accepted_date.strftime(DATETIME_FORMAT),
        }

        if supplier_code:
            supplier = {
                "supplierCode": supplier_code,
                "name": supplier_name,
            }
            user['role'] = 'supplier'
            user['supplier'] = supplier
        return {
            "users": user
        }

    @staticmethod
    def _get_fixture_data(fixture_filename):
        test_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), ".")
        )
        fixture_path = os.path.join(
            test_root, 'fixtures', fixture_filename
        )
        with open(fixture_path) as fixture_file:
            return json.load(fixture_file)

    @staticmethod
    def _get_search_results_fixture_data():
        return BaseApplicationTest._get_fixture_data(
            'search_results_fixture.json'
        )

    @staticmethod
    def _get_search_results_multiple_page_fixture_data():
        return BaseApplicationTest._get_fixture_data(
            'search_results_multiple_pages_fixture.json'
        )

    @staticmethod
    def _get_g4_service_fixture_data():
        return BaseApplicationTest._get_fixture_data('g4_service_fixture.json')

    @staticmethod
    def _get_g5_service_fixture_data():
        return BaseApplicationTest._get_fixture_data('g5_service_fixture.json')

    @staticmethod
    def _get_g6_service_fixture_data():
        return BaseApplicationTest._get_fixture_data('g6_service_fixture.json')

    @staticmethod
    def _get_dos_brief_fixture_data(multi=False):
        if multi:
            return BaseApplicationTest._get_fixture_data('dos_multiple_briefs_fixture.json')
        else:
            return BaseApplicationTest._get_fixture_data('dos_brief_fixture.json')

    @staticmethod
    def _get_supplier_fixture_data():
        return BaseApplicationTest._get_fixture_data('supplier_fixture.json')

    @staticmethod
    def _get_supplier_with_minimum_fixture_data():
        return BaseApplicationTest._get_fixture_data('supplier_fixture_with_minium_data.json')

    @staticmethod
    def _get_suppliers_by_prefix_fixture_data():
        return BaseApplicationTest._get_fixture_data(
            'suppliers_by_prefix_fixture.json')

    @staticmethod
    def _get_suppliers_by_prefix_fixture_data_page_2():
        return BaseApplicationTest._get_fixture_data(
            'suppliers_by_prefix_fixture_page_2.json')

    @staticmethod
    def _get_suppliers_by_prefix_fixture_with_next_and_prev():
        return BaseApplicationTest._get_fixture_data(
            'suppliers_by_prefix_fixture_page_with_next_and_prev.json')

    @staticmethod
    def _strip_whitespace(whitespace_in_this):
        return re.sub(r"\s+", "",
                      whitespace_in_this, flags=re.UNICODE)

    @staticmethod
    def _normalize_whitespace(whitespace_in_this):
        # NOTE proper xml-standard way of doing this is a little more complex afaik
        return re.sub(r"\s+", " ",
                      whitespace_in_this, flags=re.UNICODE).strip()

    @classmethod
    def _squashed_element_text(cls, element):
        return element.text + "".join(
            cls._squashed_element_text(child_element)+child_element.tail for child_element in element
        )

    def teardown_login(self):
        if self.get_user_patch is not None:
            self.get_user_patch.stop()

    def login_as_supplier(self, supplier_code=1234):
        with patch('app.main.views.login.data_api_client') as login_api_client:
            login_api_client.authenticate_user.return_value = self.user(
                123, "email@email.com", supplier_code, 'Supplier Name', 'Name', role='supplier')

            self.get_user_patch = patch.object(
                data_api_client,
                'get_user',
                return_value=self.user(123, "email@email.com", supplier_code, 'Supplier Name', 'Name', role='supplier')
            )
            self.get_user_patch.start()

            self.client.post(self.expand_path('/login'), data={
                'email_address': 'valid@email.com',
                'password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            })

            login_api_client.authenticate_user.assert_called_once_with(
                "valid@email.com", "1234567890")

    def login_as_buyer(self, user_id=123, terms_accepted_date=None):
        with patch('app.main.views.login.data_api_client') as login_api_client:
            user = self.user(
                user_id,
                'buyer@email.com',
                None,
                None,
                'Some Buyer',
                terms_accepted_date=terms_accepted_date,
            )
            login_api_client.authenticate_user.return_value = user

            self.get_user_patch = patch.object(data_api_client, 'get_user', return_value=user)
            self.get_user_patch.start()

            response = self.client.post(self.expand_path('/login'), data={
                'email_address': 'buyer@email.com',
                'password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            })

            login_api_client.authenticate_user.assert_called_once_with('buyer@email.com', '1234567890')

    def login_as_admin(self):
        with patch('app.main.views.login.data_api_client') as login_api_client:
            login_api_client.authenticate_user.return_value = self.user(
                123, "admin@email.com", None, None, 'Name', role='admin')

            self.get_user_patch = patch.object(
                data_api_client,
                'get_user',
                return_value=self.user(123, "admin@email.com", None, None, 'Some Admin', role='admin')
            )
            self.get_user_patch.start()

            self.client.post(self.expand_path('/login'), data={
                'email_address': 'valid@email.com',
                'password': '1234567890',
                'csrf_token': FakeCsrf.valid_token,
            })

            login_api_client.authenticate_user.assert_called_once_with(
                "valid@email.com", "1234567890")

    @staticmethod
    def get_cookie_by_name(response, name):
        cookies = response.headers.getlist('Set-Cookie')
        for cookie in cookies:
            if name in parse_cookie(cookie):
                return parse_cookie(cookie)
        return None

    @staticmethod
    def strip_all_whitespace(content):
        pattern = re.compile(r'\s+')
        return re.sub(pattern, '', content)

    # Method to test flashes taken from http://blog.paulopoiati.com/2013/02/22/testing-flash-messages-in-flask/
    def assert_flashes(self, expected_message, expected_category='message'):
        with self.client.session_transaction() as session:
            try:
                category, message = session['_flashes'][0]
            except KeyError:
                raise AssertionError('nothing flashed')
            assert expected_message in message
            assert expected_category == category
