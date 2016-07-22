# -*- coding: utf-8 -*-
import json
import os
from flask import abort, render_template, request, redirect, current_app
from app.api_client.data import DataAPIClient

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
    filters = [
        Filter('Capabilities', [
            Option('category', 'pm', 'Product Management', False),
            Option('category', 'ba', 'Business Analysis', False),
            Option('category', 'dm', 'Delivery Management and Agile Coaching', False),
            Option('category', 'ur', 'User Research', False),
            Option('category', 'sd', 'Service Design and Interaction Design', False),
            Option('category', 'sd', 'Service Design and Interaction Design', False),
            Option('category', 'perf', 'Performance and Web Analytics', False),
            Option('category', 'acc', 'Inclusive Design and Accessibility', False),
            Option('category', 'dta', 'Digital Transformation Advisors', False),
        ]),

        # Roles are deprecated
        #        Filter('Roles', [
        #            Option('role', 'tl', 'Technical Lead', False),
        #            Option('role', 'dev', 'Developer', False),
        #            Option('role', 'hck', 'Ethical Hacker', False),
        #            Option('role', 'ops', 'Web Devops Engineer', False),
        #        ])

    ]
    results = [
        Result(
            'PublicNet',
            'PublicNet is a wholly owned Indigenous non-profit company dedicated to'
            'providing specialised Business Analysis services for the public and community sector.',
            [Badge('badge-security', 'Security clearance'), Badge('badge-tick', 'ABC compliant')],
            [Category('Business Analysis'), Category('User Research')],
            [ExtraDetail('Location', 'Sydney'),
             ExtraDetail('Able to work interstate', 'Yes'),
             ExtraDetail('Indigenous owned', 'Yes'),
             ExtraDetail('Employs Indigenous Australians', 'Yes'),
             ExtraDetail('Uses Indigenous Providers', 'Yes'),
             ExtraDetail('Worked with government before', 'Yes'),
             ExtraDetail('Size of company', '20 people')],
            '/'
        ),
        Result(
            'VX Productions',
            'VX is a leading provider of web design and hosting solutions.',
            [Badge('badge-tick', 'XYZ compliant')],
            [Category('Delivery Management and Agile Coaching')],
            [ExtraDetail('Location', 'Sydney'), ExtraDetail('Able to work interstate', 'Yes')],
            '/'
        ),
    ]

    return render_template(
        'search_suppliers.html',
        title='Supplier Catalogue',
        search_url='/search/suppliers',
        search_keywords='',
        filters=filters,
        num_results=len(results),
        results=results,
        results_from='0',
        results_to=len(results)
    )
