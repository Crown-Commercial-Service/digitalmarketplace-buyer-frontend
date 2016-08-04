import mock
import re
import json
from nose.tools import assert_equal, assert_true, assert_false, assert_in
from ...helpers import BaseApplicationTest
import pytest

#pytestmark = pytest.mark.skipif(True, reason='need to be adapted for Australia')


def find_pagination_links(res_data):
    return re.findall(
        '<li class="[next|previous]+">[^<]+<a\ href="(/g-cloud/search\?[^"]+)',
        res_data,
        re.MULTILINE)


def find_search_summary(res_data):
    return re.findall(
        r'<span class="search-summary-count">.+</span>[^\n]+', res_data)


@mock.patch('app.main.views.search.DataAPIClient')
class TestSearchSuppliers(BaseApplicationTest):

    def test_catalogue_page(self, api_client):
        res = self.client.get('/marketplace/search/suppliers')
        assert 200 == res.status_code

    def test_catalogue_has_filter_checkboxes(self, api_client):
        data = self._get_fixture_data('supplier_roles.json')
        api_client.return_value.get_roles.return_value = data
        res = self.client.get('/marketplace/search/suppliers')
        for role_row in data['roles']:
            role = role_row['role'].replace('Senior ', '').replace('Junior ', '')  # Mind the white space after Junior
            if 'type="checkbox" name="%s"' % role not in res.read:
                assert False
        assert True