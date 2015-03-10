import json
from . import main
from app import models
from flask import abort, render_template, request, Response
from ..presenters.search_presenters import SearchFilters
from ..helpers.search_helpers import (
    get_keywords_from_request, get_template_data
)
from ..exceptions import AuthException


@main.route('/')
def index():
    return "Hello, World!", 200


@main.route('/service/<service_id>')
def get_service_by_id(service_id):
    try:
        service = models.get_service(service_id)
        return Response(service, mimetype='application/json')
    except AuthException as e:
        abort(500, "Application error")
    except KeyError:
        abort(404, "Service ID '%s' can not be found" % service_id)


@main.route('/search')
def search():
    search_keywords = get_keywords_from_request(request)
    search_filters_obj = SearchFilters(blueprint=main, request=request)
    response = models.search_for_services(
        query=search_keywords,
        filters=search_filters_obj.get_request_filters()
    )
    search_results_json = json.loads(response)
    template_data = get_template_data(main, {
        'title': 'Search results',
        'search_keywords': search_keywords,
        'filter_groups': search_filters_obj.get_filter_groups(),
        'services': search_results_json['services']
    })
    return render_template('search.html', **template_data)
