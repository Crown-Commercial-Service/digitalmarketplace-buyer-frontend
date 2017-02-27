import os
import json
from app.main.presenters.service_presenters import (
    Service, Meta, lowercase_first_character_unless_part_of_acronym,
    chunk_string
)
from app import content_loader


def _get_fixture_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'g6_service_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


def test_chunk_string():
    assert list(chunk_string("123456", 3)) == ["123", "456"]
    assert list(chunk_string("1234567", 3)) == ["123", "456", "7"]
    assert list(chunk_string("12345678910", 4)) == ["1234", "5678", "910"]
    assert list(chunk_string("123456789101", 4)) == ["1234", "5678", "9101"]


class TestService(object):
    def setup_method(self, method):
        self.fixture = _get_fixture_data()
        self.fixture = self.fixture['services']
        self.service = Service(
            self.fixture, content_loader.get_builder('g-cloud-6', 'display_service')
        )

    def test_title_attribute_is_set(self):
        assert self.service.title == self.fixture['serviceName']

    def test_lot_attribute_is_set(self):
        assert self.service.lot == self.fixture['lot']

    def test_framework_attribute_is_set(self):
        assert self.service.frameworkName == self.fixture['frameworkName']

    def test_Service_works_if_supplierName_is_not_set(self):
        del self.fixture['supplierName']
        self.service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        assert not hasattr(self.service, 'supplierName')

    def test_Service_works_if_serviceFeatures_is_not_set(self):
        del self.fixture['serviceFeatures']
        self.service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        assert not hasattr(self.service, 'features')

    def test_Service_works_if_serviceBenefits_is_not_set(self):
        del self.fixture['serviceBenefits']
        self.service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        assert not hasattr(self.service, 'benefits')

    def test_features_attributes_are_correctly_set(self):
        assert hasattr(self.service, 'features')
        assert len(self.service.features) == 6

    def test_benefits_attributes_are_correctly_set(self):
        assert hasattr(self.service, 'benefits')
        assert len(self.service.benefits) == 6

    def test_attributes_are_correctly_set(self):
        service = Service(
            self.fixture, content_loader.get_builder('g-cloud-6', 'display_service').filter({'lot': 'iaas'})
        )
        assert service.attributes[0]['name'] == 'Support'
        assert len(service.attributes) == 30
        assert len(list(service.attributes[0]['rows'])) == 5

    def test_the_support_attribute_group_is_not_there_if_no_attributes(self):
        del self.fixture['openStandardsSupported']
        service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        for group in service.attributes:
            assert group['name'] != 'Open standards', "Support group should not be found"

    def test_only_attributes_with_a_valid_type_are_added_to_groups(self):
        invalidValue = (u'Manuals provided', u'CMS training')
        self.fixture['onboardingGuidance'] = invalidValue
        service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        for group in service.attributes:
            assert not (group['name'] == 'External interface protection' and 'onboardingGuidance' in group), \
                "Attribute with tuple value should not be in group"

    def test_attributes_with_assurance_in_the_fields_add_it_correctly(self):
        service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        for group in service.attributes:
            if group['name'] == 'Data-in-transit protection':
                for row in group['rows']:
                    # string with bespoke assurance caveat
                    if row.label == 'Data protection between services':
                        assert row.value == [u'No encryption']
                        assert row.assurance == u'independent validation of assertion'
                    # string with standard assurance caveat
                    if row.label == 'Data protection within service':
                        assert row.value == [u'No encryption']

    def test_attributes_with_assurance_for_a_list_value_has_a_caveat(self):
        service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        for group in service.attributes:
            if group['name'] == 'Asset protection and resilience':
                for row in group['rows']:
                    # list with bespoke assurance caveat
                    if row.label == 'Data management location':
                        assert u'independent validation of assertion' in row.assurance


