from app.helpers.terms_helpers import TermsManager


class TestTermsManager(object):

    full_template_list = [
        '2010-01-01 01:00.html',
        '2011-3-2 4:00.html',
        '2012-03-12 13:00.html',
        'README',
        '_base_template.html',
    ]

    def assert_sane(self):
        assert len(self.manager.versions) > 0
        dates = [v.date for v in self.manager.versions]
        assert all(self.manager.current_version.date >= d for d in dates)
        assert len(set(dates)) == len(dates)

    def test_real_terms_data_is_valid(self):
        self.manager = TermsManager()
        self.assert_sane()

    def test_ideal_data(self):
        self.manager = TermsManager(self.full_template_list)
        self.assert_sane()

    def test_one_version_only(self):
        self.manager = TermsManager(self.full_template_list[:1])
        self.assert_sane()

    def test_broken_filename(self):
        try:
            self.manager = TermsManager(['broken.html'])
        except ValueError as e:
            assert 'broken.html' in e.message
        else:
            assert False, 'Should raise exception'

    def test_missing_versions(self):
        try:
            self.manager = TermsManager(['README'])
        except LookupError as e:
            pass
        else:
            assert False, 'Should raise exception'
