from datetime import datetime, timedelta
from functools import partial
import os
import re

import json
import mock
from werkzeug.http import parse_cookie
from markupsafe import escape

from dmcontent import ContentLoader
from dmtestutils.api_model_stubs import FrameworkStub
from dmtestutils.api_model_stubs.lot import dos_lots, as_a_service_lots, cloud_lots
from dmutils.formats import DATETIME_FORMAT

from app import create_app, data_api_client, _make_content_loader_factory
from tests import login_for_tests


def get_frameworks_list_fixture_data():
    g_cloud_8_variation = {
        "1": {
            "countersignedAt": "2016-10-05T11:00:00.000000Z",
            "countersignerName": "Dan Saxby",
            "countersignerRole": "Category Director",
            "createdAt": "2016-08-19T15:31:00.000000Z"
        }
    }

    frameworks = [
        FrameworkStub(
            id=4, slug='g-cloud-7', status='live', lots=as_a_service_lots()
        ).single_result_response(),
        FrameworkStub(
            id=1, slug='g-cloud-6', status='expired', lots=as_a_service_lots()
        ).single_result_response(),
        FrameworkStub(
            id=6, slug='g-cloud-8', status='live', lots=as_a_service_lots(),
            framework_agreement_version='v1.0', framework_variations=g_cloud_8_variation
        ).single_result_response(),
        FrameworkStub(
            id=3, slug='g-cloud-5', status='expired', lots=as_a_service_lots()
        ).single_result_response(),
        FrameworkStub(
            id=2, slug='g-cloud-4', status='expired', lots=as_a_service_lots()
        ).single_result_response(),
        FrameworkStub(
            id=7, slug='digital-outcomes-and-specialists-2', status='live',
            lots=dos_lots(), framework_agreement_version='v1.0', has_further_competition=True
        ).single_result_response(),
        FrameworkStub(
            id=12, slug='digital-outcomes-and-specialists-4', status='live',
            lots=dos_lots(), has_further_competition=True
        ).single_result_response(),
        FrameworkStub(
            id=5, slug='digital-outcomes-and-specialists', status='live',
            lots=dos_lots(), framework_agreement_version='v1.0', has_further_competition=True
        ).single_result_response(),
        FrameworkStub(
            id=8, slug='g-cloud-9', status='live', lots=cloud_lots()
        ).single_result_response(),
    ]

    return {'frameworks': [framework['frameworks'] for framework in frameworks]}


def get_expired_frameworks_list_fixture_data():
    frameworks = [
        FrameworkStub(
            id=4, slug='g-cloud-7', status='expired', lots=as_a_service_lots()
        ).single_result_response(),
        FrameworkStub(
            id=1, slug='g-cloud-6', status='expired', lots=as_a_service_lots()
        ).single_result_response(),
        FrameworkStub(
            id=6, slug='g-cloud-8', status='expired', lots=as_a_service_lots(),
        ).single_result_response(),
        FrameworkStub(
            id=3, slug='g-cloud-5', status='expired', lots=as_a_service_lots()
        ).single_result_response(),
        FrameworkStub(
            id=2, slug='g-cloud-4', status='expired', lots=as_a_service_lots()
        ).single_result_response(),
        FrameworkStub(
            id=8, slug='g-cloud-9', status='expired', lots=cloud_lots()
        ).single_result_response(),
    ]

    return {'frameworks': [framework['frameworks'] for framework in frameworks]}


class BaseAPIClientMixin:
    """
    Mixin for patching the API clients when imported for each view module.

    Import this base class to the test module, and initialise with the path to the import:

    :: test_marketplace.py
    class APIClientMixin(BaseAPIClientMixin):
        data_api_client_patch_path = 'app.main.views.marketplace.data_api_client'
        search_api_client_patch_path = 'app.main.views.marketplace.search_api_client'

    # Put the mixin before the BaseApplicationTest class:

    class TestMyView(APIClientMixin, BaseApplicationTest):
        def test_something(self):
            self.search_api_client.search.return_value = {}
            assert self.data_api_client.find_frameworks.call_args_list == []

    Multiple subclasses of the mixin can be created and passed into the test class if the API client
    is patched in different places (hopefully this should be rare!).
    """
    data_api_client_patch_path = None
    data_api_client_patch = None
    search_api_client_patch_path = None
    search_api_client_patch = None

    @classmethod
    def setup_class(cls):
        if cls.data_api_client_patch_path:
            cls.data_api_client_patch = mock.patch(cls.data_api_client_patch_path, autospec=True)
        if cls.search_api_client_patch_path:
            cls.search_api_client_patch = mock.patch(cls.search_api_client_patch_path, autospec=True)

    def setup_method(self, method):
        super().setup_method(method)
        if self.data_api_client_patch:
            self.data_api_client = self.data_api_client_patch.start()
            # Default return values - can be overwritten at test level
            self.data_api_client.find_frameworks.return_value = get_frameworks_list_fixture_data()
        if self.search_api_client_patch:
            self.search_api_client = self.search_api_client_patch.start()

    def teardown_method(self, method):
        if self.data_api_client_patch:
            self.data_api_client_patch.stop()
        if self.search_api_client_patch:
            self.search_api_client_patch.stop()
        super().teardown_method(method)


