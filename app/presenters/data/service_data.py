def _service_availability(service):
    result = {}
    if 'serviceAvailabilityPercentage' in service:
        return {
            'value': (
                str(service['serviceAvailabilityPercentage']['value']) + '%'
            ),
            'assurance': service['serviceAvailabilityPercentage']['assurance']
        }
    else:
        return False
