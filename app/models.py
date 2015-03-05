import requests
import os
from flask import json


api_url = os.getenv('DM_API_URL')
api_access_token = os.getenv('DM_BUYER_FRONTEND_API_AUTH_TOKEN')
search_url = os.getenv('DM_SEARCH_API_URL') + "/search"
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


def strip_services_wrapper(content):
    content_json = json.loads(content)
    return json.dumps(content_json["services"])


def get_service(service_id):
    url = api_url + "/services/" + service_id
    response = requests.get(
        url,
        headers={
            "authorization": "Bearer {}".format(api_access_token)
        }
    )
    return strip_services_wrapper(response.content)


def search_for_services(query="", filters={}):
    payload = {'q': query}
    for k, v in filters.iteritems():
        payload[k] = v
    response = requests.get(
        search_url,
        params=payload,
        headers={
            "authorization": "Bearer {}".format(search_access_token)
        }
    )
    return response.content
