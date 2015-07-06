import mock

from nose.tools import assert_equal, assert_false, assert_true
from werkzeug.datastructures import MultiDict

from app.helpers import search_helpers


def test_should_hide_both_next_and_prev_if_no_services():
    assert_false(search_helpers.pagination(0, 100)["show_prev"])
    assert_false(search_helpers.pagination(0, 100)["show_next"])


def test_should_hide_both_next_and_prev_if_less_services_than_page():
    assert_false(search_helpers.pagination(50, 100)["show_prev"])
    assert_false(search_helpers.pagination(50, 100)["show_next"])


def test_should_hide_prev_if_page_one():
    assert_false(search_helpers.pagination(101, 100)["show_prev"])


def test_should_show_prev_if_after_page_one():
    assert_true(search_helpers.pagination(101, 100, 2)["show_prev"])


def test_should_show_prev_if_last_page():
    assert_true(search_helpers.pagination(201, 100, 2)["show_prev"])


def test_show_next():
    assert_true(search_helpers.pagination(101, 100,)["show_next"])
    assert_true(search_helpers.pagination(101, 100, 1)["show_next"])


def test_hide_next_if_last_page():
    assert_false(search_helpers.pagination(101, 100, 2)["show_next"])


def test_show_prev_as_last_page_if_too_big_page():
    assert_true(search_helpers.pagination(101, 100, 20)["show_prev"])


def test_set_total_pages():
    assert_equal(search_helpers.pagination(99, 100)["total_pages"], 1)
    assert_equal(search_helpers.pagination(100, 100)["total_pages"], 1)
    assert_equal(search_helpers.pagination(101, 100)["total_pages"], 2)


def test_should_set_next_page():
    assert_equal(search_helpers.pagination(99, 100)["next_page"], None)
    assert_equal(search_helpers.pagination(101, 100)["next_page"], 2)
    assert_equal(search_helpers.pagination(201, 100, 2)["next_page"], 3)


def test_should_set_prev_page():
    assert_equal(search_helpers.pagination(99, 100)["prev_page"], None)
    assert_equal(search_helpers.pagination(101, 100, 2)["prev_page"], 1)
    assert_equal(search_helpers.pagination(301, 100, 3)["prev_page"], 2)
    assert_equal(search_helpers.pagination(301, 100, 100)["prev_page"], 4)


def test_should_strip_page_from_multidict():
    params = MultiDict()
    params.add("this", "that")
    params.add("page", 100)

    parsed = search_helpers.query_args_for_pagination(params)
    assert_equal(parsed['this'], 'that')
    assert_false('page' in parsed)


def test_should_calculate_correct_page_total():
    cases = [
        (1, 1),
        (100, 1),
        (101, 2),
        (200, 2),
        (201, 3),
        (1001, 11),
        (0, 1)
    ]

    for test, expected in cases:
        yield \
            assert_equal, \
            search_helpers.total_pages(test, 100), \
            expected, \
            test


def test_should_reject_invalid_page():
    cases = [
        (1, 1),
        (100, 100),
        (-1, None),
        ("aa", None),
    ]

    for test, expected in cases:
        yield \
            assert_equal, \
            search_helpers.valid_page(test), \
            expected, \
            test


