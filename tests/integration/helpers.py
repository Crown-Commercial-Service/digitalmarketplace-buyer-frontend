from config import config
import string
import random
import requests
import json


def random_string():
    return ''.join(random.choice(string.lowercase) for x in range(20))


def logout(browser):
    browser.visit('{0}{1}'.format(config['DM_FRONTEND_URL'], '/logout'))


def login(browser, email, password):
    logout(browser)
    browser.visit('{0}{1}'.format(config['DM_FRONTEND_URL'], '/login'))
    browser.is_element_present_by_name('email_address')
    browser.fill('email_address', email)
    browser.fill('password', password)
    click_button('Log in', browser)
    wait_for_page('Dashboard', browser)


def click_button(text, browser):
    button = browser.find_by_value(text).first
    button.click()


def save_and_continue(browser):
    click_button('Save and continue', browser)


def click_link(link_text, browser):
    browser.click_link_by_text(link_text)


def click_text(text, browser):
    element = browser.find_by_text(text)
    element.click()


def visit_page(page, browser):
    browser.visit('{0}{1}'.format(config['DM_FRONTEND_URL'], page))


def enter_title(title, browser):
    browser.fill('title', title)


def create_brief(title, browser):
    visit_page('/', browser)
    click_link('Find an individual specialist', browser)
    wait_for_page('Research, write and publish your brief', browser)
    click_button('Create brief', browser)
    wait_for_page('Create a title for your brief', browser)
    enter_title(title, browser)
    click_button('Save and continue', browser)
    wait_for_page('quick and easy to publish a brief', browser)


def delete_brief(title):
    headers = {'Authorization': 'Bearer {}'.format(config['DM_DATA_API_AUTH_TOKEN']),
               'Content-type': 'application/json'}
    get_briefs = requests.get('{}/briefs?per_page=1000'.format(config['DM_DATA_API_URL']), headers=headers)
    get_briefs.raise_for_status()
    briefs = [b for b in get_briefs.json()['briefs'] if b['title'] == title]
    if briefs:
        requests.delete('{}/briefs/{}'.format(config['DM_DATA_API_URL'], briefs[0]['id']), headers=headers,
                        data=json.dumps({'updated_by': ''}))


def wait_for_page(page_text, browser):
    for i in range(0, 3):
        try:
            result = browser.is_text_present(page_text)
        except Exception as exception:
            if type(exception).__name__ == 'StaleElementReferenceException':
                continue
            raise
        assert result
        break
