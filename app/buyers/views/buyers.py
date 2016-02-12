from flask import abort, render_template, request, redirect, url_for
from flask_login import current_user

from app import data_api_client
from .. import buyers, content_loader
from ...helpers.buyers_helpers import count_suppliers_on_lot, get_framework_and_lot
from ...helpers.search_helpers import get_template_data

from dmapiclient import HTTPError


@buyers.route('/buyers')
def buyer_dashboard():
    template_data = get_template_data(buyers, {})
    user_briefs = data_api_client.find_briefs(current_user.id).get('briefs', [])
    draft_briefs = [brief for brief in user_briefs if brief['status'] == 'draft']
    live_briefs = [brief for brief in user_briefs if brief['status'] == 'live']

    return render_template(
        'buyers/dashboard.html',
        draft_briefs=draft_briefs,
        live_briefs=live_briefs,
        **template_data
    )


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>', methods=['GET'])
def info_page_for_starting_a_brief(framework_slug, lot_slug):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client)

    if framework['status'] != 'live':
        abort(404)
    if not lot['allowsBrief']:
        abort(404)

    return render_template(
        "buyers/start_brief_info.html",
        framework=framework,
        lot=lot,
        supplier_count=count_suppliers_on_lot(framework, lot),
        **dict(buyers.config['BASE_TEMPLATE_DATA'])
    ), 200


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/create', methods=['GET'])
def start_new_brief(framework_slug, lot_slug):
    """Page to kick off creation of a new brief."""

    framework = data_api_client.get_framework(framework_slug)['frameworks']
    if framework['status'] != 'live':
        abort(404)

    try:
        lot = next(lot for lot in framework['lots'] if lot['slug'] == lot_slug)
    except StopIteration:
        abort(404)
    if not lot['allowsBrief']:
        abort(404)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )

    section = content.get_section(content.get_next_editable_section_id())

    return render_template(
        "buyers/edit_brief_section.html",
        framework=framework,
        data={},
        section=section,
        **dict(buyers.config['BASE_TEMPLATE_DATA'])
    ), 200


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/create', methods=['POST'])
def create_new_brief(framework_slug, lot_slug):
    framework = data_api_client.get_framework(framework_slug)["frameworks"]
    if framework["status"] != "live":
        abort(404)

    try:
        lot = next(lot for lot in framework['lots'] if lot['slug'] == lot_slug)
    except StopIteration:
        abort(404)
    if not lot['allowsBrief']:
        abort(404)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )

    section = content.get_section(content.get_next_editable_section_id())

    update_data = section.get_data(request.form)

    try:
        brief = data_api_client.create_brief(
            framework_slug,
            lot_slug,
            current_user.id,
            update_data,
            updated_by=current_user.email_address,
            page_questions=update_data.keys()
        )["briefs"]
    except HTTPError as e:
        update_data = section.unformat_data(update_data)
        errors = section.get_error_messages(e.message, lot_slug)

        return render_template(
            "buyers/edit_brief_section.html",
            framework=framework,
            data=update_data,
            section=section,
            errors=errors,
            **dict(buyers.config['BASE_TEMPLATE_DATA'])
        ), 400

    return redirect(
        url_for(".edit_brief_submission",
                framework_slug=framework_slug,
                lot_slug=lot_slug,
                brief_id=brief['id'],
                section_id=content.get_next_editable_section_id(section.slug)))


@buyers.route(
    '/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/edit/<section_id>',
    methods=['GET'])
def edit_brief_submission(framework_slug, lot_slug, brief_id, section_id):
    framework = data_api_client.get_framework(framework_slug)["frameworks"]
    if framework["status"] != "live":
        abort(404)

    try:
        lot = next(lot for lot in framework['lots'] if lot['slug'] == lot_slug)
    except StopIteration:
        abort(404)
    if not lot['allowsBrief']:
        abort(404)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )

    brief = data_api_client.get_brief(brief_id)["briefs"]
    # TODO: cannot edit published brief
    # TODO: update dmutils
    # TODO: fix javascript for lists
    section = content.get_section(section_id)

    return render_template(
        "buyers/edit_brief_section.html",
        framework=framework,
        data=brief,
        section=section,
        **dict(buyers.config['BASE_TEMPLATE_DATA'])
    ), 200


@buyers.route(
    '/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/edit/<section_id>',
    methods=['POST'])
def update_brief_submission(framework_slug, lot_slug, brief_id, section_id):
    framework = data_api_client.get_framework(framework_slug)["frameworks"]
    if framework["status"] != "live":
        abort(404)

    try:
        lot = next(lot for lot in framework['lots'] if lot['slug'] == lot_slug)
    except StopIteration:
        abort(404)
    if not lot['allowsBrief']:
        abort(404)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )

    # TODO: cannot edit published brief
    brief = data_api_client.get_brief(brief_id)["briefs"]
    section = content.get_section(section_id)

    update_data = section.get_data(request.form)

    try:
        brief = data_api_client.update_brief(
            brief_id,
            update_data,
            updated_by=current_user.email_address,
            page_questions=update_data.keys()
        )["briefs"]
    except HTTPError as e:
        update_data = section.unformat_data(update_data)
        errors = section.get_error_messages(e.message, lot_slug)

        return render_template(
            "buyers/edit_brief_section.html",
            framework=framework,
            data=update_data,
            section=section,
            errors=errors,
            **dict(buyers.config['BASE_TEMPLATE_DATA'])
        ), 200

    next_section = content.get_next_editable_section_id(section.slug)
    if next_section:
        return redirect(
            url_for(".edit_brief_submission",
                    framework_slug=framework_slug,
                    lot_slug=lot_slug,
                    brief_id=brief['id'],
                    section_id=next_section))
    else:
        return redirect(url_for(".buyer_dashboard"))
