from math import ceil
import re

from flask import url_for
from werkzeug.datastructures import MultiDict
from werkzeug.urls import Href


def get_valid_lot_from_args_or_none(args, all_lots):
    lot = args.get('lot', None)
    return lot if (not lot or lot in all_lots) else None


def get_keywords_from_request(request):
    return request.args.get('q', '')


def get_page_from_request(request):
    try:
        return int(request.args['page'])
    except (KeyError, ValueError, TypeError):
        return None


def get_request_url_without_any_filters(request, filters, view_name, **kwargs):
    """
    This function will returns the url path without any filters.
    It will still retain the categories, keyword and lots parameters as well as any others included.

    Args:
        request: Request Object (import from flask) of the current request.
        filters: list of all filters from digital marketplace framework

    Returns:
        URL path in string format.
    """

    all_request_filters = MultiDict(request.args.copy())

    for section in filters:
        for _filter in filters[section]['filters']:
            all_request_filters.poplist(_filter['name'])

    all_request_filters.poplist('page')
    all_request_filters.poplist('live-results')

    search_link_builder = Href(url_for('.{}'.format(view_name), **kwargs))
    url = search_link_builder(all_request_filters)

    return url


def get_filters_from_request(cleaned_request_args):
    """Returns the filters applied to a search from the request args"""

    filters = MultiDict(cleaned_request_args.copy())
    filters.poplist('q')
    filters.poplist('lot')
    filters.poplist('page')
    return filters


def allowed_request_lot_filters(lot_filters):
    """Create a set of (name, value) pairs for all form filters."""

    filters = set()

    def recursive_search(filters):
        more_filters = set()
        for f in filters:
            more_filters.add((f['name'], f['value']))
            children = f.get('children')
            if children:
                more_filters.update(recursive_search(children))
        return more_filters
    # recursive search to account for sub-filters (i.e. sub-categories)

    for section in lot_filters:
        filters.update(recursive_search(section['filters']))

    return filters


def clean_request_args(request_args, lot_filters, lots_by_slug, for_aggregation=False):
    """Removes any unknown args keys or values from request.

    Compares every key/value pair from request query parameters
    with the list of name/value pairs retrieved from search
    presenters. Only pairs that match are kept.

    'q' and 'page' arguments are preserved if present in the request.args.
    'lot' is only kept if the value is a valid lot.

    """
    allowed_filters = allowed_request_lot_filters(lot_filters)

    clean_args = MultiDict([
        f for f in request_args.items(multi=True)
        if f in allowed_filters
    ])

    restore_keys = ['q']

    if not for_aggregation:
        restore_keys.append('page')

    if request_args.get('lot') in lots_by_slug:
        restore_keys.append('lot')

    for key in restore_keys:
        if request_args.get(key):
            clean_args[key] = request_args.get(key)

    return clean_args


def group_request_filters(request_filters, content_builder):
    """Groups filters using ','/& according to question type.

    * Questions of type "radios" result in OR filters - there's only one
      possible value for the service, so searching for more than one option
      returns a union of results for both options. Search-api expects values
      joined by `,` for OR filters.
    * Questions of type "checkbox" result in AND filters - each service can
      have multiple values for the field, so searching for more than one
      option returns only services that contain all matching values. Search-api
      expects separate `&key=value` parameters for each AND filter.

    """
    filter_query = {}
    for key, values in request_filters.lists():
        if is_radio_type(content_builder, key):
            filter_query[key] = ','.join(values)
        elif len(values) == 1:
            filter_query[key] = values[-1]
        else:
            filter_query[key] = values

    return filter_query


def ungroup_request_filters(request_filters, content_builder):
    """Carries out the inverse of the above method which is required when going from search api url parameters
    to frontend url parameters. Where group_request_filters takes request_filters as a MultiDict, this method
    takes request_filters as a tuple of tuple pairs ((param_name, param_value), ...)"""
    filter_query = []

    for key, value in request_filters:
        if is_radio_type(content_builder, key):
            if ',' in value:
                for value in value.split(','):
                    filter_query.append((key, value))
            else:
                filter_query.append((key, value))
        else:
            filter_query.append((key, value))

    return tuple(filter_query)


def is_radio_type(content_builer, key):
    if key == 'lot':
        return True

    question = content_builer.get_question(key) or {}
    return question.get('type') == 'radios'


def replace_g5_search_dots(keywords_query):
    """Replaces '.' with '-' in G5 service IDs to support old ID search format."""

    return re.sub(
        r'5\.G(\d)\.(\d{4})\.(\d{3})',
        r'5-G\1-\2-\3',
        keywords_query
    )


def get_filter_value_from_question_option(option):
    """
    Processes `option` into a search term value suitable for the Search API.

    The Search API does not allow commas in filter values, because they are used
    to separate the terms in an 'OR' search - see `group_request_filters`. They
    are removed from the field values by the indexer by the Search API itself,
    see `dm-search-api:app.main.services.conversions.strip_and_lowercase`.

    :return: normalized string value
    """
    return (option.get('value') or option.get('label', '')).lower().replace(',', '')


def build_search_query(request_args, lot_filters, content_builder, lots_by_slug, for_aggregation=False):
    """Match request args with known filters.

    Removes any unknown query parameters, and will only keep `page`, `q`
    and `lot` if they are set.

    Resulting query will only contain fields and values that could be set
    through the UI and will group OR and AND filters.

    """
    query = clean_request_args(
        request_args,
        lot_filters,
        lots_by_slug,
        for_aggregation=for_aggregation
    )

    return group_request_filters(query, content_builder)


def query_args_for_pagination(args):
    """
    To use url_for for pagination next/prev page links
    We need to not have the current page in the query args
    :param request:
    :return request args without page
    """
    query = args.copy()

    if 'page' in query:
        del query['page']
        return query
    else:
        return query


def total_pages(total, page_size):
    if int(total) > 1:
        return int(ceil(float(total) / page_size))
    else:
        return 1


def pagination(num_services, page_size, page=None):
    total_num_pages = total_pages(num_services, page_size)
    next_page = None
    prev_page = None
    show_prev = False
    show_next = False

    # are we currently paginated?
    if page:
        # next page is page + 1 if num services exceeds page size
        if num_services > page_size:
            next_page = page + 1

        # prev page is page - 1 OR last page if page beyond upper bound
        if page > 1:
            prev_page = page - 1
        if page > total_num_pages:
            prev_page = total_num_pages

        # show previous link if after page 1
        if page > 1:
            show_prev = True

        # Show next link if have multiple pages and are not at last page
        if total_num_pages > 1 and page < total_num_pages:
            show_next = True
    # on first page
    else:
        # next page always page 2 if have more services than page size
        if num_services > page_size:
            next_page = 2
        # show next if have more than 1 page
        # not on last page as no page param
        if total_num_pages > 1:
            show_next = True

    return {
        "total_pages": total_num_pages,
        "show_prev": show_prev,
        "show_next": show_next,
        "next_page": next_page,
        "prev_page": prev_page,
    }


def valid_page(page):
    """
    Valid pages are positive integers
    If an invalid page is supplied negative or text
    default to non-paginated search
    :param args:
    :return:
    """
    if page:
        try:
            val = int(page)
            if val < 1:
                raise ValueError("No negative numbers")
            return val
        except ValueError:
            return None
    return None
