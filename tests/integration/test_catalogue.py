from pytest_bdd import scenario, given, when, then, parsers
from conftest import config


@scenario('catalogue.feature', 'Navigate to search page')
def test_catalogue():
    pass


@given("I am on the home page")
def home_page(browser):
    print config
    browser.visit(config['dm_frontend_url'])


@when(parsers.parse('I click the {link_text} link'))
def click_link(link_text, browser):
    browser.click_link_by_text(link_text)


@then(parsers.parse('I should see the {title} page'))
def page_verify(title, browser):
    assert browser.title == title
