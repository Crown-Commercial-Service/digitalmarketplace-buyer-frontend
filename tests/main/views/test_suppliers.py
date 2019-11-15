# coding: utf-8
import mock

from lxml import html

from dmapiclient import APIError

from ...helpers import BaseApplicationTest, BaseAPIClientMixin


class DataAPIClientMixin(BaseAPIClientMixin):
    data_api_client_patch_path = 'app.main.views.suppliers.data_api_client'


class TestSuppliersPage(DataAPIClientMixin, BaseApplicationTest):
    def setup_method(self, method):
        super().setup_method(method)

        self.suppliers_by_prefix = self._get_suppliers_by_prefix_fixture_data()
        self.suppliers_by_prefix_page_2 = self._get_suppliers_by_prefix_fixture_data_page_2()
        self.suppliers_by_prefix_next_and_prev = self._get_suppliers_by_prefix_fixture_with_next_and_prev()
        self.supplier = self._get_supplier_fixture_data()
        self.supplier_with_minimum_data = self._get_supplier_with_minimum_fixture_data()
        self.data_api_client.find_suppliers.return_value = self.suppliers_by_prefix
        self.data_api_client.get_supplier.return_value = self.supplier

        gcloud9_framework = self._get_framework_fixture_data('g-cloud-9')['frameworks']
        self.data_api_client.find_frameworks.return_value = {'frameworks': [gcloud9_framework]}

    def test_should_call_api_with_correct_params(self):
        self.client.get('/g-cloud/suppliers')
        self.data_api_client.find_suppliers.assert_called_once_with('A', 1, 'g-cloud')

    def test_should_show_suppliers_prefixed_by_a_default(self):
        res = self.client.get('/g-cloud/suppliers')
        assert res.status_code == 200
        assert self._strip_whitespace(
            '<li class="selected"><span class="visuallyhidden">Suppliers starting with </span><strong>A</strong></li>'
        ) in self._strip_whitespace(res.get_data(as_text=True))

    def test_should_show_suppliers_prefixed_by_a_param(self):
        res = self.client.get('/g-cloud/suppliers?prefix=M')
        self.data_api_client.find_suppliers.assert_called_once_with('M', 1, 'g-cloud')
        assert res.status_code == 200
        assert self._strip_whitespace(
            '<li class="selected"><span class="visuallyhidden">Suppliers starting with </span><strong>M</strong></li>'
        ) in self._strip_whitespace(res.get_data(as_text=True))

    def test_should_use_uppercase_prefix(self):
        res = self.client.get('/g-cloud/suppliers?prefix=b')
        assert res.status_code == 200
        assert self._strip_whitespace(
            '<li class="selected"><span class="visuallyhidden">Suppliers starting with </span><strong>B</strong></li>'
        ) in self._strip_whitespace(res.get_data(as_text=True))

    def test_should_use_default_if_invalid(self):
        res = self.client.get('/g-cloud/suppliers?prefix=+')
        self.data_api_client.find_suppliers.assert_called_once_with('A', 1, 'g-cloud')

        assert res.status_code == 200
        assert self._strip_whitespace(
            '<li class="selected"><span class="visuallyhidden">Suppliers starting with </span><strong>A</strong></li>'
        ) in self._strip_whitespace(res.get_data(as_text=True))

    def test_should_use_default_if_multichar_prefix(self):
        res = self.client.get('/g-cloud/suppliers?prefix=Prefix')
        self.data_api_client.find_suppliers.assert_called_once_with('A', 1, 'g-cloud')

        assert res.status_code == 200

        assert self._strip_whitespace(
            '<li class="selected"><span class="visuallyhidden">Suppliers starting with </span><strong>A</strong></li>'
        ) in self._strip_whitespace(res.get_data(as_text=True))

    def test_should_use_number_range_prefix(self):
        res = self.client.get('/g-cloud/suppliers?prefix=other')
        self.data_api_client.find_suppliers.assert_called_once_with(u'other', 1, 'g-cloud')

        assert res.status_code == 200
        assert self._strip_whitespace(
            u'<li class="selected"><span class="visuallyhidden">Suppliers starting with </span>' +
            u'<strong>1–9</strong></li>'
        ) in self._strip_whitespace(res.get_data(as_text=True))

    def test_should_show_supplier_names_link_and_description(self):
        res = self.client.get('/g-cloud/suppliers')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        assert document.xpath(
            "//*[contains(@class, 'search-result')]"
            "[.//h2//a[@href=$u][normalize-space(string())=$t]]"
            "[.//p[normalize-space(string())=$b]]",
            u="/g-cloud/supplier/586559",
            t="ABM UNITED KINGDOM LTD",
            b="""We specialise in the development of intelligence and investigative software across law enforcement agencies, public sector and commercial organisations. We provide solutions to clients across the globe, including the United Kingdom, Australia, USA, Canada and Europe.""",  # noqa
        )

    def test_should_show_a_t_z_nav(self):
        res = self.client.get('/g-cloud/suppliers')
        assert res.status_code == 200

        supplier_html = self._strip_whitespace(u'''
                <li class="selected"><span class="visuallyhidden">Suppliers starting with </span><strong>A</strong></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=B">B</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=C">C</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=D">D</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=E">E</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=F">F</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=G">G</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=H">H</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=I">I</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=J">J</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=K">K</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=L">L</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=M">M</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=N">N</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=O">O</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=P">P</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=Q">Q</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=R">R</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=S">S</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=T">T</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=U">U</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=V">V</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=W">W</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=X">X</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=Y">Y</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=Z">Z</a></li>
                <li><span class="visuallyhidden">Suppliers starting with </span><a href="/g-cloud/suppliers?prefix=other">1–9</a></li>
        ''')  # noqa
        assert supplier_html in self._strip_whitespace(res.get_data(as_text=True))

    def test_should_show_no_suppliers_page_if_api_returns_404(self):
        self.data_api_client.find_suppliers.side_effect = APIError(mock.Mock(status_code=404))

        res = self.client.get('/g-cloud/suppliers')
        assert res.status_code == 404

    def test_should_show_next_page_on_supplier_list(self):
        res = self.client.get('/g-cloud/suppliers')
        assert res.status_code == 200
        html_tag = '<li class="next">'
        html_link = '<a href="/g-cloud/suppliers?'
        html_prefix = 'prefix=A'
        html_page = 'page=2'

        assert html_tag in res.get_data(as_text=True)
        assert html_prefix in res.get_data(as_text=True)
        assert html_link in res.get_data(as_text=True)
        assert html_page in res.get_data(as_text=True)

    def test_should_show_next_nav_on_supplier_list(self):
        self.data_api_client.find_suppliers.return_value = self.suppliers_by_prefix_page_2  # noqa
        res = self.client.get('/g-cloud/suppliers?page=2')
        self.data_api_client.find_suppliers.assert_called_once_with('A', 2, 'g-cloud')

        assert res.status_code == 200
        html_tag = '<li class="previous">'
        html_link = '<a href="/g-cloud/suppliers?'
        html_prefix = 'prefix=A'
        html_page = 'page=1'
        assert html_tag in res.get_data(as_text=True)
        assert html_prefix in res.get_data(as_text=True)
        assert html_link in res.get_data(as_text=True)
        assert html_page in res.get_data(as_text=True)

    def test_should_show_next_and_prev_nav_on_supplier_list(self):
        self.data_api_client.find_suppliers.return_value = self.suppliers_by_prefix_next_and_prev  # noqa
        res = self.client.get('/g-cloud/suppliers?page=2')

        assert res.status_code == 200

        previous_html_tag = '<li class="previous">'
        previous_html_link = '<a href="/g-cloud/suppliers?'
        previous_html_prefix = 'prefix=A'
        previous_html_page = 'page=1'

        assert previous_html_tag in res.get_data(as_text=True)
        assert previous_html_prefix in res.get_data(as_text=True)
        assert previous_html_link in res.get_data(as_text=True)
        assert previous_html_page in res.get_data(as_text=True)

        next_html_tag = '<li class="next">'
        next_html_link = '<a href="/g-cloud/suppliers?'
        next_html_prefix = 'prefix=A'
        next_html_page = 'page=3'

        assert next_html_tag in res.get_data(as_text=True)
        assert next_html_link in res.get_data(as_text=True)
        assert next_html_prefix in res.get_data(as_text=True)
        assert next_html_page in res.get_data(as_text=True)

    def test_should_have_supplier_details_on_supplier_page(self):
        res = self.client.get('/g-cloud/supplier/92191')
        assert res.status_code == 200
        assert '<h1>ExampleCompanyLimited</h1>' in self._strip_whitespace(res.get_data(as_text=True))
        assert "Example Company Limited is an innovation station sensation; we deliver software so bleeding "\
            "edge you literally won&#39;t be able to run any of it on your systems." in res.get_data(as_text=True)

    def test_should_show_supplier_with_no_desc_or_clients(self):
        self.data_api_client.get_supplier.return_value = self.supplier_with_minimum_data  # noqa

        res = self.client.get('/g-cloud/supplier/92191')
        assert res.status_code == 200
        assert '<h1>ExampleCompanyLimited</h1>' in self._strip_whitespace(res.get_data(as_text=True))
        assert self._strip_whitespace("<h2>Clients</h2>") not in self._strip_whitespace(res.get_data(as_text=True))

    def test_should_have_supplier_contact_details_on_supplier_page(self):
        res = self.client.get('/g-cloud/supplier/92191')

        assert res.status_code == 200
        assert self._strip_whitespace(
            '<span itemprop="name">John Example</span>'
        ) in self._strip_whitespace(res.get_data(as_text=True))
        assert self._strip_whitespace(
            '<span itemprop="telephone">07309404738</span>'
        ) in self._strip_whitespace(res.get_data(as_text=True))

        email_html = '''<a href="mailto:j@examplecompany.biz"
        data-event-category="Email a supplier"
        data-event-label="Example Company Limited">j@examplecompany.biz</a>'''

        assert self._strip_whitespace(email_html) in self._strip_whitespace(res.get_data(as_text=True))

    def test_should_have_minimum_supplier_contact_details_on_supplier_page(self):
        self.data_api_client.get_supplier.return_value = self.supplier_with_minimum_data  # noqa

        res = self.client.get('/g-cloud/supplier/92191')

        assert res.status_code == 200
        assert self._strip_whitespace(
            '<span itemprop="name">John Example</span>'
        ) in self._strip_whitespace(res.get_data(as_text=True))

        email_html = '''<a href="mailto:j@examplecompany.biz"
        data-event-category="Email a supplier"
        data-event-label="Example Company Limited">j@examplecompany.biz</a>'''

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
