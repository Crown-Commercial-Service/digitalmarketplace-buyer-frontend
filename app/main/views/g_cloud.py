# -*- coding: utf-8 -*-
from datetime import datetime
import inflection
from operator import itemgetter

from flask import abort, render_template, request, redirect, current_app, url_for, flash, Markup
from flask_login import current_user
from werkzeug.urls import Href, url_encode, url_decode

from dmapiclient import HTTPError
from dmcontent.formats import format_service_price
from dmcontent.questions import Pricing
from dmutils.formats import dateformat, DATETIME_FORMAT, datetimeformat
from dmutils.filters import capitalize_first
from dmutils.ods import A as AnchorElement
from dmutils.views import SimpleDownloadFileView

from app import search_api_client, data_api_client, content_loader
from ..exceptions import AuthException
from ..forms.direct_award_forms import CreateProjectForm
from ..helpers.search_helpers import (
    get_keywords_from_request, pagination,
    get_page_from_request, query_args_for_pagination,
    get_valid_lot_from_args_or_none,
    build_search_query,
    clean_request_args, get_request_url_without_any_filters,
)
from ..helpers import framework_helpers
from ..helpers.direct_award_helpers import is_direct_award_project_accessible, get_direct_award_projects
from ..helpers.search_save_helpers import SearchMeta
from ..helpers.shared_helpers import get_fields_from_manifest, get_questions_from_manifest_by_id
from ...main import main, direct_award
from ..presenters.search_presenters import (
    filters_for_lot,
    set_filter_states,
    build_lots_and_categories_link_tree,
)
from ..presenters.search_results import SearchResults
from ..presenters.search_summary import SearchSummary
from ..presenters.service_presenters import Service


