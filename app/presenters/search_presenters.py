import os
import json

class SearchResults(object):
    """Provides access to elasticsearch search results formatted as view data"""

    def __init__(self, results_dict):
        self.lots = {
            'IaaS': 'Infrastructure as a Service',
            'SaaS': 'Software as a Service',
            'PaaS': 'Platform as a Service',
            'SCS': 'Specialist Cloud Services'
        }
        self.total = results_dict['hits']['total']
        self.results = []
        results = results_dict['hits']['hits']
        for raw_result in results:
            result = {}
            for field in raw_result['fields']:
              result[field] = raw_result['fields'][field][0]

            result['lot'] = self.lots[result['lot']]
            self.results.append(result)

    def get_services(self):
        """Returns the services from the search results"""

        return self.results

    def get_total(self):
        """Returns the total number of services in the search results"""

        return { 'total' : self.total }

    def get_results(self):
        """Returns an object containing all services in the search results and their total number"""

        return {
            'services' : self.get_services(),
            'total' : self.get_total()
        }

class SearchFilters(object):
    """Provides access to the filters for a search based on request parameters"""

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


