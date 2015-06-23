import os
import re
import yaml
from flask import Markup
from werkzeug.datastructures import MultiDict
from dmutils.content_loader import ContentLoader
from ..helpers.shared_helpers import get_label_for_lot_param


class SearchFilters(object):
    """Provides access to the filters for a search based on request parameters
    """

    @staticmethod
    def get_current_lot(request):
        return request.args.get('lot', None)

    @staticmethod
    def get_filters_from_default_question(question):
        # boolean questions have no options as 'Yes' or 'No' is
        # implied
        return {
            'label': question['question'],
            'name': question['id'],
            'id': question['id'],
            'value': 'true',
            'lots': [lot.strip() for lot in (
                question['dependsOnLots'].lower().split(",")
            )]
        }

    @staticmethod
    def get_filters_from_question_with_options(question, index):
        filter_group = []

        if re.match('^serviceTypes(SCS|SaaS|IaaS)', question['id']):
            filter_name = 'serviceTypes'
        else:
            filter_name = question['id']
        for option in question['options']:
            filter_id = option['label'].lower().replace(' ', '-')
            filter = {
                'label': option['label'],
                'name': filter_name,
                'id': '{}-{}'.format(filter_name, filter_id),
                'value': option['label'].lower(),
                'lots': [lot.strip() for lot in (
                    question['dependsOnLots'].lower().split(",")
                )]
            }
            filter_group.append(filter)
            index = index + 1
        return filter_group

    @staticmethod
    def get_filter_groups_from_questions(manifest, questions_dir):
        filter_groups = []
        g6_questions = ContentLoader(
            manifest,
            questions_dir
        )

        def add_filters_for_question(question, filters):
            # if the 1st question has options, they will become the
            # filters and it's label will become the group label
            if question['type'] in ['radios', 'checkboxes']:
                filters += \
                    SearchFilters.get_filters_from_question_with_options(
                        question,
                        len(filters)
                    )
            else:
                filters.append(
                    SearchFilters.get_filters_from_default_question(
                        question
                    )
                )
            return filters

        for section in g6_questions.sections:
            filter_group = {
                'label': section['name'],
                'depends_on_lots': section['depends_on_lots'],
                'filters': []
            }
            for question in section['questions']:
                filter_group['filters'] = add_filters_for_question(
                    question=question, filters=filter_group['filters']
                )
            filter_groups.append(filter_group)
        return filter_groups

    def __init__(self, blueprint=None, request=None):
        self.filter_groups = blueprint.config['FILTER_GROUPS']
        self.request_filters = self._get_filters_from_request(request)
        self.lot_filters = self._get_lot_filters_from_request(request)
        self._sift_filters_based_on_lot(request.args.get('lot', 'all'))
        self._set_filter_states()

    def _sift_filters_based_on_lot(self, lot):
        sifted_groups = []
        lots = ['saas', 'paas', 'iaas', 'scs']

        def _filter_is_in_all_lots(filter):
            for lot in lots:
                if lot not in filter['lots']:
                    return False
            return True

        for filter_group in self.filter_groups:
            sifted_group = filter_group.copy()
            sifted_group['filters'] = []
            for index, filter in enumerate(filter_group['filters']):
                if (lot == 'all'):
                    if _filter_is_in_all_lots(filter):
                        sifted_group['filters'].append(filter)
                else:  # lot is singular
                    if lot in filter['lots']:
                        sifted_group['filters'].append(filter)
            if len(sifted_group['filters']) > 0:
                sifted_groups.append(sifted_group)
        self.filter_groups = sifted_groups

    def _get_lot_filters_from_request(self, request):
        """Returns data to construct lot filters from"""

        def _get_url(keywords=None, lot=None):
            params = []
            if keywords is not None:
                params.append('q=' + keywords)
            if lot is not None:
                params.append('lot=' + lot)
            if len(params) == 0:
                return '/g-cloud/search'
            else:
                return '/g-cloud/search?' + '&'.join(params)

        lot_names = ['all', 'saas', 'paas', 'iaas', 'scs']
        current_lot = request.args.get('lot', 'all')
        keywords = request.args.get('q', None)
        lot_filters = [
            {
                'isActive': False,
                'label': u'All categories',
                'url': _get_url(keywords=keywords)
            },
            {
                'isActive': False,
                'label': u'Software as a Service',
                'url': _get_url(keywords=keywords, lot='saas')
            },
            {
                'isActive': False,
                'label': u'Platform as a Service',
                'url': _get_url(keywords=keywords, lot='paas')
            },
            {
                'isActive': False,
                'label': u'Infrastructure as a Service',
                'url': _get_url(keywords=keywords, lot='iaas')
            },
            {
                'isActive': False,
                'label': u'Specialist Cloud Services',
                'url': _get_url(keywords=keywords, lot='scs')
            }
        ]
        if current_lot is not None:
            lot_filters[lot_names.index(current_lot)]['isActive'] = True
        return lot_filters

    def _get_filters_from_request(self, request):
        """Returns the filters applied to a search from the request object"""

        filters = MultiDict(request.args.copy())
        filters.poplist('q')
        filters.poplist('lot')
        return filters

    def _set_filter_states(self):
        """Sets a flag on each filter to mark it as set or not"""
        for filter_group in self.filter_groups:
            for filter in filter_group['filters']:
                filter['checked'] = False
                param_values = self.request_filters.getlist(
                    filter['name'],
                    type=str
                )
                if len(param_values) > 0:
                    filter['checked'] = (
                        filter['value'] in param_values
                    )


