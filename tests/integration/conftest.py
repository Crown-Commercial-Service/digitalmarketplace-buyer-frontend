from pytest_bdd import given, when, then, parsers
import pytest
import os
import string
import random


DM_FRONTEND_URL = os.getenv('DM_FRONTEND_URL', 'http://localhost:5002/marketplace')
DM_BUYER_EMAIL = os.getenv('DM_BUYER_EMAIL', '')
DM_BUYER_PASSWORD = os.getenv('DM_BUYER_PASSWORD', '')
DM_SUPPLIER_EMAIL = os.getenv('DM_SUPPLIER_EMAIL', '')
DM_SUPPLIER_PASSWORD = os.getenv('DM_SUPPLIER_PASSWORD', '')


def logout(browser):
    browser.visit('{0}{1}'.format(DM_FRONTEND_URL, '/logout'))


def login(browser, email, password):
    logout(browser)
    browser.visit('{0}{1}'.format(DM_FRONTEND_URL, '/login'))
    browser.fill('email_address', email)
    browser.fill('password', password)
    button_click('Log in', browser)


def button_click(text, browser):
    button = browser.find_by_value(text).first
    button.click()


def random_string():
    return ''.join(random.choice(string.lowercase) for x in range(10))


@pytest.fixture(scope='session')
def splinter_webdriver():
    return 'firefox'


@pytest.fixture(scope='session')
def title():
    return random_string()


@given(parsers.parse("I am on the {page} page"))
def visit_page(page, browser):
    browser.visit('{0}{1}'.format(DM_FRONTEND_URL, page))


@given(parsers.parse("I am an anonymous user"))
def anonymous_user(browser):
    logout(browser)


@given(parsers.parse("I am a Buyer"))
def buyer_user(browser):
    login(browser, DM_BUYER_EMAIL, DM_BUYER_PASSWORD)


@given(parsers.parse("I am a Supplier"))
def supplier_user(browser):
    login(browser, DM_SUPPLIER_EMAIL, DM_SUPPLIER_PASSWORD)


@when(parsers.parse('I click the {link_text} link'))
def click_link(link_text, browser):
    browser.click_link_by_text(link_text)


@when(parsers.parse('I click the {button_text} button'))
def click_button(button_text, browser):
    button_click(button_text, browser)


@then(parsers.parse('I should see the {title} page'))
def page_verify(title, browser):
    assert browser.title == title


@then(parsers.parse('I should see {text} text'))
def text_verify(text, browser):
    assert browser.is_element_present_by_text(text)
