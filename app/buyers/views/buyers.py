# coding: utf-8
from __future__ import unicode_literals
import unicodecsv

from flask import abort, render_template, request, redirect, url_for, flash, Response
from flask_login import current_user

from app import data_api_client
from .. import buyers, content_loader
from ...helpers.buyers_helpers import (
    get_flattened_brief, all_essentials_are_true, counts_for_failed_and_eligible_brief_responses,
    get_framework_and_lot, get_sorted_responses_for_brief, is_brief_associated_with_user, count_unanswered_questions,
    brief_can_be_edited, add_unanswered_counts_to_briefs
)

from dmapiclient import HTTPError


@buyers.route('/buyers')
def buyer_dashboard():
    user_briefs = data_api_client.find_briefs(current_user.id).get('briefs', [])
    draft_briefs = add_unanswered_counts_to_briefs([brief for brief in user_briefs if brief['status'] == 'draft'],
                                                   content_loader)
    live_briefs = [brief for brief in user_briefs if brief['status'] == 'live']
    closed_briefs = [brief for brief in user_briefs if brief['status'] == 'closed']

    return render_template(
        'buyers/dashboard.html',
        draft_briefs=draft_briefs,
        live_briefs=live_briefs,
        closed_briefs=closed_briefs
    )


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/create', methods=['GET'])
def start_new_brief(framework_slug, lot_slug):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )

    section = content.get_section(content.get_next_editable_section_id())

    # TODO make sure we can still create briefs
    return render_template(
        "buyers/create_brief_question.html",
        framework=framework,
        brief_data={},
        section=section,
        question=section.questions[0],
        lot=lot
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
            "buyers/edit_brief_question.html",
            framework=framework,
            data=update_data,
            section=section.get('title'),
            errors=errors
        ), 400

    return redirect(
        url_for(".view_brief_overview",
                framework_slug=framework_slug,
                lot_slug=lot_slug,
                brief_id=brief['id']))


@buyers.route(
    '/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/edit/<section_slug>/<question_id>',
    methods=['GET'])
def edit_brief_question(framework_slug, lot_slug, brief_id, section_slug, question_id):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_associated_with_user(brief, current_user.id) or not brief_can_be_edited(brief):
        abort(404)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )
    section = content.get_section(section_slug)
    if section is None or not section.editable:
        abort(404)

    return render_template(
        "buyers/edit_brief_question.html",
        framework=framework,
        lot=lot,
        brief_data=brief,
        section=section,
        question=section.get_question(question_id)
    ), 200


@buyers.route(
    '/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/edit/<section_id>/<question_name>',
    methods=['POST'])
def update_brief_submission(framework_slug, lot_slug, brief_id, section_id, question_name):

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

    question = section.get_question(question_name)
    if not question:
        abort(404)

    update_data = question.get_data(request.form)

    try:
        data_api_client.update_brief(
            brief_id,
            update_data,
            updated_by=current_user.email_address,
            page_questions=question.form_fields
        )
    except HTTPError as e:
        update_data = section.unformat_data(update_data)
        errors = section.get_error_messages(e.message)

        # we need the brief_id to build breadcrumbs and the update_data to fill in the form.
        brief.update(update_data)
        return render_template(
            "buyers/edit_brief_question.html",
            framework=framework,
            lot=lot,
            brief_data=brief,
            section=section,
            question=question,
            errors=errors
        ), 200

    if section.has_summary_page:
        return redirect(
            url_for(
                ".view_brief_section_summary",
                framework_slug=framework_slug,
                lot_slug=lot_slug,
                brief_id=brief_id,
                section_slug=section.slug)
        )

    return redirect(
        url_for(".view_brief_overview", framework_slug=framework_slug, lot_slug=lot_slug, brief_id=brief_id)
    )


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>', methods=['GET'])
def view_brief_overview(framework_slug, lot_slug, brief_id):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client, must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_associated_with_user(brief, current_user.id):
        abort(404)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )
    sections = content.summary(brief)

    completed_sections = {}
    for section in sections:
        required, optional = count_unanswered_questions([section])
        completed_sections[section.slug] = True if required == 0 else False

    brief['clarificationQuestions'] = [
        dict(question, number=index+1)
        for index, question in enumerate(brief['clarificationQuestions'])
    ]

    return render_template(
        "buyers/brief_overview.html",
        framework=framework,
        lot=lot,
        confirm_remove=request.args.get("confirm_remove", None),
        brief_data=brief,
        sections=sections,
        completed_sections=completed_sections,
        step_sections=[section.step for section in sections if hasattr(section, 'step')],
    ), 200


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/<section_slug>', methods=['GET'])
def view_brief_section_summary(framework_slug, lot_slug, brief_id, section_slug):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]

    if brief["status"] != "draft":
        abort(404)

    if not is_brief_associated_with_user(brief, current_user.id):
        abort(404)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )
    sections = content.summary(brief)
    section = sections.get_section(section_slug)

    if not section:
        abort(404)

    return render_template(
        "buyers/section_summary.html",
        framework=framework,
        lot=lot,
        brief_data=brief,
        section=section
    ), 200


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/responses', methods=['GET'])
def view_brief_responses(framework_slug, lot_slug, brief_id):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client, must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_associated_with_user(brief, current_user.id):
        abort(404)

    failed_count, eligible_count = counts_for_failed_and_eligible_brief_responses(brief["id"], data_api_client)

    return render_template(
        "buyers/brief_responses.html",
        framework=framework,
        lot=lot,
        response_counts={"failed": failed_count, "eligible": eligible_count},
        brief_data=brief
    ), 200


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/responses/download',
              methods=['GET'])
