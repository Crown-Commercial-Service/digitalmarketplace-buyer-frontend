# coding=utf-8
from string import ascii_uppercase
from .. import main
from flask import render_template, request
from app.helpers.search_helpers import get_template_data
from ... import data_api_client


@main.route('/suppliers')
def suppliers_list_by_prefix():
    prefix = request.args.get('prefix', default='a')
    suppliers = data_api_client.get_suppliers(prefix)["suppliers"]
    template_data = get_template_data(main, {
        'title': 'Digital Marketplace - Suppliers'
    })
    return render_template('suppliers_list.html',
                           suppliers=suppliers,
                           nav=ascii_uppercase,
                           count=len(suppliers),
                           prefix=prefix,
                           **template_data)


@main.route('/suppliers/<supplier_id>')
def suppliers_details(supplier_id):
    supplier = data_api_client.get_supplier_by_id(supplier_id)["suppliers"]
    services = data_api_client.get_services_by_supplier_id(supplier_id)["services"]

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


