
import mock
from nose.tools import assert_equal, assert_true
from ...helpers import BaseApplicationTest


class TestServicePage(BaseApplicationTest):

    def setup(self):
        super(TestServicePage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.views.data_api_client'
        ).start()

        self.service = self._get_service_fixture_data()

    def teardown(self):
        self._data_api_client.stop()

    def test_service_page_url(self):
        self._data_api_client.get_service.return_value = \
            self.service

        res = self.client.get('/services/1234567890123456')
        assert_equal(200, res.status_code)
        assert_true("<h1>Blogging platform</h1>" in res.get_data(as_text=True))
