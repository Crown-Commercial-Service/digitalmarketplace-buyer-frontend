from flask import abort, render_template, request, redirect, url_for, flash
from flask_login import current_user

from app import data_api_client
from .. import buyers, content_loader
from ...helpers.buyers_helpers import (
    count_suppliers_on_lot, get_framework_and_lot, is_brief_associated_with_user,
    count_unanswered_questions, brief_can_be_edited, add_unanswered_counts_to_briefs,
    clarification_questions_open
)

from dmapiclient import HTTPError


@buyers.route('/buyers')
def buyer_dashboard():
    user_briefs = data_api_client.find_briefs(current_user.id).get('briefs', [])
    draft_briefs = add_unanswered_counts_to_briefs([brief for brief in user_briefs if brief['status'] == 'draft'])
    live_briefs = [brief for brief in user_briefs if brief['status'] == 'live']

    return render_template(
        'buyers/dashboard.html',
        draft_briefs=draft_briefs,
        live_briefs=live_briefs
    )


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>', methods=['GET'])
def info_page_for_starting_a_brief(framework_slug, lot_slug):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)

    return render_template(
        "buyers/start_brief_info.html",
        framework=framework,
        lot=lot,
        supplier_count=count_suppliers_on_lot(framework, lot)
    ), 200


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/create', methods=['GET'])
def start_new_brief(framework_slug, lot_slug):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )

    section = content.get_section(content.get_next_editable_section_id())

    return render_template(
        "buyers/edit_brief_section.html",
        framework=framework,
        data={},
        section=section
    ), 200


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/create', methods=['POST'])
def create_new_brief(framework_slug, lot_slug):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)

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
            page_questions=section.get_field_names()
        )["briefs"]
    except HTTPError as e:
        update_data = section.unformat_data(update_data)
        errors = section.get_error_messages(e.message)

        return render_template(
            "buyers/edit_brief_section.html",
            framework=framework,
            data=update_data,
            section=section,
            errors=errors
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

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_associated_with_user(brief, current_user.id) or not brief_can_be_edited(brief):
        abort(404)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )
    section = content.get_section(section_id)
    if section is None or not section.editable:
        abort(404)

    return render_template(
        "buyers/edit_brief_section.html",
        framework=framework,
        data=brief,
        section=section
    ), 200


@buyers.route(
    '/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/edit/<section_id>',
    methods=['POST'])
def update_brief_submission(framework_slug, lot_slug, brief_id, section_id):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_associated_with_user(brief, current_user.id) or not brief_can_be_edited(brief):
        abort(404)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )
    section = content.get_section(section_id)
    if section is None or not section.editable:
        abort(404)

    update_data = section.get_data(request.form)

    try:
        data_api_client.update_brief(
            brief_id,
            update_data,
            updated_by=current_user.email_address,
            page_questions=section.get_field_names()
        )
    except HTTPError as e:
        update_data = section.unformat_data(update_data)
        errors = section.get_error_messages(e.message)

        return render_template(
            "buyers/edit_brief_section.html",
            framework=framework,
            data=update_data,
            section=section,
            errors=errors
        ), 200

    return redirect(
        url_for(".view_brief_summary", framework_slug=framework_slug, lot_slug=lot_slug, brief_id=brief_id)
    )


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>', methods=['GET'])
def view_brief_summary(framework_slug, lot_slug, brief_id):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_associated_with_user(brief, current_user.id):
        abort(404)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )
    sections = content.summary(brief)
    unanswered_required, unanswered_optional = count_unanswered_questions(sections)
    delete_requested = True if request.args.get('delete_requested') else False

    flattened_brief = []
    for section in sections:
        for question in section.questions:
            question.section_id = section.id

            # Look up display values for options that have different labels from values
            options = question.get('options')
            if options and question.value:
                for option in options:
                    if 'label' in option and 'value' in option and option['value'] == question.value:
                        question.display_value = option['label']
                        break

            flattened_brief.append(question)

    brief['clarificationQuestions'] = [
        dict(question, number=index+1)
        for index, question in enumerate(brief['clarificationQuestions'])
    ]

    return render_template(
        "buyers/brief_summary.html",
        framework=framework,
        lot=lot,
        confirm_remove=request.args.get("confirm_remove", None),
        brief_data=brief,
        flattened_brief=flattened_brief,
        unanswered_required=unanswered_required,
        unanswered_optional=unanswered_optional,
        can_publish=not unanswered_required,
        delete_requested=delete_requested,
        clarification_questions_open=clarification_questions_open(brief)
    ), 200


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/delete', methods=['POST'])
def delete_a_brief(framework_slug, lot_slug, brief_id):

    # Don't need the return values here; the call is just to test conditions on lot and framework
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_associated_with_user(brief, current_user.id):
        abort(404)

    if request.form.get('delete_confirmed'):
        data_api_client.delete_brief(brief_id, current_user.email_address)
        flash({"requirements_deleted": brief.get("title")})
        return redirect(url_for('.buyer_dashboard'))
    else:
        return redirect(
            url_for('.view_brief_summary', framework_slug=framework_slug, lot_slug=lot_slug,
                    brief_id=brief_id, delete_requested=True)
        )


@buyers.route("/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/answer-question",
              methods=["GET", "POST"])
def add_clarification_question(framework_slug, lot_slug, brief_id):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status="live", must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_associated_with_user(brief, current_user.id):
        abort(404)

    if brief["status"] != "live":
        abort(404)

    if not clarification_questions_open(brief):
        abort(404)

    content = content_loader.get_manifest(framework_slug, "clarification_question")
    section = content.get_section(content.get_next_editable_section_id())

    errors = {}
    status_code = 200

    if request.method == "POST":
        try:
            data_api_client.add_brief_clarification_question(brief_id,
                                                             request.form.get("question", ""),
                                                             request.form.get("answer", ""),
                                                             current_user.email_address)

            return redirect(
                url_for('.view_brief_summary', framework_slug=framework_slug, lot_slug=lot_slug,
                        brief_id=brief_id) + "#clarification-questions")
        except HTTPError as e:
            if e.status_code != 400:
                raise
            errors = section.get_error_messages(e.message)
            status_code = 400

    return render_template(
        "buyers/answer_question.html",
        framework=framework,
        lot=lot,
        brief=brief,
        data=request.form,
        section=section,
        errors=errors
    ), status_code
