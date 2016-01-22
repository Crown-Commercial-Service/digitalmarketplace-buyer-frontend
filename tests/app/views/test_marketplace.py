# coding=utf-8

import mock
from nose.tools import assert_equal, assert_true, assert_in, assert_not_in
from ...helpers import BaseApplicationTest
from dmapiclient import APIError


class TestApplication(BaseApplicationTest):
    def setup(self):
        super(TestApplication, self).setup()

    def test_analytics_code_should_be_in_javascript(self):
        res = self.client.get('/static/javascripts/application.js')
        assert_equal(200, res.status_code)
        assert_true(
            'trackPageview'
            in res.get_data(as_text=True))

    def test_should_use_local_cookie_page_on_cookie_message(self):
        res = self.client.get('/')
        assert_equal(200, res.status_code)
        assert_true(
            '<p>GOV.UK uses cookies to make the site simpler. <a href="/cookies">Find out more about cookies</a></p>'
            in res.get_data(as_text=True)
        )


class TestHomepageSidebarMessage(BaseApplicationTest):
    def setup(self):
        super(TestHomepageSidebarMessage, self).setup()

    @staticmethod
    def _find_frameworks(framework_slugs_and_statuses):

        _frameworks = []

        for index, framework_slug_and_status in enumerate(framework_slugs_and_statuses):
            framework_slug, framework_status = framework_slug_and_status
            _frameworks.append({
                'framework': 'framework',
                'slug': framework_slug,
                'id': index + 1,
                'status': framework_status,
                'name': 'Framework'
            })

        return {
            'frameworks': _frameworks
        }

    @staticmethod
    def _assert_message_container_is_empty(response_data):
        empty_message_container = '<div class="framework-message column-one-third"></div>'
        assert_in(
            BaseApplicationTest._strip_whitespace(empty_message_container),
            BaseApplicationTest._strip_whitespace(response_data),
        )

    @staticmethod
    def _assert_message_container_is_not_empty(response_data):
        empty_message_container = '<div class="framework-message column-one-third"></div>'
        assert_not_in(
            BaseApplicationTest._strip_whitespace(empty_message_container),
            BaseApplicationTest._strip_whitespace(response_data),
        )

    @mock.patch('app.main.views.marketplace.data_api_client')
    def _load_homepage(self, framework_slugs_and_statuses, framework_messages, data_api_client):

        data_api_client.find_frameworks.return_value = self._find_frameworks(framework_slugs_and_statuses)
        res = self.client.get('/')
        assert_equal(200, res.status_code)
        response_data = res.get_data(as_text=True)

        if framework_messages:
            self._assert_message_container_is_not_empty(response_data)
            for message in framework_messages:
                assert_in(message, response_data)
        else:
            self._assert_message_container_is_empty(response_data)

    def test_homepage_sidebar_message_exists_dos_coming(self):

        framework_slugs_and_statuses = [
            ('g-cloud-7', 'pending'),
            ('digital-outcomes-and-specialists', 'coming')
        ]
        framework_messages = [
            u"Become a Digital Outcomes and Specialists supplier",
            u"Digital Outcomes and Specialists will be open for applications soon."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

    def test_homepage_sidebar_message_exists_dos_open(self):

        framework_slugs_and_statuses = [
            ('g-cloud-7', 'pending'),
            ('digital-outcomes-and-specialists', 'open')
        ]
        framework_messages = [
            u"Become a Digital Outcomes and Specialists supplier",
            u"Digital Outcomes and Specialists is open for applications."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

    def test_homepage_sidebar_message_exists_g_cloud_7_pending(self):

        framework_slugs_and_statuses = [
            ('g-cloud-7', 'pending')
        ]
        framework_messages = [
            u"G‑Cloud 7 is closed for applications",
            u"G‑Cloud 7 services will be available from 23 November 2015."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

    def test_homepage_sidebar_message_doesnt_exist_without_frameworks(self):
        framework_slugs_and_statuses = [
            ('g-cloud-2', 'expired'),
            ('g-cloud-3', 'expired'),
            ('g-cloud-4', 'expired')
        ]

        # there are no messages
        self._load_homepage(framework_slugs_and_statuses, None)

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_api_error_message_doesnt_exist(self, data_api_client):

        data_api_client.find_frameworks.side_effect = APIError()
        res = self.client.get('/')
        assert_equal(200, res.status_code)
        self._assert_message_container_is_empty(res.get_data(as_text=True))

    # here we've given an valid framework with a valid status but there is no message.yml file to read from
    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_g_cloud_6_open_blows_up(self, data_api_client):
        framework_slugs_and_statuses = [
            ('g-cloud-6', 'open')
        ]

        data_api_client.find_frameworks.return_value = self._find_frameworks(framework_slugs_and_statuses)
        res = self.client.get('/')
        assert_equal(500, res.status_code)
