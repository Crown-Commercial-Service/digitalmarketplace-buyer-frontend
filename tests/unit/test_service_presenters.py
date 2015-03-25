import os
import json
import unittest
from app.presenters.service_presenters import Service, Attribute, Meta


def _get_fixture_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'service_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


class TestService(unittest.TestCase):

    def setUp(self):
        self.fixture = _get_fixture_data()['services']
        self.service = Service(self.fixture)

    def tearDown(self):
        pass

    def test_title_attribute_is_set(self):
        self.assertEquals(self.service.title, self.fixture['serviceName'])

    def test_supplierName_attribute_is_set(self):
        self.assertEquals(
            self.service.supplierName, self.fixture['supplierName']
        )

    def test_features_attributes_are_correctly_set(self):
        self.assertEquals(len(self.service.features), 6)

    def test_benefits_attributes_are_correctly_set(self):
        self.assertEquals(len(self.service.benefits), 6)

    def test_attributes_are_correctly_set(self):
        self.maxDiff = None
        self.assertEquals(self.service.attributes[0], {
            'name': u'Support',
            'rows': [
                {
                    'key': u'Support service type',
                    'type': 'list',
                    'value': [
                        u'Service desk',
                        u'Email',
                        u'Phone'
                    ]
                },
                {
                    'key': u'Support accessible to any third-party suppliers',
                    'type': 'string',
                    'value': u'Yes'
                },
                {
                    'key': u'Support availablility',
                    'type': 'string',
                    'value': u'24/7, 365 days a year'
                },
                {
                    'key': u'Standard support response times',
                    'type': 'string',
                    'value': (
                        u'Normally 1 hour as standard, up to a maximum of 4 ' +
                        u'hours'
                    )
                },
                {
                    'key': u'Incident escalation process available',
                    'type': 'string',
                    'value': u'Yes'
                }
            ]
        })

    def test_the_support_attribute_group_is_not_there_if_no_attributes(self):
        del self.fixture['openStandardsSupported']
        service = Service(self.fixture)
        for group in service.attributes:
            if group['name'] == 'Open standards':
                self.fail("Support group should not be found")

    def test_only_attributes_with_a_valid_type_are_added_to_groups(self):
        invalidValue = (u'Manuals provided', u'CMS training')
        self.fixture['onboardingGuidance'] = invalidValue
        service = Service(self.fixture)
        for group in service.attributes:
            if (
                (group['name'] == 'External interface protection')
                and
                ('onboardingGuidance' in group)
            ):
                self.fail("Attribute with tuple value should not be in group")

    def test_attributes_are_given_the_correct_type(self):
        service = Service(self.fixture)
        for group in service.attributes:
            if group['name'] == 'Support':
                for row in group['rows']:
                    if row['key'] == 'supportTypes':
                        self.assertEqual(row['type'], 'list')
                    if row['key'] == 'supportForThirdParties':
                        self.assertEqual(row['type'], 'boolean')
                    if row['key'] == 'supportAvailability':
                        self.assertEqual(row['type'], 'string')
            elif group['name'] == 'Secure service administration':
                for row in group['rows']:
                    if row['key'] == 'serviceManagementModel':
                        self.assertEqual(row['type'], 'dictonary')

    def test_attributes_with_assurance_in_the_fields_add_it_correctly(self):
        service = Service(self.fixture)
        for group in service.attributes:
            if group['name'] == 'Data-in-transit protection':
                for row in group['rows']:
                    # string with bespoke assurance caveat
                    if row['key'] == 'Data protection between services':
                        self.assertEqual(
                            row['value'],
                            (
                                u'No encryption, assured by ' +
                                u'independent validation of assertion'
                            )
                        )
                    # string with standard assurance caveat
                    if row['key'] == 'Data protection within service':
                        self.assertEqual(
                            row['value'],
                            u'No encryption'
                        )

    def test_attributes_with_assurance_for_a_list_value_has_a_caveat(self):
        service = Service(self.fixture)
        for group in service.attributes:
            if group['name'] == 'Asset protection and resilience':
                for row in group['rows']:
                    # list with bespoke assurance caveat
                    if row['key'] == 'Data management location':
                        self.assertEqual(
                            row['assuranceCaveat'],
                            u'Assured by independent validation of assertion'
                        )
                    # list with standard assurance caveat
                    if row['key'] == 'Data management location':
                        self.assertIn('assuranceCaveat', row)


