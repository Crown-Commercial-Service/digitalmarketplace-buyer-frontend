from marionette_driver import Wait, expected
from helpers import go_home


def test_view_briefs(client):
    go_home(client)
    link = client.find_element('id', 'opportunities__call-to-action')
    link.click()
    Wait(client).until(expected.elements_present('class name', 'brief-result'))


def test_view_catalogue(client):
    go_home(client)
    link = client.find_element('id', 'catalogue__call-to-action')
    link.click()
    Wait(client).until(expected.elements_present('class name', 'supplier-result'))


def test_register_buyer(client):
    go_home(client)
    link = client.find_element('id', 'buyer__call-to-action')
    link.click()
    Wait(client).until(expected.element_present('id', 'employment_status'))
