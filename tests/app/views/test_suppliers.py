import mock
from nose.tools import assert_equal, assert_true
from ...helpers import BaseApplicationTest


class TestSuppliersPage(BaseApplicationTest):
    def setup(self):
        super(TestSuppliersPage, self).setup()

        self._data_api_client = mock.patch(
                'app.main.suppliers.data_api_client'
            ).start()

        self.suppliers_by_prefix = self._get_suppliers_by_prefix_fixture_data() # noqa
        self._data_api_client.find_suppliers.return_value = \
            self.suppliers_by_prefix

        def teardown(self):
            self._data_api_client.stop()

    def test_should_show_suppliers_prefixed_by_a_default(self):
        res = self.client.get('/suppliers')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>A</h1>'
            in res.get_data(as_text=True))

    def test_should_show_suppliers_prefixed_by_a_param(self):
        res = self.client.get('/suppliers?prefix=M')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>M</h1>'
            in res.get_data(as_text=True))

    def test_should_use_uppercase_prefix(self):
        res = self.client.get('/suppliers?prefix=b')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>B</h1>'
            in res.get_data(as_text=True))

    def test_should_use_default_if_invalid(self):
        res = self.client.get('/suppliers?prefix=+')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>A</h1>'
            in res.get_data(as_text=True))

    def test_should_use_first_char_if_multichar_prefix(self):
        res = self.client.get('/suppliers?prefix=Prefix')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>P</h1>'
            in res.get_data(as_text=True))

    def test_should_use_other_prefix(self):
        res = self.client.get('/suppliers?prefix=other')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>other</h1>'
            in res.get_data(as_text=True))

    def test_should_show_supplier_names_link_and_description(self):
        res = self.client.get('/suppliers')
        assert_equal(200, res.status_code)

        supplier_html = self._strip_whitespace('''
        <div class="search-result">
            <h2 class="search-result-title">
            <a href="/suppliers/586559">ABM UNITED KINGDOM LTD</a>
        </h2>

        <p class="search-result-excerpt">
            We specialise in the development of intelligence and investigative software across law enforcement agencies, public sector and commercial organisations. We provide solutions to clients across the globe, including the United Kingdom, Australia, USA, Canada and Europe.
        </p>
        </div>''')  # noqa

        assert_true(
            supplier_html
            in self._strip_whitespace(res.get_data(as_text=True)))

    def test_should_show_warning_message_on_supplier_list(self):
        res = self.client.get('/suppliers')
        assert_equal(200, res.status_code)

        assert_true(
            '<strong>This page is for information only</strong><br/>Services should be chosen using your requirements.'  # noqa
            in res.get_data(as_text=True))
        assert_true(
            'Please use the <a href="https://www.digitalmarketplace.service.gov.uk/buyers-guide/">buyers guide</a> for help.'  # noqa
            in res.get_data(as_text=True))
