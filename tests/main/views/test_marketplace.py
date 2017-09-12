# coding=utf-8

import mock
from six import iteritems
from six.moves.urllib.parse import urlparse, parse_qs
from lxml import html
import re
from ...helpers import BaseApplicationTest
import pytest


class TestApplication(BaseApplicationTest):
    def setup_method(self, method):
        super(TestApplication, self).setup_method(method)

    def test_analytics_code_should_be_in_javascript(self):
        res = self.client.get('/static/javascripts/application.js')
        assert res.status_code == 200
        assert 'trackPageview' in res.get_data(as_text=True)

    def test_should_use_local_cookie_page_on_cookie_message(self):
        res = self.client.get('/')
        assert res.status_code == 200
        assert '<p>GOV.UK uses cookies to make the site simpler. <a href="/cookies">' \
            'Find out more about cookies</a></p>' in res.get_data(as_text=True)


@mock.patch('app.main.views.marketplace.data_api_client', autospec=True)
class TestHomepageAccountCreationVirtualPageViews(BaseApplicationTest):
    def test_data_analytics_track_page_view_is_shown_if_account_created_flag_flash_message(self, data_api_client):
        with self.client.session_transaction() as session:
            session['_flashes'] = [('flag', 'account-created')]

        res = self.client.get("/")
        data = res.get_data(as_text=True)

        assert 'data-analytics="trackPageView" data-url="buyers?account-created=true"' in data
        # however this should not be shown as a regular flash message
        flash_banner_match = re.search('<p class="banner-message">\s*(.*)', data, re.MULTILINE)
        assert flash_banner_match is None, "Unexpected flash banner message '{}'.".format(
            flash_banner_match.groups()[0])

    def test_data_analytics_track_page_view_not_shown_if_no_account_created_flag_flash_message(self, data_api_client):
        res = self.client.get("/")
        data = res.get_data(as_text=True)

        assert 'data-analytics="trackPageView" data-url="buyers?account-created=true"' not in data


@mock.patch('app.main.views.marketplace.data_api_client', autospec=True)
class TestHomepageBrowseList(BaseApplicationTest):

    mock_live_dos_1_framework = {
        "framework": "digital-outcomes-and-specialists",
        "slug": "digital-outcomes-and-specialists",
        "status": "live",
        "id": 5
    }

    mock_live_dos_2_framework = {
        "framework": "digital-outcomes-and-specialists",
        "slug": "digital-outcomes-and-specialists-2",
        "status": "live",
        "id": 7
    }

    mock_live_g_cloud_9_framework = {
        "framework": "g-cloud",
        "slug": "g-cloud-9",
        "status": "live",
        "id": 8
    }

    def test_dos_links_are_shown(self, data_api_client):
        with self.app.app_context():
            data_api_client.find_frameworks.return_value = {
                "frameworks": [
                    self.mock_live_dos_1_framework
                ]
            }

            res = self.client.get("/")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            link_texts = [item.text_content().strip() for item in document.cssselect('.browse-list-item a')]
            assert link_texts[0] == "Find an individual specialist"
            assert link_texts[-1] == "Buy physical datacentre space"
            assert "Find specialists to work on digital projects" not in link_texts

    def test_links_are_for_existing_dos_framework_when_a_new_dos_framework_in_standstill_exists(self, data_api_client):
        with self.app.app_context():
            mock_standstill_dos_2_framework = self.mock_live_dos_2_framework.copy()
            mock_standstill_dos_2_framework.update({"status": "standstill"})

            data_api_client.find_frameworks.return_value = {
                "frameworks": [
                    self.mock_live_dos_1_framework,
                    mock_standstill_dos_2_framework,
                ]
            }

            res = self.client.get("/")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            link_locations = [item.values()[1] for item in document.cssselect('.browse-list-item a')]

            lots = ['digital-specialists', 'digital-outcomes', 'user-research-participants', 'user-research-studios']
            dos_base_path = '/buyers/frameworks/digital-outcomes-and-specialists/requirements/{}'

            for index, lot_slug in enumerate(lots):
                assert link_locations[index] == dos_base_path.format(lot_slug)

    def test_links_are_for_the_newest_live_dos_framework_when_multiple_live_dos_frameworks_exist(self, data_api_client):
        with self.app.app_context():
            data_api_client.find_frameworks.return_value = {
                "frameworks": [
                    self.mock_live_dos_1_framework,
                    self.mock_live_dos_2_framework,
                ]
            }

            res = self.client.get("/")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            link_locations = [item.values()[1] for item in document.cssselect('.browse-list-item a')]

            lots = ['digital-specialists', 'digital-outcomes', 'user-research-participants', 'user-research-studios']
            dos2_base_path = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/{}'

            for index, lot_slug in enumerate(lots):
                assert link_locations[index] == dos2_base_path.format(lot_slug)

    def test_links_are_for_live_dos_framework_when_expired_dos_framework_exists(self, data_api_client):
        with self.app.app_context():
            mock_expired_dos_1_framework = self.mock_live_dos_1_framework.copy()
            mock_expired_dos_1_framework.update({"status": "expired"})

            data_api_client.find_frameworks.return_value = {
                "frameworks": [
                    mock_expired_dos_1_framework,
                    self.mock_live_dos_2_framework,
                ]
            }

            res = self.client.get("/")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            link_locations = [item.values()[1] for item in document.cssselect('.browse-list-item a')]

            lots = ['digital-specialists', 'digital-outcomes', 'user-research-participants', 'user-research-studios']
            dos2_base_path = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/{}'

            for index, lot_slug in enumerate(lots):
                assert link_locations[index] == dos2_base_path.format(lot_slug)

    def test_non_dos_links_are_shown_if_no_live_dos_framework(self, data_api_client):
        with self.app.app_context():
            mock_expired_dos_1_framework = self.mock_live_dos_1_framework.copy()
            mock_expired_dos_1_framework.update({"status": "expired"})
            mock_expired_dos_2_framework = self.mock_live_dos_2_framework.copy()
            mock_expired_dos_2_framework.update({"status": "expired"})
            mock_g_cloud_9_framework = self.mock_live_g_cloud_9_framework.copy()

            data_api_client.find_frameworks.return_value = {
                "frameworks": [
                    mock_expired_dos_1_framework,
                    mock_expired_dos_2_framework,
                    mock_g_cloud_9_framework,
                ]
            }

            res = self.client.get("/")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            link_texts = [item.text_content().strip() for item in document.cssselect('.browse-list-item a')]
            assert link_texts[0] == "Find cloud hosting, software and support"
            assert link_texts[1] == "Buy physical datacentre space"
            assert len(link_texts) == 2


