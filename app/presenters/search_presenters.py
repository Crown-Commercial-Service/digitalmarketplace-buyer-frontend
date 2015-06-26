from werkzeug.datastructures import MultiDict
from dmutils.formats import lot_to_lot_case


def filters_for_lot(lot, builder):

    filters = []
    if lot == 'all':
        sections = builder.filter(
            {'lot': 'IaaS'}).filter(
            {'lot': 'PaaS'}).filter(
            {'lot': 'SaaS'}).filter(
            {'lot': 'SCS'}).sections
    else:
        sections = builder.filter({'lot': lot_to_lot_case(lot)}).sections

    for section in sections:
        filter = {
            "label": section["name"],
            "filters": [],
        }
        for question in section["questions"]:
            if question['type'] == 'boolean':
                actual_filter = {
                    'label': question['question'],
                    'name': question['id'],
                    'id': question['id'],
                    'value': 'true',
                }
                filter["filters"].append(actual_filter)

            if question['type'] in ['checkboxes', 'radios']:
                for option in question['options']:
                    actual_filter = {
                        'label': option['label'],
                        'name': question['id'],
                        'id': option['label'].lower(),
                        'value': option['label'].lower(),
                    }
                    filter["filters"].append(actual_filter)

        filters.append(filter)

    return filters


def get_current_lot(request):
    return request.args.get('lot', None)


def get_filters_from_request(request):
    """Returns the filters applied to a search from the request object"""

    filters = MultiDict(request.args.copy())
    filters.poplist('q')
    filters.poplist('lot')
    return filters


def set_filter_states(filter_groups, request):
    """Sets a flag on each filter to mark it as set or not"""
    request_filters = get_filters_from_request(request)

    for filter_group in filter_groups:
        for filter in filter_group['filters']:
            filter['checked'] = False
            param_values = request_filters.getlist(
                filter['name'],
                type=str
            )
            if len(param_values) > 0:
                filter['checked'] = (
                    filter['value'] in param_values
                )
