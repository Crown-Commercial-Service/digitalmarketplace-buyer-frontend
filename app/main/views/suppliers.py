# coding=utf-8
import re

from flask import render_template
from flask_login import login_required

from app.main import main
from app.api_client.data import DataAPIClient


@main.route('/supplier/<int:code>')
@login_required
def get_supplier(code):
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
