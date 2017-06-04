# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import io
import json
import xlsxwriter

from flask_login import current_user
from flask import abort, current_app, config, make_response, redirect, \
    render_template, request, session, url_for, jsonify, flash, Response
import flask_featureflags as feature

from dmutils.forms import DmForm, render_template_with_csrf
from react.response import from_response, validate_form_data
from react.render import render_component
from app.main.utils import get_page_list

from app import data_api_client, content_loader
from app.main import main
from app.helpers.terms_helpers import check_terms_acceptance, get_current_terms_version
from app.helpers.buyers_helpers import allowed_email_domain

from ..forms.brief_forms import BriefSearchForm

from flask_weasyprint import HTML, render_pdf
from app.api_client.data import DataAPIClient
from app.api_client.error import APIError


@main.route('/')
def index():
    try:
        metrics = data_api_client.get_metrics()
        buyers_count = metrics['buyer_count']['value']
        suppliers_count = metrics['supplier_count']['value']
        briefs_count = metrics['briefs_total']['value']
    except Exception as e:
        buyers_count = 0
        suppliers_count = 0
        briefs_count = 0
        current_app.logger.error(e)

    check_terms_acceptance()
    return render_template(
        'index.html',
        buyers_count=buyers_count,
        suppliers_count=suppliers_count,
        briefs_count=briefs_count
    )


@main.route('/metrics')
def metrics():
    data = data_api_client.get_metrics()
    del data["brief_response_count"]
    return jsonify(data)


@main.route('/charts')
def seller_applications_charts():
    def format_applications(metrics):
        output = []
        dates = set()

        for metric in metrics:
            for val in metrics[metric]:
                dates.add(val['ts'])
        output.append(['x'] + [x.split("T")[0] for x in sorted(list(dates))])

        for metric in metrics:
            data = [metric]
            for date in sorted(list(dates)):
                hasValue = False
                for val in metrics[metric]:
                    if val['ts'] == date:
                        hasValue = True
                        data.append(val['value'])
                if not hasValue:
                    data.append(None)
            output.append(data)

        return [x for x in metrics], output

    def format_metrics(columns, column_name):
        column_names = []
        values = {}

        for column in columns:
            del column['timestamp']
            column_names.append(column[column_name])
            for k in column.keys():
                if k not in values and k != column_name:
                    values[k] = []

        for k in values.keys():
            for column in columns:
                if k in column:
                    values[k].append(column[k])
                else:
                    values[k].append(None)

        # order seller type values from largest to smallest
        if column_name == 'seller_type':
            type_data = {x['seller_type']: x['count'] for x in columns}
            ordered_types = reversed(sorted(type_data, key=type_data.get))

            new_values = {'count': []}
            new_column_names = []
            for seller_type in ordered_types:
                new_column_names.append(seller_type)
                new_values['count'].append(type_data[seller_type])
            column_names = new_column_names
            values = new_values

        if column_name == 'domain':

            domain_order = ['Strategy and Policy',
                            'User research and Design',
                            'Agile delivery and Governance',
                            'Software engineering and Development',
                            'Support and Operations',
                            'Content and Publishing',
                            'Change, Training and Transformation',
                            'Marketing, Communications and Engagement',
                            'Cyber security',
                            'Data science',
                            'Emerging technologies']
            domain_names = {'Strategy and Policy': 'Strategy and policy',
                            'User research and Design': 'User research and design',
                            'Agile delivery and Governance': 'Agile delivery and governance',
                            'Software engineering and Development': 'Software engineering and development',
                            'Support and Operations': 'Support and operations',
                            'Content and Publishing': 'Content and publishing',
                            'Change, Training and Transformation': 'Change, training and transformation',
                            'Marketing, Communications and Engagement': 'Marketing, communications and engagement',
                            'Cyber security': 'Cyber security',
                            'Data science': 'Data science',
                            'Emerging technologies': 'Emerging technologies'}
            new_values = {'unsubmitted': [], 'completed': []}
            for domain in domain_order:
                if domain not in column_names:
                    new_values['unsubmitted'].append(0)
                    new_values['completed'].append(0)
                else:
                    if 'unsubmitted' in values:
                        new_values['unsubmitted'].append(values['unsubmitted'][column_names.index(domain)])
                    else:
                        new_values['unsubmitted'].append(0)
                    total = 0
                    if values.get('assessed') and values['assessed'][column_names.index(domain)]:
                        total += values['assessed'][column_names.index(domain)]
                    if values.get('submitted') and values['submitted'][column_names.index(domain)]:
                        total += values['submitted'][column_names.index(domain)]
                    if values.get('unassessed') and values['unassessed'][column_names.index(domain)]:
                        total += values['unassessed'][column_names.index(domain)]
                    new_values['completed'].append(total)
            column_names = [domain_names[x] for x in domain_order]
            values = new_values

        if column_name == 'step':
            new_values = []
            step_order = ['start',
                          'profile',
                          'business',
                          'info',
                          'disclosures',
                          'documents',
                          'tools',
                          'awards',
                          'recruiter',
                          'digital',
                          'casestudy',
                          'candidates',
                          'products',
                          'review',
                          ]
            for step in step_order:
                if step not in column_names:
                    new_values.append(0)
                else:
                    new_values.append(values['count'][column_names.index(step)])
            column_names = step_order
            values['count'] = new_values
        metrics = values.keys()
        output = [[k] + values[k] for k in values.keys()]
        return column_names, metrics, output
    events = data_api_client.req.metrics().applications().history().get()

    (groups, applications) = format_applications(dict((k, v) for k, v in events.items()
                                                      if k in ['started_application_count',
                                                               'completed_application_count']))

    (domain_columns, domain_groups, domains) \
        = format_metrics(data_api_client.req.metrics().domains().get(), "domain")
    (seller_type_columns, seller_type_groups, seller_types) \
        = format_metrics(data_api_client.req.metrics().applications().seller_types().get(), "seller_type")
    (steps_columns, steps_groups, steps) \
        = format_metrics(data_api_client.req.metrics().applications().steps().get(), "step")

    return render_template('charts.html',
                           applications=json.dumps(applications),
                           domains=json.dumps(domains),
                           domain_groups=json.dumps(domain_groups),
                           domain_columns=json.dumps(domain_columns),
                           seller_types=json.dumps(seller_types),
                           seller_type_groups=json.dumps(seller_type_groups),
                           seller_type_columns=json.dumps(seller_type_columns),
                           steps=json.dumps(steps),
                           steps_groups=json.dumps(steps_groups),
                           steps_columns=json.dumps(steps_columns),
                           )