class TestHomepageSidebarMessage(BaseApplicationTest):
    def setup_method(self, method):
        super(TestHomepageSidebarMessage, self).setup_method(method)

    @staticmethod
    def _find_frameworks(framework_slugs_and_statuses):

        _frameworks = []

        for index, framework_slug_and_status in enumerate(framework_slugs_and_statuses):
            framework_slug, framework_status = framework_slug_and_status
            _frameworks.append({
                'framework': 'framework',
                'slug': framework_slug,
                'id': index + 1,
                'status': framework_status,
                'name': 'Framework'
            })

        return {
            'frameworks': _frameworks
        }

    @staticmethod
    def _assert_message_container_is_empty(response_data):
        document = html.fromstring(response_data)
        message_container_contents = document.xpath('//div[@class="supplier-messages column-one-third"]/aside/*')
        assert len(message_container_contents) == 0

    @staticmethod
    def _assert_message_container_is_not_empty(response_data):
        document = html.fromstring(response_data)
        message_container_contents = document.xpath('//div[@class="supplier-messages column-one-third"]/aside/*')
        assert len(message_container_contents) > 0
        assert message_container_contents[0].xpath('text()')[0].strip() == "Sell services"

    @mock.patch('app.main.views.marketplace.data_api_client', autospec=True)
    def _load_homepage(self, framework_slugs_and_statuses, framework_messages, data_api_client):
        data_api_client.find_frameworks.return_value = self._find_frameworks(framework_slugs_and_statuses)
        res = self.client.get('/')
        assert res.status_code == 200
        response_data = res.get_data(as_text=True)

        if framework_messages:
            self._assert_message_container_is_not_empty(response_data)
            for message in framework_messages:
                assert message in response_data
        else:
            self._assert_message_container_is_empty(response_data)

    def test_homepage_sidebar_message_exists_gcloud_8_coming(self):

        framework_slugs_and_statuses = [
            ('g-cloud-8', 'coming'),
            ('digital-outcomes-and-specialists', 'live')
        ]
        framework_messages = [
            u"Provide cloud software and support to the public sector.",
            u"You need an account to receive notifications about when you can apply."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

    def test_homepage_sidebar_message_exists_gcloud_8_open(self):

        framework_slugs_and_statuses = [
            ('g-cloud-8', 'open'),
            ('digital-outcomes-and-specialists', 'live')
        ]
        framework_messages = [
            u"Provide cloud software and support to the public sector",
            u"You need an account to apply.",
            u"The application deadline is 5pm BST, 23 June 2016."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

    def test_homepage_sidebar_message_exists_g_cloud_7_pending(self):

        framework_slugs_and_statuses = [
            ('g-cloud-7', 'pending'),
        ]
        framework_messages = [
            u"G‑Cloud 7 is closed for applications",
            u"G‑Cloud 7 services will be available from 23 November 2015."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

    @mock.patch('app.main.views.marketplace.data_api_client', autospec=True)
    def test_homepage_sidebar_messages_when_logged_out(self, data_api_client):
        data_api_client.find_frameworks.return_value = self._find_frameworks([
            ('digital-outcomes-and-specialists', 'live')
        ])
        res = self.client.get('/')
        assert res.status_code == 200
        response_data = res.get_data(as_text=True)

        document = html.fromstring(response_data)

        sidebar_links = document.xpath(
            '//div[@class="supplier-messages column-one-third"]/aside/div/p[1]/a[@class="top-level-link"]/text()'
        )
        sidebar_link_texts = [str(item).strip() for item in sidebar_links]

        assert 'View Digital Outcomes and Specialists opportunities' in sidebar_link_texts
        assert 'Create a supplier account' in sidebar_link_texts

    @mock.patch('app.main.views.marketplace.data_api_client', autospec=True)
    def test_homepage_sidebar_messages_when_logged_in(self, data_api_client):
        data_api_client.find_frameworks.return_value = self._find_frameworks([
            ('digital-outcomes-and-specialists', 'live')
        ])
        self.login_as_supplier()

        res = self.client.get('/')
        assert res.status_code == 200
        response_data = res.get_data(as_text=True)

        document = html.fromstring(response_data)

        sidebar_links = document.xpath(
            '//div[@class="supplier-messages column-one-third"]/aside/div/p[1]/a[@class="top-level-link"]/text()'
        )
        sidebar_link_texts = [str(item).strip() for item in sidebar_links]

        assert 'View Digital Outcomes and Specialists opportunities' in sidebar_link_texts
        assert 'Create a supplier account' not in sidebar_link_texts

    # here we've given an valid framework with a valid status but there is no message.yml file to read from
    @mock.patch('app.main.views.marketplace.data_api_client', autospec=True)
    def test_g_cloud_6_open_blows_up(self, data_api_client):
        framework_slugs_and_statuses = [
            ('g-cloud-6', 'open')
        ]

        data_api_client.find_frameworks.return_value = self._find_frameworks(framework_slugs_and_statuses)
        res = self.client.get('/')
        assert res.status_code == 500


class TestStaticMarketplacePages(BaseApplicationTest):
    def setup_method(self, method):
        super(TestStaticMarketplacePages, self).setup_method(method)

    def test_cookie_page(self):
        res = self.client.get('/cookies')
        assert res.status_code == 200
        assert '<h1>Cookies</h1>' in self._strip_whitespace(res.get_data(as_text=True))

    def test_terms_and_conditions_page(self):
        res = self.client.get('/terms-and-conditions')
        assert res.status_code == 200
        assert '<h1>Termsandconditions</h1>' in self._strip_whitespace(res.get_data(as_text=True))


class BaseBriefPageTest(BaseApplicationTest):
    def setup_method(self, method):
        super(BaseBriefPageTest, self).setup_method(method)

        self._data_api_client_patch = mock.patch('app.main.views.marketplace.data_api_client', autospec=True)
        self._data_api_client = self._data_api_client_patch.start()

        self.brief = self._get_dos_brief_fixture_data()
        self.brief_responses = self._get_dos_brief_responses_fixture_data()
        self.brief_id = self.brief['briefs']['id']
        self._data_api_client.get_brief.return_value = self.brief
        self._data_api_client.find_brief_responses.return_value = self.brief_responses

    def teardown_method(self, method):
        self._data_api_client_patch.stop()


class TestBriefPage(BaseBriefPageTest):

    def test_dos_brief_404s_if_brief_is_draft(self):
        self.brief['briefs']['status'] = 'draft'
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 404

    def test_dos_brief_has_correct_title(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        page_heading = document.xpath('//header[@class="page-heading-smaller"]')[0]
        assert page_heading.xpath('h1/text()')[0] == self.brief['briefs']['title']
        assert page_heading.xpath('p[@class="context"]/text()')[0] == self.brief['briefs']['organisation']

    @pytest.mark.parametrize('status', ['closed', 'unsuccessful', 'cancelled', 'awarded'])
    def test_only_one_banner_at_once_brief_page(self, status):
        self.brief['briefs']['status'] = status
        if self.brief['briefs']['status'] == 'awarded':
            self.brief['briefs']['awardedBriefResponseId'] = 14276
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))
        number_of_banners = len(document.xpath('//div[@class="banner-temporary-message-without-action"]'))

        assert number_of_banners == 1

    def test_dos_brief_displays_application_stats(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        incomplete_responses_section = document.xpath('//div[@id="incomplete-applications"]')[0]
        completed_responses_section = document.xpath('//div[@id="completed-applications"]')[0]

        assert incomplete_responses_section.xpath('div[@class="big-statistic"]/text()')[0] == '3'
        assert incomplete_responses_section.xpath('div[@class="statistic-name"]/text()')[0] == "Incomplete applications"
        assert incomplete_responses_section.xpath('div[@class="statistic-description"]/text()')[0] == "3 SME, 0 large"

        assert completed_responses_section.xpath('div[@class="big-statistic"]/text()')[0] == '5'
        assert completed_responses_section.xpath('div[@class="statistic-name"]/text()')[0] == "Completed applications"
        assert completed_responses_section.xpath('div[@class="statistic-description"]/text()')[0] == "4 SME, 1 large"

    def test_application_stats_pluralised_correctly(self):
        brief_id = self.brief['briefs']['id']
        self._data_api_client.find_brief_responses.return_value = {
            "briefResponses": [
                {
                    "id": 14275,
                    "briefId": brief_id,
                    "createdAt": "2016-12-02T11:09:28.054129Z",
                    "status": "submitted",
                    "submittedAt": "2016-12-05T11:09:28.054129Z",
                    "supplierId": 1234,
                    "supplierOrganisationSize": 'large'
                },
                {
                    "id": 14276,
                    "briefId": brief_id,
                    "createdAt": "2016-12-02T11:09:28.054129Z",
                    "status": "draft",
                    "submittedAt": "2016-12-05T11:09:28.054129Z",
                    "supplierId": 706033,
                    "supplierOrganisationSize": 'micro'
                }
            ]
        }
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        incomplete_responses_section = document.xpath('//div[@id="incomplete-applications"]')[0]
        completed_responses_section = document.xpath('//div[@id="completed-applications"]')[0]

        assert incomplete_responses_section.xpath('div[@class="big-statistic"]/text()')[0] == '1'
        assert incomplete_responses_section.xpath('div[@class="statistic-name"]/text()')[0] == "Incomplete application"
        assert incomplete_responses_section.xpath('div[@class="statistic-description"]/text()')[0] == "1 SME, 0 large"

        assert completed_responses_section.xpath('div[@class="big-statistic"]/text()')[0] == '1'
        assert completed_responses_section.xpath('div[@class="statistic-name"]/text()')[0] == "Completed application"
        assert completed_responses_section.xpath('div[@class="statistic-description"]/text()')[0] == "0 SME, 1 large"

    def test_dos_brief_displays_application_stats_correctly_when_no_applications(self):
        brief_id = self.brief['briefs']['id']
        self._data_api_client.find_brief_responses.return_value = {"briefResponses": []}
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))
        incomplete_responses_section = document.xpath('//div[@id="incomplete-applications"]')[0]
        completed_responses_section = document.xpath('//div[@id="completed-applications"]')[0]

        assert incomplete_responses_section.xpath('div[@class="big-statistic"]/text()')[0] == '0'
        assert completed_responses_section.xpath('div[@class="big-statistic"]/text()')[0] == '0'
        assert incomplete_responses_section.xpath('div[@class="statistic-name"]/text()')[0] == "Incomplete applications"
        assert completed_responses_section.xpath('div[@class="statistic-name"]/text()')[0] == "Completed applications"
        assert len(incomplete_responses_section.xpath('div[@class="statistic-description"]/text()')) == 0
        assert len(completed_responses_section.xpath('div[@class="statistic-description"]/text()')) == 0

    def test_dos_brief_has_lot_analytics_string(self):
        brief = self.brief['briefs']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief['id']))
        assert res.status_code == 200

        data = res.get_data(as_text=True)
        analytics_string = '<span data-lot="{lot_slug}"></span>'.format(lot_slug=brief['lotSlug'])

        assert analytics_string in data

    def test_dos_brief_has_important_dates(self):
        brief_id = self.brief['briefs']['id']
        self.brief['briefs']['clarificationQuestionsClosedAt'] = "2016-12-14T11:08:28.054129Z"
        self.brief['briefs']['applicationsClosedAt'] = "2016-12-15T11:08:28.054129Z"
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        brief_important_dates = document.xpath(
            '(//table[@class="summary-item-body"])[1]/tbody/tr')
        assert 3 == len(brief_important_dates)
        assert brief_important_dates[0].xpath('td[@class="summary-item-field-first"]')[0].text_content().strip() \
            == "Published"
        assert brief_important_dates[0].xpath('td[@class="summary-item-field"]')[0].text_content().strip() \
            == "Thursday 1 December 2016"
        assert brief_important_dates[1].xpath('td[@class="summary-item-field-first"]')[0].text_content().strip() \
            == "Deadline for asking questions"
        assert brief_important_dates[1].xpath('td[@class="summary-item-field"]')[0].text_content().strip() \
            == "Wednesday 14 December 2016 at 11:08am GMT"
        assert brief_important_dates[2].xpath('td[@class="summary-item-field-first"]')[0].text_content().strip() \
            == "Closing date for applications"
        assert brief_important_dates[2].xpath('td[@class="summary-item-field"]')[0].text_content().strip() \
            == "Thursday 15 December 2016 at 11:08am GMT"

    def test_dos_brief_with_daylight_savings_has_question_deadline_closing_date_forced_to_utc(self):
        brief_id = self.brief['briefs']['id']
        self.brief['briefs']['publishedAt'] = "2016-08-01T23:59:00.000000Z"
        self.brief['briefs']['clarificationQuestionsClosedAt'] = "2016-08-14T23:59:00.000000Z"
        self.brief['briefs']['applicationsClosedAt'] = "2016-08-15T23:59:00.000000Z"
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        brief_important_dates = document.xpath(
            '(//table[@class="summary-item-body"])[1]/tbody/tr')
        assert 3 == len(brief_important_dates)
        # Publish date does not have UTC filter applied
        assert brief_important_dates[0].xpath('td[@class="summary-item-field"]')[0].text_content().strip() \
            == "Monday 1 August 2016"
        # Question deadline and closing date are forced to 11.59pm (UTC+00) on the correct day
        assert brief_important_dates[1].xpath('td[@class="summary-item-field"]')[0].text_content().strip() \
            == "Sunday 14 August 2016 at 11:59pm GMT"
        assert brief_important_dates[2].xpath('td[@class="summary-item-field"]')[0].text_content().strip() \
            == "Monday 15 August 2016 at 11:59pm GMT"

    def test_dos_brief_has_at_least_one_section(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        section_heading = document.xpath('//h2[@class="summary-item-heading"]')[0]
        section_attributes = section_heading.xpath('following-sibling::table[1]/tbody/tr')

        start_date_key = section_attributes[2].xpath('td[1]/span/text()')
        start_date_value = section_attributes[2].xpath('td[2]/span/text()')

        contract_length_key = section_attributes[3].xpath('td[1]/span/text()')
        contract_length_value = section_attributes[3].xpath('td[2]/span/text()')

        assert section_heading.get('id') == 'opportunity-attributes-1'
        assert section_heading.text.strip() == 'Overview'
        assert start_date_key[0] == 'Latest start date'
        assert start_date_value[0] == 'Wednesday 1 March 2017'
        assert contract_length_key[0] == 'Expected contract length'
        assert contract_length_value[0] == '4 weeks'

    def test_dos_brief_has_questions_and_answers(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        xpath = '//h2[@id="clarification-questions"]/following-sibling::table/tbody/tr'
        clarification_questions = document.xpath(xpath)

        number = clarification_questions[0].xpath('td[1]/span/span/text()')[0].strip()
        question = clarification_questions[0].xpath('td[1]/span/text()')[0].strip()
        answer = clarification_questions[0].xpath('td[2]/span/text()')[0].strip()

        assert number == "1."
        assert question == "Why?"
        assert answer == "Because"

    def test_can_apply_to_live_brief(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._assert_start_application(document, brief_id)

    def test_apply_button_visible_if_status_is_draft(self):
        self.brief_responses['briefResponses'][0]['status'] = 'draft'
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._assert_start_application(document, brief_id)

    @pytest.mark.parametrize('status', ['closed', 'unsuccessful', 'cancelled'])
    def test_cannot_apply_to_closed_cancelled_or_unsuccessful_brief(self, status):
        self.brief['briefs']['status'] = status
        self.brief['briefs']['applicationsClosedAt'] = "2016-12-15T11:08:28.054129Z"
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        apply_links = document.xpath('//a[@href="/suppliers/opportunities/{}/responses/start"]'.format(brief_id))
        assert len(apply_links) == 0

    def test_cannot_apply_to_awarded_brief(self):
        self.brief['briefs']['status'] = "awarded"
        self._data_api_client.find_brief_responses.return_value = {
            "briefResponses": [
                {
                    "awardDetails": {"awardedContractStartDate": "2017-08-21", "awardedContractValue": "20000.00"},
                    "id": 14276,
                    "briefId": 1,
                    "createdAt": "2016-12-02T11:09:28.054129Z",
                    "status": "awarded",
                    "submittedAt": "2016-12-05T11:09:28.054129Z",
                    "supplierId": 123456,
                    "supplierName": "Another, Better, Company Limited",
                    "supplierOrganisationSize": "large"
                }
            ]
        }
        self.brief['briefs']['awardedBriefResponseId'] = 14276

        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        apply_links = document.xpath('//a[@href="/suppliers/opportunities/{}/responses/start"]'.format(brief_id))
        assert len(apply_links) == 0

    def test_dos_brief_specialist_role_displays_label(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))

        assert 'qualityAssurance' not in res.get_data(as_text=True)
        assert 'Quality assurance analyst' in res.get_data(as_text=True)

    def _assert_start_application(self, document, brief_id):
        message_list = document.xpath("//p[@class='dmspeak']/text()")
        message = message_list[0] if message_list else None

        assert message == "To apply, you must give evidence for all the essential and nice-to-have " \
            "skills and experience you have."
        assert len(document.xpath(
            '//a[@href="{0}"][contains(normalize-space(text()), normalize-space("{1}"))]'.format(
                "/suppliers/opportunities/{}/responses/start".format(brief_id),
                'Apply',
            )
        )) == 1

    def _assert_view_application(self, document, brief_id):
        assert len(document.xpath(
            '//a[@href="{0}"][contains(normalize-space(text()), normalize-space("{1}"))]'.format(
                "/suppliers/opportunities/{}/responses/result".format(brief_id),
                "View your application",
            )
        )) == 1

    def test_unauthenticated_start_application(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._assert_start_application(document, brief_id)

    def test_buyer_start_application(self):
        self.login_as_buyer()
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._assert_start_application(document, brief_id)

    def test_supplier_start_application(self):
        self.login_as_supplier()
        # mocking that we haven't applied
        self._data_api_client.find_brief_responses.return_value = {
            "briefResponses": []
        }
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._assert_start_application(document, brief_id)

    def test_supplier_applied_view_application_for_live_opportunity(self):
        self.login_as_supplier()
        # fixtures for brief responses have been set up so one of them has the supplier_id we are logged in as.
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._assert_view_application(document, brief_id)

    @pytest.mark.parametrize('status', ['closed', 'unsuccessful', 'cancelled'])
    def test_supplier_applied_view_application_for_closed_unsuccessful_or_cancelled_opportunity(self, status):
        self.login_as_supplier()
        self.brief['briefs']['status'] = status
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._assert_view_application(document, brief_id)

    def test_supplier_applied_view_application_for_opportunity_awarded_to_logged_in_supplier(self):
        self.login_as_supplier()
        self.brief['briefs']['status'] = 'awarded'

        self._data_api_client.find_brief_responses.return_value = {
            "briefResponses": [
                {
                    "awardDetails": {"awardedContractStartDate": "2017-08-21", "awardedContractValue": "20000.00"},
                    "id": 14276,
                    "briefId": 1,
                    "createdAt": "2016-12-02T11:09:28.054129Z",
                    "status": "awarded",
                    "submittedAt": "2016-12-05T11:09:28.054129Z",
                    "supplierId": 1234,
                    "supplierName": "Example Company Limited",
                    "supplierOrganisationSize": "small"
                }
            ]
        }

        self.brief['briefs']['awardedBriefResponseId'] = 14276
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._assert_view_application(document, brief_id)

    def test_supplier_applied_view_application_for_opportunity_pending_awarded_to_logged_in_supplier(self):
        self.login_as_supplier()
        self.brief['briefs']['status'] = 'closed'

        self._data_api_client.find_brief_responses.return_value = {
            "briefResponses": [
                {
                    "awardDetails": {"pending": True},
                    "id": 14276,
                    "briefId": 1,
                    "createdAt": "2016-12-02T11:09:28.054129Z",
                    "status": "pending-awarded",
                    "submittedAt": "2016-12-05T11:09:28.054129Z",
                    "supplierId": 1234,
                    "supplierName": "Example Company Limited",
                    "supplierOrganisationSize": "small"
                }
            ]
        }

        self.brief['briefs']['awardedBriefResponseId'] = 14276
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._assert_view_application(document, brief_id)

    def test_supplier_applied_view_application_for_opportunity_awarded_to_other_supplier(self):
        self.login_as_supplier()

        self._data_api_client.find_brief_responses.return_value = {
            "briefResponses": [
                {
                    "awardDetails": {"awardedContractStartDate": "2017-08-21", "awardedContractValue": "20000.00"},
                    "id": 14276,
                    "briefId": 1,
                    "createdAt": "2016-12-02T11:09:28.054129Z",
                    "status": "awarded",
                    "submittedAt": "2016-12-05T11:09:28.054129Z",
                    "supplierId": 123456,
                    "supplierName": "Another, Better, Company Limited",
                    "supplierOrganisationSize": "large"
                },
                {
                    "id": 14277,
                    "briefId": 1,
                    "createdAt": "2016-12-02T11:09:28.054129Z",
                    "status": "submitted",
                    "submittedAt": "2016-12-05T11:09:28.054129Z",
                    "supplierId": 1234,
                    "supplierName": "Example Company Limited",
                    "supplierOrganisationSize": "small"
                }
            ]
        }
        self.brief['briefs']['status'] = 'awarded'
        self.brief['briefs']['awardedBriefResponseId'] = 14276

        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._assert_view_application(document, brief_id)


class TestBriefPageQandASectionViewQandASessionDetails(BaseBriefPageTest):

    def setup_method(self, method):
        super(TestBriefPageQandASectionViewQandASessionDetails, self).setup_method(method)
        self.brief['briefs']['questionAndAnswerSessionDetails'] = {'many': 'details'}
        self.brief['briefs']['clarificationQuestionsAreClosed'] = False

    def test_live_brief_q_and_a_session(self):
        """
        As long as a:
            A user is not logged in
            The brief is live
            Clarification questions are open
            The brief has Q and A session details
        We should show the:
            link to login and view the QAS details
        """
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        expected_text = "Log in to view question and answer session details"
        expected_link = '/suppliers/opportunities/{}/question-and-answer-session'.format(self.brief_id)

        assert expected_text in document.xpath('.//a[contains(text(),"{}")]'.format(expected_text))[0].text
        assert document.xpath('.//a[contains(text(),"{}")]'.format(expected_text))[0].attrib['href'] == expected_link

    def test_live_brief_q_and_a_session_logged_in(self):
        """
        As long as a:
            Supplier user is logged in
            The brief is live
            Clarification questions are open
            The brief has Q and A session details
        We should show the:
            Link to view the QAS details
        """
        self.login_as_supplier()

        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        expected_text = "View question and answer session details"
        expected_link = '/suppliers/opportunities/{}/question-and-answer-session'.format(self.brief_id)

        assert expected_text in document.xpath('.//a[contains(text(),"{}")]'.format(expected_text))[0].text
        assert document.xpath('.//a[contains(text(),"{}")]'.format(expected_text))[0].attrib['href'] == expected_link

    @pytest.mark.parametrize(
        'brief_data', [
            {'status': 'withdrawn'},
            {'status': 'closed'},
            {'questionAndAnswerSessionDetails': None},
            {'clarificationQuestionsAreClosed': True}
        ]
    )
    def test_brief_q_and_a_session_link_not_shown(self, brief_data):
        """
        On viewing briefs with data like the above the page should load but we should not get the link.
        """
        self.brief['briefs'].update(brief_data)

        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        unexpected_texts = [
            "Log in to view question and answer session details",
            "View question and answer session details"
        ]
        for unexpected_text in unexpected_texts:
            assert len(document.xpath('.//a[contains(text(),"{}")]'.format(unexpected_text))) == 0


class TestBriefPageQandASectionAskAQuestion(BaseBriefPageTest):

    def setup_method(self, method):
        super(TestBriefPageQandASectionAskAQuestion, self).setup_method(method)
        self.brief['briefs']['clarificationQuestionsAreClosed'] = False

    def test_live_brief_ask_a_question(self):
        """
        As long as a:
            A user is not logged in
            The brief is live
            Clarification questions are open
        We should show the:
            link to login and ask a question
        """
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        expected_text = "Log in to ask a question"
        expected_link = '/suppliers/opportunities/{}/ask-a-question'.format(self.brief_id)

        assert expected_text in document.xpath('.//a[contains(text(),"{}")]'.format(expected_text))[0].text
        assert document.xpath('.//a[contains(text(),"{}")]'.format(expected_text))[0].attrib['href'] == expected_link

    def test_live_brief_ask_a_question_logged_in(self):
        """
        As long as a:
            Supplier user is logged in
            The brief is live
            Clarification questions are open
        We should show the:
            Link to ask a question
        """
        self.login_as_supplier()

        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        expected_text = "Ask a question"
        expected_link = '/suppliers/opportunities/{}/ask-a-question'.format(self.brief_id)

        assert expected_text in document.xpath('.//a[contains(text(),"{}")]'.format(expected_text))[0].text
        assert document.xpath('.//a[contains(text(),"{}")]'.format(expected_text))[0].attrib['href'] == expected_link

    @pytest.mark.parametrize(
        'brief_data', [
            {'status': 'withdrawn'},
            {'status': 'closed'},
            {'clarificationQuestionsAreClosed': True}
        ]
    )
    def test_brief_ask_a_question_link_not_shown(self, brief_data):
        """
        On viewing briefs with data like the above the page should load but we should not get either the
        log in to ask a question or ask a question links.
        """
        self.brief['briefs'].update(brief_data)

        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        unexpected_texts = ["Log in to ask a question", "Ask a question"]
        for unexpected_text in unexpected_texts:
            assert len(document.xpath('.//a[contains(text(),"{}")]'.format(unexpected_text))) == 0


class TestAwardedBriefPage(BaseBriefPageTest):
    def setup_method(self, method):
        super(TestAwardedBriefPage, self).setup_method(method)
        self.brief['briefs']['status'] = 'awarded'
        self.brief['briefs']['awardedBriefResponseId'] = 14276

    def test_award_banner_with_winning_supplier_shown_on_awarded_brief_page(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))
        awarded_banner = document.xpath('//div[@class="banner-temporary-message-without-action"]')[0]

        assert 'Awarded to Example Company Limited' in awarded_banner.xpath('h2/text()')[0]

    def test_contract_start_date_visible_on_award_banner(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))
        awarded_banner = document.xpath('//div[@class="banner-temporary-message-without-action"]')[0]

        assert 'Start date: Monday 21 August 2017' in awarded_banner.xpath('p/text()')[0]

    def test_contract_value_visible_on_award_banner_does_not_include_zero_pence(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))
        awarded_banner = document.xpath('//div[@class="banner-temporary-message-without-action"]')[0]

        assert u'Value: £20,000' in awarded_banner.xpath('p/text()')[1]

    def test_contract_value_visible_on_award_banner_includes_non_zero_pence(self):
        self.brief_responses["briefResponses"][1]["awardDetails"]["awardedContractValue"] = "20000.10"
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))
        awarded_banner = document.xpath('//div[@class="banner-temporary-message-without-action"]')[0]

        assert u'Value: £20,000.10' in awarded_banner.xpath('p/text()')[1]

    def test_supplier_size_visible_on_award_banner(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))
        awarded_banner = document.xpath('//div[@class="banner-temporary-message-without-action"]')[0]

        assert 'Company size: SME' in awarded_banner.xpath('p/text()')[2]


