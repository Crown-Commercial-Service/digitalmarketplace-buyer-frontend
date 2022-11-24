# coding: utf-8
from ...helpers import BaseApplicationTest, BaseAPIClientMixin


class DataAPIClientMixin(BaseAPIClientMixin):
    data_api_client_patch_path = 'app.main.views.suppliers.data_api_client'


class TestSuppliersPage(DataAPIClientMixin, BaseApplicationTest):
    def setup_method(self, method):
        super().setup_method(method)

        self.supplier = self._get_supplier_fixture_data()
        self.supplier_with_minimum_data = self._get_supplier_with_minimum_fixture_data()
        self.data_api_client.get_supplier.return_value = self.supplier

    def test_should_redirect_to_apply_to_supply(self):
        response = self.client.get('/g-cloud/suppliers')
        assert 301 == response.status_code
        assert "https://www.applytosupply.digitalmarketplace.service.gov.uk/g-cloud/suppliers" == response.location

    def test_should_have_supplier_details_on_supplier_page(self):
        res = self.client.get('/g-cloud/supplier/92191')
        assert res.status_code == 200
        assert '<h1class="govuk-heading-l">ExampleCompanyLimited</h1>' \
            in self._strip_whitespace(res.get_data(as_text=True))
        assert "Example Company Limited is an innovation station sensation; we deliver software so bleeding "\
            "edge you literally won&#39;t be able to run any of it on your systems." in res.get_data(as_text=True)

    def test_should_show_supplier_with_no_desc_or_clients(self):
        self.data_api_client.get_supplier.return_value = self.supplier_with_minimum_data  # noqa

        res = self.client.get('/g-cloud/supplier/92191')
        assert res.status_code == 200
        assert '<h1class="govuk-heading-l">ExampleCompanyLimited</h1>' \
            in self._strip_whitespace(res.get_data(as_text=True))
        assert self._strip_whitespace("<h2>Clients</h2>") not in self._strip_whitespace(res.get_data(as_text=True))

    def test_should_have_supplier_contact_details_on_supplier_page(self):
        res = self.client.get('/g-cloud/supplier/92191')

        assert res.status_code == 200
        assert self._strip_whitespace(
            'John Example'
        ) in self._strip_whitespace(res.get_data(as_text=True))
        assert self._strip_whitespace(
            '07309404738'
        ) in self._strip_whitespace(res.get_data(as_text=True))

        email_html = '''<a href="mailto:j@examplecompany.biz"
        data-event-category="Email a supplier"
        data-event-label="Example Company Limited">
        <span class="govuk-visually-hidden">Email: </span>j@examplecompany.biz</a>'''

        assert self._strip_whitespace(email_html) in self._strip_whitespace(res.get_data(as_text=True))

    def test_should_have_minimum_supplier_contact_details_on_supplier_page(self):
        self.data_api_client.get_supplier.return_value = self.supplier_with_minimum_data  # noqa

        res = self.client.get('/g-cloud/supplier/92191')

        assert res.status_code == 200
        assert self._strip_whitespace(
            'John Example'
        ) in self._strip_whitespace(res.get_data(as_text=True))

        email_html = '''<a href="mailto:j@examplecompany.biz"
        data-event-category="Email a supplier"
        data-event-label="Example Company Limited">
        <span class="govuk-visually-hidden">Email: </span>j@examplecompany.biz</a>'''

        assert self._strip_whitespace(email_html) in self._strip_whitespace(res.get_data(as_text=True))

    def test_should_not_show_web_address(self):
        res = self.client.get('/g-cloud/supplier/92191')
        assert 'www.examplecompany.biz' not in res.get_data(as_text=True)

    def test_should_not_show_supplier_without_services_on_framework(self):
        supplier_data = self.supplier.copy()
        supplier_data['suppliers']['service_counts']['G-Cloud 9'] = 0
        self.data_api_client.get_supplier.return_value = supplier_data

        res = self.client.get('/g-cloud/supplier/92191')
        assert res.status_code == 404
