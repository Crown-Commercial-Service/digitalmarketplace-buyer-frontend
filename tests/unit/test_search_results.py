import os
import json
import unittest
from nose.tools import assert_equal

from flask import Markup
from app.presenters.search_results import SearchResults


def _get_fixture_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_results_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


def _get_fixture_multiple_pages_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_results_multiple_pages_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


class TestSearchResults(unittest.TestCase):

    def _get_service_result_by_id(self, results, id):
        for result in results:
            if result['id'] == id:
                return result
        return False

    def setUp(self):
        self.fixture = _get_fixture_data()
        self.multiple_pages_fixture = _get_fixture_multiple_pages_data()
        self.service = SearchResults(self.fixture)

    def tearDown(self):
        pass

    def test_search_results_is_set(self):
        search_results_instance = SearchResults(self.fixture)
        self.assertTrue(hasattr(search_results_instance, 'search_results'))

    def test_search_results_total_is_set(self):
        search_results_instance = SearchResults(self.fixture)
        self.assertTrue(hasattr(search_results_instance, 'total'))
        assert_equal(search_results_instance.total, 9)

    def test_search_results_page_is_not_set(self):
        search_results_instance = SearchResults(self.fixture)
        self.assertFalse(hasattr(search_results_instance, 'page'))

    def test_search_results_page_is_set(self):
        search_results_instance = SearchResults(self.multiple_pages_fixture)
        self.assertTrue(hasattr(search_results_instance, 'page'))
        assert_equal(search_results_instance.page, "20")

    def test_highlighting_for_one_line_summary(self):
        search_results_instance = SearchResults(self.fixture)
        result_with_one_line_highlight = self._get_service_result_by_id(
            search_results_instance.search_results, '4-G4-0871-001'
        )
        self.assertEquals(
            result_with_one_line_highlight['serviceSummary'],
            Markup(
                u"Fastly <em>CDN</em> (Content Delivery Network) speeds up" +
                u" delivery of your website and its content to your"
            )
        )

    def test_highlighting_for_multiple_line_summary(self):
        search_results_instance = SearchResults(self.fixture)
        result_with_multi_line_highlight = self._get_service_result_by_id(
            search_results_instance.search_results, '4-G1-0340-001'
        )
        self.assertEquals(
            result_with_multi_line_highlight['serviceSummary'],
            Markup(
                u" Baycloud Systems or in a suitable Content Delivery"
                u" Network (<em>CDN</em>) such as the Windows Azure" +
                u" <em>CDN</em>. The <em>CDN</em> improves performance" +
                u" by caching content at locations closest to visitors" +
                u" to customer\u2019s websites. The Windows Azure" +
                u" <em>CDN</em> is a managed service that is operated by" +
                u" Microsoft and has a 99.99% monthly"
            )
        )

    def test_highlighting_only_happens_on_service_summaries(self):
        search_results_instance = SearchResults(self.fixture)
        result_with_service_name_highlight = self._get_service_result_by_id(
            search_results_instance.search_results, '5-G3-0279-010'
        )
        self.assertEquals(
            result_with_service_name_highlight['serviceName'],
            "CDN VDMS"
        )
