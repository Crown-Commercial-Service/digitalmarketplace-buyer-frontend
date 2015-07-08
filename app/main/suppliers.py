# coding=utf-8
from string import ascii_uppercase
import flask_featureflags
from app.main import main
from flask import render_template, request
from app.helpers.search_helpers import get_template_data
from app import data_api_client
import re

try:
    from urlparse import urlparse, parse_qs
except ImportError:
    from urllib.parse import urlparse, parse_qs


def process_prefix(prefix):
    if prefix == "123":  # special case
        return prefix
    if is_alpha(prefix):
        return prefix[:1].upper()
    return "A"  # default


def process_page(page):
    reg = "^[1-9]{1}$"  # valid page
    if re.search(reg, page):
        return page
    return "1"  # default


def is_alpha(character):
    reg = "^[A-Za-z]{1}$"  # valid prefix
    return re.search(reg, character)


def parse_links(links):
    pagination_links = {
        "prev": None,
        "next": None
    }

    if 'prev' in links:
        pagination_links['prev'] = parse_qs(urlparse(links['prev']).query)
    if 'next' in links:
        pagination_links['next'] = parse_qs(urlparse(links['next']).query)

    return pagination_links


@main.route('/g-cloud/suppliers')
@flask_featureflags.is_active_feature('SUPPLIER_A_TO_Z')
def suppliers_list_by_prefix():
    prefix = process_prefix(request.args.get('prefix', default='A'))
    page = process_page(request.args.get('page', default="1"))

    api_result = data_api_client.find_suppliers(prefix, page, 'gcloud')
    suppliers = api_result["suppliers"]
    links = api_result["links"]

    template_data = get_template_data(main, {
        'title': 'Digital Marketplace - Suppliers'
    })

    return render_template('suppliers_list.html',
                           suppliers=suppliers,
                           nav=ascii_uppercase,
                           count=len(suppliers),
                           prev_link=parse_links(links)['prev'],
                           next_link=parse_links(links)['next'],
                           prefix=prefix,
                           **template_data)


@main.route('/g-cloud/supplier/<supplier_id>')
@flask_featureflags.is_active_feature('SUPPLIER_A_TO_Z')
def suppliers_details(supplier_id):
    supplier = data_api_client.get_supplier(
        supplier_id=supplier_id)["suppliers"]

    template_data = get_template_data(main, {
        'title': 'Digital Marketplace - Suppliers'
    })

    first_character_of_supplier_name = supplier["name"][:1]
    if is_alpha(first_character_of_supplier_name):
        prefix = process_prefix(supplier["name"][:1])
    else:
        prefix = "123"

    return render_template(
        'suppliers_details.html',
        supplier=supplier,
        prefix=prefix,
        **template_data)