class BaseApplicationTest(object):
    injected_content_loader = ContentLoader('app/content')

    def setup_method(self, method):
        """
        A data_api_client instance is required for `create_app`, so we need some careful patching to initialise
        the Flask test client:
         - patch the .find_frameworks() method of `app.data_api_client` with the fixture
         - initialise the app with `create_app('test')`
         - in the tests, use a subclass of `BaseAPIClientMixin` above, with the path to the imported data_api_client
         - the .find_frameworks() return value will need to be provided separately in those tests, as the import
           path will (hopefully!) be different there.
        """
        self.app_env_var_mock = mock.patch.dict('gds_metrics.os.environ', {'PROMETHEUS_METRICS_PATH': '/_metrics'})
        self.app_env_var_mock.start()

        self.session_mock = mock.patch('dmutils.session.init_app')
        self.session_mock.start()

        data_api_client.find_frameworks = mock.Mock()
        data_api_client.find_frameworks.return_value = self._get_frameworks_list_fixture_data()

        # if we don't make this tweak, the content loader will get re-built for every test, which is incredibly slow.
        # instead we replace the `_make_content_loader_factory` with a variant which injects `injected_content_loader`
        # as the `initial_instance` argument, which we keep as a class attribute. `_make_content_loader_factory` still
        # executes inside `create_app`, but all the content it asks to be loaded should already be present in the
        # content_loader it is operating on, so it effectively does nothing.
        # a test that needed a "clean" content loader for some reason would be able to override a test instance's
        # injected_content_loader early in the setup_method process (e.g. with None)
        self.make_content_loader_factory_mock = mock.patch("app._make_content_loader_factory")
        self.make_content_loader_factory_mock.start().side_effect = partial(
            _make_content_loader_factory,
            initial_instance=self.injected_content_loader,
        )

        self.app = create_app('test')
        self.app.register_blueprint(login_for_tests)
        self.client = self.app.test_client()
        self.get_user_patch = None

    def teardown_method(self, method):
        self.teardown_login()
        self.make_content_loader_factory_mock.stop()
        self.app_env_var_mock.stop()
        self.session_mock.stop()

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
        return get_frameworks_list_fixture_data()

    @staticmethod
    def _get_expired_frameworks_list_fixture_data():
        return get_expired_frameworks_list_fixture_data()

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
    def _get_expired_framework_fixture_data(framework_slug):
        return {
            'frameworks': next(f for f in BaseApplicationTest._get_expired_frameworks_list_fixture_data()['frameworks']
                               if f['slug'] == framework_slug)
        }

    @staticmethod
    def _get_dos_brief_fixture_data(multi=False):
        if multi:
            return BaseApplicationTest._get_fixture_data('dos_multiple_briefs_fixture.json')
        else:
            return BaseApplicationTest._get_fixture_data('dos_brief_fixture.json')

    @staticmethod
    def _get_dos_brief_search_api_response_fixture_data():
        return BaseApplicationTest._get_fixture_data('dos_brief_search_api_response.json')

    @staticmethod
    def _get_dos_brief_search_api_aggregations_response_outcomes_fixture_data():
        return BaseApplicationTest._get_fixture_data('dos_brief_search_api_aggregations_response_outcomes.json')

    @staticmethod
    def _get_dos_brief_search_api_aggregations_response_specialists_fixture_data():
        return BaseApplicationTest._get_fixture_data('dos_brief_search_api_aggregations_response_specialists.json')

    @staticmethod
    def _get_dos_brief_search_api_aggregations_response_user_research_fixture_data():
        return BaseApplicationTest._get_fixture_data('dos_brief_search_api_aggregations_response_user_research.json')

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
    def _get_direct_award_project_list_fixture(**kwargs):
        return BaseApplicationTest._get_fixture_data('direct_award_project_list_fixture.json')

    @staticmethod
    def _get_direct_award_project_list_xss_fixture(**kwargs):
        return BaseApplicationTest._get_fixture_data('direct_award_project_list_xss_fixture.json')

    @staticmethod
    def _get_direct_award_project_fixture(**kwargs):
        project = BaseApplicationTest._get_fixture_data('direct_award_project_fixture.json')

        for key, value in kwargs.items():
            if key in project['project']:
                project['project'][key] = value
            else:
                raise ValueError('Key "{}" does not exist in the Direct Award project fixture.'.format(key))

        return project

    @staticmethod
    def _get_direct_award_lock_project_fixture():
        return BaseApplicationTest._get_direct_award_project_fixture(lockedAt="2017-09-08T00:00:00.000000Z")

    @staticmethod
    def _get_direct_award_not_lock_project_fixture():
        return BaseApplicationTest._get_direct_award_project_fixture(lockedAt=False)

    @staticmethod
    def _get_direct_award_project_outcome_awarded_fixture():
        return BaseApplicationTest._get_fixture_data('direct_award_project_outcome_awarded_fixture.json')

    @staticmethod
    def _get_direct_award_project_completed_outcome_awarded_fixture():
        outcome = BaseApplicationTest._get_direct_award_project_outcome_awarded_fixture()
        outcome['outcome']['completed'] = True
        return outcome

    @staticmethod
    def _get_direct_award_project_with_outcome_awarded_fixture():
        project = BaseApplicationTest._get_direct_award_lock_project_fixture()
        project['project']['outcome'] = \
            BaseApplicationTest._get_direct_award_project_outcome_awarded_fixture()['outcome']
        return project

    @staticmethod
    def _get_direct_award_project_with_completed_outcome_awarded_fixture():
        project = BaseApplicationTest._get_direct_award_lock_project_fixture()
        project['project']['outcome'] = \
            BaseApplicationTest._get_direct_award_project_completed_outcome_awarded_fixture()['outcome']
        return project

    @staticmethod
    def _get_direct_award_project_searches_fixture(only_active=False):
        searches = BaseApplicationTest._get_fixture_data('direct_award_project_searches_fixture.json')

        if only_active:
            searches = {'searches': [search for search in searches['searches'] if search['active']]}

        return searches

    @staticmethod
    def _get_direct_award_project_services_fixture():
        return BaseApplicationTest._get_fixture_data('direct_award_project_services_fixture.json')

    @staticmethod
    def _get_direct_award_project_services_zero_state_fixture():
        return BaseApplicationTest._get_fixture_data('direct_award_project_services_zero_state_fixture.json')

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
            cls._squashed_element_text(child_element) + child_element.tail for child_element in element
        )

    def teardown_login(self):
        if self.get_user_patch is not None:
            self.get_user_patch.stop()

    def login_as_supplier(self):
        with mock.patch('app.data_api_client') as login_api_client:
            login_api_client.authenticate_user.return_value = self.user(
                123, "email@email.com", 1234, u'Supplier NĀme', u'Năme')

            self.get_user_patch = mock.patch.object(
                data_api_client,
                'get_user',
                return_value=self.user(123, "email@email.com", 1234, u'Supplier NĀme', u'Năme')
            )
            self.get_user_patch.start()

            response = self.client.post("/auto-supplier-login")
            assert response.status_code == 200

    def login_as_buyer(self, user_id=123):
        with mock.patch('app.data_api_client') as login_api_client:
            login_api_client.authenticate_user.return_value = self.user(
                user_id, "buyer@email.com", None, None, 'Ā Buyer', role='buyer')

            self.get_user_patch = mock.patch.object(
                data_api_client,
                'get_user',
                return_value=self.user(user_id, "buyer@email.com", None, None, 'Buyer', role='buyer')
            )
            self.get_user_patch.start()

            response = self.client.post("/auto-buyer-login")
            assert response.status_code == 200

    def login_as_admin(self):
        with mock.patch('app.main.views.login.data_api_client') as login_api_client:
            login_api_client.authenticate_user.return_value = self.user(
                123, "admin@email.com", None, None, 'Name', role='admin')

            self.get_user_patch = mock.patch.object(
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
        return re.findall(r'<span class="app-search-summary__count">.+</span>[^\n]+', res_data)

    # Method to test flashes taken from http://blog.paulopoiati.com/2013/02/22/testing-flash-messages-in-flask/
    def assert_flashes(self, expected_message_markup, expected_category='message'):
        with self.client.session_transaction() as session:
            try:
                category, message = session['_flashes'][0]
            except KeyError:
                raise AssertionError('nothing flashed')
            # The code under test put `message` into the template, and jinja will call `escape` on it.
            # We need to ensure we didn't wrap something unsafe in a `Markup` object, so should be checking the
            # output markup, not the message that went in.
            assert expected_message_markup in escape(message)
            assert expected_category == category


class CustomAbortException(Exception):
    """Custom error for testing abort"""
    pass
