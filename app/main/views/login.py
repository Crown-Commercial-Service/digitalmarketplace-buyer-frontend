from __future__ import absolute_import

import six
import rollbar
from datetime import datetime

from flask_login import current_user
from flask import abort, current_app, flash, redirect, render_template, request, session, url_for, get_flashed_messages
from flask_login import logout_user, login_user, login_required

from dmutils.user import User, user_logging_string
from dmutils.email import hash_email
from dmutils.forms import render_template_with_csrf
from dmutils.formats import DATETIME_FORMAT
from dmutils import terms_of_use
from app import data_api_client
from app.main import main
from app.helpers.login_helpers import redirect_logged_in_user
from app.helpers.terms_helpers import check_terms_acceptance
from app.main.forms import auth_forms


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
