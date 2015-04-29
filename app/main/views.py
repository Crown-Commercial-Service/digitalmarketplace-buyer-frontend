# coding=utf-8

import os
import re
import json

from . import main
from app import models
from flask import abort, render_template, request, Response
from ..presenters.search_presenters import SearchFilters
from ..presenters.service_presenters import Service
from ..helpers.search_helpers import (
    get_keywords_from_request, get_template_data
)
from ..helpers.service_helpers import get_lot_name_from_acronym
from ..exceptions import AuthException


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
        service = models.get_service(service_id)
        service_view_data = Service(service)
        breadcrumb = [
            {'text': get_lot_name_from_acronym(main, service['lot'])}
        ]
        template_data = get_template_data(main, {
            'crumbs': breadcrumb,
            'service': service_view_data
        })
        return render_template('service.html', **template_data)
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
        filters=search_filters_obj.request_filters
    )
    search_results_json = response
    template_data = get_template_data(main, {
        'title': 'Search results',
        'current_lot': SearchFilters.get_current_lot(request),
        'lots': search_filters_obj.lot_filters,
        'search_keywords': search_keywords,
        'filter_groups': search_filters_obj.filter_groups,
        'services': search_results_json['search']['services']
    })
    return render_template('search.html', **template_data)


def _get_questions():
    question_sections_manifest = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "../helpers/question_sections_manifest.yml"
    ))
    questions_directory = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "../../bower_components/digital-marketplace-ssp-content/g6"
    ))
    return QuestionsLoader(question_sections_manifest, questions_directory)
