import json
import os

from mock import Mock
from werkzeug.datastructures import MultiDict

from app import content_loader
from app.main.presenters.search_presenters import filters_for_lot
from app.main.presenters.search_results import SearchResults
from app.main.presenters.search_summary import SearchSummary, \
    SummaryRules, SummaryFragment
from app.main.helpers import framework_helpers
from ...helpers import BaseApplicationTest

filter_groups = None
g9_filter_groups = None


def setup_module(module):
    # TODO we should have example subset search_filter manifests as fixtures
    content_loader.load_manifest('g-cloud-6', 'services', 'services_search_filters')
    content_loader.load_manifest('g-cloud-9', 'services', 'services_search_filters')

    module.filter_groups = filters_for_lot(
        "saas",
        content_loader.get_manifest('g-cloud-6', 'services_search_filters')
    ).values()

    module.g9_filter_groups = filters_for_lot(
        'cloud-software',
        content_loader.get_manifest('g-cloud-9', 'services_search_filters')
    ).values()


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


class TestSearchSummary(BaseApplicationTest):
    def setup_method(self, method):
        super().setup_method(method)

        self._lots_by_slug = framework_helpers.get_lots_by_slug(
            self._get_framework_fixture_data('g-cloud-6')['frameworks']
        )

        self._g9_lots_by_slug = framework_helpers.get_lots_by_slug(
            self._get_framework_fixture_data('g-cloud-9')['frameworks']
        )

        self.fixture = _get_fixture_data()
        self.search_results = SearchResults(self.fixture, self._lots_by_slug)
        self.request_args = MultiDict((
            ('lot', 'saas'),
            ('q', 'email'),
        ))

    def teardown_method(self, method):
        super().teardown_method(method)

    def test_write_list_as_sentence_with_one_item(self):
        assert SearchSummary.write_list_as_sentence(['item1'], 'and') == u"item1"

    def test_write_list_as_sentence_with_two_items(self):
        assert SearchSummary.write_list_as_sentence(['item1', 'item2'], 'and') == u"item1 and item2"

    def test_write_list_as_sentence_with_three_items(self):
        assert SearchSummary.write_list_as_sentence(['item1', 'item2', 'item3'], 'and') == u"item1, item2 and item3"

    def test_write_parts_as_sentence_with_first_part_None(self):
        assert SearchSummary.write_parts_as_sentence([None, u"Hour"]) == u"Hour"

    def test_write_parts_as_sentence_with_second_part_None(self):
        assert SearchSummary.write_parts_as_sentence([u"Hour", None]) == u"Hour"

    def test_write_parts_as_sentence_with_both_parts_not_None(self):
        assert SearchSummary.write_parts_as_sentence([u"an", u"Hour"]) == u"an Hour"

    def test_search_summary_works_with_keywords(self):
        search_summary = SearchSummary('1', self.request_args, filter_groups, self._lots_by_slug)
        assert search_summary.count == '1'
        assert search_summary.sentence == (u"result found containing <strong>email</strong> in "
                                           "<strong>Software as a Service</strong>")
        assert len(search_summary.filters_fragments) == 0

    def test_search_summary_works_with_blank_keywords(self):
        self.request_args.setlist('q', [''])
        search_summary = SearchSummary('1', self.request_args, filter_groups, self._lots_by_slug)
        assert search_summary.count == '1'
        assert search_summary.sentence == u"result found in <strong>Software as a Service</strong>"
        assert len(search_summary.filters_fragments) == 0

    def test_search_summary_works_with_a_different_lot(self):
        self.request_args.setlist('lot', ['iaas'])
        search_summary = SearchSummary('1', self.request_args, filter_groups, self._lots_by_slug)
        assert search_summary.count == '1'
        assert search_summary.sentence == (
            u"result found containing <strong>email</strong> in <strong>Infrastructure as a Service</strong>"
        )
        assert len(search_summary.filters_fragments) == 0

    def test_search_summary_works_with_no_results(self):
        search_summary = SearchSummary('0', self.request_args, filter_groups, self._lots_by_slug)
        assert search_summary.count == '0'
        assert search_summary.sentence == (
            u"results found containing <strong>email</strong> in <strong>Software as a Service</strong>"
        )
        assert len(search_summary.filters_fragments) == 0

    def test_search_summary_works_with_single_result(self):
        search_summary = SearchSummary(1, self.request_args, filter_groups, self._lots_by_slug)
        assert search_summary.count == '1'
        assert search_summary.sentence == (
            u"result found containing <strong>email</strong> in <strong>Software as a Service</strong>"
        )
        assert len(search_summary.filters_fragments) == 0

    def test_search_summary_works_with_multiple_results(self):
        search_summary = SearchSummary('9', self.request_args, filter_groups, self._lots_by_slug)
        assert search_summary.count == '9'
        assert search_summary.sentence == (
            u"results found containing <strong>email</strong> in <strong>Software as a Service</strong>"
        )
        assert len(search_summary.filters_fragments) == 0

    def test_search_summary_with_a_single_filter_group(self):
        self.request_args.setlist('serviceTypes', ['collaboration'])
        search_summary = SearchSummary('9', self.request_args, filter_groups, self._lots_by_slug)
        assert search_summary.count == '9'
        assert search_summary.sentence == (
            u"results found containing <strong>email</strong> in <strong>Software as a Service</strong>"
        )
        assert len(search_summary.filters_fragments) == 1

    def test_search_summary_with_two_filter_groups(self):
        self.request_args.setlist(
            'serviceTypes',
            ['collaboration', 'energy and environment']
        )
        self.request_args.setlist(
            'datacentreTier',
            ['tia-942 tier 1', 'uptime institute tier 1']
        )
        search_summary = SearchSummary('9', self.request_args, filter_groups, self._lots_by_slug)
        assert search_summary.count == '9'
        assert search_summary.sentence == (
            u"results found containing <strong>email</strong> in <strong>Software as a Service</strong>"
        )
        assert len(search_summary.filters_fragments) == 2

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
        search_summary = SearchSummary('9', self.request_args, filter_groups, self._lots_by_slug)
        assert search_summary.count == '9'
        assert search_summary.sentence == (
            u"results found containing <strong>email</strong> in <strong>Software as a Service</strong>"
        )
        assert len(search_summary.filters_fragments) == 3

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
        search_summary = SearchSummary('9', self.request_args, filter_groups, self._lots_by_slug)
        correct_order = [
            'Categories', 'Pricing', 'Datacentre tier'
        ]
        order_of_groups_of_filters = [
            fragment.id for fragment in search_summary.filters_fragments]
        assert order_of_groups_of_filters == correct_order

    def test_mix_boolean_and_radio_filters(self):
        """
        Test for a bug where a radio button's filter summary would replace (rather than add
        to) the summary for a boolean, in the same filter group.
        """
        self.request_args.setlist(
            'phoneSupport',
            ['true']
        )
        self.request_args.setlist(
            'emailOrTicketingSupport',
            ['yes']
        )
        search_summary = SearchSummary('9', self.request_args, g9_filter_groups, self._g9_lots_by_slug)
        summary_markup = search_summary.markup()
        assert "email or online ticketing" in summary_markup
        assert "phone" in summary_markup

    def test_mixed_radios_with_identical_values(self):
        """
        Test for a bug where two radio buttons (from different questions, but in the same filter
        group) with the same value would overwrite each other's summary, rather than combine
        together correctly.
        """
        self.request_args.setlist(
            'webChatSupport',
            ['yes']
        )
        self.request_args.setlist(
            'emailOrTicketingSupport',
            ['yes']
        )
        search_summary = SearchSummary('9', self.request_args, g9_filter_groups, self._g9_lots_by_slug)
        summary_markup = search_summary.markup()
        assert "web chat" in summary_markup
        assert "email or online ticketing" in summary_markup

    def test_category_filters_are_available(self):
        self.request_args.setlist(
            'serviceCategories',
            ['accounting and finance']
        )
        search_summary = SearchSummary('9', self.request_args, g9_filter_groups, self._g9_lots_by_slug)
        summary_markup = search_summary.markup()
        assert "category <strong>Accounting and finance</strong>" in summary_markup

    def test_subcategory_filters_are_available(self):
        self.request_args.setlist(
            'serviceCategories',
            ['analytics']
        )
        search_summary = SearchSummary('9', self.request_args, g9_filter_groups, self._g9_lots_by_slug)
        summary_markup = search_summary.markup()
        assert "category <strong>Analytics</strong>" in summary_markup

    def test_each_filter(self):
        """
        Test each filter individually adds a single text string to the summary text
        """
        for lot in self._g9_lots_by_slug:
            self.request_args['lot'] = lot
            for filter_group in g9_filter_groups:
                for f in filter_group['filters']:
                    request_args = self.request_args.copy()
                    request_args[f['name']] = f['value']
                    search_summary = SearchSummary('9', request_args, g9_filter_groups, self._g9_lots_by_slug)
                    summary_markup = search_summary.markup()
                    assert summary_markup.count("<strong>") == 3  # the keyword, the lot, and one filter

    def test_all_filters(self):
        """
        Incrementally add filters, so if there's one that doesn't seem to work in conjunction with the
        others, we find it.
        """
        for lot in self._g9_lots_by_slug:
            self.request_args['lot'] = lot
            filter_count = 0
            request_args = self.request_args.copy()  # reset all filters for a new lot
            for filter_group in g9_filter_groups:
                for f in filter_group['filters']:
                    request_args.add(f['name'], f['value'])
                    filter_count += 1

                    search_summary = SearchSummary('9', request_args, g9_filter_groups, self._g9_lots_by_slug)
                    summary_markup = search_summary.markup()
                    assert summary_markup.count("<strong>") == 2 + filter_count

    def test_get_starting_sentence_works(self):
        search_summary = SearchSummary('9', self.request_args, filter_groups, self._lots_by_slug)
        search_summary.count = '9'
        search_summary.COUNT_PRE_TAG = '<strong>'
        search_summary.COUNT_POST_TAG = '</strong>'
        search_summary.sentence = (
            u"results found containing <strong>email</strong>" +
            u" in <strong>Software as a Service</strong>")
        assert search_summary.get_starting_sentence() == (
            u"<strong>9</strong> results found containing "
            "<strong>email</strong> in <strong>Software as a Service</strong>"
        )

    def test_markup_method_works_with_no_fragments(self):
        def get_starting_sentence():
            return u"5 results found"

        search_summary = SearchSummary(9, self.request_args, filter_groups, self._lots_by_slug)
        search_summary.get_starting_sentence = get_starting_sentence
        search_summary.filters_fragments = []
        assert search_summary.markup() == u"5 results found"

    def test_markup_method_works_with_fragments(self):
        def get_starting_sentence():
            return u"5 results found"

        fragment = Mock(**{"str.return_value": u"with option1 and option2"})
        search_summary = SearchSummary(9, self.request_args, filter_groups, self._lots_by_slug)
        search_summary.get_starting_sentence = get_starting_sentence
        search_summary.filters_fragments = [fragment]
        assert search_summary.markup() == u"5 results found with option1 and option2"


