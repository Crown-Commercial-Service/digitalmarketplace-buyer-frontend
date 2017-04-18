# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import abort, render_template, request, redirect, current_app, url_for

from dmutils.formats import dateformat
from dmapiclient import HTTPError

from ...main import main
from ..presenters.search_presenters import (
    filters_for_lot,
    set_filter_states,
    annotate_lots_with_categories_selection,
)
from ..presenters.search_results import SearchResults
from ..presenters.search_summary import SearchSummary
from ..presenters.service_presenters import Service
from ..helpers.search_helpers import (
    get_keywords_from_request, pagination,
    get_page_from_request, query_args_for_pagination,
    get_lot_from_request, build_search_query,
    clean_request_args
)
from ..helpers import framework_helpers

from ..exceptions import AuthException
from app import search_api_client, data_api_client, content_loader


@main.route('/g-cloud')
def index_g_cloud():
    # if there are multiple live g-cloud frameworks, assume they all have the same lots
    all_frameworks = data_api_client.find_frameworks().get('frameworks')
    framework = framework_helpers.get_latest_live_framework(all_frameworks, 'g-cloud')

    # TODO remove me after G-Cloud 9 goes live
    show_search_box = not framework_helpers.is_g9_live(all_frameworks)

    lot_browse_list_items = list()
    for lot in framework['lots']:
        lot_item = {
            "link": url_for('.search_services', lot=lot['slug']),
            "title": lot['name']
        }

        # TODO proper lot body/subtext for G9 - G7/G8 content moved here temporarily from template

        if lot['slug'] == 'saas':
            lot_item.update({
                "body": "Find applications or services that are run over the internet or in the cloud",
                "subtext": "eg accounting tools or email",
            })
        elif lot['slug'] == 'paas':
            lot_item.update({
                "body": "Find platforms that provide a basis for building other services and applications",
            })
        elif lot['slug'] == 'iaas':
            lot_item.update({
                "body": "Find networks, hosting facilities and servers on which platforms and software depend",
                "subtext": "eg hosting or content delivery",
            })
        elif lot['slug'] == 'scs':
            lot_item.update({
                "body": "Find help with cloud management and deployment",
                "subtext": "eg IT health checks or data migrations",
            })

        lot_browse_list_items.append(lot_item)

    return render_template('index-g-cloud.html', lots=lot_browse_list_items, show_search_box=show_search_box)


@main.route('/g-cloud/framework')
def framework_g_cloud():
    return redirect('https://www.gov.uk/guidance/the-g-cloud-framework-on-the-digital-marketplace', 301)


@main.route('/buyers-guide')
def buyers_guide():
    return redirect('https://www.gov.uk/guidance/g-cloud-buyers-guide', 301)


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
        framework_slug = service_data['frameworkSlug']

        # Some frameworks don't actually have framework content of their own (e.g. G-Cloud 4 and 5) - they
        # use content from some other framework (for those examples, G-Cloud 6 content works fine). In those
        # cases, we need to override the framework slug that we got from the service data, and load that
        # content instead.
        override_framework_slug = current_app.config.get('DM_FRAMEWORK_CONTENT_MAP', {}).get(framework_slug)
        if override_framework_slug:
            framework_slug = override_framework_slug

        framework = data_api_client.get_framework(framework_slug)['frameworks']
        service_view_data = Service(
            service_data,
            content_loader.get_builder(framework_slug, 'display_service').filter(
                service_data
            ),
            framework_helpers.get_lots_by_slug(framework)
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

        return render_template(
            'service.html',
            service=service_view_data,
            service_unavailability_information=service_unavailability_information,
            lot=service_view_data.lot), status_code
    except AuthException:
        abort(500, "Application error")
    except HTTPError as e:
        abort(e.status_code)


@main.route('/g-cloud/search')
def search_services():
    # if there are multiple live g-cloud frameworks, we must assume the same filters work on them all
    all_frameworks = data_api_client.find_frameworks().get('frameworks')
    framework = framework_helpers.get_latest_live_framework(all_frameworks, 'g-cloud')

    # TODO remove me after G-Cloud 9 goes live
    is_g9_live = framework_helpers.is_g9_live(all_frameworks)

    current_lot_slug = get_lot_from_request(request)
    lots_by_slug = framework_helpers.get_lots_by_slug(framework)

    # the bulk of the possible filter parameters are defined through the content loader. they're all boolean and the
    # search api uses the same "question" labels as the content for its attributes, so we can really use those labels
    # verbatim. It also means we can use their human-readable names as defined in the content
    content_manifest = content_loader.get_manifest(framework['slug'], 'search_filters')
    # filters - an OrderedDictionary of dicts describing each parameter group
    filters = filters_for_lot(
        current_lot_slug,
        content_manifest
    )

    search_api_response = search_api_client.search_services(
        **build_search_query(request, filters.values(), content_manifest, lots_by_slug)
    )

    search_results_obj = SearchResults(search_api_response, lots_by_slug)

    # the search api doesn't supply its own pagination information: use this `pagination` function to figure out what
    # links to show
    pagination_config = pagination(
        search_results_obj.total,
        current_app.config["DM_SEARCH_PAGE_SIZE"],
        get_page_from_request(request)
    )

    search_summary = SearchSummary(
        search_api_response['meta']['total'],
        clean_request_args(request.args, filters.values(), lots_by_slug),
        filters.values(),
        lots_by_slug
    )

    # for display purposes (but not for actual filtering purposes), we
    # remove 'categories' from the list of filters, and process them into a single structure with the lots
    if is_g9_live:
        category_filter_group = filters.pop('categories') if 'categories' in filters else None
    else:
        category_filter_group = None

    lots = framework['lots']
    current_category_filter = annotate_lots_with_categories_selection(lots, category_filter_group, request)

    current_lot = lots_by_slug.get(current_lot_slug)

    # annotate `filters` with their values as set in this request for re-rendering purposes.
    set_filter_states(filters.values(), request)

    return render_template(
        'search/services.html',
        current_lot=current_lot,
        current_category_filter=current_category_filter,
        filters=filters.values(),
        lots=lots,
        pagination=pagination_config,
        search_keywords=get_keywords_from_request(request),
        search_query=query_args_for_pagination(request.args),
        services=search_results_obj.search_results,
        summary=search_summary.markup(),
        title='Search results',
        total=search_results_obj.total,
        show_all_categories=not is_g9_live,
    )
