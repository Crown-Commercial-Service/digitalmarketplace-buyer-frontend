from flask import Markup


class SearchResults(object):
    """Provides access to the search results information"""

    def __init__(self, response, lots_by_slug):
        self.search_results = response['documents']
        self._lots = lots_by_slug
        self._annotate()
        self.total = response['meta']['total']
        if 'page' in response['meta']['query']:
            self.page = response['meta']['query']['page']

    def _annotate(self):
        for document in self.search_results:
            self._replace_lot(document)
            self._add_highlighting(document)

    def _replace_lot(self, document):
        # replace lot slug with reference to dict containing all the relevant lot data
        document['lot'] = self._lots.get(document['lot'])

    def _add_highlighting(self, document):
        if 'highlight' in document:
            for highlighted_field in ['serviceSummary', 'serviceDescription']:
                if highlighted_field in document['highlight']:
                    document[highlighted_field] = Markup(
                        ''.join(document['highlight'][highlighted_field])
                    )


class AggregationResults(object):
    """Provides access to the aggregation results information"""

    def __init__(self, response):
        self.results = response['aggregations']
        self.total = response['meta']['total']
        if 'page' in response['meta']['query']:
            self.page = response['meta']['query']['page']
