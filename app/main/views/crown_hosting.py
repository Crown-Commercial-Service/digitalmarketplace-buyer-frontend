# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import render_template
from ...helpers.search_helpers import get_template_data
from ...main import main


@main.route('/crown-hosting')
def index_crown_hosting():
    template_data = get_template_data(main, {})
    return render_template('content/index-crown-hosting.html', **template_data)


@main.route('/crown-hosting/framework')
def framework_crown_hosting():
    template_data = get_template_data(main, {})
    return render_template(
        'content/framework-crown-hosting.html', **template_data
    )
