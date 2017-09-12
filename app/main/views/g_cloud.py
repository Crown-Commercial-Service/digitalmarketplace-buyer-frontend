# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import abort, render_template, request, redirect, current_app, url_for, flash, Markup
from flask_login import current_user

from dmutils.formats import dateformat
from dmutils.filters import capitalize_first
from dmapiclient import HTTPError

from ...main import main, direct_award
from ..presenters.search_presenters import (
    filters_for_lot,
    set_filter_states,
    build_lots_and_categories_link_tree,
)
from ..presenters.search_results import SearchResults
from ..presenters.search_summary import SearchSummary
from ..presenters.service_presenters import Service
from ..helpers.search_helpers import (
    get_keywords_from_request, pagination,
    get_page_from_request, query_args_for_pagination,
    get_lot_from_request, build_search_query,
    clean_request_args, get_request_url_without_any_filters,
)
from ..helpers import framework_helpers
from ..helpers.search_save_helpers import SearchMeta
from ..forms.direct_award_forms import CreateProjectForm

from ..helpers.direct_award_helpers import is_direct_award_project_accessible

from ..exceptions import AuthException
from app import search_api_client, data_api_client, content_loader


PROJECT_CREATED_MESSAGE = Markup("""Your new project has been created.""")
PROJECT_ENDED_MESSAGE = Markup("""Your search has been ended. You can now download your shortlist.""")


@main.route('/g-cloud')
def index_g_cloud():
    # if there are multiple live g-cloud frameworks, assume they all have the same lots
    all_frameworks = data_api_client.find_frameworks().get('frameworks')
    framework = framework_helpers.get_latest_live_framework(all_frameworks, 'g-cloud')

    content_loader.load_messages(framework['slug'], ['advice', 'descriptions'])
    gcloud_page_title = content_loader.get_message(framework['slug'], 'descriptions', 'framework')
    gcloud_lot_messages = content_loader.get_message(framework['slug'], 'advice', 'lots')
    gcloud_lot_messages = {x['slug']: x for x in gcloud_lot_messages}

    lot_browse_list_items = list()
    for lot in framework['lots']:
        lot_item = {
            "link": url_for('.search_services', lot=lot['slug']),
            "title": lot['name'],
            "body": gcloud_lot_messages[lot['slug']]['body'],
            "subtext": gcloud_lot_messages[lot['slug']].get('advice'),
        }

        lot_browse_list_items.append(lot_item)

    return render_template('index-g-cloud.html',
                           title=gcloud_page_title,
                           lots=lot_browse_list_items)


@main.route('/g-cloud/framework')
def framework_g_cloud():
    return redirect('https://www.gov.uk/guidance/the-g-cloud-framework-on-the-digital-marketplace', 301)


@main.route('/buyers-guide')
def buyers_guide():
    return redirect('https://www.gov.uk/guidance/g-cloud-buyers-guide', 301)


@main.route('/suppliers-guide')
def suppliers_guide():
    return redirect('/g-cloud/suppliers-guide', 301)


@main.route('/g-cloud/buyers-guide')
def buyers_guide_g_cloud():
    return redirect('https://www.gov.uk/guidance/g-cloud-buyers-guide', 301)


@main.route('/g-cloud/suppliers-guide')
def suppliers_guide_g_cloud():
    return redirect('https://www.gov.uk/guidance/g-cloud-suppliers-guide', 301)