class TestCancelledBriefPage(BaseBriefPageTest):
    def setup_method(self, method):
        super(TestCancelledBriefPage, self).setup_method(method)
        self.brief['briefs']['status'] = 'cancelled'

    def test_cancelled_banner_shown_on_cancelled_brief_page(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))
        cancelled_banner = document.xpath('//div[@class="banner-temporary-message-without-action"]')[0]

        assert 'This opportunity was cancelled' in cancelled_banner.xpath('h2/text()')[0]

    def test_explanation_message_shown_on_cancelled_banner(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))
        cancelled_banner = document.xpath('//div[@class="banner-temporary-message-without-action"]')[0]
        expected_message = ("The buyer cancelled this opportunity, for example because they no longer have the budget. "
                            "They may publish an updated version later."
                            )
        assert expected_message in cancelled_banner.xpath('p/text()')[0]


class TestUnsuccessfulBriefPage(BaseBriefPageTest):
    def setup_method(self, method):
        super(TestUnsuccessfulBriefPage, self).setup_method(method)
        self.brief['briefs']['status'] = 'unsuccessful'

    def test_unsuccessful_banner_shown_on_unsuccessful_brief_page(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))
        unsuccessful_banner = document.xpath('//div[@class="banner-temporary-message-without-action"]')[0]

        assert 'No suitable suppliers applied' in unsuccessful_banner.xpath('h2/text()')[0]

    def test_explanation_message_shown_on_unsuccessful_banner(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))
        cancelled_banner = document.xpath('//div[@class="banner-temporary-message-without-action"]')[0]
        expected_message = ("The buyer didn't award this contract because no suppliers met their requirements. "
                            "They may publish an updated version later."
                            )
        assert expected_message in cancelled_banner.xpath('p/text()')[0]


