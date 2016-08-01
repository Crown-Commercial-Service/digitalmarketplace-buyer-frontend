import os
import json
import unittest
from app.presenters.service_presenters import (
    Service, Attribute, Meta, lowercase_first_character_unless_part_of_acronym
)
from app import content_loader


def _get_fixture_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'g6_service_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


class TestService(unittest.TestCase):

    def setUp(self):
        self.fixture = _get_fixture_data()
        self.fixture = self.fixture['services']
        self.service = Service(
            self.fixture, content_loader.get_builder('g-cloud-6', 'display_service')
        )

    def tearDown(self):
        pass

    def test_title_attribute_is_set(self):
        self.assertEquals(
            self.service.title,
            self.fixture['serviceName'])

    def test_lot_attribute_is_set(self):
        self.assertEquals(
            self.service.lot,
            self.fixture['lot'])

    def test_framework_attribute_is_set(self):
        self.assertEquals(
            self.service.frameworkName,
            self.fixture['frameworkName'])

    def test_Service_works_if_supplierName_is_not_set(self):
        del self.fixture['supplierName']
        self.service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        self.assertFalse(hasattr(self.service, 'supplierName'))

    def test_Service_works_if_serviceFeatures_is_not_set(self):
        del self.fixture['serviceFeatures']
        self.service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        self.assertFalse(hasattr(self.service, 'features'))

    def test_Service_works_if_serviceBenefits_is_not_set(self):
        del self.fixture['serviceBenefits']
        self.service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        self.assertFalse(hasattr(self.service, 'benefits'))

    def test_features_attributes_are_correctly_set(self):
        self.assertTrue(hasattr(self.service, 'features'))
        self.assertEquals(len(self.service.features), 6)

    def test_benefits_attributes_are_correctly_set(self):
        self.assertTrue(hasattr(self.service, 'benefits'))
        self.assertEquals(len(self.service.benefits), 6)

    def test_attributes_are_correctly_set(self):
        service = Service(
            self.fixture, content_loader.get_builder('g-cloud-6', 'display_service')
        )
        self.assertEquals(
            service.attributes[0]['name'],
            'Support'
        )
        self.assertEquals(
            len(service.attributes),
            30
        )
        self.assertEquals(
            len(list(service.attributes[0]['rows'])),
            5
        )

    def test_the_support_attribute_group_is_not_there_if_no_attributes(self):
        del self.fixture['openStandardsSupported']
        service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        for group in service.attributes:
            if group['name'] == 'Open standards':
                self.fail("Support group should not be found")

    def test_only_attributes_with_a_valid_type_are_added_to_groups(self):
        invalidValue = (u'Manuals provided', u'CMS training')
        self.fixture['onboardingGuidance'] = invalidValue
        service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        for group in service.attributes:
            if (
                (group['name'] == 'External interface protection') and
                ('onboardingGuidance' in group)
            ):
                self.fail("Attribute with tuple value should not be in group")

    def test_attributes_with_assurance_in_the_fields_add_it_correctly(self):
        service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        for group in service.attributes:
            if group['name'] == 'Data-in-transit protection':
                for row in group['rows']:
                    # string with bespoke assurance caveat
                    if row.label == 'Data protection between services':
                        self.assertEqual(
                            row.value, [u'No encryption']
                        )
                        self.assertEqual(
                            row.assurance, u'independent validation of assertion'
                        )
                    # string with standard assurance caveat
                    if row.label == 'Data protection within service':
                        self.assertEqual(
                            row.value,
                            [u'No encryption']
                        )

    def test_attributes_with_assurance_for_a_list_value_has_a_caveat(self):
        service = Service(self.fixture, content_loader.get_builder('g-cloud-6', 'display_service'))
        for group in service.attributes:
            if group['name'] == 'Asset protection and resilience':
                for row in group['rows']:
                    # list with bespoke assurance caveat
                    if row.label == 'Data management location':
                        self.assertIn(
                            u'independent validation of assertion',
                            row.assurance
                        )


