# coding: utf-8
from __future__ import unicode_literals
import inflection
import sys

from flask import abort, render_template, request, redirect, url_for, flash, Response, current_app
from flask.views import View
from flask_login import current_user

from app import data_api_client
from .. import buyers, content_loader
from ..helpers.buyers_helpers import (
    get_framework_and_lot, get_sorted_responses_for_brief, count_unanswered_questions,
    brief_can_be_edited, add_unanswered_counts_to_briefs, is_brief_correct,
    section_has_at_least_one_required_question
)

from ..helpers.ods import SpreadSheet

from dmapiclient import HTTPError
from dmutils.dates import get_publishing_dates
from dmutils import csv_generator
from datetime import datetime

from odf.style import TextProperties, TableRowProperties, TableColumnProperties, TableCellProperties, FontFace

from io import BytesIO

from collections import Counter


@buyers.route('')
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


@buyers.route('/frameworks/<framework_slug>/requirements/<lot_slug>/create', methods=['GET'])
def start_new_brief(framework_slug, lot_slug):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           allowed_statuses=['live'], must_allow_brief=True)

    content = content_loader.get_manifest(framework_slug, 'edit_brief').filter(
        {'lot': lot['slug']}
    )

    section = content.get_section(content.get_next_editable_section_id())

    return render_template(
        "buyers/create_brief_question.html",
        brief={},
        framework=framework,
        lot=lot,
        section=section,
        question=section.questions[0],
    ), 200


@buyers.route('/frameworks/<framework_slug>/requirements/<lot_slug>/create', methods=['POST'])
def create_new_brief(framework_slug, lot_slug):

    framework, lot = get_framework_and_lot(framework_slug, lot_slug, data_api_client,
                                           allowed_statuses=['live'], must_allow_brief=True)

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
            "buyers/create_brief_question.html",
            data=update_data,
            brief={},
            framework=framework,
            lot=lot,
            section=section,
            question=section.questions[0],
            errors=errors
        ), 400

    return redirect(
        url_for(".view_brief_overview",
                framework_slug=framework_slug,
                lot_slug=lot_slug,
                brief_id=brief['id']))


@buyers.route('/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>', methods=['GET'])
def view_brief_overview(framework_slug, lot_slug, brief_id):
    framework, lot = get_framework_and_lot(
        framework_slug,
        lot_slug,
        data_api_client,
        allowed_statuses=['live', 'expired'],
        must_allow_brief=True
    )
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    content = content_loader.get_manifest(brief['frameworkSlug'], 'edit_brief').filter({'lot': brief['lotSlug']})
    sections = content.summary(brief)
    delete_requested = True if request.args.get('delete_requested') else False

    content_loader.load_messages(brief['frameworkSlug'], ['urls'])
    call_off_contract_url = content_loader.get_message(brief['frameworkSlug'], 'urls', 'call_off_contract_url')
    framework_agreement_url = content_loader.get_message(brief['frameworkSlug'], 'urls', 'framework_agreement_url')

    completed_sections = {}
    for section in sections:
        required, optional = count_unanswered_questions([section])
        if section_has_at_least_one_required_question(section):
            completed_sections[section.slug] = True if required == 0 else False
        else:
            completed_sections[section.slug] = True if optional == 0 else False

    brief['clarificationQuestions'] = [
        dict(question, number=index + 1)
        for index, question in enumerate(brief['clarificationQuestions'])
    ]

    return render_template(
        "buyers/brief_overview.html",
        framework=framework,
        confirm_remove=request.args.get("confirm_remove", None),
        brief=brief,
        sections=sections,
        completed_sections=completed_sections,
        step_sections=[section.step for section in sections if hasattr(section, 'step')],
        delete_requested=delete_requested,
        call_off_contract_url=call_off_contract_url,
        framework_agreement_url=framework_agreement_url,
    ), 200


@buyers.route('/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/<section_slug>', methods=['GET'])
def view_brief_section_summary(framework_slug, lot_slug, brief_id, section_slug):
    get_framework_and_lot(
        framework_slug,
        lot_slug,
        data_api_client,
        allowed_statuses=['live', 'expired'],
        must_allow_brief=True
    )
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
    '/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/edit/<section_slug>/<question_id>',
    methods=['GET'])
