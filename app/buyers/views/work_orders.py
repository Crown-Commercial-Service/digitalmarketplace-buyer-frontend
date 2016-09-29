# coding: utf-8
from flask import abort, render_template, request, redirect, url_for, flash, Response
from flask_login import current_user

from app import data_api_client
from .. import buyers
from app.helpers.buyers_helpers import is_brief_correct
from dmutils.forms import render_template_with_csrf

from dmapiclient import HTTPError, APIError
from app.main.forms.work_order_forms import WorkOrderSellerForm


def create_work_order_from_brief(brief, seller):
    contacts = seller.get('contacts', None)
    contact = contacts[0] if contacts is not None and 0 < len(contacts) else None
    contact_name = contact.get('name') if contact is not None else ''

    return {
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
        return render_template_with_csrf(
            'workorder/select-seller.html',
            status_code=e.status_code,
            brief=brief,
            form=form,
            error=e.message,
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

    return render_template_with_csrf('workorder/work-order-instruction-list.html', work_order=work_order)
