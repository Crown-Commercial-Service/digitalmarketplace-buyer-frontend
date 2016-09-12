# coding=utf-8
import re

from flask import render_template, current_app, flash
from flask_login import current_user, login_required
import flask_featureflags

from app.main import main
from app.api_client.data import DataAPIClient


def can_view_supplier_page(code):
    if not current_user.is_authenticated:
        return False
    if current_user.role in ('buyer', 'admin'):
        return True
    if flask_featureflags.is_active('SUPPLIERS_VIEW_OWN_PAGE') and \
       current_user.role == 'supplier' and current_user.supplier_code == code:
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

    return render_template(
        'suppliers_details.html',
        supplier=supplier,
        supplier_categories=supplier_categories,
    )
