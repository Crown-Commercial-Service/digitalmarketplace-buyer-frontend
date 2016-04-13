# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from app import data_api_client

from flask import abort, render_template
from ...helpers.buyers_helpers import get_framework_and_lot
from ...main import main


@main.route('/buyers/frameworks/<framework_slug>/requirements/user-research-studios', methods=['GET'])
def studios_start_page(framework_slug):
    framework = data_api_client.get_framework(framework_slug)['frameworks']
    if framework['status'] != 'live':
        abort(404)

    return render_template(
        "buyers/studios_start_page.html"
    ), 200


@main.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>', methods=['GET'])
def info_page_for_starting_a_brief(framework_slug, lot_slug):
    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)
    return render_template(
        "buyers/start_brief_info.html",
        framework=framework,
        lot=lot
    ), 200
