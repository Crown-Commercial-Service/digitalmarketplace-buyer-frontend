# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import abort, render_template, request, redirect, current_app

from dmutils.formats import get_label_for_lot_param, dateformat
from dmapiclient import HTTPError
from dmutils.formats import LOTS

from ...main import main
from ...presenters.search_presenters import (
    filters_for_lot,
    set_filter_states,
)
from ...presenters.search_results import SearchResults
from ...presenters.search_summary import SearchSummary
from ...presenters.service_presenters import Service
from ...helpers.search_helpers import (
    get_keywords_from_request, pagination,
    get_page_from_request, query_args_for_pagination,
    get_lot_from_request, build_search_query,
    clean_request_args
)

from ...exceptions import AuthException
from app import data_api_client, content_loader


@main.route('/g-cloud')
def index_g_cloud():
    return render_template('index-g-cloud.html')


@main.route('/g-cloud/framework')
def framework_g_cloud():
    return redirect('https://www.gov.uk/guidance/the-g-cloud-framework-on-the-digital-marketplace', 301)


@main.route('/suppliers-guide')
def suppliers_guide():
    return redirect('/g-cloud/suppliers-guide', 301)


@main.route('/g-cloud/buyers-guide')
def buyers_guide_g_cloud():
    return redirect('https://www.gov.uk/guidance/g-cloud-buyers-guide', 301)


@main.route('/g-cloud/suppliers-guide')
def suppliers_guide_g_cloud():
    return redirect('https://www.gov.uk/guidance/g-cloud-suppliers-guide', 301)


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
                service_data['supplierCode']
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

        return render_template(
            'service.html',
            service=service_view_data,
            service_unavailability_information=service_unavailability_information,
            lot=service_view_data.lot.lower(),
            lot_label=get_label_for_lot_param(service_view_data.lot.lower())), status_code
    except AuthException:
        abort(500, "Application error")
    except KeyError:
        abort(404, "Service ID '%s' can not be found" % service_id)
    except HTTPError as e:
        abort(e.status_code)
