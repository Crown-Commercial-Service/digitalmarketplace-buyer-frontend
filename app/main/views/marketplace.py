# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask_login import current_user
from flask import abort, current_app, render_template, request

from dmapiclient import APIError
from dmcontent.content_loader import ContentNotFoundError

from ...main import main
from ..helpers.shared_helpers import (
    get_one_framework_by_status_in_order_of_preference,
    parse_link,
    count_brief_responses_by_size
)
from ..helpers.framework_helpers import get_latest_live_framework, get_framework_description

from ..forms.brief_forms import BriefSearchForm

from app import data_api_client, content_loader

ALL_BRIEF_RESPONSE_STATUSES = ['draft', 'submitted', 'pending-awarded', 'awarded']
COMPLETED_BRIEF_RESPONSE_STATUSES = ['submitted', 'pending-awarded', 'awarded']
PUBLISHED_BRIEF_STATUSES = ['live', 'withdrawn', 'closed', 'awarded']


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

    # Capture the slug for the most recent live framework. There will only be multiple if currently transitioning
    # between frameworks and more than one has a `live` status.
    dos_framework = get_latest_live_framework(frameworks, 'digital-outcomes-and-specialists')

    return render_template(
        'index.html',
        dos_slug=dos_framework['slug'] if dos_framework else None,
        frameworks={framework['slug']: framework for framework in frameworks},
        temporary_message=temporary_message,
        gcloud_framework_description=get_framework_description(data_api_client, 'g-cloud'),
    )


@main.route('/cookies')
def cookies():
    return render_template('content/cookies.html')


@main.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template('content/terms-and-conditions.html')


@main.route('/<framework_framework>/opportunities/<brief_id>')
def get_brief_by_id(framework_framework, brief_id):
    briefs = data_api_client.get_brief(brief_id)
    brief = briefs.get('briefs')

    if brief['status'] not in PUBLISHED_BRIEF_STATUSES or brief['frameworkFramework'] != framework_framework:
        abort(404, "Opportunity '{}' can not be found".format(brief_id))

    brief_responses = data_api_client.find_brief_responses(
        brief_id=brief_id,
        status=",".join(ALL_BRIEF_RESPONSE_STATUSES)
    ).get('briefResponses')

    winning_response = None
    if brief['status'] == 'awarded':
        winning_response = next(response for response in brief_responses if response["id"] == brief[
            'awardedBriefResponseId'
        ])

    started_brief_responses = [response for response in brief_responses if response['status'] == 'draft']
    completed_brief_responses = [
        response for response in brief_responses if response['status'] in COMPLETED_BRIEF_RESPONSE_STATUSES
    ]

    # Counts for application statistics
    sme, large = ['micro', 'small', 'medium'], ['large']
    started_sme_responses_count = count_brief_responses_by_size(started_brief_responses, sme)
    started_large_responses_count = count_brief_responses_by_size(started_brief_responses, large)
    completed_sme_responses_count = count_brief_responses_by_size(completed_brief_responses, sme)
    completed_large_responses_count = count_brief_responses_by_size(completed_brief_responses, large)

    if brief['status'] not in PUBLISHED_BRIEF_STATUSES or brief['frameworkFramework'] != framework_framework:
        abort(404, "Opportunity '{}' can not be found".format(brief_id))
    try:
        has_supplier_responded_to_brief = (
            current_user.supplier_id in [
                res['supplierId'] for res in brief_responses if res["status"] in COMPLETED_BRIEF_RESPONSE_STATUSES
            ]
        )
    except AttributeError:
        has_supplier_responded_to_brief = False

    brief['clarificationQuestions'] = [
        dict(question, number=index+1)
        for index, question in enumerate(brief['clarificationQuestions'])
    ]

    brief_content = content_loader.get_manifest(brief['frameworkSlug'], 'display_brief').filter(brief)

    return render_template(
        'brief.html',
        brief=brief,
        completed_responses_stats={
            'sme_count': completed_sme_responses_count,
            'large_count': completed_large_responses_count,
            'total': completed_sme_responses_count + completed_large_responses_count
        },
        content=brief_content,
        has_supplier_responded_to_brief=has_supplier_responded_to_brief,
        started_responses_stats={
            'sme_count': started_sme_responses_count,
            'large_count': started_large_responses_count,
            'total': started_sme_responses_count + started_large_responses_count
        },
        winning_response=winning_response
    )


@main.route('/<framework_framework>/opportunities')
def list_opportunities(framework_framework):
    frameworks = data_api_client.find_frameworks()['frameworks']

    frameworks = [v for v in frameworks if v['framework'] == framework_framework]
    frameworks.sort(key=lambda x: x['id'], reverse=True)

    if not frameworks:
        abort(404, "No framework {}".format(framework_framework))

    # disabling csrf protection as this should only ever be a GET request
    form = BriefSearchForm(request.args, frameworks=frameworks, data_api_client=data_api_client, csrf_enabled=False)
    if not form.validate():
        abort(404, "Invalid form data")

    api_result = form.get_briefs()

    briefs = [{
        "data": brief,
        "content": content_loader.get_manifest(brief['frameworkSlug'], 'display_brief').filter(brief)
    } for brief in api_result["briefs"]]

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

    return render_template('search/briefs.html',
                           framework=frameworks[-1],
                           form=form,
                           filters=form.get_filters(),
                           filters_applied=form.filters_applied(),
                           briefs=briefs,
                           lot_names=tuple(label for id_, label in form.lot.choices),
                           prev_link_args=prev_link_args,
                           next_link_args=next_link_args,
                           briefs_count=api_result.get("meta", {}).get("total", None),
                           )
