from pytest_bdd import scenario, given, when, then, parsers


@scenario('catalogue.feature', 'Navigate to search page')
def test_catalogue():
    pass


@scenario('catalogue.feature', 'Anonymous users cannot view supplier details')
def test_anonymous_supplier_details():
    pass


@scenario('catalogue.feature', 'Buyers can view supplier details')
def test_buyers_supplier_details():
    pass


@when(parsers.parse('I click the first supplier link'))
def click_supplier_link(browser):
    links = browser.find_by_xpath('//li[@class="supplier-result"]/article/h2/a')
    links.first.click()
