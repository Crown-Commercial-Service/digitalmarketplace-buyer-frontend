# coding=utf-8
from string import ascii_uppercase
from app.main import main
from flask import render_template, request, abort
from app import data_api_client
from dmapiclient import APIError
from ...helpers.shared_helpers import parse_link
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


def is_alpha(character):
    reg = "^[A-Za-z]{1}$"  # valid prefix
    return re.search(reg, character)


@main.route('/g-cloud/suppliers')
def suppliers_list_by_prefix():
    api_prefix = process_prefix(
        prefix=request.args.get('prefix', default=u"A"),
        format='api')
    template_prefix = process_prefix(
        prefix=request.args.get('prefix', default=u"A"),
        format='view')
    page = request.args.get('page', default=1, type=int)

    try:
        api_result = data_api_client.find_suppliers(api_prefix, page, 'g-cloud')
        suppliers = api_result["suppliers"]
        links = api_result["links"]

        return render_template('suppliers_list.html',
                               suppliers=suppliers,
                               nav=ascii_uppercase,
                               count=len(suppliers),
                               prev_link=parse_link(links, 'prev'),
                               next_link=parse_link(links, 'next'),
                               prefix=template_prefix
                               )
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

    return render_template(
        'suppliers_details.html',
        supplier=supplier,
        prefix=prefix
    )
