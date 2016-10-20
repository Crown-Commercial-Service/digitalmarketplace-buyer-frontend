# coding=utf-8
import re

from flask import render_template, current_app, flash, jsonify, redirect, url_for, request
from flask_login import current_user, login_required
from wtforms.csrf.session import SessionCSRF
import flask_featureflags

from app.main import main
from app.api_client.data import DataAPIClient
from app.api_client.error import APIError
from app.helpers.react.render import render_component
from app.helpers.shared_helpers import request_wants_json
from dmutils.forms import DmForm


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

    supplier["categories"] = list(set(
        price['serviceRole']['role'].replace('Junior ', '').replace('Senior ', '')  # Mind the white space after Junior
        for price in supplier['prices']
    ))

    supplier["caseStudies"] = []
    for casestudy_id in supplier['case_study_ids']:
        casestudy = DataAPIClient().get_case_study(casestudy_id)['caseStudy']
        supplier["caseStudies"].append(casestudy)

    if request_wants_json():
        return jsonify(dict(supplier))

    return render_template(
        'suppliers_details.html',
        supplier=supplier,
        user_owns_page=user_owns_page(code),
        render_component=render_component
    )


@main.route('/case-study/<int:casestudy_id>')
@login_required
def get_supplier_case_study(casestudy_id):
    casestudy = DataAPIClient().get_case_study(casestudy_id)['caseStudy']
    supplier_code = casestudy.get('supplierCode') if casestudy else None

    if not can_view_supplier_page(supplier_code):
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()

    if request_wants_json():
        return jsonify(casestudy)

    rendered_component = render_component('bundles/CaseStudy/CaseStudyViewWidget.js', {"casestudy": dict(casestudy)})
    return render_template(
        '_react.html',
        component=rendered_component
    )


@main.route('/case-study/create', methods=['GET'])
@login_required
def new_supplier_case_study():
    if not current_user.role == 'supplier':
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()
    form = DmForm()
    rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js',
                                          {'form_options': {'csrf_token': form.csrf_token.current_token}})
    return render_template(
        '_react.html',
        component=rendered_component
    )


@main.route('/case-study/create', methods=['POST'])
@login_required
def create_new_supplier_case_study():
    if not current_user.role == 'supplier':
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()

    casestudy = {}
    for key in request.form.keys():
        if key not in ['csrf_token']:
            value = request.form.getlist(key)
            if len(value) == 1 and key not in ['projectLinks', 'outcome']:
                casestudy[key] = value[0]
            else:
                casestudy[key] = value
    casestudy['supplierCode'] = current_user.supplier_code

    try:
        case_study = DataAPIClient().create_case_study(
            caseStudy=casestudy
        )['caseStudy']

    except APIError as e:
        form = DmForm()
        rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js',
                                              {'errors': e.message,
                                               'form_options': {'csrf_token': form.csrf_token.current_token},
                                               'caseStudy': casestudy})
        return render_template(
            '_react.html',
            component=rendered_component
        )

    return redirect(
        url_for(
            'main.get_supplier_case_study',
            casestudy_id=case_study['id'],
        )
    )
