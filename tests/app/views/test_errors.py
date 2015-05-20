import mock
from nose.tools import assert_equal, assert_true
from requests import ConnectionError
from ...helpers import BaseApplicationTest


class TestErrors(BaseApplicationTest):
    def setup(self):
        super(TestErrors, self).setup()

        self._search_api_client = mock.patch(
            'app.main.views.search_api_client'
        ).start()

        self.search_results = self._get_search_results_fixture_data()

    def teardown(self):
        self._search_api_client.stop()

    def test_404(self):
        res = self.client.get('/service/1234')
        assert_equal(404, res.status_code)
        assert_true(
            'Page could not be found'
            in res.get_data(as_text=True))

    def test_500(self):
        self.app.config['DEBUG'] = False
        self._search_api_client.search_services = mock.Mock(
            side_effect=ConnectionError('API is down')
        )

        res = self.client.get('/search?q=email')
        assert_equal(500, res.status_code)
        assert_true(
            'An error has occurred'
            in res.get_data(as_text=True))

