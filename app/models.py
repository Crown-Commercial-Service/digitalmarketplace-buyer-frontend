import requests
import os
import urlparse
from flask import json
from .exceptions import AuthException


api_url = os.getenv('DM_API_URL')
api_access_token = os.getenv('DM_BUYER_FRONTEND_API_AUTH_TOKEN')
search_url = urlparse.urljoin(
    os.getenv('DM_SEARCH_API_URL'),
    'g-cloud/services/search'
)
search_access_token = os.getenv('DM_BUYER_FRONTEND_SEARCH_API_AUTH_TOKEN')

if api_access_token is None:
    print('Token must be supplied in DM_BUYER_FRONTEND_API_AUTH_TOKEN')
    raise Exception("DM_BUYER_FRONTEND_API_AUTH_TOKEN token is not set")
if api_url is None:
    print('API URL must be supplied in DM_API_URL')
    raise Exception("DM_API_URL is not set")
if search_access_token is None:
    print('Token must be supplied in DM_BUYER_FRONTEND_SEARCH_API_AUTH_TOKEN')
    raise Exception("DM_BUYER_FRONTEND_SEARCH_API_AUTH_TOKEN token is not set")
if search_url is None:
    print('Search API URL must be supplied in DM_SEARCH_API_URL')
    raise Exception("DM_SEARCH_API_URL is not set")


def handle_api_errors(response):
    if (response.status_code == 403):
        raise AuthException("API authentication failed")


def strip_services_wrapper(content):
    content_json = json.loads(content)
    return content_json["services"]


def get_service(service_id):
    url = api_url + "/services/" + service_id
    response = requests.get(
        url,
        headers={
            "authorization": "Bearer {}".format(api_access_token)
        }
    )
    handle_api_errors(response)
    response_content = strip_services_wrapper(response.content)
    return response_content


def search_for_services(query="", filters={}):
    payload = {'q': query}
    for k, v in filters.items():
        payload[k] = v
    '''
    response = requests.get(
        search_url,
        params=payload,
        headers={
            "authorization": "Bearer {}".format(search_access_token)
        }
    )
    return response.json()
    '''

    search_results_stub_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "tests",
            "fixtures",
            "search_results.json"
        )
    )
    return json.load(open(search_results_stub_path))
