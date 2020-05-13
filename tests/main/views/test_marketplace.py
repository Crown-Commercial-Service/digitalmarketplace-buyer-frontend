# coding=utf-8
import json
import re
from urllib.parse import urlparse, parse_qs

from flask import current_app
from lxml import html
import mock
import pytest

from ...helpers import BaseApplicationTest, BaseAPIClientMixin

from dmtestutils.api_model_stubs import FrameworkStub
from dmtestutils.api_model_stubs.lot import dos_lots, cloud_lots


class APIClientMixin(BaseAPIClientMixin):
    data_api_client_patch_path = 'app.main.views.marketplace.data_api_client'
    search_api_client_patch_path = 'app.main.views.marketplace.search_api_client'


class TestApplication(APIClientMixin, BaseApplicationTest):

    def test_analytics_code_should_be_in_javascript(self):
        res = self.client.get('/static/javascripts/application.js')
        assert res.status_code == 200
        assert 'trackPageview' in res.get_data(as_text=True)

    def test_should_display_cookie_banner(self):
        res = self.client.get('/')
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        cookie_banner = document.xpath('//div[@id="dm-cookie-banner"]')
        assert cookie_banner[0].xpath('//h2//text()')[0].strip() == "Can we store analytics cookies on your device?"
        assert len(self.data_api_client.find_frameworks.call_args_list) == 2

    def test_google_verification_code_shown_on_homepage(self):
        res = self.client.get('/')
        assert res.status_code == 200
        assert 'name="google-site-verification" content="NotARealVerificationKey"' in res.get_data(as_text=True)
        assert len(self.data_api_client.find_frameworks.call_args_list) == 2


class TestHomepageAccountCreationVirtualPageViews(APIClientMixin, BaseApplicationTest):

    def test_data_analytics_track_page_view_is_shown_if_account_created_flash_message(self):
        with self.client.session_transaction() as session:
            session['_flashes'] = [('track-page-view', 'buyers?account-created=true')]

        res = self.client.get("/")
        data = res.get_data(as_text=True)

        assert 'data-analytics="trackPageView" data-url="buyers?account-created=true"' in data
        # however this should not be shown as a regular flash message
        flash_banner_match = re.search(r'<p class="banner-message">\s*(.*)', data, re.MULTILINE)
        assert flash_banner_match is None, "Unexpected flash banner message '{}'.".format(
            flash_banner_match.groups()[0])

        assert len(self.data_api_client.find_frameworks.call_args_list) == 2

    def test_data_analytics_track_page_view_not_shown_if_no_account_created_flash_message(self):
        res = self.client.get("/")
        data = res.get_data(as_text=True)

        assert 'data-analytics="trackPageView" data-url="buyers?account-created=true"' not in data
        assert len(self.data_api_client.find_frameworks.call_args_list) == 2


class TestHomepageBrowseList(APIClientMixin, BaseApplicationTest):

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

    def test_dos_links_are_shown(self):
        self.data_api_client.find_frameworks.return_value = {
            "frameworks": [
                self.mock_live_dos_1_framework
            ]
        }

        res = self.client.get("/")
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        link_texts = [item.text_content().strip() for item in document.cssselect('#app-buyer-nav a')]
        assert link_texts[0] == "Find an individual specialist"
        assert link_texts[-1] == "Find physical datacentre space"
        assert "Find specialists to work on digital projects" not in link_texts

    def test_links_are_for_existing_dos_framework_when_a_new_dos_framework_in_standstill_exists(self):
        mock_standstill_dos_2_framework = self.mock_live_dos_2_framework.copy()
        mock_standstill_dos_2_framework.update({"status": "standstill"})

        self.data_api_client.find_frameworks.return_value = {
            "frameworks": [
                self.mock_live_dos_1_framework,
                mock_standstill_dos_2_framework,
            ]
        }

        res = self.client.get("/")
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        link_locations = [item.values()[1] for item in document.cssselect('#app-buyer-nav a')]

        lots = ['digital-specialists', 'digital-outcomes', 'user-research-participants', 'user-research-studios']
        dos_base_path = '/buyers/frameworks/digital-outcomes-and-specialists/requirements/{}'

        for index, lot_slug in enumerate(lots):
            assert link_locations[index] == dos_base_path.format(lot_slug)

    def test_links_are_for_the_newest_live_dos_framework_when_multiple_live_dos_frameworks_exist(self):
        self.data_api_client.find_frameworks.return_value = {
            "frameworks": [
                self.mock_live_dos_1_framework,
                self.mock_live_dos_2_framework,
            ]
        }

        res = self.client.get("/")
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        link_locations = [item.values()[1] for item in document.cssselect('#app-buyer-nav a')]

        lots = ['digital-specialists', 'digital-outcomes', 'user-research-participants', 'user-research-studios']
        dos2_base_path = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/{}'

        for index, lot_slug in enumerate(lots):
            assert link_locations[index] == dos2_base_path.format(lot_slug)

    def test_links_are_for_live_dos_framework_when_expired_dos_framework_exists(self):
        mock_expired_dos_1_framework = self.mock_live_dos_1_framework.copy()
        mock_expired_dos_1_framework.update({"status": "expired"})

        self.data_api_client.find_frameworks.return_value = {
            "frameworks": [
                mock_expired_dos_1_framework,
                self.mock_live_dos_2_framework,
            ]
        }

        res = self.client.get("/")
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        link_locations = [item.values()[1] for item in document.cssselect('#app-buyer-nav a')]

        lots = ['digital-specialists', 'digital-outcomes', 'user-research-participants', 'user-research-studios']
        dos2_base_path = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/{}'

        for index, lot_slug in enumerate(lots):
            assert link_locations[index] == dos2_base_path.format(lot_slug)

    def test_non_dos_links_are_shown_if_no_live_dos_framework(self):
        mock_expired_dos_1_framework = self.mock_live_dos_1_framework.copy()
        mock_expired_dos_1_framework.update({"status": "expired"})
        mock_expired_dos_2_framework = self.mock_live_dos_2_framework.copy()
        mock_expired_dos_2_framework.update({"status": "expired"})
        mock_g_cloud_9_framework = self.mock_live_g_cloud_9_framework.copy()

        self.data_api_client.find_frameworks.return_value = {
            "frameworks": [
                mock_expired_dos_1_framework,
                mock_expired_dos_2_framework,
                mock_g_cloud_9_framework,
            ]
        }

        res = self.client.get("/")
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        link_texts = [item.text_content().strip() for item in document.cssselect('#app-buyer-nav a')]
        assert link_texts[0] == "Find cloud hosting, software and support"
        assert link_texts[1] == "Find physical datacentre space"
        assert len(link_texts) == 2


