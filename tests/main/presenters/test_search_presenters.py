import itertools
import json
import os

import flask
import mock
import pytest
from werkzeug.datastructures import MultiDict
from werkzeug.urls import Href

from dmcontent.content_loader import ContentLoader

from app.main.presenters.search_presenters import (
    filters_for_lot,
    set_filter_states,
    build_lots_and_categories_link_tree,
)
from ...helpers import BaseApplicationTest

content_loader = ContentLoader('tests/fixtures/content')
content_loader.load_manifest('g6', 'data', 'manifest')
content_loader.load_manifest('g9', 'data', 'manifest')
g6_builder = content_loader.get_manifest('g6', 'manifest')
g9_builder = content_loader.get_manifest('g9', 'manifest')


def _get_fixture_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_results_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


def _get_g9_aggregations_fixture_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'g9_aggregations_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


def _get_fixture_multiple_pages_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_results_multiple_pages_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


def _get_framework_lots(framework_slug):
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'frameworks.json'
    )
    with open(fixture_path) as fixture_file:
        frameworks = json.load(fixture_file)['frameworks']
        framework = list(filter(lambda x: x['slug'] == framework_slug, frameworks))[0]

        return framework['lots']


class TestSearchFilters(BaseApplicationTest):

    def _get_filter_group_by_label(self, lot, label):
        filter_groups = filters_for_lot(lot, g6_builder, all_lots=_get_framework_lots('g-cloud-6'))
        for filter_group in filter_groups.values():
            if filter_group['label'] == label:
                return filter_group

    def _get_request_for_params(self, params):
        return mock.Mock(args=MultiDict(params))

    def test_get_filter_groups_from_questions_with_radio_filters(self):
        radios_filter_group = self._get_filter_group_by_label(
            'saas', 'Radios example'
        )

        assert radios_filter_group == {
            'label': 'Radios example',
            'slug': 'radios-example',
            'filters': [
                {
                    'label': 'Option 1',
                    'name': 'radiosExample',
                    'id': 'radiosExample-option-1',
                    'value': 'option 1',
                },
                {
                    'label': 'Option 2',
                    'name': 'radiosExample',
                    'id': 'radiosExample-option-2',
                    'value': 'option 2',
                },
            ],
        }

    def test_get_filter_groups_from_questions_with_checkbox_filters(self):
        checkboxes_filter_group = self._get_filter_group_by_label(
            'saas', 'Checkboxes example'
        )
        assert checkboxes_filter_group == {
            'label': 'Checkboxes example',
            'slug': 'checkboxes-example',
            'filters': [
                {
                    'label': 'Option 1',
                    'name': 'checkboxesExample',
                    'id': 'checkboxesExample-option-1',
                    'value': 'option 1',
                },
                {
                    'label': 'Option 2',
                    'name': 'checkboxesExample',
                    'id': 'checkboxesExample-option-2',
                    'value': 'option 2',
                },
            ],
        }

    def test_filters_with_commas(self):
        checkboxes_filter_group = filters_for_lot('cloud-software', g9_builder)['categories-example']
        filter_with_comma = None
        for some_filter in checkboxes_filter_group['filters']:
            if some_filter['label'] == 'Option 3, with comma':
                filter_with_comma = some_filter
                break
        assert filter_with_comma is not None
        assert filter_with_comma['id'] == 'checkboxTreeExample-option-3-with-comma'
        assert filter_with_comma['value'] == 'option 3 with comma'

    def test_filters_with_values(self):
        checkboxes_filter_group = filters_for_lot('cloud-software', g9_builder)['categories-example']
        filter_with_value = None
        for some_filter in checkboxes_filter_group['filters']:
            if some_filter['label'] == 'Option 4 has a value':
                filter_with_value = some_filter
                break
        assert filter_with_value is not None
        assert filter_with_value['id'] == 'checkboxTreeExample-option_4_value'
        assert filter_with_value['value'] == 'option_4_value'

    def test_filters_with_filter_labels(self):
        checkboxes_filter_group = filters_for_lot('cloud-software', g9_builder)['categories-example']
        filter_with_special_label = None
        for some_filter in checkboxes_filter_group['filters']:
            if some_filter['value'] == 'option_5_value':
                filter_with_special_label = some_filter
                break
        assert filter_with_special_label is not None
        assert filter_with_special_label['label'] == 'Option 5 filter label'
        assert filter_with_special_label['id'] == 'checkboxTreeExample-option_5_value'

    def test_filters_with_filter_label_but_no_value(self):
        checkboxes_filter_group = filters_for_lot('cloud-software', g9_builder)['categories-example']
        filter_with_special_label = None
        for some_filter in checkboxes_filter_group['filters']:
            if some_filter['label'] == 'Option 6 filter label':
                filter_with_special_label = some_filter
                break
        assert filter_with_special_label is not None
        assert filter_with_special_label['id'] == 'checkboxTreeExample-option-6'
        assert filter_with_special_label['value'] == 'option 6'

    def test_get_filter_groups_from_questions_with_boolean_filters(self):
        booleans_filter_group = self._get_filter_group_by_label(
            'saas', 'Booleans example'
        )
        assert booleans_filter_group == {
            'label': 'Booleans example',
            'slug': 'booleans-example',
            'filters': [
                {
                    'label': 'Option 1',
                    'name': 'booleanExample1',
                    'id': 'booleanExample1',
                    'value': 'true',
                },
                {
                    'label': 'Option 2',
                    'name': 'booleanExample2',
                    'id': 'booleanExample2',
                    'value': 'true',
                },
            ],
        }

    def test_request_filters_are_set(self):
        search_filters = list(filters_for_lot('saas', g6_builder).values())
        request = self._get_request_for_params({
            'q': 'email',
            'booleanExample1': 'true'
        })

        set_filter_states(search_filters, request)
        assert search_filters[0]['filters'][0]['name'] == 'booleanExample1'
        assert search_filters[0]['filters'][0]['checked'] is True
        assert search_filters[0]['filters'][1]['name'] == 'booleanExample2'
        assert search_filters[0]['filters'][1]['checked'] is False

    def test_filter_groups_have_correct_default_state(self):
        request = self._get_request_for_params({
            'q': 'email',
            'lot': 'paas'
        })

        search_filters = list(filters_for_lot('paas', g6_builder).values())
        set_filter_states(search_filters, request)
        assert search_filters[0] == {
            'label': 'Booleans example',
            'slug': 'booleans-example',
            'filters': [
                {
                    'checked': False,
                    'label': 'Option 1',
                    'name': 'booleanExample1',
                    'id': 'booleanExample1',
                    'value': 'true',
                },
                {
                    'checked': False,
                    'label': 'Option 2',
                    'name': 'booleanExample2',
                    'id': 'booleanExample2',
                    'value': 'true',
                },
            ],
        }

    def test_filter_groups_have_correct_state_when_changed(self):
        request = self._get_request_for_params({
            'q': 'email',
            'lot': 'paas',
            'booleanExample1': 'true'
        })

        search_filters = list(filters_for_lot('paas', g6_builder).values())
        set_filter_states(search_filters, request)

        assert search_filters[0] == {
            'label': 'Booleans example',
            'slug': 'booleans-example',
            'filters': [
                {
                    'checked': True,
                    'label': 'Option 1',
                    'name': 'booleanExample1',
                    'id': 'booleanExample1',
                    'value': 'true',
                },
                {
                    'checked': False,
                    'label': 'Option 2',
                    'name': 'booleanExample2',
                    'id': 'booleanExample2',
                    'value': 'true',
                },
            ],
        }

    def test_no_lot_is_the_same_as_all(self):
        all_filters = self._get_filter_group_by_label(
            'all', 'Radios example'
        )
        no_lot_filters = self._get_filter_group_by_label(
            None, 'Radios example'
        )

        assert all_filters
        assert all_filters == no_lot_filters

    def test_instance_has_correct_filter_groups_for_paas(self):
        search_filters = filters_for_lot('paas', g6_builder).values()

        filter_group_labels = [
            group['label'] for group in search_filters
        ]

        assert 'Booleans example' in filter_group_labels
        assert 'Checkboxes example' in filter_group_labels
        assert 'Radios example' in filter_group_labels

    def test_instance_has_correct_filter_groups_for_iaas(self):
        search_filters = filters_for_lot('iaas', g6_builder).values()

        filter_group_labels = [
            group['label'] for group in search_filters
        ]

        assert 'Booleans example' not in filter_group_labels
        assert 'Checkboxes example' in filter_group_labels
        assert 'Radios example' in filter_group_labels


