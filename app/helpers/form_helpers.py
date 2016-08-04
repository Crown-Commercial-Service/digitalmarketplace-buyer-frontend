from datetime import timedelta
from functools import wraps

from flask import abort, current_app, render_template, request, Response, session
from wtforms import Form
from wtforms.csrf.core import CSRF
from wtforms.csrf.session import SessionCSRF


class FakeCsrf(CSRF):
    """
    For testing purposes only.
    """

    valid_token = 'valid_fake_csrf_token'

    def generate_csrf_token(self, csrf_token):
        return self.valid_token

    def validate_csrf_token(self, form, field):
        if field.data != self.valid_token:
            raise ValueError('Invalid (fake) CSRF token')


class DmForm(Form):

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = None
        csrf_time_limit = None

        @property
        def csrf_context(self):
            return session

    def __init__(self, *args, **kwargs):
        if current_app.config['CSRF_ENABLED']:
            self.Meta.csrf_secret = current_app.config['SECRET_KEY']
            self.Meta.csrf_time_limit = timedelta(seconds=current_app.config['CSRF_TIME_LIMIT'])
        if current_app.config.get('CSRF_FAKED', False):
            self.Meta.csrf_class = FakeCsrf
        else:
            # FIXME: deprecated
            self.Meta.csrf = False
            self.Meta.csrf_class = None
        super(DmForm, self).__init__(*args, **kwargs)


def render_template_with_csrf(template_name, status_code=200, **kwargs):
    if 'form' not in kwargs:
        kwargs['form'] = DmForm()
    response = Response(render_template(template_name, **kwargs))

    # CSRF tokens are user-specific, even if the user isn't logged in
    response.cache_control.private = True

    max_age = current_app.config['DM_DEFAULT_CACHE_MAX_AGE']
    max_age = min(max_age, current_app.config.get('CSRF_TIME_LIMIT', max_age))
    response.cache_control.max_age = max_age

    return response, status_code


def is_csrf_token_valid():
    if not current_app.config['CSRF_ENABLED'] and not current_app.config.get('CSRF_FAKED', False):
        return True
    if 'csrf_token' not in request.form:
        return False
    form = DmForm(csrf_token=request.form['csrf_token'])
    return form.validate()


def valid_csrf_or_abort():
    if is_csrf_token_valid():
        return
    current_app.logger.info(
        u'csrf.invalid_token: Aborting request, user_id: {user_id}',
        extra={'user_id': session.get('user_id', '<unknown')})
    abort(400, 'Invalid CSRF token. Please try again.')


def check_csrf(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        valid_csrf_or_abort()
        return view(*args, **kwargs)
    return wrapped
