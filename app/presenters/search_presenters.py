class SearchFilters(object):
    """Provides access to the filters for a search based on request parameters
    """

    def __init__(self, blueprint=False, request={}):
        self.filter_groups = blueprint.config['SEARCH_FILTERS']
        self.request_filters = self.__get_filters_from_request(request)
        if self.request_filters:
            self.__set_filter_states()

    def get_filter_groups(self):
        """Returns the filters for the search in their groups"""

        return self.filter_groups

    def get_request_filters(self):
        """Returns the filters for the search from the request parameters"""

        return self.request_filters

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
                filter['isSet'] = False
                if filter['name'] in self.request_filters:
                    filter['isSet'] = True