class TestBuildSearchQueryHelpers(object):
    def setUp(self):
        self.lot_filters = [
            {'label': 'section1', 'filters': [
                {'name': 'question1', 'value': 'true'},
                {'name': 'question2', 'value': 'true'},
                {'name': 'question3', 'value': 'option1'},
                {'name': 'question3', 'value': 'option2'},
                {'name': 'question3', 'value': 'option3'},
            ]},
            {'label': 'section2', 'filters': [
                {'name': 'question4', 'value': 'true'},
                {'name': 'question5', 'value': 'true'},
                {'name': 'question6', 'value': 'option1'},
                {'name': 'question6', 'value': 'option2'},
                {'name': 'question6', 'value': 'option3'},
            ]},
        ]

    def _request(self, params):
        return mock.Mock(args=MultiDict(params))

    def _loader(self, question_types=None):
        question_types = question_types or {
            'question1': {'type': 'boolean'},
            'question4': {},
            'question3': {'type': 'radios'},
            'question6': {'type': 'checkboxes'},
            'page': {},
            'lot': {},
            'q': {},
        }

        def _mock_get_question(question):
            return question_types[question]

        loader = mock.Mock()
        loader.get_question = _mock_get_question

        return loader

    def test_get_filters_from_request(self):
        request = self._request({
            'q': '',
            'page': 1,
            'someFilter': 'filter',
            'otherFilter': [1, 2]
        })

        assert_equal(
            search_helpers.get_filters_from_request(request).to_dict(False),
            {
                'someFilter': ['filter'],
                'otherFilter': [1, 2]
            }
        )

    def test_allowed_request_lot_filters(self):
        assert_equal(
            search_helpers.allowed_request_lot_filters(self.lot_filters),
            {
                ('question1', 'true'),
                ('question2', 'true'),
                ('question3', 'option1'),
                ('question3', 'option2'),
                ('question3', 'option3'),
                ('question4', 'true'),
                ('question5', 'true'),
                ('question6', 'option1'),
                ('question6', 'option2'),
                ('question6', 'option3'),
            }
        )

    def test_clean_request_args(self):
        filters = MultiDict({
            'question1': 'true',
            'question2': ['true', 'false', 1],
            'question3': ['option1', 'true', 'option5', 'option2', 2, None],
            'question6': '',
            'question4': 'false',
            'lot': 'saas',
            'q': 'email',
            'page': 9,
            'unknown': 'key',
        })

        assert_equal(
            search_helpers.clean_request_args(filters, self.lot_filters),
            MultiDict({
                'question1': 'true',
                'question2': 'true',
                'question3': ['option1', 'option2'],
                'page': 'false',
                'q': 'email',
                'lot': 'saas',
                'page': 9,
            })
        )

    def test_clean_request_args_incorrect_lot(self):
        filters = MultiDict({
            'lot': 'saaspaas',
        })

        assert_equal(
            search_helpers.clean_request_args(filters, self.lot_filters),
            MultiDict({})
        )

    def test_group_request_filters(self):
        filters = MultiDict({
            'question1': 'true',
            'question3': ['option1', 'option2'],
            'question4': 'true',
            'question6': ['option1', 'option3'],
        })

        assert_equal(
            search_helpers.group_request_filters(filters, self._loader()),
            {
                'question1': 'true',
                'question4': 'true',
                'question3': 'option1,option2',
                'question6': ['option1', 'option3'],
            }
        )

    def test_build_search_query(self):
        request = self._request({
            'page': 5,
            'q': 'email',
            'non': 1,
            'newkey': 'true',
            'lot': 'saas',
            'question1': 'true',
            'question3': ['option1', 'option2'],
            'question4': 'true',
            'question6': ['option1', 'option3'],
        })

        assert_equal(
            search_helpers.build_search_query(
                request, self.lot_filters, self._loader()),
            {
                'page': 5,
                'q': 'email',
                'lot': 'saas',
                'question1': 'true',
                'question4': 'true',
                'question3': 'option1,option2',
                'question6': ['option1', 'option3'],
            }
        )

    def test_build_search_query_unknown_lot(self):
        request = self._request({
            'lot': 'saasaas',
        })

        assert_equal(
            search_helpers.build_search_query(
                request, self.lot_filters, self._loader()),
            {}
        )

    def test_build_search_query_multiple_lots(self):
        request = self._request({
            'lot': 'saas,paas',
        })

        assert_equal(
            search_helpers.build_search_query(
                request, self.lot_filters, self._loader()),
            {}
        )

    def test_build_search_query_no_keywords(self):
        request = self._request({
            'q': '',
        })

        assert_equal(
            search_helpers.build_search_query(
                request, self.lot_filters, self._loader()),
            {}
        )

    def test_build_search_query_no_page(self):
        request = self._request({
            'page': '',
        })

        assert_equal(
            search_helpers.build_search_query(
                request, self.lot_filters, self._loader()),
            {}
        )
