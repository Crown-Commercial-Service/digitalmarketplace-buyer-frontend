import six

from datetime import datetime
from itsdangerous import BadSignature, SignatureExpired
from flask_login import current_user
from flask import current_app, flash, redirect, url_for

from dmutils.email import decode_token
from dmutils.formats import DATETIME_FORMAT

ONE_DAY_IN_SECONDS = 86400
SEVEN_DAYS_IN_SECONDS = 604800


def redirect_logged_in_user(next_url=None):
    if current_user.is_authenticated():
        if current_user.role == 'supplier':
            if next_url and next_url.startswith('/suppliers'):
                return redirect(next_url)
            else:
                return redirect('/suppliers')
        if current_user.role.startswith('admin'):
            if next_url and next_url.startswith('/admin'):
                return redirect(next_url)
            else:
                return redirect('/admin')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        else:
            # TODO: direct to buyer dashboard, once it exists
            pass

    return redirect(url_for('.index'))


def decode_password_reset_token(token, data_api_client):
    try:
        decoded, timestamp = decode_token(
            token,
            current_app.config["SECRET_KEY"],
            current_app.config["RESET_PASSWORD_SALT"],
            ONE_DAY_IN_SECONDS
        )
    except SignatureExpired:
        current_app.logger.info("Password reset attempt with expired token.")
        flash('token_expired', 'error')
        return None
    except BadSignature as e:
        current_app.logger.info("Error changing password: {error}", extra={'error': six.text_type(e)})
        flash('token_invalid', 'error')
        return None

    user = data_api_client.get_user(decoded["user"])
    user_last_changed_password_at = datetime.strptime(
        user['users']['passwordChangedAt'],
        DATETIME_FORMAT
    )

    if token_created_before_password_last_changed(
            timestamp,
            user_last_changed_password_at
    ):
        current_app.logger.info("Error changing password: Token generated earlier than password was last changed.")
        flash('token_invalid', 'error')
        return None

    return decoded


def decode_invitation_token(encoded_token, buyer=False):
    required_token_fields = ['email_address'] if buyer else ['email_address', 'supplier_id', 'supplier_name']
    try:
        token, timestamp = decode_token(
            encoded_token,
            current_app.config['SHARED_EMAIL_KEY'],
            current_app.config['INVITE_EMAIL_SALT'],
            SEVEN_DAYS_IN_SECONDS
        )
        if all(field in token for field in required_token_fields):
            return token
        else:
            raise ValueError('Invitation token is missing required keys')
    except SignatureExpired as e:
        current_app.logger.info("Invitation attempt with expired token. error {error}",
                                extra={'error': six.text_type(e)})
        return None
    except BadSignature as e:
        current_app.logger.info("Invitation reset attempt with expired token. error {error}",
                                extra={'error': six.text_type(e)})
        return None
    except ValueError as e:
        current_app.logger.info("error {error}",
                                extra={'error': six.text_type(e)})
        return None


def token_created_before_password_last_changed(token_timestamp, user_timestamp):
    return token_timestamp < user_timestamp
