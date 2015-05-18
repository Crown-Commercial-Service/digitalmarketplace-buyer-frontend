import os
import json
import unittest
from nose.tools import assert_equal, assert_is_none

from flask import Markup
from mock import Mock
from werkzeug.datastructures import MultiDict
from app.presenters.search_presenters import SearchResults, SearchSummary


def _get_fixture_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_results_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


def _get_fixture_multiple_pages_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_results_multiple_pages_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


class TestSearchResults(unittest.TestCase):

    def _get_service_result_by_id(self, results, id):
        for result in results:
            if result['id'] == id:
                return result
        return False

    def setUp(self):
        self.fixture = _get_fixture_data()
        self.multiple_pages_fixture = _get_fixture_multiple_pages_data()
        self.service = SearchResults(self.fixture)

    def tearDown(self):
        pass

    def test_search_results_is_set(self):
        search_results_instance = SearchResults(self.fixture)
        self.assertTrue(hasattr(search_results_instance, 'search_results'))

    def test_search_results_total_is_set(self):
        search_results_instance = SearchResults(self.fixture)
        self.assertTrue(hasattr(search_results_instance, 'total'))
        assert_equal(search_results_instance.total, 9)

    def test_search_results_page_is_not_set(self):
        search_results_instance = SearchResults(self.fixture)
        self.assertFalse(hasattr(search_results_instance, 'page'))

    def test_search_results_page_is_set(self):
        search_results_instance = SearchResults(self.multiple_pages_fixture)
        self.assertTrue(hasattr(search_results_instance, 'page'))
        assert_equal(search_results_instance.page, "20")

    def test_highlighting_for_one_line_summary(self):
        search_results_instance = SearchResults(self.fixture)
        result_with_one_line_highlight = self._get_service_result_by_id(
            search_results_instance.search_results, '4-G4-0871-001'
        )
        self.assertEquals(
            result_with_one_line_highlight['serviceSummary'],
            Markup(
                u"Fastly <em>CDN</em> (Content Delivery Network) speeds up" +
                u" delivery of your website and its content to your"
            )
        )

    def test_highlighting_for_multiple_line_summary(self):
        search_results_instance = SearchResults(self.fixture)
        result_with_multi_line_highlight = self._get_service_result_by_id(
            search_results_instance.search_results, '4-G1-0340-001'
        )
        self.assertEquals(
            result_with_multi_line_highlight['serviceSummary'],
            Markup(
                u" Baycloud Systems or in a suitable Content Delivery"
                u" Network (<em>CDN</em>) such as the Windows Azure" +
                u" <em>CDN</em>. The <em>CDN</em> improves performance" +
                u" by caching content at locations closest to visitors" +
                u" to customer\u2019s websites. The Windows Azure" +
                u" <em>CDN</em> is a managed service that is operated by" +
                u" Microsoft and has a 99.99% monthly"
            )
        )

    def test_highlighting_only_happens_on_service_summaries(self):
        search_results_instance = SearchResults(self.fixture)
        result_with_service_name_highlight = self._get_service_result_by_id(
            search_results_instance.search_results, '5-G3-0279-010'
        )
        self.assertEquals(
            result_with_service_name_highlight['serviceName'],
            "CDN VDMS"
        )


