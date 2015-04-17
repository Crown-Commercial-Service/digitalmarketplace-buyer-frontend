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
        self.__set_filter_states()

    def __get_filters_from_request(self, request):
        """Returns the filters applied to a search from the request object"""

        # TODO: only use request arguments that map to recognised filters
        filters = {}
        for key in request.args:
            if key != 'q':
                filters[key] = request.args[key]
        return filters

    def __set_filter_states(self):
        """Sets a flag on each filter to mark it as set or not"""
        for filter_group in self.filter_groups:
            for filter in filter_group['filters']:
                if self.request_filters:
                    filter['isSet'] = (
                        filter['name'] in self.request_filters
                    )
