# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from app import data_api_client

from flask import render_template
from ...helpers.buyers_helpers import get_framework_and_lot, count_suppliers_on_lot
from ...main import main


@main.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>', methods=['GET'])
def info_page_for_starting_a_brief(framework_slug, lot_slug):
    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)
    print("LOT: {}".format(lot))
    print("FRAMEWORK: {}".format(framework))
    return render_template(
        "buyers/start_brief_info.html",
        framework=framework,
        lot=lot,
        supplier_count=count_suppliers_on_lot(framework, lot)
    ), 200
