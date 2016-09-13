from pytest_bdd import scenario, given, when, then, parsers
from helpers import save_and_continue, create_brief, visit_page


@scenario('build_brief.feature', 'Anonymous users cannot create brief')
def test_anonymous_build_brief():
    pass


@scenario('build_brief.feature', 'Suppliers cannot create brief')
def test_supplier_build_brief():
    pass


@scenario('build_brief.feature', 'Buyers can create a brief')
def test_buyer_create_brief():
    pass


@scenario('build_brief.feature', 'Select a digital specialist for your brief')
def test_select_digital_specialist():
    pass


@scenario('build_brief.feature', 'Select a location for your brief')
def test_select_location():
    pass


@scenario('build_brief.feature', 'Enter the Description of work for your brief')
def test_enter_work():
    pass


@scenario('build_brief.feature', 'Enter the Evaluation process for your brief')
def test_enter_eval():
    pass


@scenario('build_brief.feature', 'Select how long your brief will be open')
def test_how_long():
    pass


@scenario('build_brief.feature', 'Select who can respond')
def test_who_can_respond():
    pass


@scenario('build_brief.feature', 'Review and publish your requirements')
def test_publish_brief():
    pass


@given(parsers.parse('I have created a brief'))
def verify_brief(title, browser):
    visit_page('/buyers', browser)
    if browser.is_text_present(title):
        browser.click_link_by_text(title)
    else:
        create_brief(title, browser)


@when(parsers.parse('I enter {input_text} into {input_names}'))
def enter_text(input_text, input_names, browser):
    for text, input in zip(input_text.split(','), input_names.split(',')):
        browser.fill(input, text)
    save_and_continue(browser)


@when('I select an option in the list')
def select_digital_specialist(browser):
    specialists = browser.find_by_xpath('//fieldset/label')
    specialists.first.click()


@then('I should see the Overview')
def verify_overview(title, browser):
    assert browser.title.startswith(title)
