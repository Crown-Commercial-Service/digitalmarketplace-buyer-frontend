# -*- coding: utf-8 -*-
from collections import defaultdict
import json
from flask.helpers import url_for
import os
from flask import abort, render_template, request, redirect, current_app, jsonify
import flask_featureflags as feature
from app.api_client.data import DataAPIClient
from app.main.utils import get_page_list
from react.render import render_component
from app.helpers.shared_helpers import request_wants_json

from ...main import main
from app import cache

import dmapiclient

# from ... import data_api_client as real_data_api_client
from collections import OrderedDict as od


# For prototyping
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, as_completed


Filter = namedtuple('Filter', 'name options')
Option = namedtuple('Option', 'name value label checked')
Badge = namedtuple('Badge', 'css_class label')
Role = namedtuple('Role', 'label')
ExtraDetail = namedtuple('ExtraDetail', 'key value')
Result = namedtuple('Result', 'title description badges roles url')

SUPPLIER_RESULTS_PER_PAGE = 10


def normalise_role(role_name):
    return role_name.replace('Senior ', '').replace('Junior ', '')  # Mind the white space after Junior


def get_all_roles(data_api_client):
    """
    Returns a two-valued tuple:
    1. A set containing all role strings
    2. A map from role strings to original role data

    The original role data is actually a list of dicts because of folding Senior/Junior roles into one role.
    """
    response = data_api_client.get_roles()

    roles = set()
    raw_role_data = defaultdict(list)
    for role_data in response['roles']:
        role = normalise_role(role_data['role'])
        raw_role_data[role].append(role_data)
        roles.add(role)
    return roles, raw_role_data


def get_all_domains(data_api_client):
    return [_['name'] for _ in data_api_client.req.get_domains()['domains']]


SELLER_TYPES = od([
    ('Start up', 'start_up'),
    ('SME', 'sme'),
    ('Not-for-profit / social enterprise', 'nfp_social_enterprise'),
    ('Regional', 'regional'),
    ('Australian disability enterprise', 'disability'),
    ('Indigenous business', 'indigenous'),
    ('Recruiter', 'recruiter')
])


def to_seller_type_key(s):
    if s in SELLER_TYPES:
        return SELLER_TYPES[s]
    elif s in list(SELLER_TYPES.values()):
        return s
    else:
        raise ValueError('bad param')


