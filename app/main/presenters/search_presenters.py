from collections import OrderedDict

from werkzeug.datastructures import MultiDict

from ..helpers.framework_helpers import get_lots_by_slug
from ..helpers.search_helpers import (
    get_filters_from_request,
    get_valid_lot_from_args_or_none,
    get_filter_value_from_question_option,
    build_search_query,
    clean_request_args
)
from ..presenters.search_results import AggregationResults


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
            "slug": section["slug"],
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
    request_filters = get_filters_from_request(request.args)

    for filter_group in filter_groups:
        for filter_item in filter_group['filters']:
            filter_item['checked'] = False

            param_values = request_filters.getlist(
                filter_item['name'],
                type=str
            )
            if len(param_values) > 0:
                filter_item['checked'] = (
                    filter_item['value'] in param_values
                )


def _get_category_filter_key_set(category_filter_group):
    """
    Returns the set of keys used in the category filter group. In practice
    there should only be one, but for completeness we allow for the possibility
    of there being several. In G6/7/8, this was {'serviceTypes'}, in G9 it's
    {'serviceCategories'} .
    :return: set[string]
    """
    keys = {'lot'}

    if category_filter_group is not None and category_filter_group['filters']:
        keys.update({f['name'] for f in category_filter_group['filters']})

    return keys


def _get_aggregations_for_lot_with_filters(
    lot, content_manifest, framework, cleaned_request_args, doc_type, index, search_api_client
):
    filters = filters_for_lot(lot, content_manifest, all_lots=framework['lots'])
    lots_by_slug = get_lots_by_slug(framework)

    aggregate_request_args = cleaned_request_args.copy()
    aggregate_on_fields = _get_category_filter_key_set(filters.get('categories'))

    # We need to remove filters we're aggregating on because they'll throw off the counts.
    for filter_to_remove in aggregate_on_fields.intersection(aggregate_request_args.keys()):
        aggregate_request_args.pop(filter_to_remove)

    aggregate_request_args['lot'] = lot

    aggregate_api_response = search_api_client.aggregate(
        index=index,
        doc_type=doc_type,
        aggregations=aggregate_on_fields,
        **build_search_query(
            aggregate_request_args,
            filters.values(),
            content_manifest,
            lots_by_slug,
            for_aggregation=True
        )
    )

    return AggregationResults(aggregate_api_response)


def _build_base_url_args(request_args, content_manifest, framework, lot_slug):
    """Returns a copy of request.args (MultiDict) with filters cleaned for the specified lot"""
    url_args = request_args.copy()

    filters = filters_for_lot(lot_slug, content_manifest, all_lots=framework['lots'])
    lots_by_slug = get_lots_by_slug(framework)

    url_args = clean_request_args(url_args, filters.values(), lots_by_slug)

    return url_args


def _update_base_url_args_for_lot_and_category(url_args, keys_to_remove, lot_slug=None, category=None,
                                               parent_category=None):
    """Returns a copy of request.args (MultiDict) with lot and category set, suitable for href link building."""

    # Remove existing keys so we can re-use a dict without having to make a clean copy each time.
    for arg_key in keys_to_remove.intersection(url_args):
        del url_args[arg_key]

    url_args['lot'] = lot_slug

    if category:
        url_args[category['name']] = category['value']

        if parent_category:
            url_args['parentCategory'] = parent_category
        elif 'parentCategory' in url_args:
            del url_args['parentCategory']

    return url_args


