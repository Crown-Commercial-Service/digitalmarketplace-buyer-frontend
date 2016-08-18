# coding: utf-8
from __future__ import unicode_literals

from ...helpers import BaseApplicationTest
from dmapiclient import api_stubs, HTTPError
from dmcontent.content_loader import ContentLoader
import mock
from lxml import html
import pytest


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
            assert draft_row[1] == "Tuesday 2 February 2016"

            live_row = [cell.text_content().strip() for cell in tables[1].xpath('.//tbody/tr/td')]
            assert live_row[0] == "A live brief"
            assert live_row[1] == "Thursday 4 February 2016"


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
    def test_create_new_digital_specialists_brief(self, data_api_client):
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
                "title": "Title"
            })

        assert res.status_code == 302
        data_api_client.create_brief.assert_called_with(
            'digital-outcomes-and-specialists',
            'digital-specialists',
            123,
            {'title': "Title"},
            page_questions=['title'],
            updated_by='buyer@email.com'
        )

    def test_create_new_digital_outcomes_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/create",
            data={
                "title": "Title"
            })

        assert res.status_code == 302
        data_api_client.create_brief.assert_called_with(
            'digital-outcomes-and-specialists',
            'digital-outcomes',
            123,
            {'title': "Title"},
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
                "specialistRole": "agileCoach"
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
                "specialistRole": "agileCoach"
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
                "specialistRole": "agileCoach"
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
                "title": "Title"
            })
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 400
        anchor = document.cssselect('div.validation-masthead a[href="#title"]')

        assert len(anchor) == 1
        assert "Title" in anchor[0].text_content().strip()
        data_api_client.create_brief.assert_called_with(
            'digital-outcomes-and-specialists',
            'digital-specialists',
            123,
            {'title': "Title"},
            page_questions=['title'],
            updated_by='buyer@email.com'
        )


class TestEveryDamnPage(BaseApplicationTest):

    # @mock.patch("app.buyers.views.buyers.content_loader")
    def _load_page(self, url, status_code, method='get', data=None):
        data = {} if data is None else data
        baseurl = "/buyers/frameworks/digital-outcomes-and-specialists/requirements"

        with mock.patch('app.buyers.views.buyers.content_loader') as content_loader, \
                mock.patch('app.buyers.views.buyers.data_api_client') as data_api_client:
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    api_stubs.lot(slug='digital-outcomes', allows_brief=True)
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()
            content_fixture = ContentLoader('tests/fixtures/content')
            content_fixture.load_manifest('dos', 'data', 'edit_brief')
            content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

            res = getattr(self.client, method)(
                "{}{}".format(baseurl, url),
                data=data)
            assert res.status_code == status_code

    # These should all work as expected

    def test_wrong_lot_get_view_brief_overview(self):
        self._load_page("/digital-specialists/1234", 200)

    def test_wrong_lot_get_view_section_summary(self):
        self._load_page("/digital-specialists/1234/section-1", 200)

    def test_wrong_lot_get_edit_brief_question(self):
        self._load_page("/digital-specialists/1234/edit/section-1/required1", 200)

    def test_wrong_lot_post_edit_brief_question(self):
        data = {"required1": True}
        self._load_page("/digital-specialists/1234/edit/section-1/required1", 302, method='post', data=data)

    def test_wrong_lot_get_view_brief_responses(self):
        self._load_page("/digital-specialists/1234/responses", 200)

    # get and post are the same for publishing

    def test_wrong_lot_post_delete_a_brief(self):
        data = {"delete_confirmed": True}
        self._load_page("/digital-specialists/1234/delete", 302, method='post', data=data)

    # Wrong lots

    def test_get_view_brief_overview(self):
        self._load_page("/digital-outcomes/1234", 404)

    def test_get_view_section_summary(self):
        self._load_page("/digital-outcomes/1234/section-1", 404)

    def test_get_edit_brief_question(self):
        self._load_page("/digital-outcomes/1234/edit/section-1/required1", 404)

    def test_post_edit_brief_question(self):
        data = {"required1": True}
        self._load_page("/digital-outcomes/1234/edit/section-1/required1", 404, method='post', data=data)

    def test_get_view_brief_responses(self):
        self._load_page("/digital-outcomes/1234/responses", 404)

    # get and post are the same for publishing
    def test_publish_brief(self):
        self._load_page("/digital-outcomes/1234/publish", 404)

    def test_post_delete_a_brief(self):
        data = {"delete_confirmed": True}
        self._load_page("/digital-outcomes/1234/delete", 404, method='post', data=data)


