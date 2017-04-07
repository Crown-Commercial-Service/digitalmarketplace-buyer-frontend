# coding: utf-8
from __future__ import unicode_literals
from dmutils.email import send_email, EmailError, hash_email
from flask.globals import current_app
import six
import csvx
import pendulum
import io
import re
import rollbar
from collections import OrderedDict as od

import xlsxwriter
from string import ascii_uppercase

from flask import abort, render_template, request, redirect, url_for, flash, Response
from flask_login import current_user

from app import data_api_client
from .. import buyers, content_loader
from app.helpers.buyers_helpers import (
    all_essentials_are_true, counts_for_failed_and_eligible_brief_responses,
    get_framework_and_lot, get_sorted_responses_for_brief, count_unanswered_questions,
    brief_can_be_edited, add_unanswered_counts_to_briefs, is_brief_correct,
    section_has_at_least_one_required_question
)
from dmutils.forms import render_template_with_csrf
from dmutils.logging import notify_team
from dmutils.documents import get_signed_url
from dmapiclient import HTTPError, APIError
from dmutils import s3
from react.render import render_component


@buyers.route('/buyers')
def buyer_dashboard():
    user_briefs = data_api_client.find_briefs(current_user.id).get('briefs', [])
    draft_briefs = add_unanswered_counts_to_briefs([brief for brief in user_briefs if brief['status'] == 'draft'],
                                                   content_loader)
    live_briefs = [brief for brief in user_briefs if brief['status'] == 'live']
    closed_briefs = [brief for brief in user_briefs if brief['status'] == 'closed']

    return render_template(
        'buyers/dashboard-briefs.html',
        draft_briefs=draft_briefs,
        live_briefs=live_briefs,
        closed_briefs=closed_briefs
    )


@buyers.route('/buyers/overview')
def buyer_overview():
    email_domain = current_user.email_address.split('@')[-1]
    teammembers_response = data_api_client.req.teammembers(email_domain).get()

    teammembers = list(sorted(teammembers_response['teammembers'], key=lambda tm: tm['name']))

    rendered_component = render_component(
        'bundles/BuyerDashboard/BuyerDashboardWidget.js',
        {
            'teammembers': teammembers,

            'meta': {
                'domain': email_domain,
                'teamname': teammembers_response['teamname']
            }
        }
    )

    return render_template(
        '_react.html',
        component=rendered_component,
    )


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/create', methods=['GET'])
def start_new_brief(framework_slug, lot_slug):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           status='live', must_allow_brief=True)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )

    section = content.get_section(content.get_next_editable_section_id())

    return render_template_with_csrf(
        "buyers/create_brief_question.html",
        brief={},
        framework=framework,
        lot=lot,
        section=section,
        question=section.questions[0],
    )


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

        return render_template_with_csrf(
            "buyers/create_brief_question.html",
            status_code=400,
            data=update_data,
            brief={},
            framework=framework,
            lot=lot,
            section=section,
            question=section.questions[0],
            errors=errors
        )

    return redirect(
        url_for(".view_brief_overview",
                framework_slug=framework_slug,
                lot_slug=lot_slug,
                brief_id=brief['id']))


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>', methods=['GET'])
def view_brief_overview(framework_slug, lot_slug, brief_id):
    framework, lot = get_framework_and_lot(
        framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    content = content_loader.get_manifest(brief['frameworkSlug'], 'edit_brief').filter({'lot': brief['lotSlug']})
    sections = content.summary(brief)
    delete_requested = True if request.args.get('delete_requested') else False

    completed_sections = {}
    for section in sections:
        required, optional = count_unanswered_questions([section])
        if section_has_at_least_one_required_question(section):
            completed_sections[section.slug] = True if required == 0 else False
        else:
            completed_sections[section.slug] = True if optional == 0 else False

    brief['clarificationQuestions'] = [
        dict(question, number=index+1)
        for index, question in enumerate(brief['clarificationQuestions'])
    ]

    return render_template_with_csrf(
        "buyers/brief_overview.html",
        framework=framework,
        confirm_remove=request.args.get("confirm_remove", None),
        brief=brief,
        sections=sections,
        completed_sections=completed_sections,
        step_sections=[section.step for section in sections if hasattr(section, 'step')],
        delete_requested=delete_requested,
    )


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/<section_slug>', methods=['GET'])
def view_brief_section_summary(framework_slug, lot_slug, brief_id, section_slug):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id) or not brief_can_be_edited(brief):
        abort(404)

    content = content_loader.get_manifest(brief['frameworkSlug'], 'edit_brief').filter({'lot': brief['lotSlug']})
    sections = content.summary(brief)
    section = sections.get_section(section_slug)

    if not section:
        abort(404)

    return render_template(
        "buyers/section_summary.html",
        brief=brief,
        section=section
    ), 200


