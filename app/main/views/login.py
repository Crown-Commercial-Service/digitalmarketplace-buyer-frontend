from __future__ import absolute_import

import six
import rollbar
from datetime import datetime

from flask_login import current_user
from flask import abort, current_app, flash, redirect, render_template, request, session, url_for, get_flashed_messages
from flask_login import logout_user, login_user, login_required

from dmapiclient.audit import AuditTypes
from dmutils.user import User, user_logging_string
from dmutils.email import (
    decode_invitation_token, decode_password_reset_token, EmailError, generate_token, hash_email, InvalidToken,
    send_email
)
from dmutils.forms import render_template_with_csrf
from dmutils.formats import DATETIME_FORMAT
from dmutils import terms_of_use
from app import data_api_client
from app.main import main
from app.helpers.login_helpers import (
    decode_buyer_creation_token, decode_user_creation_token, generate_buyer_creation_token, redirect_logged_in_user,
    send_buyer_account_activation_email, send_buyer_onboarding_email
)
from app.helpers.terms_helpers import check_terms_acceptance
from app.main.forms import auth_forms
from ...api_client.error import HTTPError
from react.render import render_component
from react.response import from_response, validate_form_data
from dmutils.forms import is_government_email


@main.route('/login', methods=["GET"])
def render_login():
    next_url = request.args.get('next')
    if current_user.is_authenticated and not get_flashed_messages():
        return redirect_logged_in_user(next_url)
    return render_template_with_csrf(
        "auth/login.html",
        form=auth_forms.LoginForm(),
        next=next_url)


@main.route('/login', methods=["POST"])
def process_login():
    form = auth_forms.LoginForm(request.form)
    next_url = request.args.get('next')
    if form.validate():
        result = data_api_client.authenticate_user(
            form.email_address.data,
            form.password.data)
        if not result:
            current_app.logger.info(
                "login.fail: failed to sign in {email_hash}",
                extra={'email_hash': hash_email(form.email_address.data)})
            flash("no_account", "error")
            return render_template_with_csrf(
                "auth/login.html",
                status_code=403,
                form=form,
                next=next_url)

        user = User.from_json(result)

        login_user(user)
        current_app.logger.info('login.success: {user}', extra={'user': user_logging_string(user)})
        check_terms_acceptance()
        return redirect_logged_in_user(next_url, result.get('validation_result', None))

    else:
        return render_template_with_csrf(
            "auth/login.html",
            status_code=400,
            form=form,
            next=next_url)


@main.route('/logout', methods=["GET"])
def logout():
    current_app.logger.info('logout: {user}', extra={'user': user_logging_string(current_user)})
    terms_of_use.set_session_flag(False)
    logout_user()
    return redirect(url_for('.render_login'))


@main.route('/reset-password', methods=["GET"])
def request_password_reset():
    return redirect('/2/reset-password')


@main.route('/reset-password', methods=["POST"])
def send_reset_password_email():
    form = auth_forms.EmailAddressForm(request.form)
    if form.validate():
        email_address = form.email_address.data
        user_json = data_api_client.get_user(email_address=email_address)

        if user_json is not None:

            user = User.from_json(user_json)

            token = generate_token(
                {
                    "user": user.id,
                    "email": user.email_address
                },
                current_app.config['SECRET_KEY'],
                current_app.config['RESET_PASSWORD_SALT']
            )

            url = url_for('main.reset_password', token=token, _external=True)

            email_body = render_template(
                "emails/reset_password_email.html",
                url=url,
                locked=user.locked)

            try:
                send_email(
                    user.email_address,
                    email_body,
                    current_app.config['RESET_PASSWORD_EMAIL_SUBJECT'],
                    current_app.config['RESET_PASSWORD_EMAIL_FROM'],
                    current_app.config['RESET_PASSWORD_EMAIL_NAME'],
                )
            except EmailError as e:
                rollbar.report_exc_info()
                current_app.logger.error(
                    "Password reset email failed to send. "
                    "error {error} email_hash {email_hash}",
                    extra={'error': six.text_type(e),
                           'email_hash': hash_email(user.email_address)})
                abort(503, response="Failed to send password reset.")

            current_app.logger.info(
                "login.reset-email.sent: Sending password reset email for "
                "supplier_code {supplier_code} email_hash {email_hash}",
                extra={'supplier_code': user.supplier_code,
                       'email_hash': hash_email(user.email_address)})
        else:
            current_app.logger.info(
                "login.reset-email.invalid-email: "
                "Password reset request for invalid supplier email {email_hash}",
                extra={'email_hash': hash_email(email_address)})

        flash('email_sent')
        return redirect(url_for('.request_password_reset'))
    else:
        return render_template_with_csrf("auth/request-password-reset.html", status_code=400, form=form)