@mock.patch('app.buyers.views.buyers.data_api_client')
class TestEditBriefSubmission(BaseApplicationTest):

    def _test_breadcrumbs_on_question_page(self, response, has_summary_page=False, section_name=None):
        breadcrumbs = html.fromstring(response.get_data(as_text=True)).xpath(
            '//*[@id="global-breadcrumb"]/nav/ol/li'
        )

        breadcrumbs_we_expect = [
            ('Digital Marketplace', '/'),
            ('Your account', '/buyers'),
            ('I need a thing to do a thing',
             '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234')
        ]
        if has_summary_page and section_name:
            breadcrumbs_we_expect.append((
                section_name,
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/{}'.format(
                    section_name.lower().replace(' ', '-')
                )
            ))

        assert len(breadcrumbs) == len(breadcrumbs_we_expect)

        for index, link in enumerate(breadcrumbs_we_expect):
            assert breadcrumbs[index].find('a').text_content().strip() == link[0]
            assert breadcrumbs[index].find('a').get('href').strip() == link[1]

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
            "/1234/edit/description-of-work/organisation")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        assert document.xpath('//h1')[0].text_content().strip() == "Organisation the work is for"

    @mock.patch("app.buyers.views.buyers.content_loader")
    def test_edit_brief_submission_return_link_to_section_summary_if_section_has_description(
            self, content_loader, data_api_client
    ):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/section-4/optional2")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        secondary_action_link = document.xpath('//form//div[contains(@class, "secondary-action-link")]/a')[0]
        assert document.xpath('//h1')[0].text_content().strip() == "Optional 2"
        assert secondary_action_link.get('href').strip() == "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-4"  # noqa
        assert secondary_action_link.text_content().strip() == "Return to section 4"
        self._test_breadcrumbs_on_question_page(response=res, has_summary_page=True, section_name='Section 4')

    @mock.patch("app.buyers.views.buyers.content_loader")
    def test_edit_brief_submission_return_link_to_section_summary_if_other_questions(self, content_loader,
    data_api_client):  # noqa
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/section-1/required1")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        secondary_action_link = document.xpath('//form//div[contains(@class, "secondary-action-link")]/a')[0]
        assert document.xpath('//h1')[0].text_content().strip() == "Required 1"
        assert secondary_action_link.get('href').strip() == "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-1"  # noqa
        assert secondary_action_link.text_content().strip() == "Return to section 1"
        self._test_breadcrumbs_on_question_page(response=res, has_summary_page=True, section_name='Section 1')

    @mock.patch("app.buyers.views.buyers.content_loader")
    def test_edit_brief_submission_return_link_to_brief_overview_if_single_question(self, content_loader,
    data_api_client):  # noqa
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/section-2/required2")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        secondary_action_link = document.xpath('//form//div[contains(@class, "secondary-action-link")]/a')[0]
        assert document.xpath('//h1')[0].text_content().strip() == "Required 2"
        assert secondary_action_link.get('href').strip() == "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"  # noqa
        assert secondary_action_link.text_content().strip() == "Return to overview"
        self._test_breadcrumbs_on_question_page(response=res, has_summary_page=False)

    @mock.patch("app.buyers.views.buyers.content_loader")
    def test_edit_brief_submission_multiquestion(self, content_loader, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/edit/section-5/required3")  # noqa

        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))
        assert document.xpath('//h1')[0].text_content().strip() == "Required 3"
        assert document.xpath(
            '//*[@id="required3_1"]//span[contains(@class, "question-heading")]/p'
        )[0].text_content().strip() == "Required 3_1"
        assert document.xpath(
            '//*[@id="required3_2"]//span[contains(@class, "question-heading")]/p'
        )[0].text_content().strip() == "Required 3_2"

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
            "/1234/edit/description-of-work/organisation")

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
            "/1234/edit/description-of-work/organisation")

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
            "/1234/edit/description-of-work/organisation")

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
            "/1234/edit/description-of-work/organisation")

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
            "/1234/edit/description-of-work/organisation")

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
            "/1234/not-a-real-section")

        assert res.status_code == 404

    def test_404_if_question_does_not_exist(self, data_api_client):
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
            "/1234/edit/description-of-work/not-a-real-question")

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
            "digital-specialists/1234/edit/description-of-work/organisation",
            data={
                "organisation": "GDS"
            })

        assert res.status_code == 302
        data_api_client.update_brief.assert_called_with(
            '1234',
            {"organisation": "GDS"},
            page_questions=['organisation'],
            updated_by='buyer@email.com'
        )

    @mock.patch("app.buyers.views.buyers.content_loader")
    def test_post_update_if_multiple_questions_redirects_to_section_summary(self, content_loader, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/section-1/required1",
            data={
                "required1": True
            })

        assert res.status_code == 302
        data_api_client.update_brief.assert_called_with(
            '1234',
            {"required1": True},
            page_questions=['required1'],
            updated_by='buyer@email.com'
        )
        assert res.headers['Location'].endswith(
            'buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-1'
        ) is True

    @mock.patch("app.buyers.views.buyers.content_loader")
    def test_post_update_if_section_description_redirects_to_section_summary(self, content_loader, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/section-4/optional2",
            data={
                "optional2": True
            })

        assert res.status_code == 302
        data_api_client.update_brief.assert_called_with(
            '1234',
            {"optional2": True},
            page_questions=['optional2'],
            updated_by='buyer@email.com'
        )
        assert res.headers['Location'].endswith(
            'buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-4'
        ) is True

    @mock.patch("app.buyers.views.buyers.content_loader")
    def test_post_update_if_single_question_no_description_redirects_to_overview(self, content_loader, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/section-2/required2",
            data={
                "required2": True
            })

        assert res.status_code == 302
        data_api_client.update_brief.assert_called_with(
            '1234',
            {"required2": True},
            page_questions=['required2'],
            updated_by='buyer@email.com'
        )
        assert res.headers['Location'].endswith(
            'buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234'
        ) is True

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
            "digital-specialists/1234/edit/description-of-work/organisation",
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
            "digital-specialists/1234/edit/description-of-work/organisation",
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
            "digital-octopuses/1234/edit/description-of-work/organisation",
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
            "digital-specialists/1234/edit/description-of-work/organisation",
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
            "digital-specialists/1234/edit/description-of-work/organisation",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called

    def test_404_if_question_does_not_exist(self, data_api_client):
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
            "digital-specialists/1234/edit/description-of-work/some-made-up-question",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called


