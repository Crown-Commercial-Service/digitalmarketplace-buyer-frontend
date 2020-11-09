import os
import json

import pytest

from app import content_loader
from app.main.helpers import framework_helpers
from app.main.presenters.service_presenters import (
    Service, Meta,
    chunk_string
)
from ...helpers import BaseApplicationTest


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


class TestService(BaseApplicationTest):
    def setup_method(self, method):
        super().setup_method(method)

        self.fixture = _get_fixture_data()
        self.fixture = self.fixture['services']
        self._lots_by_slug = framework_helpers.get_lots_by_slug(
            self._get_framework_fixture_data('g-cloud-6')['frameworks']
        )

        self.service = Service(
            self.fixture, content_loader.get_manifest('g-cloud-6', 'display_service'), self._lots_by_slug
        )

    def teardown_method(self, method):
        super().teardown_method(method)

    def test_title_attribute_is_set(self):
        assert self.service.title == self.fixture['serviceName']

    def test_lot_attribute_is_set(self):
        assert self.service.lot['slug'] == self.fixture['lot'].lower()

    def test_framework_attribute_is_set(self):
        assert self.service.frameworkName == self.fixture['frameworkName']

    def test_Service_works_if_supplierName_is_not_set(self):
        del self.fixture['supplierName']
        self.service = Service(self.fixture, content_loader.get_manifest('g-cloud-6', 'display_service'),
                               self._lots_by_slug)
        assert not hasattr(self.service, 'supplierName')

    def test_Service_works_if_serviceFeatures_is_not_set(self):
        del self.fixture['serviceFeatures']
        self.service = Service(self.fixture, content_loader.get_manifest('g-cloud-6', 'display_service'),
                               self._lots_by_slug)
        assert not hasattr(self.service, 'features')

    def test_Service_works_if_serviceBenefits_is_not_set(self):
        del self.fixture['serviceBenefits']
        self.service = Service(self.fixture, content_loader.get_manifest('g-cloud-6', 'display_service'),
                               self._lots_by_slug)
        assert not hasattr(self.service, 'benefits')

    def test_features_attributes_are_correctly_set(self):
        assert hasattr(self.service, 'features')
        assert len(self.service.features) == 6

    def test_benefits_attributes_are_correctly_set(self):
        assert hasattr(self.service, 'benefits')
        assert len(self.service.benefits) == 6

    @pytest.mark.parametrize('declaration, expected', [(None, {}), ({'foo': 'bar'}, {'foo': 'bar'})])
    def test_declaration_attribute_is_correctly_set_on_meta(self, declaration, expected):
        service = Service(
            self.fixture,
            content_loader.get_manifest('g-cloud-6', 'display_service'),
            self._lots_by_slug,
            declaration=declaration
        )
        assert hasattr(service.meta, 'declaration')
        assert service.meta.declaration == expected

    def test_service_properties_available_via_summary_manifest(self):
        service = Service(
            self.fixture,
            content_loader.get_manifest('g-cloud-6', 'display_service').filter({'lot': 'iaas'}),
            self._lots_by_slug
        )
        assert service.summary_manifest.sections[0].name == 'Support'
        assert len(service.summary_manifest.sections) == 30
        assert len(service.summary_manifest.sections[0].questions) == 5


