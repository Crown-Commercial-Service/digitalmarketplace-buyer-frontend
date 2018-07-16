# -*- coding: utf-8 -*-
from flask import redirect

from dmutils.flask import timed_render_template as render_template

from ...main import main


@main.route('/crown-hosting')
def index_crown_hosting():
    return render_template(
        'content/index-crown-hosting.html'
    )


@main.route('/crown-hosting/framework')
def framework_crown_hosting():
    return redirect(
        'https://www.gov.uk/guidance/the-crown-hosting-data-centres-framework-on-the-digital-marketplace', 301)
