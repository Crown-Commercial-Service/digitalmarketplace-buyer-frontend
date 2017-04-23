# coding=utf-8

from flask import render_template, current_app, flash, jsonify, redirect, url_for, request, session
from flask_login import current_user, login_required
import flask_featureflags as feature

from app.main import main
from app.api_client.data import DataAPIClient
from app import data_api_client
from app.api_client.error import APIError
from react.response import from_response, validate_form_data
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

    owns_profile = user_owns_page(code)

    if request_wants_json():
        return jsonify(dict(supplier))
    if feature.is_active('NEW_SELLER_PROFILE'):
        # add business/authorized representative contact details
        if len(supplier['contacts']) > 0:
            supplier['contact_email'] = supplier['contacts'][0]['email']
            supplier['contact_phone'] = supplier['contacts'][0]['phone']
            supplier['contact_name'] = supplier['contacts'][0]['name']
            supplier['representative'] = supplier['contacts'][0]['name']
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
    return render_template(
        'suppliers_details.html',
        supplier=supplier,
        user_owns_page=owns_profile,
        render_component=render_component
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
    if current_user.role == 'supplier':
        casestudy['meta'] = {'editLink': url_for('.update_supplier_case_study', casestudy_id=casestudy_id),
                             'deleteLink': url_for('.delete_supplier_case_study', casestudy_id=casestudy_id)}
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


@main.route('/case-study/create/<int:domain_id>/brief/<int:brief_id>', methods=['GET'])
@login_required
def new_supplier_case_study(domain_id, brief_id):
    domain = data_api_client.req.domain(str(domain_id)).get()
    if not current_user.role == 'supplier':
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()
    form = DmForm()
    basename = url_for('.create_new_supplier_case_study', domain_id=domain_id, brief_id=brief_id)
    props = {
        'form_options': {
            'csrf_token': form.csrf_token.current_token
        },
        'casestudy': {
            'domain_id': domain_id,
            'service': domain['domain']['name'],
            'is_assessment': True
        },
        'basename': basename
    }

    if 'casestudy' in session:
        props['caseStudyForm'] = session['casestudy']

    rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js', props)

    return render_template(
        '_react.html',
        breadcrumb_items=[
            {'link': url_for('main.index'), 'label': 'Home'},
            {'link': url_for('main.get_supplier', code=current_user.supplier_code), 'label': 'Seller details'},
            {'label': 'Add case study'}
        ],
        component=rendered_component
    )


@main.route('/case-study/<int:casestudy_id>/delete', methods=['GET'])
@login_required
def delete_supplier_case_study(casestudy_id):
    casestudy = DataAPIClient().get_case_study(casestudy_id)['caseStudy']
    supplier_code = casestudy.get('supplierCode') if casestudy else None

    if not current_user.role == 'supplier' or not can_view_supplier_page(supplier_code):
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


@main.route('/case-study/create/<int:domain_id>/brief/<int:brief_id>', methods=['POST'])
@login_required
def create_new_supplier_case_study(domain_id, brief_id):
    domain = data_api_client.req.domain(str(domain_id)).get()
    if not current_user.role == 'supplier':
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()

    casestudy = from_response(request)
    casestudy['service'] = domain['domain']['name']
    casestudy['supplierCode'] = current_user.supplier_code

    fields = ['opportunity', 'title', 'client', 'timeframe', 'outcome', 'approach']

    basename = url_for('.new_supplier_case_study', domain_id=domain_id, brief_id=brief_id)
    errors = validate_form_data(casestudy, fields)
    if errors:
        form = DmForm()
        rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js', {
            'form_options': {
                'csrf_token': form.csrf_token.current_token,
                'errors': errors
            },
            'casestudy': {
                'returnLink': url_for('main.get_supplier', code=current_user.supplier_code)
            },
            'caseStudyForm': casestudy,
            'basename': basename
        })

        return render_template(
            '_react.html',
            component=rendered_component
        )

    try:
        supplier_updates = {'services': {domain['domain']['name']: True}}
        supplier = data_api_client.update_supplier(
            current_user.supplier_code,
            supplier_updates,
            user=current_user.email_address
        )
        case_study = DataAPIClient().create_case_study(
            caseStudy=casestudy
        )['caseStudy']

        return redirect('/sellers/opportunities/{}/assessment'.format(brief_id))

    except APIError as e:
        form = DmForm()
        flash('', 'error')
        rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js', {
            'form_options': {
                'csrf_token': form.csrf_token.current_token
            },
            'caseStudyForm': casestudy,
            'basename': basename
        })

        return render_template(
            '_react.html',
            component=rendered_component
        )