@main.route('/g-cloud/services/<service_id>')
def get_service_by_id(service_id):
    try:
        service = data_api_client.get_service(service_id)
        if service is None:
            abort(404, "Service ID '{}' can not be found".format(service_id))
        if service['services']['frameworkStatus'] not in ("live", "expired"):
            abort(404, "Service ID '{}' can not be found".format(service_id))

        service_data = service['services']
        framework_slug = service_data['frameworkSlug']

        # Some frameworks don't actually have framework content of their own (e.g. G-Cloud 4 and 5) - they
        # use content from some other framework (for those examples, G-Cloud 6 content works fine). In those
        # cases, we need to override the framework slug that we got from the service data, and load that
        # content instead.
        override_framework_slug = current_app.config.get('DM_FRAMEWORK_CONTENT_MAP', {}).get(framework_slug)
        if override_framework_slug:
            framework_slug = override_framework_slug

        framework = data_api_client.get_framework(framework_slug)['frameworks']
        if framework['framework'] != 'g-cloud':
            abort(404)

        service_view_data = Service(
            service_data,
            content_loader.get_manifest(framework_slug, 'display_service').filter(
                service_data
            ),
            framework_helpers.get_lots_by_slug(framework)
        )

        try:
            # get supplier data and add contact info to service object
            supplier = data_api_client.get_supplier(
                service_data['supplierId']
            )
            supplier_data = supplier['suppliers']
            service_view_data.meta.set_contact_attribute(
                supplier_data['contactInformation'][0].get('contactName'),
                supplier_data['contactInformation'][0].get('phoneNumber'),
                supplier_data['contactInformation'][0].get('email')
            )

        except HTTPError as e:
            abort(e.status_code)

        service_unavailability_information = None
        status_code = 200
        if service['serviceMadeUnavailableAuditEvent'] is not None:
            service_unavailability_information = {
                'date': dateformat(service['serviceMadeUnavailableAuditEvent']['createdAt']),
                'type': service['serviceMadeUnavailableAuditEvent']['type']
            }
            # mark the resource as unavailable in the headers
            status_code = 410

        return render_template(
            'service.html',
            service=service_view_data,
            service_unavailability_information=service_unavailability_information,
            lot=service_view_data.lot,
            gcloud_framework_description=framework_helpers.get_framework_description(data_api_client, 'g-cloud'),
        ), status_code
    except AuthException:
        abort(500, "Application error")
    except HTTPError as e:
        abort(e.status_code)


@main.route('/g-cloud/search')
def search_services():
    # if there are multiple live g-cloud frameworks, we must assume the same filters work on them all
    all_frameworks = data_api_client.find_frameworks().get('frameworks')
    framework = framework_helpers.get_latest_live_framework(all_frameworks, 'g-cloud')

    lots_by_slug = framework_helpers.get_lots_by_slug(framework)

    current_lot_slug = get_lot_from_request(request, lots_by_slug)

    # the bulk of the possible filter parameters are defined through the content loader. they're all boolean and the
    # search api uses the same "question" labels as the content for its attributes, so we can really use those labels
    # verbatim. It also means we can use their human-readable names as defined in the content
    content_manifest = content_loader.get_manifest(framework['slug'], 'search_filters')
    # filters - an OrderedDictionary of dicts describing each parameter group
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

    search_api_response = search_api_client.search_services(
        index=framework['slug'],
        **build_search_query(request.args, filters.values(), content_manifest, lots_by_slug)
    )
    search_results_obj = SearchResults(search_api_response, lots_by_slug)

    # the search api doesn't supply its own pagination information: use this `pagination` function to figure out what
    # links to show
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

    # for display purposes (but not for actual filtering purposes), we
    # remove 'categories' from the list of filters, and process them into a single structure with the lots
    category_filter_group = filters.pop('categories') if 'categories' in filters else None

    lots = framework['lots']
    selected_category_tree_filters = build_lots_and_categories_link_tree(framework, lots, category_filter_group,
                                                                         request, content_manifest)

    # Filter form should also filter by lot, and by category, when any of those are selected.
    # (But if a sub-category is selected, there is no need to filter by the parent category as,
    # well, so we can just take one hidden field per key - sub-cat will be last.)
    filter_form_hidden_fields_by_name = {f['name']: f for f in selected_category_tree_filters[1:]}

    current_lot = lots_by_slug.get(current_lot_slug)

    # annotate `filters` with their values as set in this request for re-rendering purposes.
    set_filter_states(filters.values(), request)

    # Uppercase first character of filter labels for display
    for filter_groups in filters.values():
        for filter_instance in filter_groups['filters']:
            if 'label' in filter_instance:
                filter_instance['label'] = capitalize_first(filter_instance['label'])

    clear_filters_url = get_request_url_without_any_filters(request, filters)

    template_args = dict(
        current_lot=current_lot,
        framework_family=framework['framework'],
        category_tree_root=selected_category_tree_filters[0],
        filter_form_hidden_fields=filter_form_hidden_fields_by_name.values(),
        filters=filters.values(),
        lots=lots,
        pagination=pagination_config,
        search_keywords=get_keywords_from_request(request),
        search_query=query_args_for_pagination(clean_request_query_params),
        services=search_results_obj.search_results,
        summary=search_summary.markup(),
        title='Search results',
        total=search_results_obj.total,
        gcloud_framework_description=framework_helpers.get_framework_description(data_api_client, 'g-cloud'),
        clear_filters_url=clear_filters_url)

    if request.args.get('live-results'):
        from flask import jsonify

        live_results_dict = {
            "results": {
                "selector": "#js-dm-live-search-results",
                "html": render_template("search/_services_results_wrapper.html", **template_args)
            },
            "categories": {
                "selector": "#js-dm-live-search-categories",
                "html": render_template("search/_services_categories_wrapper.html", **template_args)
            },
            "summary": {
                "selector": "#js-dm-live-search-summary",
                "html": render_template("search/_services_summary.html", **template_args)
            }
        }

        return jsonify(live_results_dict)

    return render_template(
        'search/services.html',
        **template_args
    )


