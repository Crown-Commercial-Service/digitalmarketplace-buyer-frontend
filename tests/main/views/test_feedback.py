from lxml import html

import mock
from ...helpers import BaseApplicationTest


class TestFeedbackForm(BaseApplicationTest):
    def _post(self):
        return self.client.post('/feedback', data={
            'uri': 'test:some-uri',
            'what_doing': 'what doing text',
            'what_happened': 'what happened text'})

    def _check_success(self, response):
        # The idea here is that the user will know only success, even if due to some failure we end up logging their
        # feedback rather than recording it properly.
        assert response.status_code == 303
        new_page = self.client.get(response.location)
        assert "Thank you for your message" in new_page.get_data(as_text=True)

    @mock.patch('requests.post')
    @mock.patch('flask.Flask.logger')
    def test_google_gone_logs_problem(self, logger, external_requests_post):
        external_requests_post.return_value.status_code = 404
        self._check_success(self._post())
        logger.warning.assert_called_once_with(
            'Feedback message was not correctly recorded: test:some-uri / what doing text / what happened text')

    @mock.patch('requests.post')
    def test_feedback_submission(self, external_requests_post):
        external_requests_post.return_value.status_code = 200
        self._check_success(self._post())

    def test_feedback_form_has_csrf(self):
        res = self.client.get("/")
        document = html.fromstring(res.get_data(as_text=True))

        assert len(document.cssselect('.report-a-problem-container form input[name="csrf_token"]')) == 1
