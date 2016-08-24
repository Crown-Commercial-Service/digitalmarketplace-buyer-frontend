import pytest
import os


@pytest.fixture(scope='session')
def splinter_webdriver():
    return 'phantomjs'


config = {'dm_frontend_url': os.getenv('DM_FRONTEND_URL', 'http://localhost:5002/marketplace')}
