from collections import OrderedDict

from flask import url_for
from werkzeug.datastructures import MultiDict
from werkzeug.urls import Href

from ..helpers.search_helpers import (
    get_filters_from_request,
    get_lot_from_request,
    get_filter_value_from_question_option,
)


def sections_for_lot(lot, builder, all_lots=[]):
    if lot is None or lot == 'all':
        for lot_slug in [x['slug'] for x in all_lots]:
            builder = builder.filter({'lot': lot_slug})
    else:
        builder = builder.filter({'lot': lot})

    return builder.sections


def filters_for_lot(lot, builder, all_lots=[]):
    sections = sections_for_lot(lot, builder, all_lots=all_lots)
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


def _get_category_filter_key_set(category_filter_group):
    """
    Returns the set of keys used in the category filter group. In practice
    there should only be one, but for completeness we allow for the possibility
    of there being several. In G6/7/8, this was {'serviceTypes'}, in G9 it's
    {'serviceCategories'} .
    :return: set[string]
    """
    if category_filter_group is not None and category_filter_group['filters']:
        return {f['name'] for f in category_filter_group['filters']}
    else:
        return set()


def build_lots_and_categories_link_tree(lots, category_filter_group, request):
    """
    Equivalent of set_filter_states but for where we are creating a tree of links i.e. the
    lots/categories widget. Adds links (where necessary) and shows the currently-selected
    lot and/or categories.

    :param lots: a sequence of lot dicts applicable to the live framework(s)
    :param category_filter_group: a single filter group loaded from the framework search_filters manifest
    :param request: current request so that we can figure out what lots and categories are selected
    :return: the 'all categories' node which is the root of the tree
    """
    current_lot_slug = get_lot_from_request(request)

    # Links in the tree should preserve all the filters, except those relating to this tree (i.e. lot
    # and category).
    search_link_builder = Href(url_for('.search_services'))
    keys_to_remove = _get_category_filter_key_set(category_filter_group)
    keys_to_remove.add('lot')
    clean_url_args = MultiDict((k, v) for (k, v) in request.args.items(multi=True) if k not in keys_to_remove)

    # Create root node for the tree, always selected, which is the parent of the various lots.
    root_node = dict()
    root_node['name'] = 'All categories'
    root_node['selected'] = True  # for consistency with lower levels
    root_node['link'] = search_link_builder(clean_url_args)
    root_node['children'] = list()

    for lot in lots:
        selected_categories = []
        lot_selected = (lot['slug'] == current_lot_slug)
        lot_filter = lot.copy()
        if lot_selected:
            categories = category_filter_group['filters'] if category_filter_group else []
            # We could preserve the returned list of selected categories along with the selected lot, if we
            # wanted to build a breadcrumb trail.
            selected_categories = _annotate_categories_with_selection(lot['slug'], categories, request)

            lot_filter['children'] = categories
            lot_filter['selected'] = True

        if not lot_selected or selected_categories:
            # we need a link to the lot _without_ a category selected
            url_args = MultiDict(clean_url_args)
            url_args['lot'] = lot['slug']

            lot_filter['link'] = search_link_builder(url_args)

        if lot_selected or current_lot_slug is None:
            root_node['children'].append(lot_filter)

    return root_node


def _annotate_categories_with_selection(lot_slug, category_filters, request, parent_category=None):
    """
    Recursive setting of 'selected' state and adding of links to categories
    as part of building the lots/categories tree.
    :param lot_slug for the lot that owns this set of categories
    :param category_filters: iterable of category filters as previously produced by filters_for_question
    :param request: request object from which to extract active filters
    :param parent_category: The name of the parent category; only set internally for recursion.
    :return: list of filters that were selected, if any; the last of which was directly selected
    """
    request_filters = get_filters_from_request(request)
    selected_category_filters = []
    search_link_builder = Href(url_for('.search_services'))
    selected_category_at_this_level = None

    for category in category_filters:
        category['selected'] = False
        param_values = request_filters.getlist(
            category['name'],
            type=str
        )
        directly_selected = (category['value'] in param_values)

        selected_descendants = _annotate_categories_with_selection(lot_slug, category.get('children', []), request,
                                                                   parent_category=category['value'])

        if selected_descendants:
            # If a parentCategory has been sent as a url query param, de-select all other parent categories.
            if request.values.get('parentCategory', category['value']) != category['value']:
                selected_descendants = []

        if directly_selected or selected_descendants:
            selected_category_at_this_level = category
            selected_category_filters.append(category)
            selected_category_filters.extend(selected_descendants)
            category['selected'] = True

        # As with lots, we want a link to the category - but not if the category is directly selected.
        # If we're showing it as 'selected' because one of its children is selected, then the link is
        # useful as a kind of breadcrumb, to return to showing all services in that overall category.
        if not directly_selected:
            url_args = MultiDict(request.args)
            # The argument in the URL must reflect the 'name' of the filter (i.e. the particular question
            # name it was derived from - 'serviceTypes' for G7/G8, 'serviceCategories' for G9.
            url_args[category['name']] = category['value']
            url_args['lot'] = lot_slug

            # If this category has a parent, add it as a query param to the link generated.
            if parent_category:
                url_args['parentCategory'] = parent_category
            elif 'parentCategory' in url_args:
                del url_args['parentCategory']

            category['link'] = search_link_builder(url_args)

    # When there's a selection, and the selected category has children, remove sibling subcategories,
    # as they are confusing. Siblings are still shown at the bottom level (i.e. where there are
    # no child categories.)
    if selected_category_at_this_level and selected_category_at_this_level.get('children', []):
        category_filters[:] = (c for c in category_filters if c['selected'])  # in-place filter(!)

    return selected_category_filters
