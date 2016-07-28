import re

from app.csrf import SessionlessCsrf
from app.main.forms.common import DmForm

from wtforms.validators import ValidationError

from ..helpers import BaseApplicationTest


def mockNow(times):
    """
    now() function mock that returns the given times in order.
    """
    times.reverse()

    def now():
        return times.pop()

    return now


class TestSessionlessCsrf(BaseApplicationTest):

    def setup(self):
        super(TestSessionlessCsrf, self).setup()
        self.app.config['CSRF_ENABLED'] = True

    def makeUut(self):
        form = DmForm()
        uut = SessionlessCsrf()
        uut.setup_form(form)
        return uut

    def test_valid_csrf(self):
        with self.app.test_request_context(environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            uut = self.makeUut()
            token = uut.generate_csrf_token(None)

            form = DmForm()
            form.csrf_token.data = token

            uut.validate_csrf_token(form, form.csrf_token)  # no exceptions raised

    def test_invalid_csrf(self):
        with self.app.test_request_context(environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            uut = self.makeUut()

            token = uut.generate_csrf_token(None)
            bad_token = token + 'bad'
            form = DmForm()
            form.csrf_token.data = bad_token

            try:
                uut.validate_csrf_token(form, form.csrf_token)  # no exceptions raised
            except ValidationError, e:
                assert 'invalid' in e.message
            else:
                raise Exception('Token {} should have been rejected'.format(bad_token))

    def test_csrf_expiry(self):
        with self.app.test_request_context(environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            uut = self.makeUut()
            uut.now = mockNow([0, 365*24*3600])

            token = uut.generate_csrf_token(None)
            form = DmForm()
            form.csrf_token.data = token

            try:
                uut.validate_csrf_token(form, form.csrf_token)  # no exceptions raised
            except ValidationError, e:
                assert 'expire' in e.message
            else:
                raise Exception('Token should have expired'.format(bad_token))

    def test_expiry_tampering(self):
        with self.app.test_request_context(environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            uut = self.makeUut()

            token = uut.generate_csrf_token(None)
            version, expiry, hash_value = token.split(':')
            bad_token = '{}:{}:{}'.format(version, str(int(expiry) + 1), hash_value)

            form = DmForm()
            form.csrf_token.data = bad_token

            try:
                uut.validate_csrf_token(form, form.csrf_token)  # no exceptions raised
            except ValidationError, e:
                assert 'invalid' in e.message
            else:
                raise Exception('Token {} expiry tampering should have been detected'.format(bad_token))

    def test_good_origin(self):
        environ = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_ORIGIN': 'https://localhost:5002/ https://proxy.example.com/',
        }
        with self.app.test_request_context(environ_base=environ):
            uut = self.makeUut()
            token = uut.generate_csrf_token(None)

            form = DmForm()
            form.csrf_token.data = token

            uut.validate_csrf_token(form, form.csrf_token)  # no exceptions raised

    def test_bad_origin(self):
        environ = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_ORIGIN': 'https://external.example.com:5002/ https://proxy.example.com/',
        }
        with self.app.test_request_context(environ_base=environ):
            uut = self.makeUut()
            token = uut.generate_csrf_token(None)

            form = DmForm()
            form.csrf_token.data = token

            try:
                uut.validate_csrf_token(form, form.csrf_token)  # no exceptions raised
            except ValidationError, e:
                assert 'external' in e.message
            else:
                raise Exception('External origin request should have been rejected')

    def test_good_referer(self):
        environ = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_REFERER': 'https://localhost:5002/marketplace/foo',
        }
        with self.app.test_request_context(environ_base=environ):
            uut = self.makeUut()
            token = uut.generate_csrf_token(None)

            form = DmForm()
            form.csrf_token.data = token

            uut.validate_csrf_token(form, form.csrf_token)  # no exceptions raised

    def test_bad_referer(self):
        environ = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_REFERER': 'https://external.example.com/xss-vulnerable-page',
        }
        with self.app.test_request_context(environ_base=environ):
            uut = self.makeUut()
            token = uut.generate_csrf_token(None)

            form = DmForm()
            form.csrf_token.data = token

            try:
                uut.validate_csrf_token(form, form.csrf_token)  # no exceptions raised
            except ValidationError, e:
                assert 'external' in e.message
            else:
                raise Exception('External origin request should have been rejected')
