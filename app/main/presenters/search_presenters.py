from collections import OrderedDict

from flask import url_for

from ..helpers.search_helpers import (
    get_filters_from_request,
    get_lot_from_request,
    get_keywords_from_request,
    get_filter_value_from_question_option,
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
            'label': question.get('filter_label') or question.get('name') or question['question'],
            'name': question['id'],
            'id': question['id'],
            'value': 'true',
        })

    elif question['type'] in ['checkboxes', 'radios', 'checkbox_tree']:
        _recursive_add_option_filters(question, question['options'], question_filters)

    return question_filters


def _recursive_add_option_filters(question, options_list, filters_list):
    for option in options_list:
        if not option.get('filter_ignore'):
            value = get_filter_value_from_question_option(option)
            presented_filter = {
                'label': option.get('filter_label') or option['label'],
                'name': question['id'],
                'id': '{}-{}'.format(
                    question['id'],
                    value.replace(' ', '-')),
                'value': value,
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


def annotate_lots_with_categories_selection(lots, category_filter_group, request):
    """
    Equivalent of set_filter_states but for where we are creating a tree of links i.e. the
    lots/categories widget. Adds links (where necessary) and shows the currently-selected
    lot and/or categories.
    :param lots: a sequence of lot dicts, which this function will annotate
    :param category_filter_group: a single filter group loaded from the framework search_filters manifest
    :param request: current request so that we can figure out what lots and categories are selected
    :return: the category filter that was directly selected, if any
    """
    current_lot_slug = get_lot_from_request(request)
    selected_category = None

    for lot in lots:
        lot_selected = (lot['slug'] == current_lot_slug)
        if lot_selected:
            lot['selected'] = True
            categories = category_filter_group['filters'] if category_filter_group else []
            selected_category = _annotate_categories_with_selection(lot, categories, request)
            lot['categories'] = categories

        if not lot_selected or selected_category is not None:
            # we need a link back to the lot _without_ a category selected
            lot['link'] = url_for('.search_services', q=get_keywords_from_request(request), lot=lot['slug'])

    return selected_category


def _annotate_categories_with_selection(lot, category_filters, request, parent_category=None):
    """
    Recursive setting of 'selected' state and adding of links to categories
    as part of building the lots/categories tree.
    :param category_filters: iterable of category filters as previously produced by filters_for_question
    :param request: request object from which to extract active filters
    :param parent_category: The name of the parent category; only set internally for recursion.
    :return: the category filter that was directly selected, if any
    """
    request_filters = get_filters_from_request(request)
    selected_category_filter = None

    for category in category_filters:
        category['selected'] = False
        param_values = request_filters.getlist(
            category['name'],
            type=str
        )
        directly_selected = (category['value'] in param_values)

        selected_descendant = _annotate_categories_with_selection(lot, category.get('children', []), request,
                                                                  parent_category=category['value'])

        if selected_descendant is not None:
            # If a parentCategory has been sent as a url query param, de-select all other parent categories.
            if request.values.get('parentCategory', category['value']) != category['value']:
                category['selected'] = False
                selected_descendant = None

            else:
                selected_category_filter = selected_descendant

        elif directly_selected:
            selected_category_filter = category

        if directly_selected or selected_descendant is not None:
            category['selected'] = True

        # As with lots, we want a link to the category - but not if the category is directly selected.
        # If we're showing it as 'selected' because one of its children is selected, then the link is
        # useful as a kind of breadcrumb, to return to showing all services in that overall category.
        if not directly_selected:
            # The argument in the URL must reflect the 'name' of the filter (i.e. the particular question
            # name it was derived from - 'serviceTypes' for G7/G8, 'serviceCategories' for G9.
            url_args = {category['name']: category['value']}

            # If this category has a parent, add it as a query param to the link generated.
            if parent_category:
                url_args['parentCategory'] = parent_category

            category['link'] = url_for('.search_services',
                                       q=get_keywords_from_request(request),
                                       lot=lot['slug'],
                                       **url_args)

    # When there's a selection, remove parent categories (i.e. preserve the selection, plus
    # sub-categories, which is those without children). The effect is that siblings of any
    # selected category or sub-category are shown, if that selection has no children.
    if selected_category_filter is not None:
        category_filters[:] = (c for c in category_filters
                               if c['selected'] or not c.get('children', []))  # in-place filter(!)

    return selected_category_filter
