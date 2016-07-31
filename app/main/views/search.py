# -*- coding: utf-8 -*-
import json
from flask.helpers import url_for
import os
from flask import abort, render_template, request, redirect, current_app
from app.api_client.data import DataAPIClient
from app.main.utils import get_page_list

from ...main import main
from app import search_api_client, data_api_client, content_loader


# For prototyping
from collections import namedtuple

Filter = namedtuple('Filter', 'name options')
Option = namedtuple('Option', 'name value label checked')
Badge = namedtuple('Badge', 'css_class label')
Role = namedtuple('Role', 'label')
ExtraDetail = namedtuple('ExtraDetail', 'key value')
Result = namedtuple('Result', 'title description badges roles url')


@main.route('/search/suppliers')
def supplier_search():
    sort_order = request.args.get('sort_order', 'asc')  # asc or desc
    sort_terms = request.args.getlist('sort_term')
    keyword = request.args.get('keyword', None)

    if not sort_terms:  # Sort by A-Z for default
        sort_terms = ['name']

    role_list_from_request = request.args.getlist('role')
    response = DataAPIClient().get_roles()
    role_list = []
    role_list_plain = []
    role_filters = []
    for role_row in response['roles']:
        role = role_row['role'].replace('Senior ', '').replace('Junior ', '')  # Mind the white space after Junior
        if role not in role_list_plain:
            # Example: Option('category', 'pm', 'Product Management', False),
            option = Option('role', role, role, role in role_list_from_request)
            role_list.append(option)
            role_list_plain.append(role)

            if role in role_list_from_request:
                role_filters.append(role_row['role'])

    filters = [
        Filter('Capabilities', role_list),
        ]

    #    results = [
    #        Result(
    #            'PublicNet',
    #            'PublicNet is a wholly owned Indigenous non-profit company dedicated to'
    #            'providing specialised Business Analysis services for the public and community sector.',
    #            [Badge('badge-security', 'Security clearance'), Badge('badge-tick', 'ABC compliant')],
    #            [Category('Business Analysis'), Category('User Research')],
    #            [ExtraDetail('Location', 'Sydney'),
    #             ExtraDetail('Able to work interstate', 'Yes'),
    #             ExtraDetail('Indigenous owned', 'Yes'),
    #             ExtraDetail('Employs Indigenous Australians', 'Yes'),
    #             ExtraDetail('Uses Indigenous Providers', 'Yes'),
    #             ExtraDetail('Worked with government before', 'Yes'),
    #             ExtraDetail('Size of company', '20 people')],
    #            '/'
    #        ),
    #        Result(
    #            'VX Productions',
    #            'VX is a leading provider of web design and hosting solutions.',
    #            [Badge('badge-tick', 'XYZ compliant')],
    #            [Category('Delivery Management and Agile Coaching')],
    #            [ExtraDetail('Location', 'Sydney'), ExtraDetail('Able to work interstate', 'Yes')],
    #            '/'
    #        ),
    #    ]

    #    role_queries = []
    #    for role in role_list_from_request:
    #        role_queries.append({
    #            "term": {
    #                "prices.serviceRole.role": role
    #            }
    #        })

    sort_queries = []
    allowed_sort_terms = ['name']  # Limit what can be sorted
    for sort_term in sort_terms:
        if sort_term in allowed_sort_terms:
            if sort_term == 'name':  # Use 'name' in url to keep it clean but query needs to search on not analyzed.
                sort_term = 'name.not_analyzed'

            sort_queries.append({
                sort_term: {"order": sort_order, "mode": "min"}
            })

    if role_list_from_request:
        query = {
            "query": {
                "filtered": {
                    "query": {
                        "match_all": {}
                    },
                    "filter": {
                        "terms": {"prices.serviceRole.role": role_filters},
                        }
                }
            },
            "sort": sort_queries,
            }

    elif keyword:
        query = {
            "query": {
                "wildcard": {
                    "name": {
                        "value": '*' + keyword + '*'
                    }
                }
            },
            "sort": sort_queries,
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
    size = 10  # Number of results per page
    results_from = (page * size) - size

    params = {
        'from': results_from,
        'size': size
    }

    response = DataAPIClient().find_suppliers(data=query, params=params)

    results = []
    for supplier in response['hits']['hits']:
        details = supplier['_source']

        supplier_roles = []
        supplier_roles_plain = []
        for price in details['prices']:
            # Mind the white space after Junior
            role = price['serviceRole']['role'].replace('Senior ', '').replace('Junior ', '')
            if role not in supplier_roles_plain:
                supplier_roles.append(Role(role))
                supplier_roles_plain.append(role)

        result = Result(
            details['name'],
            details['summary'],
            [Badge('badge-security', 'Security clearance'), Badge('badge-tick', 'ABC compliant')],
            sorted(supplier_roles),
            url_for('.get_supplier', code=details['code']))

        results.append(result)

    num_results = response['hits']['total']
    results_to = num_results if num_results < (page * size) else (page * size)

    pages = get_page_list(size, num_results, page)

    return render_template(
        'search_suppliers.html',
        title='Supplier Catalogue',
        search_url=url_for('.supplier_search'),
        search_keywords='',
        filters=filters,
        num_results=num_results,
        results=results,
        results_from=results_from + 1,
        results_to=results_to,
        pages=pages,
        page=page,
        num_pages=pages[-1],
        role_list_from_request=role_list_from_request,
        sort_order=sort_order,
        sort_terms=sort_terms,
        sort_term_name_label='A to Z' if sort_order == 'asc' else 'Z to A',
        keyword=keyword,
        )
