from lxml import html

import mock
from ...helpers import BaseApplicationTest


class TestFeedbackForm(BaseApplicationTest):
    def _post(self):
        return self.client.post('/feedback', data={
            'uri': 'test:some-uri',
            'what_doing': 'test: what doing text',
            'what_happened': 'test: what happened text'})

    @mock.patch('requests.post')
    def test_google_gone_gives_503(self, external_requests_post):
        assert self._post().status_code == 503

    @mock.patch('requests.post')
    def test_feedback_submission(self, external_requests_post):
        external_requests_post.return_value.status_code = 200
        response = self._post()

        assert response.status_code == 303
        new_page = self.client.get(response.location)
        assert "Thank you for your message" in new_page.get_data(as_text=True)

    def test_feedback_form_has_csrf(self):
        res = self.client.get("/")
        document = html.fromstring(res.get_data(as_text=True))

        assert len(document.cssselect('.report-a-problem-container form input[name="csrf_token"]')) == 1

    @mock.patch('requests.post')
    def test_feedback_form_fail(self, external_requests_post):
        external_requests_post.return_value.status_code = 404
        response = self._post()

        assert response.status_code == 503
