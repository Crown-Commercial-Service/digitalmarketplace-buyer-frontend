from __future__ import absolute_import

import six

from flask_login import current_user
from flask import abort, current_app, flash, redirect, render_template, request, session, url_for, get_flashed_messages
from flask_login import logout_user, login_user

from dmapiclient import HTTPError
from dmapiclient.audit import AuditTypes
from dmutils.user import User
from dmutils.email import (
    decode_invitation_token, decode_password_reset_token, generate_token, send_email,
    MandrillException
)
from .. import main
from ..forms.auth_forms import LoginForm, EmailAddressForm, ChangePasswordForm, CreateUserForm
from ...helpers import hash_email
from ...helpers.login_helpers import redirect_logged_in_user
from ... import data_api_client


@main.route('/login', methods=["GET"])
def render_login():
    next_url = request.args.get('next')
    if current_user.is_authenticated() and not get_flashed_messages():
        return redirect_logged_in_user(next_url)
    return render_template(
        "auth/login.html",
        form=LoginForm(),
        next=next_url), 200


@main.route('/login', methods=["POST"])
def process_login():
    form = LoginForm()
    next_url = request.args.get('next')
    if form.validate_on_submit():
        user_json = data_api_client.authenticate_user(
            form.email_address.data,
            form.password.data)
        if not user_json:
            current_app.logger.info(
                "login.fail: failed to log in {email_hash}",
                extra={'email_hash': hash_email(form.email_address.data)})
            flash("no_account", "error")
            return render_template(
                "auth/login.html",
                form=form,
                next=next_url), 403

        user = User.from_json(user_json)

        login_user(user)
        current_app.logger.info("login.success: role={role} user={email_hash}",
                                extra={'role': user.role, 'email_hash': hash_email(form.email_address.data)})
        return redirect_logged_in_user(next_url)

    else:
        return render_template(
            "auth/login.html",
            form=form,
            next=next_url), 400


@main.route('/logout', methods=["GET"])
def logout():
    logout_user()
    return redirect(url_for('.render_login'))


@main.route('/reset-password', methods=["GET"])
def request_password_reset():
    return render_template("auth/request-password-reset.html",
                           form=EmailAddressForm()), 200


@main.route('/reset-password', methods=["POST"])
def send_reset_password_email():
    form = EmailAddressForm()
    if form.validate_on_submit():
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
                    current_app.config['DM_MANDRILL_API_KEY'],
                    current_app.config['RESET_PASSWORD_EMAIL_SUBJECT'],
                    current_app.config['RESET_PASSWORD_EMAIL_FROM'],
                    current_app.config['RESET_PASSWORD_EMAIL_NAME'],
                    ["password-resets"]
                )
            except MandrillException as e:
                current_app.logger.error(
                    "Password reset email failed to send. "
                    "error {error} email_hash {email_hash}",
                    extra={'error': six.text_type(e),
                           'email_hash': hash_email(user.email_address)})
                abort(503, response="Failed to send password reset.")

            current_app.logger.info(
                "login.reset-email.sent: Sending password reset email for "
                "supplier_id {supplier_id} email_hash {email_hash}",
                extra={'supplier_id': user.supplier_id,
                       'email_hash': hash_email(user.email_address)})
        else:
            current_app.logger.info(
                "login.reset-email.invalid-email: "
                "Password reset request for invalid supplier email {email_hash}",
                extra={'email_hash': hash_email(email_address)})

        flash('email_sent')
        return redirect(url_for('.request_password_reset'))
    else:
        return render_template("auth/request-password-reset.html",
                               form=form), 400


@main.route('/reset-password/<token>', methods=["GET"])
def reset_password(token):
    decoded = decode_password_reset_token(token, data_api_client)
    if decoded.get('error', None):
        flash(decoded['error'], 'error')
        return redirect(url_for('.request_password_reset'))

    email_address = decoded['email']

    return render_template("auth/reset-password.html",
                           email_address=email_address,
                           form=ChangePasswordForm(),
                           token=token), 200


@main.route('/reset-password/<token>', methods=["POST"])
def update_password(token):
    form = ChangePasswordForm()
    decoded = decode_password_reset_token(token, data_api_client)
    if decoded.get('error', None):
        flash(decoded['error'], 'error')
        return redirect(url_for('.request_password_reset'))

    user_id = decoded["user"]
    email_address = decoded["email"]
    password = form.password.data

    if form.validate_on_submit():
        if data_api_client.update_user_password(user_id, password, email_address):
            current_app.logger.info(
                "User {user_id} successfully changed their password",
                extra={'user_id': user_id})
            flash('password_updated')
        else:
            flash('password_not_updated', 'error')
        return redirect(url_for('.render_login'))
    else:
        return render_template("auth/reset-password.html",
                               email_address=email_address,
                               form=form,
                               token=token), 400