@buyers.route(
    '/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/edit/<section_slug>/<question_id>',
    methods=['GET'])
def edit_brief_question(framework_slug, lot_slug, brief_id, section_slug, question_id):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id) or not brief_can_be_edited(brief):
        abort(404)

    content = content_loader.get_manifest(brief['frameworkSlug'], 'edit_brief').filter(
        {'lot': brief['lotSlug']}
    )
    section = content.get_section(section_slug)
    if section is None or not section.editable:
        abort(404)

    question = section.get_question(question_id)
    if not question:
        abort(404)

    return render_template_with_csrf(
        "buyers/edit_brief_question.html",
        brief=brief,
        section=section,
        question=question
    )


@buyers.route(
    '/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/edit/<section_id>/<question_id>',
    methods=['POST'])
def update_brief_submission(framework_slug, lot_slug, brief_id, section_id, question_id):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id) or not brief_can_be_edited(brief):
        abort(404)

    content = content_loader.get_manifest(brief['frameworkSlug'], 'edit_brief').filter({'lot': brief['lotSlug']})
    section = content.get_section(section_id)
    if section is None or not section.editable:
        abort(404)

    question = section.get_question(question_id)
    if not question:
        abort(404)

    update_data = question.get_data(request.form)

    question_ids = section.get_section_question_ids()

    question_id_index = None
    if question_id in question_ids:
        question_id_index = question_ids.index(question_id)

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
        return render_template_with_csrf(
            "buyers/edit_brief_question.html",
            status_code=400,
            brief=brief,
            section=section,
            question=question,
            errors=errors
        )

    if section.has_summary_page:
        # If there are more than 1 questions and it is not the last one.
        if question_id_index is not None and len(question_ids) > 1 and question_id_index != len(question_ids) - 1:
            return redirect(
                url_for('.edit_brief_question',
                        framework_slug=brief['frameworkSlug'],
                        lot_slug=brief['lotSlug'],
                        brief_id=brief['id'],
                        section_slug=section.slug,
                        # must be inside the current if statement to make sure it exists.
                        question_id=question_ids[question_id_index + 1]
                        )
            )

        return redirect(
            url_for(
                ".view_brief_section_summary",
                framework_slug=brief['frameworkSlug'],
                lot_slug=brief['lotSlug'],
                brief_id=brief['id'],
                section_slug=section.slug)
        )

    return redirect(
        url_for(
            ".view_brief_overview",
            framework_slug=brief['frameworkSlug'],
            lot_slug=brief['lotSlug'],
            brief_id=brief['id']
        )
    )


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/responses', methods=['GET'])
def view_brief_responses(framework_slug, lot_slug, brief_id):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    failed_count, eligible_count = counts_for_failed_and_eligible_brief_responses(brief["id"], data_api_client)

    return render_template(
        "buyers/brief_responses.html",
        response_counts={"failed": failed_count, "eligible": eligible_count},
        brief=brief
    ), 200


def prepared_response_contents_for_brief(brief, responses):
    ESS = 'essentialRequirements'
    NTH = 'niceToHaveRequirements'

    ess_req_names = brief.get(ESS, [])
    nth_req_names = brief.get(NTH, [])

    def csv_cell_sanitize(text):
        return re.sub(r"^(=|\+|-|@|!|\|{|}|\[|\]|<)+", '', unicode(text).strip())

    def row(r):
        answers = od()

        ess_responses = r.get(ESS, [])
        nth_responses = r.get(NTH, [])

        answers.update({'Supplier': r.get('supplierName', 'UNKNOWN')})
        answers.update({'Contact': r.get('respondToEmailAddress', 'UNKNOWN')})
        answers.update({'Availability Date': r.get('availability', 'UNKNOWN')})
        answers.update({'Day rate': r.get('dayRate', '')})
        for i in range(0, 3):
            answers.update({'Attached Document URL {}'.format(i+1): url_for('.download_brief_response_attachment',
                                                                            framework_slug=brief['frameworkSlug'],
                                                                            lot_slug=brief['lotSlug'],
                                                                            brief_id=brief['id'],
                                                                            response_id=r.get('id'),
                                                                            attachment_id=i,
                                                                            _external=True
                                                                            )
                            if i < len(r.get('attachedDocumentURL', [])) else ''})
        answers.update(zip(ess_req_names, ess_responses))
        answers.update(zip(nth_req_names, nth_responses))

        for k, v in answers.items():
            answers[k] = csv_cell_sanitize(v)

        return answers

    rows = [row(_) for _ in responses]
    return rows


