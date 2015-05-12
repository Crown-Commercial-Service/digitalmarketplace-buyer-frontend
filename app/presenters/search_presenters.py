import os
import re
import yaml
from flask import Markup
from werkzeug.datastructures import MultiDict
from ..helpers.questions import QuestionsLoader


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
                'id': '%s-%s' % (filter_name, filter_id),
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
        g6_questions = QuestionsLoader(
            manifest=manifest,
            questions_dir=questions_dir
        )

        def add_filters_for_question(question, filters):
            questions_with_options = [
                'radios',
                'checkboxes'
            ]
            # if the 1st question has options, they will become the
            # filters and it's details will define the group
            if question['type'] in questions_with_options:
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

    def __init__(self, blueprint=False, request={}):
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
                return '/search'
            else:
                return '/search?' + '&'.join(params)

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

        # TODO: only use request arguments that map to recognised filters
        filters = MultiDict(request.args.copy())
        filters.poplist('q')
        return filters

    def _set_filter_states(self):
        """Sets a flag on each filter to mark it as set or not"""
        for filter_group in self.filter_groups:
            for filter in filter_group['filters']:
                if self.request_filters:
                    filter['isSet'] = False
                    param_values = self.request_filters.getlist(
                        filter['name'],
                        type=str
                    )
                    if len(param_values) > 0:
                        filter['isSet'] = (
                            filter['value'] in param_values
                        )


class SearchResults(object):
    """Provides access to the search results information"""

    @staticmethod
    def get_search_summary(results_total, request_filters, filter_groups):
        return SearchSummary(results_total, request_filters, filter_groups)

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

    def __init__(self, results_total, request_filters, filter_groups):
        self.filters = self._group_request_filters(
                request_filters,
                filter_groups
            )
        print "self.filters:"
        print self.filters
        template = u"{} found"
        if int(results_total) < 2:
            self.total = '1'
            self.sentence = Markup(template.format(u"result"))
        else:
            self.total = results_total
            self.sentence = Markup(template.format(u"result"))

    def _group_request_filters(self, request_filters, filter_groups):
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

        groups = {}
        for filter_mapping in request_filters.lists():
            filter, values = filter_mapping
            if _is_option(values):
                group_name = _get_group_label_for_option(filter)
                _add_filter_to_group(group_name, filter)
            else: # filter is a group whose values are the options
                group_name =_get_group_label_for_option(filter)
                groups[group_name] = [
                    _get_label_for_string_option(value) for value in values]
        return groups

    def _get_search_summary_rules(self):
        manifest_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'helpers',
            'search_summary_manifest.yml'
        )

        with open(manifest_path, 'r') as file:
            summary_rules = yaml.load(file)
        return { rule['id']: rule for rule in summary_rules }

    def _join_group_filters(self, filters, conjunction, rules=None):

        def _filter_with_rules(filter):
            if rules is None:
                return filter
            if rules['id'] == filter:
                return '{} {}'.format(rules['preposition'], filter)
            # if no rules found
            return unicode(filter)

        filters_string = u''
        number_of_filters = len(filters)
        last_index = number_of_filters - 1
        if number_of_filters == 1:
            return u' {}'.format(_filter_with_rules(filters[0]))
        for index, filter in enumerate(filters):
            if index == last_index:
                filters_string += u'{} {}'.format(
                    conjunction, _filter_with_rules(filter))
            else:
                filters_string += u', ' + _filter_with_rules(filter)
        print "group filters:'{}".format(filters_string)
        return u' {}'.format(filters_string)

    def _get_search_summary(self, total):

        def _get_summary_section(section_rules, section_filters):

            def _format_piece(rule):
                if rule is not None:
                    return u' ' + rule
                else:
                    return u''

            section_string = u''
            for rule in ['labelPreposition', 'label', 'filtersPreposition']:
                print "Adding rule value:'{}'".format(
                    _format_piece(section_rules[rule]))
                section_string = u'{}{}'.format(
                    section_string, _format_piece(section_rules[rule]))
            print "Section string before adding filters:'{}'"\
                .format(section_string)
            section_string = u'{}{}'.format(
                section_string, self._join_group_filters(
                    section_filters,
                    section_rules['conjunction'], section_rules))
            print "Section string after adding filters:'{}'"\
                .format(section_string)
            return section_string

        def _get_summary_string_preposition():
            if total > 0:
                return u'{} services found'.format(unicode(total))
            else:
                return u'{} service found'.format(unicode(total))

        def _get_summary_data_from_request_filters(request_filters):
            summary_data = {}
            print "params:"
            print ""
            for param in request_filters.iterlists():
                print param
                param_key = param[0]
                section = self._get_group_name_from_filter_id(param_key)
                if section is not False:
                    print "Adding summary data for the '{}' section"\
                        .format(section)
                    param_values = [
                        self._get_filter_name_from_param(
                            param_key, value) for value in param[1]]
                    summary_data[section] = {
                        'id': section,
                        'filters': param_values
                    }
            return summary_data

        summary_rules = self._get_search_summary_rules()
        summary_preposition = _get_summary_string_preposition()
        summary_data = _get_summary_data_from_request_filters(
            self.request_filters)

        print "summary_rules:"
        print summary_rules
        print ""
        print "summary_data:"
        print summary_data
        print ""

        # turn summary data into a summary string
        summary_string = summary_preposition
        for group_rules in summary_rules:
            if group_rules['id'] in summary_data:
                print 'Adding section for {}'.format(group_rules['id'])
                u'{}{}'.format(
                    summary_string, _get_summary_section(
                        group_rules,
                        summary_data[group_rules['id']]['filters']))
        print "summary_string:"
        print summary_string
        return ''

