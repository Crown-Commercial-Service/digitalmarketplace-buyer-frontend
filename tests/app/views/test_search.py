from flask.helpers import url_for
import mock
import re
import json
from nose.tools import assert_equal, assert_true, assert_false, assert_in
from ...helpers import BaseApplicationTest
from lxml import html
import pytest


def find_pagination_links(res_data):
    return re.findall(
        '<li class="[next|previous]+">[^<]+<a\ href="(/g-cloud/search\?[^"]+)',
        res_data,
        re.MULTILINE)


def find_search_summary(res_data):
    return re.findall(
        r'<span class="search-summary-count">.+</span>[^\n]+', res_data)


@mock.patch('app.main.views.search.SUPPLIER_RESULTS_PER_PAGE', 4)
@mock.patch('app.main.views.search.DataAPIClient')
class TestCataloguePage(BaseApplicationTest):

    def _setUp(self, url, api_client):
        base_url = '/marketplace/search/suppliers'
        url = base_url + url

        self.roles_json = self._get_fixture_data('supplier_roles.json')
        self.results_json = self._get_fixture_data('supplier_results.json')

        api_client.return_value.get_roles.return_value = self.roles_json
        api_client.return_value.find_suppliers.return_value = self.results_json

        self.response = self.client.get(url)
        self.page = html.fromstring(self.response.get_data(as_text=True))

    def test_fixture_has_more_than_8_results_to_test_pagination(self, api_client):
        self._setUp('', api_client)
        assert len(self.results_json['hits']['hits']) > 8

    def test_catalogue_first_page_loads(self, api_client):
        self._setUp('', api_client)
        assert self.response.status_code == 200

    def test_catalogue_second_page_loads(self, api_client):
        self._setUp('?page=2', api_client)
        assert self.response.status_code == 200

    def test_catalogue_has_filter_checkboxes(self, api_client):
        self._setUp('', api_client)
        for role_row in self.roles_json['roles']:
            role = role_row['role'].replace('Senior ', '').replace('Junior ', '')  # Mind the white space after Junior
            checkbox = self.page.get_element_by_id(role.lower().replace(' ', '-'), None)
            assert (checkbox is not None and checkbox.name == 'role' and checkbox.type == 'checkbox')

    def test_catalogue_first_page_has_correct_number_of_results(self, api_client):
        self._setUp('', api_client)
        assert len(self.page.find_class('supplier-result')) == len(self.results_json['hits']['hits'])

    def test_catalogue_second_page_has_back_page_link(self, api_client):
        self._setUp('?page=2', api_client)
        found = False
        for element, attribute, link, pos in self.page.find_class('pagination')[0].iterlinks():
            if 'page=1' in link:
                found = True
        assert found

    def test_catalogue_second_page_has_next_page_link(self, api_client):
        self._setUp('?page=2', api_client)
        found = False
        for element, attribute, link, pos in self.page.find_class('pagination')[0].iterlinks():
            if 'page=3' in link:
                found = True
        assert found

    def test_catalogue_pagination_links_have_supplied_query_string(self, api_client):
        self._setUp('?page=2&sort_term=name&sort_order=desc&role=Agile+Coach&role=Delivery+Manager', api_client)
        found = False
        for element, attribute, link, pos in self.page.find_class('pagination')[0].iterlinks():
            # Because it can be in any order
            if 'page=2' in link and 'sort_term=name' in link and 'sort_order=desc' in link and \
               'role=Agile+Coach' in link and 'role=Delivery+Manager' in link:
                found = True
        assert found


