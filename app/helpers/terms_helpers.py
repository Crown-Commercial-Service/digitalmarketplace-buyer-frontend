import os

from datetime import datetime


TERMS_DIR = 'content/terms-of-use/'


def get_terms_templates():
    return os.listdir(os.path.join('app', 'templates', TERMS_DIR))


class TermsVersion(object):

    def __init__(self, filename):
        if not filename.endswith('.html'):
            raise ValueError()
        timestamp = filename[:-5]
        self.date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M')
        self.template_file = os.path.join(TERMS_DIR, filename)


class TermsManager(object):

    def __init__(self, _template_list=get_terms_templates()):
        """
        _template_list is only meant for testing purposes.
        """
        self.versions = []
        for filename in _template_list:
            if filename.startswith('_') or not filename.endswith('.html'):
                continue
            try:
                version = TermsVersion(filename)
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
