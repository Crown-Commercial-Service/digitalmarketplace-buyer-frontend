from flask import Markup

from .search_summary import SearchSummary


class SearchResults(object):
    """Provides access to the search results information"""

    def __init__(self, response):
        self.search_results = response['services']
        self._add_highlighting()
        self.total = response['meta']['total']
        if 'page' in response['meta']['query']:
            self.page = response['meta']['query']['page']

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