class TestSearchSummary(unittest.TestCase):

    def setUp(self):
        self.fixture = _get_fixture_data()
        self.search_results = SearchResults(self.fixture)
        self.request_args = MultiDict([('lot', ['saas'])])

    def tearDown(self):
        pass

    def test_search_summary_works_with_none(self):
        empty_result = self.fixture.copy()
        empty_result['services'] = []
        empty_result['total'] = '0'
        search_results_instance = SearchResults(empty_result)
        self.assertEqual(
            search_results_instance.summary,
            Markup(
                u"<span class='search-summary-count'>0</span> results found"))

    def test_search_summary_for_multiple_results(self):
        search_summary = SearchSummary(9, self.request_args, filter_groups)
        self.assertEqual(search_summary.markup(), Markup(
            u"<span class='search-summary-count'>9</span> results found"))

    def test_search_summary_for_single_result(self):
        single_result = self.fixture.copy()
        single_result['services'] = [single_result['services'][0]]
        single_result['total'] = '1'
        search_summary = SearchSummary(1, self.request_args, filter_groups)
        self.assertEqual(
            search_summary.markup(),
            Markup(
                u"<span class='search-summary-count'>1</span> result found"))

    def test_search_summary_with_a_single_filter(self):
        self.request_args.setlist(('serviceTypes', ['collaboration']))
        search_summary = SearchSummary(9, self.request_args, filter_groups)
        self.assertEqual(
            search_summary.markup(),
            Markup(
                u"<span class='search-summary-count'>9</span> results found" +
                u" in the category <em>collaboration</em>"))

    def test_search_summary_with_a_group_of_two_filters(self):
        self.request_args.setlist(
            'serviceTypes',
            ['collaboration', 'energy and environment'])
        search_summary = SearchSummary(9, self.request_args, filter_groups)
        self.assertEqual(
            search_summary.markup(),
            Markup(
                u"<span class='search-summary-count'>9</span> results found" +
                u" in the categories <em>Collaboration</em> and" +
                u" <em>Energy and environment</em>"))

    def test_search_summary_with_a_group_of_three_filters(self):
        self.request_args.setlist(
            'serviceTypes',
            ['collaboration', 'energy and environment', 'healthcare']
        )
        search_summary = SearchSummary(9, self.request_args, filter_groups)
        self.assertEqual(
            search_summary.markup(),
            Markup(
                u"<span class='search-summary-count'>9</span> results found" +
                u" in the categories <em>Collaboration</em>," +
                u" <em>Energy and environment</em> and <em>Healthcare</em>"))

    def test_search_summary_with_two_filter_groups(self):
        self.request_args.setlist(
            'serviceTypes',
            ['collaboration', 'energy and environment']
        )
        self.request_args.setlist(
            'datacentreTier',
            ['tia-942 tier 1', 'uptime institute tier 1']
        )
        search_summary = SearchSummary(9, self.request_args, filter_groups)
        self.assertEqual(
            search_summary.markup(),
            Markup(
                u"<span class='search-summary-count'>9</span> results found" +
                u" in the categories <em>collaboration</em> and" +
                u" <em>Energy and environment</em> and" +
                u" with a datacentre tier of <em>TIA-942 Tier 1" +
                u" </em> or <em>Uptime Institute Tier 1</em>"))

    def test_search_summary_with_three_filters(self):
        self.request_args.setlist(
            'serviceTypes',
            ['collaboration', 'energy and environment',]
        )
        self.request_args.setlist(
            'datacentreTier',
            ['tia-942 tier 1', 'uptime institute tier 1']
        )
        self.request_args.setlist(
            'freeOption',
            ['true']
        )
        self.request_args.setlist(
            'trialOption',
            ['true']
        )
        search_summary = SearchSummary(9, self.request_args, filter_groups)
        self.assertEqual(
            search_summary.markup(),
            Markup(
                u"<span class='search-summary-count'>9</span> results found" +
                u" in the categories <em>collaboration</em> and" +
                u" <em>Energy and environment</em>," +
                u" with a datacentre tier of <em>TIA-942 Tier 1" +
                u" </em> or <em>Uptime Institute Tier 1</em> and" +
                u" with a <em>Free option</em> and a <em>Trial option</em>"))