@main.route('/case-study/<int:casestudy_id>/update', methods=['GET'])
@login_required
def edit_supplier_case_study(casestudy_id):
    casestudy = DataAPIClient().get_case_study(casestudy_id)['caseStudy']
    supplier_code = casestudy.get('supplierCode') if casestudy else None

    if not current_user.role == 'supplier' or not can_view_supplier_page(supplier_code):
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()

    form = DmForm()
    basename = url_for('.edit_supplier_case_study', casestudy_id=casestudy.get('id'))
    rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js', {
        'form_options': {
            'csrf_token': form.csrf_token.current_token,
            'mode': 'edit'
        },
        'casestudy': {
            'returnLink': url_for('main.get_supplier', code=current_user.supplier_code)
        },
        'caseStudyForm': casestudy,
        'basename': basename
    })

    return render_template(
        '_react.html',
        breadcrumb_items=[
            {'link': url_for('main.index'), 'label': 'Home'},
            {'link': url_for('main.supplier_search'), 'label': 'Sellers catalogue'},
            {'link': url_for('main.get_supplier', code=current_user.supplier_code), 'label': 'Seller details'},
            {'label': 'Edit case study'}
        ],
        component=rendered_component
    )


@main.route('/case-study/<int:casestudy_id>/update', methods=['POST'])
@main.route(
    '/case-study/<int:casestudy_id>/update/<path:step>',
    methods=['POST'],
    endpoint='update_supplier_case_study_step'
)
@login_required
def update_supplier_case_study(casestudy_id, step=None):
    old_casestudy = DataAPIClient().get_case_study(casestudy_id)['caseStudy']
    supplier_code = old_casestudy.get('supplierCode') if old_casestudy else None

    if not current_user.role == 'supplier' or not can_view_supplier_page(supplier_code):
        flash('buyer-role-required', 'error')
        return current_app.login_manager.unauthorized()

    casestudy = from_response(request)
    casestudy['id'] = casestudy_id
    casestudy['supplierCode'] = current_user.supplier_code

    fields = ['opportunity', 'title', 'client', 'timeframe', 'outcome', 'approach']
    if step == 'reference':
        fields = fields + ['acknowledge']

        # Permission is only required if any of these four fields have values.
        optional_require_errors = validate_form_data(casestudy, ['name', 'role', 'phone', 'email'])
        if not len(optional_require_errors) == 4:
            fields = fields + ['permission']

    basename = url_for('.edit_supplier_case_study', casestudy_id=casestudy.get('id'))
    errors = validate_form_data(casestudy, fields)
    if errors:
        form = DmForm()

        rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js', {
            'form_options': {
                'csrf_token': form.csrf_token.current_token,
                'errors': errors,
                'mode': 'edit'
            },
            'casestudy': {
                'returnLink': url_for('main.get_supplier', code=current_user.supplier_code)
            },
            'caseStudyForm': casestudy,
            'basename': basename
        })

        return render_template(
            '_react.html',
            component=rendered_component
        )

    try:
        case_study = DataAPIClient().update_case_study(casestudy_id, casestudy)['caseStudy']

    except APIError as e:
        form = DmForm()
        flash('', 'error')
        rendered_component = render_component('bundles/CaseStudy/CaseStudyWidget.js', {
            'form_options': {
                'csrf_token': form.csrf_token.current_token
            },
            'caseStudyForm': casestudy,
            'basename': basename
        })

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
