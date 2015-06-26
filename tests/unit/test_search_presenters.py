import os
import json
import unittest
from mock import Mock
from dmutils.content_loader import ContentLoader
from werkzeug.datastructures import MultiDict


questions_builder = ContentLoader(
    "app/helpers/questions_manifest.yml",
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

    def setup(self):
        pass

    def tearDown(self):
        pass

    def _get_filter_group_by_label(self, filter_groups, label):
        for filter_group in filter_groups:
            if filter_group['label'] == label:
                return filter_group

    def _get_request_for_params(self, params):
        return Mock(args=MultiDict(params))

    @unittest.skip("until content refactor")
    def test_get_filter_groups_from_questions_with_radio_filters(self):
        filter_groups = questions_builder
        radios_filter_group = self._get_filter_group_by_label(
            filter_groups,
            'Radios example'
        )
        self.assertEqual({
            'label': 'Radios example',
            'depends_on_lots': ['saas', 'paas', 'iaas'],
            'filters': [
                {
                    'label': 'Option 1',
                    'name': 'radiosExample',
                    'id': 'radiosExample-option-1',
                    'value': 'option 1',
                    'lots': ['saas', 'paas', 'iaas']
                },
                {
                    'label': 'Option 2',
                    'name': 'radiosExample',
                    'id': 'radiosExample-option-2',
                    'value': 'option 2',
                    'lots': ['saas', 'paas', 'iaas']
                }
            ]
        }, radios_filter_group)

    @unittest.skip("until content refactor")
    def test_get_filter_groups_from_questions_with_checkbox_filters(self):
        filter_groups = SearchFilters.get_filter_groups_from_questions(
            manifest="tests/fixtures/g6_questions/manifest.yml",
            questions_dir="tests/fixtures/g6_questions/data/"
        )
        checkboxes_filter_group = self._get_filter_group_by_label(
            filter_groups,
            'Checkboxes example'
        )
        self.assertEqual({
            'label': 'Checkboxes example',
            'depends_on_lots': ['saas', 'paas', 'iaas'],
            'filters': [
                {
                    'label': 'Option 1',
                    'name': 'checkboxesExample',
                    'id': 'checkboxesExample-option-1',
                    'value': 'option 1',
                    'lots': ['saas', 'paas', 'iaas']
                },
                {
                    'label': 'Option 2',
                    'name': 'checkboxesExample',
                    'id': 'checkboxesExample-option-2',
                    'value': 'option 2',
                    'lots': ['saas', 'paas', 'iaas']
                }
            ]
        }, checkboxes_filter_group)

    @unittest.skip("until content refactor")
    def test_get_filter_groups_from_questions_with_boolean_filters(self):
        filter_groups = SearchFilters.get_filter_groups_from_questions(
            manifest="tests/fixtures/g6_questions/manifest.yml",
            questions_dir="tests/fixtures/g6_questions/data/"
        )
        booleans_filter_group = self._get_filter_group_by_label(
            filter_groups,
            'Booleans example'
        )
        self.assertEqual({
            'label': 'Booleans example',
            'depends_on_lots': [
                'saas', 'paas', 'saas', 'paas'],
            'filters': [
                {
                    'label': 'Option 1',
                    'name': 'booleanExample1',
                    'id': 'booleanExample1',
                    'value': 'true',
                    'lots': ['saas', 'paas']
                },
                {
                    'label': 'Option 2',
                    'name': 'booleanExample2',
                    'id': 'booleanExample2',
                    'value': 'true',
                    'lots': ['saas', 'paas']
                }
            ]
        }, booleans_filter_group)

    @unittest.skip("until content refactor")
    def test_request_filters_are_set(self):
        search_filters = SearchFilters(
            blueprint=self._get_blueprint_mock(),
            request=self._get_request_for_params({
                'q': 'email',
                'booleanExample1': 'true'
            })
        )

        self.assertIsInstance(search_filters.request_filters, MultiDict)
        self.assertEqual(
            search_filters.request_filters.get('booleanExample1'), 'true')

    @unittest.skip("until content refactor")
    def test_request_filters_strip_out_lot_and_keywords(self):
        search_filters = SearchFilters(
            blueprint=self._get_blueprint_mock(),
            request=self._get_request_for_params({
                'q': 'email',
                'lot': 'saas',
                'booleanExample1': 'true'
            })
        )

        self.assertEqual(
            search_filters.request_filters.get('lot', ''), '')

    @unittest.skip("until content refactor")
    def test_filter_groups_have_correct_default_state(self):
        search_filters = SearchFilters(
            blueprint=self._get_blueprint_mock(),
            request=self._get_request_for_params({
                'q': 'email',
                'lot': 'paas'
            })
        )
        boolean_filter_group = self._get_filter_group_by_label(
            search_filters.filter_groups, 'Booleans example'
        )
        self.assertEqual(
            boolean_filter_group,
            {
                'label': 'Booleans example',
                'depends_on_lots': [
                    'saas', 'paas', 'saas', 'paas'],
                'filters': [
                    {
                        'checked': False,
                        'label': 'Option 1',
                        'name': 'booleanExample1',
                        'id': 'booleanExample1',
                        'value': 'true',
                        'lots': ['saas', 'paas']
                    },
                    {
                        'checked': False,
                        'label': 'Option 2',
                        'name': 'booleanExample2',
                        'id': 'booleanExample2',
                        'value': 'true',
                        'lots': ['saas', 'paas']
                    }
                ]
            }
        )

    @unittest.skip("until content refactor")
    def test_filter_groups_have_correct_state_when_changed(self):
        search_filters = SearchFilters(
            blueprint=self._get_blueprint_mock(),
            request=self._get_request_for_params({
                'q': 'email',
                'lot': 'paas',
                'booleanExample1': 'true'
            })
        )
        boolean_filter_group = self._get_filter_group_by_label(
            search_filters.filter_groups, 'Booleans example'
        )
        self.assertEqual(
            boolean_filter_group,
            {
                'label': 'Booleans example',
                'depends_on_lots': [
                    'saas', 'paas', 'saas', 'paas'],
                'filters': [
                    {
                        'checked': True,
                        'label': 'Option 1',
                        'name': 'booleanExample1',
                        'id': 'booleanExample1',
                        'value': 'true',
                        'lots': ['saas', 'paas']
                    },
                    {
                        'checked': False,
                        'label': 'Option 2',
                        'name': 'booleanExample2',
                        'id': 'booleanExample2',
                        'value': 'true',
                        'lots': ['saas', 'paas']
                    }
                ]
            }
        )

    @unittest.skip("until content refactor")
    def test_lot_filters_work_when_no_lot_is_selected(self):
        search_filters = SearchFilters(
            blueprint=self._get_blueprint_mock(),
            request=self._get_request_for_params({
                'q': 'email'
            })
        )
        self.assertEqual(
            search_filters.lot_filters,
            [
                {
                    'isActive': True,
                    'label': u'All categories',
                    'url': '/g-cloud/search?q=email'
                },
                {
                    'isActive': False,
                    'label': u'Software as a Service',
                    'url': '/g-cloud/search?q=email&lot=saas'
                },
                {
                    'isActive': False,
                    'label': u'Platform as a Service',
                    'url': '/g-cloud/search?q=email&lot=paas'
                },
                {
                    'isActive': False,
                    'label': u'Infrastructure as a Service',
                    'url': '/g-cloud/search?q=email&lot=iaas'
                },
                {
                    'isActive': False,
                    'label': u'Specialist Cloud Services',
                    'url': '/g-cloud/search?q=email&lot=scs'
                }
            ])

    @unittest.skip("until content refactor")
    def test_lot_filters_work_when_a_lot_is_selected(self):
        search_filters = SearchFilters(
            blueprint=self._get_blueprint_mock(),
            request=self._get_request_for_params({
                'q': 'email',
                'lot': 'saas'
            })
        )
        self.assertEqual(
            search_filters.lot_filters,
            [
                {
                    'isActive': False,
                    'label': u'All categories',
                    'url': '/g-cloud/search?q=email'
                },
                {
                    'isActive': True,
                    'label': u'Software as a Service',
                    'url': '/g-cloud/search?q=email&lot=saas'
                },
                {
                    'isActive': False,
                    'label': u'Platform as a Service',
                    'url': '/g-cloud/search?q=email&lot=paas'
                },
                {
                    'isActive': False,
                    'label': u'Infrastructure as a Service',
                    'url': '/g-cloud/search?q=email&lot=iaas'
                },
                {
                    'isActive': False,
                    'label': u'Specialist Cloud Services',
                    'url': '/g-cloud/search?q=email&lot=scs'
                }
            ])

    @unittest.skip("until content refactor")
    def test_instance_has_correct_filter_groups_for_paas(self):
        search_filters = SearchFilters(
            blueprint=self._get_blueprint_mock(),
            request=self._get_request_for_params({
                'q': 'email',
                'lot': 'paas'
            })
        )
        filter_group_labels = [
            group['label'] for group in search_filters.filter_groups]
        self.assertTrue('Booleans example' in filter_group_labels)
        self.assertTrue('Checkboxes example' in filter_group_labels)
        self.assertTrue('Radios example' in filter_group_labels)

    @unittest.skip("until content refactor")
    def test_instance_has_correct_filter_groups_for_iaas(self):
        search_filters = SearchFilters(
            blueprint=self._get_blueprint_mock(),
            request=self._get_request_for_params({
                'q': 'email',
                'lot': 'iaas'
            })
        )
        filter_group_labels = [
            group['label'] for group in search_filters.filter_groups]
        self.assertFalse('Booleans example' in filter_group_labels)
        self.assertTrue('Checkboxes example' in filter_group_labels)
        self.assertTrue('Radios example' in filter_group_labels)
