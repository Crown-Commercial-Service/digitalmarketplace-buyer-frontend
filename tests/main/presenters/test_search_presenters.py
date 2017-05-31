import os
import json
import itertools
from mock import Mock
from dmcontent.content_loader import ContentLoader
from werkzeug.datastructures import MultiDict
import flask

from app.main.presenters.search_presenters import (
    filters_for_lot,
    set_filter_states,
    get_lots_and_categories_selection,
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
        return Mock(args=MultiDict(params))

    def test_get_filter_groups_from_questions_with_radio_filters(self):
        radios_filter_group = self._get_filter_group_by_label(
            'saas', 'Radios example'
        )

        assert radios_filter_group == {
            'label': 'Radios example',
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

    def test_show_lots_and_categories_selection(self):
        framework = self._get_framework_fixture_data('g-cloud-9')['frameworks']
        lots = framework['lots']
        lot_slug = 'cloud-software'

        category_filter_group = filters_for_lot(lot_slug, g9_builder)['categories-example']

        with self.app.test_request_context("/g-cloud/search?q=&lot={}&otherfilter=somevalue".format(lot_slug)):
            selection = get_lots_and_categories_selection(lots, category_filter_group, flask.request)
            assert len(selection) == 2

            assert selection[0].get('name') == 'All categories'

            assert selection[1].get('name') == 'Cloud software'
            lot_filters = selection[0]['children']
            assert selection[1] in lot_filters

            category_filters = selection[1]['children']
            assert 'checkboxTreeExample=option+1' in category_filters[0]['link']
            assert not category_filters[0].get('children')
            assert 'checkboxTreeExample=option+2' in category_filters[1]['link']
            sub_category_filters = category_filters[1]['children']
            assert 'checkboxTreeExample=option+2.1' in sub_category_filters[0]['link']
            assert 'checkboxTreeExample=option+2.2' in sub_category_filters[1]['link']

            for f in itertools.chain(category_filters, sub_category_filters):
                assert 'otherfilter=somevalue' in f['link']

    def test_filter_groups_have_correct_default_state(self):
        request = self._get_request_for_params({
            'q': 'email',
            'lot': 'paas'
        })

        search_filters = list(filters_for_lot('paas', g6_builder).values())
        set_filter_states(search_filters, request)
        assert search_filters[0] == {
            'label': 'Booleans example',
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