@mock.patch('app.buyers.views.buyers.data_api_client')
class TestPublishBrief(BaseApplicationTest):
    def test_publish_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'backgroundInformation': 'test background info',
            'contractLength': 'A very long time',
            'culturalFitCriteria': ['CULTURAL', 'FIT'],
            'culturalWeighting': 10,
            'essentialRequirements': 'Everything',
            'evaluationType': ['test evaluation type'],
            'existingTeam': 'team team team',
            'importantDates': 'Near future',
            'numberOfSuppliers': 5,
            'location': 'somewhere',
            'organisation': 'test organisation',
            'priceWeighting': 80,
            'specialistRole': 'communicationsManager',
            'specialistWork': 'work work work',
            'startDate': 'startDate',
            'summary': 'blah',
            'technicalWeighting': 10,
            'workingArrangements': 'arrangements',
            'workplaceAddress': 'address',
            'requirementsLength': '1 week'
        })
        data_api_client.get_brief.return_value = brief_json

        res = self.client.post("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                               "digital-specialists/1234/publish")
        assert res.status_code == 302
        assert data_api_client.update_brief_status.called
        assert res.location == "http://localhost/buyers/frameworks/digital-outcomes-and-specialists/" \
                               "requirements/digital-specialists/1234?published=true"

    def test_publish_brief_with_unanswered_required_questions(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        data_api_client.get_brief.return_value = api_stubs.brief(status="draft")

        res = self.client.post("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                               "digital-specialists/1234/publish")
        assert res.status_code == 400
        assert not data_api_client.update_brief_status.called

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

    def test_publish_button_available_if_questions_answered(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'backgroundInformation': 'test background info',
            'contractLength': 'A very long time',
            'culturalFitCriteria': ['CULTURAL', 'FIT'],
            'culturalWeighting': 10,
            'essentialRequirements': 'Everything',
            'evaluationType': ['test evaluation type'],
            'existingTeam': 'team team team',
            'importantDates': 'Near future',
            'location': 'somewhere',
            'numberOfSuppliers': 3,
            'organisation': 'test organisation',
            'priceWeighting': 80,
            'specialistRole': 'communicationsManager',
            'specialistWork': 'work work work',
            'startDate': 'startDate',
            'summary': 'blah',
            'technicalWeighting': 10,
            'workingArrangements': 'arrangements',
            'workplaceAddress': 'address',
            'requirementsLength': '1 week'
        })
        data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Publish requirements' in page_html, page_html

    def test_publish_button_unavailable_if_questions_not_answered(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'requirementsLength': '1 week'
        })
        data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Publish requirements' not in page_html

    def test_warning_about_setting_requirement_length_is_not_displayed_if_not_specialist_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True)
            ]
        )

        data_api_client.get_brief.return_value = api_stubs.brief(status="draft", lot_slug="digital-outcomes")

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-outcomes/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'This will show you what the supplier application deadline will be' not in page_html
        assert 'Your requirements will be open for 2 weeks' in page_html

    def test_correct_content_is_displayed_if_no_requirementLength_is_set(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        data_api_client.get_brief.return_value = api_stubs.brief(status="draft")

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'href="/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/edit/set-how-long-your-requirements-will-be-open-for/requirementsLength"' in page_html  # noqa
        assert 'This will show you what the supplier application deadline will be' in page_html
        assert 'Your requirements will be open for' not in page_html

    def test_correct_content_is_displayed_if_requirementLength_is_1_week(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'requirementsLength': '1 week'
        })
        data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Your requirements will be open for 1 week.' in page_html
        assert 'This will show you what the supplier application deadline will be' not in page_html
        assert 'Your requirements will be open for 2 weeks' not in page_html

    def test_correct_content_is_displayed_if_requirementLength_is_2_weeks(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'requirementsLength': '2 weeks'
        })
        data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Your requirements will be open for 2 weeks.' in page_html
        assert 'This will show you what the supplier application deadline will be' not in page_html
        assert 'Your requirements will be open for 1 week' not in page_html

    def test_correct_content_is_displayed_if_requirementLength_is_not_set(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'requirementsLength': None
        })
        data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)
        document = html.fromstring(page_html)

        assert res.status_code == 200
        assert 'Your requirements will be open for 2 weeks.' not in page_html
        assert 'This will show you what the supplier application deadline will be' in page_html
        assert 'Your requirements will be open for 1 week' not in page_html
        assert not document.xpath('//a[contains(text(), "Set how long your requirements will be live for")]')

    def test_heading_for_unanswered_questions_not_displayed_if_only_requirements_length_unset(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'backgroundInformation': 'test background info',
            'contractLength': 'A very long time',
            'culturalFitCriteria': ['CULTURAL', 'FIT'],
            'culturalWeighting': 10,
            'essentialRequirements': 'Everything',
            'evaluationType': ['test evaluation type'],
            'existingTeam': 'team team team',
            'importantDates': 'Near future',
            'location': 'somewhere',
            'numberOfSuppliers': 3,
            'organisation': 'test organisation',
            'priceWeighting': 80,
            'specialistRole': 'communicationsManager',
            'specialistWork': 'work work work',
            'startDate': 'startDate',
            'summary': 'blah',
            'technicalWeighting': 10,
            'workingArrangements': 'arrangements',
            'workplaceAddress': 'address'
        })
        data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)
        document = html.fromstring(page_html)

        assert res.status_code == 200
        assert "You still need to complete the following questions before your requirements " \
            "can be published:" not in page_html