@direct_award.route('/<string:framework_framework>', methods=['GET'])
def saved_search_overview(framework_framework):
    all_frameworks = data_api_client.find_frameworks().get('frameworks')
    framework = framework_helpers.get_latest_live_framework(all_frameworks, framework_framework)

    if not framework:
        abort(404)

    content_loader.load_messages(framework['slug'], ['descriptions', 'urls'])
    framework_short_description = content_loader.get_message(framework['slug'], 'descriptions', 'framework_short')

    projects = data_api_client.find_direct_award_projects(current_user.id).get('projects', [])
    open_projects = []
    closed_projects = []

    for project in projects:
        if project['lockedAt'] is None:
            open_projects.append(project)
        else:
            closed_projects.append(project)

    return render_template(
        'direct-award/index.html',
        open_projects=open_projects,
        closed_projects=closed_projects,
        framework=framework,
        framework_short_description=framework_short_description
    )


@direct_award.route('/<string:framework_framework>/projects', methods=['GET'])
def view_projects(framework_framework):
    return redirect(url_for('.saved_search_overview', framework_framework=framework_framework))


@direct_award.route('/<string:framework_framework>/save-search', methods=['GET'])
def save_search(framework_framework):
    # Get core data
    all_frameworks = data_api_client.find_frameworks().get('frameworks')
    framework = framework_helpers.get_latest_live_framework(all_frameworks, framework_framework)
    lots_by_slug = framework_helpers.get_lots_by_slug(framework)
    current_lot_slug = get_lot_from_request(request, lots_by_slug)

    content_manifest = content_loader.get_manifest(framework['slug'], 'search_filters')
    filters = filters_for_lot(current_lot_slug, content_manifest, all_lots=framework['lots'])
    clean_request_query_params = clean_request_args(request.args, filters.values(), lots_by_slug)

    # Retrieve results so we can display SearchSummary
    search_api_response = search_api_client.search_services(
        index=framework['slug'],
        **build_search_query(request.args, filters.values(), content_manifest, lots_by_slug)
    )

    search_summary = SearchSummary(search_api_response['meta']['total'], clean_request_query_params.copy(),
                                   filters.values(), lots_by_slug)

    # Embed search api URL in form so that the next view can be aware of it
    # This is maybe not ideal
    search_api_url = search_api_client.get_search_url(
        index=framework['slug'],
        **build_search_query(request.args, filters.values(), content_manifest, lots_by_slug)
    )

    return render_template(
        'direct-award/save-search.html',
        framework_framework=framework_framework,
        search_summary_sentence=search_summary.markup(),
        search_api_url=search_api_url,
        form=CreateProjectForm(),
    )


@direct_award.route('/<string:framework_framework>/projects/create', methods=['POST'])
def project_create(framework_framework):
    form = CreateProjectForm()
    if form.validate_on_submit():
        name = form.name.data
        try:
            api_project = data_api_client.create_direct_award_project(user_id=current_user.id,
                                                                      user_email=current_user.email_address,
                                                                      project_name=name)

        except HTTPError as e:
            abort(e.status_code)

        project = api_project['project']

        try:
            data_api_client.create_direct_award_project_search(user_id=current_user.id,
                                                               user_email=current_user.email_address,
                                                               project_id=project['id'],
                                                               search_url=request.form['search_api_url'])
        except HTTPError as e:
            abort(e.status_code)

        flash(PROJECT_CREATED_MESSAGE, 'success')

        return redirect(url_for('.view_project',
                                framework_framework=framework_framework,
                                project_id=project['id']
                                ))
    else:
        frameworks_by_slug = framework_helpers.get_frameworks_by_slug(data_api_client)

        search_meta = SearchMeta(request.form['search_api_url'], frameworks_by_slug)

        return render_template('direct-award/save-search.html',
                               form=form,
                               search_summary_sentence=search_meta.search_summary.markup(),
                               search_api_url=request.form['search_api_url'],
                               framework_framework=framework_framework)


