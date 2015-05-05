import requests

try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse
from flask import json
from .exceptions import AuthException
from . import search_api_client


def handle_api_errors(response):
    if response.status_code == 403:
        raise AuthException("API authentication failed")


def strip_services_wrapper(content):
    content_json = json.loads(content)
    return content_json["services"]


def get_service(service_id):
    url = "http://localhost:5000/services/" + service_id
    response = requests.get(
        url,
        headers={
            "authorization": "Bearer myToken"
        }
    )
    handle_api_errors(response)
    response_content = strip_services_wrapper(response.content)
    return response_content


def search_for_services(args):
    return search_api_client.search(
        _convert_multidict_to_request_payload(args)
    )


def _convert_multidict_to_request_payload(args):
    """
        minimumContractPeriod is an OR filter - the only one currently
        needs to be a comma separated string NOT multiple key/value pairs
    """
    payload = {}
    for query_arg in args.iterlists():
        if query_arg[0] == "q":
            payload[query_arg[0]] = query_arg[1][0]
        elif query_arg[0] == "minimumContractPeriod":
            payload["filter_" + query_arg[0]] = ",".join(query_arg[1])
        elif len(query_arg[1]) == 1:
            payload["filter_" + query_arg[0]] = query_arg[1][0]
        else:
            payload["filter_" + query_arg[0]] = query_arg[1]

    return payload