@mock.patch('app.buyers.views.buyers.data_api_client')
class TestDeleteBriefSubmission(BaseApplicationTest):
    def test_delete_brief_submission(self, data_api_client):
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
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/delete"
        )

        assert res.status_code == 302
        assert data_api_client.delete_brief.called
        assert res.location == "http://localhost/buyers"

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
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/delete",
        )

        assert res.status_code == 404
        assert not data_api_client.delete_brief.called

    def test_cannot_delete_live_brief(self, data_api_client):
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
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/delete",
        )

        assert res.status_code == 404
        assert not data_api_client.delete_brief.called

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
    def test_show_draft_brief_summary_page(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="draft")
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            document = html.fromstring(page_html)

            assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"
            assert [e.text_content() for e in document.xpath('//main[@id="content"]//ul/li/a')] == [
                'Title',
                'Specialist role',
                'Location',
                'Description of work',
                'Shortlist and evaluation process',
                'Set how long your requirements will be open for',
                'Describe question and answer session',
                'Review and publish your requirements',
                'How to answer supplier questions',
                'How to shortlist suppliers',
                'How to evaluate suppliers',
                'How to award a contract',
                'View the Digital Outcomes and Specialists contract',
            ]

            assert document.xpath('//a[contains(text(), "Delete")]')

    def test_show_live_brief_summary_page(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="live")
            brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            document = html.fromstring(page_html)

            assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"
            assert [e.text_content() for e in document.xpath('//main[@id="content"]//ul/li/a')] == [
                'View question and answer dates',
                'View your published requirements',
                'Publish questions and answers',
                'How to answer supplier questions',
                'How to shortlist suppliers',
                'How to evaluate suppliers',
                'How to award a contract',
                'View the Digital Outcomes and Specialists contract',
            ]

            assert not document.xpath('//a[contains(text(), "Delete")]')

    def test_show_closed_brief_summary_page(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="closed")
            brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            document = html.fromstring(page_html)

            assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"
            assert [e.text_content() for e in document.xpath('//main[@id="content"]//ul/li/a')] == [
                'View your published requirements',
                'View and shortlist suppliers',
                'How to shortlist suppliers',
                'How to evaluate suppliers',
                'How to award a contract',
                'View the Digital Outcomes and Specialists contract',
            ]

            assert not document.xpath('//a[contains(text(), "Delete")]')

    def test_show_clarification_questions_page_for_live_brief_with_no_questions(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="live")
            brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
            brief_json['briefs']["clarificationQuestionsAreClosed"] = False
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/supplier-questions"  # noqa
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            assert "Supplier questions" in page_html
            assert "No questions or answers have been published" in page_html
            assert "Answer a supplier question" in page_html

    def test_show_clarification_questions_page_for_live_brief_with_one_question(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="live", clarification_questions=[
                {"question": "Why is my question a question?",
                 "answer": "Because",
                 "publishedAt": "2016-01-01T00:00:00.000000Z"}
            ])
            brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/supplier-questions"  # noqa
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            assert "Supplier questions" in page_html
            assert "Why is my question a question?" in page_html
            assert "Because" in page_html
            assert "Answer a supplier question" in page_html
            assert "No questions or answers have been published" not in page_html

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
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
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
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 404

    @mock.patch("app.buyers.views.buyers.content_loader")
    def test_links_to_sections_go_to_the_correct_pages_whether_they_be_sections_or_questions(self, content_loader, data_api_client):  # noqa
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            content_fixture = ContentLoader('tests/fixtures/content')
            content_fixture.load_manifest('dos', 'data', 'edit_brief')
            content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 200

            document = html.fromstring(res.get_data(as_text=True))
            section_steps = document.xpath(
                '//*[@id="content"]/div/div/ol[contains(@class, "instruction-list")]')
            section_1_link = section_steps[0].xpath('li//a[contains(text(), "Section 1")]')
            section_2_link = section_steps[0].xpath('li//a[contains(text(), "Section 2")]')
            section_4_link = section_steps[0].xpath('li//a[contains(text(), "Section 4")]')

            # section with multiple questions
            assert section_1_link[0].get('href').strip() == \
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-1'
            # section with single question
            assert section_2_link[0].get('href').strip() == \
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/edit/section-2/required2'  # noqa
            # section with single question and a description
            assert section_4_link[0].get('href').strip() == \
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-4'


