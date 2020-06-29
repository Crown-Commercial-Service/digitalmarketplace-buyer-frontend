from enum import Enum

from flask import abort, current_app, url_for
from werkzeug.datastructures import MultiDict

from app import content_loader
from app.main.helpers.framework_helpers import get_lots_by_slug
from app.main.helpers.search_helpers import clean_request_args
from app.main.presenters.search_presenters import filters_for_lot
from app.main.presenters.search_summary import SearchSummary
from .search_helpers import ungroup_request_filters
from ..helpers.shared_helpers import construct_url_from_base_and_params


class SavedSearchStateEnum(Enum):
    NOT_LOCKED_STANDSTILL = 1
    NOT_LOCKED_POST_LIVE = 2
    LOCKED_STANDSTILL = 3
    LOCKED_POST_LIVE_DURING_INTERIM = 4
    LOCKED_POST_LIVE_POST_INTERIM = 5


class SearchMeta(object):
    def __init__(self, search_api_client, search_api_url, frameworks_by_slug, include_markup=False):
        # Get core data
        self.framework_slug = search_api_client.get_index_from_search_api_url(search_api_url)
        framework = frameworks_by_slug[self.framework_slug]
        content_manifest = content_loader.get_manifest(self.framework_slug, 'services_search_filters')
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

    @property
    def search_count(self):
        return int(self.search_summary.count)


def get_saved_search_banner_message_status(project, framework, following_framework):
    if following_framework['status'] in ['coming', 'open', 'pending']:
        return None

    if not project['lockedAt']:
        if following_framework['status'] == 'standstill':
            return SavedSearchStateEnum.NOT_LOCKED_STANDSTILL.value
        elif following_framework['status'] in ['live', 'expired']:
            return SavedSearchStateEnum.NOT_LOCKED_POST_LIVE.value
    else:
        if following_framework['status'] == 'standstill':
            return SavedSearchStateEnum.LOCKED_STANDSTILL.value
        elif framework['status'] == 'live' and following_framework['status'] in ['live', 'expired']:
            return SavedSearchStateEnum.LOCKED_POST_LIVE_DURING_INTERIM.value
        elif framework['status'] == 'expired' and following_framework['status'] in ['live', 'expired']:
            return SavedSearchStateEnum.LOCKED_POST_LIVE_POST_INTERIM.value

    # this should never be reached
    current_app.logger.error(
        "Saved search banner messages invalid frameworks state: "
        "'{}' - '{}' and '{}' - '{}'".format(
            framework['slug'], framework['status'], following_framework['slug'], following_framework['status']
        )
    )
    abort(500)
