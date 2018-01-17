# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask_login import current_user
from flask import abort, current_app, render_template, request, url_for

from werkzeug.urls import Href
from werkzeug.datastructures import MultiDict

from dmapiclient import APIError
from dmcontent.content_loader import ContentNotFoundError
from dmutils.filters import capitalize_first

from ...main import main
from ..helpers.shared_helpers import get_one_framework_by_status_in_order_of_preference
from ..helpers.brief_helpers import (
    count_brief_responses_by_size_and_status, format_winning_supplier_size,
    COMPLETED_BRIEF_RESPONSE_STATUSES, ALL_BRIEF_RESPONSE_STATUSES, PUBLISHED_BRIEF_STATUSES
)
from ..helpers.search_helpers import (
    pagination, get_page_from_request, query_args_for_pagination, get_valid_lot_from_args_or_none, build_search_query,
    clean_request_args, get_request_url_without_any_filters,
)
from ..presenters.search_presenters import filters_for_lot, set_filter_states, build_lots_and_categories_link_tree
from ..presenters.search_results import SearchResults
from ..presenters.search_summary import SearchSummary
from ..helpers.framework_helpers import get_latest_live_framework, get_framework_description, get_lots_by_slug

from app import search_api_client, data_api_client, content_loader


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


@main.route('/support')
def support():
    return render_template('support/index.html')


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

    winning_response, winning_supplier_size = None, None
    if brief['status'] == 'awarded':
        winning_response = next(response for response in brief_responses if response["id"] == brief[
            'awardedBriefResponseId'
        ])
        winning_supplier_size = format_winning_supplier_size(winning_response["supplierOrganisationSize"])

    brief_responses_stats = count_brief_responses_by_size_and_status(brief_responses)

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
        dict(question, number=index + 1)
        for index, question in enumerate(brief['clarificationQuestions'])
    ]

    brief_content = content_loader.get_manifest(brief['frameworkSlug'], 'display_brief').filter(brief)

    return render_template(
        'brief.html',
        brief=brief,
        brief_responses_stats=brief_responses_stats,
        content=brief_content,
        has_supplier_responded_to_brief=has_supplier_responded_to_brief,
        winning_response=winning_response,
        winning_supplier_size=winning_supplier_size
    )


@main.route('/<framework_family>/opportunities')
def list_opportunities(framework_family):
    frameworks = data_api_client.find_frameworks()['frameworks']
    frameworks = [v for v in frameworks if v['framework'] == framework_family]
    framework = get_latest_live_framework(frameworks, framework_family)

    if not framework:
        abort(404, "No framework {}".format(framework_family))

    lots_by_slug = get_lots_by_slug(framework)
    current_lot_slug = get_valid_lot_from_args_or_none(request.args, lots_by_slug)
    content_manifest = content_loader.get_manifest(framework['slug'], 'briefs_search_filters')

    filters = filters_for_lot(
        current_lot_slug,
        content_manifest,
        all_lots=framework['lots']
    )

    clean_request_query_params = clean_request_args(request.args, filters.values(), lots_by_slug)

    try:
        if int(request.args.get('page', 1)) <= 0:
            abort(404)
    except ValueError:
        abort(404)

    index = 'briefs-digital-outcomes-and-specialists'
    doc_type = 'briefs'
    updated_request_args = None

    if 'status' not in clean_request_query_params.keys():
        updated_request_args = MultiDict([('status', 'live'), ('status', 'closed')])
        updated_request_args.update(clean_request_query_params)

    search_api_response = search_api_client.search(
        index=index,
        doc_type=doc_type,
        **build_search_query(
            updated_request_args if updated_request_args else clean_request_query_params,
            filters.values(),
            content_manifest,
            lots_by_slug
        )
    )

    # Convert the values of certain attributes to their label counterparts
    content = content_loader.get_manifest(framework['slug'], 'briefs_search_filters')
    for brief in search_api_response['documents']:
        if brief.get('specialistRole'):
            brief['specialistRole'] = content.summary(brief).get_question('specialistRole').value
        brief['location'] = content.summary(brief).get_question('location').value

    search_results_obj = SearchResults(search_api_response, lots_by_slug)

    pagination_config = pagination(
        search_results_obj.total,
        current_app.config["DM_SEARCH_PAGE_SIZE"],
        get_page_from_request(request)
    )

    search_summary = SearchSummary(
        search_api_response['meta']['total'],
        clean_request_query_params.copy(),
        filters.values(),
        lots_by_slug
    )

    category_filter_group = filters.pop('categories') if 'categories' in filters else None
    lots = [lot for lot in framework['lots'] if lot['allowsBrief']]

    view_name = 'list_opportunities'
    selected_category_tree_filters = build_lots_and_categories_link_tree(
        framework,
        lots,
        category_filter_group,
        request,
        updated_request_args if updated_request_args else clean_request_query_params,
        content_manifest,
        doc_type,
        index,
        Href(url_for('.{}'.format(view_name), framework_family=framework['framework'])),
    )

    filter_form_hidden_fields_by_name = {f['name']: f for f in selected_category_tree_filters[1:]}
    current_lot = lots_by_slug.get(current_lot_slug)

    set_filter_states(filters.values(), request)

    for filter_groups in filters.values():
        for filter_instance in filter_groups['filters']:
            if 'label' in filter_instance:
                filter_instance['label'] = capitalize_first(filter_instance['label'])

    clear_filters_url = get_request_url_without_any_filters(
        request, filters, view_name, framework_family=framework_family
    )
    search_query = query_args_for_pagination(clean_request_query_params)

    template_args = dict(
        briefs=search_results_obj.search_results,
        category_tree_root=selected_category_tree_filters[0],
        clear_filters_url=clear_filters_url,
        current_lot=current_lot,
        doc_type=doc_type,
        filters=filters.values(),
        filter_form_hidden_fields=filter_form_hidden_fields_by_name.values(),
        framework=framework,
        framework_family=framework['framework'],
        framework_family_name='Digital Outcomes and Specialists',
        lot_names=tuple(lot['name'] for lot in lots_by_slug.values() if lot['allowsBrief']),
        pagination=pagination_config,
        search_query=search_query,
        summary=search_summary.markup(),
        total=search_results_obj.total,
        view_name=view_name,
    )

    if request.args.get('live-results'):
        from flask import jsonify

        live_results_dict = {
            "results": {
                "selector": "#js-dm-live-search-results",
                "html": render_template("search/_results_wrapper.html", **template_args)
            },
            "categories": {
                "selector": "#js-dm-live-search-categories",
                "html": render_template("search/_categories_wrapper.html", **template_args)
            },
            "summary": {
                "selector": "#js-dm-live-search-summary",
                "html": render_template("search/_summary.html", **template_args)
            },
        }

        return jsonify(live_results_dict)

    return render_template(
        'search/briefs.html',
        **template_args
    )
