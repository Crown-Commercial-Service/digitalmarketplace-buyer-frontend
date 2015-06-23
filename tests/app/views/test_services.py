
import mock
import re
from lxml import html
from nose.tools import assert_equal, assert_in, assert_false
from ...helpers import BaseApplicationTest


class TestServicePage(BaseApplicationTest):

    def setup(self):
        super(TestServicePage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.views.data_api_client'
        ).start()

        self.supplier = self._get_supplier_fixture_data()
        self._data_api_client.get_supplier.return_value = self.supplier

        self.lots = {
            'SaaS': 'Software as a Service',
            'PaaS': 'Platform as a Service',
            'IaaS': 'Infrastructure as a Service',
            'SCS': 'Specialist Cloud Services'
        }

    def teardown(self):
        self._data_api_client.stop()

    def _assert_contact_details(self, document):

        supplier_name = self.supplier['suppliers']['name']
        contact_info = self.supplier['suppliers']['contactInformation'][0]

        meta = document.xpath('//div[@id="meta"]')[0]
        contact_heading = meta.xpath('//div/p[@class="contact-details-organisation"]/span/text()')[0]  # noqa
        ps = [
            p.text_content().strip()
            for p in meta.xpath('//div[@class="contact-details"]//p')
        ]

        assert_equal(supplier_name, contact_heading)

        for contact_detail in [
            contact_info['contactName'],
            contact_info['phoneNumber'],
            contact_info['email']
        ]:
            assert_in("{}".format(contact_detail), ps)

    def _assert_document_links(self, document):

        service = self.service['services']

        # Hardcoded stuff comes from 'get_documents' in service_presenters.py
        url_keys = [
            'pricingDocumentURL',
            'sfiaRateDocumentURL',
            'serviceDefinitionDocumentURL',
            'termsAndConditionsDocumentURL'
        ]

        doc_hrefs = [a.get('href') for a in document.xpath(
            '//div[@id="meta"]//li[@class="document-list-item"]/a')]

        for url_key in url_keys:
            if url_key in self.service['services']:
                assert_in(
                    # Replace all runs of whitespace with a '%20'
                    self._replace_whitespace(service[url_key], '%20'),
                    doc_hrefs
                )

        if 'additionalDocumentURLs' in service:
            for document_url in service['additionalDocumentURLs']:
                assert_in(
                    self._replace_whitespace(document_url, '%20'),
                    doc_hrefs
                )

    def _replace_whitespace(self, string, replacement_substring):
            # Replace all runs of whitespace with replacement_substring
            return re.sub(r"\s+", replacement_substring, string)

    def _assert_breadcrumbs(self, document, lot):
        # check links exist back to
        # (1) digital marketplace,
        # (2) cloud tech and support,
        # (3) search page for lot

        # Hardcoded stuff found in 'views.py'
        breadcrumbs_expected = {
            '/': 'Digital Marketplace',
            '/g-cloud': 'Cloud technology and support',
            '/g-cloud/search?lot={}'.format(lot.lower()): self.lots[lot]
        }

        breadcrumbs = document.xpath('//div[@id="global-breadcrumb"]//a')
        assert_equal(3, len(breadcrumbs))

        for breadcrumb in breadcrumbs:
            breadcrumb_text = breadcrumb.text_content().strip()
            breakcrumb_href = breadcrumb.get('href').strip()
            # check that the link exists in our expected breadcrumbs
            assert_in(
                breakcrumb_href, breadcrumbs_expected
            )
            # check that the link text is the same
            assert_equal(
                breadcrumb_text, breadcrumbs_expected[breakcrumb_href]
            )

    def _assert_service_page_url(self):

        service_id = self.service['services']['id']
        service_title = self.service['services']['title']

        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        page_title = document.xpath('//div[@id="wrapper"]//h1/text()')[0]
        assert_equal("{}".format(service_title), page_title)

        self._assert_contact_details(document)
        self._assert_document_links(document)
        self._assert_breadcrumbs(document, self.service['services']['lot'])

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

    def test_enabled_service_not_displayed(self):
        self.service = self._get_g6_service_fixture_data()
        self.service['services']['status'] = 'enabled'
        self._data_api_client.get_service.return_value = \
            self.service
        service_id = self.service['services']['id']
        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert_equal(404, res.status_code)

    def test_disabled_service_not_displayed(self):
        self.service = self._get_g6_service_fixture_data()
        self.service['services']['status'] = 'disabled'
        self._data_api_client.get_service.return_value = \
            self.service
        service_id = self.service['services']['id']
        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert_equal(404, res.status_code)

    def test_certifications_section_not_displayed_if_service_has_none(self):
        self.service = self._get_g6_service_fixture_data()
        self.service['services']['vendorCertifications'] = []
        self._data_api_client.get_service.return_value = self.service
        service_id = self.service['services']['id']

        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        attribute_headings = document.xpath(
            '//div[@id="wrapper"]//div[@class="grid-row service-attributes"]' +
            '//h2/text()')

        attribute_headings = [
            heading.strip() for heading in attribute_headings]

        assert_false('Certifications' in attribute_headings)
