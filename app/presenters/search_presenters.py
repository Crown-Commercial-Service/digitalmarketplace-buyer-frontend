from dmutils.formats import lot_to_lot_case
from ..helpers.search_helpers import get_filters_from_request


def sections_for_lot(lot, builder):
    if lot is None or lot == 'all':
        sections = builder.filter(
            {'lot': 'IaaS'}).filter(
            {'lot': 'PaaS'}).filter(
            {'lot': 'SaaS'}).filter(
            {'lot': 'SCS'}).sections
    else:
        sections = builder.filter({'lot': lot_to_lot_case(lot)}).sections

    return sections


def filters_for_lot(lot, builder):
    sections = sections_for_lot(lot, builder)
    lot_filters = []

    for section in sections:
        section_filter = {
            "label": section["name"],
            "filters": [],
        }
        for question in section["questions"]:
            section_filter["filters"].extend(
                filters_for_question(question)
            )

        lot_filters.append(section_filter)

    return lot_filters


def filters_for_question(question):
    question_filters = []
    if question['type'] == 'boolean':
        question_filters.append({
            'label': question['question'],
            'name': question['id'],
            'id': question['id'],
            'value': 'true',
        })

    elif question['type'] in ['checkboxes', 'radios']:
        for option in question['options']:
            question_filters.append({
                'label': option['label'],
                'name': question['id'],
                'id': '{}-{}'.format(
                    question['id'],
                    option['label'].lower().replace(' ', '-')),
                'value': option['label'].lower(),
            })

    return question_filters


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
