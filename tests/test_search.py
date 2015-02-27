from .helpers import BaseApplicationTest


class TestApplication(BaseApplicationTest):
    def test_search_with_query(self):
        response = self.client.get('/search?q=email')
        assert 200 == response.status_code

    def test_search_with_query_and_lot(self):
        response = self.client.get('/search?q=email&lot=saas')
        assert 200 == response.status_code

    def test_search_with_query_and_filters(self):
        response = self.client.get('/search?q=email&elasticCloud=True')
        assert 200 == response.status_code
