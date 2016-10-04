# coding: utf-8
from flask import abort, render_template, request, redirect, url_for, flash, Response
from flask_login import current_user

from app import data_api_client
from .. import buyers
from app.helpers.buyers_helpers import is_brief_correct
from dmutils.forms import render_template_with_csrf

from dmapiclient import HTTPError, APIError
from app.main.forms.work_order_forms import WorkOrderSellerForm, FormFactory
from app.main.forms.work_order_data import questions


def create_work_order_from_brief(brief, seller):
    contacts = seller.get('contacts', None)
    contact = contacts[0] if contacts is not None and 0 < len(contacts) else None
    contact_name = contact.get('name') if contact is not None else ''

    return {
        'son': 'SON3364729',
        'seller': {
            'abn': seller.get('abn', ''),
            'name': seller.get('name', ''),
            'contact': contact_name,
        },
        'deliverables': brief.get('summary', ''),
        'orderPeriod': brief.get('contractLength', ''),
        'additionalTerms': brief.get('additionalTerms', ''),
        'securityClearance': brief.get('securityClearance', ''),
    }


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<int:brief_id>/work-orders/create',
              methods=['GET'])
def select_seller_for_work_order(framework_slug, lot_slug, brief_id):
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    form = WorkOrderSellerForm(data_api_client=data_api_client, brief_id=brief_id)

    return render_template_with_csrf('workorder/select-seller.html',
                                     brief=brief,
                                     form=form)


@buyers.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<int:brief_id>/work-orders/create',
              methods=['POST'])
def create_new_work_order(framework_slug, lot_slug, brief_id):
    brief = data_api_client.get_brief(brief_id)["briefs"]

    if not is_brief_correct(brief, framework_slug, lot_slug, current_user.id):
        abort(404)

    form = WorkOrderSellerForm(formdata=request.form, data_api_client=data_api_client, brief_id=brief_id)

    if not form.validate():
        return render_template_with_csrf(
            'workorder/select-seller.html',
            status_code=400,
            brief=brief,
            form=form
        )

    try:
        seller = data_api_client.get_supplier(form.seller.data)['supplier']

        work_order = data_api_client.create_work_order(
            briefId=brief_id,
            supplierCode=form.seller.data,
            workOrder=create_work_order_from_brief(brief, seller)
        )['workOrder']

    except APIError as e:
        form.errors['seller'] = [e.message]
        return render_template_with_csrf(
            'workorder/select-seller.html',
            status_code=e.status_code,
            brief=brief,
            form=form,
        )

    return redirect(
        url_for(
            'buyers.get_work_order',
            work_order_id=work_order['id'],
        )
    )


@buyers.route('/work-orders/<int:work_order_id>', methods=['GET'])
def get_work_order(work_order_id):
    try:
        work_order = data_api_client.get_work_order(work_order_id)['workOrder']
    except APIError as e:
        abort(e.status_code)

    return render_template_with_csrf('workorder/work-order-instruction-list.html',
                                     work_order=work_order,
                                     questions=questions)


@buyers.route('/work-orders/<int:work_order_id>/questions/<question_slug>', methods=['GET'])
def get_work_order_question(work_order_id, question_slug):
    try:
        work_order = data_api_client.get_work_order(work_order_id)['workOrder']
    except APIError as e:
        abort(e.status_code)

    if questions.get(question_slug, None) is None:
        abort(404)

    form = FormFactory(question_slug)
    value = work_order.get(question_slug, None)

    if value is not None:
        if questions[question_slug].get('type') == 'address':
            form.abn.data = value['abn']
            form.contact.data = value['contact']
            form.name.data = value['name']
        else:
            form[question_slug].data = value

    return render_template_with_csrf(
        'workorder/work-order-question.html',
        work_order_id=work_order_id,
        question_slug=question_slug,
        form=form
    )


@buyers.route('/work-orders/<int:work_order_id>/questions/<question_slug>', methods=['POST'])
def update_work_order_question(work_order_id, question_slug):
    try:
        data_api_client.get_work_order(work_order_id)['workOrder']
    except APIError as e:
        abort(e.status_code)

    if questions.get(question_slug, None) is None:
        abort(404)

    form = FormFactory(question_slug, formdata=request.form)

    if not form.validate():
        return render_template_with_csrf(
            'workorder/work-order-question.html',
            status_code=400,
            work_order_id=work_order_id,
            question_slug=question_slug,
            form=form
        )

    if questions[question_slug].get("type") == 'address':
        data = {question_slug: {
            'abn': request.form['abn'],
            'name': request.form['name'],
            'contact': request.form['contact']}
        }
    else:
        data = {question_slug: request.form[question_slug]}

    data_api_client.update_work_order(work_order_id, data)

    return redirect(
        url_for(
            'buyers.get_work_order',
            work_order_id=work_order_id,
        )
    )
