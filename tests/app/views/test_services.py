
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
        self.supplier = self._get_supplier_fixture_data()

        self._data_api_client.get_service.return_value = self.service
        self._data_api_client.get_supplier.return_value = self.supplier

    def teardown(self):
        self._data_api_client.stop()

    def test_service_page_redirect(self):
        self._data_api_client.get_service.return_value = \
            self.service

        res = self.client.get('/services/1234567890123456')
        assert_equal(301, res.status_code)
        assert_equal(
            'http://localhost/g-cloud/services/1234567890123456',
            res.location)

    def test_service_page_url(self):
        self._data_api_client.get_service.return_value = \
            self.service
        service_id = self.service['services']['id']

        res = self.client.get('/services/{}'.format(service_id))
        assert_equal(200, res.status_code)
        assert_true("<h1>Blogging platform</h1>" in res.get_data(as_text=True))

        supplier_name = self.supplier['suppliers']['name']
        contact_info = self.supplier['suppliers']['contactInformation'][0]

        assert_true(
            "Contact {}".format(supplier_name) in res.get_data(as_text=True))

        for contact_detail in [
            contact_info['contactName'],
            contact_info['phoneNumber'],
            'mailto:{}'.format(contact_info['email'])
        ]:

            assert_true(
                "{}".format(contact_detail)
                in res.get_data(as_text=True))
