from nose.tools import assert_equal, assert_false
from werkzeug.datastructures import MultiDict

from app.helpers import search_helpers


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
        (0, None),
        (None, None)
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