def build_lots_and_categories_link_tree(
    framework, lots, category_filter_group, request, cleaned_request_args,
    content_manifest, doc_type, index, search_link_builder, search_api_client
):
    """
    Equivalent of set_filter_states but for where we are creating a tree of links i.e. the
    lots/categories widget. Adds links (where necessary) and shows the currently-selected
    lot and/or categories.

    Returns a list of selected filters: there will always be at least one element, which is
    the root of the tree; there may then be a category; there may then follow a sub-category.

    :param framework: the framework from the API
    :param lots: a sequence of lot dicts applicable to the live framework(s)
    :param category_filter_group: a single filter group loaded from the framework search_filters manifest
    :param request: the original request for creating links for nodes
    :param cleaned_request_args: current cleaned request args so that we can figure out selected lots and categories
    :param content_manifest: a ContentManifest instance for the frameworks search_filters.
    :param search_link_builder: a werkzeug Href object instanciated with the view that the category tree links should
                                link to as its base. It can be called with any number of positional and keyword
                                arguments which than are used to assemble the full URL.
    :return: list of selected category and lot filters, starting with the 'all categories' root node
    """
    current_lot_slug = get_valid_lot_from_args_or_none(cleaned_request_args, [lot['slug'] for lot in lots])

    # Links in the tree should preserve all the filters, except those relating to this tree (i.e. lot
    # and category).
    keys_to_remove = _get_category_filter_key_set(category_filter_group)
    keys_to_remove.add('page')
    preserved_request_args = MultiDict(
        (k, v) for (k, v) in request.args.items(multi=True) if k not in keys_to_remove
    )

    selected_filters = list()
    # Create root node for the tree, always selected, which is the parent of the various lots.
    root_node = {
        'label': 'All categories',
        'selected': True,  # for consistency with lower levels
        'link': search_link_builder(_build_base_url_args(preserved_request_args, content_manifest, framework, None)),
        'children': [],
    }

    selected_filters.append(root_node)

    aggregations_by_lot = {
        lot['slug']: _get_aggregations_for_lot_with_filters(
            lot['slug'], content_manifest, framework, cleaned_request_args, doc_type, index, search_api_client
        ) for lot in lots
    }

    for lot in lots:
        selected_categories = []
        lot_selected = lot['slug'] == current_lot_slug

        lot_filter = {
            'label': lot['name'],
            'name': 'lot',  # a filter's "name" is its key for form submission purposes
            'value': lot['slug'],
            'service_count': aggregations_by_lot[lot['slug']].results['lot'].get(lot['slug'], 0),
        }

        url_args_for_lot = _build_base_url_args(preserved_request_args, content_manifest, framework, lot['slug'])
        categories = category_filter_group['filters'] if category_filter_group else []

        if lot_selected:
            selected_categories = _annotate_categories_with_selection(lot['slug'], categories, cleaned_request_args,
                                                                      url_args_for_lot, content_manifest, framework,
                                                                      aggregations_by_lot[lot['slug']], keys_to_remove,
                                                                      search_link_builder)
            selected_filters.append(lot_filter)
            selected_filters.extend(selected_categories)

            lot_filter['children'] = categories
            lot_filter['selected'] = True

        if not lot_selected or selected_categories:
            url_args_for_lot = _update_base_url_args_for_lot_and_category(url_args_for_lot,
                                                                          keys_to_remove,
                                                                          lot_slug=lot['slug'])
            lot_filter['link'] = search_link_builder(url_args_for_lot)

        if lot_selected or current_lot_slug is None or (current_lot_slug and not categories):
            root_node['children'].append(lot_filter)

    return selected_filters


def _annotate_categories_with_selection(lot_slug, category_filters, cleaned_request_args, url_args_for_lot,
                                        content_manifest, framework, aggregations, keys_to_remove, search_link_builder,
                                        parent_category=None):
    """
    Recursive setting of 'selected' state and adding of links to categories
    as part of building the lots/categories tree.
    :param lot_slug for the lot that owns this set of categories
    :param category_filters: iterable of category filters as previously produced by filters_for_question
    :param cleaned_request_args: request args for extracting filters
    :param url_args_for_lot: MultiDict of arguments to be preserved when generating links
    :param content_manifest: a ContentManifest instance for G-Cloud search_filters.
    :param framework: the latest G-Cloud framework from the API
    :param aggregations: A dict of aggregation results for categories, by lot slug.
    :param keys_to_remove: set of lot/category keys to remove from dicts when building links.
    :param search_link_builder: a werkzeug Href object for the view category tree links link to
    :param parent_category: The name of the parent category; only set internally for recursion.
    :return: list of filters that were selected, if any; the last of which was directly selected
    """
    request_filters = get_filters_from_request(cleaned_request_args)
    selected_category_filters = []
    selected_category_at_this_level = None

    for category in category_filters:
        category['selected'] = False
        category['service_count'] = aggregations.results.get('serviceCategories', {}).get(category['label'], 0)

        param_values = request_filters.getlist(
            category['name'],
            type=str
        )
        directly_selected = (category['value'] in param_values)

        selected_descendants = _annotate_categories_with_selection(
            lot_slug, category.get('children', []), cleaned_request_args, url_args_for_lot,
            content_manifest, framework, aggregations, keys_to_remove, search_link_builder,
            parent_category=category['value'])

        if selected_descendants:
            # If a parentCategory has been sent as a url query param, and it's this category...
            # (Note: `get` fallback is for if there are selected descendants but no parent category is set, which is
            # not expected, but could happen if constructing URLs by hand.)
            if cleaned_request_args.get('parentCategory', category['value']) == category['value']:
                # ... then ensure this choice survives as a hidden field for the filters form
                parent_category_filter = dict()
                parent_category_filter['name'] = 'parentCategory'
                parent_category_filter['value'] = category['value']
                selected_category_filters.append(parent_category_filter)

            else:
                # ... but otherwise, don't include this category's children in the tree
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
            url_args = _update_base_url_args_for_lot_and_category(url_args_for_lot,
                                                                  keys_to_remove,
                                                                  lot_slug=lot_slug,
                                                                  category=category,
                                                                  parent_category=parent_category)
            category['link'] = search_link_builder(url_args)

    # When there's a selection, and the selected category has children, remove sibling subcategories,
    # as they are confusing. Siblings are still shown at the bottom level (i.e. where there are
    # no child categories.)
    if selected_category_at_this_level and selected_category_at_this_level.get('children', []):
        category_filters[:] = (c for c in category_filters if c['selected'])  # in-place filter(!)

    return selected_category_filters