def edit_brief_question(framework_slug, lot_slug, brief_id, section_slug, question_id):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, allowed_statuses=['live'], must_allow_brief=True)
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

    return render_template(
        "buyers/edit_brief_question.html",
        brief=brief,
        section=section,
        question=question
    ), 200


@buyers.route(
    '/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/edit/<section_id>/<question_id>',
    methods=['POST'])
def update_brief_submission(framework_slug, lot_slug, brief_id, section_id, question_id):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, allowed_statuses=['live'], must_allow_brief=True)
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
            brief=brief,
            section=section,
            question=question,
            errors=errors
        ), 400

    if section.has_summary_page:
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


@buyers.route('/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/responses', methods=['GET'])
def view_brief_responses(framework_slug, lot_slug, brief_id):
    get_framework_and_lot(
        framework_slug,
        lot_slug,
        data_api_client,
        allowed_statuses=['live', 'expired'],
        must_allow_brief=True,
    )
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    if brief['status'] != "closed":
        abort(404)

    brief_responses = data_api_client.find_brief_responses(brief_id)['briefResponses']

    brief_responses_require_evidence = (
        datetime.strptime(current_app.config['FEATURE_FLAGS_NEW_SUPPLIER_FLOW'], "%Y-%m-%d")
        <= datetime.strptime(brief['publishedAt'][0:10], "%Y-%m-%d")
    )

    counter = Counter()

    for response in brief_responses:
        counter[all(response['essentialRequirements'])] += 1

    return render_template(
        "buyers/brief_responses.html",
        response_counts={"failed": counter[False], "eligible": counter[True]},
        brief_responses_require_evidence=brief_responses_require_evidence,
        brief=brief
    ), 200