@main.route('/metrics/history')
def metrics_historical():
    data = data_api_client.get_metrics_historical()
    del data["brief_response_count"]
    return jsonify(data)


@main.route('/<template_name>')
def content(template_name):
    try:
        return render_template('content/{}.html'.format(template_name))
    except:
        abort(404)


@main.route('/terms-of-use')
def terms_of_use():
    terms = get_current_terms_version()
    return render_template(
        'content/terms-of-use/_template.html',
        terms_content=terms.template_file,
        update_time=terms.datetime.date())


@main.route('/<framework_slug>/opportunities/<brief_id>')
def get_brief_by_id(framework_slug, brief_id):
    briefs = data_api_client.get_brief(brief_id)
    brief = briefs.get('briefs')
    if brief['status'] not in ['live', 'closed']:
        if not current_user.is_authenticated or (
                        brief['users'][0]['id'] != current_user.id and not allowed_email_domain(
                            current_user.id, brief, data_api_client
                )
        ):
            abort(404, "Opportunity '{}' can not be found".format(brief_id))

    if current_user.is_authenticated and current_user.role == 'supplier':
        brief_responses = data_api_client.find_brief_responses(brief_id, current_user.supplier_code)["briefResponses"]
    else:
        brief_responses = None

    brief['clarificationQuestions'] = [
        dict(question, number=index+1)
        for index, question in enumerate(brief['clarificationQuestions'])
    ]

    brief_content = content_loader.get_builder(framework_slug, 'display_brief').filter(
        brief
    )

    brief_of_current_user = False
    if not current_user.is_anonymous and len(brief.get('users')) > 0:
        brief_of_current_user = brief['users'][0]['id'] == current_user.id

    is_restricted_brief = brief.get('sellerSelector', '') in ('someSellers', 'oneSeller')

    application_url = "/sellers/opportunities/{}/responses/create".format(brief['id'])
    add_case_study_url = None

    return render_template_with_csrf(
        'brief.html',
        brief=brief,
        brief_responses=brief_responses,
        content=brief_content,
        show_pdf_link=brief['status'] in ['live', 'closed'],
        is_restricted_brief=is_restricted_brief,
        application_url=application_url,
        add_case_study_url=add_case_study_url,
        brief_of_current_user=brief_of_current_user
    )


