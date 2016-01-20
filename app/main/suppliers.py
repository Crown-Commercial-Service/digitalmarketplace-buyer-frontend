# coding=utf-8
from string import ascii_uppercase
from app.main import main
from flask import render_template, request, abort
from app.helpers.search_helpers import get_template_data
from app import data_api_client
from dmapiclient import APIError
import numbers
import re

try:
    from urlparse import urlparse, parse_qs
except ImportError:
    from urllib.parse import urlparse, parse_qs


def process_prefix(prefix=None, format='view'):
    if prefix == u"other":  # special case
        if format == 'api':
            return u"other"
        else:
            return prefix
    if is_alpha(prefix):
        return prefix[:1].upper()
    return u"A"  # default


def process_page(page):
    try:
        int(page)
        return page
    except ValueError:
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
def suppliers_list_by_prefix():
    api_prefix = process_prefix(
        prefix=request.args.get('prefix', default=u"A"),
        format='api')
    template_prefix = process_prefix(
        prefix=request.args.get('prefix', default=u"A"),
        format='view')
    page = process_page(request.args.get('page', default=u"1"))

    try:
        api_result = data_api_client.find_suppliers(api_prefix, page, 'gcloud')
        suppliers = api_result["suppliers"]
        links = api_result["links"]

        template_data = get_template_data(main, {})

        return render_template('suppliers_list.html',
                               suppliers=suppliers,
                               nav=ascii_uppercase,
                               count=len(suppliers),
                               prev_link=parse_links(links)['prev'],
                               next_link=parse_links(links)['next'],
                               prefix=template_prefix,
                               **template_data)
    except APIError as e:
        if e.status_code == 404:
            abort(404, "No suppliers for prefix {} page {}".format(api_prefix, page))
        else:
            raise e


@main.route('/g-cloud/supplier/<supplier_id>')
def suppliers_details(supplier_id):
    supplier = data_api_client.get_supplier(
        supplier_id=supplier_id)["suppliers"]

    first_character_of_supplier_name = supplier["name"][:1]
    if is_alpha(first_character_of_supplier_name):
        prefix = process_prefix(
            prefix=first_character_of_supplier_name, format='template')
    else:
        prefix = u"other"

    template_data = get_template_data(main, {})

    return render_template(
        'suppliers_details.html',
        supplier=supplier,
        prefix=prefix,
        **template_data)
