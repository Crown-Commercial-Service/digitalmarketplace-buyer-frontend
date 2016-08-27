# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask_login import current_user
from flask import abort, current_app, make_response, render_template, request

from dmapiclient import APIError
from dmcontent.content_loader import ContentNotFoundError

from ...main import main
from ...helpers.shared_helpers import get_one_framework_by_status_in_order_of_preference, parse_link

from ..forms.brief_forms import BriefSearchForm

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
        brief_builder=current_app.config.get('FEATURE_FLAGS_BRIEF_BUILDER', False)
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


@main.route('/capabilities-and-rates')
def roles_and_services():
    return render_template('content/capabilities-and-rates.html')


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


@main.route('/sellers-guide')
def sellers_guide():
    return render_template('content/sellers-guide.html')


@main.route('/copyright')
def copyright():
    return render_template('content/copyright.html')


@main.route('/<framework_slug>/opportunities/<brief_id>')
def get_brief_by_id(framework_slug, brief_id):
    briefs = data_api_client.get_brief(brief_id)
    brief = briefs.get('briefs')
    if brief['status'] not in ['live', 'closed']:
        if not current_user.is_authenticated or brief['users'][0]['id'] != current_user.id:
            abort(404, "Opportunity '{}' can not be found".format(brief_id))

    if current_user.is_authenticated and current_user.role == 'supplier':
        brief_responses = data_api_client.find_brief_responses(brief_id, current_user.supplier_code)["briefResponses"]
    else:
        brief_responses = None

    brief['clarificationQuestions'] = [
        dict(question, number=index+1)
        for index, question in enumerate(brief['clarificationQuestions'])
    ]

    brief_content = content_loader.get_builder('digital-service-professionals', 'display_brief').filter(
        brief
    )
    return render_template(
        'brief.html',
        brief=brief,
        brief_responses=brief_responses,
        content=brief_content,
    )


@main.route('/<framework_slug>/opportunities')
def list_opportunities(framework_slug):
    framework = data_api_client.get_framework(framework_slug)['frameworks']
    if not framework:
        abort(404, "No framework {}".format(framework_slug))

    form = BriefSearchForm(request.args, framework=framework, data_api_client=data_api_client)
    # disabling csrf protection as this should only ever be a GET request
    del form.csrf_token
    if not form.validate():
        abort(400, "Invalid form data")

    api_result = form.get_briefs()

    briefs = api_result["briefs"]
    links = api_result["links"]

    api_prev_link_args = parse_link(links, "prev")
    prev_link_args = None
    if api_prev_link_args:
        prev_link_args = request.args.copy()
        prev_link_args.setlist("page", api_prev_link_args.get("page") or ())

    api_next_link_args = parse_link(links, "next")
    next_link_args = None
    if api_next_link_args:
        next_link_args = request.args.copy()
        next_link_args.setlist("page", api_next_link_args.get("page") or ())

    html = render_template('search/briefs.html',
                           framework=framework,
                           form=form,
                           filters=form.get_filters(),
                           filters_applied=form.filters_applied(),
                           briefs=briefs,
                           lot_names=tuple(label for id_, label in form.lot.choices),
                           prev_link_args=prev_link_args,
                           next_link_args=next_link_args,
                           briefs_count=api_result.get("meta", {}).get("total", None),
                           )
    response = make_response(html)
    if current_user.is_authenticated and current_user.has_role('buyer'):
        # Buyers can create new briefs and want to see their updates more quickly.
        response.cache_control.max_age = min(300, current_app.config['DM_DEFAULT_CACHE_MAX_AGE'])
    return response
