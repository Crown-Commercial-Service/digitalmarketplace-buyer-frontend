import os
import json
import unittest
from nose.tools import assert_equal, assert_is_none

from flask import Markup
from mock import Mock
from werkzeug.datastructures import MultiDict
from app.presenters.search_presenters import (
    SearchResults, SearchSummary, SearchFilters, SummaryFragment, SummaryRules)


filter_groups = SearchFilters.get_filter_groups_from_questions(
    manifest="app/helpers/questions_manifest.yml",
    questions_dir="bower_components/digital-marketplace-ssp-content/g6/"
)


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


class TestSearchSummary(unittest.TestCase):

    def setUp(self):
        self.fixture = _get_fixture_data()
        self.search_results = SearchResults(self.fixture)
        self.request_args = MultiDict([
            ('lot', 'saas'),
            ('q', 'email')])

    def tearDown(self):
        pass

    def test_write_list_as_sentence_with_one_item(self):
        self.assertEqual(
            SearchSummary.write_list_as_sentence(['item1'], 'and'),
            u"item1")

    def test_write_list_as_sentence_with_two_items(self):
        self.assertEqual(
            SearchSummary.write_list_as_sentence(['item1', 'item2'], 'and'),
            u"item1 and item2")

    def test_write_list_as_sentence_with_three_items(self):
        self.assertEqual(
            SearchSummary.write_list_as_sentence(
                ['item1', 'item2', 'item3'], 'and'),
            u"item1, item2 and item3")

    def test_write_parts_as_sentence_with_first_part_None(self):
        self.assertEqual(
            SearchSummary.write_parts_as_sentence(
                [None, u"Hour"]),
            u"Hour")

    def test_write_parts_as_sentence_with_second_part_None(self):
        self.assertEqual(
            SearchSummary.write_parts_as_sentence(
                [u"Hour", None]),
            u"Hour")

    def test_write_parts_as_sentence_with_both_parts_not_None(self):
        self.assertEqual(
            SearchSummary.write_parts_as_sentence(
                [u"an", u"Hour"]),
            u"an Hour")

    def test_search_summary_works_with_keywords(self):
        search_summary = SearchSummary('1', self.request_args, filter_groups)
        self.assertEqual(search_summary.count, '1')
        self.assertEqual(search_summary.sentence, (
            u"result found containing <em>&ldquo;email&rdquo;</em>" +
            u" in <em>Software as a Service</em>"))
        self.assertEqual(len(search_summary.filters_fragments), 0)

    def test_search_summary_works_with_blank_keywords(self):
        self.request_args.setlist('q', [''])
        search_summary = SearchSummary('1', self.request_args, filter_groups)
        self.assertEqual(search_summary.count, '1')
        self.assertEqual(search_summary.sentence, (
            u"result found containing <em>&ldquo;&rdquo;</em>" +
            u" in <em>Software as a Service</em>"))
        self.assertEqual(len(search_summary.filters_fragments), 0)

    def test_search_summary_works_with_a_different_lot(self):
        self.request_args.setlist('lot', ['iaas'])
        search_summary = SearchSummary('1', self.request_args, filter_groups)
        self.assertEqual(search_summary.count, '1')
        self.assertEqual(search_summary.sentence, (
            u"result found containing <em>&ldquo;email&rdquo;</em>" +
            u" in <em>Infrastructure as a Service</em>"))
        self.assertEqual(len(search_summary.filters_fragments), 0)

    def test_search_summary_works_with_no_results(self):
        search_summary = SearchSummary('0', self.request_args, filter_groups)
        self.assertEqual(search_summary.count, '0')
        self.assertEqual(search_summary.sentence, (
            u"results found containing <em>&ldquo;email&rdquo;</em>" +
            u" in <em>Software as a Service</em>"))
        self.assertEqual(len(search_summary.filters_fragments), 0)

    def test_search_summary_works_with_single_result(self):
        search_summary = SearchSummary(1, self.request_args, filter_groups)
        self.assertEqual(search_summary.count, '1')
        self.assertEqual(search_summary.sentence, (
            u"result found containing <em>&ldquo;email&rdquo;</em>" +
            u" in <em>Software as a Service</em>"))
        self.assertEqual(len(search_summary.filters_fragments), 0)

    def test_search_summary_works_with_multiple_results(self):
        search_summary = SearchSummary('9', self.request_args, filter_groups)
        self.assertEqual(search_summary.count, '9')
        self.assertEqual(search_summary.sentence, (
            u"results found containing <em>&ldquo;email&rdquo;</em>" +
            u" in <em>Software as a Service</em>"))
        self.assertEqual(len(search_summary.filters_fragments), 0)

    def test_search_summary_with_a_single_filter_group(self):
        self.request_args.setlist('serviceTypes', ['collaboration'])
        search_summary = SearchSummary('9', self.request_args, filter_groups)
        self.assertEqual(search_summary.count, '9')
        self.assertEqual(search_summary.sentence, (
            u"results found containing <em>&ldquo;email&rdquo;</em>" +
            u" in <em>Software as a Service</em>"))
        self.assertEqual(len(search_summary.filters_fragments), 1)

    def test_search_summary_with_two_filter_groups(self):
        self.request_args.setlist(
            'serviceTypes',
            ['collaboration', 'energy and environment']
        )
        self.request_args.setlist(
            'datacentreTier',
            ['tia-942 tier 1', 'uptime institute tier 1']
        )
        search_summary = SearchSummary('9', self.request_args, filter_groups)
        self.assertEqual(search_summary.count, '9')
        self.assertEqual(search_summary.sentence, (
            u"results found containing <em>&ldquo;email&rdquo;</em>" +
            u" in <em>Software as a Service</em>"))
        self.assertEqual(len(search_summary.filters_fragments), 2)

    def test_search_summary_with_three_filter_groups(self):
        self.request_args.setlist(
            'serviceTypes',
            ['collaboration', 'energy and environment']
        )
        self.request_args.setlist(
            'datacentreTier',
            ['tia-942 tier 1', 'uptime institute tier 1']
        )
        self.request_args.setlist(
            'freeOption',
            ['true']
        )
        self.request_args.setlist(
            'trialOption',
            ['true']
        )
        search_summary = SearchSummary('9', self.request_args, filter_groups)
        self.assertEqual(search_summary.count, '9')
        self.assertEqual(search_summary.sentence, (
            u"results found containing <em>&ldquo;email&rdquo;</em>" +
            u" in <em>Software as a Service</em>"))
        self.assertEqual(len(search_summary.filters_fragments), 3)

    def test_search_summary_orders_filter_groups_as_in_manifest(self):
        self.request_args.setlist(
            'serviceTypes',
            ['collaboration', 'energy and environment']
        )
        self.request_args.setlist(
            'datacentreTier',
            ['tia-942 tier 1', 'uptime institute tier 1']
        )
        self.request_args.setlist(
            'freeOption',
            ['true']
        )
        self.request_args.setlist(
            'trialOption',
            ['true']
        )
        search_summary = SearchSummary('9', self.request_args, filter_groups)
        correct_order = [
            'Categories', 'Pricing', 'Datacentre tier'
        ]
        order_of_groups_of_filters = [
            fragment.id for fragment in search_summary.filters_fragments]
        self.assertEqual(order_of_groups_of_filters, correct_order)

    def test_get_starting_sentence_works(self):
        search_summary = SearchSummary('9', self.request_args, filter_groups)
        search_summary.count = '9'
        search_summary.COUNT_PRE_TAG = '<em>'
        search_summary.COUNT_POST_TAG = '</em>'
        search_summary.sentence = (
            u"results found containing <em>&ldquo;email&rdquo;</em>" +
            u" in <em>Software as a Service</em>")
        self.assertEqual(search_summary.get_starting_sentence(), (
            u"<em>9</em> results found containing" +
            u" <em>&ldquo;email&rdquo;</em> in" +
            u" <em>Software as a Service</em>"))

    def test_markup_method_works_with_no_fragments(self):
        def get_starting_sentence():
            return u"5 results found"

        search_summary = SearchSummary(9, self.request_args, filter_groups)
        search_summary.get_starting_sentence = get_starting_sentence
        search_summary.filters_fragments = []
        self.assertEqual(
            search_summary.markup(),
            Markup(u"5 results found"))

    def test_markup_method_works_with_fragments(self):
        def get_starting_sentence():
            return u"5 results found"

        fragment = Mock(**{"str.return_value": u"with option1 and option2"})
        search_summary = SearchSummary(9, self.request_args, filter_groups)
        search_summary.get_starting_sentence = get_starting_sentence
        search_summary.filters_fragments = [fragment]
        self.assertEqual(
            search_summary.markup(),
            Markup(u"5 results found with option1 and option2"))


