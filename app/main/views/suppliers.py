# coding=utf-8
import re

from flask import redirect, abort

from dmutils.flask import timed_render_template as render_template

from app import data_api_client
from app.main import main
from ..helpers.framework_helpers import get_framework_description


def process_prefix(prefix=None):
    if prefix == "other":  # special case
        return prefix
    if is_alpha(prefix):
        return prefix[:1].upper()
    return "A"  # default


def is_alpha(character):
    reg = "^[A-Za-z]{1}$"  # valid prefix
    return re.search(reg, character)


@main.route('/g-cloud/suppliers')
def suppliers_list_by_prefix():
    return redirect('https://www.applytosupply.digitalmarketplace.service.gov.uk/g-cloud/suppliers', 301)


@main.route('/g-cloud/supplier/<supplier_id>')
def suppliers_details(supplier_id):
    supplier = data_api_client.get_supplier(supplier_id=supplier_id)["suppliers"]

    all_frameworks = data_api_client.find_frameworks().get('frameworks')
    live_framework_names = [f['name'] for f in all_frameworks if f['status'] == 'live' and f['framework'] == 'g-cloud']

    if any(supplier.get('service_counts', {}).get(framework_name, 0) > 0 for framework_name in live_framework_names):
        first_character_of_supplier_name = supplier["name"][:1]
        if is_alpha(first_character_of_supplier_name):
            prefix = first_character_of_supplier_name.upper()
        else:
            prefix = "other"

        return render_template(
            'suppliers_details.html',
            supplier=supplier,
            prefix=prefix,
            gcloud_framework_description=get_framework_description(data_api_client, 'g-cloud'),
        )

    else:
        abort(404)
