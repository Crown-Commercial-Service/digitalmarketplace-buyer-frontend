# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import io
import json
import xlsxwriter
import ast

from flask_login import current_user
from flask import abort, current_app, config, make_response, redirect, \
    render_template, request, session, url_for, jsonify, flash, Response
import flask_featureflags as feature

from dmutils.formats import DateFormatter
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
from app.api_client.error import APIError, HTTPError


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
        if not current_user.is_authenticated or brief['users'][0]['id'] != current_user.id:
            abort(404, "Opportunity '{}' can not be found".format(brief_id))

    if current_user.is_authenticated and current_user.role == 'supplier':
        brief_responses = data_api_client.find_brief_responses(
            brief_id, current_user.supplier_code)["briefResponses"]
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

    profile_application_id = None
    profile_application_status = None
    profile_application = None
    supplier = None
    unassessed_domains = {}
    assessed_domains = {}
    is_recruiter = False
    product_seller = False
    profile_url = None
    recruiter_domain_list = []
    supplier_assessments = {}
    supplier_framework = None

    if current_user.is_authenticated:
        if current_user.supplier_code is not None:
            supplier = data_api_client.get_supplier(
                current_user.supplier_code
            ).get('supplier', None)

        profile_application_id = current_user.application_id

        if supplier is not None:
            profile_url = '/supplier/{}'.format(supplier.get('code'))
            assessed_domains = supplier.get('domains').get('assessed', None)
            unassessed_domains = supplier.get('domains').get('unassessed', None)
            legacy_domains = supplier.get('domains').get('legacy', None)

            if profile_application_id is None:
                profile_application_id = supplier.get('application_id', None)
            is_recruiter = supplier.get('is_recruiter', False)
            if is_recruiter == 'true':
                is_recruiter = True
            else:
                is_recruiter = False
            if is_recruiter:
                for key, value in supplier.get('recruiter_info').items():
                    recruiter_domain_list.append(key)

            products = supplier.get('products', None)
            services = supplier.get('services', None)

            if products and not services:
                product_seller = any(products)
            supplier_code = supplier.get('code')
            supplier_assessments = data_api_client.req.assessments().supplier(supplier_code).get()

            if len(legacy_domains) != 0:
                for i in range(len(legacy_domains)):
                    supplier_assessments['assessed'].append(legacy_domains[i])

            supplier_framework_ids = supplier.get('frameworks')
            for i in range(len(supplier_framework_ids)):
                if supplier.get('frameworks')[i].get('framework_id') == 7:
                    supplier_framework = 'digital-marketplace'
            if supplier_framework is None:
                supplier_framework = 'digital-service-professionals'

        if profile_application_id is not None:
            try:
                profile_application = data_api_client.req.applications(profile_application_id).get()

                if unassessed_domains is None:
                    unassessed_domains = profile_application.get(
                        'application').get('supplier').get('domains', None).get('unassessed', None)
                if assessed_domains is None:
                    assessed_domains = profile_application.get(
                        'application').get('supplier').get('domains', None).get('assessed', None)

                profile_application_status = profile_application.get('application').get('status', None)
                if profile_application.get('application').get('type') == 'edit':
                    profile_application_status = 'approved'

            except APIError:
                pass
            except HTTPError:
                pass

    aoe_seller = False
    if not product_seller and not is_recruiter:
        aoe_seller = True

    return render_template_with_csrf(
        'brief.html',
        aoe_seller=aoe_seller,
        add_case_study_url=add_case_study_url,
        application_url=application_url,
        assessed_domains=assessed_domains,
        brief=brief,
        brief_responses=brief_responses,
        brief_of_current_user=brief_of_current_user,
        content=brief_content,
        is_recruiter=is_recruiter,
        is_restricted_brief=is_restricted_brief,
        product_seller=product_seller,
        profile_application_status=profile_application_status,
        profile_url=profile_url,
        recruiter_domain_list=recruiter_domain_list,
        show_pdf_link=brief['status'] in ['live', 'closed'],
        unassessed_domains=unassessed_domains,
        supplier_assessments=supplier_assessments,
        supplier_framework=supplier_framework
    )


