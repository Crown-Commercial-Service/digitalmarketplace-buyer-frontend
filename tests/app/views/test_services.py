
import mock
import re
from nose.tools import assert_equal, assert_true
from ...helpers import BaseApplicationTest


class TestServicePage(BaseApplicationTest):

    def setup(self):
        super(TestServicePage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.views.data_api_client'
        ).start()

        self.supplier = self._get_supplier_fixture_data()
        self._data_api_client.get_supplier.return_value = self.supplier

    def teardown(self):
        self._data_api_client.stop()

    def _assert_contact_details(self, res):

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

    def _assert_document_links(self, res):

        service = self.service['services']

        # Hardcoded stuff comes from 'get_documents' in service_presenters.py
        url_keys = [
            'pricingDocumentURL',
            'sfiaRateDocumentURL',
            'serviceDefinitionDocumentURL',
            'termsAndConditionsDocumentURL'
        ]

        for url_key in url_keys:
            if url_key in self.service['services']:
                assert_true(
                    '<a href="{}" class="document-link-with-icon">'.format(
                        # Replace all runs of whitespace with a '%20'
                        self._replace_whitespace(service[url_key], '%20')
                    ) in res.get_data(as_text=True)
                )

        if 'additionalDocumentURLs' in service:
            for document_url in service['additionalDocumentURLs']:
                assert_true(
                    '<a href="{}" class="document-link-with-icon">'.format(
                        self._replace_whitespace(document_url, '%20')
                    ) in res.get_data(as_text=True)
                )

    def _replace_whitespace(self, string, replacement_substring):
            # Replace all runs of whitespace with replacement_substring
            return re.sub(r"\s+", replacement_substring, string)

    def _assert_service_page_url(self):

        service_id = self.service['services']['id']
        service_title = self.service['services']['title']

        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert_equal(200, res.status_code)
        assert_true(
            "<h1>{}</h1>".format(service_title)
            in res.get_data(as_text=True)
        )

        self._assert_contact_details(res)
        self._assert_document_links(res)

    def _assert_redirect_deprecated_service_page_url(self):
        self._data_api_client.get_service.return_value = \
            self.service

        service_id = self.service['services']['id']

        service_id_string = "{}".format(service_id)
        res = self.client.get('service/{}'.format(service_id_string.lower()))
        assert_equal(301, res.status_code)
        assert_equal(
            'http://localhost/g-cloud/services/{}'.format(
                service_id_string.upper()
            ),
            res.location)

    def test_g5_service_page_url(self):

        self.service = self._get_g5_service_fixture_data()
        self._data_api_client.get_service.return_value = self.service

        self._assert_redirect_deprecated_service_page_url()
        self._assert_service_page_url()

    def test_g6_service_page_url(self):

        self.service = self._get_g6_service_fixture_data()
        self._data_api_client.get_service.return_value = self.service

        self._assert_redirect_deprecated_service_page_url()
        self._assert_service_page_url()