@main.route('/<framework_slug>/opportunities/<brief_id>/response')
def get_brief_response_preview_by_id(framework_slug, brief_id):
    briefs = data_api_client.get_brief(brief_id)
    brief = briefs.get('briefs')
    if brief['status'] not in ['live', 'closed']:
        if not current_user.is_authenticated \
                or (
                    brief['users'][0]['id'] != current_user.id and
                    not allowed_email_domain(current_user.id, brief, data_api_client)
                ):
            abort(404, "Opportunity '{}' can not be found".format(brief_id))

    outdata = io.BytesIO()

    workbook = xlsxwriter.Workbook(outdata)
    bold = workbook.add_format({'bold': True})
    heading = workbook.add_format({'bold': True, 'font_size': '14'})
    header = workbook.add_format({'bg_color': '#e8f5fa'})
    question = workbook.add_format({'bg_color': '#f3f3f3', 'valign': 'top', 'text_wrap':  True,
                                    'border': 1, 'border_color': "#AAAAAA"})

    sheet = workbook.add_worksheet('Response')

    sheet.set_column('C:C', 70)
    sheet.set_column('B:B', 50, question)
    sheet.set_column('A:A', 50, question)
    sheet.set_row(0, 140, header)

    sheet.write_rich_string('A1',  heading, 'Apply for this opportunity', header,
                            '\nThe buyer will compare your response with other seller responses to create a shortlist '
                            'for the evaluation stage. To progress, consider each answer carefully.\n\n'
                            'As a guide, you could explain:\n\n'
                            '- What the situation was\n'
                            '- The work the specialist or team completed\n'
                            '- What the results were\n'
                            '\n'
                            'You can reuse examples if you wish.')

    e_start = 2
    e = 2
    for essential in brief['essentialRequirements']:
        sheet.write_rich_string('B'+str(e), bold, essential,  question, '\n\n150 words')
        e += 1
    sheet.merge_range(e_start-1, 0, e-2, 0, '', question)
    sheet.write_rich_string('A'+str(e_start), bold, 'Do you have the essential skills and experience?', question,
                            "\n\nYou must have all essential skills and experience to apply for this opportunity."
                            )
    n_start = e
    n = e
    for nice in brief['niceToHaveRequirements']:
        sheet.write_rich_string('B'+str(n), bold, nice, question, '\n\n150 words')
        n += 1
    sheet.merge_range(n_start-1, 0, n-2, 0, '', question)
    sheet.write_rich_string('A'+str(n_start), bold, 'Nice to have skills and experience...', question,
                            "\n\nYou must have all essential skills and experience to apply for this opportunity."
                            )

    sheet.write_rich_string('B'+str(n), bold, "When can you start?")
    sheet.write_rich_string('B'+str(n+1), bold, "Contact email:", question,
                            "\n\nAll communication about your application will be sent to this address")

    workbook.close()

    return Response(
        outdata.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            "Content-Disposition": "attachment;filename=brief-response-template-{}.xlsx".format(brief['id']),
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
    ), 200


@main.route('/<framework_slug>/opportunities/opportunity_<brief_id>.pdf')
def get_brief_pdf(framework_slug, brief_id):
    return render_pdf(url_for('.get_brief_by_id', framework_slug=framework_slug, brief_id=brief_id))


@main.route('/<framework_slug>/opportunities')
def list_opportunities(framework_slug):
    framework = data_api_client.get_framework(framework_slug)['frameworks']
    if not framework:
        abort(404, "No framework {}".format(framework_slug))

    form = BriefSearchForm(request.args, framework=framework, data_api_client=data_api_client)
    # disabling csrf protection as this should only ever be a GET request
    del form.csrf_token
    if not form.validate():
        abort(400, "Invalid form data")

    api_result = form.get_briefs()

    briefs = api_result["briefs"]
    meta = api_result['meta']

    results_per_page = meta['per_page']
    total_results = meta['total']
    current_page = int(request.args.get('page', 1))

    pages = get_page_list(results_per_page, total_results, current_page)

    html = render_template('search/briefs.html',
                           framework=framework,
                           form=form,
                           filters=form.get_filters(),
                           filters_applied=form.filters_applied(),
                           briefs=briefs,
                           lot_names=tuple(label for id_, label in form.lot.choices),
                           briefs_count=total_results,
                           pages=pages,
                           num_pages=pages[-1],
                           current_page=current_page,
                           link_args=request.args,
                           )
    response = make_response(html)
    if current_user.is_authenticated and current_user.has_role('buyer'):
        # Buyers can create new briefs and want to see their updates more quickly.
        response.cache_control.max_age = min(300, current_app.config['DM_DEFAULT_CACHE_MAX_AGE'])
    return response


