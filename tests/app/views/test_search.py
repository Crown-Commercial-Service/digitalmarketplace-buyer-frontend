from flask.helpers import url_for
import mock
import re
from ...helpers import BaseApplicationTest
from lxml import html


def find_pagination_links(res_data):
    return re.findall(
        '<li class="[next|previous]+">[^<]+<a\ href="(/g-cloud/search\?[^"]+)',
        res_data,
        re.MULTILINE)


def find_search_summary(res_data):
    return re.findall(
        r'<span class="search-summary-count">.+</span>[^\n]+', res_data)


class TestCataloguePageNewDomains(BaseApplicationTest):
    def setup(self):
        super(TestCataloguePageNewDomains, self).setup()

        with self.app.app_context():
            self.base_url = url_for('main.supplier_search')

        self._api_client = mock.patch('app.main.views.search.DataAPIClient').start()
        self._results_per_page = mock.patch('app.main.views.search.SUPPLIER_RESULTS_PER_PAGE', 4).start()

        self.results_json = self._get_fixture_data('supplier_results.json')
        self.domains_json = self._get_fixture_data('supplier_domains.json')

        self._api_client.return_value.req.get_domains.return_value = self.domains_json
        self._api_client.return_value.find_suppliers.return_value = self.results_json

    def _get_response_and_page(self, url=''):
        response = self.client.get(self.base_url + url)
        page = html.fromstring(response.get_data(as_text=True))
        return response, page

    def test_fixture_has_more_than_8_results_to_test_pagination(self):
        """
        This test is patched to have 4 results per page. So the test data must have 9 or more results to be able to
        go up to page 3 to test.
        """
        assert len(self.results_json['hits']['hits']) > 8

    def test_catalogue_first_page_loads(self):
        response, page = self._get_response_and_page()
        assert response.status_code == 200

    def test_catalogue_second_page_loads(self):
        response, page = self._get_response_and_page('?page=2')
        assert response.status_code == 200

    def test_catalogue_has_filter_checkboxes(self):
        response, page = self._get_response_and_page()
        page = html.fromstring(response.get_data(as_text=True))

        for role_row in self.domains_json['domains']:
            role = role_row['name']
            checkbox = page.get_element_by_id(role.lower().replace(' ', '_').replace('&', '').replace(',', '')
                                              .replace('__', '_'), None)
            assert (checkbox is not None and checkbox.name == 'role' and checkbox.type == 'checkbox')

    def test_catalogue_first_page_has_correct_number_of_results(self):
        response, page = self._get_response_and_page()
        page = html.fromstring(response.get_data(as_text=True))
        assert len(page.find_class('card')) == 4

    def test_catalogue_search(self):
        supplier_name = self.results_json['hits']['hits'][0]['_source']['name']

        response, page = self._get_response_and_page('?keyword=%s' % supplier_name.replace(' ', '+'))

        found = False
        for result in page.find_class('card'):
            for element, attribute, link, pos in result.iterlinks():
                if element.text_content().strip() == supplier_name:
                    found = True
                    break
        assert found

    def test_clear_buttons_have_valid_url(self):
        response, page = self._get_response_and_page()
        valid = True
        for button in page.find_class('clear-all'):
            if button.attrib['href'] not in self.base_url:
                valid = False
        assert valid

    def test_with_sort_by_parameter(self):
        response = self.client.get(self.url_for('main.supplier_search', sort_by='latest'))
        assert response.status_code == 200

    def test_invalid_sort_order(self):
        response = self.client.get(self.url_for('main.supplier_search', sort_order='no'))
        assert response.status_code == 400

    def test_invalid_sort_term(self):
        response = self.client.get(self.url_for('main.supplier_search', sort_term='no'))
        assert response.status_code == 400
        assert 'sort_term' in response.get_data(as_text=True)

    def test_invalid_role(self):
        response = self.client.get(self.url_for('main.supplier_search', role='no'))
        assert response.status_code == 400
        assert 'role' in response.get_data(as_text=True)

    def test_invalid_page(self):
        response = self.client.get(self.url_for('main.supplier_search', page='no'))
        assert response.status_code == 400
        assert 'page' in response.get_data(as_text=True)
