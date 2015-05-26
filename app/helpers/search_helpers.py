from math import ceil


def get_template_data(blueprint, view_data):
    """Returns a single object holding the base template data with the view
       data added"""

    template_data = blueprint.config['BASE_TEMPLATE_DATA']
    for key in view_data:
        template_data[key] = view_data[key]
    return template_data


def get_keywords_from_request(request):
    if 'q' in request.args:
        return request.args['q']
    else:
        return ""


def get_page_from_request(request):
    if 'page' in request.args:
        return int(request.args['page'])
    else:
        return None


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
    if total:
        return int(ceil(float(total) / page_size))
    else:
        return None


def pagination(num_services, page_size, page=None):
    total = total_pages(num_services, page_size)
    next_page = None
    prev_page = None

    if page and num_services > page_size:
        next_page = page + 1
    elif not page and num_services > page_size:
        next_page = 2

    if page and page > 1:
        prev_page = page - 1

    if page and page > total:
        prev_page = total

    show_prev = False
    show_next = False

    if page and page > 1:
        show_prev = True

    if (page is None and total > 1) or (total > 1 and page < total):
        show_next = True

    return {
        "total_pages": total,
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
