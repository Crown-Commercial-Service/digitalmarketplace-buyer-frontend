# -*- coding: utf-8 -*-
from urllib.parse import urljoin

from flask_login import current_user
from flask import abort, current_app, request, url_for
from lxml import html
from werkzeug.urls import Href
from werkzeug.datastructures import MultiDict

from dmapiclient import APIError
from dmcontent.content_loader import ContentNotFoundError
from dmutils.errors import render_error_page
from dmutils.filters import capitalize_first
from dmutils.flask import timed_render_template as render_template
from dmcontent.html import to_summary_list_rows, text_to_html
from app import search_api_client, data_api_client, content_loader
from ..helpers.brief_helpers import (
    count_brief_responses_by_size_and_status, format_winning_supplier_size,
    get_evaluation_description,
    COMPLETED_BRIEF_RESPONSE_STATUSES, ALL_BRIEF_RESPONSE_STATUSES, PUBLISHED_BRIEF_STATUSES
)
from ..helpers.framework_helpers import (
    abort_if_not_further_competition_framework,
    get_latest_live_framework,
    get_latest_live_framework_or_404,
    get_framework_description,
    get_lots_by_slug
)
from ..helpers.search_helpers import (
    build_search_query,
    clean_request_args,
    get_keywords_from_request,
    get_page_from_request,
    get_request_url_without_any_filters,
    get_valid_lot_from_args_or_none,
    pagination,
    query_args_for_pagination,
)
from ..helpers.shared_helpers import get_one_framework_by_status_in_order_of_preference
from ...main import main
from ..presenters.search_presenters import filters_for_lot, set_filter_states, build_lots_and_categories_link_tree
from ..presenters.search_results import SearchResults
from ..presenters.search_summary import SearchSummary


@main.route('/')
def index():
    framework_status_message = {}

    try:
        frameworks = data_api_client.find_frameworks().get('frameworks')
        framework = get_one_framework_by_status_in_order_of_preference(
            frameworks,
            ['open', 'coming', 'pending']
        )

        if framework is not None:
            content_loader.load_messages(framework.get('slug'), ['homepage-sidebar'])
            framework_status_message = content_loader.get_message(
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
        framework_status_message=framework_status_message,
        gcloud_framework_description=get_framework_description(data_api_client, 'g-cloud'),
    )


@main.route('/help')
def help():
    return render_template('help/index.html')


@main.route('/cookies')
def cookies():
    return render_template('content/cookies.html')


@main.route('/privacy-notice')
def privacy_notice():
    return render_template('content/privacy-notice.html')


@main.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template('content/terms-and-conditions.html')


@main.route('/404')
def external_404():
    """
    Our router app proxies errors (e.g. on an assets domain) to the frontend app's /404 page (i.e. this route).
    Relative links in our normal 404 page will not work if the domain doesn't match, so here we ensure all links
    in the page are absolute.
    :return: Our usual 404 page, but with all relative links made absolute
    """
    error_page, status_code = render_error_page(status_code=404)
    document = html.fromstring(error_page)
    relative_links = document.xpath('//a[starts-with(@href, "/")]')
    forms_with_relative_actions = document.xpath('//form[starts-with(@action, "/")]')

    for link in relative_links:
        link.set("href", urljoin(current_app.config.get("DM_PATCH_FRONTEND_URL", ""), link.get("href")))

    for form in forms_with_relative_actions:
        form.set("action", urljoin(current_app.config.get("DM_PATCH_FRONTEND_URL", ""), form.get("action")))

    return html.tostring(document), status_code


