from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def parse_link(links, label):
    return parse_qs(urlparse(links[label]).query) if label in links else None


def get_one_framework_by_status_in_order_of_preference(frameworks, statuses_in_order_of_preference):
    for status in statuses_in_order_of_preference:
        for framework in frameworks:
            if framework.get('status') == status:
                return framework


def construct_url_from_base_and_params(base_url, query_params):
    """
    Combine a base url (MUST NOT HAVE ANY QUERY PARAMS TO BE RETAINED) with supplied query params
    :param base_url: A url e.g. http://localhost
    :param query_params: A tuple of key/value tuples ((param_name, param_val), ...)
    :return: A url with the query params inline e.g. http://localhost?param_name=param_val
    """
    # urlparse breaks a URL into six items (scheme, netloc, path, params, query, fragment)
    parsed_url = list(urlparse(base_url))

    # We want to use all existing segments except the current query params (5th item), which we'll overwrite.
    parsed_url[4] = urlencode(query_params)

    # Reconstruct the full URL with inline params from our six-item iterable
    return urlunparse(parsed_url)
