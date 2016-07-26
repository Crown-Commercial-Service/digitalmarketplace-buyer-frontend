# coding=utf-8
from string import ascii_uppercase
from app.main import main
from flask import render_template, request, abort
from app import data_api_client
from dmapiclient import APIError
from ...helpers.shared_helpers import parse_link
import re

try:
    from urlparse import urlparse, parse_qs
except ImportError:
    from urllib.parse import urlparse, parse_qs


def process_prefix(prefix=None, format='view'):
    if prefix == u"other":  # special case
        if format == 'api':
            return u"other"
        else:
            return prefix
    if is_alpha(prefix):
        return prefix[:1].upper()
    return u"A"  # default


def is_alpha(character):
    reg = "^[A-Za-z]{1}$"  # valid prefix
    return re.search(reg, character)


@main.route('/suppliers/<int:code>')
def get_supplier(code):
    supplier = data_api_client.get_supplier(code)['supplier']

    supplier_categories = set(
        price['serviceRole']['role'].replace('Junior', '').replace('Senior', '')
        for price in supplier['prices']
    )

    return render_template(
        'suppliers_details.html',
        supplier=supplier,
        supplier_categories=supplier_categories,
    )
