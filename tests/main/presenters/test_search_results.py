import os
import json

from flask import Markup
from app.main.presenters.search_results import SearchResults

from ...helpers import BaseApplicationTest
from app.main.helpers import framework_helpers


def _get_fixture_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_results_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


def _get_fixture_multiple_pages_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_results_multiple_pages_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


class TestSearchResults(BaseApplicationTest):

    def _get_service_result_by_id(self, results, id):
        for result in results:
            if result['id'] == id:
                return result
        return False

    def setup_method(self, method):
        super(TestSearchResults, self).setup_method(method)

        self.fixture = _get_fixture_data()
        self.multiple_pages_fixture = _get_fixture_multiple_pages_data()
        self._lots_by_slug = framework_helpers.get_lots_by_slug(
            self._get_framework_fixture_data('g-cloud-6')['frameworks']
        )

    def test_search_results_is_set(self):
        search_results_instance = SearchResults(self.fixture, self._lots_by_slug)
        assert hasattr(search_results_instance, 'search_results')

    def test_search_results_total_is_set(self):
        search_results_instance = SearchResults(self.fixture, self._lots_by_slug)
        assert hasattr(search_results_instance, 'total')
        assert search_results_instance.total == 9

    def test_search_results_page_is_not_set(self):
        search_results_instance = SearchResults(self.fixture, self._lots_by_slug)
        assert not hasattr(search_results_instance, 'page')

    def test_search_results_page_is_set(self):
        search_results_instance = SearchResults(self.multiple_pages_fixture, self._lots_by_slug)
        assert hasattr(search_results_instance, 'page')
        assert search_results_instance.page == "20"

    def test_highlighting_for_one_line_summary(self):
        search_results_instance = SearchResults(self.fixture, self._lots_by_slug)
        result_with_one_line_highlight = self._get_service_result_by_id(
            search_results_instance.search_results, '4-G4-0871-001'
        )
        assert result_with_one_line_highlight['serviceSummary'] == Markup(
            u"Fastly <em>CDN</em> (Content Delivery Network) speeds up delivery of your website and its content to your"
        )

    def test_highlighting_for_multiple_line_summary(self):
        search_results_instance = SearchResults(self.fixture, self._lots_by_slug)
        result_with_multi_line_highlight = self._get_service_result_by_id(
            search_results_instance.search_results, '4-G1-0340-001'
        )
        assert result_with_multi_line_highlight['serviceSummary'] == Markup(
            u" Baycloud Systems or in a suitable Content Delivery"
            u" Network (<em>CDN</em>) such as the Windows Azure" +
            u" <em>CDN</em>. The <em>CDN</em> improves performance" +
            u" by caching content at locations closest to visitors" +
            u" to customer\u2019s websites. The Windows Azure" +
            u" <em>CDN</em> is a managed service that is operated by" +
            u" Microsoft and has a 99.99% monthly"
        )

    def test_highlighting_only_happens_on_service_summaries(self):
        search_results_instance = SearchResults(self.fixture, self._lots_by_slug)
        result_with_service_name_highlight = self._get_service_result_by_id(
            search_results_instance.search_results, '5-G3-0279-010'
        )
        assert result_with_service_name_highlight['serviceName'] == "CDN VDMS"