END_SEARCH_LIMIT = 100  # TODO: This should be done in the API.
PROJECT_SAVED_MESSAGE = Markup("""Search saved.""")
PROJECT_ENDED_MESSAGE = Markup("""Search ended. You can now download your search results.""")
TOO_MANY_RESULTS_MESSAGE = Markup("""
    You have too many results. Choose a category or add filters to refine your search.""")


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
    doc_type = 'services'

    lots_by_slug = framework_helpers.get_lots_by_slug(framework)

    current_lot_slug = get_valid_lot_from_args_or_none(request.args, lots_by_slug)
    # the bulk of the possible filter parameters are defined through the content loader. they're all boolean and the
    # search api uses the same "question" labels as the content for its attributes, so we can really use those labels
    # verbatim. It also means we can use their human-readable names as defined in the content
    content_manifest = content_loader.get_manifest(framework['slug'], 'services_search_filters')
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

    search_api_response = search_api_client.search(
        index=framework['slug'],
        doc_type=doc_type,
        **build_search_query(clean_request_query_params, filters.values(), content_manifest, lots_by_slug)
    )
    search_results_obj = SearchResults(
        search_api_response,
        lots_by_slug,
        highlight_fields=frozenset((
            'serviceSummary',
            'serviceDescription',
        )),
    )

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
    view_name = 'search_services'
    selected_category_tree_filters = build_lots_and_categories_link_tree(
        framework,
        lots,
        category_filter_group,
        request,
        clean_request_query_params,
        content_manifest,
        doc_type,
        framework['slug'],
        Href(url_for('.{}'.format(view_name))),
    )

    # Filter form should also filter by lot, and by category, when any of those are selected.
    # (If a sub-category is selected, we also need the parent category id, so that the correct part
    # of the category tree is displayed when the sub-category appears under multiple parents.)
    filter_form_hidden_fields_by_name = {f['name']: f for f in selected_category_tree_filters[1:]}

    current_lot = lots_by_slug.get(current_lot_slug)

    # annotate `filters` with their values as set in this request for re-rendering purposes.
    set_filter_states(filters.values(), request)

    # Uppercase first character of filter labels for display
    for filter_groups in filters.values():
        for filter_instance in filter_groups['filters']:
            if 'label' in filter_instance:
                filter_instance['label'] = capitalize_first(filter_instance['label'])

    clear_filters_url = get_request_url_without_any_filters(request, filters, view_name)
    search_query = query_args_for_pagination(clean_request_query_params)

    template_args = dict(
        category_tree_root=selected_category_tree_filters[0],
        clear_filters_url=clear_filters_url,
        current_lot=current_lot,
        doc_type=doc_type,
        filters=filters.values(),
        filter_form_hidden_fields=filter_form_hidden_fields_by_name.values(),
        framework_family=framework['framework'],
        gcloud_framework_description=framework_helpers.get_framework_description(data_api_client, 'g-cloud'),
        lots=lots,
        pagination=pagination_config,
        search_count=search_api_response['meta']['total'],
        search_keywords=get_keywords_from_request(request),
        search_query=search_query,
        search_query_url=url_encode(search_query),  # for save-search form
        services=search_results_obj.search_results,
        summary=search_summary.markup(),
        title='Search results',
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
            "save-form": {
                "selector": "#js-dm-live-save-search-form",
                "html": render_template("search/_services_save_search.html", **template_args)
            },
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

    projects = get_direct_award_projects(current_user.id, latest_first=True)
    projects['closed_projects'].sort(key=itemgetter('lockedAt'), reverse=True)

    return render_template(
        'direct-award/index.html',
        open_projects=projects['open_projects'],
        closed_projects=projects['closed_projects'],
        framework=framework,
        framework_short_description=framework_short_description
    )


@direct_award.route('/<string:framework_framework>/projects', methods=['GET'])
def view_projects(framework_framework):
    return redirect(url_for('.saved_search_overview', framework_framework=framework_framework))


@direct_award.route('/<string:framework_framework>/save-search', methods=['GET', 'POST'])
def save_search(framework_framework):
    # Get core data
    all_frameworks = data_api_client.find_frameworks().get('frameworks')
    framework = framework_helpers.get_latest_live_framework(all_frameworks, framework_framework)
    lots_by_slug = framework_helpers.get_lots_by_slug(framework)

    search_query = url_decode(request.values.get('search_query'))

    current_lot_slug = get_valid_lot_from_args_or_none(search_query, lots_by_slug)

    content_manifest = content_loader.get_manifest(framework['slug'], 'services_search_filters')
    filters = filters_for_lot(current_lot_slug, content_manifest, all_lots=framework['lots'])
    clean_request_query_params = clean_request_args(search_query, filters.values(), lots_by_slug)

    form = CreateProjectForm()
    name = form.name.data

    save_search_selection = request.form.get('save_search_selection', None)

    name_is_invalid = save_search_selection == "new_search" and not name

    if request.method == 'GET' or not form.validate_on_submit() or not save_search_selection or name_is_invalid:
        projects = get_direct_award_projects(current_user.id, 'open_projects', 'name')
        projects.sort(key=lambda x: x['name'])

        # Retrieve results so we can display SearchSummary
        search_api_response = search_api_client.search(
            index=framework['slug'],
            doc_type='services',
            **build_search_query(search_query, filters.values(), content_manifest, lots_by_slug)
        )
        search_summary = SearchSummary(search_api_response['meta']['total'], clean_request_query_params.copy(),
                                       filters.values(), lots_by_slug)

        if not name and request.method == 'POST':
            form.name.errors = ["Names must be between 1 and 100 characters"]

        if not save_search_selection and request.method == "POST":
            save_search_selection_error = "Please choose where to save your search"
        else:
            save_search_selection_error = None

        return render_template('direct-award/save-search.html',
                               form=form,
                               save_search_selection_error=save_search_selection_error,
                               search_summary_sentence=search_summary.markup(),
                               search_query=url_encode(search_query),
                               search_url=url_for('main.search_services', **search_query),
                               request=request,
                               projects=projects,
                               framework_framework=framework_framework), 400 if request.method == 'POST' else 200

    elif save_search_selection == "new_search" and name:
        try:
            api_project = data_api_client.create_direct_award_project(user_id=current_user.id,
                                                                      user_email=current_user.email_address,
                                                                      project_name=name)
        except HTTPError as e:
            abort(e.status_code)

        project = api_project['project']

    elif save_search_selection:
        project = data_api_client.get_direct_award_project(project_id=save_search_selection)['project']
        if not project or not is_direct_award_project_accessible(project, current_user.id):
            abort(404)

    search_api_url = search_api_client.get_search_url(
        index=framework['slug'],
        **build_search_query(search_query, filters.values(), content_manifest, lots_by_slug)
    )
    try:
        data_api_client.create_direct_award_project_search(user_id=current_user.id,
                                                           user_email=current_user.email_address,
                                                           project_id=project['id'],
                                                           search_url=search_api_url)

    except HTTPError as e:
        abort(e.status_code)

    flash(PROJECT_SAVED_MESSAGE, 'success')

    return redirect(url_for('.view_project',
                            framework_framework=framework_framework,
                            project_id=project['id']
                            ), code=303)


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

    content_loader.load_messages(framework['slug'], ['urls'])
    framework_urls = content_loader.get_message(framework['slug'], 'urls')

    # Current Project Stage
    current_project_stage = None

    if project['downloadedAt']:
        current_project_stage = 'download_results'
    elif project['lockedAt']:
        current_project_stage = 'search_ended'
    else:
        current_project_stage = 'save_and_refine_search'

    return render_template('direct-award/view-project.html',
                           framework=framework,
                           project=project,
                           current_project_stage=current_project_stage,
                           search=search,
                           buyer_search_page_url=buyer_search_page_url,
                           search_summary_sentence=search_summary_sentence,
                           framework_urls=framework_urls,
                           call_off_contract_url=framework_urls['call_off_contract_url'],
                           customer_benefits_record_form_url=framework_urls['customer_benefits_record_form_url'],
                           customer_benefits_record_form_email=framework_urls['customer_benefits_record_form_email'])


@direct_award.route('/<string:framework_framework>/projects/<int:project_id>/end-search', methods=['GET', 'POST'])
def end_search(framework_framework, project_id):
    all_frameworks = data_api_client.find_frameworks().get('frameworks')
    framework = framework_helpers.get_latest_live_framework(all_frameworks, framework_framework)
    frameworks_by_slug = framework_helpers.get_frameworks_by_slug(data_api_client)

    # Get the requested Direct Award Project.
    project = data_api_client.get_direct_award_project(project_id=project_id)['project']
    if not is_direct_award_project_accessible(project, current_user.id):
        abort(404)

    searches = data_api_client.find_direct_award_project_searches(user_id=current_user.id,
                                                                  project_id=project['id'],
                                                                  only_active=True)['searches']
    search = searches[0]
    search_meta = SearchMeta(search['searchUrl'], frameworks_by_slug)
    search_count = search_meta.search_summary.count
    disable_end_search_btn = False

    if int(search_count) > END_SEARCH_LIMIT:
        flash(TOO_MANY_RESULTS_MESSAGE, 'error')
        disable_end_search_btn = True

    if not framework or not project:
        abort(404)

    if project['lockedAt']:
        abort(400)

    if request.method == 'POST' and int(search_count) <= END_SEARCH_LIMIT:
        try:
            data_api_client.lock_direct_award_project(user_email=current_user.email_address, project_id=project_id)
        except HTTPError as e:
            abort(e.status_code)

        flash(PROJECT_ENDED_MESSAGE, 'success')

        return redirect(url_for('.view_project', framework_framework=framework_framework, project_id=project['id']))

    return render_template(
        'direct-award/end-search.html',
        project=project,
        framework=framework,
        disable_end_search_btn=disable_end_search_btn,
        search_count=search_count,
    )


@direct_award.route('/<string:framework_framework>/projects/<int:project_id>/results')
def search_results(framework_framework, project_id):
    # Get the requested Direct Award Project.
    project = data_api_client.get_direct_award_project(project_id=project_id)['project']
    if not is_direct_award_project_accessible(project, current_user.id):
        abort(404)

    if not project['lockedAt']:
        abort(400)

    try:
        search = data_api_client.find_direct_award_project_searches(user_id=current_user.id,
                                                                    project_id=project['id'],
                                                                    only_active=True)['searches'][0]
    except (KeyError, IndexError):
        abort(400)

    # Indexes for our search API are named by the framework slug they relate to.
    framework_slug = search_api_client.get_index_from_search_api_url(search['searchUrl'])
    framework = data_api_client.get_framework(framework_slug)['frameworks']

    content_loader.load_messages(framework['slug'], ['descriptions', 'urls'])
    framework_urls = content_loader.get_message(framework['slug'], 'urls')

    return render_template('direct-award/results.html',
                           framework=framework,
                           project=project,
                           framework_urls=framework_urls
                           )


class DownloadResultsView(SimpleDownloadFileView):
    def _init_hook(self, **kwargs):
        self.data_api_client = data_api_client
        self.search_api_client = search_api_client
        self.content_loader = content_loader

    def _post_request_hook(self, response, **kwargs):
        if response[1] == 200:
            self.data_api_client.record_direct_award_project_download(user_email=current_user.email_address,
                                                                      project_id=kwargs['project_id'])

    def determine_filetype(self, file_context=None, **kwargs):
        file_type = self.request.args.get('filetype', '').lower()

        if file_type == 'csv':
            return DownloadResultsView.FILETYPES.CSV

        elif file_type == 'ods':
            return DownloadResultsView.FILETYPES.ODS

        abort(400)

    @staticmethod
    def get_project_and_search(project_id):
        project = data_api_client.get_direct_award_project(project_id=project_id)['project']
        if not is_direct_award_project_accessible(project, current_user.id):
            abort(404)  # TODO: This should really be a 403, but we don't have a template for that error.

        if not project['lockedAt']:
            abort(400)

        try:
            search = data_api_client.find_direct_award_project_searches(user_id=current_user.id,
                                                                        project_id=project['id'],
                                                                        only_active=True)['searches'][0]
        except (KeyError, IndexError):
            abort(400)

        return project, search

    def get_file_context(self, **kwargs):
        """All of the data required to generate what will go into the files"""
        project, search = self.get_project_and_search(kwargs['project_id'])

        frameworks_by_slug = framework_helpers.get_frameworks_by_slug(data_api_client)
        framework_slug = self.search_api_client.get_index_from_search_api_url(search['searchUrl'])

        download_results_manifest = self.content_loader.get_manifest(framework_slug, 'download_results')
        required_fields = get_fields_from_manifest(download_results_manifest)

        manifest_questions = get_questions_from_manifest_by_id(download_results_manifest)
        price_question = list(filter(lambda x: type(x) == Pricing, manifest_questions.values()))

        locked_at = datetime.strptime(project['lockedAt'], DATETIME_FORMAT)
        filename = '{}-{}-results'.format(locked_at.strftime('%Y-%m-%d'), inflection.parameterize(project['name']))
        formatted_locked_at = datetimeformat(locked_at)

        services = self.data_api_client.get_direct_award_project_services_iter(project_id=project['id'],
                                                                               user_id=current_user.id,
                                                                               fields=required_fields)

        all_services = []

        for service in services:
            if price_question:  # Assumption: only one pricing question per service - SW - 23/09/2017
                service['data'][price_question[0].id] = format_service_price(service['data'])

            all_services.append(service)

        search_meta = SearchMeta(search['searchUrl'], frameworks_by_slug)

        file_context = {
            'framework': frameworks_by_slug[framework_slug]['name'],
            'search': search,
            'project': project,
            'questions': manifest_questions,
            'services': all_services,
            'filename': filename,
            "sheetname": "Search results",
            'locked_at': formatted_locked_at,
            'search_summary': search_meta.search_summary.text_content(),
        }

        return file_context

    def get_file_data_and_column_styles(self, file_context):
        """Generate the structure and styling for the download from the file context"""
        file_rows = []

        # Assign the column styles
        column_styles = [
            {'stylename': 'col-wide'},  # Framework/supplier name
            {'stylename': 'col-wide'},  # Search ended/service name
            {'stylename': 'col-extra-wide'},     # summary/description
            {'stylename': 'col-wide'},  # price
            {'stylename': 'col-wide'},  # service page URL
            {'stylename': 'col-wide'},  # contact name
            {'stylename': 'col-wide'},  # contact telephone
            {'stylename': 'col-extra-wide'},     # contact email
        ]

        # Search meta - headers
        file_rows.append({
            'cells': ['Framework', 'Search ended', 'Search summary'],
            'meta': {'name': 'meta-header',
                     'row_styles': {'stylename': 'row-default'},
                     'cell_styles': {'stylename': 'cell-header'}},
        })

        # Search meta - data
        file_rows.append({
            'cells': [file_context['framework'], file_context['locked_at'], file_context['search_summary']],
            'meta': {'name': 'meta-header',
                     'row_styles': {'stylename': 'row-tall-optimal'},
                     'cell_styles': {'stylename': 'cell-default'}},
        })

        # Blank divider between the two sections
        file_rows.append({'cells': [], 'meta': {'name': 'divider'}})

        # Search results - headers
        content_headers = [question.name for question in file_context['questions'].values()]
        file_rows.append({
            'cells': ['Supplier name'] + content_headers + ['Service page URL', 'Contact name', 'Telephone', 'Email'],
            'meta': {'name': 'results-header',
                     'row_styles': {'stylename': 'row-default'},
                     'cell_styles': {'stylename': 'cell-header'}},
        })

        # Search results - data
        for service in file_context['services']:
            content_fields = [service['data'].get(question_id) for question_id in file_context['questions'].keys()]

            service_values = [
                service['supplier']['name']] + content_fields + [
                AnchorElement(href=url_for('main.get_service_by_id', service_id=service['id'], _external=True),
                              text=url_for('main.get_service_by_id', service_id=service['id'], _external=True)),
                service['supplier']['contact']['name'],
                service['supplier']['contact']['phone'],
                service['supplier']['contact']['email'],
            ]

            file_rows.append({
                'cells': service_values,
                'meta': {'name': 'results-{}'.format(service['id']),
                         'row_styles': {'stylename': 'row-default'},
                         'cell_styles': {'stylename': 'cell-default'}},
            })

        return file_rows, column_styles


direct_award.add_url_rule('/<string:framework_framework>/projects/<int:project_id>/results/download',
                          view_func=DownloadResultsView.as_view(str('download_results')),
                          methods=['GET'])
