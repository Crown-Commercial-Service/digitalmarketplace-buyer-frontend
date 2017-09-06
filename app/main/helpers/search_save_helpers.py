from werkzeug.datastructures import MultiDict
from flask import url_for

from app.main.helpers.framework_helpers import get_lots_by_slug

from app.main.presenters.search_presenters import filters_for_lot
from app.main.presenters.search_summary import SearchSummary
from app.main.helpers.search_helpers import clean_request_args
from ..helpers.shared_helpers import construct_url_from_base_and_params

from app import search_api_client, content_loader
from .search_helpers import ungroup_request_filters


class SearchMeta(object):
    def __init__(self, search_api_url, frameworks_by_slug):
        # Get core data
        self.framework_slug = search_api_client.get_index_from_search_api_url(search_api_url)
        framework = frameworks_by_slug[self.framework_slug]
        content_manifest = content_loader.get_manifest(self.framework_slug, 'search_filters')
        lots_by_slug = get_lots_by_slug(framework)

        # We need to get buyer-frontend query params from our saved search API URL.
        search_query_params = search_api_client.get_frontend_params_from_search_api_url(search_api_url)
        search_query_params = ungroup_request_filters(search_query_params, content_manifest)
        search_query_params_multidict = MultiDict(search_query_params)

        current_lot_slug = search_query_params_multidict.get('lot', None)
        filters = filters_for_lot(current_lot_slug, content_manifest, all_lots=framework['lots'])
        clean_request_query_params = clean_request_args(search_query_params_multidict, filters.values(), lots_by_slug)

        # Now build the buyer-frontend URL representing the saved Search API URL
        self.url = construct_url_from_base_and_params(url_for('main.search_services'), search_query_params)

        # Get the saved Search API URL result set and build the search summary.
        search_api_response = search_api_client._get(search_api_url)
        self.search_summary = SearchSummary(
            search_api_response['meta']['total'],
            clean_request_query_params.copy(),
            filters.values(),
            lots_by_slug
        )