class TestWithdrawnSpecificBriefPage(BaseBriefPageTest):
    def setup_method(self, method):
        super(TestWithdrawnSpecificBriefPage, self).setup_method(method)
        self.brief['briefs']['status'] = "withdrawn"
        self.brief['briefs']['withdrawnAt'] = "2016-11-25T10:47:23.126761Z"

    def test_dos_brief_visible_when_withdrawn(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))

        assert res.status_code == 200

    def test_apply_button_not_visible_for_withdrawn_briefs(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))
        apply_links = document.xpath('//a[@href="/suppliers/opportunities/{}/responses/start"]'.format(self.brief_id))

        assert len(apply_links) == 0

    def test_deadline_text_not_shown(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        page = res.get_data(as_text=True)

        assert 'The deadline for asking questions about this opportunity was ' not in page

    def test_withdrawn_banner_shown_on_withdrawn_brief(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        page = res.get_data(as_text=True)

        assert 'This opportunity was withdrawn on' in page
        assert (
            "You can&#39;t apply for this opportunity now. "
            "The buyer may publish an updated&nbsp;version on the Digital&nbsp;Marketplace"
        ) in page

    @pytest.mark.parametrize('status', ['live', 'closed'])
    def test_withdrawn_banner_not_shown_on_live_and_closed_brief(self, status):
        self.brief['briefs']['status'] = status
        del self.brief['briefs']['withdrawnAt']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        page = res.get_data(as_text=True)

        assert 'This opportunity was withdrawn on' not in page

    def test_dateformat_in_withdrawn_banner_displayed_correctly(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        page = res.get_data(as_text=True)

        assert 'This opportunity was withdrawn on Friday&nbsp;25&nbsp;November&nbsp;2016' in page


class TestCatalogueOfBriefsPage(BaseApplicationTest):
    def setup_method(self, method):
        super(TestCatalogueOfBriefsPage, self).setup_method(method)

        self._data_api_client_patch = mock.patch('app.main.views.marketplace.data_api_client', autospec=True)
        self._data_api_client = self._data_api_client_patch.start()

        self.briefs = self._get_dos_brief_fixture_data(multi=True)
        self._data_api_client.find_briefs.return_value = self.briefs

        self._data_api_client.find_frameworks.return_value = {'frameworks': [
            {
                'id': 3,
                'name': "Digital Outcomes and Specialists 2",
                'slug': "digital-outcomes-and-specialists-2",
                'framework': "digital-outcomes-and-specialists",
                'lots': [
                    {'name': 'Lot 1', 'slug': 'lot-one', 'allowsBrief': True},
                    {'name': 'Lot 2', 'slug': 'lot-two', 'allowsBrief': False},
                    {'name': 'Lot 3', 'slug': 'lot-three', 'allowsBrief': True},
                    {'name': 'Lot 4', 'slug': 'lot-four', 'allowsBrief': True},
                ]
            },
            {
                'id': 1,
                'name': "Digital Outcomes and Specialists",
                'slug': "digital-outcomes-and-specialists",
                'framework': "digital-outcomes-and-specialists",
                'lots': [
                    {'name': 'Lot 1', 'slug': 'lot-one', 'allowsBrief': True},
                    {'name': 'Lot 2', 'slug': 'lot-two', 'allowsBrief': False},
                    {'name': 'Lot 3', 'slug': 'lot-three', 'allowsBrief': True},
                    {'name': 'Lot 4', 'slug': 'lot-four', 'allowsBrief': True},
                ]
            },
            {
                'id': 2,
                'name': "Foobar",
                'slug': "foobar",
                'framework': "foobar",
                'lots': [
                    {'name': 'Lot 1', 'slug': 'lot-one', 'allowsBrief': True},
                    {'name': 'Lot 2', 'slug': 'lot-two', 'allowsBrief': False},
                    {'name': 'Lot 3', 'slug': 'lot-three', 'allowsBrief': True},
                    {'name': 'Lot 4', 'slug': 'lot-four', 'allowsBrief': True},
                ]
            },
        ]}

    def teardown_method(self, method):
        self._data_api_client_patch.stop()

    def normalize_qs(self, qs):
        return {k: set(v) for k, v in iteritems(parse_qs(qs)) if k != "page"}

    def test_catalogue_of_briefs_page(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._data_api_client.find_frameworks.assert_called_once_with()
        regular_args = {
            k: v for k, v in iteritems(self._data_api_client.find_briefs.call_args[1]) if k not in ("status", "lot",)
        }
        assert regular_args == {
            "framework": "digital-outcomes-and-specialists-2,digital-outcomes-and-specialists",
            "page": 1,
            "human": True,
        }
        assert set(self._data_api_client.find_briefs.call_args[1]["status"].split(",")) == {
            "live", "closed", "awarded", "unsuccessful", "cancelled"
        }
        assert set(self._data_api_client.find_briefs.call_args[1]["lot"].split(",")) == {
            "lot-one",
            "lot-three",
            "lot-four",
        }

        heading = document.xpath('normalize-space(//h1/text())')
        assert heading == "Digital Outcomes and Specialists opportunities"
        assert 'lot 1, lot 3 and lot 4' in document.xpath(
            "normalize-space(//div[@class='marketplace-paragraph']/p/text())"
        )

        lot_inputs = document.xpath("//form[@method='get']//input[@name='lot']")
        assert set(element.get("value") for element in lot_inputs) == {
            "lot-one",
            "lot-three",
            "lot-four",
        }
        assert not any(element.get("checked") for element in lot_inputs)

        status_inputs = document.xpath("//form[@method='get']//input[@name='status']")
        assert set(element.get("value") for element in status_inputs) == {"live", "closed"}
        assert not any(element.get("checked") for element in status_inputs)

        ss_elem = document.xpath("//p[@class='search-summary']")[0]
        assert self._normalize_whitespace(self._squashed_element_text(ss_elem)) == "6 opportunities"

        specialist_role_labels = document.xpath("//div[@class='search-result']/ul[2]/li[2]/text()")
        assert len(specialist_role_labels) == 1  # only one brief has a specialist role so only one label should exist
        assert specialist_role_labels[0].strip() == "Business analyst"

    def test_catalogue_of_briefs_page_filtered(self):
        original_url = "/digital-outcomes-and-specialists/opportunities?page=2&status=live&lot=lot-one&lot=lot-three"
        res = self.client.get(original_url)
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._data_api_client.find_frameworks.assert_called_once_with()
        regular_args = {
            k: v for k, v in iteritems(self._data_api_client.find_briefs.call_args[1]) if k not in ("status", "lot",)
        }
        assert regular_args == {
            "framework": "digital-outcomes-and-specialists-2,digital-outcomes-and-specialists",
            "page": 2,
            "human": True,
        }
        assert set(self._data_api_client.find_briefs.call_args[1]["status"].split(",")) == {"live"}
        assert set(self._data_api_client.find_briefs.call_args[1]["lot"].split(",")) == {"lot-one", "lot-three"}

        heading = document.xpath('normalize-space(//h1/text())')
        assert heading == "Digital Outcomes and Specialists opportunities"
        assert 'lot 1, lot 3 and lot 4' in document.xpath(
            "normalize-space(//div[@class='marketplace-paragraph']/p/text())"
        )

        lot_inputs = document.xpath("//form[@method='get']//input[@name='lot']")
        assert {
            element.get("value"): bool(element.get("checked"))
            for element in lot_inputs
        } == {
            "lot-one": True,
            "lot-three": True,
            "lot-four": False,
        }

        status_inputs = document.xpath("//form[@method='get']//input[@name='status']")
        assert {
            element.get("value"): bool(element.get("checked"))
            for element in status_inputs
        } == {
            "live": True,
            "closed": False,
        }

        parsed_original_url = urlparse(original_url)
        parsed_prev_url = urlparse(document.xpath("//li[@class='previous']/a/@href")[0])
        parsed_next_url = urlparse(document.xpath("//li[@class='next']/a/@href")[0])
        assert parsed_original_url.path == parsed_prev_url.path == parsed_next_url.path

        assert self.normalize_qs(parsed_original_url.query) == \
            self.normalize_qs(parsed_next_url.query) == \
            self.normalize_qs(parsed_prev_url.query)

        ss_elem = document.xpath("//p[@class='search-summary']")[0]
        assert self._normalize_whitespace(self._squashed_element_text(ss_elem)) == "6 results"

    def test_catalogue_of_briefs_page_filtered_all_options_selected(self):
        original_url = "/digital-outcomes-and-specialists/opportunities?status=live&lot=lot-one&lot=lot-three"\
            "&status=closed&lot=lot-four"
        res = self.client.get(original_url)
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self._data_api_client.find_frameworks.assert_called_once_with()
        regular_args = {
            k: v for k, v in iteritems(self._data_api_client.find_briefs.call_args[1]) if k not in ("status", "lot",)
        }
        assert regular_args == {
            "framework": "digital-outcomes-and-specialists-2,digital-outcomes-and-specialists",
            "page": 1,
            "human": True,
        }
        assert set(self._data_api_client.find_briefs.call_args[1]["status"].split(",")) == {
            "live", "closed", "awarded", "unsuccessful", "cancelled"
        }
        assert set(self._data_api_client.find_briefs.call_args[1]["lot"].split(",")) == {
            "lot-one",
            "lot-three",
            "lot-four",
        }

        heading = document.xpath('normalize-space(//h1/text())')
        assert heading == "Digital Outcomes and Specialists opportunities"
        assert 'lot 1, lot 3 and lot 4' in document.xpath(
            "normalize-space(//div[@class='marketplace-paragraph']/p/text())"
        )

        lot_inputs = document.xpath("//form[@method='get']//input[@name='lot']")
        assert {
            element.get("value"): bool(element.get("checked"))
            for element in lot_inputs
        } == {
            "lot-one": True,
            "lot-three": True,
            "lot-four": True,
        }

        status_inputs = document.xpath("//form[@method='get']//input[@name='status']")
        assert {
            element.get("value"): bool(element.get("checked"))
            for element in status_inputs
        } == {
            "live": True,
            "closed": True,
        }

        parsed_original_url = urlparse(original_url)
        parsed_next_url = urlparse(document.xpath("//li[@class='next']/a/@href")[0])
        assert parsed_original_url.path == parsed_next_url.path

        assert self.normalize_qs(parsed_original_url.query) == self.normalize_qs(parsed_next_url.query)

        ss_elem = document.xpath("//p[@class='search-summary']")[0]
        assert self._normalize_whitespace(self._squashed_element_text(ss_elem)) == "6 results"

    def test_catalogue_of_briefs_404_if_invalid_status(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities?status=pining-for-fjords')
        assert res.status_code == 404

    def test_catalogue_of_briefs_page_shows_pagination_if_more_pages(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200
        page = res.get_data(as_text=True)
        document = html.fromstring(page)

        assert '<li class="previous">' in page
        assert '<li class="next">' in page
        prev_url = str(document.xpath('string(//li[@class="previous"]/a/@href)'))
        next_url = str(document.xpath('string(//li[@class="next"]/a/@href)'))
        assert prev_url.endswith('/opportunities?page=1')
        assert next_url.endswith('/opportunities?page=3')

    def test_no_pagination_if_no_more_pages(self):
        del self.briefs['links']['prev']
        del self.briefs['links']['next']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200
        page = res.get_data(as_text=True)

        assert '<li class="previous">' not in page
        assert '<li class="next">' not in page

    def test_catalogue_of_briefs_page_404_for_framework_that_does_not_exist(self):
        res = self.client.get('/digital-giraffes-and-monkeys/opportunities')

        assert res.status_code == 404
        self._data_api_client.find_frameworks.assert_called_once_with()

    def test_briefs_search_does_not_have_js_hidden_filter_button(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        filter_button = document.xpath('//button[@class="button-save" and normalize-space(text())="Filter"]')
        assert len(filter_button) == 1

    def test_opportunity_status_and_published_date(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        live_opportunity_published_at = document.xpath(
            '//div[@class="search-result"][1]//li[@class="search-result-metadata-item"]'
        )[-2].text_content().strip()
        assert live_opportunity_published_at == "Published: Wednesday 9 March 2016"

        live_opportunity_closing_at = document.xpath(
            '//div[@class="search-result"][1]//li[@class="search-result-metadata-item"]'
        )[-1].text_content().strip()
        assert live_opportunity_closing_at == "Closing: Thursday 24 March 2016"

        closed_opportunity_status = document.xpath(
            '//div[@class="search-result"][3]//li[@class="search-result-metadata-item"]'
        )[-1].text_content().strip()
        assert closed_opportunity_status == "Closed"

        awarded_opportunity_status = document.xpath(
            '//div[@class="search-result"][4]//li[@class="search-result-metadata-item"]'
        )[-1].text_content().strip()
        assert awarded_opportunity_status == "Closed"

        cancelled_opportunity_status = document.xpath(
            '//div[@class="search-result"][5]//li[@class="search-result-metadata-item"]'
        )[-1].text_content().strip()
        assert cancelled_opportunity_status == "Closed"

        unsuccessful_opportunity_status = document.xpath(
            '//div[@class="search-result"][6]//li[@class="search-result-metadata-item"]'
        )[-1].text_content().strip()
        assert unsuccessful_opportunity_status == "Closed"


@mock.patch('app.main.views.marketplace.data_api_client', autospec=True)
class TestGCloudHomepageLinks(BaseApplicationTest):

    mock_live_g_cloud_framework = {
        "framework": "g-cloud",
        "slug": "g-cloud-x",
        "status": "live",
        "id": 5
    }

    @pytest.mark.parametrize('framework_slug, gcloud_content',
                             (('g-cloud-8', 'Find cloud technology and support'),
                              ('g-cloud-9', 'Find cloud hosting, software and support')))
    def test_g_cloud_homepage_content_is_correct(self, data_api_client, framework_slug, gcloud_content):
        with self.app.app_context():
            data_api_client.find_frameworks.return_value = {
                "frameworks": [self.mock_live_g_cloud_framework.copy()]
            }
            data_api_client.find_frameworks.return_value['frameworks'][0].update({'slug': framework_slug})

            res = self.client.get("/")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            link_texts = [item.text_content().strip() for item in document.cssselect('.browse-list-item a')]
            assert link_texts[-2] == gcloud_content
            assert link_texts[-1] == 'Buy physical datacentre space'