class TestLotsAndCategoriesSelection(BaseApplicationTest):
    def setup_method(self, method):
        super().setup_method(method)

        self.framework = self._get_framework_fixture_data('g-cloud-9')['frameworks']
        self.category_filter_group = filters_for_lot('cloud-software', g9_builder)['categories-example']
        # in these tests, the key 'category' key is 'checkboxTreeExample'

        self.search_api_client_patch = mock.patch(
            'app.main.views.g_cloud.search_api_client', autospec=True
        )
        self.search_api_client = self.search_api_client_patch.start()
        self.search_api_client.aggregate.return_value = _get_g9_aggregations_fixture_data()

    def teardown_method(self, method):
        self.search_api_client_patch.stop()
        super().teardown_method(method)

    def test_top_level_category_selection(self):
        url = "/g-cloud/search?q=&lot=cloud-software&otherfilter=somevalue&filterExample=option+1" \
              "&checkboxTreeExample=option+1&page=2"
        with self.app.test_request_context(url):
            selection = build_lots_and_categories_link_tree(
                self.framework,
                self.framework['lots'],
                self.category_filter_group,
                flask.request,
                flask.request.args,
                g9_builder,
                'services',
                'g-cloud-9',
                Href(flask.url_for('.search_services')),
                self.search_api_client
            )
            assert len(selection) == 3  # all -> software -> option1

            tree_root = selection[0]
            assert tree_root.get('label') == 'All categories'

            lot_filters = tree_root['children']
            selected_lot = next(f for f in lot_filters if f['selected'])
            assert selected_lot.get('label') == 'Cloud software'
            # there should be a link to the lot without a category, as a category has been selected within it
            assert 'lot=cloud-software' in selected_lot['link']
            assert 'checkboxTreeExample' not in selected_lot['link']

            # check that we have links in place to a search with the relevant category filter applied,
            # except to the currently-selected category
            category_filters = selected_lot['children']
            assert 'link' not in category_filters[0]
            assert not category_filters[0].get('children')
            assert 'checkboxTreeExample=option+2' in category_filters[1]['link']
            sub_category_filters = category_filters[1]['children']
            assert 'checkboxTreeExample=option+2.1' in sub_category_filters[0]['link']
            assert 'checkboxTreeExample=option+2.2' in sub_category_filters[1]['link']

            # ...and also that each link preserves only the values of filters that are valid for the target...
            for f in itertools.chain(category_filters, sub_category_filters):
                if f.get('link'):
                    assert 'filterExample=option+1' in f['link']
                    assert 'otherfilter=somevalue' not in f['link']
                    assert 'page=' not in f['link']

    def test_sub_category_selection(self):
        url = "/g-cloud/search?q=&lot=cloud-software&otherfilter=somevalue&checkboxTreeExample=option+2.2"
        with self.app.test_request_context(url):
            selection = build_lots_and_categories_link_tree(
                self.framework,
                self.framework['lots'],
                self.category_filter_group,
                flask.request,
                flask.request.args,
                g9_builder,
                'services',
                'g-cloud-9',
                Href(flask.url_for('.search_services')),
                self.search_api_client
            )
            assert len(selection) == 5  # all -> software -> option2 -> option2.2; option2 as a parent category filter

            tree_root = selection[0]
            # check that only siblings of the selected sub-category are shown, and other categories
            # have been removed
            lot_filters = tree_root['children']
            selected_lot = next(f for f in lot_filters if f['selected'])
            category_filters = selected_lot['children']
            assert len(category_filters) == 1
            assert category_filters[0]['selected']
            sub_category_filters = category_filters[0]['children']
            assert len(sub_category_filters) == 2

            assert [f for f in selection if f.get('name') == 'parentCategory'] == [
                {'name': 'parentCategory', 'value': 'option 2'}]

    def test_build_lots_and_categories_link_tree_with_no_categories_or_filters(self):
        url = "/g-cloud/search"
        with self.app.test_request_context(url):
            tree = build_lots_and_categories_link_tree(
                self.framework,
                self.framework['lots'],
                self.category_filter_group,
                flask.request,
                flask.request.args,
                g9_builder,
                'services',
                'g-cloud-9',
                Href(flask.url_for('.search_services')),
                self.search_api_client
            )

            assert tree == [
                {
                    'children': [
                        {
                            'label': 'Cloud hosting',
                            'link': '/g-cloud/search?lot=cloud-hosting',
                            'name': 'lot',
                            'service_count': 500,
                            'value': 'cloud-hosting'
                        },
                        {
                            'label': 'Cloud software',
                            'link': '/g-cloud/search?lot=cloud-software',
                            'name': 'lot',
                            'service_count': 500,
                            'value': 'cloud-software'
                        },
                        {
                            'label': 'Cloud support',
                            'link': '/g-cloud/search?lot=cloud-support',
                            'name': 'lot',
                            'service_count': 500,
                            'value': 'cloud-support'
                        }
                    ],
                    'label': 'All categories',
                    'link': '/g-cloud/search',
                    'selected': True
                }
            ]

    def test_build_lots_and_categories_link_tree_with_lot(self):
        url = "/g-cloud/search?lot=cloud-software"
        with self.app.test_request_context(url):
            tree = build_lots_and_categories_link_tree(
                self.framework,
                self.framework['lots'],
                self.category_filter_group,
                flask.request,
                flask.request.args,
                g9_builder,
                'services',
                'g-cloud-9',
                Href(flask.url_for('.search_services')),
                self.search_api_client
            )

            assert tree == [
                {
                    'label': 'All categories',
                    'link': '/g-cloud/search',
                    'selected': True,
                    'children': [
                        {
                            'label': 'Cloud software',
                            'name': 'lot',
                            'selected': True,
                            'service_count': 500,
                            'value': 'cloud-software',
                            'children': [
                                {
                                    'id': 'checkboxTreeExample-option-1',
                                    'label': 'Option 1',
                                    'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+1',
                                    'name': 'checkboxTreeExample',
                                    'selected': False,
                                    'service_count': 0,
                                    'value': 'option 1'
                                },
                                {
                                    'id': 'checkboxTreeExample-option-2',
                                    'label': 'Option 2',
                                    'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2',
                                    'name': 'checkboxTreeExample',
                                    'selected': False,
                                    'service_count': 0,
                                    'value': 'option 2',
                                    'children': [
                                        {
                                            'id': 'checkboxTreeExample-option-2.1',
                                            'label': 'Option 2.1',
                                            'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2.1&parentCategory=option+2',  # NOQA
                                            'name': 'checkboxTreeExample',
                                            'selected': False,
                                            'service_count': 0,
                                            'value': 'option 2.1'
                                        },
                                        {
                                            'id': 'checkboxTreeExample-option-2.2',
                                            'label': 'Option 2.2',
                                            'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2.2&parentCategory=option+2',  # NOQA
                                            'name': 'checkboxTreeExample',
                                            'selected': False,
                                            'service_count': 0,
                                            'value': 'option 2.2'
                                        }
                                    ],
                                },
                                {
                                    'id': 'checkboxTreeExample-option-3-with-comma',
                                    'label': 'Option 3, with comma',
                                    'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+3+with+comma',  # NOQA
                                    'name': 'checkboxTreeExample',
                                    'selected': False,
                                    'service_count': 0,
                                    'value': 'option 3 with comma'
                                },
                                {
                                    'id': 'checkboxTreeExample-option_4_value',
                                    'label': 'Option 4 has a value',
                                    'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option_4_value',
                                    'name': 'checkboxTreeExample',
                                    'selected': False,
                                    'service_count': 0,
                                    'value': 'option_4_value'
                                },
                                {
                                    'id': 'checkboxTreeExample-option_5_value',
                                    'label': 'Option 5 filter label',
                                    'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option_5_value',
                                    'name': 'checkboxTreeExample',
                                    'selected': False,
                                    'service_count': 0,
                                    'value': 'option_5_value'
                                },
                                {
                                    'id': 'checkboxTreeExample-option-6',
                                    'label': 'Option 6 filter label',
                                    'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+6',
                                    'name': 'checkboxTreeExample',
                                    'selected': False,
                                    'service_count': 0,
                                    'value': 'option 6'
                                }
                            ],
                        }
                    ],
                },
                {
                    'label': 'Cloud software',
                    'name': 'lot',
                    'selected': True,
                    'service_count': 500,
                    'value': 'cloud-software',
                    'children': [
                        {
                            'id': 'checkboxTreeExample-option-1',
                            'label': 'Option 1',
                            'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+1',
                            'name': 'checkboxTreeExample',
                            'selected': False,
                            'service_count': 0,
                            'value': 'option 1'
                        },
                        {
                            'id': 'checkboxTreeExample-option-2',
                            'label': 'Option 2',
                            'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2',
                            'name': 'checkboxTreeExample',
                            'selected': False,
                            'service_count': 0,
                            'value': 'option 2',
                            'children': [
                                {
                                    'id': 'checkboxTreeExample-option-2.1',
                                    'label': 'Option 2.1',
                                    'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2.1&parentCategory=option+2',  # NOQA
                                    'name': 'checkboxTreeExample',
                                    'selected': False,
                                    'service_count': 0,
                                    'value': 'option 2.1'
                                },
                                {
                                    'id': 'checkboxTreeExample-option-2.2',
                                    'label': 'Option 2.2',
                                    'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2.2&parentCategory=option+2',  # NOQA
                                    'name': 'checkboxTreeExample',
                                    'selected': False,
                                    'service_count': 0,
                                    'value': 'option 2.2'
                                }
                            ],
                        },
                        {
                            'id': 'checkboxTreeExample-option-3-with-comma',
                            'label': 'Option 3, with comma',
                            'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+3+with+comma',
                            'name': 'checkboxTreeExample',
                            'selected': False,
                            'service_count': 0,
                            'value': 'option 3 with comma'
                        },
                        {
                            'id': 'checkboxTreeExample-option_4_value',
                            'label': 'Option 4 has a value',
                            'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option_4_value',
                            'name': 'checkboxTreeExample',
                            'selected': False,
                            'service_count': 0,
                            'value': 'option_4_value'
                        },
                        {
                            'id': 'checkboxTreeExample-option_5_value',
                            'label': 'Option 5 filter label',
                            'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option_5_value',
                            'name': 'checkboxTreeExample',
                            'selected': False,
                            'service_count': 0,
                            'value': 'option_5_value'
                        },
                        {
                            'id': 'checkboxTreeExample-option-6',
                            'label': 'Option 6 filter label',
                            'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+6',
                            'name': 'checkboxTreeExample',
                            'selected': False,
                            'service_count': 0,
                            'value': 'option 6'
                        }
                    ],
                }
            ]

    def test_build_lots_and_categories_link_tree_with_lot_and_no_category_filters_has_all_lots_in_root_node(self):
        url = "/g-cloud/search?lot=cloud-software"
        with self.app.test_request_context(url):
            tree = build_lots_and_categories_link_tree(
                self.framework,
                self.framework['lots'],
                None,
                flask.request,
                flask.request.args,
                g9_builder,
                'services',
                'g-cloud-9',
                Href(flask.url_for('.search_services')),
                self.search_api_client
            )

            assert tree[0] == {
                'label': 'All categories',
                'link': '/g-cloud/search',
                'selected': True,
                'children': [
                    {
                        'label': 'Cloud hosting',
                        'link': '/g-cloud/search?lot=cloud-hosting',
                        'name': 'lot',
                        'service_count': 500,
                        'value': 'cloud-hosting'
                    },
                    {
                        'children': [],
                        'label': 'Cloud software',
                        'name': 'lot',
                        'selected': True,
                        'service_count': 500,
                        'value': 'cloud-software'
                    },
                    {
                        'label': 'Cloud support',
                        'link': '/g-cloud/search?lot=cloud-support',
                        'name': 'lot',
                        'service_count': 500,
                        'value': 'cloud-support'
                    }
                ]
            }

    @property
    def tree_with_cloud_software__option_2__option_2_1__selected(self):
        return [
            {
                'label': 'All categories',
                'selected': True,
                'link': '/g-cloud/search',
                'children': [
                    {
                        'label': 'Cloud software',
                        'name': 'lot',
                        'value': 'cloud-software',
                        'service_count': 500,
                        'children': [
                            {
                                'label': 'Option 2',
                                'name': 'checkboxTreeExample',
                                'id': 'checkboxTreeExample-option-2',
                                'value': 'option 2',
                                'children': [
                                    {
                                        'label': 'Option 2.1',
                                        'name': 'checkboxTreeExample',
                                        'id': 'checkboxTreeExample-option-2.1',
                                        'value': 'option 2.1',
                                        'selected': True,
                                        'service_count': 0
                                    }, {
                                        'label': 'Option 2.2',
                                        'name': 'checkboxTreeExample',
                                        'id': 'checkboxTreeExample-option-2.2',
                                        'value': 'option 2.2',
                                        'selected': False,
                                        'service_count': 0,
                                        'link': (
                                            '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2.2'
                                            '&parentCategory=option+2'
                                        )
                                    }
                                ],
                                'selected': True,
                                'service_count': 0,
                                'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2'
                            }
                        ],
                        'selected': True,
                        'link': '/g-cloud/search?lot=cloud-software'
                    }
                ]
            }, {
                'label': 'Cloud software',
                'name': 'lot',
                'value': 'cloud-software',
                'service_count': 500,
                'children': [
                    {
                        'label': 'Option 2',
                        'name': 'checkboxTreeExample',
                        'id': 'checkboxTreeExample-option-2',
                        'value': 'option 2',
                        'children': [
                            {
                                'label': 'Option 2.1',
                                'name': 'checkboxTreeExample',
                                'id': 'checkboxTreeExample-option-2.1',
                                'value': 'option 2.1',
                                'selected': True,
                                'service_count': 0
                            }, {
                                'label': 'Option 2.2',
                                'name': 'checkboxTreeExample',
                                'id': 'checkboxTreeExample-option-2.2',
                                'value': 'option 2.2',
                                'selected': False,
                                'service_count': 0,
                                'link': (
                                    '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2.2'
                                    '&parentCategory=option+2'
                                )
                            }
                        ],
                        'selected': True,
                        'service_count': 0,
                        'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2'
                    }
                ],
                'selected': True,
                'link': '/g-cloud/search?lot=cloud-software'
            }, {
                'name': 'parentCategory',
                'value': 'option 2'
            }, {
                'label': 'Option 2',
                'name': 'checkboxTreeExample',
                'id': 'checkboxTreeExample-option-2',
                'value': 'option 2',
                'children': [
                    {
                        'label': 'Option 2.1',
                        'name': 'checkboxTreeExample',
                        'id': 'checkboxTreeExample-option-2.1',
                        'value': 'option 2.1',
                        'selected': True,
                        'service_count': 0
                    }, {
                        'label': 'Option 2.2',
                        'name': 'checkboxTreeExample',
                        'id': 'checkboxTreeExample-option-2.2',
                        'value': 'option 2.2',
                        'selected': False,
                        'service_count': 0,
                        'link': (
                            '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2.2&parentCategory=option+2'
                        )
                    }
                ],
                'selected': True,
                'service_count': 0,
                'link': '/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2'
            }, {
                'label': 'Option 2.1',
                'name': 'checkboxTreeExample',
                'id': 'checkboxTreeExample-option-2.1',
                'value': 'option 2.1',
                'selected': True,
                'service_count': 0
            }
        ]

    @pytest.mark.parametrize(
        'url', (
            "/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2.1",
            "/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2.1&parentCategory=option+2"
        )
    )
    def test_build_lots_and_categories_link_tree_with_lot_and_filter_selected(self, url):
        with self.app.test_request_context(url):
            tree = build_lots_and_categories_link_tree(
                self.framework,
                self.framework['lots'],
                self.category_filter_group.copy(),
                flask.request,
                flask.request.args,
                g9_builder,
                'services',
                'g-cloud-9',
                Href(flask.url_for('.search_services')),
                self.search_api_client
            )

        assert tree == self.tree_with_cloud_software__option_2__option_2_1__selected
        # Assert, as per the url, that only our specified filter is 'selected' in the output
        assert(
            [(child['id'], child['selected']) for child in tree[0]['children'][0]['children'][0]['children']] ==
            [('checkboxTreeExample-option-2.1', True), ('checkboxTreeExample-option-2.2', False)]
        )

    def test_build_lots_and_categories_link_tree_with_lot_and_filter_and_same_named_filter_in_tree(self):
        url = "/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2.1&parentCategory=option+2"

        self.category_filter_group['filters'] += [
            {
                'label': 'Option 7',
                'name': 'checkboxTreeExample',
                'id': 'checkboxTreeExample-option-7',
                'value': 'option 7',
                'children': [
                    {
                        'label': 'Option 2.1',
                        'name': 'checkboxTreeExample',
                        'id': 'checkboxTreeExample-option-2.1',
                        'value': 'option 2.1'
                    }, {
                        'label': 'Option 7.1',
                        'name': 'checkboxTreeExample',
                        'id': 'checkboxTreeExample-option-7.1',
                        'value': 'option 7.1'
                    }
                ]
            }
        ]
        with self.app.test_request_context(url):
            tree = build_lots_and_categories_link_tree(
                self.framework,
                self.framework['lots'],
                self.category_filter_group.copy(),
                flask.request,
                flask.request.args,
                g9_builder,
                'services',
                'g-cloud-9',
                Href(flask.url_for('.search_services')),
                self.search_api_client
            )

        assert tree == self.tree_with_cloud_software__option_2__option_2_1__selected
        assert(
            [(child['id'], child['selected']) for child in tree[0]['children'][0]['children'][0]['children']] ==
            [('checkboxTreeExample-option-2.1', True), ('checkboxTreeExample-option-2.2', False)]
        )

        tree_child_value_lists = [[child.get('id') for child in node.get('children', [])] for node in tree]
        tree_child_values = [item for sublist in tree_child_value_lists for item in sublist]

        assert 'checkboxTreeExample-option-7.1' not in tree_child_values
        assert tree_child_values.count('checkboxTreeExample-option-2.1') == 1

    def test_build_lots_and_categories_link_tree_with_lot_and_filter_and_same_named_filter_in_tree_with_no_parent(self):
        url = "/g-cloud/search?lot=cloud-software&checkboxTreeExample=option+2.1"

        self.category_filter_group['filters'] += [
            {
                'label': 'Option 7',
                'name': 'checkboxTreeExample',
                'id': 'checkboxTreeExample-option-7',
                'value': 'option 7',
                'children': [
                    {
                        'label': 'Option 2.1',
                        'name': 'checkboxTreeExample',
                        'id': 'checkboxTreeExample-option-2.1',
                        'value': 'option 2.1'
                    }, {
                        'label': 'Option 7.1',
                        'name': 'checkboxTreeExample',
                        'id': 'checkboxTreeExample-option-7.1',
                        'value': 'option 7.1'
                    }
                ]
            }
        ]
        with self.app.test_request_context(url):
            tree = build_lots_and_categories_link_tree(
                self.framework,
                self.framework['lots'],
                self.category_filter_group.copy(),
                flask.request,
                flask.request.args,
                g9_builder,
                'services',
                'g-cloud-9',
                Href(flask.url_for('.search_services')),
                self.search_api_client
            )

        tree_child_value_selected_lists = [
            [(child.get('id'), child['selected']) for child in node.get('children', [])] for node in tree
        ]
        tree_child_value_selected = [item for sublist in tree_child_value_selected_lists for item in sublist]

        assert ('checkboxTreeExample-option-7.1', False) in tree_child_value_selected
        assert tree_child_value_selected.count(('checkboxTreeExample-option-2.1', True)) == 2
