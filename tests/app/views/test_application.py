import mock
from nose.tools import assert_equal, assert_true
from ...helpers import BaseApplicationTest


class TestApplication(BaseApplicationTest):
    def setup(self):
        super(TestApplication, self).setup()

    def test_should_have_analytics_on_page(self):
        res = self.client.get('/')
        assert_equal(200, res.status_code)
        assert_true(
            'GOVUK.analytics.trackPageview'
            in res.get_data(as_text=True))
