# coding=utf-8
from string import ascii_uppercase
from app.main import main
from flask import render_template, request, current_app
from app.helpers.search_helpers import get_template_data, pagination, get_page_from_request
from app import data_api_client
import re
from urlparse import urlparse, parse_qs


def process_prefix(prefix):
    reg = "^[A-Za-z]{1}$"  # valid prefix
    if prefix == "other":  # special case
        return prefix
    if re.search(reg, prefix):
        return prefix[:1].upper()
    return "A"  # default


def process_page(page):
    reg = "^[1-9]{1}$"  # valid page
    if re.search(reg, page):
        return page
    return "1"  # default


def parse_links(links):
    prev_page = None
    next_page = None
    if 'prev' in links:
        prev_page = parse_qs(urlparse(links['prev']).query)
    if 'next' in links:
        next_page = parse_qs(urlparse(links['next']).query)

    return {
        "prev": prev_page,
        "next": next_page
    }

@main.route('/suppliers')
def suppliers_list_by_prefix():
    prefix = process_prefix(request.args.get('prefix', default='A'))
    page = process_page(request.args.get('page', default="1"))

    api_result = data_api_client.find_suppliers(prefix, page)
    suppliers = api_result["suppliers"]
    links = api_result["links"]

    template_data = get_template_data(main, {
        'title': 'Digital Marketplace - Suppliers'
    })
    return render_template('suppliers_list.html',
                           suppliers=suppliers,
                           nav=ascii_uppercase,
                           count=len(suppliers),
                           pagination=parse_links(links),
                           prefix=prefix,
                           **template_data)


@main.route('/supplier-details/<supplier_id>')
def suppliers_details(supplier_id):
    supplier = data_api_client.get_supplier(
        supplier_id=supplier_id)["suppliers"]
    services = data_api_client.find_services(
        supplier_id=supplier_id)["services"]

    grouped_by_lot = {
        'IaaS': [],
        'PaaS': [],
        'SaaS': [],
        'SCS': []
    }

    for service in services:
        grouped_by_lot[service['lot']].append(service)

    template_data = get_template_data(main, {
        'title': 'Digital Marketplace - Suppliers'
    })

    return render_template(
        'suppliers_details.html',
        supplier=supplier,
        services=grouped_by_lot,
        services_count=len(services),
        **template_data)
