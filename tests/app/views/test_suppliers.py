# coding: utf-8
import mock
from lxml import html

from nose.tools import assert_equal, assert_true, assert_false
from ...helpers import BaseApplicationTest
from app.api_client.error import APIError


@mock.patch('app.main.suppliers.DataAPIClient')
class TestSuppliersPage(BaseApplicationTest):
    def setup(self):
        super(TestSuppliersPage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.suppliers.DataAPIClient'
        ).start()

        self.supplier = self._get_supplier_fixture_data()
        self.supplier_with_minimum_data = self._get_supplier_with_minimum_fixture_data()

    def teardown(self):
        self._data_api_client.stop()

    def test_should_have_supplier_details_on_supplier_page(self, api_client):
        api_client.return_value.get_supplier.return_value = self.supplier

        res = self.client.get('/suppliers/1')
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200
        assert document.xpath('//h1')[0].text.strip() == 'Example PTY LTD'

    def test_should_show_supplier_with_minimum_data(self, api_client):
        api_client.return_value.get_supplier.return_value = self.supplier_with_minimum_data

        res = self.client.get('/suppliers/1')
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200
        assert document.xpath('//h1')[0].text.strip() == 'Example PTY LTD'
        assert 'None' not in res.get_data(as_text=True)

    def test_should_return_404_if_supplier_code_doesnt_exist(self, api_client):
        api_client.return_value.get_supplier.side_effect = APIError(mock.Mock(status_code=404))

        res = self.client.get('/suppliers/1')
        assert res.status_code == 404

        # Check that the test is not silently passing because the URL changed
        api_client.return_value.get_supplier.side_effect = APIError(mock.Mock(status_code=500))

        res = self.client.get('/suppliers/1')
        assert res.status_code == 500