class DownloadBriefResponsesView(View):
    def __init__(self, **kwargs):
        self.data_api_client = kwargs.pop('data_api_client', data_api_client)
        self.content_loader = kwargs.pop('content_loader', content_loader)

        super(View, self).__init__(**kwargs)

    def get_responses(self, brief):
        return get_sorted_responses_for_brief(brief, self.data_api_client)

    def get_context_data(self, **kwargs):
        get_framework_and_lot(
            kwargs['framework_slug'],
            kwargs['lot_slug'],
            self.data_api_client,
            allowed_statuses=['live', 'expired'],
            must_allow_brief=True,
        )

        brief = self.data_api_client.get_brief(kwargs['brief_id'])["briefs"]

        if not is_brief_correct(brief, kwargs['framework_slug'],
                                kwargs['lot_slug'], current_user.id):
            abort(404)

        if brief['status'] != "closed":
            abort(404)

        text_type = str if sys.version_info[0] == 3 else unicode
        filename = inflection.parameterize(text_type(brief['title']))

        kwargs.update({
            'brief': brief,
            'responses': self.get_responses(brief),
            'filename': 'supplier-responses-{0}'.format(filename),
        })

        return kwargs

    def get_questions(self, framework_slug, lot_slug, manifest):
        section = 'view-response-to-requirements'
        result = self.content_loader.get_manifest(framework_slug, manifest)\
                                    .filter({'lot': lot_slug}, dynamic=False)\
                                    .get_section(section)

        return result.questions if result else []

    def create_csv_response(self, context=None):
        column_headings = []
        question_key_sequence = []
        boolean_list_questions = []
        csv_rows = []
        brief = context['brief']

        questions = self.get_questions(context['framework_slug'],
                                       context['lot_slug'],
                                       'legacy_output_brief_response')

        # Build header row from manifest and add it to the list of rows
        for question in questions:
            question_key_sequence.append(question.id)
            if question['type'] == 'boolean_list' and brief.get(question.id):
                column_headings.extend(brief[question.id])
                boolean_list_questions.append(question.id)
            else:
                column_headings.append(question.name)
        csv_rows.append(column_headings)

        # Add a row for each eligible response received
        for brief_response in context['responses']:
            if all(brief_response['essentialRequirements']):
                row = []
                for key in question_key_sequence:
                    if key in boolean_list_questions:
                        row.extend(brief_response.get(key))
                    else:
                        row.append(brief_response.get(key))
                csv_rows.append(row)

        return Response(
            csv_generator.iter_csv(csv_rows),
            mimetype='text/csv',
            headers={
                "Content-Disposition": (
                    "attachment;filename=responses-to-requirements-{}.csv"
                ).format(brief['id']),
                "Content-Type": "text/csv; header=present"
            }
        ), 200

    @staticmethod
    def style_doc(doc):
        doc.add_font(FontFace(name="Arial", fontfamily="Arial"))
        standard_arial = {
            'fontfamily': 'Arial', 'fontnameasian': 'Arial', 'fontnamecomplex': 'Arial', 'fontsize': '11pt'
        }
        doc.add_style(
            "ce1",
            "table-cell",
            (TableCellProperties(wrapoption="wrap", verticalalign="top"), TextProperties(**standard_arial)),
            parentstylename="Default"
        )

        doc.add_style(
            "ce2",
            "table-cell",
            (
                TableCellProperties(wrapoption="wrap", verticalalign="top"),
                TextProperties(fontweight="bold", **standard_arial)
            ),
            parentstylename="Default"
        )

        doc.add_style(
            "ce3",
            "table-cell",
            (TableCellProperties(wrapoption="wrap", verticalalign="top"), TextProperties(**standard_arial))
        )

        doc.add_style(
            "co1",
            "table-column",
            (TableColumnProperties(columnwidth="150pt", breakbefore="auto"),)
        )

        doc.add_style(
            "co2",
            "table-column",
            (TableColumnProperties(columnwidth="300pt", breakbefore="auto"),)
        )

        doc.add_style(
            "ro1",
            "table-row",
            (TableRowProperties(rowheight="30pt", breakbefore="auto", useoptimalrowheight="false"),)
        )

        doc.add_style(
            "ro2",
            "table-row",
            (TableRowProperties(rowheight="30pt", breakbefore="auto", useoptimalrowheight="true"),)
        )

    @staticmethod
    def write_question(sheet, brief, question):
        if question._data['type'] in ('boolean_list', 'dynamic_list'):
            length = len(brief[question.id])

            for i, requirement in enumerate(brief[question.id]):
                row = sheet.create_row("{0}[{1}]".format(question.id, i))
                if i == 0:
                    row.write_cell(
                        question.name,
                        stylename="ce2",
                        numberrowsspanned=str(length)
                    )
                else:
                    row.write_covered_cell()
                row.write_cell(requirement, stylename="ce3")
        else:
            row = sheet.create_row(question.id, stylename="ro2")
            row.write_cell(
                question.name,
                stylename="ce2",
                numbercolumnsspanned="2"
            )
            row.write_covered_cell()

    @staticmethod
    def write_response(sheet, brief, question, response):
        if question._data['type'] == 'dynamic_list':
            if not brief.get(question.id):
                return

            for i, item in enumerate(response[question.id]):
                row = sheet.get_row("{0}[{1}]".format(question.id, i))
                # TODO this is stupid, fix it (key should not be hard coded)
                row.write_cell(item.get('evidence') or '', stylename="ce1")

        elif question.type == 'boolean_list' and brief.get(question.id):
            if not brief.get(question.id):
                return

            for i, item in enumerate(response[question.id]):
                row = sheet.get_row("{0}[{1}]".format(question.id, i))
                row.write_cell(str(bool(item)).lower(), stylename="ce1")

        else:
            sheet.get_row(question.id).write_cell(response.get(question.id, ''), stylename="ce1")

    def generate_ods(self, brief, responses):
        doc = SpreadSheet()
        self.style_doc(doc)

        sheet = doc.sheet("Supplier evidence")

        questions = self.get_questions(
            brief['frameworkSlug'],
            brief['lotSlug'],
            'output_brief_response'
        )

        # two intro columns for boolean and dynamic lists
        sheet.create_column(stylename="co1", defaultcellstylename="ce1")
        sheet.create_column(stylename="co1", defaultcellstylename="ce1")

        # HEADER
        row = sheet.create_row("header", stylename="ro1")
        row.write_cell(brief['title'], stylename="ce2", numbercolumnsspanned=str(len(responses) + 2))

        # QUESTIONS
        for question in questions:
            self.write_question(sheet, brief, question)
        # RESPONSES
        for response in responses:
            sheet.create_column(stylename="co2", defaultcellstylename="ce1")
            for question in questions:
                self.write_response(sheet, brief, question, response)

        return doc

    def create_ods_response(self, context=None):
        buf = BytesIO()

        self.generate_ods(context['brief'], context['responses']).save(buf)

        return Response(
            buf.getvalue(),
            mimetype='application/vnd.oasis.opendocument.spreadsheet',
            headers={
                "Content-Disposition": ("attachment;filename={0}.ods").format(context['filename']),
                "Content-Type": "application/vnd.oasis.opendocument.spreadsheet"
            }
        ), 200

    def create_response(self, context=None):
        responses = context['responses']

        if responses and 'essentialRequirementsMet' in responses[0]:
            return self.create_ods_response(context)

        return self.create_csv_response(context)

    def dispatch_request(self, **kwargs):
        context = self.get_context_data(**kwargs)

        return self.create_response(context)


