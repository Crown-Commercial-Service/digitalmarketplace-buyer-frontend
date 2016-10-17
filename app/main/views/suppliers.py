# coding=utf-8
import re

from flask import render_template, current_app, flash
from flask_login import current_user, login_required
import flask_featureflags

from app.main import main
from app.api_client.data import DataAPIClient
from app.helpers.react.render import render_component


def can_view_supplier_page(code):
    if not current_user.is_authenticated:
        return False
    if current_user.role in ('buyer', 'admin'):
        return True
    return user_owns_page(code)


def user_owns_page(code):
    if current_user.role == 'supplier' and current_user.supplier_code == code:
        return True
    return False


@main.route('/supplier/<int:code>')
@login_required
def get_supplier(code):
    if not can_view_supplier_page(code):
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()

    supplier = DataAPIClient().get_supplier(code)['supplier']

    supplier_categories = set(
        price['serviceRole']['role'].replace('Junior ', '').replace('Senior ', '')  # Mind the white space after Junior
        for price in supplier['prices']
    )

    # supplier_casestudies = [{"id":"1","links":{"edit":"#edit", "delete":"#delete"},
    #                          "timeframe":"2015-2016",
    #                          "company":"Example Pty Ltd",
    #                          "title":"Giizmo Refactoring",
    #                          "sections":[
    #                              {"title":"In the beginning",
    #                               "content": "we did good"}]
    #                          }]
    supplier_casestudies = []
    for casestudy_id in supplier['case_study_ids']:
        casestudy = DataAPIClient().get_case_study(casestudy_id)['caseStudy']
        supplier_casestudies.append(casestudy)


    return render_template(
        'suppliers_details.html',
        supplier=supplier,
        supplier_categories=supplier_categories,
        supplier_casestudies=supplier_casestudies,
        user_owns_page=user_owns_page(code),
        render_component=render_component
    )
