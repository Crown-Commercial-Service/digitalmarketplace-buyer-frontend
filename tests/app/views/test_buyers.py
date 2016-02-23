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
                     "createdAt": "2016-02-02T00:00:00.000000Z",
                     "frameworkSlug": "digital-outcomes-and-specialists"},
                    {"status": "live",
                     "title": "A live brief",
                     "createdAt": "2016-02-01T00:00:00.000000Z",
                     "publishedAt": "2016-02-04T12:00:00.000000Z",
                     "frameworkSlug": "digital-outcomes-and-specialists"},
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

    def test_404_if_lot_does_not_exist(self, data_api_client):
        with self.app.app_context():
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
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-octopuses/create")

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
                "title": "My title"
            })

        assert res.status_code == 302
        data_api_client.create_brief.assert_called_with('digital-outcomes-and-specialists',
                                                        'digital-specialists',
                                                        123,
                                                        {'title': "My title"},
                                                        page_questions=['title'],
                                                        updated_by='buyer@email.com'
                                                        )

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

    def test_404_if_lot_does_not_exist(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='open',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-octopuses/create",
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
                "title": "My title"
            })
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 400
        anchor = document.cssselect('div.validation-masthead a[href="#title"]')

        assert len(anchor) == 1
        assert "Requirements title" in anchor[0].text_content().strip()
        data_api_client.create_brief.assert_called_with('digital-outcomes-and-specialists',
                                                        'digital-specialists',
                                                        123,
                                                        {'title': "My title"},
                                                        page_questions=['title'],
                                                        updated_by='buyer@email.com'
                                                        )


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

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1/edit/your-organisation")

        assert res.status_code == 404

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

    def test_404_if_lot_does_not_exist(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-octopuses"
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
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/your-organisation",
            data={
                "organisation": "GDS"
            })

        assert res.status_code == 302
        data_api_client.update_brief.assert_called_with('1234',
                                                        {"organisation": "GDS"},
                                                        page_questions=['organisation'],
                                                        updated_by='buyer@email.com'
                                                        )

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/your-organisation",
            data={
                "organisation": "GDS"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called

    def test_404_if_lot_does_not_allow_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/your-organisation",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called

    def test_404_if_lot_does_not_exist(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-octopuses/1234/edit/your-organisation",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called

    def test_404_if_framework_status_is_not_live(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='open',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/your-organisation",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called

    def test_404_if_brief_is_already_live(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(status='live')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/your-organisation",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called

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

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/some-made-up-section",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called


@mock.patch('app.buyers.views.buyers.data_api_client')
class TestStartBriefInfoPage(BaseApplicationTest):
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

    def test_404_if_framework_status_is_not_live_(self, data_api_client):
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


@mock.patch('app.buyers.views.buyers.data_api_client')
class TestDeleteBriefSubmission(BaseApplicationTest):
    def test_delete_brief_submission_click_delete_button(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/delete",
            data={})

        assert res.status_code == 302
        assert not data_api_client.delete_brief.called
        assert res.location == "http://localhost/buyers/frameworks/digital-outcomes-and-specialists/requirements/" \
                               "digital-specialists/1234?delete_requested=True"

    def test_delete_brief_submission_click_confirm_delete_button(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/delete",
            data={"delete_confirmed": True})

        data_api_client.delete_brief.assert_called_with('1234', 'buyer@email.com')
        assert res.status_code == 302
        assert res.location == "http://localhost/buyers"
        self.assert_flashes('requirements_deleted')

    def test_404_if_framework_is_not_live(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='standstill',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/delete",
            data={"delete_confirmed": True})

        assert res.status_code == 404

    def test_404_if_framework_does_not_allow_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/delete",
            data={"delete_confirmed": True})

        assert res.status_code == 404

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/delete",
            data={"delete_confirmed": True})

        assert res.status_code == 404


@mock.patch('app.buyers.views.buyers.data_api_client')
class TestBriefSummaryPage(BaseApplicationTest):
    def test_show_brief_summary_page(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief()
            brief_json['briefs']['specialistRole'] = 'communications_manager'
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1"
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            document = html.fromstring(page_html)

            assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"

            last_update = document.cssselect('p.last-edited')
            assert self._strip_whitespace(last_update[0].text_content()) == "Lastedited:Tuesday29March2016at11:11"

            hint = document.cssselect('span.move-to-complete-hint')
            assert hint[0].text_content().strip() == "12 unanswered questions"

            assert 'communications_manager' not in page_html
            assert 'Communications manager' in page_html

    def test_404_if_framework_is_not_live(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='pending',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1"
            )

            assert res.status_code == 404

    def test_404_if_framework_does_not_allow_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=False),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1"
            )

            assert res.status_code == 404

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1"
            )

            assert res.status_code == 404