class TestSummaryRules(unittest.TestCase):

    def setUp(self):
        if SummaryRules.loaded is False:
            SummaryRules.load_rules(manifest=os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                'app',
                'helpers',
                'search_summary_manifest.yml'
            ))

    def tearDown(self):
        pass

    def test_set_up_where_rules_do_not_exist(self):
        summary_rules = SummaryRules('Sites')
        self.assertFalse(summary_rules.exist)

    def test_set_up_where_rules_do_exist(self):
        summary_rules = SummaryRules('Categories')
        self.assertTrue(summary_rules.exist)

    def test_get_method_works_for_key_with_value(self):
        summary_rules = SummaryRules('Categories')
        self.assertEqual(summary_rules.get('conjunction'), 'and')

    def test_get_method_works_for_empty_key(self):
        summary_rules = SummaryRules('Categories')
        self.assertEqual(summary_rules.get('filterRules'), None)

    def test_filter_rules_ids_are_set_if_filterRules_exist(self):
        summary_rules = SummaryRules('Minimum contract period')
        self.assertTrue(hasattr(summary_rules, "filter_rules_ids"))
        self.assertEqual(
            summary_rules.filter_rules_ids,
            ['Hour', 'Day', 'Month', 'Year', 'Other'])

    def test_add_preposition_with_a_filter_that_has_one(self):
        summary_rules = SummaryRules('Minimum contract period')
        self.assertEqual(
            u"an <em>Hour</em>", summary_rules.add_filter_preposition(
                filter_id='Hour', filter_string=u"<em>Hour</em>"))

    def test_add_preposition_with_a_filter_without_any_for_its_group(self):
        summary_rules = SummaryRules('Pricing')
        self.assertEqual(
            u"<em>Trial option</em>", summary_rules.add_filter_preposition(
                filter_id='Trial option',
                filter_string=u"<em>Trial option</em>"))

    def test_add_preposition_with_a_filter_without_in_a_group_with_some(self):
        SummaryRules._rules['Minimum contract period']['filterRules'].remove({
            'preposition': 'an',
            'id': 'Hour'
        })
        summary_rules = SummaryRules('Minimum contract period')
        self.assertEqual(
            u"<em>Hour</em>", summary_rules.add_filter_preposition(
                filter_id='Hour',
                filter_string=u"<em>Hour</em>"))
        # Make SummaryRules to reload its data
        SummaryRules.loaded = False


