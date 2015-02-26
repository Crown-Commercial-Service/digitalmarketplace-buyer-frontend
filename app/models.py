import requests
import os
from flask import json
from elasticsearch import Elasticsearch

es = Elasticsearch()


def strip_services_wrapper(content):
    content_json = json.loads(content)
    return json.dumps(content_json["services"])


def get_service(service_id):
    # TODO: Don't do these checks for every call - initialise once
    access_token = os.getenv('DM_API_BEARER')
    api_url = os.getenv('DM_API_URL')
    if access_token is None:
        print('Bearer token must be supplied in DM_API_BEARER')
        raise Exception("DM_API_BEARER token is not set")
    if api_url is None:
        print('API URL must be supplied in DM_API_URL')
        raise Exception("DM_API_URL is not set")
    url = api_url + "/services/" + service_id
    response = requests.get(
        url,
        headers={
            "authorization": "Bearer {}".format(access_token)
        }
    )
    return strip_services_wrapper(response.content)


def search_for_service(query, start_from=0, size=10):
    res = es.search(index="services",
                    body={
                        "from": start_from, "size": size,
                        "fields": ["id", "serviceName", "lot",
                                   "serviceSummary"],
                        "query": {
                            "multi_match": {
                                "query": query,
                                "fields": ["serviceName",
                                           "serviceSummary",
                                           "serviceFeatures",
                                           "serviceBenefits"],
                                "operator": "or"
                            }
                        }
                        }
                    )
    return res


def search_with_lot_filter(query, lot, start_from=0, size=10):
    res = es.search(index="services",
                    body={
                        "from": start_from, "size": size,
                        "fields": ["id", "serviceName", "lot",
                                   "serviceSummary"],
                        "query": {
                            "filtered": {
                                "query": {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["serviceName",
                                                   "serviceSummary",
                                                   "serviceFeatures",
                                                   "serviceBenefits"],
                                        "operator": "or"
                                    }
                                },
                                "filter": {
                                    "term": {"lot": lot.lower()}
                                }
                            }
                        }
                    }
                    )
    return res


def search_with_filters(query, args, start_from=0, size=10):
    filters = []
    for k, v in args.iteritems():
        filters.append({"term": {k: v.lower()}})
    res = es.search(index="services",
                    body={
                        "from": start_from, "size": size,
                        "fields": ["id", "serviceName", "lot",
                                   "serviceSummary"],
                        "query": {
                            "filtered": {
                                "query": {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["serviceName",
                                                   "serviceSummary",
                                                   "serviceFeatures",
                                                   "serviceBenefits"],
                                        "operator": "or"
                                    }
                                },
                                "filter": {
                                    "bool": {"must": filters}
                                }
                            }
                        }
                    }
                    )
    return res
