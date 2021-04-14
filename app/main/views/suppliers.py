# coding=utf-8
import re
from string import ascii_uppercase

from flask import request, abort

from dmapiclient import APIError

from dmutils.flask import timed_render_template as render_template

from app import data_api_client
from app.main import main
from ..helpers.shared_helpers import parse_link
from ..helpers.framework_helpers import get_framework_description


def process_prefix(prefix=None):
    if prefix == u"other":  # special case
        return prefix
    if is_alpha(prefix):
        return prefix[:1].upper()
    return u"A"  # default


def is_alpha(character):
    reg = "^[A-Za-z]{1}$"  # valid prefix
    return re.search(reg, character)


@main.route('/g-cloud/suppliers')
def suppliers_list_by_prefix():
    prefix = process_prefix(prefix=request.args.get('prefix', default=u"A"))
    page = request.args.get('page', default=1, type=int)

    try:
        api_result = data_api_client.find_suppliers(prefix, page, 'g-cloud')
        suppliers = api_result["suppliers"]
        links = api_result["links"]

        return render_template('suppliers_list.html',
                               suppliers=suppliers,
                               nav=ascii_uppercase,
                               count=len(suppliers),
                               prev_link=parse_link(links, 'prev'),
                               next_link=parse_link(links, 'next'),
                               prefix=prefix,
                               gcloud_framework_description=get_framework_description(data_api_client, 'g-cloud'),
                               )
    except APIError as e:
        if e.status_code == 404:
            abort(404, "No suppliers for prefix {} page {}".format(prefix, page))
        else:
            raise e


@main.route('/g-cloud/supplier/<supplier_id>')
def suppliers_details(supplier_id):
    supplier = data_api_client.get_supplier(supplier_id=supplier_id)["suppliers"]

    all_frameworks = data_api_client.find_frameworks().get('frameworks')
    live_framework_names = [f['name'] for f in all_frameworks if f['status'] == 'live' and f['framework'] == 'g-cloud']

    if any(supplier.get('service_counts', {}).get(framework_name, 0) > 0 for framework_name in live_framework_names):
        first_character_of_supplier_name = supplier["name"][:1]
        if is_alpha(first_character_of_supplier_name):
            prefix = process_prefix(prefix=first_character_of_supplier_name)
        else:
            prefix = u"other"

        return render_template(
            'suppliers_details.html',
            supplier=supplier,
            prefix=prefix,
            gcloud_framework_description=get_framework_description(data_api_client, 'g-cloud'),
        )

    else:
        abort(404)
