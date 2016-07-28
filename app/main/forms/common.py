from datetime import timedelta
from flask import current_app, session
from flask.ext.login import current_user
from wtforms import Form

from wtforms.csrf.session import SessionCSRF


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
        else:
            self.Meta.csrf = False
            self.Meta.csrf_class = None
        super(DmForm, self).__init__(*args, **kwargs)
