# coding=utf-8
import re

from flask import render_template, current_app, flash
from flask_login import current_user, login_required

from app.main import main
from app.api_client.data import DataAPIClient


@main.route('/supplier/<int:code>')
@login_required
def get_supplier(code):
    if current_user.is_authenticated and current_user.role != 'buyer':
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
