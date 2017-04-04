from collections import OrderedDict

from flask import url_for

from ..helpers.search_helpers import (
    get_filters_from_request,
    get_lot_from_request,
    get_keywords_from_request,
)


def sections_for_lot(lot, builder):
    if lot is None or lot == 'all':
        sections = builder.filter(
            {'lot': 'iaas'}).filter(
            {'lot': 'paas'}).filter(
            {'lot': 'saas'}).filter(
            {'lot': 'scs'}).sections
    else:
        sections = builder.filter({'lot': lot}).sections

    return sections


def filters_for_lot(lot, builder):
    sections = sections_for_lot(lot, builder)
    lot_filters = OrderedDict()

    for section in sections:
        section_filter = {
            "label": section["name"],
            "filters": [],
        }
        for question in section["questions"]:
            section_filter["filters"].extend(
                filters_for_question(question)
            )

        lot_filters[section.slug] = section_filter

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

    elif question['type'] in ['checkboxes', 'radios', 'checkbox_tree']:
        _recursive_add_option_filters(question, question['options'], question_filters)

    return question_filters


def _recursive_add_option_filters(question, options_list, filters_list):
    for option in options_list:
        presented_filter = {
            'label': option['label'],
            'name': question['id'],
            'id': '{}-{}'.format(
                question['id'],
                option['label'].lower().replace(' ', '-')),
            'value': option['label'].lower(),
        }
        if option.get('options'):
            presented_filter['children'] = []
            _recursive_add_option_filters(question, option.get('options', []), presented_filter['children'])

        filters_list.append(presented_filter)


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


def show_lots_and_categories_selection(lots, category_filter_group, request):
    """
    Equivalent of set_filter_states but for where we are creating a tree of links i.e. the
    lots/categories widget. Adds links (where necessary) and shows the currently-selected
    lot and/or categories.
    """
    current_lot_slug = get_lot_from_request(request)

    for lot in lots:
        lot_selected = (lot['slug'] == current_lot_slug)
        if lot_selected:
            lot['selected'] = True
            categories = category_filter_group['filters'] if category_filter_group else []
            category_was_selected = _show_category_selection(lot, categories, request)
            lot['categories'] = categories

        if not lot_selected or category_was_selected:
            # we need a link back to the lot _without_ a category selected
            lot['link'] = url_for('.search_services', q=get_keywords_from_request(request), lot=lot['slug'])


def _show_category_selection(lot, category_filters, request):
    """
    Recursive setting of 'selected' state and adding of links to categories
    as part of building the lots/categories tree.
    :param category_filters: set of category filters as previously produced by filters_for_question
    :param request: request object from which to extract active filters
    :return: True iff a category from the list was selected
    """
    request_filters = get_filters_from_request(request)
    any_category_selected = False
    any_descendant_selected = False

    for category in category_filters:
        category['selected'] = False
        param_values = request_filters.getlist(
            category['name'],
            type=str
        )
        directly_selected = (category['value'] in param_values)
        any_child_selected = _show_category_selection(lot, category.get('children', []), request)
        if directly_selected or any_child_selected:
            any_category_selected = True
            category['selected'] = True
        if any_child_selected:
            any_descendant_selected = True

        # As with lots, we want a link to the category - but not if the category is directly selected.
        # If we're showing it as 'selected' because one of its children is selected, then the link is
        # useful as a kind of breadcrumb, to return to showing all services in that overall category.
        if not directly_selected:
            # The argument in the URL must reflect the 'name' of the filter (i.e. the particular question
            # name it was derived from - 'serviceTypes' for G7/G8, 'serviceCategories' for G9.
            url_args = {category['name']: category['value']}

            category['link'] = url_for('.search_services',
                                       q=get_keywords_from_request(request),
                                       lot=lot['slug'],
                                       **url_args)

    # Remove parent categories (except the selected one), when any subcategory is selected - we
    # we think this may make navigation easier (and it's similar to what Amazon does)
    if any_descendant_selected:
        category_filters[:] = (c for c in category_filters if c['selected'])  # in-place filter(!)
    return any_category_selected
