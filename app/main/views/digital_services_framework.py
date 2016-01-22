# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import render_template
from ...helpers.search_helpers import get_template_data
from ...main import main


@main.route('/digital-services/framework')
def framework_digital_services():
    template_data = get_template_data(main, {})
    return render_template(
        'content/framework-digital-services.html', **template_data
    )
