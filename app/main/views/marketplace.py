# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import abort, current_app, render_template, request

from dmapiclient import APIError
from dmcontent.content_loader import ContentNotFoundError

from ...main import main
from ...helpers.shared_helpers import get_one_framework_by_status_in_order_of_preference, parse_link

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
        temporary_message=temporary_message
    )


# URL to see raw template for frontend developers
@main.route('/templates/<template_slug>')
def my_template(template_slug):
    return render_template('%s.html' % template_slug)


@main.route('/cookies')
def cookies():
    return render_template('content/cookies.html')


@main.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template('content/terms-and-conditions.html')


@main.route('/ideation')
def ideation():
    return render_template('content/ideation.html')


@main.route('/new-seller')
def new_seller():
    return render_template('content/new-seller.html')


@main.route('/pitch')
def pitch():
    return render_template('content/pitch.html')


@main.route('/about-us')
def about_us():
    return render_template('content/about-us.html')


@main.route('/roles-and-services')
def roles_and_services():
    return render_template('content/roles-and-services.html')


@main.route('/contact-us')
def contact_us():
    return render_template('content/contact-us.html')


@main.route('/terms-of-use')
def terms_of_use():
    return render_template('content/terms-of-use.html')


@main.route('/privacy-policy')
def privacy_policy():
    return render_template('content/privacy-policy.html')

@main.route('/disclaimer')
def disclaimer():
    return render_template('content/disclaimer.html')

@main.route('/buyers-guide')
def buyers_guide():
    return render_template('content/buyers-guide.html')


@main.route('/<framework_slug>/opportunities/<brief_id>')
def get_brief_by_id(framework_slug, brief_id):
    briefs = data_api_client.get_brief(brief_id)
    brief = briefs.get('briefs')
    if brief['status'] not in ['live', 'closed']:
        abort(404, "Opportunity '{}' can not be found".format(brief_id))

    brief['clarificationQuestions'] = [
        dict(question, number=index+1)
        for index, question in enumerate(brief['clarificationQuestions'])
    ]

    brief_content = content_loader.get_builder('digital-outcomes-and-specialists', 'display_brief').filter(
        brief
    )
    return render_template(
        'brief.html',
        brief=brief,
        content=brief_content
    )


@main.route('/<framework_slug>/opportunities')
def list_opportunities(framework_slug):
    page = request.args.get('page', default=1, type=int)
    framework = data_api_client.get_framework(framework_slug)['frameworks']

    if not framework:
        abort(404, "No framework {}".format(framework_slug))

    api_result = data_api_client.find_briefs(status='live,closed', framework=framework_slug, page=page)

    briefs = api_result["briefs"]
    links = api_result["links"]

    return render_template('briefs_catalogue.html',
                           framework=framework,
                           lot_names=[lot['name'] for lot in framework['lots'] if lot['allowsBrief']],
                           briefs=briefs,
                           prev_link=parse_link(links, 'prev'),
                           next_link=parse_link(links, 'next')
                           )
