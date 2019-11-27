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

        document = html.fromstring(res.get_data(as_text=True))

        nav_lis = document.xpath(
            "//li[.//*[contains(@class, 'visuallyhidden')][normalize-space(string())=$s]][.//a[@href]]",
            s="Suppliers starting with",
        )
        expected_strings = (
            ("Suppliers starting with B", "B", "/g-cloud/suppliers?prefix=B",),
            ("Suppliers starting with C", "C", "/g-cloud/suppliers?prefix=C",),
            ("Suppliers starting with D", "D", "/g-cloud/suppliers?prefix=D",),
            ("Suppliers starting with E", "E", "/g-cloud/suppliers?prefix=E",),
            ("Suppliers starting with F", "F", "/g-cloud/suppliers?prefix=F",),
            ("Suppliers starting with G", "G", "/g-cloud/suppliers?prefix=G",),
            ("Suppliers starting with H", "H", "/g-cloud/suppliers?prefix=H",),
            ("Suppliers starting with I", "I", "/g-cloud/suppliers?prefix=I",),
            ("Suppliers starting with J", "J", "/g-cloud/suppliers?prefix=J",),
            ("Suppliers starting with K", "K", "/g-cloud/suppliers?prefix=K",),
            ("Suppliers starting with L", "L", "/g-cloud/suppliers?prefix=L",),
            ("Suppliers starting with M", "M", "/g-cloud/suppliers?prefix=M",),
            ("Suppliers starting with N", "N", "/g-cloud/suppliers?prefix=N",),
            ("Suppliers starting with O", "O", "/g-cloud/suppliers?prefix=O",),
            ("Suppliers starting with P", "P", "/g-cloud/suppliers?prefix=P",),
            ("Suppliers starting with Q", "Q", "/g-cloud/suppliers?prefix=Q",),
            ("Suppliers starting with R", "R", "/g-cloud/suppliers?prefix=R",),
            ("Suppliers starting with S", "S", "/g-cloud/suppliers?prefix=S",),
            ("Suppliers starting with T", "T", "/g-cloud/suppliers?prefix=T",),
            ("Suppliers starting with U", "U", "/g-cloud/suppliers?prefix=U",),
            ("Suppliers starting with V", "V", "/g-cloud/suppliers?prefix=V",),
            ("Suppliers starting with W", "W", "/g-cloud/suppliers?prefix=W",),
            ("Suppliers starting with X", "X", "/g-cloud/suppliers?prefix=X",),
            ("Suppliers starting with Y", "Y", "/g-cloud/suppliers?prefix=Y",),
            ("Suppliers starting with Z", "Z", "/g-cloud/suppliers?prefix=Z",),
            ("Suppliers starting with 1–9", "1–9", "/g-cloud/suppliers?prefix=other",),
        )

        assert tuple(
            (
                nl.xpath("normalize-space(string())"),
                nl.xpath("normalize-space(string(.//a))"),
                nl.xpath(".//a/@href")[0],
            ) for nl in nav_lis
        ) == expected_strings
        # these lis should all have the same parent
        assert len(frozenset(nl.getparent() for nl in nav_lis)) == 1
        # that parent should only have one other li
        assert len(nav_lis[0].getparent().getchildren()) == len(expected_strings) + 1
        # that li should be the first and match this pattern
        assert nav_lis[0].getparent().xpath(
            "./*[1][normalize-space(string())=$t][not(.//a[@href])]",
            t="Suppliers starting with A",
        )

    def test_should_show_no_suppliers_page_if_api_returns_404(self):
        self.data_api_client.find_suppliers.side_effect = APIError(mock.Mock(status_code=404))

        res = self.client.get('/g-cloud/suppliers')
        assert res.status_code == 404

    def test_should_show_next_page_on_supplier_list(self):
        res = self.client.get('/g-cloud/suppliers')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        assert document.xpath("//li[contains(@class, 'next')]")
        assert document.xpath(
            "//a[starts-with(@href, $u)][contains(@href, $px)][contains(@href, $pg)]",
            u="/g-cloud/suppliers?",
            px="prefix=A",
            pg="page=2",
        )

    def test_should_show_next_nav_on_supplier_list(self):
        self.data_api_client.find_suppliers.return_value = self.suppliers_by_prefix_page_2  # noqa
        res = self.client.get('/g-cloud/suppliers?page=2')
        self.data_api_client.find_suppliers.assert_called_once_with('A', 2, 'g-cloud')

        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        assert document.xpath("//li[contains(@class, 'previous')]")
        assert document.xpath(
            "//a[starts-with(@href, $u)][contains(@href, $px)][contains(@href, $pg)]",
            u="/g-cloud/suppliers?",
            px="prefix=A",
            pg="page=1",
        )

    def test_should_show_next_and_prev_nav_on_supplier_list(self):
        self.data_api_client.find_suppliers.return_value = self.suppliers_by_prefix_next_and_prev  # noqa
        res = self.client.get('/g-cloud/suppliers?page=2')

        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        assert document.xpath("//li[contains(@class, 'previous')]")
        assert document.xpath(
            "//a[starts-with(@href, $u)][contains(@href, $px)][contains(@href, $pg)]",
            u="/g-cloud/suppliers?",
            px="prefix=A",
            pg="page=1",
        )

        assert document.xpath("//li[contains(@class, 'next')]")
        assert document.xpath(
            "//a[starts-with(@href, $u)][contains(@href, $px)][contains(@href, $pg)]",
            u="/g-cloud/suppliers?",
            px="prefix=A",
            pg="page=3",
        )

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