class TestSummaryFragment(unittest.TestCase):

    def _get_mock(self, key):
        return self.rules[key]

    def setUp(self):
        self.rules_instance = SummaryRules('')
        self.rules_instance_mock = Mock()
        self.rules = {
            'id': 'Datacentre tier',
            'labelPreposition': None,
            'label': None,
            'filtersPreposition': None,
            'filterRules': None,
            'conjunction': 'or'
        }
        self.rules_instance_mock.get = self._get_mock

    def tearDown(self):
        pass

    def test_fragment_has_correct_form_for_a_single_filter(self):
        id = 'Datacentre tier'
        filters = ['TIA-942 Tier 1']
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        self.assertTrue(hasattr(summary_fragment, 'form'))
        self.assertEqual(summary_fragment.form, 'singular')

    def test_fragment_has_correct_form_for_multiple_filters(self):
        id = 'Datacentre tier'
        filters = ['TIA-942 Tier 1', 'uptime institute tier 1']
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        self.assertTrue(hasattr(summary_fragment, 'form'))
        self.assertEqual(summary_fragment.form, 'plural')

    def test_fragment_with_no_label_and_single_filter(self):
        id = 'Datacentre tier'
        filters = ['TIA-942 Tier 1']
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        self.assertEqual(
            summary_fragment.str(), u"<em>TIA-942 Tier 1</em>")

    def test_fragment_with_label_and_one_filter(self):
        id = 'Datacentre tier'
        filters = ['TIA-942 Tier 1']
        self.rules['label'] = {
            'singular': 'datacentre tier',
            'plural': 'datacentre tier'
        }
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        self.assertEqual(
            summary_fragment.str(), u"datacentre tier <em>TIA-942 Tier 1</em>")

    def test_fragment_with_label_and_two_filters(self):
        id = 'Datacentre tier'
        filters = ['TIA-942 Tier 1', 'uptime institute tier 1']
        self.rules['label'] = {
            'singular': 'datacentre tier',
            'plural': 'datacentre tiers'
        }
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        self.assertEqual(
            summary_fragment.str(),
            u"datacentre tiers <em>TIA-942 Tier 1</em>" +
            u" or <em>uptime institute tier 1</em>")

    def test_fragment_with_label_and_three_filters(self):
        id = 'Datacentre tier'
        filters = [
            'TIA-942 Tier 1',
            'uptime institute tier 1',
            'uptime institute tier 2']
        self.rules['label'] = {
            'singular': 'datacentre tier',
            'plural': 'datacentre tiers'
        }
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        self.assertEqual(
            summary_fragment.str(),
            u"datacentre tiers <em>TIA-942 Tier 1</em>" +
            u", <em>uptime institute tier 1</em>" +
            u" or <em>uptime institute tier 2</em>")

    def test_fragment_with_label_and_three_filters_with_prepositions(self):

        def _add_preposition(filter_id=None, filter_string=None):
            if filter_id == 'TIA-942 Tier 1':
                preposition = 'with a'
            elif filter_id == 'uptime institute tier 1':
                preposition = 'met with a'
            elif filter_id == 'uptime institute tier 2':
                preposition = 'aligned with'
            return u"{} {}".format(preposition, filter_string)

        id = 'Datacentre tier'
        filters = [
            'TIA-942 Tier 1',
            'uptime institute tier 1',
            'uptime institute tier 2']
        self.rules['label'] = {
            'singular': 'datacentre tier',
            'plural': 'datacentre tiers'
        }
        self.rules['filterRules'] = []  # filterRules just needs to be set
        self.rules_instance_mock.filter_rules_ids = filters
        self.rules_instance_mock.add_filter_preposition = _add_preposition
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        self.assertEqual(
            summary_fragment.str(),
            u"datacentre tiers with a <em>TIA-942 Tier 1</em>" +
            u", met with a <em>uptime institute tier 1</em>" +
            u" or aligned with <em>uptime institute tier 2</em>")

    def test_str_method_works(self):
        id = 'Datacentre tier'
        filters = ['TIA-942 Tier 1']
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        summary_fragment.label_string = u"categories"
        summary_fragment.filters = [u"FreeOption"]
        self.rules['filtersPreposition'] = 'with'
        self.assertEqual(summary_fragment.str(), u"categories with FreeOption")
