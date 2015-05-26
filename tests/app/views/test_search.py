import mock
from nose.tools import assert_equal, assert_true, assert_false
from ...helpers import BaseApplicationTest


class TestSearchResults(BaseApplicationTest):
    def setup(self):
        super(TestSearchResults, self).setup()

        self._search_api_client = mock.patch(
            'app.main.views.search_api_client'
        ).start()

        self.search_results = self._get_search_results_fixture_data()
        self.search_results_multiple_page = \
            self._get_search_results_multiple_page_fixture_data()

    def teardown(self):
        self._search_api_client.stop()

    def test_search_page_redirect(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/search?q=email')
        assert_equal(301, res.status_code)
        assert_equal('http://localhost/g-cloud/search?q=email', res.location)

    def test_search_page_results_service_links(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?q=email')
        assert_equal(200, res.status_code)
        assert_true(
            '<a href="/g-cloud/services/5-G3-0279-010">CDN VDMS</a>'
            in res.get_data(as_text=True))

    def test_search_page_form(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?q=email')
        assert_equal(200, res.status_code)
        assert_true(
            '<form action="/g-cloud/search" method="get">'
            in res.get_data(as_text=True))

    def test_search_page_allows_non_keyword_search(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?lot=saas')
        assert_equal(200, res.status_code)
        assert_true(
            '<a href="/g-cloud/services/5-G3-0279-010">CDN VDMS</a>'
            in res.get_data(as_text=True))

    def test_should_not_render_pagination_on_single_results_page(self):
        self._search_api_client.search_services.return_value = \
            self.search_results

        res = self.client.get('/g-cloud/search?lot=saas')
        assert_equal(200, res.status_code)
        assert_false(
            '<li class="next">'
            in res.get_data(as_text=True))
        assert_false(
            '<li class="previous">'
            in res.get_data(as_text=True))

    def test_should_render_pagination_link_on_first_results_page(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=saas')
        assert_equal(200, res.status_code)
        assert_true(
            'previous-next-navigation'
            in res.get_data(as_text=True))
        assert_false(
            '<li class="previous">'
            in res.get_data(as_text=True))
        assert_true(
            '<li class="next">'
            in res.get_data(as_text=True))
        assert_true(
            '<a href="/g-cloud/search?page=2&amp;lot=saas">'
            in res.get_data(as_text=True))

    def test_should_render_pagination_link_on_second_results_page(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=saas&page=2')
        assert_equal(200, res.status_code)
        assert_true(
            'previous-next-navigation'
            in res.get_data(as_text=True))
        assert_true(
            '<li class="previous">'
            in res.get_data(as_text=True))
        assert_true(
            '<li class="next">'
            in res.get_data(as_text=True))
        assert_true(
            '<a href="/g-cloud/search?page=1&amp;lot=saas">'
            in res.get_data(as_text=True))
        assert_true(
            '<a href="/g-cloud/search?page=3&amp;lot=saas">'
            in res.get_data(as_text=True))

    def test_should_render_total_pages_on_pagination_links(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=saas&page=2')
        assert_equal(200, res.status_code)
        assert_true(
            'previous-next-navigation'
            in res.get_data(as_text=True))
        assert_true(
            '<span class="page-numbers">1 of 200</span>'
            in res.get_data(as_text=True))
        assert_true(
            '<span class="page-numbers">3 of 200</span>'
            in res.get_data(as_text=True))

    def test_should_render_pagination_link_on_last_results_page(self):
        self._search_api_client.search_services.return_value = \
            self.search_results_multiple_page

        res = self.client.get('/g-cloud/search?lot=saas&page=200')
        assert_equal(200, res.status_code)
        assert_true(
            'previous-next-navigation'
            in res.get_data(as_text=True))
        assert_true(
            '<li class="previous">'
            in res.get_data(as_text=True))
        assert_false(
            '<li class="next">'
            in res.get_data(as_text=True))
        assert_true(
            '<a href="/g-cloud/search?page=199&amp;lot=saas">'
            in res.get_data(as_text=True))
