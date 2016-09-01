import six
import urlparse

from flask_login import current_user
from flask import current_app, redirect, render_template, session, url_for

from dmutils.email import (
    decode_token, EmailError, generate_token, hash_email, InvalidToken, ONE_DAY_IN_SECONDS, send_email
)


def redirect_logged_in_user(next_url=None):
    site_url_prefix = current_app.config['URL_PREFIX']
    if not site_url_prefix:
        site_url_prefix = '/'
    if current_user.is_authenticated:
        if next_url and next_url.startswith(site_url_prefix):
            return redirect(next_url)

        if current_user.role == 'buyer':
            return redirect(url_for('buyers.buyer_dashboard'))

        if current_user.role == 'supplier':
            return redirect(url_for('.list_opportunities', framework_slug='digital-service-professionals'))

    return redirect(url_for('.index'))


def generate_buyer_creation_token(name, email_address, **unused):
    data = {
        'name': name,
        'emailAddress': email_address,
    }
    token = generate_token(data, current_app.config['SECRET_KEY'], current_app.config['BUYER_CREATION_TOKEN_SALT'])
    return token


def decode_buyer_creation_token(token):
    data = decode_token(
        token,
        current_app.config['SECRET_KEY'],
        current_app.config['BUYER_CREATION_TOKEN_SALT'],
        7*ONE_DAY_IN_SECONDS
    )
    if not set(('name', 'emailAddress')).issubset(set(data.keys())):
        raise InvalidToken
    return data


def send_buyer_account_activation_email(name, email_address, token):
    token = generate_buyer_creation_token(name=name, email_address=email_address)
    url = url_for('main.create_buyer_account', token=token, _external=True)
    email_body = render_template('emails/create_buyer_user_email.html', url=url)
    try:
        send_email(
            email_address,
            email_body,
            current_app.config['CREATE_USER_SUBJECT'],
            current_app.config['RESET_PASSWORD_EMAIL_FROM'],
            current_app.config['RESET_PASSWORD_EMAIL_NAME'],
        )
        session['email_sent_to'] = email_address
    except EmailError as e:
        current_app.logger.error(
            'buyercreate.fail: Create user email failed to send. '
            'error {error} email_hash {email_hash}',
            extra={
                'error': six.text_type(e),
                'email_hash': hash_email(email_address)})
        abort(503, response='Failed to send user creation email.')
