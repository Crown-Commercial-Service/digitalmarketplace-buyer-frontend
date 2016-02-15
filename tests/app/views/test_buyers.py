from ...helpers import BaseApplicationTest
from dmapiclient import api_stubs, HTTPError
import mock
from lxml import html


@mock.patch('app.buyers.views.buyers.data_api_client')
class TestBuyerDashboard(BaseApplicationTest):
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


@mock.patch('app.buyers.views.buyers.data_api_client')
class TestStartNewBrief(BaseApplicationTest):
    def test_show_start_brief_page(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create")

            assert res.status_code == 200

    def test_404_if_lot_does_not_allow_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=False)
                ]
            )

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create")

            assert res.status_code == 404

    def test_404_if_framework_status_is_not_live(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='open',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create")

            assert res.status_code == 404


@mock.patch('app.buyers.views.buyers.data_api_client')
class TestCreateNewBrief(BaseApplicationTest):
    def test_create_new_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create",
            data={
                "title": ""
            })

        assert res.status_code == 302
        assert data_api_client.create_brief.called

    def test_404_if_lot_does_not_allow_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='open',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create",
            data={
                "title": "My title"
            })

        assert res.status_code == 404
        assert not data_api_client.create_brief.called

    def test_404_if_framework_status_is_not_live(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='open',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create",
            data={
                "title": "My title"
            })

        assert res.status_code == 404
        assert not data_api_client.create_brief.called

    def test_400_if_form_error(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.create_brief.side_effect = HTTPError(
            mock.Mock(status_code=400),
            {"title": "answer_required"})

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create",
            data={
                "title": ""
            })
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 400
        anchor = document.cssselect('div.validation-masthead a[href="#title"]')

        assert len(anchor) == 1
        assert "Requirements title" in anchor[0].text_content().strip()
        assert data_api_client.create_brief.called


@mock.patch('app.buyers.views.buyers.data_api_client')
class TestEditBriefSubmission(BaseApplicationTest):
    def test_edit_brief_submission(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1/edit/your-organisation")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        assert document.xpath('//h1')[0].text_content().strip() == "Your organisation"

    def test_404_if_lot_does_not_allow_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False)
            ]
        )

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1/edit/your-organisation")

        assert res.status_code == 404

    def test_404_if_framework_status_is_not_live(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='open',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1/edit/your-organisation")

        assert res.status_code == 404

    def test_404_if_brief_has_published_status(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(status='published')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1/edit/your-organisation")

        assert res.status_code == 404

    def test_404_if_section_does_not_exist(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1/edit/not-a-real-section")

        assert res.status_code == 404


@mock.patch('app.buyers.views.buyers.data_api_client')
class TestUpdateBriefSubmission(BaseApplicationTest):
    def test_update_brief_submission(self, data_api_client):
        pass

    def test_404_if_lot_does_not_allow_brief(self, data_api_client):
        pass

    def test_404_if_framework_status_is_not_live(self, data_api_client):
        pass

    def test_404_if_brief_has_published_state(self, data_api_client):
        pass

    def test_404_if_section_does_not_exist(self, data_api_client):
        pass


class TestStartBriefInfoPage(BaseApplicationTest):
    @mock.patch('app.buyers.views.buyers.data_api_client')
    def test_show_start_brief_info_page(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists")
            assert res.status_code == 200
            document = html.fromstring(res.get_data(as_text=True))
            assert document.xpath('//h1')[0].text_content().strip() == "Find an individual specialist"

    @mock.patch('app.buyers.views.buyers.data_api_client')
    def test_404_if_lot_does_not_allow_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=False)
                ]
            )

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists")
            assert res.status_code == 404

    @mock.patch('app.buyers.views.buyers.data_api_client')
    def test_404_if_framework_status_is_not_live_1(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='open',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists")
            assert res.status_code == 404