@main.route('/<framework_family>/opportunities/<brief_id>')
def get_brief_by_id(framework_family, brief_id):
    frameworks = data_api_client.find_frameworks()['frameworks']
    frameworks = [framework for framework in frameworks if framework['framework'] == framework_family]
    framework = get_latest_live_framework_or_404(frameworks, framework_family)

    abort_if_not_further_competition_framework(framework)

    briefs = data_api_client.get_brief(brief_id)
    brief = briefs.get('briefs')

    if brief['status'] not in PUBLISHED_BRIEF_STATUSES or brief['framework']['family'] != framework_family:
        abort(404, "Opportunity '{}' can not be found".format(brief_id))

    brief_responses = data_api_client.find_brief_responses(
        brief_id=brief_id,
        status=",".join(ALL_BRIEF_RESPONSE_STATUSES),
        with_data=False,
    ).get('briefResponses')

    winning_response, winning_supplier_size = None, None
    if brief['status'] == 'awarded':
        winning_response = next(response for response in brief_responses if response["id"] == brief[
            'awardedBriefResponseId'
        ])
        winning_supplier_size = format_winning_supplier_size(winning_response["supplierOrganisationSize"])

    brief_responses_stats = count_brief_responses_by_size_and_status(brief_responses)

    if brief['status'] not in PUBLISHED_BRIEF_STATUSES or brief['framework']['family'] != framework_family:
        abort(404, "Opportunity '{}' can not be found".format(brief_id))
    try:
        has_supplier_responded_to_brief = (
            current_user.supplier_id in [
                res['supplierId'] for res in brief_responses if res["status"] in COMPLETED_BRIEF_RESPONSE_STATUSES
            ]
        )
    except AttributeError:
        has_supplier_responded_to_brief = False

    # Get Q&A in format suitable for govukSummaryList
    for index, question in enumerate(brief['clarificationQuestions']):
        question["key"] = {
            "html": f"{str(index + 1)}. "
                    f"{text_to_html(question['question'], format_links=True, preserve_line_breaks=True)}"
        }
        question["value"] = {"html": text_to_html(question["answer"], format_links=True, preserve_line_breaks=True)}

    brief_content = content_loader.get_manifest(brief['frameworkSlug'], 'display_brief').filter(brief)

    # Get attributes in format suitable for govukSummaryList
    brief_summary = brief_content.summary(brief)
    for section in brief_summary:
        section.summary_list = to_summary_list_rows(section.questions, format_links=True, filter_empty=False)

    # Add in mandatory evaluation method, missing from the display_brief manifest summary_page_description
    evaluation_description = get_evaluation_description(brief, brief_content)

    return render_template(
        'brief.html',
        brief=brief,
        brief_responses_stats=brief_responses_stats,
        content=brief_content,
        brief_content_summary=brief_summary,
        has_supplier_responded_to_brief=has_supplier_responded_to_brief,
        winning_response=winning_response,
        winning_supplier_size=winning_supplier_size,
        evaluation_description=evaluation_description
    )


@main.route('/<framework_family>/opportunities')
def list_opportunities(framework_family):
    frameworks = data_api_client.find_frameworks()['frameworks']
    frameworks = [v for v in frameworks if v['framework'] == framework_family]
    framework = get_latest_live_framework_or_404(frameworks, framework_family)

    abort_if_not_further_competition_framework(framework)

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

    # This will exclude anything with a 'withdrawn' status
    if 'statusOpenClosed' not in clean_request_query_params.keys():
        updated_request_args = MultiDict(
            [('statusOpenClosed', 'open'), ('statusOpenClosed', 'closed')]
        )
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

    search_results_obj = SearchResults(
        search_api_response,
        lots_by_slug,
        highlight_fields=frozenset((
            'summary',
        )),
    )

    # Get the results per page from the Search API meta data (or fall back to Buyer FE config setting)
    results_per_page = search_api_response['meta'].get('results_per_page', current_app.config["DM_SEARCH_PAGE_SIZE"])

    # Get prev/next link info and number of pages
    pagination_config = pagination(
        search_results_obj.total,
        results_per_page,
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
        search_api_client
    )

    filter_form_hidden_fields_by_name = {
        f["name"]: f for f in selected_category_tree_filters[1:]
    }
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
        form_action=url_for('.list_opportunities', framework_family=framework_family),
        framework=framework,
        framework_family=framework['framework'],
        framework_family_name='Digital Outcomes and Specialists',
        lot_names=tuple(lot['name'] for lot in lots_by_slug.values() if lot['allowsBrief']),
        outcomes={
            'awarded': 'awarded',
            'cancelled': 'cancelled',
            'closed': 'awaiting outcome',
            'unsuccessful': 'no suitable suppliers'
        },
        pagination=pagination_config,
        search_keywords=get_keywords_from_request(request),
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
            "summary-accessible-hint": {
                "selector": "#js-dm-live-search-summary-accessible-hint",
                "html": render_template("search/_summary_accessible_hint.html", **template_args)
            },
            "filter-title": {
                "selector": "#js-dm-live-filter-title",
                "html": render_template("search/_filter_title.html", **template_args)
            },
        }

        return jsonify(live_results_dict)

    return render_template(
        'search/briefs.html',
        **template_args
    )
