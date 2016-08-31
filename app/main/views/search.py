# -*- coding: utf-8 -*-
from collections import defaultdict
import json
from flask.helpers import url_for
import os
from flask import abort, render_template, request, redirect, current_app
from app.api_client.data import DataAPIClient
from app.main.utils import get_page_list

from ...main import main
from app import cache


# For prototyping
from collections import namedtuple

Filter = namedtuple('Filter', 'name options')
Option = namedtuple('Option', 'name value label checked')
Badge = namedtuple('Badge', 'css_class label')
Role = namedtuple('Role', 'label')
ExtraDetail = namedtuple('ExtraDetail', 'key value')
Result = namedtuple('Result', 'title description badges roles url')

SUPPLIER_RESULTS_PER_PAGE = 50


def normalise_role(role_name):
    return role_name.replace('Senior ', '').replace('Junior ', '')  # Mind the white space after Junior


@cache.cached(timeout=300, key_prefix='get_all_roles')
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


@main.route('/search/sellers')
def supplier_search():
    sort_order = request.args.get('sort_order', 'asc')  # asc or desc
    sort_terms = request.args.getlist('sort_term')
    keyword = request.args.get('keyword', None)

    if not sort_terms:  # Sort by A-Z for default
        sort_terms = ['name']

    data_api_client = DataAPIClient()

    selected_roles = set(request.args.getlist('role'))
    roles, raw_role_data = get_all_roles(data_api_client)

    sidepanel_roles = [Option('role', role, role, role in selected_roles) for role in roles]
    sidepanel_filters = [
        Filter('Capabilities', sidepanel_roles),
    ]

    sort_queries = []
    allowed_sort_terms = set(('name',))  # Limit what can be sorted
    for sort_term in sort_terms:
        if sort_term in allowed_sort_terms:
            if sort_term == 'name':  # Use 'name' in url to keep it clean but query needs to search on not analyzed.
                sort_term = 'name.not_analyzed'

            sort_queries.append({
                sort_term: {"order": sort_order, "mode": "min"}
            })

    if selected_roles:
        filters = []
        for role in selected_roles:
            filters.extend(raw_role_data[role])
        query = {
            "query": {
                "filtered": {
                    "query": {
                        "match_all": {}
                    },
                    "filter": {
                        "terms": {"prices.serviceRole.role": filters},
                        }
                }
            },
            "sort": sort_queries,
            }
    elif keyword:
        query = {
            "query": {
                "match_phrase_prefix": {
                    "name": keyword
                }
            },
            "sort": sort_queries
        }
    else:
        query = {
            "query": {
                "match_all": {
                }
            },
            "sort": sort_queries
        }

    page = int(request.args.get('page', 1))
    results_from = (page - 1) * SUPPLIER_RESULTS_PER_PAGE

    find_suppliers_params = {
        'from': results_from,
        'size': SUPPLIER_RESULTS_PER_PAGE
    }
    response = data_api_client.find_suppliers(data=query, params=find_suppliers_params)

    results = []
    for supplier in response['hits']['hits']:
        details = supplier['_source']

        supplier_roles = []
        seen_supplier_roles = set()
        for price in details['prices']:
            role = normalise_role(price['serviceRole']['role'])
            if role not in seen_supplier_roles:
                supplier_roles.append(Role(role))
                seen_supplier_roles.add(role)

        result = Result(
            details['name'],
            details['summary'],
            [],
            sorted(supplier_roles),
            url_for('.get_supplier', code=details['code']))

        results.append(result)

    num_results = response['hits']['total']
    results_to = min(num_results, page * SUPPLIER_RESULTS_PER_PAGE)

    pages = get_page_list(SUPPLIER_RESULTS_PER_PAGE, num_results, page)

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
        hide_suppliers_name_search=current_app.config.get('FEATURE_FLAGS_HIDE_SUPPLIERS_NAME_SEARCH', False)
        )
