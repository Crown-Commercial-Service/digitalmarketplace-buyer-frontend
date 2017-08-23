from __future__ import absolute_import

import os
import json
import re
import mock

from app import create_app, data_api_client
from tests import login_for_tests
from datetime import datetime, timedelta
from mock import patch
from werkzeug.http import parse_cookie

from dmutils.formats import DATETIME_FORMAT


class BaseApplicationTest(object):
    def setup_method(self, method):
        # We need to mock the API client in create_app, however we can't use patch the constructor,
        # as the DataAPIClient instance has already been created; nor can we temporarily replace app.data_api_client
        # with a mock, because then the shared instance won't have been configured (done in create_app). Instead,
        # just mock the one function that would make an API call in this case.
        data_api_client.find_frameworks = mock.Mock()
        data_api_client.find_frameworks.return_value = self._get_frameworks_list_fixture_data()
        self.app = create_app('test')
        self.app.register_blueprint(login_for_tests)
        self.client = self.app.test_client()
        self.get_user_patch = None

    def teardown_method(self, method):
        self.teardown_login()

    @staticmethod
    def user(id, email_address, supplier_id, supplier_name, name,
             is_token_valid=True, locked=False, active=True, role='buyer'):

        hours_offset = -1 if is_token_valid else 1
        date = datetime.utcnow() + timedelta(hours=hours_offset)
        password_changed_at = date.strftime(DATETIME_FORMAT)

        user = {
            "id": id,
            "emailAddress": email_address,
            "name": name,
            "role": role,
            "locked": locked,
            'active': active,
            'passwordChangedAt': password_changed_at
        }

        if supplier_id:
            supplier = {
                "supplierId": supplier_id,
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
    def _get_g9_search_results_fixture_data():
        return BaseApplicationTest._get_fixture_data(
            'g9_search_results_fixture.json'
        )

    @staticmethod
    def _get_search_results_multiple_page_fixture_data():
        return BaseApplicationTest._get_fixture_data(
            'search_results_multiple_pages_fixture.json'
        )

    @staticmethod
    def _get_frameworks_list_fixture_data():
        return BaseApplicationTest._get_fixture_data('frameworks.json')

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
    def _get_framework_fixture_data(framework_slug):
        return {
            'frameworks': next(f for f in BaseApplicationTest._get_frameworks_list_fixture_data()['frameworks']
                               if f['slug'] == framework_slug)
        }

    @staticmethod
    def _get_dos_brief_fixture_data(multi=False):
        if multi:
            return BaseApplicationTest._get_fixture_data('dos_multiple_briefs_fixture.json')
        else:
            return BaseApplicationTest._get_fixture_data('dos_brief_fixture.json')

    @staticmethod
    def _get_dos_brief_responses_fixture_data():
        return BaseApplicationTest._get_fixture_data('dos_brief_responses_fixture.json')

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
    def _get_direct_award_project_fixture():
        return BaseApplicationTest._get_fixture_data('direct_award_project_fixture.json')

    @staticmethod
    def _get_direct_award_project_searches_fixture():
        return BaseApplicationTest._get_fixture_data('direct_award_project_searches_fixture.json')

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

    def login_as_supplier(self):
        with patch('app.data_api_client') as login_api_client:
            login_api_client.authenticate_user.return_value = self.user(
                123, "email@email.com", 1234, u'Supplier NĀme', u'Năme')

            self.get_user_patch = patch.object(
                data_api_client,
                'get_user',
                return_value=self.user(123, "email@email.com", 1234, u'Supplier NĀme', u'Năme')
            )
            self.get_user_patch.start()

            response = self.client.post("/auto-supplier-login")
            assert response.status_code == 200

    def login_as_buyer(self, user_id=123):
        with patch('app.data_api_client') as login_api_client:
            login_api_client.authenticate_user.return_value = self.user(
                user_id, "buyer@email.com", None, None, 'Ā Buyer', role='buyer')

            self.get_user_patch = patch.object(
                data_api_client,
                'get_user',
                return_value=self.user(user_id, "buyer@email.com", None, None, 'Buyer', role='buyer')
            )
            self.get_user_patch.start()

            response = self.client.post("/auto-buyer-login")
            assert response.status_code == 200

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

            self.client.post("/login", data={
                'email_address': 'valid@email.com',
                'password': '1234567890'
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

    @staticmethod
    def find_search_summary(res_data):
        return re.findall(r'<span class="search-summary-count">.+</span>[^\n]+', res_data)

    # Method to test flashes taken from http://blog.paulopoiati.com/2013/02/22/testing-flash-messages-in-flask/
    def assert_flashes(self, expected_message, expected_category='message'):
        with self.client.session_transaction() as session:
            try:
                category, message = session['_flashes'][0]
            except KeyError:
                raise AssertionError('nothing flashed')
            assert expected_message in message
            assert expected_category == category
