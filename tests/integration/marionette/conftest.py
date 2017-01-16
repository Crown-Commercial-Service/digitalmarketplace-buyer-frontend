from marionette_driver.marionette import Marionette
import pytest


@pytest.fixture(scope="session")
def client():
    client = Marionette(host='localhost', port=2828)
    client.start_session()
    return client
