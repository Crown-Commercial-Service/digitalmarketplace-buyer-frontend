import pytest
from app.main.helpers.shared_helpers import construct_url_from_base_and_params


@pytest.mark.parametrize('expected_url,base_url,query_params',
                         (
                             ('http://localhost',
                              'http://localhost',
                              tuple()),
                             ('https://www.digitalmarketplace.service.gov.uk',
                              'https://www.digitalmarketplace.service.gov.uk',
                              tuple()),
                             ('https://www.digitalmarketplace.service.gov.uk/g-cloud/search',
                              'https://www.digitalmarketplace.service.gov.uk/g-cloud/search',
                              tuple()),
                             ('https://www.digitalmarketplace.service.gov.uk/g-cloud/search?q=security',
                              'https://www.digitalmarketplace.service.gov.uk/g-cloud/search',
                              (('q', 'security'),)),
                             ('http://localhost?q=hosting&lot=cloud-hosting&serviceCategories=cloud',
                              'http://localhost',
                              (('q', 'hosting'), ('lot', 'cloud-hosting'), ('serviceCategories', 'cloud'))),
                         ))
def test_construct_url_from_base_and_params(expected_url, base_url, query_params):
    assert construct_url_from_base_and_params(base_url, query_params) == expected_url