class TestSummaryRules:
    def setup_method(self, method):
        if SummaryRules.loaded is False:
            SummaryRules.load_rules(manifest=os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                'app',
                'helpers',
                'search_summary_manifest.yml'
            ))

    def test_set_up_where_rules_do_not_exist(self):
        summary_rules = SummaryRules('Sites')
        assert not summary_rules.exist

    def test_set_up_where_rules_do_exist(self):
        summary_rules = SummaryRules('Categories')
        assert summary_rules.exist

    def test_get_method_works_for_key_with_value(self):
        summary_rules = SummaryRules('Categories')
        assert summary_rules.get('conjunction') == 'and'

    def test_get_method_works_for_empty_key(self):
        summary_rules = SummaryRules('Categories')
        assert summary_rules.get('filterRules') is None

    def test_filter_rules_ids_are_set_if_filterRules_exist(self):
        summary_rules = SummaryRules('Minimum contract period')
        assert hasattr(summary_rules, "filter_rules_ids")
        assert summary_rules.filter_rules_ids == ['Hour', 'Day', 'Month', 'Year', 'Other']

    def test_add_preposition_with_a_filter_that_has_one(self):
        summary_rules = SummaryRules('Minimum contract period')
        assert u"an <strong>Hour</strong>" == summary_rules.add_filter_preposition(
            filter_id='Hour',
            filter_string=u"<strong>Hour</strong>",
        )

    def test_add_preposition_with_a_filter_without_any_for_its_group(self):
        summary_rules = SummaryRules('Pricing')
        assert summary_rules.add_filter_preposition(
            filter_id='Trial option',
            filter_string=u"<strong>Trial option</strong>",
        ) == u"<strong>Trial option</strong>"

    def test_add_preposition_with_a_filter_without_in_a_group_with_some(self):
        SummaryRules._rules['Minimum contract period']['filterRules'].remove({
            'preposition': 'an',
            'id': 'Hour'
        })
        summary_rules = SummaryRules('Minimum contract period')
        assert summary_rules.add_filter_preposition(
            filter_id='Hour',
            filter_string=u"<strong>Hour</strong>",
        ) == u"<strong>Hour</strong>"
        # Make SummaryRules to reload its data
        SummaryRules.loaded = False