@main.route('/reset-password/<token>', methods=["GET"])
def reset_password(token):
    return redirect('/2/reset-password')


@main.route('/reset-password/<token>', methods=["POST"])
def update_password(token):
    form = auth_forms.ChangePasswordForm(request.form)
    decoded = decode_password_reset_token(token.encode(), data_api_client)
    if decoded.get('error', None):
        flash(decoded['error'], 'error')
        return redirect(url_for('.request_password_reset'))

    user_id = decoded["user"]
    email_address = decoded["email"]
    password = form.password.data

    if form.validate():
        if data_api_client.update_user_password(user_id, password, email_address):
            current_app.logger.info(
                "User {user_id} ({hashed_email}) successfully changed their password",
                extra={'user_id': user_id, 'hashed_email': hash_email(email_address)})
            flash('password_updated')
        else:
            flash('password_not_updated', 'error')
        return redirect(url_for('.render_login'))
    else:
        return render_template_with_csrf("auth/reset-password.html",
                                         status_code=400,
                                         email_address=email_address,
                                         form=form,
                                         token=token)


@main.route('/signup', methods=['GET'])
def single_signup(user=None, errors=None):
    return redirect('/2/signup')


@main.route('/signup', methods=['POST'])
def submit_single_signup():
    return redirect('/2/signup')


@main.route('/buyers/signup', methods=['GET'])
def buyer_signup():
    return redirect('/2/signup')


@main.route('/buyers/signup', methods=['POST'])
def submit_buyer_signup():
    return redirect('/2/signup')


@main.route('/buyers/request-invite', methods=['POST'])
def submit_buyer_invite_request():
    form = auth_forms.BuyerInviteRequestForm(request.form)

    if not form.validate():
        return render_template_with_csrf(
            'auth/buyer-invite-request.html',
            status_code=400,
            form=form
        )

    token = generate_buyer_creation_token(**form.data)
    invite_url = url_for('.send_buyer_invite', token=token, _external=True)
    email_body = render_template(
        'emails/buyer_account_invite_request_email.html',
        form=form,
        invite_url=invite_url
    )
    try:
        send_email(
            current_app.config['BUYER_INVITE_REQUEST_ADMIN_EMAIL'],
            email_body,
            current_app.config['BUYER_INVITE_REQUEST_SUBJECT'],
            current_app.config['BUYER_INVITE_REQUEST_EMAIL_FROM'],
            current_app.config['BUYER_INVITE_REQUEST_EMAIL_NAME'],
        )
    except EmailError as e:
        rollbar.report_exc_info()
        current_app.logger.error(
            'buyerinvite.fail: Buyer account invite request email failed to send. '
            'error {error} invite email_hash {email_hash}',
            extra={
                'error': six.text_type(e),
                'email_hash': hash_email(form.email_address.data)})
        abort(503, response='Failed to send buyer account invite request email.')

    email_body = render_template('emails/buyer_account_invite_manager_confirmation.html', form=form)
    try:
        send_email(
            form.manager_email.data,
            email_body,
            current_app.config['BUYER_INVITE_MANAGER_CONFIRMATION_SUBJECT'],
            current_app.config['DM_GENERIC_NOREPLY_EMAIL'],
            current_app.config['BUYER_INVITE_MANAGER_CONFIRMATION_NAME'],
        )
    except EmailError as e:
        rollbar.report_exc_info()
        current_app.logger.error(
            'buyerinvite.fail: Buyer account invite request manager email failed to send. '
            'error {error} invite email_hash {email_hash} manager email_hash {manager_email_hash}',
            extra={
                'error': six.text_type(e),
                'email_hash': hash_email(form.email_address.data),
                'manager_email_hash': hash_email(form.manager_email.data)})
        abort(503, response='Failed to send buyer account invite request manager email.')

    return render_template('auth/buyer-invite-request-complete.html')


