# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
import flask_featureflags
import json

from flask_login import current_user
from flask import abort, current_app, make_response, render_template, request, url_for, jsonify

from dmapiclient import APIError
from dmcontent.content_loader import ContentNotFoundError
from dmutils.forms import render_template_with_csrf
from app.main.utils import get_page_list

from app import data_api_client, content_loader
from app.main import main
from app.helpers.terms_helpers import check_terms_acceptance, get_current_terms_version

from ..forms.brief_forms import BriefSearchForm

from flask_weasyprint import HTML, render_pdf


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


@main.route('/seller-applications')
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

    def fix_reverted(input):
        (metrics, output) = input
        submitted_k = None
        reverted_k = None
        for k, v in enumerate(output):
            if v[0] == 'submit_application_count':
                submitted_k = k
            if v[0] == 'revert_application_count':
                reverted_k = k
        if reverted_k:
            for k, v in enumerate(output[reverted_k]):
                if k > 0:
                    output[submitted_k][k] = int(output[submitted_k][k] or 0) + int(output[reverted_k][k] or 0)
            del output[reverted_k]
            del metrics[metrics.index('revert_application_count')]
        return metrics, output

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
            metrics = values.keys()
            new_values = {}
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
            for metric in metrics:
                new_values[metric] = []
                for domain in domain_order:
                    if domain not in column_names:
                        new_values[metric].append(0)
                    else:
                        new_values[metric].append(values[metric][column_names.index(domain)])
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
                          'finish-profile',
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
    if 'unassessed_domain_count' in events:
        del events['unassessed_domain_count']
    (groups, applications) = fix_reverted(format_applications(events))

    (domain_columns, domain_groups, domains) \
        = format_metrics(data_api_client.req.metrics().domains().get(), "domain")
    (seller_type_columns, seller_type_groups, seller_types) \
        = format_metrics(data_api_client.req.metrics().applications().seller_types().get(), "seller_type")
    (steps_columns, steps_groups, steps) \
        = format_metrics(data_api_client.req.metrics().applications().steps().get(), "step")

    return render_template('charts.html',
                           applications=json.dumps(applications),
                           applications_groups=json.dumps(groups),
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

    is_restricted_brief = brief.get('sellerSelector', '') in ('someSellers', 'oneSeller')

    return render_template_with_csrf(
        'brief.html',
        brief=brief,
        brief_responses=brief_responses,
        content=brief_content,
        show_pdf_link=brief['status'] in ['live', 'closed'],
        is_restricted_brief=is_restricted_brief,
    )


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
