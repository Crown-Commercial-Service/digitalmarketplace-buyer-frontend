# coding=utf-8

import mock
from nose.tools import assert_equal, assert_true, assert_in
from lxml import html
from ...helpers import BaseApplicationTest
from dmapiclient import APIError
import pytest


class TestHomepageBrowseList(BaseApplicationTest):
    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_homepage_headers(self, data_api_client):
        res = self.client.get(self.expand_path('/'))
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        headers = [
            item.text_content().strip() for item in document.cssselect('article#content h2')
        ]

        assert headers == [
            'Government buyers',
            'Sellers',
            'Learn more',
        ]


class TestStaticMarketplacePages(BaseApplicationTest):
    def setup(self):
        super(TestStaticMarketplacePages, self).setup()

    def test_cookie_page(self):
        res = self.client.get(self.expand_path('/cookies'))
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>Cookies</h1>'
            in self._strip_whitespace(res.get_data(as_text=True))
        )

    def test_cookie_page(self):
        res = self.client.get(self.expand_path('/terms-and-conditions'))
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>Termsandconditions</h1>'
            in self._strip_whitespace(res.get_data(as_text=True))
        )
