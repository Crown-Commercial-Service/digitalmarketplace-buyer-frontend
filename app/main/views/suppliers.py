# coding=utf-8
import re

from flask import render_template, current_app, flash, jsonify, redirect, url_for, request
from flask_login import current_user, login_required

from app.main import main
from app.api_client.data import DataAPIClient
from app.api_client.error import APIError
from react.response import from_response
from react.render import render_component
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
    casestudy['meta'] = {'editLink': url_for('.update_supplier_case_study', casestudy_id=casestudy_id),
                         'deleteLink': url_for('.delete_supplier_case_study', casestudy_id=casestudy_id)}
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


@main.route('/case-study/<int:casestudy_id>/delete', methods=['GET'])
@login_required
def delete_supplier_case_study(casestudy_id):
    casestudy = DataAPIClient().get_case_study(casestudy_id)['caseStudy']
    supplier_code = casestudy.get('supplierCode') if casestudy else None

    if not can_view_supplier_page(supplier_code):
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()

    DataAPIClient().delete_case_study(casestudy_id, current_user.email_address)
    flash({'casestudy_name': casestudy.get('title')}, 'casestudy_deleted')
    return redirect(
        url_for(
            'main.get_supplier',
            code=casestudy['supplierCode'],
        )
    )


@main.route('/case-study/create', methods=['POST'])
@login_required
def create_new_supplier_case_study():
    if not current_user.role == 'supplier':
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()

    casestudy = from_response(request)
    casestudy['supplierCode'] = current_user.supplier_code
    errors = _validate_case_study(casestudy)
    if errors:
        form = DmForm()
        rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js',
                                              {'form_options': {'csrf_token': form.csrf_token.current_token,
                                                                'errors': errors},
                                               'form': {'caseStudy': casestudy}})
        return render_template(
            '_react.html',
            component=rendered_component
        )

    try:
        case_study = DataAPIClient().create_case_study(
            caseStudy=casestudy
        )['caseStudy']

    except APIError as e:
        form = DmForm()
        flash('', 'error')
        rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js',
                                              {'form_options': {'csrf_token': form.csrf_token.current_token},
                                               'form': {'caseStudy': casestudy}})
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


@main.route('/case-study/<int:casestudy_id>/update', methods=['GET'])
@login_required
def edit_supplier_case_study(casestudy_id):
    casestudy = DataAPIClient().get_case_study(casestudy_id)['caseStudy']
    supplier_code = casestudy.get('supplierCode') if casestudy else None

    if not can_view_supplier_page(supplier_code):
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()

    form = DmForm()
    rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js', {
        'form_options': {'csrf_token': form.csrf_token.current_token, 'mode': 'edit'},
        'form': {'caseStudy': casestudy}})
    return render_template(
        '_react.html',
        component=rendered_component
    )


def _validate_case_study(casestudy):
    errors = {}
    requiredFields = ["acknowledge", "opportunity", "title", "client",
                      "projectLinks", "timeframe", "outcome", "approach"]
    for field in requiredFields:
        if not casestudy.get(field, None) or not casestudy.get(field)[0]:
            errors[field] = {"required": True}
    return errors


@main.route('/case-study/<int:casestudy_id>/update', methods=['POST'])
@login_required
def update_supplier_case_study(casestudy_id):
    old_casestudy = DataAPIClient().get_case_study(casestudy_id)['caseStudy']
    supplier_code = old_casestudy.get('supplierCode') if old_casestudy else None

    if not can_view_supplier_page(supplier_code):
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()

    casestudy = from_response(request)
    casestudy['id'] = casestudy_id
    casestudy['supplierCode'] = current_user.supplier_code
    errors = _validate_case_study(casestudy)
    if errors:
        form = DmForm()
        rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js',
                                              {'form_options': {'csrf_token': form.csrf_token.current_token,
                                                                'errors': errors, 'mode': 'edit'},
                                               'form': {'caseStudy': casestudy}})
        return render_template(
            '_react.html',
            component=rendered_component
        )

    try:
        case_study = DataAPIClient().update_case_study(casestudy_id, casestudy)['caseStudy']

    except APIError as e:
        form = DmForm()
        flash('', 'error')
        rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js',
                                              {'form_options': {'csrf_token': form.csrf_token.current_token},
                                               'form': {'caseStudy': casestudy}})
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
