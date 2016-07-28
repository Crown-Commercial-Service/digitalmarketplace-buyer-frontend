from datetime import timedelta
from flask import current_app, session
from wtforms import Form

from app.csrf import SessionlessCsrf


class DmForm(Form):

    class Meta:
        csrf = True
        csrf_class = SessionlessCsrf
        csrf_secret = None
        csrf_time_limit = None

        @property
        def csrf_context(self):
            return session

    def __init__(self, *args, **kwargs):
        if current_app.config['CSRF_ENABLED']:
            self.Meta.csrf_secret = current_app.config['SECRET_KEY']
            self.Meta.csrf_time_limit = timedelta(seconds=current_app.config['CSRF_TIME_LIMIT'])
            self.Meta.csrf_trusted_origins = current_app.config['CSRF_TRUSTED_ORIGINS'].split(';')
        else:
            self.Meta.csrf = False
            self.Meta.csrf_class = None
        super(DmForm, self).__init__(*args, **kwargs)