@mock.patch("app.buyers.views.buyers.data_api_client")
class TestAddBriefClarificationQuestion(BaseApplicationTest):
    def test_show_brief_clarification_question_form(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug="digital-outcomes-and-specialists",
            status="live",
            lots=[
                api_stubs.lot(slug="digital-specialists", allows_brief=True)
            ])
        brief_json = api_stubs.brief(status="live")
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question")

        assert res.status_code == 200

    def test_add_brief_clarification_question(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug="digital-outcomes-and-specialists",
            status="live",
            lots=[
                api_stubs.lot(slug="digital-specialists", allows_brief=True)
            ])
        brief_json = api_stubs.brief(status="live")
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question",
            data={
                "question": "Why?",
                "answer": "Because",
            })

        assert res.status_code == 302
        data_api_client.add_brief_clarification_question.assert_called_with(
            "1234", "Why?", "Because", "buyer@email.com")

        # test that the redirect ends up on the right page
        assert res.headers['Location'].endswith(
            '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/supplier-questions'  # noqa
        ) is True

    def test_404_if_framework_is_not_live(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='pending',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        brief_json = api_stubs.brief()
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question",
            data={
                "question": "Why?",
                "answer": "Because",
            })

        assert res.status_code == 404
        assert not data_api_client.add_brief_clarification_question.called

    def test_404_if_framework_does_not_allow_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False),
            ]
        )
        brief_json = api_stubs.brief()
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question",
            data={
                "question": "Why?",
                "answer": "Because",
            })

        assert res.status_code == 404
        assert not data_api_client.add_brief_clarification_question.called

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        brief_json = api_stubs.brief(user_id=234)
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question",
            data={
                "question": "Why?",
                "answer": "Because",
            })

        assert res.status_code == 404
        assert not data_api_client.add_brief_clarification_question.called

    def test_404_if_brief_is_not_live(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        brief_json = api_stubs.brief(status="draft")
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question",
            data={
                "question": "Why?",
                "answer": "Because",
            })

        assert res.status_code == 404
        assert not data_api_client.add_brief_clarification_question.called

    def test_validation_error(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug="digital-outcomes-and-specialists",
            status="live",
            lots=[
                api_stubs.lot(slug="digital-specialists", allows_brief=True)
            ])
        brief_json = api_stubs.brief(status="live")
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json
        data_api_client.add_brief_clarification_question.side_effect = HTTPError(
            mock.Mock(status_code=400),
            {"question": "answer_required"})

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question",
            data={
                "question": "Why?",
                "answer": "Because",
            })
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 400
        assert len(document.cssselect(".validation-message")) == 1, res.get_data(as_text=True)

    def test_api_error(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug="digital-outcomes-and-specialists",
            status="live",
            lots=[
                api_stubs.lot(slug="digital-specialists", allows_brief=True)
            ])
        brief_json = api_stubs.brief(status="live")
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json
        data_api_client.add_brief_clarification_question.side_effect = HTTPError(
            mock.Mock(status_code=500))

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question",
            data={
                "question": "Why?",
                "answer": "Because",
            })

        assert res.status_code == 500