class TestMeta:
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

    def test_get_documents_returns_the_correct_document_information(self):
        expected_information = [
            {
                'name': 'Pricing document',
                'url': (
                    'https://assets.digitalmarketplace.service.gov.uk/' +
                    'documents/123456/1234567890123456-pricing-document.pdf'
                )
            },
            {
                'name': 'Skills Framework for the Information Age rate card',
                'url': (
                    'https://assets.digitalmarketplace.service.gov.uk/' +
                    'documents/123456/1234567890123456-sfia-rate-card.pdf'
                )
            },
            {
                'name': 'Service definition document',
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

    @pytest.mark.parametrize("document_key", ['modernSlaveryStatement', 'modernSlaveryStatementOptional'])
    def test_get_documents_includes_declaration_documents(self, document_key):
        meta = Meta(
            self.fixture,
            declaration={
                document_key: "https://www.digitalmarketplace.service.gov.uk/suppliers/assets/not/a/real/path.pdf"
            }
        )
        documents = meta.get_documents(self.fixture)
        assert documents[4]['name'] == 'Modern Slavery statement'
        assert documents[4]['url'] == 'https://assets.digitalmarketplace.service.gov.uk/not/a/real/path.pdf'
        assert documents[4]['extension'] == 'pdf'

    def test_get_documents_raises_error_if_no_file_extension(self):
        bad_document_url = "https://assets.digitalmarketplace.service.gov.uk/documents/123456/noextension"
        service_missing_file_extension = self.fixture.copy()
        service_missing_file_extension["pricingDocumentURL"] = bad_document_url

        with pytest.raises(ValueError) as exc:
            self.meta.get_documents(service_missing_file_extension)

        assert str(exc.value) == "Missing file extension for document at URL {}".format(bad_document_url)

    def test_vat_status_is_correct(self):
        # if VAT is not included
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Excluding VAT' in [x['text'] for x in price_caveats]
        # if VAT is included
        self.fixture['vatIncluded'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Including VAT' in [x['text'] for x in price_caveats]

    def test_education_pricing_status_is_correct(self):
        # if Education pricing is included
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Education pricing available' in [x['text'] for x in price_caveats]
        # if Education pricing is excluded
        self.fixture['educationPricing'] = False
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Education pricing available' not in [x['text'] for x in price_caveats]

    def test_termination_costs_status_is_correct(self):
        # if Termination costs are excluded
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Termination costs apply' not in [x['text'] for x in price_caveats]
        # if Termination costs are included
        self.fixture['terminationCost'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Termination costs apply' in [x['text'] for x in price_caveats]
        # if the question wasn't asked
        del self.fixture['terminationCost']
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Termination costs apply' not in [x['text'] for x in price_caveats]

    def test_minimum_contract_status_is_correct(self):
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Minimum contract period: Month' in [x['text'] for x in price_caveats]

    def test_options_are_correct_if_both_false(self):
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Trial and free options available' not in [x['text'] for x in price_caveats]
        assert 'Trial option available' not in [x['text'] for x in price_caveats]
        assert 'Free option available' not in [x['text'] for x in price_caveats]

    def test_options_are_correct_if_free_is_false_and_trial_true(self):
        self.fixture['trialOption'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Trial and free options available' not in [x['text'] for x in price_caveats]
        assert 'Free option available' not in [x['text'] for x in price_caveats]
        assert 'Trial option available' in [x['text'] for x in price_caveats]

    def test_options_are_correct_if_free_is_true_and_trial_false(self):
        self.fixture['freeOption'] = True
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Trial and free options available' not in [x['text'] for x in price_caveats]
        assert 'Trial option available' not in [x['text'] for x in price_caveats]
        assert 'Free option available' in [x['text'] for x in price_caveats]

    def test_options_are_correct_if_both_are_not_set(self):
        del self.fixture['freeOption']
        del self.fixture['trialOption']
        price_caveats = self.meta.get_price_caveats(self.fixture)
        assert 'Trial and free options available' not in [x['text'] for x in price_caveats]
        assert 'Trial option available' not in [x['text'] for x in price_caveats]
        assert 'Free option available' not in [x['text'] for x in price_caveats]

    def test_caveats_for_free_trial(self):
        self.fixture['freeVersionTrialOption'] = True
        self.fixture['freeVersionLink'] = 'https://www.digitalmarketplace.service.gov.uk'
        price_caveats = self.meta.get_price_caveats(self.fixture)

        free_trial_caveat = list(filter(lambda x: x['text'] == 'Free trial available', price_caveats))
        assert len(free_trial_caveat) == 1
        assert free_trial_caveat[0]['link'] == 'https://www.digitalmarketplace.service.gov.uk'

    def test_caveat_links_must_be_valid_urls(self):
        self.fixture['freeVersionTrialOption'] = True
        self.fixture['freeVersionLink'] = 'www.gov.uk'
        price_caveats = self.meta.get_price_caveats(self.fixture)

        free_trial_caveat = list(filter(lambda x: x['text'] == 'Free trial available', price_caveats))
        assert len(free_trial_caveat) == 1
        assert 'link' not in free_trial_caveat[0]
