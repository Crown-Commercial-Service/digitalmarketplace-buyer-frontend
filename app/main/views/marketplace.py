# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import abort, render_template, current_app

from dmapiclient import APIError
from dmutils.content_loader import ContentNotFoundError

from ...main import main
from ...helpers.shared_helpers import get_one_framework_by_status_in_order_of_preference

from app import data_api_client, content_loader


@main.route('/')
def index():
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

    # if there is a problem with the API we should still show the home page
    except APIError:
        frameworks = []
    # if no message file is found (should never happen), throw a 500
    except ContentNotFoundError:
        current_app.logger.error(
            "contentloader.fail No message file found for framework. "
            "framework {} status {}".format(framework.get('slug'), framework.get('status')))
        abort(500)

    return render_template(
        'index.html',
        frameworks={framework['slug']: framework for framework in frameworks},
        temporary_message=temporary_message,
        **dict(main.config['BASE_TEMPLATE_DATA'])
    )


@main.route('/cookies')
def cookies():
    return render_template(
        'content/cookies.html',
        **dict(main.config['BASE_TEMPLATE_DATA'])
    )


@main.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template(
        'content/terms-and-conditions.html',
        **dict(main.config['BASE_TEMPLATE_DATA'])
    )


@main.route('/<framework_slug>/opportunities/<brief_id>')
def get_brief_by_id(framework_slug, brief_id):
    temporary_message = {}

    briefs = data_api_client.get_brief(brief_id)
    brief = briefs.get('briefs')
    if brief['status'] != 'live':
        abort(404, "Opportunity '{}' can not be found".format(brief_id))

    return render_template(
        'brief.html',
        brief=brief,
        **dict(main.config['BASE_TEMPLATE_DATA'])
    )