filter_groups = [
    {
        'depends_on_lots': ['scs', 'saas', 'iaas'],
        'filters': [{
            'id': 'serviceTypes-implementation',
            'lots': ['scs'],
            'name': 'serviceTypes',
            'value': 'implementation',
            'label': 'Implementation'
        }, {
            'id': 'serviceTypes-ongoing-support',
            'lots': ['scs'],
            'name': 'serviceTypes',
            'value': 'ongoing support',
            'label': 'Ongoing support'
        }, {
            'id': 'serviceTypes-planning',
            'lots': ['scs'],
            'name': 'serviceTypes',
            'value': 'planning',
            'label': 'Planning'
        }, {
            'id': 'serviceTypes-testing',
            'lots': ['scs'],
            'name': 'serviceTypes',
            'value': 'testing',
            'label': 'Testing'
        }, {
            'id': 'serviceTypes-training',
            'lots': ['scs'],
            'name': 'serviceTypes',
            'value': 'training',
            'label': 'Training'
        }, {
            'id': 'serviceTypes-accounting-and-finance',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'accounting and finance',
            'label': 'Accounting and finance'
        }, {
            'id': 'serviceTypes-business-intelligence-and-analytics',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'business intelligence and analytics',
            'label': 'Business intelligence and analytics'
        }, {
            'id': 'serviceTypes-collaboration',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'collaboration',
            'label': 'Collaboration'
        }, {
            'id': 'serviceTypes-creative-and-design',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'creative and design',
            'label': 'Creative and design'
        }, {
            'id': 'serviceTypes-customer-relationship-management-(crm)',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'customer relationship management (crm)',
            'label': 'Customer relationship management (CRM)'
        }, {
            'id': 'serviceTypes-data-management',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'data management',
            'label': 'Data management'
        }, {
            'id': (
                'serviceTypes-electronic-document-and-records-management' +
                '-(edrm)'),
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'electronic document and records management (edrm)',
            'label': 'Electronic document and records management (EDRM)'
        }, {
            'id': 'serviceTypes-energy-and-environment',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'energy and environment',
            'label': 'Energy and environment'
        }, {
            'id': 'serviceTypes-healthcare',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'healthcare',
            'label': 'Healthcare'
        }, {
            'id': 'serviceTypes-human-resources-and-employee-management',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'human resources and employee management',
            'label': 'Human resources and employee management'
        }, {
            'id': 'serviceTypes-it-management',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'it management',
            'label': 'IT management'
        }, {
            'id': 'serviceTypes-legal',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'legal',
            'label': 'Legal'
        }, {
            'id': 'serviceTypes-libraries',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'libraries',
            'label': 'Libraries'
        }, {
            'id': 'serviceTypes-marketing',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'marketing',
            'label': 'Marketing'
        }, {
            'id': 'serviceTypes-operations-management',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'operations management',
            'label': 'Operations management'
        }, {
            'id': 'serviceTypes-project-management-and-planning',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'project management and planning',
            'label': 'Project management and planning'
        }, {
            'id': 'serviceTypes-sales',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'sales',
            'label': 'Sales'
        }, {
            'id': 'serviceTypes-schools-and-education',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'schools and education',
            'label': 'Schools and education'
        }, {
            'id': 'serviceTypes-security',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'security',
            'label': 'Security'
        }, {
            'id': 'serviceTypes-software-development-tools',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'software development tools',
            'label': 'Software development tools'
        }, {
            'id': 'serviceTypes-telecoms',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'telecoms',
            'label': 'Telecoms'
        }, {
            'id': 'serviceTypes-transport-and-logistics',
            'lots': ['saas'],
            'name': 'serviceTypes',
            'value': 'transport and logistics',
            'label': 'Transport and logistics'
        }, {
            'id': 'serviceTypes-compute',
            'lots': ['iaas'],
            'name': 'serviceTypes',
            'value': 'compute',
            'label': 'Compute'
        }, {
            'id': 'serviceTypes-storage',
            'lots': ['iaas'],
            'name': 'serviceTypes',
            'value': 'storage',
            'label': 'Storage'
        }],
        'label': 'Categories'
    }, {
        'depends_on_lots': ['saas', 'paas', 'iaas', 'saas', 'paas', 'iaas'],
        'filters': [{
            'id': 'freeOption',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'freeOption',
            'value': 'true',
            'label': 'Free option'
        }, {
            'id': 'trialOption',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'trialOption',
            'value': 'true',
            'label': 'Trial option'
        }],
        'label': 'Pricing'
    }, {
        'depends_on_lots': ['saas', 'paas', 'iaas', 'scs'],
        'filters': [{
            'id': 'minimumContractPeriod-hour',
            'lots': ['saas', 'paas', 'iaas', 'scs'],
            'name': 'minimumContractPeriod',
            'value': 'hour',
            'label': 'Hour'
        }, {
            'id': 'minimumContractPeriod-day',
            'lots': ['saas', 'paas', 'iaas', 'scs'],
            'name': 'minimumContractPeriod',
            'value': 'day',
            'label': 'Day'
        }, {
            'id': 'minimumContractPeriod-month',
            'lots': ['saas', 'paas', 'iaas', 'scs'],
            'name': 'minimumContractPeriod',
            'value': 'month',
            'label': 'Month'
        }, {
            'id': 'minimumContractPeriod-year',
            'lots': ['saas', 'paas', 'iaas', 'scs'],
            'name': 'minimumContractPeriod',
            'value': 'year',
            'label': 'Year'
        }, {
            'id': 'minimumContractPeriod-other',
            'lots': ['saas', 'paas', 'iaas', 'scs'],
            'name': 'minimumContractPeriod',
            'value': 'other',
            'label': 'Other'
        }],
        'label': 'Minimum contract period'
    }, {
        'depends_on_lots': [
            'saas', 'paas', 'iaas', 'saas', 'paas', 'iaas', 'saas', 'paas',
            'iaas', 'saas', 'paas', 'iaas', 'saas', 'paas', 'iaas', 'scs'],
        'filters': [{
            'id': 'dataExtractionRemoval',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'dataExtractionRemoval',
            'value': 'true',
            'label': 'Data extraction/removal plan in place'
        }, {
            'id': 'datacentresEUCode',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'datacentresEUCode',
            'value': 'true',
            'label': 'Datacentres adhere to EU Code of Conduct for Operations'
        }, {
            'id': 'dataBackupRecovery',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'dataBackupRecovery',
            'value': 'true',
            'label': 'Backup, disaster recovery and resilience plan in place'
        }, {
            'id': 'selfServiceProvisioning',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'selfServiceProvisioning',
            'value': 'true',
            'label': 'Self-service provisioning supported'
        }, {
            'id': 'supportForThirdParties',
            'lots': ['saas', 'paas', 'iaas', 'scs'],
            'name': 'supportForThirdParties',
            'value': 'true',
            'label': 'Support accessible to any third-party suppliers'
        }],
        'label': 'Service management'
    }, {
        'depends_on_lots': ['saas', 'paas', 'iaas'],
        'filters': [{
            'id': 'datacentreTier-tia-942-tier-1',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'datacentreTier',
            'value': 'tia-942 tier 1',
            'label': 'TIA-942 Tier 1'
        }, {
            'id': 'datacentreTier-tia-942-tier-2',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'datacentreTier',
            'value': 'tia-942 tier 2',
            'label': 'TIA-942 Tier 2'
        }, {
            'id': 'datacentreTier-tia-942-tier-3',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'datacentreTier',
            'value': 'tia-942 tier 3',
            'label': 'TIA-942 Tier 3'
        }, {
            'id': 'datacentreTier-tia-942-tier-4',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'datacentreTier',
            'value': 'tia-942 tier 4',
            'label': 'TIA-942 Tier 4'
        }, {
            'id': 'datacentreTier-uptime-institute-tier-1',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'datacentreTier',
            'value': 'uptime institute tier 1',
            'label': 'Uptime Institute Tier 1'
        }, {
            'id': 'datacentreTier-uptime-institute-tier-2',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'datacentreTier',
            'value': 'uptime institute tier 2',
            'label': 'Uptime Institute Tier 2'
        }, {
            'id': 'datacentreTier-uptime-institute-tier-3',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'datacentreTier',
            'value': 'uptime institute tier 3',
            'label': 'Uptime Institute Tier 3'
        }, {
            'id': 'datacentreTier-uptime-institute-tier-4',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'datacentreTier',
            'value': 'uptime institute tier 4',
            'label': 'Uptime Institute Tier 4'
        }, {
            'id': 'datacentreTier-none-of-the-above',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'datacentreTier',
            'value': 'none of the above',
            'label': 'None of the above'
        }],
        'label': 'Datacentre tier'
    }, {
        'depends_on_lots': ['saas', 'paas', 'iaas'],
        'filters': [{
            'id': 'networksConnected-internet',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'networksConnected',
            'value': 'internet',
            'label': 'Internet'
        }, {
            'id': 'networksConnected-public-services-network-(psn)',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'networksConnected',
            'value': 'public services network (psn)',
            'label': 'Public Services Network (PSN)'
        }, {
            'id': 'networksConnected-government-secure-intranet-(gsi)',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'networksConnected',
            'value': 'government secure intranet (gsi)',
            'label': 'Government Secure intranet (GSi)'
        }, {
            'id': 'networksConnected-police-national-network-(pnn)',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'networksConnected',
            'value': 'police national network (pnn)',
            'label': 'Police National Network (PNN)'
        }, {
            'id': 'networksConnected-new-nhs-network-(n3)',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'networksConnected',
            'value': 'new nhs network (n3)',
            'label': 'New NHS Network (N3)'
        }, {
            'id': 'networksConnected-joint-academic-network-(janet)',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'networksConnected',
            'value': 'joint academic network (janet)',
            'label': 'Joint Academic Network (JANET)'
        }, {
            'id': 'networksConnected-other',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'networksConnected',
            'value': 'other',
            'label': 'Other'
        }],
        'label': 'Networks the service is directly connected to'
    }, {
        'depends_on_lots': [
            'saas', 'paas', 'iaas', 'saas', 'paas', 'iaas', 'saas', 'paas',
            'iaas'],
        'filters': [{
            'id': 'apiAccess',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'apiAccess',
            'value': 'true',
            'label': 'API access available and supported'
        }, {
            'id': 'openStandardsSupported',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'openStandardsSupported',
            'value': 'true',
            'label': 'Open standards supported and documented'
        }, {
            'id': 'openSource',
            'lots': ['saas', 'paas', 'iaas'],
            'name': 'openSource',
            'value': 'true',
            'label': 'Open-source software used and supported'
        }],
        'label': 'Interoperability'
    }
]