@mock.patch("app.buyers.views.buyers.data_api_client")
class TestViewBriefResponsesPage(BaseApplicationTest):
    two_good_three_bad_responses = {
        "briefResponses": [
            {"essentialRequirements": [True, True, True, True, True]},
            {"essentialRequirements": [True, False, True, True, True]},
            {"essentialRequirements": [True, True, False, False, True]},
            {"essentialRequirements": [True, True, True, True, True]},
            {"essentialRequirements": [True, True, True, True, False]},
        ]
    }

    def test_page_shows_correct_count_of_eligible_suppliers(self, data_api_client):
        data_api_client.find_brief_responses.return_value = self.two_good_three_bad_responses
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes")

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1/responses"
        )
        page = res.get_data(as_text=True)

        assert res.status_code == 200
        assert "2 suppliers" in page
        assert "responded to your requirements and meet all your essential skills and experience." in page

    def test_page_does_not_pluralise_for_single_response(self, data_api_client):
        data_api_client.find_brief_responses.return_value = {
            "briefResponses": [{"essentialRequirements": [True, True, True, True, True]}]
        }
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes")

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1/responses"
        )
        page = res.get_data(as_text=True)
        assert res.status_code == 200
        assert "1 supplier" in page
        assert "responded to your requirements and meets all your essential skills and experience." in page

    def test_page_shows_correct_message_if_no_eligible_suppliers(self, data_api_client):
        data_api_client.find_brief_responses.return_value = {
            "briefResponses": [{"essentialRequirements": [True, False, True, True, True]}]
        }
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes")

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        page = res.get_data(as_text=True)

        assert res.status_code == 200
        assert "No suppliers met your essential skills and experience requirements." in page

    def test_page_shows_csv_download_link_if_brief_closed(self, data_api_client):
        data_api_client.find_brief_responses.return_value = self.two_good_three_bad_responses
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes", status='closed')

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        document = html.fromstring(res.get_data(as_text=True))
        csv_link = document.xpath(
            '//a[@href="/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses/download"]'  # noqa
        )[0]

        assert res.status_code == 200
        assert self._strip_whitespace(csv_link.text_content()) == \
            "CSVdocument:Downloadsupplierresponsesto‘Ineedathingtodoathing’"

    def test_page_does_not_show_csv_download_link_if_brief_open(self, data_api_client):
        data_api_client.find_brief_responses.return_value = self.two_good_three_bad_responses
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes", status='live')

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        page = res.get_data(as_text=True)
        document = html.fromstring(page)
        csv_link = document.xpath(
            '//a[@href="/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses/download"]'  # noqa
        )

        assert res.status_code == 200
        assert len(csv_link) == 0
        assert "The file will be available here once applications have closed." in page

    def test_404_if_brief_does_not_belong_to_buyer(self, data_api_client):
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes", user_id=234)

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )

        assert res.status_code == 404

    def test_404_if_lot_does_not_allow_brief(self, data_api_client):
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=False),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes")

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )

        assert res.status_code == 404


