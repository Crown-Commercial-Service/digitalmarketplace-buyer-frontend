from ...helpers import BaseApplicationTest
import mock
from lxml import html


class TestBuyerDashboard(BaseApplicationTest):
    @mock.patch('app.buyers.views.buyers.data_api_client')
    def test_buyer_dashboard(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.find_briefs.return_value = {
                "briefs": [
                    {"status": "draft",
                     "title": "A draft brief",
                     "createdAt": "2016-02-02T00:00:00.000000Z"},
                    {"status": "live",
                     "title": "A live brief",
                     "createdAt": "2016-02-01T00:00:00.000000Z",
                     "publishedAt": "2016-02-04T12:00:00.000000Z"},
                ]
            }

            res = self.client.get("/buyers")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            tables = document.xpath('//table')
            draft_row = [cell.text_content().strip() for cell in tables[0].xpath('.//tbody/tr/td')]
            assert draft_row[0] == "A draft brief"
            assert draft_row[1] == "Tuesday 02 February 2016"

            live_row = [cell.text_content().strip() for cell in tables[1].xpath('.//tbody/tr/td')]
            assert live_row[0] == "A live brief"
            assert live_row[1] == "Thursday 04 February 2016"