@main.route('/collaborate')
def collaborate():
    if feature.is_active('COLLABORATE'):
        rendered_component = render_component('bundles/Collaborate/CollaborateLandingWidget.js', {})
        return render_template(
            '_react.html',
            breadcrumb_items=[
                {'link': url_for('main.index'), 'label': 'Home'},
                {'label': 'Collaborate'}
            ],
            component=rendered_component
        )


@main.route('/collaborate/project/new')
def collaborate_create_project():
    if feature.is_active('COLLABORATE'):
        form = DmForm()
        basename = url_for('.collaborate_create_project')
        props = {
            'form_options': {
                'csrf_token': form.csrf_token.current_token
            },
            'project': {
            },
            'basename': basename
        }

        if 'project' in session:
            props['projectForm'] = session['project']

        rendered_component = render_component('bundles/Collaborate/ProjectFormWidget.js', props)

        return render_template(
            '_react.html',
            breadcrumb_items=[
                {'link': url_for('main.index'), 'label': 'Home'},
                {'link': url_for('main.collaborate'), 'label': 'Collaborate'},
                {'label': 'Add project'}
            ],
            component=rendered_component
        )


@main.route('/collaborate/project/new', methods=['POST'])
def collaborate_create_project_submit():
    if feature.is_active('COLLABORATE'):
        project = from_response(request)

        fields = ['title', 'client', 'stage']

        basename = url_for('.collaborate_create_project')
        errors = validate_form_data(project, fields)
        if errors:
            form = DmForm()
            rendered_component = render_component('bundles/Collaborate/ProjectFormWidget.js', {
                'form_options': {
                    'csrf_token': form.csrf_token.current_token,
                    'errors': errors
                },
                'projectForm': project,
                'basename': basename
            })

            return render_template(
                '_react.html',
                breadcrumb_items=[
                    {'link': url_for('main.index'), 'label': 'Home'},
                    {'link': url_for('main.collaborate'), 'label': 'Collaborate'},
                    {'label': 'Add project'}
                ],
                component=rendered_component
            )

        try:
            project = data_api_client.req.projects().post(data={'project': project})['project']

            rendered_component = render_component('bundles/Collaborate/ProjectSubmitConfirmationWidget.js', {})

            return render_template(
                '_react.html',
                breadcrumb_items=[
                    {'link': url_for('main.index'), 'label': 'Home'},
                    {'link': url_for('main.collaborate'), 'label': 'Collaborate'},
                    {'label': 'Add project'}
                ],
                component=rendered_component
            )

        except APIError as e:
            form = DmForm()
            flash('', 'error')
            rendered_component = render_component('bundles/Collaborate/ProjectFormWidget.js', {
                'form_options': {
                    'csrf_token': form.csrf_token.current_token
                },
                'projectForm': project,
                'basename': basename
            })

            return render_template(
                '_react.html',
                breadcrumb_items=[
                    {'link': url_for('main.index'), 'label': 'Home'},
                    {'link': url_for('main.collaborate'), 'label': 'Collaborate'},
                    {'label': 'Add project'}
                ],
                component=rendered_component
            )


@main.route('/collaborate/project/<int:id>')
def collaborate_view_project(id):
    if feature.is_active('COLLABORATE'):
        project = data_api_client.req.projects(id).get()['project']
        if project.get('status', '') != 'published':
            abort(404)
        rendered_component = render_component('bundles/Collaborate/ProjectViewWidget.js', {'project': project})
        return render_template(
            '_react.html',
            breadcrumb_items=[
                {'link': url_for('main.index'), 'label': 'Home'},
                {'link': url_for('main.collaborate'), 'label': 'Collaborate'},
                {'label': project['title']}
            ],
            component=rendered_component,
            main_class='collapse'
        )
