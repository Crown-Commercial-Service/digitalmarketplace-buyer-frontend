# coding=utf-8

from . import main
from flask import abort, render_template, request, redirect, url_for
from ..presenters.search_presenters import SearchFilters, SearchResults
from ..presenters.service_presenters import Service
from ..helpers.search_helpers import (
    get_keywords_from_request, get_template_data
)
from ..helpers.service_helpers import get_lot_name_from_acronym
from ..exceptions import AuthException
from .. import search_api_client, data_api_client
from dmutils.apiclient import HTTPError


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


@main.route('/g-cloud/framework')
def framework_g_cloud():
    template_data = get_template_data(main, {
        'title': 'G-Cloud framework – Digital Marketplace',
        'crumbs': [
            {
                'text': 'Cloud technology and support',
                'link': url_for('.index_g_cloud')
            },
            {
                'text': 'Framework information'
            },
        ]
    })
    return render_template('content/framework-g-cloud.html', **template_data)


@main.route('/digital-services/framework')
def framework_digital_services():
    template_data = get_template_data(main, {
        'title': 'Digital Services framework – Digital Marketplace',
        'crumbs': [
            {
                'text': 'Specialists to work on digital projects',
                'link': 'https://digitalservicesstore.service.gov.uk'
            },
            {
                'text': 'Framework information'
            },
        ]
    })
    return render_template(
        'content/framework-digital-services.html', **template_data
    )


@main.route('/crown-hosting')
def index_crown_hosting():
    template_data = get_template_data(main, {
        'title': 'Physical datacentre space for legacy systems – Digital Marketplace',  # noqa
        'crumbs': [
            {'text': 'Physical datacentre space for legacy systems'}
        ]
    })
    return render_template('content/index-crown-hosting.html', **template_data)


@main.route('/crown-hosting/framework')
def framework_crown_hosting():
    template_data = get_template_data(main, {
        'title': 'Crown Hosting Data Centres framework – Digital Marketplace',
        'crumbs': [
            {
                'text': 'Physical datacentre space for legacy systems',
                'link': url_for('.index_crown_hosting')
            },
            {
                'text': 'Framework information'
            },
        ]
    })
    return render_template(
        'content/framework-crown-hosting.html', **template_data
    )


@main.route('/buyers-guide')
def buyers_guide():
    template_data = get_template_data(main, {
        'title': 'Buyers guide – Digital Marketplace',
        'crumbs': [
            {
                'text': 'Buyers\' guide'
            }
        ]
    })
    return render_template('content/buyers-guide.html', **template_data)


@main.route('/suppliers-guide')
def suppliers_guide():
    return redirect('/g-cloud/suppliers-guide', 301)


@main.route('/g-cloud/buyers-guide')
def buyers_guide_g_cloud():
    template_data = get_template_data(main, {
        'title': 'G-Cloud buyers\' guide – Digital Marketplace',
        'crumbs': [
            {
                'text': 'Cloud technology and support',
                'link': url_for('.index_g_cloud')
            },
            {
                'text': 'Buyers\' guide'
            }
        ]
    })
    return render_template(
        'content/buyers-guide-g-cloud.html', **template_data
    )


@main.route('/g-cloud/suppliers-guide')
def suppliers_guide_g_cloud():
    template_data = get_template_data(main, {
        'title': 'G-Cloud suppliers\' guide – Digital Marketplace',
        'crumbs': [
            {
                'text': 'Cloud technology and support',
                'link': url_for('.index_g_cloud')
            },
            {
                'text': 'Suppliers\' guide'
            }
        ]
    })
    return render_template(
        'content/suppliers-guide-g-cloud.html', **template_data
    )


@main.route('/terms-and-conditions')
def terms_and_conditions():
    template_data = get_template_data(main, {
        'title': 'Terms and conditions – Digital Marketplace',
        'crumbs': []
    })
    return render_template(
        'content/terms-and-conditions.html', **template_data
    )


@main.route('/services/<service_id>')
def get_service_by_id(service_id):
    try:
        service = data_api_client.get_service(service_id)
        service_view_data = Service(service)

        try:
            # get supplier data and add contact info to service object
            supplier = data_api_client.get_supplier(
                service['services']['supplierId']
            )
            supplier_data = supplier['suppliers']
            service_view_data.meta.set_contact_attribute(
                supplier_data['contactInformation'][0].get('contactName'),
                supplier_data['contactInformation'][0].get('phoneNumber'),
                supplier_data['contactInformation'][0].get('email')
            )

        except HTTPError as e:
            abort(e.status_code)

        breadcrumb = [
            {'text': get_lot_name_from_acronym(main, service_view_data.lot)}
        ]
        template_data = get_template_data(main, {
            'crumbs': breadcrumb,
            'service': service_view_data
        })
        return render_template('service.html', **template_data)
    except AuthException:
        abort(500, "Application error")
    except KeyError:
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