class TestAttribute(unittest.TestCase):
    def setUp(self):
        self.fixture = _get_fixture_data()['services']

    def tearDown(self):
        pass

    def test_Attribute_works_if_the_key_is_in_service_data(self):
        try:
            attribute = Attribute('supportAvailability', self.fixture)
        except KeyError:
            self.fail("'supportAvailability' key should be in service data")

    def test_Attribute_fails_if_the_key_isnt_in_service_data(self):
        key_error_raised = False
        try:
            attribute = Attribute('downtime', self.fixture)
        except KeyError:
            key_error_raised = True
        self.assertTrue(key_error_raised)

    def test_Attribute_fails_if_key_is_a_function_that_returns_false(self):
        key_error_raised = False

        def func(service_data):
            return False

        try:
            attribute = Attribute(func, self.fixture)
        except KeyError:
            key_error_raised = True
        self.assertTrue(key_error_raised)

    def test_Attribute_fails_if_key_is_a_function_that_returns_a_value(self):
        key_error_raised = False

        def func(service_data):
            return {
                'value': 'No',
                'assurance': 'Service provider assertion'
            }

        try:
            attribute = Attribute(func, self.fixture)
        except KeyError:
            key_error_raised = True
        self.assertFalse(key_error_raised)

    def test_get_data_value_retrieves_correct_value(self):
        attribute = Attribute('supportAvailability', self.fixture)
        self.assertEqual(
            attribute.get_data_value(),
            '24/7, 365 days a year'
        )

    def test_get_data_type_recognises_strings(self):
        attribute = Attribute('supportAvailability', self.fixture)
        self.assertEqual(
            attribute.get_data_type('24x7x365 with UK based engineers'),
            'string'
        )

    def test_get_data_type_recognises_floats(self):
        attribute = Attribute('supportAvailability', self.fixture)
        self.assertEqual(
            attribute.get_data_type(99.99),
            'float'
        )

    def test_get_data_type_recognises_integer(self):
        attribute = Attribute('supportAvailability', self.fixture)
        self.assertEqual(
            attribute.get_data_type(99),
            'integer'
        )

    def test_get_data_type_recognises_unicode_strings(self):
        attribute = Attribute('supportAvailability', self.fixture)
        self.assertEqual(
            attribute.get_data_type(u'24x7x365 with UK based engineers'),
            'string'
        )

    def test_get_data_type_recognises_lists(self):
        attribute = Attribute('supportAvailability', self.fixture)
        self.assertEqual(
            attribute.get_data_type([1, 2]),
            'list'
        )

    def test_get_data_type_recognises_functions(self):
        attribute = Attribute('supportAvailability', self.fixture)

        def _func():
            pass

        self.assertEqual(
            attribute.get_data_type(_func),
            'function'
        )

    def test_get_data_type_recognises_booleans(self):
        attribute = Attribute('supportAvailability', self.fixture)
        self.assertEqual(
            attribute.get_data_type(True),
            'boolean'
        )

    def test_get_data_type_recognises_dictionaries(self):
        attribute = Attribute('supportAvailability', self.fixture)
        dictionary = {
            "assurance": "Service provider assertion",
            "value": True
        }
        self.assertEqual(attribute.get_data_type(dictionary), 'dictionary')

    def test_get_data_type_returns_false_for_unrecognised_type(self):
        attribute = Attribute('supportAvailability', self.fixture)
        self.assertFalse(attribute.get_data_type(('name', 'address')))

    def test_format_returns_yes_for_true_boolean(self):
        attribute = Attribute('supportAvailability', self.fixture)
        self.assertEqual(attribute.format(True), 'Yes')

    def test_format_returns_no_for_true_boolean(self):
        attribute = Attribute('supportAvailability', self.fixture)
        self.assertEqual(attribute.format(False), 'No')

    def test_format_returns_empty_string_for_a_empty_list(self):
        # The service API returns empty lists as [ "None" ]
        attribute = Attribute('vendorCertifications', self.fixture)
        self.assertEqual(attribute.format([]), "")

    def test_format_returns_the_first_item_for_a_list_with_one_item(self):
        # The service API returns empty lists as [ "None" ]
        attribute = Attribute('vendorCertifications', self.fixture)
        self.assertEqual(attribute.format(["None"]), "None")


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