class TestSummaryFragment:
    def _get_mock(self, key):
        return self.rules[key]

    def setup_method(self, method):
        self.rules_instance = SummaryRules('')
        self.rules_instance_mock = Mock()
        self.rules = {
            'id': 'Datacentre tier',
            'labelPreposition': None,
            'label': None,
            'filtersPreposition': None,
            'filterRules': None,
            'conjunction': 'or',
        }
        self.rules_instance_mock.get = self._get_mock

    def test_fragment_has_correct_form_for_a_single_filter(self):
        id = 'Datacentre tier'
        filters = ['TIA-942 Tier 1']
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        assert hasattr(summary_fragment, 'form')
        assert summary_fragment.form == 'singular'

    def test_fragment_has_correct_form_for_multiple_filters(self):
        id = 'Datacentre tier'
        filters = ['TIA-942 Tier 1', 'uptime institute tier 1']
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        assert hasattr(summary_fragment, 'form')
        assert summary_fragment.form == 'plural'

    def test_fragment_with_no_label_and_single_filter(self):
        id = 'Datacentre tier'
        filters = ['TIA-942 Tier 1']
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        assert summary_fragment.str() == u"<strong>TIA-942 Tier 1</strong>"

    def test_fragment_with_label_and_one_filter(self):
        id = 'Datacentre tier'
        filters = ['TIA-942 Tier 1']
        self.rules['label'] = {
            'singular': 'datacentre tier',
            'plural': 'datacentre tier'
        }
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        assert summary_fragment.str() == u"datacentre tier <strong>TIA-942 Tier 1</strong>"

    def test_fragment_with_label_and_two_filters(self):
        id = 'Datacentre tier'
        filters = ['TIA-942 Tier 1', 'uptime institute tier 1']
        self.rules['label'] = {
            'singular': 'datacentre tier',
            'plural': 'datacentre tiers'
        }
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        assert summary_fragment.str() == (
            u"datacentre tiers <strong>TIA-942 Tier 1</strong> or "
            "<strong>uptime institute tier 1</strong>"
        )

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
        assert summary_fragment.str() == (
            u"datacentre tiers <strong>TIA-942 Tier 1</strong>, <strong>uptime institute tier 1</strong> "
            "or <strong>uptime institute tier 2</strong>"
        )

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
        assert summary_fragment.str() == (
            u"datacentre tiers with a <strong>TIA-942 Tier 1</strong>"
            u", met with a <strong>uptime institute tier 1</strong>"
            u" or aligned with <strong>uptime institute tier 2</strong>"
        )

        # now check we can still create a summary if some of the filters are missing from the filter-rules list
        self.rules_instance_mock.filter_rules_ids = ['uptime institute tier 1']
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        assert summary_fragment.str() == (
            u"datacentre tiers <strong>TIA-942 Tier 1</strong>"
            u", met with a <strong>uptime institute tier 1</strong>"
            u" or <strong>uptime institute tier 2</strong>"
        )

    def test_str_method_works(self):
        id = 'Datacentre tier'
        filters = ['TIA-942 Tier 1']
        summary_fragment = SummaryFragment(
            id, filters, self.rules_instance_mock)
        summary_fragment.label_string = u"categories"
        summary_fragment.filters = [u"FreeOption"]
        self.rules['filtersPreposition'] = 'with'
        assert summary_fragment.str() == u"categories with FreeOption"
