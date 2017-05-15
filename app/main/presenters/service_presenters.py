import os
import re

from app import content_loader
from dmutils.service_attribute import Attribute
from dmcontent.errors import ContentNotFoundError
from dmcontent.formats import format_service_price
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote


def chunk_string(string, chunk_length):
    return (string[0+i:chunk_length+i] for i in range(0, len(string), chunk_length))


class Service(object):
    def _add_as_attribute_if_key_exists(self, key, service_data):
        if key[0] in service_data:
            setattr(self, key[1], service_data[key[0]])

    def __init__(self, service_data, service_questions, lots_by_slug):
        self.service_questions = service_questions
        # required attributes directly mapped to service_data values
        self.title = service_data['serviceName']
        self.serviceSummary = service_data['serviceSummary']\
            if 'serviceSummary' in service_data else \
            service_data['serviceDescription']
        self.lot = lots_by_slug.get(service_data['lot'])
        self.frameworkName = service_data['frameworkName']
        # optional attributes directly mapped to service_data values
        for key in [
            ('supplierName', 'supplierName'),
            ('serviceFeatures', 'features'),
            ('serviceBenefits', 'benefits')
        ]:
            self._add_as_attribute_if_key_exists(key, service_data)
        self.attributes = self._get_service_attributes(service_data)
        self.meta = self._get_service_meta(service_data)

    def _get_service_attributes(self, service_data):
        sections = map(
            lambda section: {
                'name': section['name'],
                'rows': self._get_rows(section, service_data)
            },
            self.service_questions
        )
        return list(filter(
            lambda section: len(list(section['rows'])) > 0,
            list(sections)
        ))

    def _get_service_meta(self, service_data):
        return Meta(service_data)

    def _get_rows(self, section, service_data):
        return list(filter(
            not_empty, map(
                lambda question: Attribute(
                    value=question.get('value', service_data.get(question['id'], None)),
                    question_type=question['type'],
                    label=question['question']
                ),
                section['questions']
            )
        ))


class Meta(object):
    def __init__(self, service_data):
        self.price = format_service_price(service_data)
        self.contact = {
            'name': 'Contact name',
            'phone': 'Contact number',
            'email': 'Contact email'
        }
        self.priceCaveats = self.get_price_caveats(service_data)
        self.serviceId = self.get_service_id(service_data)
        self.documents = self.get_documents(service_data)
        self.externalFrameworkUrl = self.get_external_framework_url(service_data)

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

    def get_external_framework_url(self, service_data):
        try:
            content_loader.load_messages(service_data['frameworkSlug'], ['urls'])
            return content_loader.get_message(
                service_data['frameworkSlug'],
                'urls',
                'framework_url'
            ) or None
        except ContentNotFoundError as e:
            # If no urls.yml exists then we don't have a URL for the framework
            return None

    def get_documents(self, service_data):
        url_keys = [
            'pricingDocumentURL',
            'sfiaRateDocumentURL',
            'serviceDefinitionDocumentURL',
            'termsAndConditionsDocumentURL'
        ]
        names = [
            'Pricing',
            'SFIA rate card',
            'Service definition',
            'Terms and conditions'
        ]
        documents = []
        for index, url_key in enumerate(url_keys):
            if url_key in service_data:
                url = service_data[url_key]
                extension = self._get_document_extension(url)
                documents.append({
                    'name':  names[index],
                    'url': url,
                    'extension': extension
                })

        # get additional documents, if they exist
        if 'additionalDocumentURLs' in service_data:
            for index, url in enumerate(service_data['additionalDocumentURLs'], 1):
                extension = self._get_document_extension(url)
                name = self._get_pretty_document_name_without_extension(url)
                documents.append({
                    'name':  name,
                    'url': url,
                    'extension': extension
                })

        return documents

    def get_price_caveats(self, service_data):
        caveats = []
        main_caveats = [
            {
                'key': 'vatIncluded',
                'if_exists': 'Including VAT',
                'if_absent': 'Excluding VAT'
            },
            {
                'key': 'educationPricing',
                'if_exists': 'Education pricing available',
                'if_absent':  False
            },
            {
                'key': 'terminationCost',
                'if_exists': 'Termination costs apply',
                'if_absent': False
            }
        ]

        if 'minimumContractPeriod' in service_data:
            caveats.append('Minimum contract period: {}'.format(service_data['minimumContractPeriod']))

        if 'freeVersionTrialOption' in service_data:
            options = 'Free trial option available'
        else:
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
        for item in main_caveats:
            if item['key'] in service_data:
                if service_data[item['key']]:
                    caveats.append(item['if_exists'])
                else:
                    if item['if_absent']:
                        caveats.append(item['if_absent'])

        if options:
            caveats.append(options)
        return caveats

    def _get_pretty_document_name_without_extension(self, document_url):
        document_basename = os.path.basename(urlparse(document_url.replace(';', '%3B')).path)
        filename = unquote(os.path.splitext(document_basename)[0])
        return filename.replace('_', ' ')

    def _get_document_extension(self, document_url):
        url_object = urlparse(document_url.replace(';', '%3B'))
        return os.path.splitext(url_object.path)[1].split('.')[1]

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


def lowercase_first_character_unless_part_of_acronym(string):
    if not string:
        return ''
    if string[1:2] == string[1:2].upper():
        return string
    return string[:1].lower() + string[1:]


def not_empty(item):
    return item.value is not ''
