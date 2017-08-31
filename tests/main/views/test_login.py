from ...helpers import BaseApplicationTest


class TestCreateUser(BaseApplicationTest):
    def test_should_redirect_to_the_user_frontend_app(self):
        res = self.client.get('/create-user/1234567890')
        assert res.status_code == 301
        assert res.location == 'http://localhost/user/create/1234567890'
