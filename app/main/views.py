# coding=utf-8

import os
from . import main
from flask import abort, render_template, request
from ..presenters.search_presenters import SearchFilters, SearchResults
from ..presenters.service_presenters import Service
from ..helpers.search_helpers import (
    get_keywords_from_request, get_template_data
)
from ..helpers.service_helpers import get_lot_name_from_acronym
from ..exceptions import AuthException
from .. import search_api_client, data_api_client


@main.route('/')
def index():
    template_data = get_template_data(main, {
        'title': 'Digital Marketplace'
    })
    return render_template('index.html', **template_data)


@main.route('/g-cloud')
def index_g_cloud():
    breadcrumb = [
        {'text': 'Cloud technology and support'}
    ]
    template_data = get_template_data(main, {
        'title': 'Cloud technology and support – Digital Marketplace',
        'crumbs': breadcrumb
    })
    return render_template('index-g-cloud.html', **template_data)


@main.route('/service/<service_id>')
def get_service_by_id(service_id):
    try:
        service = data_api_client.get_service(service_id)
        service_view_data = Service(service)
        breadcrumb = [
            {'text': get_lot_name_from_acronym(main, service['lot'])}
        ]
        template_data = get_template_data(main, {
            'crumbs': breadcrumb,
            'service': service_view_data
        })
        return render_template('service.html', **template_data)
    except AuthException:
        abort(500, "Application error")
    except KeyError as e:
        print e
        abort(404, "Service ID '%s' can not be found" % service_id)


@main.route('/search')
def search():
    search_keywords = get_keywords_from_request(request)
    search_filters_obj = SearchFilters(blueprint=main, request=request)
    response = search_api_client.search_services(
        **dict([a for a in request.args.lists()]))
    search_results_obj = SearchResults(response)

    template_data = get_template_data(main, {
        'title': 'Search results',
        'current_lot': SearchFilters.get_current_lot(request),
        'lots': search_filters_obj.lot_filters,
        'search_keywords': search_keywords,
        'filter_groups': search_filters_obj.filter_groups,
        'services': search_results_obj.search_results,
        'summary': search_results_obj.summary
    })
    return render_template('search.html', **template_data)
