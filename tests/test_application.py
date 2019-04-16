from .helpers import BaseApplicationTest, BaseAPIClientMixin


class DataAPIClientMixin(BaseAPIClientMixin):
    data_api_client_patch_path = 'app.main.views.marketplace.data_api_client'


class TestApplication(DataAPIClientMixin, BaseApplicationTest):
    def test_index(self):
        response = self.client.get('/')
        assert 200 == response.status_code
        assert len(self.data_api_client.find_frameworks.call_args_list) == 2

    def test_404(self):
        response = self.client.get('/not-found')
        assert 404 == response.status_code

    def test_trailing_slashes(self):
        response = self.client.get('')
        assert 308 == response.status_code
        assert "http://localhost/" == response.location
        response = self.client.get('/trailing/')
        assert 301 == response.status_code
        assert "http://localhost/trailing" == response.location

    def test_trailing_slashes_with_query_parameters(self):
        response = self.client.get('/search/?q=r&s=t')
        assert 301 == response.status_code
        assert "http://localhost/search?q=r&s=t" == response.location

    def test_header_xframeoptions_set_to_deny(self):
        res = self.client.get('/')
        assert 200 == res.status_code
        assert 'DENY', res.headers['X-Frame-Options']
