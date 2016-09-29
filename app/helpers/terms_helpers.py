import os
import pytz

from datetime import datetime

from flask import current_app
from flask_login import current_user

from dmutils import terms_of_use


TERMS_DIR = 'content/terms-of-use/'


def get_current_terms_version():
    return current_app.extensions['dm_terms_manager'].current_version


def check_terms_acceptance():
    current_version = get_current_terms_version()
    needs_update = current_user.is_authenticated and current_user.terms_accepted_at < current_version.date
    terms_of_use.set_session_flag(needs_update)


class TermsVersion(object):

    def __init__(self, application, filename):
        if not filename.endswith('.html'):
            raise ValueError()
        timestamp = filename[:-5]
        tz = pytz.timezone(application.config['DM_TIMEZONE'])
        date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M')
        self.date = date.replace(tzinfo=tz)
        self.template_file = os.path.join(TERMS_DIR, filename)


class TermsManager(object):

    def init_app(self, application, _template_list=None):
        """
        _template_list is only meant for testing purposes.
        """
        self.load_versions(application, _template_list)
        application.extensions['dm_terms_manager'] = self

    def load_versions(self, application, template_list=None):
        if template_list is None:
            template_list = os.listdir(os.path.join('app', 'templates', TERMS_DIR))

        self.versions = []
        for filename in template_list:
            if filename.startswith('_') or not filename.endswith('.html'):
                continue
            try:
                version = TermsVersion(application, filename)
            except ValueError as e:
                raise ValueError(
                    'Couldn\'t recognise "{}" as a terms of use version.'
                    'Check app/templates/{}README for more information.'.format(filename, TERMS_DIR)
                )
            else:
                self.versions.append(version)
        if not self.versions:
            raise LookupError('No valid terms of use found.')

        self.current_version = max(self.versions, key=lambda v: v.date)