class TestMeta(object):
    def setup_method(self, method):
        self.fixture = _get_fixture_data()['services']
        self.meta = Meta(self.fixture)

    def test_Meta_instance_has_the_correct_attributes(self):
        assert hasattr(self.meta, 'price')
        assert hasattr(self.meta, 'priceCaveats')
        assert hasattr(self.meta, 'documents')
        assert hasattr(self.meta, 'serviceId')
        assert hasattr(self.meta, 'contact')
        assert 'name' in self.meta.contact
        assert 'phone' in self.meta.contact
        assert 'email' in self.meta.contact

    def test_contact_information_is_correct(self):
        assert self.meta.contact['name'] == 'Contact name'
        assert self.meta.contact['phone'] == 'Contact number'
        assert self.meta.contact['email'] == 'Contact email'

    def test_get_service_id_returns_the_correct_information(self):
        assert self.meta.get_service_id({'id': 1234567890123456}) == ['1234', '5678', '9012', '3456']
        assert self.meta.get_service_id({'id': 123456789012345}) == ['1234', '5678', '9012', '345']
        assert self.meta.get_service_id({'id': '5-G4-1046-001'}) == ['5-G4-1046-001']

    def test_external_framework_url_returns_correct_suffix(self):
        assert self.meta.get_external_framework_url({'frameworkSlug': 'g-cloud-7'}) == (
            'http://ccs-agreements.cabinetoffice.gov.uk/contracts/rm1557vii'
        )
        assert self.meta.get_external_framework_url({'frameworkSlug': 'g-cloud-6'}) is None
        assert self.meta.get_external_framework_url({'frameworkSlug': 'None'}) is None

    def test_get_documents_returns_the_correct_document_information(self):
        keys = [
            'pricing',
            'sfiaRateDocument',
            'serviceDefinitionDocument',
            'termsAndConditions'
        ]
        expected_information = [
            {
                'name': 'Pricing',
                'url': (
                    'https://assets.digitalmarketplace.service.gov.uk/' +
                    'documents/123456/1234567890123456-pricing-document.pdf'
                )
            },
            {
                'name': 'SFIA rate card',
                'url': (
                    'https://assets.digitalmarketplace.service.gov.uk/' +
                    'documents/123456/1234567890123456-sfia-rate-card.pdf'
                )
            },
            {
                'name': 'Service definition',
                'url': (
                    'https://assets.digitalmarketplace.service.gov.uk/' +
                    'documents/' +
                    '123456/1234567890123456-service-definition-document.pdf'
                )
            },
            {
                'name': 'Terms and conditions',
                'url': (
                    'https://assets.digitalmarketplace.service.gov.uk/' +
                    'documents/' +
                    '123456/1234567890123456-terms-and-conditions.pdf'
                )
            }
        ]
        documents = self.meta.get_documents(self.fixture)
        for idx, document in enumerate(documents):
            assert documents[idx]['name'] == expected_information[idx]['name']
            assert documents[idx]['url'] == expected_information[idx]['url']
            assert documents[idx]['extension'] == 'pdf'

    def test_vat_status_is_correct(self):
        # if VAT is not included
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Excluding VAT' in price_caveats
        # if VAT is included
        self.fixture['vatIncluded'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Including VAT' in price_caveats

    def test_education_pricing_status_is_correct(self):
        # if Education pricing is included
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Education pricing available' in price_caveats
        # if Education pricing is excluded
        self.fixture['educationPricing'] = False
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Education pricing available' not in price_caveats

    def test_termination_costs_status_is_correct(self):
        # if Termination costs are excluded
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Termination costs apply' not in price_caveats
        # if Termination costs are included
        self.fixture['terminationCost'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Termination costs apply' in price_caveats
        # if the question wasn't asked
        del self.fixture['terminationCost']
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Termination costs apply' not in price_caveats

    def test_minimum_contract_status_is_correct(self):
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Minimum contract period: Month' in price_caveats

    def test_options_are_correct_if_both_false(self):
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Trial and free options available' not in price_caveats
        assert 'Trial option available' not in price_caveats
        assert 'Free option available' not in price_caveats

    def test_options_are_correct_if_free_is_false_and_trial_true(self):
        self.fixture['trialOption'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Trial and free options available' not in price_caveats
        assert 'Free option available' not in price_caveats
        assert 'Trial option available' in price_caveats

    def test_options_are_correct_if_free_is_true_and_trial_false(self):
        self.fixture['freeOption'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Trial and free options available' not in price_caveats
        assert 'Trial option available' not in price_caveats
        assert 'Free option available' in price_caveats

    def test_options_are_correct_if_both_are_not_set(self):
        del self.fixture['freeOption']
        del self.fixture['trialOption']
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Trial and free options available' not in price_caveats
        assert 'Trial option available' not in price_caveats
        assert 'Free option available' not in price_caveats


class TestHelpers(object):
    def test_normal_string_can_be_lowercased(self):
        assert lowercase_first_character_unless_part_of_acronym(
            "Independent validation of assertion"
        ) == "independent validation of assertion"

    def test_string_starting_with_acronym_can_be_lowercased(self):
        assert lowercase_first_character_unless_part_of_acronym(
            "CESG-assured components"
        ) == "CESG-assured components"
