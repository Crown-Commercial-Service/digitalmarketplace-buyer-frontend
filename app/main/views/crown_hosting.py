# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import render_template
from ...main import main


@main.route('/crown-hosting')
def index_crown_hosting():
    return render_template(
        'content/index-crown-hosting.html',
        **dict(main.config['BASE_TEMPLATE_DATA'])
    )


@main.route('/crown-hosting/framework')
def framework_crown_hosting():
    return render_template(
        'content/framework-crown-hosting.html',
        **dict(main.config['BASE_TEMPLATE_DATA'])
    )
