from nose.tools import assert_equal, assert_false, assert_true
from werkzeug.datastructures import MultiDict

from app.helpers import search_helpers


def test_should_show_pagination():
    assert_true(search_helpers.pagination(101, 100)["show_pagination"])


def test_should_hide_pagination():
    assert_false(search_helpers.pagination(99, 100)["show_pagination"])


def test_should_indicate_valid_page():
    assert_false(search_helpers.pagination(101, 100, 2)["pagination_error"])


def test_should_indicate_invalid_page():
    assert_true(search_helpers.pagination(101, 100, 3)["pagination_error"])


def test_should_hide_both_next_and_prev_if_less_services_than_page():
    assert_false(search_helpers.pagination(50, 100)["show_prev"])
    assert_false(search_helpers.pagination(50, 100)["show_next"])


def test_should_hide_prev_if_page_one():
    assert_false(search_helpers.pagination(101, 100)["show_prev"])


def test_should_show_prev_if_after_page_one():
    assert_true(search_helpers.pagination(101, 100, 2)["show_prev"])


def test_show_next():
    assert_true(search_helpers.pagination(101, 100,)["show_next"])
    assert_true(search_helpers.pagination(101, 100, 1)["show_next"])


def test_hide_next_if_last_page():
    assert_false(search_helpers.pagination(101, 100, 2)["show_next"])


def test_set_total_pages():
    assert_equal(search_helpers.pagination(99, 100)["total_pages"], 1)
    assert_equal(search_helpers.pagination(100, 100)["total_pages"], 1)
    assert_equal(search_helpers.pagination(101, 100)["total_pages"], 2)


def test_should_set_next_page():
    assert_equal(search_helpers.pagination(99, 100)["next_page"], None)
    assert_equal(search_helpers.pagination(101, 100)["next_page"], 2)
    assert_equal(search_helpers.pagination(201, 100, 2)["next_page"], 3)


def test_should_set_next_page():
    assert_equal(search_helpers.pagination(99, 100)["prev_page"], None)
    assert_equal(search_helpers.pagination(101, 100, 2)["prev_page"], 1)
    assert_equal(search_helpers.pagination(301, 100, 3)["prev_page"], 2)


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