@buyers.route(
    '/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<int:brief_id>/'
    'response/<int:response_id>/attachment/<int:attachment_id>',
    methods=['GET'])
def download_brief_response_attachment(framework_slug, lot_slug, brief_id, response_id, attachment_id):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    if brief['status'] != "closed":
        abort(404)

    response = data_api_client.get_brief_response(response_id)
    if not response or not response.get('briefResponses', {}).get('attachedDocumentURL'):
        abort(404)

    url = get_signed_url(current_app.config['S3_BUCKET_NAME'],
                         response['briefResponses']['attachedDocumentURL'][attachment_id], None)
    if not url:
        abort(404)
    return redirect(url)


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/responses/download',
              methods=['GET'])
def download_brief_responses(framework_slug, lot_slug, brief_id):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    if brief['status'] != "closed":
        abort(404)

    responses = get_sorted_responses_for_brief(brief, data_api_client)
    rows = prepared_response_contents_for_brief(brief, responses)

    first = rows[0].keys() if responses else []
    rows = [first] + [_.values() for _ in rows]

    transposed = list(six.moves.zip_longest(*rows))

    outdata = io.StringIO()
    with csvx.Writer(outdata) as csv_out:
        csv_out.write_rows(transposed)
        csvdata = outdata.getvalue()

    return Response(
        csvdata,
        mimetype='text/csv',
        headers={
            "Content-Disposition": "attachment;filename=responses-to-requirements-{}.csv".format(brief['id']),
            "Content-Type": "text/csv; header=present"
        }
    ), 200


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/responses/xlsxdownload',
              methods=['GET'])
def download_brief_responses_xlsx(framework_slug, lot_slug, brief_id):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    if brief['status'] != "closed":
        abort(404)

    responses = get_sorted_responses_for_brief(brief, data_api_client)
    rows = prepared_response_contents_for_brief(brief, responses)

    first = rows[0].keys() if responses else []
    rows = [first] + [_.values() for _ in rows]

    outdata = io.BytesIO()

    workbook = xlsxwriter.Workbook(outdata)
    bold = workbook.add_format({'bold': True})

    sheet = workbook.add_worksheet('Responses')

    COLUMN_WIDTH = 25

    for column_letter, r in zip(ascii_uppercase, rows):
        sheet.set_column('{x}:{x}'.format(x=column_letter), COLUMN_WIDTH)

        for row_number, c in enumerate(r, start=1):
            cell = '{}{}'.format(column_letter, row_number)

            if column_letter == 'A':
                sheet.write(cell, unicode(c), bold)
            else:
                sheet.write(cell, unicode(c))

    workbook.close()

    return Response(
        outdata.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            "Content-Disposition": "attachment;filename=responses-to-requirements-{}.xlsx".format(brief['id']),
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
    ), 200


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/publish', methods=['GET', 'POST'])
def publish_brief(framework_slug, lot_slug, brief_id):
    TZ = current_app.config['DM_TIMEZONE']

    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id) or not brief_can_be_edited(brief):
        abort(404)

    content = content_loader.get_manifest(brief['frameworkSlug'], 'edit_brief').filter({'lot': brief['lotSlug']})
    brief_users = brief['users'][0]
    brief_user_name = brief_users['name']

    sections = content.summary(brief)
    question_and_answers = {}
    question_and_answers_content = sections.get_question('questionAndAnswerSessionDetails')
    question_and_answers['id'] = question_and_answers_content['id']

    for section in sections:
        if section.get_question('questionAndAnswerSessionDetails') == question_and_answers_content:
            question_and_answers['slug'] = section['id']

    unanswered_required, unanswered_optional = count_unanswered_questions(sections)

    if request.method == 'POST':
        if unanswered_required > 0:
            abort(400, 'There are still unanswered required questions')
        data_api_client.publish_brief(brief_id, brief_user_name)

        # the 'published' parameter is for tracking this request by analytics
        brief_url = url_for('.view_brief_overview', framework_slug=brief['frameworkSlug'], lot_slug=brief['lotSlug'],
                            brief_id=brief['id'], published='true')

        brief_url_external = url_for('main.get_brief_by_id', framework_slug=brief['frameworkSlug'],
                                     brief_id=brief['id'], _external=True)

        send_new_opportunity_email_to_sellers(brief, brief_url_external)

        notification_message = '{}\n{}\nBy: {} ({})'.format(
            brief['title'],
            brief['organisation'],
            current_user.name,
            current_user.email_address
        )
        notify_team('A buyer has published a new opportunity', notification_message, brief_url_external)

        return redirect(brief_url)
    else:

        email_address = brief_users['emailAddress']

        return render_template_with_csrf(
            "buyers/brief_publish_confirmation.html",
            email_address=email_address,
            question_and_answers=question_and_answers,
            unanswered_required=unanswered_required,
            sections=sections,
            brief=brief,
            current_date=pendulum.now(TZ)
        )


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/timeline', methods=['GET'])
def view_brief_timeline(framework_slug, lot_slug, brief_id):
    TZ = current_app.config['DM_TIMEZONE']

    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id) or brief.get('status') != 'live':
        abort(404)

    return render_template(
        "buyers/brief_publish_confirmation.html",
        email_address=brief['users'][0]['emailAddress'],
        published=True,
        current_date=pendulum.now(TZ),
        brief=brief
    )


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/delete', methods=['POST'])
def delete_a_brief(framework_slug, lot_slug, brief_id):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id) or not brief_can_be_edited(brief):
        abort(404)

    data_api_client.delete_brief(brief_id, current_user.email_address)
    flash({"requirements_deleted": brief.get("title")})
    return redirect(url_for('.buyer_dashboard'))


