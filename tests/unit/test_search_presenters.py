import os
import json
import unittest
from mock import Mock
from dmutils.content_loader import ContentLoader
from werkzeug.datastructures import MultiDict

from app.presenters.search_presenters import filters_for_lot, set_filter_states


questions_builder = ContentLoader(
    "tests/fixtures/g6_questions/manifest.yml",
    "tests/fixtures/g6_questions/data/"
).get_builder()


def _get_fixture_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_results_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


def _get_fixture_multiple_pages_data():
    test_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    fixture_path = os.path.join(
        test_root, 'fixtures', 'search_results_multiple_pages_fixture.json'
    )
    with open(fixture_path) as fixture_file:
        return json.load(fixture_file)


class TestSearchFilters(unittest.TestCase):

    def _get_filter_group_by_label(self, lot, label):
        filter_groups = filters_for_lot(lot, questions_builder)
        for filter_group in filter_groups:
            if filter_group['label'] == label:
                return filter_group

    def _get_request_for_params(self, params):
        return Mock(args=MultiDict(params))

    def test_get_filter_groups_from_questions_with_radio_filters(self):
        radios_filter_group = self._get_filter_group_by_label(
            'saas', 'Radios example'
        )

        self.assertEqual({
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
                }
            ]
        }, radios_filter_group)

    def test_get_filter_groups_from_questions_with_checkbox_filters(self):
        checkboxes_filter_group = self._get_filter_group_by_label(
            'saas', 'Checkboxes example'
        )
        self.assertEqual({
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
                }
            ]
        }, checkboxes_filter_group)

    def test_get_filter_groups_from_questions_with_boolean_filters(self):
        booleans_filter_group = self._get_filter_group_by_label(
            'saas', 'Booleans example'
        )
        self.assertEqual({
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
                }
            ]
        }, booleans_filter_group)

    def test_request_filters_are_set(self):
        search_filters = filters_for_lot('saas', questions_builder)
        request = self._get_request_for_params({
            'q': 'email',
            'booleanExample1': 'true'
        })

        set_filter_states(search_filters, request)
        self.assertEqual(search_filters[0]['filters'][0]['name'],
                         'booleanExample1')
        self.assertEqual(search_filters[0]['filters'][0]['checked'], True)
        self.assertEqual(search_filters[0]['filters'][1]['name'],
                         'booleanExample2')
        self.assertEqual(search_filters[0]['filters'][1]['checked'], False)

    def test_filter_groups_have_correct_default_state(self):
        request = self._get_request_for_params({
            'q': 'email',
            'lot': 'paas'
        })

        search_filters = filters_for_lot('paas', questions_builder)
        set_filter_states(search_filters, request)
        self.assertEqual(
            search_filters[0],
            {
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
                    }
                ]
            }
        )

    def test_filter_groups_have_correct_state_when_changed(self):
        request = self._get_request_for_params({
            'q': 'email',
            'lot': 'paas',
            'booleanExample1': 'true'
        })

        search_filters = filters_for_lot('paas', questions_builder)
        set_filter_states(search_filters, request)

        self.assertEqual(
            search_filters[0],
            {
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
                    }
                ]
            }
        )

    def test_no_lot_is_the_same_as_all(self):
        all_filters = self._get_filter_group_by_label(
            'all', 'Radios example'
        )
        no_lot_filters = self._get_filter_group_by_label(
            None, 'Radios example'
        )

        self.assertTrue(all_filters)
        self.assertEqual(all_filters, no_lot_filters)

    def test_instance_has_correct_filter_groups_for_paas(self):
        search_filters = filters_for_lot('paas', questions_builder)

        filter_group_labels = [
            group['label'] for group in search_filters
        ]

        self.assertTrue('Booleans example' in filter_group_labels)
        self.assertTrue('Checkboxes example' in filter_group_labels)
        self.assertTrue('Radios example' in filter_group_labels)

    def test_instance_has_correct_filter_groups_for_iaas(self):
        search_filters = filters_for_lot('iaas', questions_builder)

        filter_group_labels = [
            group['label'] for group in search_filters
        ]

        self.assertFalse('Booleans example' in filter_group_labels)
        self.assertTrue('Checkboxes example' in filter_group_labels)
        self.assertTrue('Radios example' in filter_group_labels)
