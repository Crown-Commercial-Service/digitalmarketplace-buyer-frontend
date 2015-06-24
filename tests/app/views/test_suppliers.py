import mock
from nose.tools import assert_equal, assert_true
from ...helpers import BaseApplicationTest


class TestSuppliersPage(BaseApplicationTest):
    def setup(self):
        super(TestSuppliersPage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.suppliers.data_api_client'
        ).start()

        self.suppliers_by_prefix = self._get_suppliers_by_prefix_fixture_data()  # noqa
        self.suppliers_by_prefix_page_2 = self._get_suppliers_by_prefix_fixture_data_page_2()  # noqa
        self.suppliers_by_prefix_next_and_prev = self._get_suppliers_by_prefix_fixture_with_next_and_prev()  # noqa
        self.supplier = self._get_supplier_fixture_data()  # noqa
        self._data_api_client.find_suppliers.return_value = self.suppliers_by_prefix  # noqa
        self._data_api_client.get_supplier.return_value = self.supplier  # noqa

    def teardown(self):
        self._data_api_client.stop()

    def test_should_show_suppliers_prefixed_by_a_default(self):
        res = self.client.get('/g-cloud/suppliers')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>A</h1>'
            in res.get_data(as_text=True))

    def test_should_show_suppliers_prefixed_by_a_param(self):
        res = self.client.get('/g-cloud/suppliers?prefix=M')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>M</h1>'
            in res.get_data(as_text=True))

    def test_should_use_uppercase_prefix(self):
        res = self.client.get('/g-cloud/suppliers?prefix=b')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>B</h1>'
            in res.get_data(as_text=True))

    def test_should_use_default_if_invalid(self):
        res = self.client.get('/g-cloud/suppliers?prefix=+')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>A</h1>'
            in res.get_data(as_text=True))

    def test_should_use_default_if_multichar_prefix(self):
        res = self.client.get('/g-cloud/suppliers?prefix=Prefix')
        assert_equal(200, res.status_code)

        assert_true(
            '<h1>A</h1>'
            in res.get_data(as_text=True))

    def test_should_use_123_prefix(self):
        res = self.client.get('/g-cloud/suppliers?prefix=123')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>123</h1>'
            in res.get_data(as_text=True))

    def test_should_show_supplier_names_link_and_description(self):
        res = self.client.get('/g-cloud/suppliers')
        assert_equal(200, res.status_code)

        supplier_html = self._strip_whitespace('''
        <div class="search-result">
            <h2 class="search-result-title">
            <a href="/g-cloud/supplier/586559">ABM UNITED KINGDOM LTD</a>
        </h2>

        <p class="search-result-excerpt">
            We specialise in the development of intelligence and investigative software across law enforcement agencies, public sector and commercial organisations. We provide solutions to clients across the globe, including the United Kingdom, Australia, USA, Canada and Europe.
        </p>
        </div>''')  # noqa

        assert_true(
            supplier_html
            in self._strip_whitespace(res.get_data(as_text=True)))

    def test_should_show_a_t_z_nav(self):
        res = self.client.get('/g-cloud/suppliers')
        assert_equal(200, res.status_code)

        supplier_html = self._strip_whitespace('''
        <div id="global-atoz-navigation" class="header-context">
        <nav>
            <ol class="group" role="breadcrumbs">
                <li><a class="home" href="/g-cloud/suppliers?prefix=A">A</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=B">B</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=C">C</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=D">D</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=E">E</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=F">F</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=G">G</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=H">H</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=I">I</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=J">J</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=K">K</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=L">L</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=M">M</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=N">N</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=O">O</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=P">P</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=Q">Q</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=R">R</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=S">S</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=T">T</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=U">U</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=V">V</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=W">W</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=X">X</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=Y">Y</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=Z">Z</a></li>
                <li><a class="home" href="/g-cloud/suppliers?prefix=123">123</a></li>
            </ol>
        </nav>
        </div>
        ''')  # noqa

        assert_true(
            supplier_html
            in self._strip_whitespace(res.get_data(as_text=True)))

    def test_should_show_warning_message_on_supplier_list(self):
        res = self.client.get('/g-cloud/suppliers')
        assert_equal(200, res.status_code)

        assert_true(
            '<strong>This page is for information only</strong><br/>Services should be chosen using your requirements.'  # noqa
            in res.get_data(as_text=True))
        assert_true(
            'Please use the <a href="https://www.digitalmarketplace.service.gov.uk/buyers-guide/">buyers guide</a> for help.'  # noqa
            in res.get_data(as_text=True))

    def test_should_show_next_page_on_supplier_list(self):
        res = self.client.get('/g-cloud/suppliers')
        assert_equal(200, res.status_code)
        html = self._strip_whitespace('''
        <li class="next">
            <a href="/g-cloud/suppliers?prefix=A&amp;page=2">
                Next <span class="visuallyhidden">page</span>
            </a>
        </li>
        ''')
        assert_true(
            html
            in self._strip_whitespace(res.get_data(as_text=True))
        )

    def test_should_show_next_nav_on_supplier_list(self):
        self._data_api_client.find_suppliers.return_value = self.suppliers_by_prefix_page_2  # noqa
        res = self.client.get('/g-cloud/suppliers?page=2')
        assert_equal(200, res.status_code)
        html = self._strip_whitespace('''
        <li class="previous">
            <a href="/g-cloud/suppliers?prefix=A&amp;page=1">
                Previous <span class="visuallyhidden">page</span>
            </a>
        </li>
        ''')
        assert_true(
            html
            in self._strip_whitespace(res.get_data(as_text=True))
        )

    def test_should_show_next_and_prev_nav_on_supplier_list(self):
        self._data_api_client.find_suppliers.return_value = self.suppliers_by_prefix_next_and_prev  # noqa
        res = self.client.get('/g-cloud/suppliers?page=2')

        assert_equal(200, res.status_code)
        previous_link = self._strip_whitespace('''
        <li class="previous">
            <a href="/g-cloud/suppliers?prefix=A&amp;page=1">
                Previous <span class="visuallyhidden">page</span>
            </a>
        </li>
        ''')
        assert_true(
            previous_link
            in self._strip_whitespace(res.get_data(as_text=True))
        )
        next_link = self._strip_whitespace('''
        <li class="next">
            <a href="/g-cloud/suppliers?prefix=A&amp;page=3">
                Next <span class="visuallyhidden">page</span>
            </a>
        </li>
        ''')
        assert_true(
            next_link
            in self._strip_whitespace(res.get_data(as_text=True))
        )

    def test_should_show_warning_message_on_supplier_details(self):
        res = self.client.get('/g-cloud/supplier/92191')
        assert_equal(200, res.status_code)

        assert_true(
            '<strong>This page is for information only</strong><br/>Services should be chosen using your requirements.'  # noqa
            in res.get_data(as_text=True))
        assert_true(
            'Please use the <a href="https://www.digitalmarketplace.service.gov.uk/buyers-guide/">buyers guide</a> for help.'  # noqa
            in res.get_data(as_text=True))


    # TEST ZERO SERVICES SUPPLIERS NOT SHOWN
    # TEST SUPPLIER DETAILS PAGE