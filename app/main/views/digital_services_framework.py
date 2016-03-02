# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import render_template
from ...main import main


@main.route('/digital-services/framework')
def framework_digital_services():
    return render_template(
        'content/framework-digital-services.html'
    )