@main.route('/search/sellers')
def supplier_search():
    DOMAINS_SEARCH = feature.is_active('DOMAINS_SEARCH')

    sort_by = request.args.get('sort_by', 'a-z')
    sort_order = request.args.get('sort_order', 'asc')
    if sort_order not in ('asc', 'desc'):
        abort(400, 'Invalid sort_order: {}'.format(sort_order))
    sort_terms = request.args.getlist('sort_term')
    keyword = request.args.get('keyword', None)

    selected_roles = set(request.args.getlist('role'))
    selected_seller_types = set(request.args.getlist('type'))

    selected_seller_types_keys = [
        to_seller_type_key(x)
        for x
        in selected_seller_types
    ]

    if not sort_terms:  # Sort by A-Z for default
        sort_terms = ['name']

    data_api_client = DataAPIClient()
    real_data_api_client = dmapiclient.DataAPIClient()
    real_data_api_client.init_app(current_app)

    if DOMAINS_SEARCH:
        roles = get_all_domains(data_api_client)
    else:
        roles, raw_role_data = get_all_roles(data_api_client)

    role_filters = {role: role in selected_roles for role in roles}

    sort_queries = []

    allowed_sort_terms = set(('name',))  # Limit what can be sorted

    for sort_term in sort_terms:
        if sort_term in allowed_sort_terms:
            if sort_term == 'name':  # Use 'name' in url to keep it clean but query needs to search on not analyzed.
                sort_term = 'name.not_analyzed'

            spec = {"order": sort_order, "mode": "min"}

            if sort_by:
                spec['sort_by'] = sort_by

            sort_queries.append({
                sort_term: spec
            })
        else:
            abort(400, 'Invalid sort_term: {}'.format(sort_term))

    query_contents = {}
    filter_terms = {}

    product_search_parameters = dict(
        sort_dir=sort_order,
        seller_types=selected_seller_types_keys,
        search_term=keyword,
        domains=list(selected_roles)
    )

    if selected_roles:
        if DOMAINS_SEARCH:
            for each in selected_roles:
                if each not in roles:
                    abort(400, 'Invalid role: {}'.format(each))
            filter_terms = {"domains.assessed": list(selected_roles)}
        else:
            filters = []
            for role in selected_roles:
                if role in raw_role_data:
                    filters.extend(raw_role_data[role])
                else:
                    abort(400, 'Invalid role: {}'.format(role))
            filter_terms = {"prices.serviceRole.role": filters}

    if selected_seller_types:
        filter_terms['seller_types'] = list(selected_seller_types_keys)

    if filter_terms:
        query_contents['filtered'] = {
            "query": {
                "match_all": {}
            },
            "filter": {
                "terms": filter_terms,
            }
        }

    if keyword:
        query_contents['match_phrase_prefix'] = {
            "name": keyword
        }
    else:
        query_contents['match_all'] = {}

    query = {
        "query": query_contents,
        "sort": sort_queries
    }

    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        abort(400, 'Invalid page number: {}'.format(request.args['page']))
    results_from = (page - 1) * SUPPLIER_RESULTS_PER_PAGE

    page_params = {
        'from': results_from,
        'size': SUPPLIER_RESULTS_PER_PAGE
    }

    query.update(product_search_parameters)

    products_requester = real_data_api_client.req.products().search()
    casestudies_requester = real_data_api_client.req.casestudies().search()

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures_to_result = {
            executor.submit(
                data_api_client.find_suppliers,
                data=query,
                params=page_params): 'suppliers',
            executor.submit(
                products_requester.get,
                data=query,
                params=page_params): 'products',
            executor.submit(
                casestudies_requester.get,
                data=query,
                params=page_params): 'casestudies'
        }

        results = {}

        for future in as_completed(futures_to_result):
            results[futures_to_result[future]] = future.result()

    response = results['suppliers']
    products_response = results['products']
    casestudies_response = results['casestudies']

    results = []

    for supplier in response['hits']['hits']:
        details = supplier['_source']

        if DOMAINS_SEARCH:
            tags = [Role(d) for d in details['domains']['assessed']]
        else:
            supplier_roles = []
            seen_supplier_roles = set()
            if details.get('prices'):
                for price in details['prices']:
                    role = normalise_role(price['serviceRole']['role'])
                    if role not in seen_supplier_roles:
                        supplier_roles.append(Role(role))
                        seen_supplier_roles.add(role)
            tags = supplier_roles

        if feature.is_active('SEARCH'):
            domains = details['domains']

            tags = domains['assessed'] + domains['unassessed']

            services = {}
            for tag in sorted(tags):
                services[tag] = True

            result = {
                'title': details['name'],
                'description': details['summary'],
                'link': url_for('.get_supplier', code=details['code']),
                'services': services,
                'products': details['products'],
                'recruiter_info': details['recruiter_info'],
                'badges': details.get('seller_type', {})
            }
        else:
            result = Result(
                details['name'],
                details['summary'],
                [],
                sorted(tags),
                url_for('.get_supplier', code=details['code']))

        results.append(result)

    num_results = response['hits']['total']
    results_to = min(num_results, page * SUPPLIER_RESULTS_PER_PAGE)

    pages = get_page_list(SUPPLIER_RESULTS_PER_PAGE, num_results, page)

    seller_type_filters = {st: to_seller_type_key(st) in selected_seller_types_keys for st in SELLER_TYPES.keys()}

    sidepanel_roles = [Option('role', role, role, role in selected_roles) for role in roles]
    sidepanel_filters = [
        Filter('Capabilities', sidepanel_roles),
    ]

    products_results = []

    for p in products_response['hits']['hits']:
        details = p['_source']

        domains = details['supplier']['domains']

        tags = domains['assessed'] + domains['unassessed']

        services = {}
        for tag in sorted(tags):
            services[tag] = True

        result = {
            'title': details['name'],
            'description': details['summary'],
            'link': details['website'],
            'services': services,
            'badges': details['supplier'].get('seller_type', {})
        }

        products_results.append(result)

    num_products_results = products_response['hits']['total']

    casestudies_results = []

    for p in casestudies_response['hits']['hits']:
        details = p['_source']

        domains = details['supplier']['domains']

        tags = domains['assessed'] + domains['unassessed']

        services = {}
        for tag in sorted(tags):
            services[tag] = True

        result = {
            'title': details['title'],
            'description': details.get('approach', ''),
            'link': url_for('.get_supplier_case_study', casestudy_id=details['id']),
            'services': services,
            'badges': details['supplier'].get('seller_type', {})
        }

        casestudies_results.append(result)

    num_casestudies_results = casestudies_response['hits']['total']

    def get_pagination(result_count):
        pages = get_page_list(SUPPLIER_RESULTS_PER_PAGE, result_count, page)

        return {
            'pages': pages,
            'page': page,
            'pageCount': pages[-1],
            'total': result_count
        }

    if feature.is_active('SEARCH'):
        props = {
            'form_options': {
                'action': url_for('.supplier_search')
            },
            'search': {
                'results': results[:SUPPLIER_RESULTS_PER_PAGE],
                'products': products_results[:SUPPLIER_RESULTS_PER_PAGE],
                'casestudies': casestudies_results[:SUPPLIER_RESULTS_PER_PAGE],
                'keyword': keyword,
                'sort_by': sort_by,
                'view': request.args.get('view', 'sellers'),
                'role': role_filters,
                'type': seller_type_filters
            },
            'pagination': {
                'sellers': get_pagination(num_results),
                'products': get_pagination(num_products_results),
                'casestudies': get_pagination(num_casestudies_results)
            },
            'basename': url_for('.supplier_search')
        }

        if request_wants_json():
            return jsonify(dict(props))
        else:
            component = render_component('bundles/Search/SearchWidget.js', props)
            return render_template(
                '_react.html',
                component=component,
                breadcrumb_items=[
                    {'link': url_for('main.index'), 'label': 'Home'},
                    {'label': 'Sellers catalogue'}
                ]
            )

    return render_template(
        'search_sellers.html',
        title='Supplier Catalogue',
        search_url=url_for('.supplier_search'),
        search_keywords='',
        sidepanel_filters=sidepanel_filters,
        num_results=num_results,
        results=results,
        results_from=results_from + 1,
        results_to=results_to,
        pages=pages,
        page=page,
        num_pages=pages[-1],
        selected_roles=selected_roles,
        sort_order=sort_order,
        sort_terms=sort_terms,
        sort_term_name_label='A to Z' if sort_order == 'asc' else 'Z to A',
        keyword=keyword,
        )
