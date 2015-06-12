from nose.tools import assert_equal, assert_true, assert_in
from ...helpers import BaseApplicationTest


class TestApplication(BaseApplicationTest):
    def setup(self):
        super(TestApplication, self).setup()

    def test_analytics_code_should_be_in_javascript(self):
        res = self.client.get('/static/javascripts/application.js')
        assert_equal(200, res.status_code)
        assert_true(
            'trackPageview'
            in res.get_data(as_text=True))
        assert_in('DENY', res.headers['X-Frame-Options'])
