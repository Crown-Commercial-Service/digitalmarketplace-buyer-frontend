from collections import defaultdict
import os
import yaml

from flask import Markup, escape
from lxml.html import document_fromstring


class SearchSummary(object):
    """Provides a paragraph summarising the search performed and results"""

    COUNT_PRE_TAG = '<span class="search-summary-count">'
    COUNT_POST_TAG = '</span>'
    KEYWORDS_PRE_TAG = '<em>'
    KEYWORDS_POST_TAG = '</em>'
    LOT_PRE_TAG = '<em>'
    LOT_POST_TAG = '</em>'

    @staticmethod
    def write_parts_as_sentence(parts):
        sentence = [part for part in parts if part is not None]
        if len(sentence) > 0:
            return u" ".join(sentence)

    @staticmethod
    def write_list_as_sentence(input_list, final_conjunction):
        if len(input_list) == 1:
            return u"{}".format(input_list[0])
        else:
            start = input_list[0:-1]
            end = input_list[-1]
            formatted_conjunction = " {} ".format(final_conjunction)
            return formatted_conjunction.join([u', '.join(start), end])

    def __init__(self, results_total, request_args, filter_groups, lots_by_slug):
        self._lots_by_slug = lots_by_slug
        self._set_initial_sentence(results_total, request_args)

        self.filter_groups = self._group_request_filters(
            request_args,
            filter_groups
        )
        self.filters_fragments = []
        SummaryRules.load_rules()
        for group in self.filter_groups:
            group_id = group[0]
            filters = group[1]
            group_rules = SummaryRules(group_id)
            if group_rules.exist is True:
                self.filters_fragments.append(
                    SummaryFragment(
                        group_id=group_id,
                        filters=filters,
                        rules=group_rules)
                )

    def _set_initial_sentence(self, results_total, request_args):
        keywords = escape(request_args.get('q', ''))
        lot_label = (self._lots_by_slug.get(request_args.get('lot'), {}).get('name')
                     or 'All categories')
        lot = u"{}{}{}".format(
            SearchSummary.LOT_PRE_TAG,
            lot_label,
            SearchSummary.LOT_POST_TAG
        )
        if int(results_total) == 1:
            self.count = '1'
            count_string = 'result found'
        else:
            self.count = str(results_total)
            count_string = u"results found"
        if keywords != '':
            self.sentence = u"{} containing {}{}{} in {}".format(
                count_string,
                SearchSummary.KEYWORDS_PRE_TAG,
                keywords,
                SearchSummary.KEYWORDS_POST_TAG,
                lot)
        else:
            self.sentence = u"{} in {}".format(count_string, lot)

    def markup(self):

        def _get_fragment_string(fragment):
            return fragment.str()

        parts = [self.get_starting_sentence()]
        if len(self.filters_fragments) > 0:
            fragment_strings = list(
                map(_get_fragment_string, self.filters_fragments))
            parts.append(SearchSummary.write_list_as_sentence(
                fragment_strings, u"and"))

        return Markup(u" ".join(parts))

    def text_content(self):
        return document_fromstring(self.markup()).text_content()

    def get_starting_sentence(self):
        return u"{}{}{} {}".format(
            self.COUNT_PRE_TAG,
            self.count,
            self.COUNT_POST_TAG,
            self.sentence
        )

    def _group_request_filters(self, request_args, filter_groups):
        """arranges the filters from the request into filter groups"""

        def _insert_filters(target_dict, filters, label):
            for f in filters:
                if f.get('children'):
                    _insert_filters(target_dict, f.get('children'), label)

                target_dict[(f['name'], f['value'])] = (f, label)

        def _sort_groups(groups):
            sorted_groups = []
            filter_group_order = [group['label'] for group in filter_groups]
            for group in filter_group_order:
                if group in groups:
                    sorted_groups.append((group, groups[group]))
            return sorted_groups

        # build map from key/value pair to the relevant filter
        # ideally this would be in the filter_groups data structure already, but it isn't
        all_filters_by_kv = dict()

        for filter_group in filter_groups:
            _insert_filters(all_filters_by_kv, filter_group['filters'], filter_group['label'])

        groups = defaultdict(list)
        for filter_name, filter_values in request_args.lists():
            if filter_name in ('lot', 'q', 'page'):
                continue

            for filter_value in filter_values:
                filter_instance, filter_group_label = all_filters_by_kv[(filter_name, filter_value)]
                groups[filter_group_label].append(filter_instance['label'])

        return _sort_groups(groups)


class SummaryRules(object):
    """Provides access to the rules for a search summary fragment"""

    _rules = {}
    loaded = False

    @staticmethod
    def load_rules(manifest=os.path.join(
        os.path.dirname(__file__),
        '..',
        'helpers',
        'search_summary_manifest.yml'
    )):

        with open(manifest, 'r') as file:
            summary_rules = yaml.safe_load(file)
        SummaryRules._rules = {rule['id']: rule for rule in summary_rules}
        SummaryRules.loaded = True

    def __init__(self, group_id):
        self.exist = group_id in SummaryRules._rules
        if self.exist is True:
            self._rules = SummaryRules._rules[group_id]
            if self.get('filterRules') is not None:
                self.filter_rules_ids = [
                    rule['id'] for rule in self._rules['filterRules']]

    def get(self, key):
        if key in self._rules:
            return self._rules[key]

    def add_filter_preposition(self, filter_id=None, filter_string=None):
        preposition = self._get_filter_preposition(filter_id)
        return SearchSummary.write_parts_as_sentence(
            [preposition, filter_string])

    def _get_filter_preposition(self, filter):
        if hasattr(self, 'filter_rules_ids'):
            try:
                index = self.filter_rules_ids.index(filter)
            except (AttributeError, TypeError, ValueError):
                return None
            return self._rules['filterRules'][index]['preposition']


class SummaryFragment(object):
    """Provides access to a search summary fragment"""

    PRE_TAG = u'<em>'
    POST_TAG = u'</em>'
    FINAL_CONJUNCTION = u'and'

    def __init__(self, group_id, filters, rules):
        self.id = group_id
        self.rules = rules
        self.form = 'singular'
        if len(filters) > 1:
            self.form = 'plural'
        self.filters = self._get_filters(filters)
        self.filters_preposition = self.rules.get('filtersPreposition')
        self.label_string = self._get_label()

    def str(self):
        filters_string = SearchSummary.write_list_as_sentence(
            self.filters, self.rules.get('conjunction')
        )
        return SearchSummary.write_parts_as_sentence([
            self.label_string,
            self.rules.get('filtersPreposition'),
            filters_string
        ])

    def _get_label(self):
        preposition = self.rules.get('labelPreposition')
        label = self.rules.get('label')
        if label is not None:
            return SearchSummary.write_parts_as_sentence(
                [preposition, label[self.form]])
        else:
            return SearchSummary.write_parts_as_sentence(
                [preposition, label])

    def _get_filters(self, filters):
        def _mark_up_filter(filter):
            return u"{}{}{}".format(
                SummaryFragment.PRE_TAG,
                filter,
                SummaryFragment.POST_TAG,
            )

        processed_filters = []
        if self.rules.get('filterRules') is None:
            processed_filters = [_mark_up_filter(filter) for filter in filters]
            return processed_filters
        else:
            for filter in filters:
                filter_string = _mark_up_filter(filter)
                if filter in self.rules.filter_rules_ids:
                    filter_string = self.rules.add_filter_preposition(
                        filter_id=filter, filter_string=filter_string)
                processed_filters.append(filter_string)

        return processed_filters