@mock.patch("app.buyers.views.buyers.data_api_client")
class TestDownloadBriefResponsesCsv(BaseApplicationTest):
    url = "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/responses/download"

    def setup(self):
        super(TestDownloadBriefResponsesCsv, self).setup()
        self.brief = api_stubs.brief(status='closed')
        self.brief['briefs']['essentialRequirements'] = ["E1", "E2"]
        self.brief['briefs']['niceToHaveRequirements'] = ["Nice1", "Nice2", "Nice3"]

        self.brief_responses = {
            "briefResponses": [
                {
                    "supplierName": "Kev's Butties",
                    "availability": "Next Tuesday",
                    "dayRate": "£1.49",
                    "essentialRequirements": [True, True],
                    "niceToHaveRequirements": [True, False, False],
                    "respondToEmailAddress": "test1@email.com",
                },
                {
                    "supplierName": "Kev's Pies",
                    "availability": "A week Friday",
                    "dayRate": "£3.50",
                    "essentialRequirements": [True, True],
                    "niceToHaveRequirements": [False, True, True],
                    "respondToEmailAddress": "test2@email.com",
                },
                {
                    "supplierName": "Kev's Doughnuts",
                    "availability": "As soon as the sugar is delivered",
                    "dayRate": "£10 a dozen",
                    "essentialRequirements": [True, False],
                    "niceToHaveRequirements": [True, True, False],
                    "respondToEmailAddress": "test3@email.com",
                },
                {
                    "supplierName": "Kev's Fried Noodles",
                    "availability": "After Christmas",
                    "dayRate": "£12.35",
                    "essentialRequirements": [False, True],
                    "niceToHaveRequirements": [True, True, True],
                    "respondToEmailAddress": "test4@email.com",
                },
                {
                    "supplierName": "Kev's Pizza",
                    "availability": "Within the hour",
                    "dayRate": "£350",
                    "essentialRequirements": [False, False],
                    "niceToHaveRequirements": [False, False, False],
                    "respondToEmailAddress": "test5@email.com",
                },
            ]
        }

        self.tricky_character_responses = {
            "briefResponses": [
                {
                    "supplierName": "K,ev’s \"Bu,tties",
                    "availability": "❝Next — Tuesday❞",
                    "dayRate": "¥1.49,",
                    "essentialRequirements": [True, True],
                    "niceToHaveRequirements": [True, False, False],
                    "respondToEmailAddress": "test1@email.com",
                },
                {
                    "supplierName": "Kev\'s \'Pies",
                    "availability": "&quot;A week Friday&rdquot;",
                    "dayRate": "&euro;3.50",
                    "essentialRequirements": [True, True],
                    "niceToHaveRequirements": [False, True, True],
                    "respondToEmailAddress": "te,st2@email.com",
                },
            ]
        }

    def test_csv_includes_all_eligible_responses_and_no_ineligible_responses(self, data_api_client):
        data_api_client.find_brief_responses.return_value = self.brief_responses
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = self.brief

        self.login_as_buyer()
        res = self.client.get(self.url)
        page = res.get_data(as_text=True)
        lines = page.splitlines()
        # There are only the two eligible responses included
        assert len(lines) == 3
        assert lines[0] == "Supplier,Date the specialist can start work,Day rate,Nice1,Nice2,Nice3,Email address"
        # The response with two nice-to-haves is sorted to above the one with only one
        assert lines[1] == "Kev's Pies,A week Friday,£3.50,False,True,True,test2@email.com"
        assert lines[2] == "Kev's Butties,Next Tuesday,£1.49,True,False,False,test1@email.com"

    def test_download_brief_responses_for_brief_without_nice_to_haves(self, data_api_client):
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )

        for response in self.brief_responses['briefResponses']:
            del response["niceToHaveRequirements"]
        data_api_client.find_brief_responses.return_value = self.brief_responses

        data_api_client.get_brief.return_value = self.brief

        self.login_as_buyer()

        del self.brief['briefs']['niceToHaveRequirements']
        res = self.client.get(self.url)
        assert res.status_code, 200

        self.brief['briefs']['niceToHaveRequirements'] = []
        res = self.client.get(self.url)
        assert res.status_code, 200

    def test_csv_handles_tricky_characters(self, data_api_client):
        data_api_client.find_brief_responses.return_value = self.tricky_character_responses
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = self.brief

        self.login_as_buyer()
        res = self.client.get(self.url)
        page = res.get_data(as_text=True)
        lines = page.splitlines()

        assert len(lines) == 3
        assert lines[0] == "Supplier,Date the specialist can start work,Day rate,Nice1,Nice2,Nice3,Email address"
        # The values with internal commas are surrounded by quotes, and all other characters appear as in the data
        assert lines[1] == 'Kev\'s \'Pies,&quot;A week Friday&rdquot;,&euro;3.50,False,True,True,"te,st2@email.com"'
        assert lines[2] == '"K,ev’s ""Bu,tties",❝Next — Tuesday❞,"¥1.49,",True,False,False,test1@email.com'

    def test_404_if_brief_does_not_belong_to_buyer(self, data_api_client):
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(user_id=234, status='closed')

        self.login_as_buyer()
        res = self.client.get(self.url)
        assert res.status_code == 404

    def test_404_if_brief_is_not_closed(self, data_api_client):
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(status='live')

        self.login_as_buyer()
        res = self.client.get(self.url)
        assert res.status_code == 404


