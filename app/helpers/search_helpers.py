from math import ceil

from werkzeug.datastructures import MultiDict

from dmutils.formats import lot_to_lot_case


def get_template_data(blueprint, view_data):
    """Returns a single object holding the base template data with the view
       data added"""

    template_data = blueprint.config['BASE_TEMPLATE_DATA']
    for key in view_data:
        template_data[key] = view_data[key]
    return template_data


def get_lot_from_request(request):
    return request.args.get('lot', None)


def get_keywords_from_request(request):
    return request.args.get('q', '')


def get_page_from_request(request):
    if 'page' in request.args:
        return int(request.args['page'])
    else:
        return None


def get_filters_from_request(request):
    """Returns the filters applied to a search from the request object"""

    filters = MultiDict(request.args.copy())
    filters.poplist('q')
    filters.poplist('lot')
    filters.poplist('page')
    return filters


def allowed_request_lot_filters(lot_filters):
    """Create a set of (name, value) pairs for all form filters."""

    return set(
        (f['name'], f['value'])
        for section in lot_filters
        for f in section['filters']
    )


def clean_request_filters(request_filters, lot_filters):
    """Removes any unknown filter keys or values from request.

    Compares every key/value pair from request query parameters
    with the list of name/value pairs retrieved from search
    presenters. Only pairs that match are kept.

    """
    allowed_filters = allowed_request_lot_filters(lot_filters)

    clean_filters = MultiDict([
        f for f in request_filters.items(multi=True)
        if f in allowed_filters
    ])

    return clean_filters


def group_request_filters(request_filters, content_loader):
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
        if content_loader.get_question(key).get("type") == 'radios':
            filter_query[key] = [','.join(values)]
        else:
            filter_query[key] = values

    return filter_query


def build_search_query(request, lot_filters, content_loader):
    """Match request args with known filters.

    Removes any unknown query parameters, and will only keep `page`, `q`
    and `lot` if they are set.

    Resulting query will only contain fields and values that could be set
    through the UI and will group OR and AND filters.

    """
    filters = clean_request_filters(
        get_filters_from_request(request),
        lot_filters
    )

    query = group_request_filters(filters, content_loader)
    lot = request.args.get('lot')

    if lot_to_lot_case(lot):
        query['lot'] = lot
    if request.args.get('q'):
        query['q'] = request.args['q']
    if request.args.get('page'):
        query['page'] = request.args['page']

    return query


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