def download_brief_responses(framework_slug, lot_slug, brief_id):
    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client, must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_associated_with_user(brief, current_user.id):
        abort(404)
    if brief['status'] != "closed":
        abort(404)

    sorted_brief_responses = get_sorted_responses_for_brief(brief_id, data_api_client)

    content = content_loader.get_manifest(framework['slug'], 'output_brief_response').filter({'lot': lot['slug']})
    section = content.get_section('view-response-to-requirements')

    column_headings = []
    question_key_sequence = []
    boolean_list_questions = []
    csv_rows = []

    # Build header row from manifest and add it to the list of rows
    for question in section.questions:
        question_key_sequence.append(question.id)
        if question['type'] == 'boolean_list':
            column_headings.extend(brief[question.id])
            boolean_list_questions.append(question.id)
        else:
            column_headings.append(question.name)
    csv_rows.append(column_headings)

    # Add a row for each eligible response received
    for brief_response in sorted_brief_responses:
        if all_essentials_are_true(brief_response):
            row = []
            for key in question_key_sequence:
                if key in boolean_list_questions:
                    row.extend(brief_response.get(key))
                else:
                    row.append(brief_response.get(key))
            csv_rows.append(row)

    def iter_csv(rows):
        class Line(object):
            def __init__(self):
                self._line = None

            def write(self, line):
                self._line = line

            def read(self):
                return self._line

        line = Line()
        writer = unicodecsv.writer(line, lineterminator='\n')
        for row in rows:
            writer.writerow(row)
            yield line.read()

    return Response(
        iter_csv(csv_rows),
        mimetype='text/csv',
        headers={
            "Content-Disposition": "attachment;filename=responses-to-requirements-{}.csv".format(brief['id']),
            "Content-Type": "text/csv; header=present"
        }
    ), 200


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/publish', methods=['GET', 'POST'])
def publish_brief(framework_slug, lot_slug, brief_id):
    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_associated_with_user(brief, current_user.id):
        abort(404)
    brief_users = brief['users'][0]
    brief_user_name = brief_users['name']

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )
    sections = content.summary(brief)

    unanswered_required, unanswered_optional = count_unanswered_questions(sections)
    if request.method == 'POST':
        if (unanswered_required > 0):
            abort(400, 'There are still unanswered required questions')
        data_api_client.update_brief_status(brief_id, 'live', brief_user_name)
        return redirect(
            url_for('.view_brief_summary', framework_slug=framework_slug, lot_slug=lot_slug,
                    brief_id=brief_id))
    else:
        flattened_brief = get_flattened_brief(sections)
        email_address = brief_users['emailAddress']

        return render_template(
            "buyers/brief_publish_confirmation.html",
            email_address=email_address,
            unanswered_required=unanswered_required,
            framework_slug=framework_slug,
            flattened_brief=flattened_brief,
            brief_data=brief,
            lot_slug=lot_slug,
            brief_id=brief_id
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
            url_for('.view_brief_overview', framework_slug=framework_slug, lot_slug=lot_slug,
                    brief_id=brief_id, delete_requested=True)
        )


@buyers.route(
    "/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/clarification-questions",
    methods=["GET"])
def clarification_questions(framework_slug, lot_slug, brief_id):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status="live", must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_associated_with_user(brief, current_user.id):
        abort(404)

    if brief["status"] != "live":
        abort(404)

    brief['clarificationQuestions'] = [
        dict(question, number=index+1)
        for index, question in enumerate(brief['clarificationQuestions'])
    ]

    return render_template(
        "buyers/clarification_questions.html",
        framework=framework,
        lot=lot,
        brief_data=brief,
    )


@buyers.route(
    "/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/clarification-questions/answer-question",
    methods=["GET", "POST"])
def add_clarification_question(framework_slug, lot_slug, brief_id):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status="live", must_allow_brief=True)

    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_associated_with_user(brief, current_user.id):
        abort(404)

    if brief["status"] != "live":
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
                url_for('.clarification_questions', framework_slug=framework_slug, lot_slug=lot_slug,
                        brief_id=brief_id))
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
