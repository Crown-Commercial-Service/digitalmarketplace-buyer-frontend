# coding=utf-8

from flask import render_template, current_app, flash, jsonify, url_for
from flask_login import current_user, login_required

from app.main import main
from app.api_client.data import DataAPIClient
from app import data_api_client
from react.render import render_component
from app.helpers.shared_helpers import request_wants_json


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

    owns_profile = user_owns_page(code)

    if request_wants_json():
        return jsonify(dict(supplier))

    # add business/authorized representative contact details
    if len(supplier['contacts']) > 0:
        supplier['contact_email'] = supplier.get('contact_email') or supplier['contacts'][0]['email']
        supplier['contact_phone'] = supplier.get('contact_phone') or supplier['contacts'][0]['phone']
        supplier['contact_name'] = supplier.get('contact_name') or supplier['contacts'][0]['name']
        supplier['representative'] = supplier.get('representative') or supplier['contacts'][0]['name']
    props = {"application": {key: supplier[key] for key in supplier if key not in ['disclosures']}}
    props['application']['case_study_url'] = '/case-study/'
    props['application']['public_profile'] = not owns_profile
    props['application']['recruiter'] = 'yes' if supplier.get('is_recruiter') == 'true' else 'no'
    props['application']['digital_marketplace_panel'] = False
    digital_marketplace_framework = data_api_client.req.frameworks('digital-marketplace').get()
    for framework in supplier.get('frameworks', []):
        if framework['framework_id'] == digital_marketplace_framework['frameworks']['id']:
            props['application']['digital_marketplace_panel'] = True
    props['application']['dsp_panel'] = len(supplier.get('domains', {'legacy': []})['legacy']) > 0
    props['basename'] = url_for('.get_supplier', code=code)
    props['form_options'] = {
        'action': "/sellers/edit",
        'submit_url': "/sellers/edit"
    }

    rendered_component = render_component('bundles/SellerRegistration/ApplicationPreviewWidget.js', props)

    return render_template(
        '_react.html',
        component=rendered_component,
        breadcrumb_items=[
          {'link': url_for('main.index'), 'label': 'Home'},
          {'link': url_for('main.supplier_search'), 'label': 'Seller catalogue'},
          {'label': 'Seller details'}
        ],
        main_class='collapse' if not owns_profile else None
    )


@main.route('/case-study/<int:casestudy_id>')
@login_required
def get_supplier_case_study(casestudy_id):
    casestudy = DataAPIClient().get_case_study(casestudy_id)['caseStudy']

    supplier_code = casestudy.get('supplierCode') if casestudy else None
    if supplier_code:
        supplier = DataAPIClient().get_supplier(supplier_code)['supplier']
        casestudy['supplier_name'] = supplier['name']
        casestudy['supplier_url'] = url_for('main.get_supplier', code=supplier_code)
    else:
        # buyers do not get referee data
        if 'refereeEmail' in casestudy:
            del casestudy['refereeEmail']
        if 'refereeName' in casestudy:
            del casestudy['refereeName']
        if 'refereePosition' in casestudy:
            del casestudy['refereePosition']

    if not can_view_supplier_page(supplier_code):
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()

    if request_wants_json():
        return jsonify(casestudy)

    rendered_component = render_component('bundles/CaseStudy/CaseStudyViewWidget.js', {"casestudy": dict(casestudy)})
    return render_template(
        '_react.html',
        breadcrumb_items=[
            {'link': url_for('main.index'), 'label': 'Home'},
            {'link': url_for('main.supplier_search'), 'label': 'Seller catalogue'},
            {'link': url_for('main.get_supplier', code=supplier_code), 'label': 'Seller details'},
            {'label': 'Case Study'}
        ],
        component=rendered_component
    )
