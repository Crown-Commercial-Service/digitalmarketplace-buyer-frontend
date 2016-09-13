from pytest_bdd import given, when, then, parsers
import pytest
from config import config
from helpers import random_string, login, logout, click_button, delete_brief, visit_page, click_link, enter_title


@pytest.fixture(scope='session')
def splinter_webdriver():
    return 'firefox'


@pytest.fixture(scope='session')
def title(request):
    title = random_string()

    def fin():
        delete_brief(title)

    request.addfinalizer(fin)
    return title


@given(parsers.parse("I am on the {page} page"))
def given_page(page, browser):
    visit_page(page, browser)


@given(parsers.parse("I am an anonymous user"))
def anonymous_user(browser):
    logout(browser)


@given(parsers.parse("I am a Buyer"))
def buyer_user(browser):
    login(browser, config['DM_BUYER_EMAIL'], config['DM_BUYER_PASSWORD'])


@given(parsers.parse("I am a Supplier"))
def supplier_user(browser):
    login(browser, config['DM_SUPPLIER_EMAIL'], config['DM_SUPPLIER_PASSWORD'])


@when(parsers.parse('I click the {link_text} link'))
def click_link_fixture(link_text, browser):
    click_link(link_text, browser)


@when(parsers.parse('I click the {button_text} button'))
def click_button_fixture(button_text, browser):
    click_button(button_text, browser)


@when('I enter a title')
def enter_title_fixture(title, browser):
    enter_title(title, browser)


@then(parsers.parse('I should see the {title} page'))
def page_verify(title, browser):
    assert browser.title == title


@then(parsers.parse('I should see {text} text'))
def text_verify(text, browser):
    assert browser.is_element_present_by_text(text)