class TestMeta(unittest.TestCase):
    def setUp(self):
        self.fixture = _get_fixture_data()['services']
        self.meta = Meta(self.fixture)

    def tearDown(self):
        pass

    def test_Meta_instance_has_the_correct_attributes(self):
        self.assertTrue(hasattr(self.meta, 'price'))
        self.assertTrue(hasattr(self.meta, 'priceCaveats'))
        self.assertTrue(hasattr(self.meta, 'documents'))
        self.assertTrue(hasattr(self.meta, 'serviceId'))
        self.assertTrue(hasattr(self.meta, 'contact'))
        self.assertIn('name', self.meta.contact)
        self.assertIn('phone', self.meta.contact)
        self.assertIn('email', self.meta.contact)

    def test_contact_information_is_correct(self):
        self.assertEqual(self.meta.contact['name'], 'Contact name')
        self.assertEqual(self.meta.contact['phone'], 'Contact number')
        self.assertEqual(self.meta.contact['email'], 'Contact email')

    def test_get_service_id_returns_the_correct_information(self):
        self.assertEqual(
            self.meta.get_service_id({'id': 1234567890123456}),
            ['1234', '5678', '9012', '3456']
        )
        self.assertEqual(
            self.meta.get_service_id({'id': '5-G4-1046-001'}),
            ['5-G4-1046-001']
        )

    def test_external_framework_url_returns_correct_suffix(self):
        self.assertEqual(
            self.meta.get_external_framework_url({'frameworkName': 'G-Cloud 7'}),
            'http://ccs-agreements.cabinetoffice.gov.uk/contracts/rm1557vii'
        )
        self.assertEqual(
            self.meta.get_external_framework_url({'frameworkName': 'G-Cloud 6'}),
            'http://ccs-agreements.cabinetoffice.gov.uk/contracts/rm1557vi'
        )
        self.assertEqual(
            self.meta.get_external_framework_url({'frameworkName': 'None'}),
            None
        )

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
            self.assertEqual(
                documents[idx]['name'],
                expected_information[idx]['name']
            )
            self.assertEqual(
                documents[idx]['url'],
                expected_information[idx]['url']
            )
            self.assertEqual(documents[idx]['extension'], 'pdf')

    def test_vat_status_is_correct(self):
        # if VAT is not included
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertIn('Excluding VAT', price_caveats)
        # if VAT is included
        self.fixture['vatIncluded'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertIn('Including VAT', price_caveats)

    def test_education_pricing_status_is_correct(self):
        # if Education pricing is included
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertIn('Education pricing available', price_caveats)
        # if Education pricing is excluded
        self.fixture['educationPricing'] = False
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertNotIn('Education pricing available', price_caveats)

    def test_termination_costs_status_is_correct(self):
        # if Termination costs are excluded
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertNotIn('Termination costs apply', price_caveats)
        # if Termination costs are included
        self.fixture['terminationCost'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertIn('Termination costs apply', price_caveats)
        # if the question wasn't asked
        del self.fixture['terminationCost']
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertNotIn('Termination costs apply', price_caveats)

    def test_minimum_contract_status_is_correct(self):
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertIn('Minimum contract period: Month', price_caveats)

    def test_options_are_correct_if_both_false(self):
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertNotIn('Trial and free options available', price_caveats)
        self.assertNotIn('Trial option available', price_caveats)
        self.assertNotIn('Free option available', price_caveats)

    def test_options_are_correct_if_free_is_false_and_trial_true(self):
        self.fixture['trialOption'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertNotIn('Trial and free options available', price_caveats)
        self.assertNotIn('Free option available', price_caveats)
        self.assertIn('Trial option available', price_caveats)

    def test_options_are_correct_if_free_is_true_and_trial_false(self):
        self.fixture['freeOption'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertNotIn('Trial and free options available', price_caveats)
        self.assertNotIn('Trial option available', price_caveats)
        self.assertIn('Free option available', price_caveats)

    def test_options_are_correct_if_free_is_true_and_trial_false(self):
        self.fixture['freeOption'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertNotIn('Trial and free options available', price_caveats)
        self.assertNotIn('Trial option available', price_caveats)
        self.assertIn('Free option available', price_caveats)

    def test_options_are_correct_if_both_are_not_set(self):
        del self.fixture['freeOption']
        del self.fixture['trialOption']
        price_caveats = self.meta.get_price_caveats(self.fixture)
        self.assertNotIn('Trial and free options available', price_caveats)
        self.assertNotIn('Trial option available', price_caveats)
        self.assertNotIn('Free option available', price_caveats)


class TestHelpers(unittest.TestCase):
    def test_normal_string_can_be_lowercased(self):
        self.assertEqual(
            lowercase_first_character_unless_part_of_acronym(
                "Independent validation of assertion"
            ),
            "independent validation of assertion"
        )

    def test_string_starting_with_acronym_can_be_lowercased(self):
        self.assertEqual(
            lowercase_first_character_unless_part_of_acronym(
                "CESG-assured components"
            ),
            "CESG-assured components"
        )
