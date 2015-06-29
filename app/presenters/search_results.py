from flask import Markup


class SearchResults(object):
    """Provides access to the search results information"""

    def __init__(self, response):
        self.search_results = response['services']
        self._add_highlighting()
        self.total = response['meta']['total']
        if 'page' in response['meta']['query']:
            self.page = response['meta']['query']['page']

    def _add_highlighting(self):
        for index, service in enumerate(self.search_results):
            if 'highlight' in service:
                if 'serviceSummary' in service['highlight']:
                    self.search_results[index]['serviceSummary'] = Markup(
                        ''.join(service['highlight']['serviceSummary'])
                    )