@main.route('/<framework_slug>/opportunities/<brief_id>/response')
def get_brief_response_preview_by_id(framework_slug, brief_id):
    briefs = data_api_client.get_brief(brief_id)
    brief = briefs.get('briefs')
    application_url = url_for('main.index', _external=True) + "sellers/opportunities/{}/responses/create"\
        .format(brief['id'])
    if brief['status'] not in ['live', 'closed']:
        if not current_user.is_authenticated or brief['users'][0]['id'] != current_user.id:
            abort(404, "Opportunity '{}' can not be found".format(brief_id))

    hypothetical_dates = brief['dates'].get('hypothetical', None)
    if hypothetical_dates is None:
        published_date = brief['dates'].get('published_date', None)
        closing_time = brief['dates'].get('closing_time', None)
    else:
        published_date = hypothetical_dates.get('published_date', None)
        closing_time = hypothetical_dates.get('closing_time', None)

    outdata = io.BytesIO()

    workbook = xlsxwriter.Workbook(outdata)
    bold_header = workbook.add_format({'bg_color': '#e8f5fa', 'bold': True, 'text_wrap':  True})
    bold_question = workbook.add_format({'bg_color': '#f3f3f3', 'valign': 'top', 'text_wrap':  True,
                                         'border': 1, 'border_color': "#AAAAAA", 'bold': True})
    bold_red = workbook.add_format({'bold': True, 'font_color': '#fc0d1b', 'text_wrap':  True})
    italic_header = workbook.add_format({'bg_color': '#e8f5fa', 'italic': True})
    italic_lightgrey = workbook.add_format({'italic': True, 'font_color': '#999999'})
    italic_darkgrey_question = workbook.add_format({'italic': True, 'font_color': '#666666', 'bg_color': '#f3f3f3',
                                                    'valign': 'top', 'text_wrap':  True,
                                                    'border': 1, 'border_color': "#AAAAAA"})
    darkgrey = workbook.add_format({'font_color': '#666666', 'text_wrap':  True})
    heading = workbook.add_format({'bold': True, 'font_size': '14', 'text_wrap':  True})
    header = workbook.add_format({'bg_color': '#e8f5fa'})
    cta = workbook.add_format({'bg_color': 'd9ead4', 'align': 'center',
                               'color': 'blue', 'underline': 1, 'text_wrap':  True})
    bold_cta = workbook.add_format({'bg_color': 'd9ead4', 'bold': True, 'align': 'center'})
    question = workbook.add_format({'bg_color': '#f3f3f3', 'valign': 'top', 'text_wrap':  True,
                                    'border': 1, 'border_color': "#AAAAAA"})
    link = workbook.add_format({'bg_color': '#e8f5fa', 'color': 'blue', 'underline': 1})
    right_border_question = workbook.add_format({'right': 1, 'right_color': 'black', 'bg_color': '#f3f3f3',
                                                 'valign': 'top', 'text_wrap':  True, 'border': 1,
                                                 'border_color': "#AAAAAA"})
    sheet = workbook.add_worksheet('Response')

    sheet.set_column('E:E', 50)
    sheet.set_column('D:D', 5)
    sheet.set_column('C:C', 50)
    sheet.set_column('B:B', 30)
    sheet.set_column('A:A', 30)

    sheet.merge_range(0, 0, 0, 2, '',  italic_header)
    sheet.write_url('A1', application_url)
    sheet.write_rich_string('A1',  italic_header,
                            'Use this template if you are waiting to be assessed, or want to collaborate '
                            'with others, before submitting your response to this brief.\n'
                            'If you have been assessed and are ready to submit, you will need to '
                            'copy and paste your answers from this template into \n', link, application_url)
    sheet.write_string('D1', '', right_border_question)

    df = DateFormatter(current_app.config['DM_TIMEZONE'])
    sheet.write_string('E1', brief['title'], heading)
    sheet.write_string('E2', brief['summary'], darkgrey)
    sheet.write_string('E3', 'For: '+brief['organisation'], darkgrey)
    sheet.write_string('E4', 'Published: '+df.dateformat(published_date), darkgrey)
    sheet.write_string('E5', 'Closing date for application: ' +
                       df.datetimeformat(closing_time), bold_red)

    sheet.write_string('A2', 'Guidance', bold_question)
    sheet.write_string('B2', 'Question', bold_question)
    sheet.write_string('C2', 'Answer', bold_question)
    sheet.write_string('D2', '', right_border_question)
    sheet.write_string('A3', '', header)
    sheet.write_string('B3', 'Essential skills and experience', bold_header)
    sheet.write_string('D3', '', right_border_question)

    e_start = 4
    e = 4
    for essential in brief['essentialRequirements']:
        sheet.write_string('B'+str(e),  essential,  question)
        sheet.write_string('C'+str(e),  '150 words', italic_lightgrey)
        sheet.write_string('D'+str(e), '', right_border_question)
        e += 1
    sheet.merge_range(e_start-1, 0, e-2, 0, 'Essential skills and experience\n'
                                            'As a guide to answering the skills and experience criteria, '
                                            'you could explain:\n'
                                            '- What the situation was\n'
                                            '- The work the specialist or team completed\n'
                                            '- What the results were \n'
                                            'You can reuse examples if you wish. \n'
                                            '\n'
                                            'You must have all essential skills and experience '
                                            'to apply for this opportunity.\n'
                                            '150 words max ', italic_darkgrey_question)
    sheet.write_string('A'+str(e), '', header)
    sheet.write_string('B'+str(e), 'Nice to have skills and experience', bold_header)
    sheet.write_string('D'+str(e), '', right_border_question)
    n_start = e+1
    n = e+1
    for nice in brief['niceToHaveRequirements']:
        sheet.write_string('B'+str(n),  nice,  question)
        sheet.write_string('C'+str(n),  '150 words', italic_lightgrey)
        sheet.write_string('D'+str(n), '', right_border_question)
        n += 1
    sheet.merge_range(n_start-1, 0, n-2, 0, '', question)

    sheet.write_string('A'+str(n), '', question)
    sheet.write_string('B'+str(n), '', question)
    sheet.write_string('D'+str(n), '',  right_border_question)
    sheet.write_string('A'+str(n+1), '', question)
    sheet.write_string('B'+str(n+1), "When can you start?", bold_question)
    sheet.write_string('D'+str(n+1), '', right_border_question)
    sheet.write_string('A'+str(n+2), '', question)
    sheet.write_string('B'+str(n+2), '', question)
    sheet.write_string('D'+str(n+2), '', right_border_question)
    sheet.write_string('A'+str(n+3), "All communication about your application will be sent to this address",
                       italic_darkgrey_question)
    sheet.write_string('B'+str(n+3), "Contact email:", bold_question)
    sheet.write_string('D'+str(n+3), '', right_border_question)
    sheet.write_string('A'+str(n+4), '', question)
    sheet.write_string('B'+str(n+4), '', question)
    sheet.write_string('C'+str(n+4), '', question)
    sheet.write_string('D'+str(n+4), '', right_border_question)
    sheet.write_string('C'+str(n+5), 'Ready to apply?', bold_cta)
    sheet.write_url('C'+str(n+6), application_url, cta, application_url)
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
    try:
        metrics = data_api_client.get_metrics()
        suppliers_count = metrics['supplier_count']['value']
    except Exception as e:
        suppliers_count = 0
    props = {
        'form_options': {
            'seller_count': suppliers_count
        }
    }
    rendered_component = render_component('bundles/Collaborate/CollaborateLandingWidget.js', props)
    return render_template(
        '_react.html',
        breadcrumb_items=[
            {'link': url_for('main.index'), 'label': 'Home'},
            {'label': 'Collaborate'}
        ],
        component=rendered_component
    )


@main.route('/collaborate/code')
def collaborate_code():
    rendered_component = render_component('bundles/Collaborate/CollaborateCodeWidget.js', {})
    return render_template(
        '_react.html',
        breadcrumb_items=[
            {'link': url_for('main.index'), 'label': 'Home'},
            {'link': url_for('main.collaborate'), 'label': 'Collaborate'},
            {'label': 'Open source library'}
        ],
        component=rendered_component,
        main_class='collapse'
    )


@main.route('/collaborate/project/new')
def collaborate_create_project():
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