@mock.patch('app.buyers.views.buyers.data_api_client')
class TestViewQuestionAndAnswerDates(BaseApplicationTest):
    def test_show_question_and_answer_dates_for_published_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="live")
            brief_json['briefs']['requirementsLength'] = '2 weeks'
            brief_json['briefs']['publishedAt'] = u"2016-04-02T20:10:00.00000Z"
            brief_json['briefs']['clarificationQuestionsClosedAt'] = u"2016-04-12T23:59:00.00000Z"
            brief_json['briefs']['clarificationQuestionsPublishedBy'] = u"2016-04-14T23:59:00.00000Z"
            brief_json['briefs']['applicationsClosedAt'] = u"2016-04-16T23:59:00.00000Z"
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/timeline"
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            document = html.fromstring(page_html)

            assert (document.xpath('//h1')[0]).text_content().strip() == "Question and answer dates"
            assert all(
                date in
                [e.text_content() for e in document.xpath('//main[@id="content"]//th/span')]
                for date in ['2 April', '8 April', '15 April', '16 April']
            )

    def test_do_not_show_question_and_answer_dates_for_draft_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="draft")
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/timeline"
            )

            assert res.status_code == 404

    def test_do_not_show_question_and_answer_dates_for_closed_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="closed")
            brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/timeline"
            )

            assert res.status_code == 404