class TestHomepageSidebarMessage(APIClientMixin, BaseApplicationTest):

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
    def _assert_supplier_nav_is_empty(response_data):
        document = html.fromstring(response_data)
        supplier_nav_contents = document.xpath('//nav[@id="app-supplier-nav"]/*')
        assert len(supplier_nav_contents) == 0

    @staticmethod
    def _assert_supplier_nav_is_not_empty(response_data):
        document = html.fromstring(response_data)
        supplier_nav_contents = document.xpath('//nav[@id="app-supplier-nav"]/*')
        assert len(supplier_nav_contents) > 0
        assert supplier_nav_contents[0].xpath('text()')[0].strip() == "Sell services"

    def _load_homepage(self, framework_slugs_and_statuses, framework_messages):
        self.data_api_client.find_frameworks.return_value = self._find_frameworks(framework_slugs_and_statuses)
        res = self.client.get('/')
        assert res.status_code == 200
        response_data = res.get_data(as_text=True)

        if framework_messages:
            self._assert_supplier_nav_is_not_empty(response_data)
            for message in framework_messages:
                assert message in response_data
        else:
            self._assert_supplier_nav_is_empty(response_data)

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

    def test_homepage_sidebar_messages_when_logged_out(self):
        self.data_api_client.find_frameworks.return_value = self._find_frameworks([
            ('digital-outcomes-and-specialists', 'live')
        ])
        res = self.client.get('/')
        assert res.status_code == 200
        response_data = res.get_data(as_text=True)

        document = html.fromstring(response_data)

        supplier_links = document.cssselect("#app-supplier-nav a")
        supplier_link_texts = [item.xpath("normalize-space(string())") for item in supplier_links]

        assert 'View Digital Outcomes and Specialists opportunities' in supplier_link_texts
        assert 'Become a supplier' in supplier_link_texts
        assert 'See Digital Marketplace sales figures' in supplier_link_texts

    def test_homepage_sidebar_messages_when_logged_in(self):
        self.data_api_client.find_frameworks.return_value = self._find_frameworks([
            ('digital-outcomes-and-specialists', 'live')
        ])
        self.login_as_supplier()

        res = self.client.get('/')
        assert res.status_code == 200
        response_data = res.get_data(as_text=True)

        document = html.fromstring(response_data)

        supplier_links = document.cssselect("#app-supplier-nav a")
        supplier_link_texts = [item.xpath("normalize-space(string())") for item in supplier_links]

        assert 'View Digital Outcomes and Specialists opportunities' in supplier_link_texts
        assert 'Become a supplier' not in supplier_link_texts

    # here we've given an valid framework with a valid status but there is no message.yml file to read from
    def test_g_cloud_6_open_blows_up(self):
        framework_slugs_and_statuses = [
            ('g-cloud-6', 'open')
        ]

        self.data_api_client.find_frameworks.return_value = self._find_frameworks(framework_slugs_and_statuses)
        res = self.client.get('/')
        assert res.status_code == 500


class TestStaticMarketplacePages(BaseApplicationTest):

    def test_cookie_page(self):
        res = self.client.get('/cookies')
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        assert len(document.xpath('//h1[contains(text(), "Cookies on Digital Marketplace")]')) == 1

    def test_terms_and_conditions_page(self):
        res = self.client.get('/terms-and-conditions')
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        assert len(document.xpath('//h1[contains(text(), "Terms and conditions")]')) == 1

    def test_external_404_makes_all_links_absolute(self):
        # Get the normal 404 page and a list of the relative URLs it contains links to
        response1 = self.client.get("/does-not-exist-404")
        assert response1.status_code == 404
        regular_404_document = html.fromstring(response1.get_data(as_text=True))
        regular_relative_links = regular_404_document.xpath('//a[starts-with(@href, "/")]')
        regular_relative_forms = regular_404_document.xpath('//form[starts-with(@action, "/")]')
        relative_urls = [link.get("href") for link in regular_relative_links] + \
                        [form.get("action") for form in regular_relative_forms]

        # Get the "external" 404 page and check it doesn't contain any relative URLs
        response2 = self.client.get("/404")
        assert response2.status_code == 404
        external_404_document = html.fromstring(response2.get_data(as_text=True))
        external_relative_links = external_404_document.xpath('//a[starts-with(@href, "/")]')
        external_relative_forms = external_404_document.xpath('//form[starts-with(@action, "/")]')
        assert len(external_relative_links) == len(external_relative_forms) == 0

        # Check that there is an absolute URL in the external 404 page for every relative URL in the normal 404 page
        external_links = external_404_document.xpath('//a')
        external_forms = external_404_document.xpath('//form')
        external_urls = [link.get("href") for link in external_links] + [form.get("action") for form in external_forms]
        for relative_url in relative_urls:
            assert "http://localhost{}".format(relative_url) in external_urls


