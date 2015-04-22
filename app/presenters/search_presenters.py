class SearchFilters(object):
    """Provides access to the filters for a search based on request parameters
    """

    @staticmethod
    def get_filters_from_boolean_question(question):
        # boolean questions have no options as 'Yes' or 'No' is
        # implied
        return {
            'label': question['question'],
            'name': question['id'],
            'id': question['id']
        }

    @staticmethod
    def get_filters_from_question_with_options(question):
        filter_group = []
        for index, option in enumerate(question['options']):
            filter_group.append({
                'label': option['label'],
                'name': question['id'] + '[]',
                'id': '%s-%s' % (question['id'], str(index))
            })
        return filter_group

    @staticmethod
    def get_filter_groups_from_questions(question_sections):
        filter_groups = []
        get_filter_for = {
            'boolean': SearchFilters.get_filters_from_boolean_question,
            'options': SearchFilters.get_filters_from_question_with_options
        }
        for section in question_sections:
            filter_group = {
                'label': section['name'],
                'depends_on_lots': section['depends_on_lots'],
                'filters': []
            }
            for question in section['questions']:
                questionType = question['type']
                if (questionType == 'boolean') or (questionType == 'text'):
                    filter_group['filters'].append(get_filter_for['boolean'](
                        question
                    ))
                else:
                    # if the 1st question has options, they will become the
                    # filters and it's details will define the group
                    filter_group['filters'] = get_filter_for['options'](
                        question
                    )
                    break
            filter_groups.append(filter_group)
        return filter_groups

    def __init__(self, blueprint=False, request={}):
        self.filter_groups = blueprint.config['FILTER_GROUPS']
        self.request_filters = self.__get_filters_from_request(request)
        self.lot_filters = self.__get_lot_filters_from_request(request)
        self.__set_filter_states()

    def __get_lot_filters_from_request(self, request):
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
        if current_lot != None:
            lot_filters[lot_names.index(current_lot)]['isActive'] = True
        return lot_filters

    def __get_filters_from_request(self, request):
        """Returns the filters applied to a search from the request object"""

        # TODO: only use request arguments that map to recognised filters
        filters = {}
        for key in request.args:
            if key != 'q':
                arg_value = request.args.get(key, None)
                if arg_value != None:
                    filters[key] = arg_value
        return filters

    def __set_filter_states(self):
        """Sets a flag on each filter to mark it as set or not"""
        for filter_group in self.filter_groups:
            for filter in filter_group['filters']:
                if self.request_filters:
                    filter['isSet'] = (
                        filter['name'] in self.request_filters
                    )
