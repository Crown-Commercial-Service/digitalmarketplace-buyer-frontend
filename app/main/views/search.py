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
Category = namedtuple('Category', 'label')
ExtraDetail = namedtuple('ExtraDetail', 'key value')
Result = namedtuple('Result', 'title description badges categories extra_details url')


@main.route('/search/suppliers')
def supplier_search():
    category_list = request.args.getlist('category')
    response = DataAPIClient().get_roles()
    capabilities = []
    capabilities_plain = []
    for role in response['roles']:
        if role['category'] not in capabilities_plain:
            # Example: Option('category', 'pm', 'Product Management', False),
            option = Option('category', role['category'], role['category'], role['category'] in category_list)
            capabilities.append(option)
            capabilities_plain.append(role['category'])

    filters = [
        Filter('Capabilities', capabilities),
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

    category_queries = []
    for category in category_list:
        category_queries.append({
            "query": {
                "query_string": {
                    "default_field": "prices.serviceRole.category",
                    "default_operator": "AND",
                    "query": category
                }
            }
        })

    if category_list:
        query = {
            "query": {
                "filtered": {
                    "query": {
                        "match_all": {}
                    },
                    "filter": {
                            "or": category_queries,
                    }
                }
            }
        }

    else:
        query = {
            "query": {
                "match_all": {
                }
            }
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

        categories = []
        categories_plain = []
        for price in details['prices']:
            ca = price['serviceRole']['category']
            if ca not in categories_plain:
                categories.append(Category(ca))
                categories_plain.append(ca)

        result = Result(
            details['name'],
            details['summary'],
            [Badge('badge-security', 'Security clearance'), Badge('badge-tick', 'ABC compliant')],
            categories,
            [ExtraDetail('Location', '%s, %s' % (details['address']['suburb'], details['address']['state'])),
             ],
            url_for('.get_supplier', code=details['code']))

        results.append(result)

    num_results = response['_shards']['total']
    results_to = num_results if num_results < (page * size) else (page * size)

    pages = get_page_list(size, num_results, page)

    return render_template(
        'search_suppliers.html',
        title='Supplier Catalogue',
        search_url='/search/suppliers',
        search_keywords='',
        filters=filters,
        num_results=num_results,
        results=results,
        results_from=results_from + 1,
        results_to=results_to,
        pages=pages,
        page=page,
        num_pages=pages[-1],
        category_list=category_list
    )

