import re

from lxml import html

from app.main.helpers import framework_helpers
from ...helpers import BaseApplicationTest, BaseAPIClientMixin


class DataAPIClientMixin(BaseAPIClientMixin):
    data_api_client_patch_path = 'app.main.views.g_cloud.data_api_client'


class UnavailableBanner(object):

    def __init__(self, document):
        self.banner = document.xpath(
            '//main//section[@class="dm-banner"]'
        )

    @property
    def exists(self):
        return bool(self.banner)

    def heading_text(self):
        return self.banner[0].xpath('h2/text()')[0].strip()

    def body_text(self):
        return self.banner[0].xpath('div/text()')[0].strip()


class TestServicePage(DataAPIClientMixin, BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)

        self.supplier = self._get_supplier_fixture_data()
        self.service = self._get_g6_service_fixture_data()

        self.data_api_client.get_supplier.return_value = self.supplier
        self.data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-6')
        self.data_api_client.get_service.return_value = self.service

        self.lots = framework_helpers.get_lots_by_slug(
            self._get_framework_fixture_data('g-cloud-6')['frameworks']
        )

    def _assert_contact_details(self, document):

        supplier_name = self.supplier['suppliers']['name']
        contact_info = self.supplier['suppliers']['contactInformation'][0]

        meta = document.xpath('//div[@id="meta"]')[0]
        contact_details_p = meta.xpath('//h2[text()="Contact"]/following-sibling::p[1]')[0].text_content()
        contact_heading = meta.xpath('//h2[text()="Contact"]/following-sibling::p[1]/span/text()')[0]

        assert contact_heading == supplier_name

        for contact_detail in [
            supplier_name,
            contact_info['contactName'],
            contact_info['phoneNumber'],
            contact_info['email']
        ]:
            assert contact_detail in contact_details_p

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
            '//div[@id="meta"]//ul[contains(@class, "govuk-list")]//li/section[@class="dm-attachment"]//p/a')]

        print(str(doc_hrefs))

        for url_key in url_keys:
            if url_key in self.service['services']:
                assert (
                    # Replace all runs of whitespace with a '%20'
                    self._replace_whitespace(service[url_key], '%20')
                    in doc_hrefs
                )

        if 'additionalDocumentURLs' in service:
            for document_url in service['additionalDocumentURLs']:
                assert (
                    self._replace_whitespace(document_url, '%20')
                    in doc_hrefs
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
            '/g-cloud': 'Cloud hosting, software and support',
            '/g-cloud/search?lot={}'.format(lot): self.lots[lot]['name']
        }

        breadcrumbs = document.xpath("//div[contains(@class, 'govuk-breadcrumbs')]/ol/li/a")
        assert len(breadcrumbs) == 3

        for breadcrumb in breadcrumbs:
            breadcrumb_text = breadcrumb.text_content().strip()
            breakcrumb_href = breadcrumb.get('href').strip()
            # check that the link exists in our expected breadcrumbs
            assert breakcrumb_href in breadcrumbs_expected
            # check that the link text is the same
            assert breadcrumb_text == breadcrumbs_expected[breakcrumb_href]

    def _assert_service_page_url(self):

        service_id = self.service['services']['id']
        service_title = self.service['services']['title']
        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        page_title = document.xpath('//main[@id="main-content"]//h1/text()')[0]
        assert page_title == "{}".format(service_title)

        self._assert_contact_details(document)
        self._assert_document_links(document)
        self._assert_breadcrumbs(document, self.service['services']['lot'])

    def _get_status_update_audit_event_for(self,
                                           update_type=None,
                                           old_status=None,
                                           new_status=None,
                                           timestamp=None,
                                           service=None):
        audit_event = {
            "links": {
                "oldArchivedService": "http://localhost:5000/archived-services/1",
                "self": "http://localhost:5000/audit-events",
                "newArchivedService": "http://localhost:5000/archived-services/2"
            },
            "type": update_type,
            "acknowledged": False,
            "user": "joebloggs",
            "id": 1,
            "createdAt": timestamp
        }

        if update_type == 'update_service_status':
            audit_event["data"] = {
                "supplierId": service["supplierId"],
                "newArchivedServiceId": 2,
                "new_status": new_status,
                "supplierName": service["supplierName"],
                "serviceId": service["id"],
                "old_status": old_status,
                "oldArchivedServiceId": 1
            }
        elif update_type == "framework_update":
            audit_event["data"] = {
                "update": {
                    "status": new_status,
                    "clarificationQuestionsOpen": True
                }
            }

        return audit_event

    def test_g5_service_page_url(self):
        self.data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-5')
        self.service = self._get_g5_service_fixture_data()
        self.data_api_client.get_service.return_value = self.service

        self._assert_service_page_url()

    def test_g6_service_page_url(self):
        self._assert_service_page_url()

    def test_published_service_doesnt_have_unavailable_banner(self):
        service_id = self.service['services']['id']
        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        unavailable_banner = UnavailableBanner(document)
        assert not unavailable_banner.exists

    def test_enabled_service_has_unavailable_banner(self):
        self.service['services']['status'] = 'enabled'
        self.service['serviceMadeUnavailableAuditEvent'] = \
            self._get_status_update_audit_event_for(
                update_type='update_service_status',
                old_status='published',
                new_status='enabled',
                timestamp='2016-01-05T17:01:07.649587Z',
                service=self.service['services']
        )
        self.data_api_client.get_service.return_value = self.service

        service_id = self.service['services']['id']
        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert res.status_code == 410

        document = html.fromstring(res.get_data(as_text=True))

        unavailable_banner = UnavailableBanner(document)
        assert unavailable_banner.exists
        assert unavailable_banner.heading_text() == '{} stopped offering this service on {}'.format(
            self.service['services']['supplierName'],
            'Tuesday 5 January 2016.',
        )
        assert unavailable_banner.body_text() == 'Any existing contracts for this service are still valid.'

    def test_disabled_service_has_unavailable_banner(self):
        self.service['services']['status'] = 'disabled'
        self.service['serviceMadeUnavailableAuditEvent'] = \
            self._get_status_update_audit_event_for(
                update_type='update_service_status',
                old_status='published',
                new_status='disabled',
                timestamp='2016-01-05T17:01:07.649587Z',
                service=self.service['services']
        )
        self.data_api_client.get_service.return_value = self.service

        service_id = self.service['services']['id']
        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert res.status_code == 410

        document = html.fromstring(res.get_data(as_text=True))

        unavailable_banner = UnavailableBanner(document)
        assert unavailable_banner.exists
        assert unavailable_banner.heading_text() == '{} stopped offering this service on {}'.format(
            self.service['services']['supplierName'],
            'Tuesday 5 January 2016.',
        )
        assert unavailable_banner.body_text() == 'Any existing contracts for this service are still valid.'

    def test_expired_framework_causes_service_to_have_unavailable_banner(self):
        self.service['services']['frameworkStatus'] = 'expired'
        self.service['serviceMadeUnavailableAuditEvent'] = \
            self._get_status_update_audit_event_for(
                update_type='framework_update',
                old_status='live',
                new_status='expired',
                timestamp='2016-01-05T17:01:07.649587Z',
                service=self.service['services']
        )
        self.data_api_client.get_service.return_value = self.service

        service_id = self.service['services']['id']
        framework_copy_with_updated_expiry_date = self.data_api_client.get_framework.return_value.copy()
        framework_copy_with_updated_expiry_date['frameworks']['frameworkExpiresAtUTC'] = '2020-01-05T17:01:07.649587Z'
        self.data_api_client.get_framework.return_value = framework_copy_with_updated_expiry_date
        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert res.status_code == 410

        document = html.fromstring(res.get_data(as_text=True))
        unavailable_banner = UnavailableBanner(document)
        assert unavailable_banner.exists
        assert unavailable_banner.heading_text() == 'This {} service is no longer available to buy.'.format(
            self.service['services']['frameworkName'],
        )
        assert unavailable_banner.body_text() == 'The {} framework expired on {}. Any existing contracts with {} are' \
            ' still valid.'.format(
                self.service['services']['frameworkName'],
                'Sunday 5 January 2020',
                self.service['services']['supplierName'],
        )

    def test_pre_live_framework_causes_404(self):
        self.service['services']['frameworkStatus'] = 'standstill'
        self.data_api_client.get_service.return_value = self.service

        service_id = self.service['services']['id']

        res = self.client.get('/g-cloud/services/{}'.format(service_id))

        assert res.status_code == 404

    def test_service_not_a_g_cloud_service_causes_404(self):
        self.service['services']['frameworkSlug'] = 'digital-outcomes-and-specialists'
        self.data_api_client.get_service.return_value = self.service
        self.data_api_client.get_framework.return_value = self._get_framework_fixture_data(
            'digital-outcomes-and-specialists'
        )

        service_id = self.service['services']['id']
        # This is the "Display service" page, generally for G-Cloud services, but in this case it now has a valid
        # digital-outcomes-and-specialists service ID.
        res = self.client.get('/g-cloud/services/{}'.format(service_id))

        assert res.status_code == 404

    def test_certifications_section_not_displayed_if_service_has_none(self):
        self.service['services']['vendorCertifications'] = []
        self.data_api_client.get_service.return_value = self.service

        service_id = self.service['services']['id']

        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        attribute_headings = document.xpath('//main//div[@id="service-attributes"]//h2/text()')

        attribute_headings = [
            heading.strip() for heading in attribute_headings]

        assert 'Certifications' not in attribute_headings

    def test_deleted_service_causes_404(self):
        self.service["services"]["status"] = "deleted"
        self.data_api_client.get_service.return_value = self.service

        service_id = self.service['services']['id']
        res = self.client.get(f'/g-cloud/services/{service_id}')
        assert res.status_code == 404
