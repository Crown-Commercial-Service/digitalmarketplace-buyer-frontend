# coding: utf-8
from __future__ import unicode_literals
from __future__ import absolute_import

import six

from flask_login import current_user
from flask import abort, current_app, flash, redirect, render_template, request, session, url_for, get_flashed_messages,\
    Markup
from flask_login import logout_user, login_user

from dmapiclient import HTTPError
from dmapiclient.audit import AuditTypes
from dmutils.user import User
from dmutils.email import (decode_invitation_token, decode_password_reset_token, generate_token, send_email)
from dmutils.email.exceptions import EmailError

from .. import main
from ..forms.auth_forms import LoginForm, EmailAddressForm, ChangePasswordForm, CreateUserForm
from ..helpers import hash_email
from ..helpers.login_helpers import redirect_logged_in_user
from ... import data_api_client


NO_ACCOUNT_MESSAGE = Markup("""Make sure you've entered the right email address and password. Accounts
    are locked after 5 failed attempts. If you think your account has been locked, email
    <a href="mailto:enquiries@digitalmarketplace.service.gov.uk">enquiries@digitalmarketplace.service.gov.uk</a>.""")
PASSWORD_UPDATED_MESSAGE = "You have successfully changed your password."
PASSWORD_NOT_UPDATED_MESSAGE = "Could not update password due to an error."
EMAIL_SENT_MESSAGE = Markup("""If the email address you've entered belongs to a Digital Marketplace account, we'll
    send a link to reset the password.""")
BAD_TOKEN_MESSAGE = Markup("""This password reset link has expired. Enter your email address and we’ll send you a
    new one. Password reset links are only valid for 24 hours.""")


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
            flash(NO_ACCOUNT_MESSAGE, "error")
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
                    "user": user.id
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
            except EmailError as e:
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

        flash(EMAIL_SENT_MESSAGE)
        return redirect(url_for('.request_password_reset'))
    else:
        return render_template("auth/request-password-reset.html",
                               form=form), 400


@main.route('/reset-password/<token>', methods=["GET"])
def reset_password(token):
    decoded = decode_password_reset_token(token, data_api_client)
    if 'error' in decoded:
        flash(BAD_TOKEN_MESSAGE, 'error')
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
    if 'error' in decoded:
        flash(BAD_TOKEN_MESSAGE, 'error')
        return redirect(url_for('.request_password_reset'))

    user_id = decoded["user"]
    email_address = decoded["email"]
    password = form.password.data

    if form.validate_on_submit():
        if data_api_client.update_user_password(user_id, password, email_address):
            current_app.logger.info(
                "User {user_id} successfully changed their password",
                extra={'user_id': user_id})
            flash(PASSWORD_UPDATED_MESSAGE)
        else:
            flash(PASSWORD_NOT_UPDATED_MESSAGE, 'error')
        return redirect(url_for('.render_login'))
    else:
        return render_template("auth/reset-password.html",
                               email_address=email_address,
                               form=form,
                               token=token), 400


@main.route('/create-user/<string:encoded_token>', methods=["GET"])
def create_user(encoded_token):
    form = CreateUserForm()

    token = decode_invitation_token(encoded_token)
    if token is None:
        current_app.logger.warning(
            "createuser.token_invalid: {encoded_token}",
            extra={'encoded_token': encoded_token})
        return render_template(
            "auth/create-buyer-user-error.html",
            token=None), 400

    user_json = data_api_client.get_user(email_address=token["email_address"])

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
    token = decode_invitation_token(encoded_token)
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
                email_address=token['email_address']), 400

        try:
            user = data_api_client.create_user({
                'name': form.name.data,
                'password': form.password.data,
                'phoneNumber': form.phone_number.data,
                'emailAddress': token['email_address'],
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

        flash('account-created', 'flag')
        return redirect_logged_in_user()


@main.route('/create-your-account-complete', methods=['GET'])
def create_your_account_complete():
    email_address = session.setdefault("email_sent_to", "the email address you supplied")
    return render_template(
        "auth/create-your-account-complete.html",
        email_address=email_address), 200
