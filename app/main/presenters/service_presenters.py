import os
import re
from collections import OrderedDict
from urllib.parse import unquote, urlparse

from dmcontent.formats import format_service_price
from dmcontent.html import to_summary_list_rows

DECLARATION_DOCUMENT_KEYS = [
    ('modernSlaveryStatement', 'modernSlaveryStatementURL'),
    ('modernSlaveryStatementOptional', 'modernSlaveryStatementURL')
]
DOCUMENT_NAMES = OrderedDict([
    ('pricingDocumentURL', 'Pricing document'),
    ('sfiaRateDocumentURL', 'Skills Framework for the Information Age rate card'),
    ('serviceDefinitionDocumentURL', 'Service definition document'),
    ('termsAndConditionsDocumentURL', 'Terms and conditions'),
    ('modernSlaveryStatementURL', 'Modern Slavery statement')
])


def chunk_string(string, chunk_length):
    return (string[0 + i:chunk_length + i] for i in range(0, len(string), chunk_length))


class Service(object):
    def _add_as_attribute_if_key_exists(self, key, service_data):
        if key[0] in service_data:
            setattr(self, key[1], service_data[key[0]])

    def __init__(self, service_data, manifest, lots_by_slug, declaration=None):
        self.summary_manifest = manifest.summary(service_data)
        # get attributes in format suitable for govukSummaryList
        for section in self.summary_manifest:
            section.summary_list = to_summary_list_rows(section.questions, capitalize_first=True)
        # required attributes directly mapped to service_data values
        self.title = service_data['serviceName']
        self.serviceSummary = service_data.get('serviceSummary', service_data.get('serviceDescription'))
        self.lot = lots_by_slug.get(service_data['lot'])
        self.frameworkName = service_data['frameworkName']
        # optional attributes directly mapped to service_data values
        for key in [
            ('supplierName', 'supplierName'),
            ('serviceFeatures', 'features'),
            ('serviceBenefits', 'benefits')
        ]:
            self._add_as_attribute_if_key_exists(key, service_data)
        self.meta = self._get_service_meta(service_data, declaration)

    def _get_service_meta(self, service_data, declaration=None):
        return Meta(service_data, declaration)


class Meta(object):
    def __init__(self, service_data, declaration=None):
        self.price = format_service_price(service_data)
        self.contact = {
            'name': 'Contact name',
            'phone': 'Contact number',
            'email': 'Contact email'
        }
        self.priceCaveats = self.get_price_caveats(service_data)
        self.serviceId = self.get_service_id(service_data)
        self.declaration = declaration or {}
        self.documents = self.get_documents(service_data)

    def set_contact_attribute(self, contactName, phone, email):
        self.contact = {
            'name': contactName,
            'phone': phone,
            'email': email
        }

    def get_service_id(self, service_data):
        id = service_data['id']
        if re.findall("[a-zA-Z]", str(id)):
            return [id]
        else:
            return list(chunk_string(str(id), 4))

    def _add_declaration_documents_to_service_data(self, service_data):
        # Check if the supplier has provided a declaration document, and add it to the service data.
        # The Service presenter will add it to the other documents ready for display
        for document_key, target_key in DECLARATION_DOCUMENT_KEYS:
            if document_key in self.declaration:
                supplier_document_url = self.declaration[document_key]
                # Convert supplier-facing url to public assets domain
                # TODO: change declaration upload functionality to store it on assets.* in the first place?
                public_document_url = supplier_document_url.replace(
                    'https://www.digitalmarketplace.service.gov.uk/suppliers/assets',
                    'https://assets.digitalmarketplace.service.gov.uk'
                )
                service_data[target_key] = public_document_url

    def get_documents(self, service_data):
        self._add_declaration_documents_to_service_data(service_data)

        documents = []
        for url_key, document_name in DOCUMENT_NAMES.items():
            if url_key in service_data:
                url = service_data[url_key]
                extension = self._get_document_extension(url)
                documents.append({
                    'name': DOCUMENT_NAMES[url_key],
                    'url': url,
                    'extension': extension
                })

        # get additional documents, if they exist (not used since G-Cloud 5)
        if 'additionalDocumentURLs' in service_data:
            for index, url in enumerate(service_data['additionalDocumentURLs'], 1):
                extension = self._get_document_extension(url)
                name = self._get_pretty_document_name_without_extension(url)
                documents.append({
                    'name': name,
                    'url': url,
                    'extension': extension
                })

        return documents

    def get_price_caveats(self, service_data):
        def make_caveat(text, link=None):
            return {'text': text, 'link': link} if link else {'text': text}

        caveats = []
        main_caveats = [
            {
                'key': 'educationPricing',
                'if_exists': 'Education pricing available',
                'if_absent': False
            }
        ]
        g8_and_earlier_caveats = [
            {
                'key': 'vatIncluded',
                'if_exists': 'Including VAT',
                'if_absent': 'Excluding VAT'
            },
            {
                'key': 'terminationCost',
                'if_exists': 'Termination costs apply',
                'if_absent': False
            }
        ]

        if 'minimumContractPeriod' in service_data:
            # G-Cloud 8 and earlier
            caveats.append(make_caveat('Minimum contract period: {}'.format(service_data['minimumContractPeriod'])))

        if service_data.get('freeVersionTrialOption') is True:
            options = make_caveat('Free trial available', service_data.get('freeVersionLink'))

        else:
            # G-Cloud 8 and earlier
            options = self._if_both_keys_or_either(
                service_data,
                keys=['trialOption', 'freeOption'],
                values={
                    'if_both': 'Trial and free options available',
                    'if_first': 'Trial option available',
                    'if_second': 'Free option available',
                    'if_neither': False
                }
            )
            options = make_caveat(options) if options else options

        for item in main_caveats + g8_and_earlier_caveats:
            # 'vatIncluded' and 'terminationCost' only displayed for services on G8 and earlier
            if item['key'] in service_data:
                if service_data[item['key']]:
                    caveats.append(make_caveat(item['if_exists']))
                else:
                    if item['if_absent']:
                        caveats.append(make_caveat(item['if_absent']))

        if options:
            caveats.append(options)

        return caveats

    def _get_pretty_document_name_without_extension(self, document_url):
        document_basename = os.path.basename(urlparse(document_url.replace(';', '%3B')).path)
        filename = unquote(os.path.splitext(document_basename)[0])
        return filename.replace('_', ' ')

    def _get_document_extension(self, document_url):
        url_object = urlparse(document_url.replace(';', '%3B'))
        try:
            return os.path.splitext(url_object.path)[1].split('.')[1]
        except IndexError:
            raise ValueError("Missing file extension for document at URL {}".format(document_url))

    def _if_both_keys_or_either(self, service_data, keys=[], values={}):
        def is_not_false(key):
            if (key in service_data) and (service_data[key] is True):
                return True
            else:
                return False

        if is_not_false(keys[0]) and is_not_false(keys[1]):
            caveat = values['if_both']
        elif is_not_false(keys[0]):
            caveat = values['if_first']
        elif is_not_false(keys[1]):
            caveat = values['if_second']
        else:  # neither is set or True
            caveat = values['if_neither']
        return caveat

    def _if_key_exists_else(self, service_data, key='', values={}):
        if hasattr(service_data, key):
            return values['if_exists']
        else:
            return values['if_absent']