buyers.add_url_rule('/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/responses/download',
                    view_func=DownloadBriefResponsesView.as_view(str('download_brief_responses')),
                    methods=['GET'])


@buyers.route('/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/publish', methods=['GET', 'POST'])
def publish_brief(framework_slug, lot_slug, brief_id):
    get_framework_and_lot(framework_slug, lot_slug, data_api_client, allowed_statuses=['live'], must_allow_brief=True)
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
        return redirect(
            # the 'published' parameter is for tracking this request by analytics
            url_for('.view_brief_overview', framework_slug=brief['frameworkSlug'], lot_slug=brief['lotSlug'],
                    brief_id=brief['id'], published='true'))
    else:
        #  requirements length is a required question but is handled separately to other
        #  required questions on the publish page if it's unanswered.
        if sections.get_section('set-how-long-your-requirements-will-be-open-for') and \
                sections.get_section('set-how-long-your-requirements-will-be-open-for').questions[0].answer_required:
                unanswered_required -= 1

        email_address = brief_users['emailAddress']
        dates = get_publishing_dates(brief)

        return render_template(
            "buyers/brief_publish_confirmation.html",
            email_address=email_address,
            question_and_answers=question_and_answers,
            unanswered_required=unanswered_required,
            sections=sections,
            brief=brief,
            dates=dates
        ), 200


@buyers.route('/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/timeline', methods=['GET'])
def view_brief_timeline(framework_slug, lot_slug, brief_id):
    get_framework_and_lot(
        framework_slug,
        lot_slug,
        data_api_client,
        allowed_statuses=['live', 'expired'],
        must_allow_brief=True
    )
    brief = data_api_client.get_brief(brief_id)["briefs"]
    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id) or brief.get('status') != 'live':
        abort(404)

    dates = get_publishing_dates(brief)

    return render_template(
        "buyers/brief_publish_confirmation.html",
        email_address=brief['users'][0]['emailAddress'],
        published=True,
        brief=brief,
        dates=dates
    ), 200


@buyers.route('/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/delete', methods=['POST'])
def delete_a_brief(framework_slug, lot_slug, brief_id):
    get_framework_and_lot(
        framework_slug,
        lot_slug,
        data_api_client,
        allowed_statuses=['live', 'expired'],
        must_allow_brief=True
    )
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id) or not brief_can_be_edited(brief):
        abort(404)

    data_api_client.delete_brief(brief_id, current_user.email_address)
    flash({"requirements_deleted": brief.get("title")})
    return redirect(url_for('.buyer_dashboard'))


@buyers.route(
    "/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/supplier-questions",
    methods=["GET"])
def supplier_questions(framework_slug, lot_slug, brief_id):
    get_framework_and_lot(
        framework_slug,
        lot_slug,
        data_api_client,
        allowed_statuses=['live', 'expired'],
        must_allow_brief=True
    )
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    if brief["status"] != "live":
        abort(404)

    brief['clarificationQuestions'] = [
        dict(question, number=index + 1)
        for index, question in enumerate(brief['clarificationQuestions'])
    ]

    return render_template(
        "buyers/supplier_questions.html",
        brief=brief,
    )


@buyers.route(
    "/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/supplier-questions/answer-question",
    methods=["GET", "POST"])
def add_supplier_question(framework_slug, lot_slug, brief_id):
    get_framework_and_lot(
        framework_slug,
        lot_slug, data_api_client,
        allowed_statuses=['live', 'expired'],
        must_allow_brief=True
    )
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    if brief["status"] != "live":
        abort(404)

    content = content_loader.get_manifest(brief['frameworkSlug'], "clarification_question").filter({})
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

    return render_template(
        "buyers/edit_brief_question.html",
        brief=brief,
        section=section,
        question=section.questions[0],
        button_label="Publish question and answer",
        errors=errors
    ), status_code
