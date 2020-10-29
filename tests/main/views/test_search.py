import json
import re

from lxml import html
import mock
import pytest

from ...helpers import BaseApplicationTest, BaseAPIClientMixin


def find_pagination_links(doc):
    return doc.xpath(
        ("//li[contains(@class, 'dm-pagination__item--next') "
         "or contains(@class, 'dm-pagination__item--previous')]"
         "//a[starts-with(@href, $u)]"),
        u="/g-cloud/search?",
    )


def find_0_results_suggestion(res_data):
    xpath = html.fromstring(res_data).xpath
    return xpath('//div[contains(@class, "search-suggestion")]')


def get_0_results_search_response():
    return {
        "documents": [],
        "meta": {
            "query": {},
            "total": 0,
            "took": 3,
            "results_per_page": 100
        },
        "links": {}
    }


class APIClientMixin(BaseAPIClientMixin):
    data_api_client_patch_path = 'app.main.views.g_cloud.data_api_client'
    search_api_client_patch_path = 'app.main.views.g_cloud.search_api_client'


class TestSearchResults(APIClientMixin, BaseApplicationTest):
    def setup_method(self, method):
        super().setup_method(method)

        self.search_api_client.aggregate.return_value = self._get_fixture_data('g9_aggregations_fixture.json')
        self.search_results = self._get_search_results_fixture_data()
        self.g9_search_results = self._get_g9_search_results_fixture_data()
        self.search_results_multiple_page = self._get_search_results_multiple_page_fixture_data()

    def test_search_page_results_service_links(self):
        self.search_api_client.search.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?q=email')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        assert document.xpath(
            "//a[@href=$u][normalize-space(string())=$t]",
            u="/g-cloud/services/5-G3-0279-010",
            t="CDN VDMS",
        )

    def test_search_page_form(self):
        self.search_api_client.search.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?q=email')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        assert document.xpath("//form[@action=$a][@method='get'][@id='js-dm-live-search-form']", a="/g-cloud/search")

    def test_search_page_allows_non_keyword_search(self):
        self.search_api_client.search.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        assert document.xpath(
            "//a[@href=$u][normalize-space(string())=$t]",
            u="/g-cloud/services/5-G3-0279-010",
            t="CDN VDMS",
        )

    def test_should_not_render_pagination_on_single_results_page(self):
        self.search_api_client.search.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200
        assert '<li class="dm-pagination__item dm-pagination__item--next">' not in res.get_data(as_text=True)
        assert '<li class="dm-pagination__item dm-pagination__item--previous">' not in res.get_data(as_text=True)

    def test_should_render_pagination_link_on_first_results_page(self):
        self.search_api_client.search.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))
        assert '<nav class="dm-pagination"' in res.get_data(as_text=True)
        assert '<li class="dm-pagination__item dm-pagination__item--previous">' not in res.get_data(as_text=True)
        assert '<li class="dm-pagination__item dm-pagination__item--next">' in res.get_data(as_text=True)

        (next_link,) = find_pagination_links(document)
        assert 'page=2' in next_link.attrib["href"]
        assert 'lot=cloud-software' in next_link.attrib["href"]

    def test_should_render_pagination_link_on_second_results_page(self):
        self.search_api_client.search.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=cloud-software&page=2')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        assert '<nav class="dm-pagination"' in res.get_data(as_text=True)
        assert '<li class="dm-pagination__item dm-pagination__item--previous">' in res.get_data(as_text=True)
        assert '<li class="dm-pagination__item dm-pagination__item--next">' in res.get_data(as_text=True)

        (prev_link, next_link) = find_pagination_links(document)

        assert 'page=1' in prev_link.attrib["href"]
        assert 'lot=cloud-software' in prev_link.attrib["href"]
        assert 'page=3' in next_link.attrib["href"]
        assert 'lot=cloud-software' in next_link.attrib["href"]

    def test_should_render_total_pages_on_pagination_links(self):
        self.search_api_client.search.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=cloud-software&page=2')
        assert res.status_code == 200
        assert '<nav class="dm-pagination"' in res.get_data(as_text=True)
        assert '<span class="dm-pagination__link-label">1 of 200</span>' in res.get_data(as_text=True)
        assert '<span class="dm-pagination__link-label">3 of 200</span>' in res.get_data(as_text=True)

    def test_should_render_pagination_link_on_last_results_page(self):
        self.search_api_client.search.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=cloud-software&page=200')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        assert '<nav class="dm-pagination"' in res.get_data(as_text=True)
        assert '<li class="dm-pagination__item dm-pagination__item--previous">' in res.get_data(as_text=True)
        assert '<li class="dm-pagination__item dm-pagination__item--next">' not in res.get_data(as_text=True)

        (prev_link,) = find_pagination_links(document)
        assert 'page=199' in prev_link.attrib["href"]
        assert 'lot=cloud-software' in prev_link.attrib["href"]

    def test_should_render_summary_for_0_results_in_all_categories_no_keywords(self):
        self.search_api_client.search.return_value = get_0_results_search_response()

        res = self.client.get('/g-cloud/search')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="app-search-summary-count">0</span> results found in <em>All categories</em>' in summary

    def test_should_render_summary_for_0_results_in_cloud_software_no_keywords(self):
        self.search_api_client.search.return_value = get_0_results_search_response()

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="app-search-summary-count">0</span> results found in <em>Cloud software</em>' in summary

    def test_should_render_suggestions_for_0_results(self):
        self.search_api_client.search.return_value = get_0_results_search_response()

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200
        suggestion = find_0_results_suggestion(res.get_data(as_text=True))
        assert len(suggestion) == 1

    def test_should_render_clear_all_filters_link(self):
        self.search_api_client.search.return_value = get_0_results_search_response()

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        assert document.xpath(
            "//a[@id=$i][contains(@class, $c)][normalize-space(string())=normalize-space($t)][@href=$h]",
            i="dm-clear-all-filters",
            c="clear-filters-link",
            t="Clear filters",
            h="/g-cloud/search?lot=cloud-software",
        )

    def test_should_not_render_suggestions_for_when_results_are_shown(self):
        self.search_api_client.search.return_value = {
            "documents": [],
            "meta": {
                "query": {},
                "total": 2,
                "took": 3,
                "results_per_page": 30
            },
            "links": {}
        }

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200
        suggestion = find_0_results_suggestion(res.get_data(as_text=True))
        assert len(suggestion) == 0

    def test_should_render_summary_for_1_result_in_cloud_software_no_keywords(self):
        return_value = self.search_results_multiple_page
        return_value["documents"] = [return_value["documents"][0]]
        return_value["meta"]["total"] = 1
        self.search_api_client.search.return_value = return_value

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="app-search-summary-count">1</span> result found in <em>Cloud software</em>' in summary

    def test_should_render_summary_for_1_result_in_cloud_hosting_no_keywords(self):
        return_value = self.search_results_multiple_page
        return_value["documents"] = [return_value["documents"][0]]
        return_value["meta"]["total"] = 1
        self.search_api_client.search.return_value = return_value

        res = self.client.get('/g-cloud/search?lot=cloud-hosting')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="app-search-summary-count">1</span> result found' \
            ' in <em>Cloud hosting</em>' in summary

    def test_should_render_summary_for_1_result_in_cloud_software_with_keywords(self):
        return_value = self.search_results_multiple_page
        return_value["documents"] = [return_value["documents"][0]]
        return_value["meta"]["total"] = 1
        self.search_api_client.search.return_value = return_value

        res = self.client.get('/g-cloud/search?q=email&lot=cloud-software')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="app-search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' in summary

    def test_should_render_summary_with_a_group_of_1_boolean_filter(self):
        return_value = self.search_results_multiple_page
        return_value["documents"] = [return_value["documents"][0]]
        return_value["meta"]["total"] = 1
        self.search_api_client.search.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=cloud-software&phoneSupport=true')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="app-search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' \
            ' where user support is available by <em>phone</em>' in summary

    def test_should_render_summary_with_a_group_of_2_boolean_filters(self):
        return_value = self.search_results_multiple_page
        return_value["documents"] = [return_value["documents"][0]]
        return_value["meta"]["total"] = 1
        self.search_api_client.search.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=cloud-software&phoneSupport=true&onsiteSupport=yes')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="app-search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' in summary
        assert ' where user support is available ' in summary
        assert 'by <em>phone</em>' in summary
        assert 'through <em>onsite support</em>' in summary

    def test_should_render_summary_with_a_group_of_1_array_filter(self):
        return_value = self.search_results_multiple_page
        return_value["documents"] = [return_value["documents"][0]]
        return_value["meta"]["total"] = 1
        self.search_api_client.search.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=cloud-software&resellingType=not_reseller')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="app-search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' \
            ' where the supplier is <em>not a reseller</em>' \
            in summary

    def test_should_render_summary_with_a_group_of_2_array_filters(self):
        return_value = self.search_results_multiple_page
        return_value["documents"] = [return_value["documents"][0]]
        return_value["meta"]["total"] = 1
        self.search_api_client.search.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=cloud-software&resellingType=not_reseller&resellingType=reseller_no_extras')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="app-search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' \
            ' where the supplier is ' in summary
        assert '<em>not a reseller</em>' in summary
        assert 'a <em>reseller (no extras)</em>' in summary

    def test_should_render_summary_with_2_groups_of_filters(self):
        return_value = self.search_results_multiple_page
        return_value["documents"] = [return_value["documents"][0]]
        return_value["meta"]["total"] = 1
        self.search_api_client.search.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=cloud-software&phoneSupport=true' +
            '&resellingType=not_reseller&resellingType=reseller_no_extras')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="app-search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' in summary
        assert ' where the supplier is ' in summary
        assert '<em>not a reseller</em>' in summary
        assert 'a <em>reseller (no extras)</em>' in summary
        assert ' where user support is available by <em>phone</em>' in summary

    def test_should_render_summary_with_3_groups_of_filters(self):
        return_value = self.search_results_multiple_page
        return_value["documents"] = [return_value["documents"][0]]
        return_value["meta"]["total"] = 1
        self.search_api_client.search.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=cloud-software&phoneSupport=true' +
            '&resellingType=not_reseller&resellingType=reseller_no_extras' +
            '&governmentSecurityClearances=dv')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="app-search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Cloud software</em>' in summary
        assert ' where the supplier is ' in summary
        assert '<em>not a reseller</em>' in summary
        assert 'a <em>reseller (no extras)</em>' in summary
        assert ' where user support is available by <em>phone</em>' in summary
        assert 'where suppliers are prepared to make sure their staff have <em>Developed Vetting (DV)</em>' in summary

    def test_should_ignore_unknown_arguments(self):
        return_value = self.search_results_multiple_page
        return_value["documents"] = [return_value["documents"][0]]
        return_value["meta"]["total"] = 1
        self.search_api_client.search.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=&lot=cloud-software' +
            '&minimumContractPeriod=hr&minimumContractPeriod=dy')

        assert res.status_code == 200

    def test_query_text_is_escaped(self):
        return_value = self.search_results_multiple_page
        return_value["documents"] = [return_value["documents"][0]]
        return_value["meta"]["total"] = 1
        self.search_api_client.search.return_value = return_value

        res = self.client.get('/g-cloud/search?q=<div>XSS</div>')

        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '&lt;div&gt;XSS&lt;/div&gt;' in summary

    def test_summary_for_unicode_query_keywords(self):
        return_value = self.search_results_multiple_page
        return_value["documents"] = [return_value["documents"][0]]
        return_value["meta"]["total"] = 1
        self.search_api_client.search.return_value = return_value

        res = self.client.get(u'/g-cloud/search?q=email+\U0001f47e&lot=cloud-software')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert u'<span class="app-search-summary-count">1</span> result found' \
            u' containing <em>email \U0001f47e</em> in' \
            u' <em>Cloud software</em>' in summary

    def test_should_404_on_invalid_page_param(self):
        self.search_api_client.search.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&page=1')
        assert res.status_code == 200

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&page=-1')
        assert res.status_code == 404

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&page=potato')
        assert res.status_code == 404

    def test_search_results_with_invalid_lot_fall_back_to_all_categories(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=bad-lot-slug')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        lots = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//li/a')
        assert lots[0].text_content().startswith('Cloud hosting')
        assert lots[1].text_content().startswith('Cloud software')
        assert lots[2].text_content().startswith('Cloud support')

    def test_search_results_show_aggregations_by_lot(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        lots = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//li/a')
        assert lots[0].text_content() == 'Cloud hosting (500)'
        assert lots[1].text_content() == 'Cloud software (500)'
        assert lots[2].text_content() == 'Cloud support (500)'

    def test_search_results_does_not_show_aggregation_for_lot_if_category_selected(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        lots = document.xpath('//div[@class="lot-filters"]//li[@aria-current="page"]/strong')
        assert lots[0].text_content() == 'Cloud software'

    def test_search_results_show_aggregations_by_parent_category(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        category_matcher = re.compile(r'(.+) \((\d+)\)')
        expected_lot_counts = self._get_fixture_data('g9_aggregations_fixture.json')['aggregations']['service'
                                                                                                     'Categories']

        categories = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//li')
        for category in categories:
            category_name, number_of_services = category_matcher.match(category.text_content()).groups()
            assert expected_lot_counts[category_name] == int(number_of_services)

    def test_search_results_sends_aggregation_request_without_page_filter(self):
        self.data_api_client.find_frameworks.return_value = {
            'frameworks': [self._get_framework_fixture_data('g-cloud-9')['frameworks']]
        }
        self.search_api_client.search.return_value = self.search_results

        res = self.client.get('/g-cloud/search?page=2')
        assert res.status_code == 200

        self.search_api_client.aggregate.assert_called_with(
            index='g-cloud-9',
            doc_type='services',
            lot='cloud-support',
            aggregations={'serviceCategories', 'lot'}
        )

    def test_search_results_does_not_show_aggregation_for_lot_or_parent_category_if_child_selected(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software&serviceCategories=accounting+and+finance')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        all_categories = document.xpath('//div[@class="lot-filters"]/ul/li')[0]
        assert all_categories.xpath('a[@class="lot-filters__top-level-link"]')[0].text_content() == 'All categories'

        cloud_software = all_categories.xpath('ul/li')[0]
        assert cloud_software.xpath('a[@class="lot-filters__top-level-link"]')[0].text_content() == 'Cloud software'

        parent_category = cloud_software.xpath('ul/li[@aria-current="page"]')[0]
        assert parent_category.xpath('strong')[0].text_content() == 'Accounting and finance'

    def test_search_results_show_aggregations_by_child_category(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software&serviceCategories=accounting+and+finance')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        category_matcher = re.compile(r'(.+) \((\d+)\)')
        expected_lot_counts = self._get_fixture_data('g9_aggregations_fixture.json')['aggregations']['service'
                                                                                                     'Categories']

        categories = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//li')

        for category in categories:
            category_name, number_of_services = category_matcher.match(category.text_content()).groups()
            assert expected_lot_counts[category_name] == int(number_of_services)

    def test_search_results_subcategory_links_include_parent_category_param(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-software&serviceCategories=accounting+and+finance')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        categories_anchors = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//li/a')

        for category_anchor in categories_anchors:
            assert 'parentCategory=accounting+and+finance' in category_anchor.get('href')

    def test_lot_links_retain_all_category_filters(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?phoneSupport=true')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        lots = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//li/a')
        for lot in lots:
            assert 'phoneSupport=true' in lot.get('href')

    def test_all_category_link_drops_lot_specific_filters(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&phoneSupport=true&scalingType=automatic')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        lots = document.xpath('//div[@class="lot-filters"]/ul/li/a')
        assert 'phoneSupport=true' in lots[0].get('href')
        assert 'scalingType=automatic' not in lots[0].get('href')

    def test_subcategory_link_retains_lot_specific_filters(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&phoneSupport=true&scalingType=automatic')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        category_links = document.xpath('//div[@class="lot-filters"]/ul/li/ul/li/ul/li/a')
        for category_link in category_links:
            assert 'phoneSupport=true' in category_link.get('href')
            assert 'scalingType=automatic' in category_link.get('href')

    def test_category_with_no_results_is_not_a_link(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?lot=cloud-support')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        training = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//'
                                  'li[normalize-space(string())=$training]', training="Training (0)")
        assert len(training) == 1
        assert len(training[0].xpath('a')) == 0

    def test_filter_form_given_category_selection(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search?parentCategory=electronic+document+and+records+management+%28edrm%29&'
                              'lot=cloud-software&serviceCategories=content+management+system+%28cms%29')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        hidden_inputs = document.xpath('//form[@id="js-dm-live-search-form"]//input[@type="hidden"]')
        kv_pairs = {input_el.get('name'): input_el.get('value') for input_el in hidden_inputs}

        assert kv_pairs == {
            'lot': 'cloud-software',
            'serviceCategories': 'content management system (cms)',
            'parentCategory': 'electronic document and records management (edrm)',
        }

    @pytest.mark.parametrize(
        ('query_string', 'expected_breadcrumbs'),
        (
            ('', (
                ('Digital Marketplace', '/'),
                ('Cloud hosting, software and support', '')
            )),
            ('?lot=foo', (
                ('Digital Marketplace', '/'),
                ('Cloud hosting, software and support', '')
            )),
            ('?bar=foo', (
                ('Digital Marketplace', '/'),
                ('Cloud hosting, software and support', '')
            )),
            ('?lot=cloud-software', (
                ('Digital Marketplace', '/'),
                ('Cloud hosting, software and support', '/g-cloud'),
                ('Cloud software', '')
            )),
            ('?lot=cloud-hosting', (
                ('Digital Marketplace', '/'),
                ('Cloud hosting, software and support', '/g-cloud'),
                ('Cloud hosting', '')
            )),
            ('?lot=cloud-support', (
                ('Digital Marketplace', '/'),
                ('Cloud hosting, software and support', '/g-cloud'),
                ('Cloud support', '')
            ))
        )
    )
    def test_breadcrumbs(self, query_string, expected_breadcrumbs):
        self.search_api_client.search.return_value = self.g9_search_results
        res = self.client.get('/g-cloud/search{}'.format(query_string))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))
        found_breadcrumb_elements = document.xpath("//div[@class='govuk-breadcrumbs']/ol/li")
        found_breadcrumbs = (
            (element.xpath("normalize-space(string())"), element.xpath("normalize-space(string(.//a/@href))"))
            for element in found_breadcrumb_elements
        )

        for found_breadcrumb, expected_breadcrumb in zip(found_breadcrumbs, expected_breadcrumbs):
            assert found_breadcrumb == expected_breadcrumb


class TestSearchFilterOnClick(APIClientMixin, BaseApplicationTest):
    def setup_method(self, method):
        super().setup_method(method)

        self.search_api_client.aggregate.return_value = self._get_fixture_data('g9_aggregations_fixture.json')

        self.search_results = self._get_search_results_fixture_data()
        self.g9_search_results = self._get_g9_search_results_fixture_data()
        self.search_results_multiple_page = self._get_search_results_multiple_page_fixture_data()

        self.search_api_client.search.return_value = self.search_results

    @pytest.mark.parametrize('query_string, content_type',
                             (('', 'text/html; charset=utf-8'),
                              ('?live-results=true', 'application/json')))
    def test_endpoint_switches_on_live_results_request(self, query_string, content_type):
        res = self.client.get('/g-cloud/search{}'.format(query_string))
        assert res.status_code == 200
        assert res.content_type == content_type

    def test_live_results_returns_valid_json_structure(self):
        res = self.client.get('/g-cloud/search?live-results=true')
        data = json.loads(res.get_data(as_text=True))

        assert sorted(data.keys()) == sorted((
            'results',
            'summary',
            'summary-accessible-hint',
            'categories',
            'save-form',
            'filter-title'
        ))

        for k, v in data.items():
            assert set(v.keys()) == {'selector', 'html'}

            # We want to enforce using css IDs to describe the nodes which should be replaced.
            assert v['selector'].startswith('#')

    live_results_expected_templates = (
        "search/_results_wrapper.html",
        "search/_categories_wrapper.html",
        "search/_summary.html",
        "search/_summary_accessible_hint.html",
        "search/_services_save_search.html",
        "search/_filter_title.html"
    )

    @pytest.mark.parametrize(
        ('query_string', 'urls'),
        (
            ('', ('search/services.html',)),
            ('?live-results=true', live_results_expected_templates)
        )
    )
    @mock.patch('app.main.views.g_cloud.render_template', autospec=True)
    def test_base_page_renders_search_services(self, render_template_patch, query_string, urls):
        render_template_patch.return_value = '<p>some html</p>'

        self.client.get('/g-cloud/search{}'.format(query_string))

        assert urls == tuple(x[0][0] for x in render_template_patch.call_args_list)

    def test_g_cloud_search_has_js_hidden_filter_button(self):
        res = self.client.get('/g-cloud/search')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        filter_button = document.xpath(
            '//button[contains(@class, "js-hidden")][contains(@class, "js-dm-live-search")]'
            '[normalize-space(text())="Filter"]'
        )
        assert len(filter_button) == 1
