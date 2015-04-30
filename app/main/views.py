# coding=utf-8
from flask import abort, render_template, request

from . import main
from .. import data_api_client, search_api_client
from ..presenters.search_presenters import SearchFilters
from ..helpers.search_helpers import (
    get_keywords_from_request, get_template_data
)
from ..helpers.service_helpers import get_lot_name_from_acronym
from ..presenters.service_presenters import Service


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
    except KeyError:
        abort(404, "Service ID '%s' can not be found" % service_id)


@main.route('/search')
def search():
    search_keywords = get_keywords_from_request(request)
    search_filters_obj = SearchFilters(blueprint=main, request=request)
    services = search_api_client.search_services(
        query=search_keywords,
        filters=search_filters_obj.get_request_filters())['services']

    template_data = get_template_data(main, {
        'title': 'Search results',
        'search_keywords': search_keywords,
        'filter_groups': search_filters_obj.get_filter_groups(),
        'services': services,
    })
    return render_template('search.html', **template_data)
