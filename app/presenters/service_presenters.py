import os
import re
from .data.service_data import mappings
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote


class Service(object):
    def _add_as_attribute_if_key_exists(self, key, service_data):
        if key[0] in service_data:
            setattr(self, key[1], service_data[key[0]])

    def __init__(self, service):
        service_data = service['services']
        # required attributes directly mapped to service_data values
        self.title = service_data['serviceName']
        self.serviceSummary = service_data['serviceSummary']
        self.lot = service_data['lot']
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
        attribute_groups = []
        for group in mappings:
            attribute_group = {
                'name': group['name'],
                'rows': self._get_rows(group['rows'], service_data)
            }
            if len(attribute_group['rows']) > 0:
                attribute_groups.append(attribute_group)

        return attribute_groups

    def _get_service_meta(self, service_data):
        return Meta(service_data)

    def _get_rows(self, group, service_data):
        rows = []

        for row in group:
            try:
                attribute = Attribute(row['value'], service_data)
            except KeyError:
                continue
            data_value = attribute.get_data_value()
            data_type = attribute.get_data_type(data_value)
            if data_type is not False and \
                    attribute.is_empty_certifications_field() is False:
                    current_row = {
                        'key': row['key'],
                        'value': data_value,
                        'type': data_type
                    }
                    if hasattr(attribute, 'assurance'):
                        current_row = attribute.add_assurance_to_row(
                            attribute.assurance,
                            current_row
                        )

                    rows.append(current_row)

        return rows


class Attribute(object):
    """Wrapper to handle accessing an attribute in service_data"""

    def __init__(self, key, service_data):
        """Returns if the attribute key points to a row in the service data"""
        self.key = key
        self.service_data = service_data
        self.key_type = self.get_data_type(key)
        if self._key_maps_to_data() is False:
            raise KeyError("Attribute key not found in service data")
        else:
            self._set_assurance()

    def get_data_type(self, value):
        """Gets the type of the value parameter"""
        if self._is_string(value):
            return 'string'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, list):
            return 'list'
        elif self._is_function(value):
            return 'function'
        elif isinstance(value, dict):
            return 'dictionary'
        else:
            return False

    def get_data_value(self):
        """Get the value for the attribute key in the service data"""
        if hasattr(self, 'data_value') is False:
            if self.key_type is 'function':
                data_value = self.key(self.service_data)
            else:
                data_value = self.service_data[self.key]
            self.data_value = self.format(data_value)
            self.data_type = self.get_data_type(data_value)
        return self.data_value

    def format(self, value):
        """Formats the value parameter based on its type"""
        value_format = self.get_data_type(value)
        if value_format is 'boolean':
            if value:
                return u'Yes'
            else:
                return u'No'
        elif (value_format is 'list') and (len(value) == 0):
            return ''
        elif (value_format is 'list') and (len(value) == 1):
            return self.format(value[0])
        else:
            return value

    def add_assurance_to_row(self, assurance, row_object):
        if row_object['type'] == 'list':
            row_object = self._add_assurance_to_list(row_object)
            return row_object
        else:
            row_object = self._add_assurance_to_string(row_object)
            return row_object

    def is_empty_certifications_field(self):
        if self.key != 'vendorCertifications':
            return False

        value = self.service_data[self.key]
        if len(value) == 0:
            return True
        else:
            return False

    def _add_assurance_to_list(self, row_object):
        if self.assurance != 'Service provider assertion':
            row_object['assuranceCaveat'] = (
                u'Assured by %s' % self.assurance.lower()
            )
        return row_object

    def _add_assurance_to_string(self, row_object):
        if self.assurance != 'Service provider assertion':
            row_object['value'] = u'%s, assured by %s' % (
                row_object['value'],
                self.assurance.lower()
            )
        return row_object

    def _set_assurance(self):
        data_value = self.get_data_value()
        if 'assurance' in data_value:
            self.assurance = data_value['assurance']
            self.data_value = self.format(data_value['value'])
            self.data_type = self.get_data_type(self.data_value)

    def _is_string(self, var):
        try:
            return isinstance(var, basestring)
        except NameError:
            return isinstance(var, str)

    def _is_function(self, var):
        return hasattr(var, '__call__')

    def _key_maps_to_data(self):
        if self.get_data_type(self.key) is 'function':
            return self.key(self.service_data) is not False
        else:
            return self.key in self.service_data


class Meta(object):
    def __init__(self, service_data):
        self.price = service_data['priceString']
        self.contact = {
            'name': 'Contact name',
            'phone': 'Contact number',
            'email': 'Contact email'
        }
        self.priceCaveats = self.get_price_caveats(service_data)
        self.serviceId = self.get_service_id(service_data)
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
            return re.findall("....", str(id))

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
        minimum_contract_str = (
            (
                'Minimum contract period: %s'
                %
                service_data['minimumContractPeriod']
            )
        )
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
            },
            {
                'key': 'minimumContractPeriod',
                'if_exists': minimum_contract_str,
                'if_absent': False
            }
        ]
        caveats = []
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
        document_basename = os.path.basename(urlparse(document_url).path)
        filename = unquote(os.path.splitext(document_basename)[0])
        return filename.replace('_', ' ')

    def _get_document_extension(self, document_url):
        url_object = urlparse(document_url)
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
