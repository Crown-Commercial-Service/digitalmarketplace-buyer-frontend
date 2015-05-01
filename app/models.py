import requests
import os
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


def search_for_services(query="", filters={}):
    print filters
    return search_api_client.search(query, filters['lot'])
