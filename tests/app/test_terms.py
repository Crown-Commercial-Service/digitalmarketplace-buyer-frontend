from datetime import timedelta
import mock

from app.helpers.terms_helpers import TermsManager

from tests.helpers import BaseApplicationTest


class TestTermsManager(BaseApplicationTest):

    full_template_list = [
        '2010-01-01 01:00.html',
        '2011-3-2 4:00.html',
        '2012-03-12 13:00.html',
        'README',
        '_base_template.html',
    ]

    def init_manager(self, template_list):
        self.terms_manager = TermsManager()
        with self.app.app_context():
            self.terms_manager.init_app(self.app, template_list)

    def assert_sane(self):
        assert len(self.terms_manager.versions) > 0
        dates = [v.date for v in self.terms_manager.versions]
        assert all(self.terms_manager.current_version.date >= d for d in dates)
        assert len(set(dates)) == len(dates)

    def test_real_terms_data_is_valid(self):
        self.init_manager(None)
        self.assert_sane()

    def test_ideal_data(self):
        self.init_manager(self.full_template_list)
        self.assert_sane()

    def test_one_version_only(self):
        self.init_manager(self.full_template_list[:1])
        self.assert_sane()

    def test_broken_filename(self):
        try:
            self.init_manager(['broken.html'])
        except ValueError as e:
            assert 'broken.html' in e.message
        else:
            assert False, 'Should raise exception'

    def test_missing_versions(self):
        try:
            self.init_manager(['README'])
        except LookupError as e:
            pass
        else:
            assert False, 'Should raise exception'


class TestAcceptanceCheck(BaseApplicationTest):

    versions = [
        '2016-01-01 00:00.html',
    ]

    def setup(self):
        super(TestAcceptanceCheck, self).setup()
        self.terms_manager.load_versions(self.app, self.versions)

    def login(self, acceptance_stale):
        if acceptance_stale:
            offset = timedelta(days=-1)
        else:
            offset = timedelta(days=1)
        acceptance_date = self.terms_manager.current_version.date + offset
        self.login_as_buyer(terms_accepted_date=acceptance_date)

    def test_non_stale_user(self):
        self.login(acceptance_stale=False)

        res = self.client.get(self.url_for('main.supplier_search'))
        assert res.status_code == 200

    def test_stale_user(self):
        self.login(acceptance_stale=True)

        res = self.client.get(self.url_for('main.supplier_search'))
        assert res.status_code == 302
        assert res.location == self.url_for('main.terms_updated', _external=True)
