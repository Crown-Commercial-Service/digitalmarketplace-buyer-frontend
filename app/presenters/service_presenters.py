import os
import re
from .data.service_data import mappings
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class Service(object):
    def __init__(self, service_data):
        self.attributes = self.set_service_attributes(service_data)
        self.service_info = self.set_service_info(service_data)
        self.features = self.set_service_features(service_data)
        self.benefits = self.set_service_benefits(service_data)
        self.meta = self.set_service_meta(service_data)

    def set_service_attributes(self, service_data):
        attribute_groups = []
        for group in mappings:
            attribute_group = {
                'name': group['name'],
                'rows': self._get_rows(group['rows'], service_data)
            }
            if len(attribute_group['rows']) > 0:
                attribute_groups.append(attribute_group)

        return attribute_groups

    def get_service_attributes(self):
        return self.attributes

    def set_service_info(self, service_data):
        return {
            'supplierName': service_data['supplierName'],
            'serviceSummary': service_data['serviceSummary']
        }

    def get_service_info(self):
        return self.service_info

    def set_service_features(self, service_data):
        return service_data['serviceFeatures']

    def get_service_features(self):
        return self.features

    def set_service_benefits(self, service_data):
        return service_data['serviceBenefits']

    def get_service_benefits(self):
        return self.benefits

    def set_service_meta(self, service_data):
        return Meta(service_data)

    def get_service_meta(self):
        return self.meta.get_all()
        
    def _get_rows(self, group, service_data):
        rows = []
        Attribute.set_service_data(service_data)

        for row in group:
            try:
                attribute = Attribute(row['value'])
            except KeyError:
                continue
            data_value = attribute.get_data_value()
            current_row = {
                'key': row['key'],
                'value': data_value,
                'type': attribute.get_data_type(data_value)
            }

            rows.append(current_row)

        return rows

class Attribute(object):
    @staticmethod
    def set_service_data(service_data):
        Attribute.service_data = service_data

    def __init__(self, key):
        """Returns if the attribute key points to a row in the service data"""
        self.key = key
        self.key_type = self.get_data_type(key)
        if self.__key_maps_to_data() == False:
            raise KeyError("Attribute key not found in service data")

    def get_data_type(self, value):
        """Gets the type of the value parameter"""
        value_type = type(value)
        if value_type == str:
            return 'string'
        elif value_type == list:
            return 'list'
        elif self._is_function(value):
            return 'function'
        elif value_type == bool:
            return 'boolean'
        elif value_type == dict:
            return 'dictionary'
        else:
            return False

    def get_data_value(self):
        """Get the value for the attribute key in the service data"""
        if hasattr(self, 'data_value') == False:
            if self.key_type == 'function':
                data_value = self.key(Attribute.service_data)
            else: 
                data_value = Attribute.service_data[self.key]
            self.data_type = self.get_data_type(data_value)
            self.data_value = self.format(data_value)
        return self.data_value

    def format(self, value):
        """Formats the value parameter based on its type"""
        value_format = self.get_data_type(value)
        if value_format == 'boolean':
            if value:
                return 'Yes'
            else:
                return 'No'
        elif value_format == 'dictionary':
            return self.format(value['value'])
        else:
            return value
        
    def _is_function(self, function):
        return hasattr(function, '__call__')

    def __key_maps_to_data(self):
        if self.get_data_type(self.key) == 'function':
            return (self.key(Attribute.service_data) != False)
        else:
            return Attribute.service_data.has_key(self.key)


class Meta(object):
    def __init__(self, service_data):
        self.price = service_data['priceString']
        self.contact = {
            'name': 'Contact name',
            'phone': 'Contact number',
            'email': 'Contact email'
        }
        self.price_caveats = self.set_price_caveats(service_data)
        self.service_id = self.set_service_id(service_data)
        self.documents = self.set_documents(service_data)

    def get_all(self):
        return {
            'price': self.price,
            'priceCaveats': self.price_caveats,
            'documents': self.documents,
            'serviceId': self.service_id,
            'contact': self.contact
        }


    def get_service_id(self):
        return self.service_id


    def set_service_id(self, service_data):
        return re.findall(
            '....', str(service_data['id'])
        )


    def get_documents(self):
        return self.documents


    def set_documents(self, service_data):
        keys = [
            'pricingDocument',
            'sfiaRateDocument',
            'serviceDefinitionDocument',
            'termsAndConditionsDocument'
        ]
        documents = []
        for key in keys:
            document_name = key
            document_url = key + 'URL'
            if document_name in service_data:
                documents.append({
                    'name':  service_data[document_name],
                    'url': service_data[document_url],
                    'extension': self._get_document_extension(service_data[document_url])
                })
        return documents


    def get_price_caveats(self):
        return self.price_caveats


    def set_price_caveats(self, service_data):
        minimum_contract_str = (
            'Minimum contract period: %s' % service_data['minimumContractPeriod']
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
        options = self._if_both_keys_or_either(service_data,
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


    def _get_document_extension(self, document_url):
        url_object = urlparse(document_url)
        return os.path.splitext(url_object.path)[1]


    def _if_both_keys_or_either(self, service_data, keys=[], values={}):
        caveat = ''
        if (service_data[keys[0]] == True) and (service_data[keys[1]] == True):
            caveat = values['if_both']
        elif (service_data[keys[0]] == True):
            caveat = values['if_first']
        elif (service_data[keys[1]] == True):
            caveat = values['if_second']
        else:
            caveat = values['if_neither']
        return caveat


    def _if_key_exists_else(self, service_data, key='', values={}):
        if hasattr(service_data, key):
            return values['if_exists']
        else:
            return values['if_absent']