@main.route('/buyers/signup/send-invite/<string:token>', methods=['GET'])
def send_buyer_invite(token):
    try:
        data = decode_user_creation_token(token.encode())
        email_address = data.get('emailAddress', None)
        if email_address is None:
            email_address = data.get('email_address', None)
        send_buyer_account_activation_email(name=data['name'], email_address=email_address, token=token)
        return render_template('auth/buyer-invite-sent.html', email_address=email_address)
    except InvalidToken:
        abort(404)


@main.route('/buyers/signup/create/<string:token>', methods=['GET'])
def create_buyer_account(token):
    try:
        data = decode_buyer_creation_token(token.encode())
    except InvalidToken:
        abort(404)

    form = auth_forms.CreateUserForm(name=data['name'])
    email_address = data.get('emailAddress', None)
    if email_address is None:
        email_address = data.get('email_address', None)

    user_json = data_api_client.get_user(email_address=email_address)

    if not user_json:
        return render_template_with_csrf(
            'auth/create-user.html',
            form=form,
            email_address=email_address,
            token=token)

    user = User.from_json(user_json)
    return render_template_with_csrf(
        'auth/create-buyer-user-error.html',
        status_code=400,
        token=token,
        user=user)


@main.route('/create-user/<string:token>', methods=['POST'])
def submit_create_buyer_account(token):
    try:
        data = decode_buyer_creation_token(token.encode())
    except InvalidToken:
        return render_template_with_csrf(
            'auth/create-buyer-user-error.html',
            status_code=400,
            token=None
        )

    form = auth_forms.CreateUserForm(request.form)
    email_address = data.get('emailAddress', None)
    if email_address is None:
        email_address = data.get('email_address', None)

    if not form.validate():
        current_app.logger.warning(
            'createbuyeruser.invalid: {form_errors}',
            extra={'form_errors': ', '.join(form.errors)})
        return render_template_with_csrf(
            'auth/create-user.html',
            status_code=400,
            form=form,
            email_address=email_address,
            token=token)

    try:
        user = data_api_client.create_user({
            'name': form.name.data,
            'password': form.password.data,
            'emailAddress': email_address,
            'role': 'buyer'
        })

        user = User.from_json(user)
        login_user(user)

        send_buyer_onboarding_email(form.name.data, email_address)

    except HTTPError as e:
        if e.status_code != 409:
            raise

        return render_template_with_csrf(
            'auth/create-buyer-user-error.html',
            status_code=400,
            error=e.message,
            token=None)

    flash('Welcome to your buyer dashboard. \
           This is where you can create and track the opportunities you publish in the Marketplace.', 'flag')
    return redirect_logged_in_user()


@main.route('/terms-updated', methods=['GET'])
@login_required
def terms_updated():
    form = auth_forms.AcceptUpdatedTerms()
    return render_template_with_csrf(
        'auth/accept-updated-terms.html',
        form=form
    )


@main.route('/terms-updated', methods=['POST'])
@login_required
def accept_updated_terms():
    form = auth_forms.AcceptUpdatedTerms(request.form)
    if not form.validate():
        return render_template_with_csrf(
            'auth/accept-updated-terms.html',
            status_code=400,
            form=form
        )
    timestamp = datetime.utcnow().strftime(DATETIME_FORMAT)
    data_api_client.update_user(current_user.id, fields={'termsAcceptedAt': timestamp})
    terms_of_use.set_session_flag(False)
    return redirect_logged_in_user()
