import mock
import re
import json
from ...helpers import BaseApplicationTest


def find_pagination_links(res_data):
    return re.findall(
        '<li class="[next|previous]+">[^<]+<a\ href="(/g-cloud/search\?[^"]+)',
        res_data,
        re.MULTILINE)


def find_search_summary(res_data):
    return re.findall(
        r'<span class="search-summary-count">.+</span>[^\n]+', res_data)


class TestSearchResults(BaseApplicationTest):
    def setup_method(self, method):
        super(TestSearchResults, self).setup_method(method)

        self._search_api_client_patch = mock.patch('app.main.views.g_cloud.search_api_client', autospec=True)
        self._search_api_client = self._search_api_client_patch.start()

        self.search_results = self._get_search_results_fixture_data()
        self.search_results_multiple_page = \
            self._get_search_results_multiple_page_fixture_data()

    def teardown_method(self, method):
        self._search_api_client_patch.stop()

    def test_search_page_results_service_links(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?q=email')
        assert res.status_code == 200
        assert '<a href="/g-cloud/services/5-G3-0279-010">CDN VDMS</a>' in res.get_data(as_text=True)

    def test_search_page_form(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?q=email')
        assert res.status_code == 200
        assert '<form action="/g-cloud/search" method="get">' in res.get_data(as_text=True)

    def test_search_page_allows_non_keyword_search(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?lot=saas')
        assert res.status_code == 200
        assert '<a href="/g-cloud/services/5-G3-0279-010">CDN VDMS</a>' in res.get_data(as_text=True)

    def test_should_not_render_pagination_on_single_results_page(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?lot=saas')
        assert res.status_code == 200
        assert '<li class="next">' not in res.get_data(as_text=True)
        assert '<li class="previous">' not in res.get_data(as_text=True)

    def test_should_render_pagination_link_on_first_results_page(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=saas')
        assert res.status_code == 200
        assert 'previous-next-navigation' in res.get_data(as_text=True)
        assert '<li class="previous">' not in res.get_data(as_text=True)
        assert '<li class="next">' in res.get_data(as_text=True)

        (next_link,) = find_pagination_links(res.get_data(as_text=True))
        assert 'page=2' in next_link
        assert 'lot=saas' in next_link

    def test_should_render_pagination_link_on_second_results_page(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=saas&page=2')
        assert res.status_code == 200
        assert 'previous-next-navigation' in res.get_data(as_text=True)
        assert '<li class="previous">' in res.get_data(as_text=True)
        assert '<li class="next">' in res.get_data(as_text=True)
        (prev_link, next_link) = find_pagination_links(
            res.get_data(as_text=True))

        assert 'page=1' in prev_link
        assert 'lot=saas' in prev_link
        assert 'page=3' in next_link
        assert 'lot=saas' in next_link

    def test_should_render_total_pages_on_pagination_links(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=saas&page=2')
        assert res.status_code == 200
        assert 'previous-next-navigation' in res.get_data(as_text=True)
        assert '<span class="page-numbers">1 of 200</span>' in res.get_data(as_text=True)
        assert '<span class="page-numbers">3 of 200</span>' in res.get_data(as_text=True)

    def test_should_render_pagination_link_on_last_results_page(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=saas&page=200')
        assert res.status_code == 200
        assert 'previous-next-navigation' in res.get_data(as_text=True)
        assert '<li class="previous">' in res.get_data(as_text=True)
        assert '<li class="next">' not in res.get_data(as_text=True)

        (prev_link,) = find_pagination_links(res.get_data(as_text=True))
        assert 'page=199' in prev_link
        assert 'lot=saas' in prev_link

    def test_should_render_summary_for_0_results_in_SaaS_no_keywords(self):
        self._search_api_client.search_services.return_value = {
            "services": [],
            "meta": {
                "query": {},
                "total": 0,
                "took": 3
            },
            "links": {}
        }

        res = self.client.get('/g-cloud/search?lot=saas')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">0</span> results found in <em>Software as a Service</em>' in summary

    def test_should_render_summary_for_1_result_in_SaaS_no_keywords(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get('/g-cloud/search?lot=saas')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found in <em>Software as a Service</em>' in summary

    def test_should_render_summary_for_1_result_in_IaaS_no_keywords(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get('/g-cloud/search?lot=iaas')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' in <em>Infrastructure as a Service</em>' in summary

    def test_should_render_summary_for_1_result_in_SaaS_with_keywords(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get('/g-cloud/search?q=email&lot=saas')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Software as a Service</em>' in summary

    def test_should_render_summary_with_a_group_of_1_boolean_filter(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=saas&freeOption=true')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Software as a Service</em>' \
            ' with a <em>Free option</em>' in summary

    def test_should_render_summary_with_a_group_of_2_boolean_filters(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=saas&freeOption=true' +
            '&trialOption=true')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Software as a Service</em>' \
            ' with a ' in summary
        assert '<em>Free option</em>' in summary
        assert '<em>Trial option</em>' in summary

    def test_should_render_summary_with_a_group_of_1_array_filter(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=saas&minimumContractPeriod=hour')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Software as a Service</em>' \
            ' with a minimum contract period of an <em>Hour</em>' \
            in summary

    def test_should_render_summary_with_a_group_of_2_array_filters(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=saas&minimumContractPeriod=hour' +
            '&minimumContractPeriod=day')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Software as a Service</em>' \
            ' with a minimum contract period of ' in summary
        assert 'an <em>Hour</em>' in summary
        assert 'a <em>Day</em>' in summary

    def test_should_render_summary_with_2_groups_of_filters(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=saas&freeOption=true' +
            '&minimumContractPeriod=hour&minimumContractPeriod=day')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Software as a Service</em>' in summary
        assert 'with a <em>Free option</em>' in summary
        assert 'with a minimum contract period of' in summary
        assert 'an <em>Hour</em>' in summary
        assert 'a <em>Day</em>' in summary

    def test_should_render_summary_with_3_groups_of_filters(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=email&lot=saas&freeOption=true' +
            '&minimumContractPeriod=hour&minimumContractPeriod=day' +
            '&datacentreTier=tia-942+tier+1')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found' \
            ' containing <em>email</em> in' \
            ' <em>Software as a Service</em>' in summary
        assert 'with a <em>Free option</em>' in summary
        assert 'with a minimum contract period of' in summary
        assert 'an <em>Hour</em>' in summary
        assert 'a <em>Day</em>' in summary
        assert 'with a datacentre tier of' in summary
        assert '<em>TIA-942 Tier 1</em>' in summary

    def test_should_ignore_unknown_arguments(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(
            '/g-cloud/search?q=&lot=saas' +
            '&minimumContractPeriod=hr&minimumContractPeriod=dy')

        assert res.status_code == 200

    def test_query_text_is_escaped(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get('/g-cloud/search?q=<div>XSS</div>')

        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '&lt;div&gt;XSS&lt;/div&gt;' in summary

    def test_summary_for_unicode_query_keywords(self):
        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get(u'/g-cloud/search?q=email+\U0001f47e&lot=saas')
        assert res.status_code == 200
        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert u'<span class="search-summary-count">1</span> result found' \
            u' containing <em>email \U0001f47e</em> in' \
            u' <em>Software as a Service</em>' in summary

    def test_should_404_on_invalid_page_param(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&page=1')
        assert res.status_code == 200

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&page=-1')
        assert res.status_code == 404

        res = self.client.get('/g-cloud/search?lot=cloud-hosting&page=potato')
        assert res.status_code == 404