@buyers.route(
    "/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/supplier-questions",
    methods=["GET"])
def supplier_questions(framework_slug, lot_slug, brief_id):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    if brief["status"] != "live":
        abort(404)

    brief['clarificationQuestions'] = [
        dict(question, number=index+1)
        for index, question in enumerate(brief['clarificationQuestions'])
    ]

    return render_template(
        "buyers/supplier_questions.html",
        brief=brief,
    )


@buyers.route(
    "/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/supplier-questions/answer-question",
    methods=["GET", "POST"])
def add_supplier_question(framework_slug, lot_slug, brief_id):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, status='live', must_allow_brief=True)
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    if brief["status"] != "live":
        abort(404)

    content = content_loader.get_manifest(brief['frameworkSlug'], "clarification_question")
    section = content.get_section(content.get_next_editable_section_id())
    update_data = section.get_data(request.form)

    errors = {}
    status_code = 200

    if request.method == "POST":
        try:
            data_api_client.add_brief_clarification_question(brief_id,
                                                             update_data['question'],
                                                             update_data['answer'],
                                                             current_user.email_address)

            return redirect(
                url_for('.supplier_questions', framework_slug=brief['frameworkSlug'], lot_slug=brief['lotSlug'],
                        brief_id=brief['id']))
        except HTTPError as e:
            if e.status_code != 400:
                raise
            brief.update(update_data)
            errors = section.get_error_messages(e.message)
            status_code = 400

    return render_template_with_csrf(
        "buyers/edit_brief_question.html",
        status_code=status_code,
        brief=brief,
        section=section,
        question=section.questions[0],
        button_label="Publish question and answer",
        errors=errors
    )


def send_new_opportunity_email_to_sellers(brief_json, brief_url):
    to_email_addresses = []
    if brief_json.get('sellerEmail'):
        to_email_addresses.append(brief_json['sellerEmail'])
    if brief_json.get('sellerEmailList'):
        to_email_addresses += brief_json['sellerEmailList']

    if to_email_addresses:
        email_body = render_template(
            'emails/seller_new_opportunity.html',
            brief=brief_json,
            brief_url=brief_url
        )

        for to_email_address in to_email_addresses:  # Send emails individually rather than sending to a list of emails

            try:
                send_email(
                    to_email_address,
                    email_body,
                    current_app.config['SELLER_NEW_OPPORTUNITY_EMAIL_SUBJECT'],
                    current_app.config['DM_GENERIC_NOREPLY_EMAIL'],
                    current_app.config['DM_GENERIC_SUPPORT_NAME'],
                )
            except EmailError as e:
                rollbar.report_exc_info()
                current_app.logger.error(
                    'seller new opportunity email failed to send. '
                    'error {error}',
                    extra={
                        'error': six.text_type(e), })
                abort(503, response='Failed to send seller new opportunity email.')