@main.route('/buyers/create', methods=["GET"])
def create_buyer_account():
    form = EmailAddressForm()

    return render_template(
        "auth/create-buyer-account.html",
        form=form), 200


@main.route('/buyers/create', methods=['POST'])
def submit_create_buyer_account():
    current_app.logger.info(
        "buyercreate: post create-buyer-account")
    form = EmailAddressForm()

    if form.validate_on_submit():
        email_address = form.email_address.data
        if not data_api_client.is_email_address_with_valid_buyer_domain(email_address):
            return render_template(
                "auth/create-buyer-user-error.html",
                error='invalid_buyer_domain'), 400
        else:
            token = generate_token(
                {
                    "email_address":  email_address
                },
                current_app.config['SHARED_EMAIL_KEY'],
                current_app.config['INVITE_EMAIL_SALT']
            )
            url = url_for('main.create_user', encoded_token=token, _external=True)
            email_body = render_template("emails/create_buyer_user_email.html", url=url)
            # print("CREATE ACCOUNT URL: {}".format(url))
            try:
                send_email(
                    email_address,
                    email_body,
                    current_app.config['DM_MANDRILL_API_KEY'],
                    current_app.config['CREATE_USER_SUBJECT'],
                    current_app.config['RESET_PASSWORD_EMAIL_FROM'],
                    current_app.config['RESET_PASSWORD_EMAIL_NAME'],
                    ["user-creation"]
                )
                session['email_sent_to'] = email_address
            except MandrillException as e:
                current_app.logger.error(
                    "buyercreate.fail: Create user email failed to send. "
                    "error {error} email_hash {email_hash}",
                    extra={
                        'error': six.text_type(e),
                        'email_hash': hash_email(email_address)})
                abort(503, response="Failed to send user creation email.")

            data_api_client.create_audit_event(
                audit_type=AuditTypes.invite_user,
                data={'invitedEmail': email_address})

            return redirect(url_for('.create_your_account_complete'), 302)
    else:
        return render_template(
            "auth/create-buyer-account.html",
            form=form,
            email_address=form.email_address.data
        ), 400


@main.route('/create-user/<string:encoded_token>', methods=["GET"])
def create_user(encoded_token):
    form = CreateUserForm()

    token = decode_invitation_token(encoded_token, role='buyer')
    if token is None:
        current_app.logger.warning(
            "createuser.token_invalid: {encoded_token}",
            extra={'encoded_token': encoded_token})
        return render_template(
            "auth/create-buyer-user-error.html",
            token=None), 400

    user_json = data_api_client.get_user(email_address=token.get("email_address"))

    if not user_json:
        return render_template(
            "auth/create-user.html",
            form=form,
            email_address=token['email_address'],
            token=encoded_token), 200

    user = User.from_json(user_json)
    return render_template(
        "auth/create-buyer-user-error.html",
        token=token,
        user=user), 400


@main.route('/create-user/<string:encoded_token>', methods=["POST"])
def submit_create_user(encoded_token):
    form = CreateUserForm()

    token = decode_invitation_token(encoded_token, role='buyer')
    if token is None:
        current_app.logger.warning("createuser.token_invalid: {encoded_token}",
                                   extra={'encoded_token': encoded_token})
        return render_template(
            "auth/create-buyer-user-error.html",
            token=None), 400

    else:
        if not form.validate_on_submit():
            current_app.logger.warning(
                "createuser.invalid: {form_errors}",
                extra={'form_errors': ", ".join(form.errors)})
            return render_template(
                "auth/create-user.html",
                form=form,
                token=encoded_token,
                email_address=token.get('email_address')), 400

        try:
            user = data_api_client.create_user({
                'name': form.name.data,
                'password': form.password.data,
                'phoneNumber': form.phone_number.data,
                'emailAddress': token.get('email_address'),
                'role': 'buyer'
            })

            user = User.from_json(user)
            login_user(user)

        except HTTPError as e:
            if e.message != 'invalid_buyer_domain' and e.status_code != 409:
                raise

            return render_template(
                "auth/create-buyer-user-error.html",
                error=e.message,
                token=None), 400

        return redirect_logged_in_user()


@main.route('/create-your-account-complete', methods=['GET'])
def create_your_account_complete():
    if 'email_sent_to' in session:
        email_address = session['email_sent_to']
    else:
        email_address = "the email address you supplied"
    session.clear()
    session['email_sent_to'] = email_address
    return render_template(
        "auth/create-your-account-complete.html",
        email_address=email_address), 200