@direct_award.route('/<string:framework_framework>/projects/<int:project_id>', methods=['GET'])
def view_project(framework_framework, project_id):
    frameworks_by_slug = framework_helpers.get_frameworks_by_slug(data_api_client)
    # Get the requested Direct Award Project.
    project = data_api_client.get_direct_award_project(project_id=project_id)['project']
    if not is_direct_award_project_accessible(project, current_user.id):
        abort(404)

    searches = data_api_client.find_direct_award_project_searches(user_id=current_user.id,
                                                                  project_id=project['id'])['searches']

    if searches:
        # A Direct Award project has one 'active' search which is what we will display on this overview page.
        search = list(filter(lambda x: x['active'], searches))[0]

        search_meta = SearchMeta(search['searchUrl'], frameworks_by_slug)

        search_summary_sentence = search_meta.search_summary.markup()
        framework = frameworks_by_slug[search_meta.framework_slug]
        buyer_search_page_url = search_meta.url

    else:
        framework = framework_helpers.get_latest_live_framework(frameworks_by_slug.values(), 'g-cloud')

        search = None
        buyer_search_page_url = None
        search_summary_sentence = None

    content_loader.load_messages(framework['slug'], ['descriptions', 'urls'])
    framework_short_description = content_loader.get_message(framework['slug'], 'descriptions', 'framework_short')
    framework_urls = content_loader.get_message(framework['slug'], 'urls')

    return render_template('direct-award/view-project.html',
                           framework=framework,
                           project=project,
                           search=search,
                           buyer_search_page_url=buyer_search_page_url,
                           search_summary_sentence=search_summary_sentence,
                           framework_short_description=framework_short_description,
                           framework_urls=framework_urls,
                           call_off_contract_url=framework_urls['call_off_contract_url'],
                           customer_benefits_record_form_url=framework_urls['customer_benefits_record_form_url'],
                           customer_benefits_record_form_email=framework_urls['customer_benefits_record_form_email'])


@direct_award.route('/<string:framework_framework>/projects/<int:project_id>/end-search', methods=['GET', 'POST'])
def end_search(framework_framework, project_id):
    all_frameworks = data_api_client.find_frameworks().get('frameworks')
    framework = framework_helpers.get_latest_live_framework(all_frameworks, framework_framework)

    project = data_api_client.get_direct_award_project(project_id).get('project')
    if not is_direct_award_project_accessible(project, current_user.id):
        abort(404)

    if not framework or not project:
        abort(404)

    if project['lockedAt']:
        abort(400)

    if request.method == 'POST':
        try:
            data_api_client.lock_direct_award_project(user_email=current_user.email_address, project_id=project_id)
        except HTTPError as e:
            abort(e.status_code)

        flash(PROJECT_ENDED_MESSAGE, 'success')

        return redirect(url_for('.view_project', framework_framework=framework_framework, project_id=project['id']))

    return render_template(
        'direct-award/end-search.html',
        project=project,
        framework=framework
    )


@direct_award.route('/<string:framework_framework>/projects/<int:project_id>/download-shortlist')
def download_shortlist(framework_framework, project_id):
    # Get the requested Direct Award Project.
    project = data_api_client.get_direct_award_project(project_id=project_id)['project']
    if not is_direct_award_project_accessible(project, current_user.id):
        abort(404)

    searches = data_api_client.find_direct_award_project_searches(user_id=current_user.id,
                                                                  project_id=project['id'])['searches']

    if searches:
        # A Direct Award project has one 'active' search which is what we will display on this overview page.
        search = list(filter(lambda x: x['active'], searches))[0]

        # Indexes for our search API are named by the framework slug they relate to.
        framework_slug = search_api_client.get_index_from_search_api_url(search['searchUrl'])
        framework = data_api_client.get_framework(framework_slug)['frameworks']

        content_loader.load_messages(framework['slug'], ['descriptions', 'urls'])
        framework_urls = content_loader.get_message(framework['slug'], 'urls')

    else:
        abort(404)

    return render_template('direct-award/download-shortlist.html',
                           framework=framework,
                           project=project,
                           framework_urls=framework_urls
                           )
