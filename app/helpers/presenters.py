class SearchResults(object):
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
        return self.results

    def get_total(self):
        return {'total': self.total}

    def get_results(self):
        return {
            'services': self.get_services(),
            'total': self.get_total()
        }

    def get_filter_groups(self, blueprint=False, request_filters={}):
        filter_groups = blueprint.config['SEARCH_FILTERS']
        if request_filters:
            filter_groups = self.__set_filter_states(filter_groups, request_filters)
        return filter_groups

    def __set_filter_states(self, filter_groups, request_filters):
        for filter_group in filter_groups:
            for filter in filter_group['filters']:
                filter['isSet'] = False
                if filter['name'] in request_filters:
                    filter['isSet'] = True

        return filter_groups

