from pytest_bdd import scenario, given, when, then, parsers
from helpers import save_and_continue, create_brief, visit_page


@scenario('home_page.feature', 'Anonymous users can click Dashboard opportunities')
def test_dashboard_opportunities():
    pass


@scenario('home_page.feature', 'Anonymous users can click Dashboard sellers')
def test_dashboard_sellers():
    pass


@scenario('home_page.feature', 'Anonymous users can click Dashboard buyers')
def test_dashboard_buyers():
    pass
