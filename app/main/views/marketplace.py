# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import abort, render_template, current_app

from dmapiclient import APIError
from dmutils.content_loader import ContentNotFoundError

from ...main import main
from ...helpers.shared_helpers import get_one_framework_by_status_in_order_of_preference
from ...helpers.search_helpers import get_template_data

from app import data_api_client, content_loader


@main.route('/')
def index():
    template_data = get_template_data(main, {})
    temporary_message = {}

    try:
        frameworks = data_api_client.find_frameworks().get('frameworks')
        framework = get_one_framework_by_status_in_order_of_preference(
            frameworks,
            ['open', 'coming', 'pending']
        )

        if framework is not None:
            content_loader.load_messages(framework.get('slug'), ['homepage-sidebar'])
            temporary_message = content_loader.get_message(
                framework.get('slug'),
                'homepage-sidebar',
                framework.get('status')
            )

    # if no framework is found (should never happen), ditch the message and load the page
    except APIError:
        pass
    # if no message file is found (should never happen), throw a 500
    except ContentNotFoundError:
        current_app.logger.error(
            "contentloader.fail No message file found for framework. "
            "framework {} status {}".format(framework.get('slug'), framework.get('status')))
        abort(500)

    return render_template(
        'index.html',
        temporary_message=temporary_message,
        **template_data
    )


@main.route('/cookies')
def cookies():
    template_data = get_template_data(main, {})
    return render_template(
        'content/cookies.html', **template_data
    )


@main.route('/terms-and-conditions')
def terms_and_conditions():
    template_data = get_template_data(main, {})
    return render_template(
        'content/terms-and-conditions.html', **template_data
    )
