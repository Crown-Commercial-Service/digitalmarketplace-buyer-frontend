from .data.service_data import mappings


class Service(object):
    def __init__(self, service_data):
        self.attributes = self.set_service_attributes(service_data)
        self.service_info = self.set_service_info(service_data)
        self.features = self.set_service_features(service_data)
        self.benefits = self.set_service_benefits(service_data)

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

