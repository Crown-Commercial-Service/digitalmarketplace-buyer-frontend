# coding=utf-8

from __future__ import unicode_literals

from datetime import datetime
from flask import abort, render_template, request, redirect, \
    url_for, current_app

from dmutils.deprecation import deprecated
from dmutils.formats import get_label_for_lot_param, dateformat
from dmapiclient import HTTPError, APIError
from dmutils.formats import LOTS
from dmutils.content_loader import ContentNotFoundError

from . import main
from ..presenters.search_presenters import (
    filters_for_lot,
    set_filter_states,
)
from ..presenters.search_results import SearchResults
from ..presenters.search_summary import SearchSummary
from ..presenters.service_presenters import Service
from ..helpers.shared_helpers import get_one_framework_by_status_in_order_of_preference
from ..helpers.search_helpers import (
    get_keywords_from_request, get_template_data, pagination,
    get_page_from_request, query_args_for_pagination,
    get_lot_from_request, build_search_query,
    clean_request_args
)

from ..exceptions import AuthException
from .. import search_api_client, data_api_client, content_loader


@main.route('/')
def index():
    template_data = get_template_data(main, {})
    temporary_message = {}

    try:
        frameworks = data_api_client.find_frameworks().get('frameworks')
        framework = get_one_framework_by_status_in_order_of_preference(
            frameworks,
            ['open', 'coming', 'pending']
        )

        if framework is not None:
            content_loader.load_messages(framework.get('slug'), ['homepage-sidebar'])
            temporary_message = content_loader.get_message(
                framework.get('slug'),
                'homepage-sidebar',
                framework.get('status')
            )

    # if no framework is found (should never happen), ditch the message and load the page
    except APIError:
        pass
    # if no message file is found (should never happen), throw a 500
    except ContentNotFoundError:
        current_app.logger.error(
            "contentloader.fail No message file found for framework. "
            "framework {} status {}".format(framework.get('slug'), framework.get('status')))
        abort(500)

    return render_template(
        'index.html',
        temporary_message=temporary_message,
        **template_data
    )


@main.route('/g-cloud')
def index_g_cloud():
    template_data = get_template_data(main, {})
    return render_template('index-g-cloud.html', **template_data)


@main.route('/g-cloud/framework')
def framework_g_cloud():
    template_data = get_template_data(main, {})
    return render_template('content/framework-g-cloud.html', **template_data)


@main.route('/digital-services/framework')
def framework_digital_services():
    template_data = get_template_data(main, {})
    return render_template(
        'content/framework-digital-services.html', **template_data
    )


@main.route('/crown-hosting')
def index_crown_hosting():
    template_data = get_template_data(main, {})
    return render_template('content/index-crown-hosting.html', **template_data)


@main.route('/crown-hosting/framework')
def framework_crown_hosting():
    template_data = get_template_data(main, {})
    return render_template(
        'content/framework-crown-hosting.html', **template_data
    )


@main.route('/buyers-guide')
def buyers_guide():
    template_data = get_template_data(main, {})
    return render_template('content/buyers-guide.html', **template_data)


@main.route('/suppliers-guide')
def suppliers_guide():
    return redirect('/g-cloud/suppliers-guide', 301)


@main.route('/g-cloud/buyers-guide')
def buyers_guide_g_cloud():
    template_data = get_template_data(main, {})
    return render_template(
        'content/buyers-guide-g-cloud.html', **template_data
    )


@main.route('/g-cloud/suppliers-guide')
def suppliers_guide_g_cloud():
    template_data = get_template_data(main, {})
    return render_template(
        'content/suppliers-guide-g-cloud.html', **template_data
    )


@main.route('/cookies')
def cookies():
    template_data = get_template_data(main, {})
    return render_template(
        'content/cookies.html', **template_data
    )


@main.route('/terms-and-conditions')
def terms_and_conditions():
    template_data = get_template_data(main, {})
    return render_template(
        'content/terms-and-conditions.html', **template_data
    )


# support legacy urls generated by the grails app
@main.route('/service/<service_id>')
@deprecated(dies_at=datetime(2016, 1, 1))
def redirect_service_page(service_id):
    return redirect(url_for(
        ".get_service_by_id",
        service_id=service_id.upper()), code=301
    )


@main.route('/g-cloud/services/<service_id>')
def get_service_by_id(service_id):
    try:
        service = data_api_client.get_service(service_id)
        if service is None:
            abort(404, "Service ID '{}' can not be found".format(service_id))
        if service['services']['frameworkStatus'] not in ("live", "expired"):
            abort(404, "Service ID '{}' can not be found".format(service_id))

        service_data = service['services']
        service_view_data = Service(
            service_data,
            content_loader.get_builder('g-cloud-6', 'display_service').filter(
                service_data
            )
        )

        try:
            # get supplier data and add contact info to service object
            supplier = data_api_client.get_supplier(
                service_data['supplierId']
            )
            supplier_data = supplier['suppliers']
            service_view_data.meta.set_contact_attribute(
                supplier_data['contactInformation'][0].get('contactName'),
                supplier_data['contactInformation'][0].get('phoneNumber'),
                supplier_data['contactInformation'][0].get('email')
            )

        except HTTPError as e:
            abort(e.status_code)

        service_unavailability_information = None
        status_code = 200
        if service['serviceMadeUnavailableAuditEvent'] is not None:
            service_unavailability_information = {
                'date': dateformat(service['serviceMadeUnavailableAuditEvent']['createdAt']),
                'type': service['serviceMadeUnavailableAuditEvent']['type']
            }
            # mark the resource as unavailable in the headers
            status_code = 410

        template_data = get_template_data(main, {
            'service': service_view_data,
            'service_unavailability_information': service_unavailability_information,
            'lot': service_view_data.lot.lower(),
            'lot_label': get_label_for_lot_param(service_view_data.lot.lower())
        })
        return render_template('service.html', **template_data), status_code
    except AuthException:
        abort(500, "Application error")
    except KeyError:
        abort(404, "Service ID '%s' can not be found" % service_id)
    except HTTPError as e:
        abort(e.status_code)


@main.route('/search')
@deprecated(dies_at=datetime(2016, 1, 1))
def redirect_search():
    return redirect(url_for(".search", **request.args), code=301)


@main.route('/g-cloud/search')
def search():
    content_builder = content_loader.get_builder('g-cloud-6', 'search_filters')
    filters = filters_for_lot(
        get_lot_from_request(request),
        content_builder
    )

    response = search_api_client.search_services(
        **build_search_query(request, filters, content_builder)
    )

    search_results_obj = SearchResults(response)

    pagination_config = pagination(
        search_results_obj.total,
        current_app.config["DM_SEARCH_PAGE_SIZE"],
        get_page_from_request(request)
    )

    search_summary = SearchSummary(
        response['meta']['total'],
        clean_request_args(request.args, filters),
        filters
    )

    set_filter_states(filters, request)
    current_lot = get_lot_from_request(request)

    template_data = get_template_data(main, {
        'title': 'Search results',
        'current_lot': current_lot,
        'lots': LOTS,
        'search_keywords': get_keywords_from_request(request),
        'services': search_results_obj.search_results,
        'total': search_results_obj.total,
        'search_query': query_args_for_pagination(request.args),
        'pagination': pagination_config,
        'summary': search_summary.markup(),
        'filters': filters,
    })
    if current_lot:
        template_data['current_lot_label'] = get_label_for_lot_param(current_lot)

    return render_template('search.html', **template_data)
