import hmac
from hashlib import sha256
import time

from flask import request
from werkzeug.security import safe_str_cmp
from wtforms.csrf.core import CSRF
from wtforms.validators import ValidationError


class SessionlessCsrf(CSRF):

    def setup_form(self, form):
        self.form_meta = form.meta
        return super(SessionlessCsrf, self).setup_form(form)

    def generate_csrf_token(self, csrf_token):
        expiry = self.now() + self.form_meta.csrf_time_limit.seconds
        hash_value = self.generate_hash(expiry)
        return '1:{}:{}'.format(expiry, hash_value)

    def generate_hash(self, expiry):
        data = '\0'.join([
            '1',
            str(expiry),
            request.remote_addr,
            request.headers.get('User-Agent', ''),
        ])
        return hmac.new(self.form_meta.csrf_secret, data, sha256).hexdigest()

    def validate_csrf_token(self, form, field):
        token = field.data
        if not field.data:
            raise ValidationError('CSRF token missing')

        try:
            version, expiry_str, provided_hash_value = token.split(':')
            expiry = int(expiry_str)
        except ValueError:
            raise ValidationError('CSRF token format error')

        if version != '1':
            raise ValidationError('CSRF token invalid version')

        if self.now() > expiry:
            raise ValidationError('CSRF token expired')

        # Secret key material used after this point, so do not leak any information in error messages or logs.

        correct_hash_value = self.generate_hash(expiry)
        if not safe_str_cmp(provided_hash_value, correct_hash_value):
            raise ValidationError('CSRF token invalid')

    def now(self):
        return int(time.time())