class BaseBriefPageTest(APIClientMixin, BaseApplicationTest):
    def setup_method(self, method):
        super().setup_method(method)

        self.brief = self._get_dos_brief_fixture_data()
        self.brief_responses = self._get_dos_brief_responses_fixture_data()
        self.brief_id = self.brief['briefs']['id']
        self.data_api_client.find_frameworks.return_value = self._get_frameworks_list_fixture_data()
        self.data_api_client.get_brief.return_value = self.brief
        self.data_api_client.find_brief_responses.return_value = self.brief_responses


class TestBriefPage(BaseBriefPageTest):

    @pytest.mark.parametrize('framework_family, expected_status_code',
                             (
                                 ('digital-outcomes-and-specialists', 200),
                                 ('g-cloud', 404),
                             ))
    def test_404_on_framework_that_does_not_support_further_competition(self, framework_family, expected_status_code):
        brief_id = self.brief['briefs']['id']
        res = self.client.get(f'/{framework_family}/opportunities/{brief_id}')
        assert res.status_code == expected_status_code

        assert self.data_api_client.find_frameworks.mock_calls == [
            mock.call(),
        ]

    def test_dos_brief_404s_if_brief_is_draft(self):
        self.brief['briefs']['status'] = 'draft'
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 404

        assert self.data_api_client.mock_calls == [
            mock.call.find_frameworks(),
            mock.call.get_brief(str(brief_id)),
        ]

    def test_dos_brief_has_correct_title(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        page_heading = document.cssselect("span.govuk-caption-l + h1.govuk-heading-l")
        assert page_heading

        heading = page_heading[0]
        assert heading.text == self.brief["briefs"]["title"]

        caption = heading.getprevious()
        assert caption.text == self.brief["briefs"]["organisation"]

    def _assert_all_normal_api_calls(self):
        assert self.data_api_client.mock_calls == [
            mock.call.find_frameworks(),
            mock.call.get_brief(str(self.brief_id)),
            mock.call.find_brief_responses(
                brief_id=str(self.brief_id),
                status='draft,submitted,pending-awarded,awarded',
                with_data=False,
            ),
        ]

    @pytest.mark.parametrize('status', ['closed', 'unsuccessful', 'cancelled', 'awarded'])
    def test_only_one_banner_at_once_brief_page(self, status):
        self.brief['briefs']['status'] = status
        if self.brief['briefs']['status'] == 'awarded':
            self.brief['briefs']['awardedBriefResponseId'] = 14276
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(self.brief_id))
        document = html.fromstring(res.get_data(as_text=True))
        number_of_banners = len(document.xpath('//div[@class="banner-temporary-message-without-action"]'))

        assert number_of_banners == 1

        self._assert_all_normal_api_calls()

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

        self._assert_all_normal_api_calls()

    def test_application_stats_pluralised_correctly(self):
        brief_id = self.brief['briefs']['id']
        self.data_api_client.find_brief_responses.return_value = {
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
        self.data_api_client.find_brief_responses.return_value = {"briefResponses": []}
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

    @pytest.mark.parametrize(
        'lot_slug, assessment_type', [
            ('digital-outcomes', 'written proposal'),
            ('digital-specialists', 'work history'),
            ('user-research-participants', 'written proposal'),
        ]
    )
    def test_dos_brief_displays_mandatory_evaluation_method_for_lot(self, lot_slug, assessment_type):
        brief = self.brief.copy()
        brief['briefs']['lot'] = lot_slug
        brief['briefs']['lotSlug'] = lot_slug
        brief['briefs']['status'] = 'live'
        brief['briefs']['publishedAt'] = '2019-01-02T00:00:00.000000Z'
        brief['briefs']['frameworkSlug'] = 'digital-outcomes-and-specialists-4'
        self.data_api_client.get_brief.return_value = brief

        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief['briefs']['id']))

        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))
        section_heading = document.xpath(
            '//h2[@class="summary-item-heading"][contains(text(), "How suppliers will be evaluated")]'
        )[0]
        section_description = section_heading.xpath('following-sibling::p')[0]
        assert section_description.text.strip() == f'All suppliers will be asked to provide a {assessment_type}.'

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
        self.data_api_client.find_brief_responses.return_value = {
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
        assert document.xpath(
            "//form[@method='get'][normalize-space(string(.//button))=$t]/@action",
            t="Apply for this opportunity",
        ) == ["/suppliers/opportunities/{}/responses/start".format(brief_id)]

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
        self.data_api_client.find_brief_responses.return_value = {
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

        self._assert_all_normal_api_calls()

    def test_supplier_applied_view_application_for_opportunity_awarded_to_logged_in_supplier(self):
        self.login_as_supplier()
        self.brief['briefs']['status'] = 'awarded'

        self.data_api_client.find_brief_responses.return_value = {
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

        self._assert_all_normal_api_calls()

    def test_supplier_applied_view_application_for_opportunity_pending_awarded_to_logged_in_supplier(self):
        self.login_as_supplier()
        self.brief['briefs']['status'] = 'closed'

        self.data_api_client.find_brief_responses.return_value = {
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

        self._assert_all_normal_api_calls()

    def test_supplier_applied_view_application_for_opportunity_awarded_to_other_supplier(self):
        self.login_as_supplier()

        self.data_api_client.find_brief_responses.return_value = {
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

        self._assert_all_normal_api_calls()


class TestBriefPageQandASectionViewQandASessionDetails(BaseBriefPageTest):

    def setup_method(self, method):
        super().setup_method(method)
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
        super().setup_method(method)
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
        super().setup_method(method)
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
        super().setup_method(method)
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
        super().setup_method(method)
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
        super().setup_method(method)
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


class TestCatalogueOfBriefsPage(APIClientMixin, BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)

        self.search_api_client.search.return_value = self._get_dos_brief_search_api_response_fixture_data()

        self.search_api_client.aggregate.side_effect = [
            self._get_dos_brief_search_api_aggregations_response_outcomes_fixture_data(),
            self._get_dos_brief_search_api_aggregations_response_specialists_fixture_data(),
            self._get_dos_brief_search_api_aggregations_response_user_research_fixture_data(),
        ]

        self.data_api_client.find_frameworks.return_value = {'frameworks': [
            FrameworkStub(
                id=3, slug='digital-outcomes-and-specialists-2', status='live', lots=dos_lots(),
                has_further_competition=True
            ).response(),
            FrameworkStub(
                id=1, slug='digital-outcomes-and-specialists', status='expired', lots=dos_lots(),
                has_further_competition=True
            ).response(),
            FrameworkStub(
                id=2, slug='foobar', status='expired', lots=cloud_lots()
            ).response(),
            FrameworkStub(
                id=4, slug='g-cloud-9', status='live', lots=cloud_lots()
            ).response()
        ]}

    def normalize_qs(self, qs):
        return {k: set(v) for k, v in parse_qs(qs).items() if k != "page"}

    @pytest.mark.parametrize('framework_family, expected_status_code',
                             (
                                 ('digital-outcomes-and-specialists', 200),
                                 ('g-cloud', 404),
                             ))
    def test_404_on_framework_that_does_not_support_further_competition(self, framework_family, expected_status_code):
        res = self.client.get(f'/{framework_family}/opportunities')
        assert res.status_code == expected_status_code

    def test_catalogue_of_briefs_page(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self.data_api_client.find_frameworks.assert_called_once_with()

        self.search_api_client.search.assert_called_once_with(
            index='briefs-digital-outcomes-and-specialists',
            doc_type='briefs',
            statusOpenClosed='open,closed'
        )

        heading = document.xpath('normalize-space(//h1/text())')
        assert heading == "Digital Outcomes and Specialists opportunities"
        assert ('View buyer requirements for digital outcomes, '
                'digital specialists and user research participants') in document.xpath(
            "normalize-space(//div[@class='marketplace-paragraph']/p/text())"
        )

        lot_filters = document.xpath("//form[@method='get']//ul[@class='lot-filters--last-list']//a")
        assert set(element.text for element in lot_filters) == {
            "Digital outcomes (629)",
            "Digital specialists (827)",
            "User research participants (39)",
        }
        assert len(document.xpath("//form[@method='get']//ul[@class='lot-filters--last-list']//strong")) == 0

        status_inputs = document.xpath("//form[@method='get']//input[@name='statusOpenClosed']")
        assert set(element.get("value") for element in status_inputs) == {"open", "closed"}
        assert not any(element.get("checked") for element in status_inputs)

        location_inputs = document.xpath("//form[@method='get']//input[@name='location']")
        assert {
            element.get("value"): bool(element.get("checked"))
            for element in location_inputs
        } == {
            "scotland": False,
            "north east england": False,
            "north west england": False,
            "yorkshire and the humber": False,
            "east midlands": False,
            "west midlands": False,
            "east of england": False,
            "wales": False,
            "london": False,
            "south east england": False,
            "south west england": False,
            "northern ireland": False,
            "international (outside the uk)": False,
            "offsite": False,
        }

        q_inputs = document.xpath("//form[@method='get']//input[@name='q']")
        assert tuple(element.get("value") for element in q_inputs) == ("",)

        ss_elem = document.xpath("//p[@class='search-summary']")[0]
        assert self._normalize_whitespace(self._squashed_element_text(ss_elem)) == "864 results found in All categories"

        specialist_role_labels = document.xpath("//div[@class='search-result']/ul[2]/li[2]/text()")
        assert len(specialist_role_labels) == 2  # only two briefs has a specialist role so only one label should exist
        assert specialist_role_labels[0].strip() == "Developer"
        assert specialist_role_labels[1].strip() == "Technical architect"

    def test_catalogue_of_briefs_page_filtered(self):
        original_url = "/digital-outcomes-and-specialists/opportunities?page=2"\
            "&statusOpenClosed=open&lot=digital-outcomes&location=wales&location=london"
        res = self.client.get(original_url)
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        self.data_api_client.find_frameworks.assert_called_once_with()
        self.search_api_client.search.assert_called_once_with(
            index='briefs-digital-outcomes-and-specialists',
            doc_type='briefs',
            statusOpenClosed='open',
            lot='digital-outcomes',
            location='wales,london',
            page='2',
        )

        heading = document.xpath('normalize-space(//h1/text())')
        assert heading == "Digital Outcomes and Specialists opportunities"
        assert ('View buyer requirements for digital outcomes, '
                'digital specialists and user research participants') in document.xpath(
            "normalize-space(//div[@class='marketplace-paragraph']/p/text())"
        )

        all_categories_return_link = document.xpath("//form[@method='get']//div[@class='lot-filters']/ul/li/a")[0]
        assert all_categories_return_link.text == 'All categories'

        lot_filters = document.xpath("//form[@method='get']//div[@class='lot-filters']//ul//ul/li/*[1]")
        assert {
            element.text: element.tag
            for element in lot_filters
        } == {
            'Digital outcomes (629)': 'strong',
            'Digital specialists (827)': 'a',
            'User research participants (39)': 'a',
        }

        assert document.xpath(
            "//a[@id=$i][contains(@class, $c)][normalize-space(string())=normalize-space($t)][@href=$h]",
            i="dm-clear-all-filters",
            c="clear-filters-link",
            t="Clear filters",
            h="/digital-outcomes-and-specialists/opportunities?lot=digital-outcomes",
        )

        status_inputs = document.xpath("//form[@method='get']//input[@name='statusOpenClosed']")
        assert {
            element.get("value"): bool(element.get("checked"))
            for element in status_inputs
        } == {
            "open": True,
            "closed": False,
        }

        location_inputs = document.xpath("//form[@method='get']//input[@name='location']")
        assert {
            element.get("value"): bool(element.get("checked"))
            for element in location_inputs
        } == {
            "scotland": False,
            "north east england": False,
            "north west england": False,
            "yorkshire and the humber": False,
            "east midlands": False,
            "west midlands": False,
            "east of england": False,
            "wales": True,
            "london": True,
            "south east england": False,
            "south west england": False,
            "northern ireland": False,
            "international (outside the uk)": False,
            "offsite": False,
        }

        q_inputs = document.xpath("//form[@method='get']//input[@name='q']")
        assert tuple(element.get("value") for element in q_inputs) == ("",)

        parsed_original_url = urlparse(original_url)
        parsed_prev_url = urlparse(document.xpath("//li[@class='previous']/a/@href")[0])
        parsed_next_url = urlparse(document.xpath("//li[@class='next']/a/@href")[0])
        assert parsed_original_url.path == parsed_prev_url.path == parsed_next_url.path

        assert self.normalize_qs(parsed_original_url.query) == \
            self.normalize_qs(parsed_next_url.query) == \
            self.normalize_qs(parsed_prev_url.query)

        ss_elem = document.xpath("//p[@class='search-summary']")[0]
        assert self._normalize_whitespace(self._squashed_element_text(ss_elem)) == \
            "864 results found in Digital outcomes"

    def test_catalogue_of_briefs_page_filtered_keyword_search(self):
        original_url = "/digital-outcomes-and-specialists/opportunities?page=2"\
            "&statusOpenClosed=open&lot=digital-outcomes"\
            "&location=offsite&q=Richie+Poldy"
        res = self.client.get(original_url)
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        self.data_api_client.find_frameworks.assert_called_once_with()
        self.search_api_client.search.assert_called_once_with(
            index='briefs-digital-outcomes-and-specialists',
            doc_type='briefs',
            statusOpenClosed='open',
            lot='digital-outcomes',
            location='offsite',
            page='2',
            q='Richie Poldy',
        )

        heading = document.xpath('normalize-space(//h1/text())')
        assert heading == "Digital Outcomes and Specialists opportunities"
        assert ('View buyer requirements for digital outcomes, '
                'digital specialists and user research participants') in document.xpath(
            "normalize-space(//div[@class='marketplace-paragraph']/p/text())"
        )

        all_categories_return_link = document.xpath("//form[@method='get']//div[@class='lot-filters']/ul/li/a")[0]
        assert all_categories_return_link.text == 'All categories'

        lot_filters = document.xpath("//form[@method='get']//div[@class='lot-filters']//ul//ul/li/*[1]")
        assert {
            element.text: element.tag
            for element in lot_filters
        } == {
            'Digital outcomes (629)': 'strong',
            'Digital specialists (827)': 'a',
            'User research participants (39)': 'a',
        }

        assert document.xpath(
            "//a[@id=$i][contains(@class, $c)][normalize-space(string())=normalize-space($t)][@href=$h]",
            i="dm-clear-all-filters",
            c="clear-filters-link",
            t="Clear filters",
            h="/digital-outcomes-and-specialists/opportunities?lot=digital-outcomes&q=Richie+Poldy",
        )

        status_inputs = document.xpath("//form[@method='get']//input[@name='statusOpenClosed']")
        assert {
            element.get("value"): bool(element.get("checked"))
            for element in status_inputs
        } == {
            "open": True,
            "closed": False,
        }

        location_inputs = document.xpath("//form[@method='get']//input[@name='location']")
        assert {
            element.get("value"): bool(element.get("checked"))
            for element in location_inputs
        } == {
            "scotland": False,
            "north east england": False,
            "north west england": False,
            "yorkshire and the humber": False,
            "east midlands": False,
            "west midlands": False,
            "east of england": False,
            "wales": False,
            "london": False,
            "south east england": False,
            "south west england": False,
            "northern ireland": False,
            "international (outside the uk)": False,
            "offsite": True,
        }

        q_inputs = document.xpath("//form[@method='get']//input[@name='q']")
        assert tuple(element.get("value") for element in q_inputs) == ("Richie Poldy",)

        parsed_original_url = urlparse(original_url)
        parsed_prev_url = urlparse(document.xpath("//li[@class='previous']/a/@href")[0])
        parsed_next_url = urlparse(document.xpath("//li[@class='next']/a/@href")[0])
        assert parsed_original_url.path == parsed_prev_url.path == parsed_next_url.path

        assert self.normalize_qs(parsed_original_url.query) == \
            self.normalize_qs(parsed_next_url.query) == \
            self.normalize_qs(parsed_prev_url.query)

        ss_elem = document.xpath("//p[@class='search-summary']")[0]
        assert self._normalize_whitespace(self._squashed_element_text(ss_elem)) == \
            "864 results found containing Richie Poldy in Digital outcomes"

    def test_catalogue_of_briefs_page_filtered_all_lots_selected(self):
        original_url = "/digital-outcomes-and-specialists/opportunities?lot=digital-outcomes&lot=digital-specialists"\
            "&lot=user-research-participants"
        res = self.client.get(original_url)
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        self.data_api_client.find_frameworks.assert_called_once_with()

        self.search_api_client.search.assert_called_once_with(
            index='briefs-digital-outcomes-and-specialists',
            doc_type='briefs',
            statusOpenClosed='open,closed',
            lot='digital-outcomes',
        )

        heading = document.xpath('normalize-space(//h1/text())')
        assert heading == "Digital Outcomes and Specialists opportunities"
        assert ('View buyer requirements for digital outcomes, '
                'digital specialists and user research participants') in document.xpath(
            "normalize-space(//div[@class='marketplace-paragraph']/p/text())"
        )

        all_categories_return_link = document.xpath("//form[@method='get']//div[@class='lot-filters']/ul/li/a")[0]
        assert all_categories_return_link.text == 'All categories'

        lot_filters = document.xpath("//form[@method='get']//div[@class='lot-filters']//ul//ul/li/*[1]")
        assert {
            element.text: element.tag
            for element in lot_filters
        } == {
            'Digital outcomes (629)': 'strong',
            'Digital specialists (827)': 'a',
            'User research participants (39)': 'a',
        }

        status_inputs = document.xpath("//form[@method='get']//input[@name='statusOpenClosed']")
        assert {
            element.get("value"): bool(element.get("checked"))
            for element in status_inputs
        } == {
            "open": False,
            "closed": False,
        }

        location_inputs = document.xpath("//form[@method='get']//input[@name='location']")
        assert {
            element.get("value"): bool(element.get("checked"))
            for element in location_inputs
        } == {
            "scotland": False,
            "north east england": False,
            "north west england": False,
            "yorkshire and the humber": False,
            "east midlands": False,
            "west midlands": False,
            "east of england": False,
            "wales": False,
            "london": False,
            "south east england": False,
            "south west england": False,
            "northern ireland": False,
            "international (outside the uk)": False,
            "offsite": False,
        }

        q_inputs = document.xpath("//form[@method='get']//input[@name='q']")
        assert tuple(element.get("value") for element in q_inputs) == ("",)

        parsed_original_url = urlparse(original_url)
        parsed_next_url = urlparse(document.xpath("//li[@class='next']/a/@href")[0])
        assert parsed_original_url.path == parsed_next_url.path

        assert self.normalize_qs(parsed_next_url.query) == {'lot': {'digital-outcomes'}}

        ss_elem = document.xpath("//p[@class='search-summary']")[0]
        assert self._normalize_whitespace(self._squashed_element_text(ss_elem)) == \
            "864 results found in Digital outcomes"

    @pytest.mark.parametrize(
        ('dos_status', 'dos2_status', 'expected_url_slug_suffix'),
        (
            ('live', 'standstill', ''),
            ('expired', 'live', '-2'),
        )
    )
    @mock.patch('app.main.views.marketplace.content_loader')
    def test_opportunity_data_download_info_and_link_visible_on_catalogue_page(
        self, content_loader, dos_status, dos2_status, expected_url_slug_suffix
    ):
        self.data_api_client.find_frameworks.return_value = {'frameworks': [
            FrameworkStub(
                id=3, slug='digital-outcomes-and-specialists-2', status=dos2_status,
                lots=dos_lots(), has_further_competition=True
            ).response(),
            FrameworkStub(
                id=1, slug='digital-outcomes-and-specialists', status=dos_status,
                lots=dos_lots(), has_further_competition=True
            ).response()
        ]}
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))

        header = document.xpath("//h2[@id='opportunity-data-header']")[0].text
        description = document.xpath("//p[@id='opportunity-data-description']")[0].text
        expected_desc = "Download data buyers have provided about closed opportunities. Some data may be missing."
        link = document.xpath("//a[normalize-space(text())='Download data (CSV)']")[0].values()
        expected_link = (
            "https://assets.digitalmarketplace.service.gov.uk"
            + f"/digital-outcomes-and-specialists{expected_url_slug_suffix}/communications/data/opportunity-data.csv"
        )

        assert "Opportunity data" in header
        assert expected_desc in description
        assert expected_link in link

    def test_catalogue_of_briefs_page_shows_pagination_if_more_pages(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities?page=2')
        assert res.status_code == 200
        page = res.get_data(as_text=True)
        document = html.fromstring(page)

        assert '<li class="previous">' in page
        assert '<li class="next">' in page
        prev_url = str(document.xpath('string(//li[@class="previous"]/a/@href)'))
        next_url = str(document.xpath('string(//li[@class="next"]/a/@href)'))
        assert prev_url.endswith('/opportunities?page=1')
        assert next_url.endswith('/opportunities?page=3')
        assert '<span class="page-numbers">1 of 9</span>' in res.get_data(as_text=True)
        assert '<span class="page-numbers">3 of 9</span>' in res.get_data(as_text=True)

    def test_no_pagination_if_no_more_pages(self):
        with self.app.app_context():
            current_app.config['DM_SEARCH_PAGE_SIZE'] = 1000
            res = self.client.get('/digital-outcomes-and-specialists/opportunities')
            assert res.status_code == 200
            page = res.get_data(as_text=True)

            assert '<li class="previous">' not in page
            assert '<li class="next">' not in page

    def test_catalogue_of_briefs_page_404_for_framework_that_does_not_exist(self):
        res = self.client.get('/digital-giraffes-and-monkeys/opportunities')

        assert res.status_code == 404
        self.data_api_client.find_frameworks.assert_called_once_with()

    def test_briefs_search_has_js_hidden_filter_button(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        filter_button = document.xpath(
            '//button[contains(@class, "js-hidden")][contains(@class, "js-dm-live-search")]'
            '[normalize-space(text())="Filter"]'
        )
        assert len(filter_button) == 1

    def test_opportunity_status_and_published_date(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        live_opportunity_published_at = document.xpath(
            '//div[@class="search-result"][1]//li[@class="search-result-metadata-item"]'
        )[-3].text_content().strip()
        assert live_opportunity_published_at == "Published: Friday 17 November 2017"

        live_opportunity_qs_closing_at = document.xpath(
            '//div[@class="search-result"][1]//li[@class="search-result-metadata-item"]'
        )[-2].text_content().strip()
        assert live_opportunity_qs_closing_at == "Deadline for asking questions: Sunday 26 November 2017"

        live_opportunity_closing_at = document.xpath(
            '//div[@class="search-result"][1]//li[@class="search-result-metadata-item"]'
        )[-1].text_content().strip()
        assert live_opportunity_closing_at == "Closing: Friday 1 December 2017"

        closed_opportunity_status = document.xpath(
            '//div[@class="search-result"][2]//li[@class="search-result-metadata-item"]'
        )[-1].text_content().strip()
        assert closed_opportunity_status == "Closed: awaiting outcome"

        unsuccessful_opportunity_status = document.xpath(
            '//div[@class="search-result"][3]//li[@class="search-result-metadata-item"]'
        )[-1].text_content().strip()
        assert unsuccessful_opportunity_status == "Closed: no suitable suppliers"

        cancelled_opportunity_status = document.xpath(
            '//div[@class="search-result"][4]//li[@class="search-result-metadata-item"]'
        )[-1].text_content().strip()
        assert cancelled_opportunity_status == "Closed: cancelled"

        awarded_opportunity_status = document.xpath(
            '//div[@class="search-result"][6]//li[@class="search-result-metadata-item"]'
        )[-1].text_content().strip()
        assert awarded_opportunity_status == "Closed: awarded"

    def test_should_render_summary_for_0_results_in_all_lots(self):
        search_results = self._get_dos_brief_search_api_response_fixture_data()
        search_results['meta']['total'] = 0
        self.search_api_client.search.return_value = search_results

        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">0</span> results found in <em>All categories</em>' in summary

    def test_should_render_summary_for_0_results_in_particular_lot(self):
        search_results = self._get_dos_brief_search_api_response_fixture_data()
        search_results['meta']['total'] = 0
        self.search_api_client.search.return_value = search_results

        res = self.client.get('/digital-outcomes-and-specialists/opportunities?lot=digital-outcomes')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">0</span> results found in <em>Digital outcomes</em>' in summary

    def test_should_render_summary_for_1_result_found_in_all_lots(self):
        search_results = self._get_dos_brief_search_api_response_fixture_data()
        search_results['meta']['total'] = 1
        self.search_api_client.search.return_value = search_results

        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found in <em>All categories</em>' in summary

    def test_should_render_summary_for_many_results_found_in_a_particular_lot(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities?lot=digital-specialists')
        assert res.status_code == 200
        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">864</span> results found in <em>Digital specialists</em>' in summary

    def test_should_render_suggestions_for_0_results(self):
        search_results = self._get_dos_brief_search_api_response_fixture_data()
        search_results['meta']['total'] = 0
        self.search_api_client.search.return_value = search_results

        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200

        xpath = html.fromstring(res.get_data(as_text=True)).xpath
        assert xpath('boolean(//div[contains(@class, "search-suggestion")])')

    def test_should_not_render_suggestions_when_results(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200

        xpath = html.fromstring(res.get_data(as_text=True)).xpath
        assert not xpath('boolean(//div[contains(@class, "search-suggestion")])')

    def test_should_ignore_unknown_arguments(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities?location=my-lovely-horse')

        assert res.status_code == 200

    def test_should_404_on_invalid_page_param(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities?page=1')
        assert res.status_code == 200

        res = self.client.get('/digital-outcomes-and-specialists/opportunities?page=-1')
        assert res.status_code == 404

        res = self.client.get('/digital-outcomes-and-specialists/opportunities?page=potato')
        assert res.status_code == 404

    def test_search_results_with_invalid_lot_fall_back_to_all_categories(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities?lot=bad-lot-slug')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        lots = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//li/a')
        assert lots[0].text_content().startswith('Digital outcomes')
        assert lots[1].text_content().startswith('Digital specialists')
        assert lots[2].text_content().startswith('User research participants')

    def test_lot_links_retain_all_category_filters(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities?location=london')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        lots = document.xpath('//div[@class="lot-filters"]//ul[@class="lot-filters--last-list"]//li/a')
        for lot in lots:
            assert 'location=london' in lot.get('href')

    def test_lot_with_no_briefs_is_not_a_link(self):
        specialists_aggregation = self._get_dos_brief_search_api_aggregations_response_specialists_fixture_data()
        specialists_aggregation['aggregations']['lot']['digital-specialists'] = 0
        self.search_api_client.aggregate.side_effect = [
            self._get_dos_brief_search_api_aggregations_response_outcomes_fixture_data(),
            specialists_aggregation,
            self._get_dos_brief_search_api_aggregations_response_user_research_fixture_data(),
        ]

        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        specialist_label = document.xpath("//ul[@class='lot-filters--last-list']//li")[-2]
        assert len(specialist_label.xpath('a')) == 0
        assert specialist_label.text_content() == 'Digital specialists (0)'

    def test_filter_form_given_filter_selection(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities?lot=digital-outcomes&location=london')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        hidden_inputs = document.xpath('//form[@id="js-dm-live-search-form"]//input[@type="hidden"]')
        kv_pairs = {input_el.get('name'): input_el.get('value') for input_el in hidden_inputs}

        assert kv_pairs == {'lot': 'digital-outcomes'}


class TestCatalogueOfBriefsFilterOnClick(APIClientMixin, BaseApplicationTest):

    def setup_method(self, method):
        super().setup_method(method)

        self.search_api_client.search.return_value = self._get_dos_brief_search_api_response_fixture_data()

        self.search_api_client.aggregate.side_effect = [
            self._get_dos_brief_search_api_aggregations_response_outcomes_fixture_data(),
            self._get_dos_brief_search_api_aggregations_response_specialists_fixture_data(),
            self._get_dos_brief_search_api_aggregations_response_user_research_fixture_data(),
        ]

        self.data_api_client.find_frameworks.return_value = {
            'frameworks': [
                FrameworkStub(
                    id=3, slug='digital-outcomes-and-specialists-2', status='live',
                    lots=dos_lots(), has_further_competition=True
                ).response()
            ]
        }

    @pytest.mark.parametrize('query_string, content_type',
                             (('', 'text/html; charset=utf-8'),
                              ('?live-results=true', 'application/json')))
    def test_endpoint_switches_on_live_results_request(self, query_string, content_type):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities{}'.format(query_string))
        assert res.status_code == 200
        assert res.content_type == content_type

    def test_live_results_returns_valid_json_structure(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities?live-results=true')
        data = json.loads(res.get_data(as_text=True))

        assert sorted(data.keys()) == sorted((
            'results',
            'summary',
            'summary-accessible-hint',
            'categories',
            'filter-title'
        ))

        for k, v in data.items():
            assert set(v.keys()) == {'selector', 'html'}

            # We want to enforce using css IDs to describe the nodes which should be replaced.
            assert v['selector'].startswith('#')

    live_results_expected_templates = (
        "search/_results_wrapper.html",
        "search/_categories_wrapper.html",
        "search/_summary.html",
        "search/_summary_accessible_hint.html",
        "search/_filter_title.html"
    )

    @pytest.mark.parametrize(
        ('query_string', 'urls'),
        (
            ('', ('search/briefs.html',)),
            ('?live-results=true', live_results_expected_templates)
        )
    )
    @mock.patch('app.main.views.marketplace.render_template', autospec=True)
    def test_base_page_renders_search_services(self, render_template_patch, query_string, urls):
        render_template_patch.return_value = '<p>some html</p>'

        self.client.get('/digital-outcomes-and-specialists/opportunities{}'.format(query_string))

        assert urls == tuple(x[0][0] for x in render_template_patch.call_args_list)

    def test_form_has_js_hidden_filter_button(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        filter_button = document.xpath(
            '//button[contains(@class, "js-hidden")][contains(@class, "js-dm-live-search")]'
            '[normalize-space(text())="Filter"]'
        )
        assert len(filter_button) == 1


class TestGCloudHomepageLinks(APIClientMixin, BaseApplicationTest):

    mock_live_g_cloud_framework = {
        "framework": "g-cloud",
        "slug": "g-cloud-x",
        "status": "live",
        "id": 5
    }

    @pytest.mark.parametrize('framework_slug, gcloud_content',
                             (('g-cloud-8', 'Find cloud technology and support'),
                              ('g-cloud-9', 'Find cloud hosting, software and support')))
    def test_g_cloud_homepage_content_is_correct(self, framework_slug, gcloud_content):
        self.data_api_client.find_frameworks.return_value = {
            "frameworks": [self.mock_live_g_cloud_framework.copy()]
        }
        self.data_api_client.find_frameworks.return_value['frameworks'][0].update({'slug': framework_slug})

        res = self.client.get("/")
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        link_texts = [item.text_content().strip() for item in document.cssselect('#app-buyer-nav a')]
        assert link_texts[-2] == gcloud_content
        assert link_texts[-1] == 'Find physical datacentre space'
