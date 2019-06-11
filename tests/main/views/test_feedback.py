from ...helpers import BaseApplicationTest


class TestFeedbackForm(BaseApplicationTest):
    def test_feedback_submission_results_in_410_gone(self):
        response = self.client.post(
            "/feedback",
            data={
                "uri": "test:some-uri",
                "what_doing": "what doing text",
                "what_happened": "what happened text",
            },
        )

        assert response.status_code == 410