class SearchResults(object):
    """Provides access to the search results information"""

    @staticmethod
    def get_search_summary(results_total, request_args, filter_groups):
        return SearchSummary(results_total, request_args, filter_groups)

    def _add_highlighting(self):
        for index, service in enumerate(self.search_results):
            if 'highlight' in service:
                if 'serviceSummary' in service['highlight']:
                    self.search_results[index]['serviceSummary'] = Markup(
                        ''.join(service['highlight']['serviceSummary'])
                    )

    def __init__(self, response):
        self.search_results = response['services']
        self._add_highlighting()
        self.total = response['meta']['total']
        if 'page' in response['meta']['query']:
            self.page = response['meta']['query']['page']


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

    def __init__(self, results_total, request_args, filter_groups):
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
        keywords = request_args.get('q', '', type=str)
        lot = u"{}{}{}".format(
            SearchSummary.LOT_PRE_TAG,
            get_label_for_lot_param(request_args.get('lot', 'all', type=str)),
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

    def get_starting_sentence(self):
        return u"{}{}{} {}".format(
            self.COUNT_PRE_TAG,
            self.count,
            self.COUNT_POST_TAG,
            self.sentence
        )

    def _group_request_filters(self, request_args, filter_groups):
        """arranges the filters from the request into filter groups"""

        def _is_option(values):
            return (len(values) == 1) and (values[0] == u'true')

        def _get_group_label_for_option(option):
            for group in filter_groups:
                for filter in group['filters']:
                    if filter['name'] == option:
                        return group['label']

        def _get_label_for_string_option(option):
            for group in filter_groups:
                for filter in group['filters']:
                    if filter['value'] == option:
                        return filter['label']

        def _get_label_for_boolean_option(option):
            for group in filter_groups:
                for filter in group['filters']:
                    if filter['name'] == option:
                        return filter['label']

        def _add_filter_to_group(group_name, filter):
            option_label = _get_label_for_boolean_option(filter)
            if group_name not in groups:
                groups[group_name] = [option_label]
            else:
                groups[group_name].append(option_label)

        def _sort_groups(groups):
            sorted_groups = []
            filter_group_order = [group['label'] for group in filter_groups]
            for group in filter_group_order:
                if group in groups:
                    sorted_groups.append((group, groups[group]))
            return sorted_groups

        groups = {}
        for filter_mapping in request_args.lists():
            filter, values = filter_mapping
            if filter == 'lot' or filter == 'q':
                continue
            if _is_option(values):
                group_name = _get_group_label_for_option(filter)
                _add_filter_to_group(group_name, filter)
            else:  # filter is a group whose values are the options
                group_name = _get_group_label_for_option(filter)
                groups[group_name] = [
                    _get_label_for_string_option(value) for value in values]
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
            summary_rules = yaml.load(file)
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
            except:
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
                if filter in self.rules.filter_rules_ids:
                    filter_string = _mark_up_filter(filter)
                    filter_string = self.rules.add_filter_preposition(
                        filter_id=filter, filter_string=filter_string)
                    processed_filters.append(filter_string)
        return processed_filters
