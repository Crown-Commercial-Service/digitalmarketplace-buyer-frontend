from dateutil import parser
import sys
from urllib.parse import quote_plus, urlparse

from html import escape as html_escape
from lxml import html
import mock
import pytest
from werkzeug.exceptions import BadRequest, NotFound

from dmapiclient import HTTPError
from dmcontent.content_loader import ContentLoader, ContentNotFoundError
from dmtestutils.api_model_stubs import FrameworkStub

from app import content_loader
from app.main.views.g_cloud import (DownloadResultsView, END_SEARCH_LIMIT, TOO_MANY_RESULTS_MESSAGE,
                                    CONFIRM_START_ASSESSING_MESSAGE, )
from ...helpers import BaseApplicationTest, BaseAPIClientMixin


class APIClientMixin(BaseAPIClientMixin):
    data_api_client_patch_path = 'app.main.views.g_cloud.data_api_client'
    search_api_client_patch_path = 'app.main.views.g_cloud.search_api_client'


class TestDirectAwardBase(APIClientMixin, BaseApplicationTest):
    def setup_method(self, method):
        super().setup_method(method)
        self.search_api_client.aggregate.return_value = self._get_fixture_data('g9_aggregations_fixture.json')

        self.search_api_client.get_index_from_search_api_url.return_value = 'g-cloud-9'

        self.g9_search_results = self._get_g9_search_results_fixture_data()

        self.data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-9')

        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_project_fixture()
        self.data_api_client.find_direct_award_projects.return_value = self._get_direct_award_project_list_fixture()
        self.data_api_client.find_direct_award_project_searches.return_value = \
            self._get_direct_award_project_searches_fixture()

    def teardown_method(self, method):
        super().teardown_method(method)


class TestDirectAward(TestDirectAwardBase):
    @classmethod
    def setup_class(cls):
        super().setup_class()

        cls.SAVE_SEARCH_OVERVIEW_URL = '/buyers/direct-award/g-cloud'
        cls.SAVE_SEARCH_URL = '/buyers/direct-award/g-cloud/save-search'
        cls.SIMPLE_SEARCH_PARAMS = 'lot=cloud-software'
        cls.SEARCH_URL = '/g-cloud/search?' + cls.SIMPLE_SEARCH_PARAMS
        cls.PROJECT_CREATE_URL = '/buyers/direct-award/g-cloud/projects/create'
        cls.SIMPLE_SAVE_SEARCH_URL = '{}?search_query={}'.format(
            cls.SAVE_SEARCH_URL, quote_plus(cls.SIMPLE_SEARCH_PARAMS))
        cls.SEARCH_API_URL = 'g-cloud-9/services/search'

    def test_invalid_framework_family(self):
        self.login_as_buyer()
        res = self.client.get("/buyers/direct-award/shakespeare")
        assert res.status_code == 404

    def test_renders_saved_search_overview(self):
        self.login_as_buyer()
        res = self.client.get(self.SAVE_SEARCH_OVERVIEW_URL)
        assert res.status_code == 200

        result_html = res.get_data(as_text=True)
        doc = html.fromstring(result_html)
        page_header = doc.cssselect("h1.govuk-heading-xl")[0].text.strip()

        assert page_header == "Your saved searches"
        assert page_header in doc.xpath('/html/head/title')[0].text.strip()
        assert doc.xpath('//*[@id="searching_table"]')[0].text.strip() == "Searching"
        assert doc.xpath('//*[@id="search_ended_table"]')[0].text.strip() == "Results exported"

        tables = [
            doc.xpath('//*[@id="content"]/div/div/table[1]/tbody/tr'),
            doc.xpath('//*[@id="content"]/div/div/table[2]/tbody/tr')
        ]

        for table in tables:
            previous_date = None
            for row in table:
                current_date = row[1][0].text
                if previous_date:
                    assert parser.parse(previous_date) >= parser.parse(current_date)
                previous_date = current_date

    def test_renders_outcome_column_for_search_ended(self):
        self.login_as_buyer()
        res = self.client.get(self.SAVE_SEARCH_OVERVIEW_URL)
        assert res.status_code == 200

        result_html = res.get_data(as_text=True)
        doc = html.fromstring(result_html)

        search_ended_table = doc.xpath('//*[@id="content"]/div/div/table[2]/tbody/tr')

        for row in search_ended_table:
            if row[2][0].xpath('a'):
                assert row[2][0].xpath('a')[0].text in [
                    "Tell us the outcome", "Download search results"
                ]
            else:
                assert row[2][0].text in [
                    "Awarded",
                    "No suitable services found",
                    "The work has been cancelled"
                ]

    def test_renders_save_search_button(self):
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get(self.SEARCH_URL)
        assert res.status_code == 200

        doc = html.fromstring(res.get_data(as_text=True))
        assert doc.xpath('id("js-dm-live-save-search-form")//input[@name="search_query"]'
                         '/@value')[0] == self.SIMPLE_SEARCH_PARAMS
        assert doc.xpath('id("js-dm-live-save-search-form")//form/@action')[0] == self.SAVE_SEARCH_URL
        assert len(doc.xpath('id("js-dm-live-save-search-form")//form//button[@type="submit"]')) > 0

    def test_save_search_redirects_to_login(self):
        res = self.client.get(self.SIMPLE_SAVE_SEARCH_URL)
        assert res.status_code == 302
        assert res.location == 'http://localhost/user/login?next={}'.format(quote_plus(self.SIMPLE_SAVE_SEARCH_URL))

    def test_save_search_renders_summary_on_page(self):
        self.login_as_buyer()
        self.search_api_client.search.return_value = self.g9_search_results

        res = self.client.get(self.SIMPLE_SAVE_SEARCH_URL)

        assert res.status_code == 200

        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1150</span> results found in <em>Cloud software</em>' in summary

    def _save_search(self, name, save_search_selection="new_search"):
        self.login_as_buyer()
        self.search_api_client.search.return_value = self.g9_search_results
        self.data_api_client.create_direct_award_project.return_value = self._get_direct_award_project_fixture()
        self.data_api_client.create_direct_award_project_search.return_value = \
            self._get_direct_award_project_searches_fixture()['searches'][0]

        return self.client.post(self.SAVE_SEARCH_URL,
                                data={
                                    'name': name,
                                    'search_query': self.SIMPLE_SEARCH_PARAMS,
                                    'save_search_selection': save_search_selection
                                })

    def _update_existing_project(self, save_search_selection):
        return self._save_search(None, save_search_selection)

    def _asserts_for_create_project_failure(self, res):
        assert res.status_code == 400
        html = res.get_data(as_text=True)
        assert self.SEARCH_API_URL not in html  # it was once, so let's check
        assert self.SIMPLE_SEARCH_PARAMS in html
        assert "Search name must be between 1 and 100 characters" in html

    def test_save_search_submit_success(self):
        res = self._save_search('some name " foo bar \u2016')
        assert res.status_code == 303
        assert urlparse(res.location).path == '/buyers/direct-award/g-cloud/projects/1'

    def test_save_existing_search_submit_success(self):
        res = self._save_search(name='', save_search_selection='1')
        assert res.status_code == 303
        assert urlparse(res.location).path == '/buyers/direct-award/g-cloud/projects/1'

    def test_save_search_submit_no_name(self):
        res = self._save_search('')
        self._asserts_for_create_project_failure(res)

    def test_save_search_submit_name_too_long(self):
        res = self._save_search('x' * 101)
        self._asserts_for_create_project_failure(res)

    @pytest.mark.parametrize("method", ("GET", "POST"))
    def test_save_search_invalid_framework_family(self, method):
        self.login_as_buyer()
        res = self.client.open("/buyers/direct-award/shakespeare/save-search", method=method)
        assert res.status_code == 404


class TestDirectAwardProjectOverview(TestDirectAwardBase):
    def setup_method(self, method):
        super().setup_method(method)

        self.search_api_client.get_frontend_params_from_search_api_url.return_value = (('q', 'accelerator'), )

        self.login_as_buyer()

        self.content_loader = ContentLoader('tests/fixtures/content')
        self.content_loader.load_messages('g9', ['urls'])

    def teardown_method(self, method):
        super().teardown_method(method)

    def _task_has_link(self, tasklist, task, link):
        """Task here refers to the tasklist item number rather than the zero-indexed python array. This feels easier to
        understand and amend in the context of the tasklist."""
        anchors = tasklist[task - 1].xpath('.//a[@href="{}"]'.format(link))

        return len(anchors) == 1

    def _task_has_button(self, tasklist, task, name, value):
        """Task here refers to the tasklist item number rather than the zero-indexed python array. This feels easier to
        understand and amend in the context of the tasklist."""
        anchors = tasklist[task - 1].xpath('.//button[@name="{}" and @value="{}"]'.format(name, value))

        return len(anchors) == 1

    def _task_has_box(self, tasklist, task, style, text):
        if task <= 0:
            raise ValueError()

        box = tasklist[task - 1].xpath('.//p[@class="instruction-list-item-box {}"'
                                       ' and normalize-space(text())="{}"]'.format(style, text))
        return len(box) == 1

    def _task_cannot_start_yet(self, tasklist, task):
        return self._task_has_box(tasklist, task, style='inactive', text='Can’t start yet')

    def _task_completed(self, tasklist, task):
        return self._task_has_box(tasklist, task, style='complete', text='Completed')

    def _cannot_start_from_task(self, tasklist, cannot_start_from):
        return all([self._task_cannot_start_yet(tasklist, task + 1) is ((task + 1) >= cannot_start_from)
                    for task in range(len(tasklist))])

    def _set_project_locked_and_framework_states(self, locked_at, framework_status, following_framework_status):
        project = self._get_direct_award_project_fixture()
        project['project']['lockedAt'] = locked_at
        self.data_api_client.get_direct_award_project.return_value = project

        self.data_api_client.find_frameworks.return_value = {
            "frameworks": [
                FrameworkStub(
                    slug='g-cloud-9', status=framework_status
                ).response()
            ]
        }
        self.data_api_client.get_framework.return_value = FrameworkStub(
            slug='g-cloud-10', status=following_framework_status
        ).single_result_response()

    def test_view_project_page_shows_title(self):
        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')

        doc = html.fromstring(res.get_data(as_text=True))
        project_name = self._get_direct_award_project_fixture()['project']['name']
        assert len(doc.xpath('//h1[contains(normalize-space(string()), $t)]', t=project_name)) == 1
        assert doc.xpath('//head/title[contains(normalize-space(string()), $t)]', t=project_name)

    @pytest.mark.parametrize('user_id, expected_status_code', ((122, 404), (123, 200)))
    def test_view_project_checks_user_access_to_project_or_404s(self, user_id, expected_status_code):
        self.login_as_buyer(user_id=user_id)
        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == expected_status_code

    def test_all_steps_are_rendered_for_all_states(self):
        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        item_headings = ['Save a search', 'Export your results', 'Start assessing',
                         'Award a contract', 'Submit a Customer Benefits Record']

        tasklist = doc.xpath('//li[contains(@class, "instruction-list-item")]')

        for i, item in enumerate(tasklist):
            assert item_headings[i] in item.xpath('h2/text()')[0]

    def test_overview_renders_links_common_to_all_states(self):
        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[contains(@class, "instruction-list-item")]')

        # Step 1 should link to the guidance for buying fairly.
        assert self._task_has_link(tasklist, 1, 'https://www.gov.uk/guidance/g-cloud-buyers-guide#fairness')

        # Step 3 should link to guidance on comparing services.
        buyer_guide_compare_services_url = \
            "https://www.gov.uk/guidance/g-cloud-buyers-guide#review-and-compare-services"
        assert self._task_has_link(tasklist, 3, buyer_guide_compare_services_url)

        # Step 5 has a link to framework customer benefits form
        customer_benefits_record_form_url = self.content_loader.get_message('g9', 'urls',
                                                                            'customer_benefits_record_form_url')
        assert self._task_has_link(tasklist, 5, customer_benefits_record_form_url)

        breadcrumbs = doc.xpath("//div[@class='govuk-breadcrumbs']/ol/li")
        assert tuple(li.xpath("normalize-space(string())") for li in breadcrumbs) == (
            "Digital Marketplace",
            "Your account",
            "Your saved searches",
            "My procurement project <",
        )
        assert tuple(li.xpath(".//a/@href") for li in breadcrumbs) == (
            ["/"],
            ["/buyers"],
            ["/buyers/direct-award/g-cloud"],
            [],
        )

    def test_overview_renders_specific_elements_for_no_search_state(self):
        searches = self._get_direct_award_project_searches_fixture()

        searches['searches'] = []

        self.data_api_client.find_direct_award_project_searches.return_value = searches

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[contains(@class, "instruction-list-item")]')

        assert self._task_has_link(tasklist, 1, '/buyers/direct-award/g-cloud/choose-lot')
        assert self._task_has_link(tasklist, 2, '/buyers/direct-award/g-cloud/projects/1/end-search') is False

        assert self._cannot_start_from_task(tasklist, 2)

        assert "Before you start you should" not in doc.xpath("normalize-space(string())")

    def test_overview_renders_specific_elements_for_search_created_state(self):
        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[contains(@class, "instruction-list-item")]')

        assert self._task_has_link(tasklist, 1, '/g-cloud/search?q=accelerator')
        assert self._task_has_link(tasklist, 2, '/buyers/direct-award/g-cloud/projects/1/end-search')

        assert self._cannot_start_from_task(tasklist, 3)

        assert doc.xpath('//p[contains(@class, "search-summary")]')[0].text_content() == '1 result found containing '\
                                                                                         'accelerator in All categories'

    def test_overview_renders_specific_elements_for_search_ended_state(self):
        searches = self._get_direct_award_project_searches_fixture()
        for search in searches['searches']:
            search['searchedAt'] = search['createdAt']

        self.data_api_client.find_direct_award_project_searches.return_value = searches

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[contains(@class, "instruction-list-item")]')

        assert self._task_has_link(tasklist, 1, '/g-cloud/search?q=accelerator') is False
        assert self._task_completed(tasklist, 2)
        assert self._task_has_link(tasklist, 2,
                                   '/buyers/direct-award/g-cloud/projects/1/results')
        assert self._task_has_button(tasklist, 3, 'readyToAssess', 'true')
        assert self._task_has_link(tasklist, 4,
                                   '/buyers/direct-award/g-cloud/projects/1/did-you-award-contract') is False

    def test_overview_renders_specific_elements_once_assessing_started(self):
        searches = self._get_direct_award_project_searches_fixture()
        for search in searches['searches']:
            search['searchedAt'] = search['createdAt']

        project = self._get_direct_award_project_fixture()
        project['project']['readyToAssessAt'] = project['project']['createdAt']
        self.data_api_client.get_direct_award_project.return_value = project

        self.data_api_client.find_direct_award_project_searches.return_value = searches

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[contains(@class, "instruction-list-item")]')

        assert self._task_has_link(tasklist, 1, '/g-cloud/search?q=accelerator') is False
        assert self._task_completed(tasklist, 2)
        assert self._task_has_link(tasklist, 2,
                                   '/buyers/direct-award/g-cloud/projects/1/results')
        assert self._task_completed(tasklist, 3)
        assert self._task_has_link(tasklist, 4,
                                   '/buyers/direct-award/g-cloud/projects/1/did-you-award-contract')

    def test_assess_button_not_present_if_outcome_awarded(self):
        searches = self._get_direct_award_project_searches_fixture()
        for search in searches['searches']:
            search['searchedAt'] = search['createdAt']

        self.data_api_client.get_direct_award_project.return_value = \
            self._get_direct_award_project_with_completed_outcome_awarded_fixture()

        self.data_api_client.find_direct_award_project_searches.return_value = searches

        res = self.client.get("/buyers/direct-award/g-cloud/projects/1")
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)
        tasklist = doc.xpath('//li[contains(@class, "instruction-list-item")]')

        assert not self._task_has_button(tasklist, 3, 'readyToAssess', 'true')

    @pytest.mark.parametrize(
        ('framework_status', 'following_framework_status', 'locked_at', 'position', 'heading'),
        (
            ('live', 'coming', None, None,
                'G-Cloud\xa010 services will replace existing services on Wednesday 5 January 2000'),
            ('live', 'open', None, None,
                'G-Cloud\xa010 services will replace existing services on Wednesday 5 January 2000'),
            ('live', 'pending', None, None,
                'G-Cloud\xa010 services will replace existing services on Wednesday 5 January 2000'),
            ('live', 'standstill', None, 'sidebar',
                'G-Cloud\xa010 services will replace existing services on Wednesday 5 January 2000'),
            ('live', 'live', None, 'sidebar',
                'G-Cloud\xa010 services replaced G-Cloud\xa09 services on Wednesday 5 January 2000'),
            ('expired', 'live', None, 'sidebar',
                'G-Cloud\xa010 services replaced G-Cloud\xa09 services on Wednesday 5 January 2000'),
            ('live', 'coming', '2018-06-25T21:57:00.881261Z', None,
                'The G-Cloud\xa09 services you found will expire soon'),
            ('live', 'open', '2018-06-25T21:57:00.881261Z', None,
                'The G-Cloud\xa09 services you found will expire soon'),
            ('live', 'pending', '2018-06-25T21:57:00.881261Z', None,
                'The G-Cloud\xa09 services you found will expire soon'),
            ('live', 'standstill', '2018-06-25T21:57:00.881261Z', 'banner',
                'The G-Cloud\xa09 services you found will expire soon'),
            ('live', 'live', '2018-06-25T21:57:00.881261Z', 'banner',
                'The G-Cloud\xa09 services you found will expire soon'),
            ('expired', 'live', '2018-06-25T21:57:00.881261Z', 'banner',
                'The G-Cloud\xa09 services you found have expired'),
        )
    )
    @mock.patch('app.main.helpers.framework_helpers.content_loader')
    def test_overview_displays_correct_temporary_message(
        self, content_loader_mock, framework_status, following_framework_status, locked_at, position, heading
    ):
        self._set_project_locked_and_framework_states(locked_at, framework_status, following_framework_status)
        content_loader_mock.get_metadata.return_value = {'slug': 'g-cloud-11'}

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        if position is None:
            assert not doc.xpath("//div[@class='temporary-message-banner']")
            assert not doc.xpath("//div[@class='temporary-message']")
        elif position == 'sidebar':
            assert len(doc.xpath("//div[@class='temporary-message']")) == 1
            assert not doc.xpath("//div[@class='temporary-message-banner']")
        elif position == 'banner':
            assert len(doc.xpath("//div[@class='temporary-message-banner']")) == 1
            assert not doc.xpath("//div[@class='temporary-message']")
        else:
            raise

        if position:
            assert doc.xpath(f"//h3[@class='temporary-message-heading'][contains(normalize-space(), '{heading}')]")

    @mock.patch('app.main.helpers.framework_helpers.content_loader')
    def test_temporary_messages_not_shown_if_no_defined_following_framework(self, content_loader_mock):
        content_loader_mock.get_metadata.side_effect = ContentNotFoundError()

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        assert not doc.xpath("//div[@class='temporary-message']")
        assert not doc.xpath("//div[@class='temporary-message-banner']")

    @mock.patch('app.main.helpers.framework_helpers.content_loader')
    def test_temporary_messages_not_shown_if_following_framework_not_found(self, content_loader_mock):
        self.data_api_client.get_framework.side_effect = HTTPError(response=mock.Mock(status_code=404))
        content_loader_mock.get_metadata.return_value = {'slug': 'g-cloud-11'}

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        doc = html.fromstring(res.get_data(as_text=True))
        assert not doc.xpath("//div[@class='temporary-message']")
        assert not doc.xpath("//div[@class='temporary-message-banner']")

    @mock.patch('app.main.helpers.framework_helpers.content_loader')
    def test_following_framework_still_raises_on_api_error(self, content_loader_mock):
        self.data_api_client.get_framework.side_effect = HTTPError(response=mock.Mock(status_code=500))
        content_loader_mock.get_metadata.return_value = {'slug': 'g-cloud-11'}

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 500

    @pytest.mark.parametrize(
        ('framework_status', 'following_framework_status'),
        (
            ('live', 'live'),
            ('expired', 'live'),
        )
    )
    @mock.patch('app.main.helpers.framework_helpers.content_loader')
    def test_temp_message_search_links_are_correctly_displayed(
        self, content_loader_mock, framework_status, following_framework_status
    ):
        self._set_project_locked_and_framework_states(
            '2018-06-25T21:57:00.881261Z', framework_status, following_framework_status
        )
        content_loader_mock.get_metadata.return_value = {'slug': 'g-cloud-11'}

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        search_links = doc.xpath("//div[@class='temporary-message-banner']//a")
        assert len(search_links) == 1
        assert search_links[0].xpath("normalize-space(string())") == 'start a new search for G-Cloud\xa010 services'
        assert search_links[0].attrib["href"] == '/g-cloud/search?q=accelerator'

    @pytest.mark.parametrize(
        ('locked_at', 'fwork_status', 'following_fwork_status', 'xpath', 'index', 'date'),
        (
            (None, 'live', 'standstill', '//h3[@class="temporary-message-heading"]', 0, 'Wednesday 5 January 2000'),
            (None, 'live', 'standstill', '//p[@class="temporary-message-message"]', 1, 'before 5 January they'),
            (None, 'live', 'live', '//h3[@class="temporary-message-heading"]', 0, 'Wednesday 5 January 2000'),
            (True, 'live', 'standstill', '//ul[@class="list-bullet-small"]/li', 1, 'Wednesday 5 January 2000'),
            (True, 'expired', 'live', '//p[@class="temporary-message-message"]', 0, 'Thursday 6 January 2000'),
        )
    )
    @mock.patch('app.main.helpers.framework_helpers.content_loader')
    def test_temp_message_dates_are_correctly_shown(
        self, content_loader_mock, locked_at, fwork_status, following_fwork_status, xpath, index, date
    ):
        self._set_project_locked_and_framework_states(locked_at, fwork_status, following_fwork_status)
        content_loader_mock.get_metadata.return_value = {'slug': 'g-cloud-11'}

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        assert date in doc.xpath(xpath)[index].text

    def test_search_completed_if_less_than_30_results(self):
        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[contains(@class, "instruction-list-item")]')
        assert self._task_completed(tasklist, 1)

    def test_search_not_completed_if_more_than_30_results(self):
        search_results = self.g9_search_results
        search_results['meta']['total'] = 100

        self.search_api_client._get.return_value = search_results

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[contains(@class, "instruction-list-item")]')
        assert not self._task_completed(tasklist, 1)
        assert self._cannot_start_from_task(tasklist, 2)
        assert len(doc.xpath(
            '(//li[contains(@class, "instruction-list-item")])[2]/p[contains(normalize-space(),'
            ' "You have too many services to assess.")]')) == 1


class TestDirectAwardURLGeneration(BaseApplicationTest):
    """
    This class tests the effects of the search_api_client.get_index_from_search_api_url method, which we don't
    want to patch. The .search() and ._get() methods need to be patched, however.

    This means we can't use the APIClientMixin as per the other classes.
    """
    def setup_method(self, method):
        super().setup_method(method)

        self.data_api_client_patch = mock.patch('app.main.views.g_cloud.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()
        self.data_api_client.find_frameworks.return_value = self._get_frameworks_list_fixture_data()
        self.data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-9')

        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_project_fixture()
        self.data_api_client.find_direct_award_project_searches.return_value = \
            self._get_direct_award_project_searches_fixture()

        # Patch only the .search and ._get methods on the search_api_client
        self.search_api_client_search_patch = mock.patch(
            'app.main.views.g_cloud.search_api_client.search', autospec=True
        )
        self.search_api_client_search = self.search_api_client_search_patch.start()
        self.search_api_client_get_patch = mock.patch('app.main.views.g_cloud.search_api_client._get', autospec=True)
        self.search_api_client_get = self.search_api_client_get_patch.start()

    def teardown_method(self, method):
        self.search_api_client_get_patch.stop()
        self.search_api_client_search_patch.stop()
        self.data_api_client_patch.stop()
        super().teardown_method(method)

    @pytest.mark.parametrize('search_api_url, frontend_url',
                             (
                                 ('https://search-api.digitalmarketplace.service.gov.uk/g-cloud-9/services/search',
                                  '/g-cloud/search'),
                                 ('https://search-api.digitalmarketplace.service.gov.uk/g-cloud-9/services/search?'
                                  'filter_lot=cloud-hosting',
                                  '/g-cloud/search?lot=cloud-hosting'),
                                 ('https://search-api.digitalmarketplace.service.gov.uk/g-cloud-9/services/search?'
                                  'filter_lot=cloud-hosting&filter_serviceCategories=firewall',
                                  '/g-cloud/search?lot=cloud-hosting&serviceCategories=firewall'),
                                 ('https://search-api.digitalmarketplace.service.gov.uk/g-cloud-9/services/search?'
                                  'filter_lot=cloud-hosting&filter_serviceCategories=firewall&filter_governmentSe'
                                  'curityClearances=dv%2Csc',
                                  '/g-cloud/search?lot=cloud-hosting&serviceCategories=firewall&governmentSecurityCl'
                                  'earances=dv&governmentSecurityClearances=sc')
                             ))
    @mock.patch('app.main.helpers.framework_helpers.content_loader')
    def test_search_api_urls_convert_to_correct_frontend_urls(self, content_loader_mock, search_api_url, frontend_url):
        self.login_as_buyer()
        content_loader_mock.get_metadata.return_value = {'slug': 'g-cloud-11'}

        self.search_api_client_search.return_value = self._get_g9_search_results_fixture_data()
        self.search_api_client_get.return_value = self._get_search_results_fixture_data()

        project_searches = self.data_api_client.find_direct_award_project_searches.return_value
        project_searches['searches'][0]['searchUrl'] = search_api_url

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')

        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)
        assert html_escape(frontend_url) in body
        assert len(doc.xpath('//a[@href="{}"]'.format(frontend_url)))


class TestDirectAwardEndSearch(TestDirectAwardBase):
    def test_end_search_page_renders(self):
        self.login_as_buyer()

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1/end-search')
        assert res.status_code == 200

        doc = html.fromstring(res.get_data(as_text=True))
        assert len(doc.xpath('//h1[contains(normalize-space(), "Before you export your results")]')) == 1

    @pytest.mark.parametrize("method", ("GET", "POST"))
    def test_invalid_framework_family(self, method):
        self.login_as_buyer()
        res = self.client.open('/buyers/direct-award/shakespeare/projects/1/end-search', method=method)
        assert res.status_code == 404

    def test_end_search_page_renders_error_when_results_more_than_limit(self):
        self.login_as_buyer()

        self.search_api_client._get.return_value = {
            "services": [],
            "meta": {
                "query": {},
                "total": END_SEARCH_LIMIT + 1,
                "took": 3
            },
            "links": {}
        }

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1/end-search')

        assert res.status_code == 200
        assert TOO_MANY_RESULTS_MESSAGE in res.get_data(as_text=True)

    def test_must_confirm_understanding(self):
        self.login_as_buyer()

        self.data_api_client.lock_direct_award_project.return_value = self._get_direct_award_lock_project_fixture()

        res = self.client.post('/buyers/direct-award/g-cloud/projects/1/end-search')

        assert res.status_code == 400

        doc = html.fromstring(res.get_data(as_text=True))
        assert doc.get_element_by_id('error-user_understands') is not None

    def test_end_search_redirects_to_results_page(self):
        self.login_as_buyer()

        self.data_api_client.lock_direct_award_project.return_value = self._get_direct_award_lock_project_fixture()

        res = self.client.post('/buyers/direct-award/g-cloud/projects/1/end-search', data={'user_understands': 'True'})

        assert res.status_code == 302
        assert res.location.endswith('/buyers/direct-award/g-cloud/projects/1/results')


class TestDirectAwardReadyToAssess(TestDirectAwardBase):
    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_lock_project_fixture()
        self.data_api_client.find_direct_award_project_services.return_value = \
            self._get_direct_award_project_services_fixture()

        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_lock_project_fixture()

    def test_ready_button_does_something(self):
        self.login_as_buyer()
        res = self.client.post('/buyers/direct-award/g-cloud/projects/1', data={"readyToAssess": "true"})

        assert res.status_code == 302
        assert res.location.endswith('/buyers/direct-award/g-cloud/projects/1')
        self.data_api_client.update_direct_award_project.assert_called_once_with(
            project_data={'readyToAssess': True}, project_id=1, user_email='buyer@email.com')
        self.assert_flashes(html_escape(CONFIRM_START_ASSESSING_MESSAGE))


class TestDirectAwardAwardContract(TestDirectAwardBase):
    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_lock_project_fixture()
        self.data_api_client.find_direct_award_project_services.return_value = \
            self._get_direct_award_project_services_fixture()

        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_lock_project_fixture()

    def test_award_contract_page_renders(self):
        self.login_as_buyer()

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1/did-you-award-contract')
        assert res.status_code == 200

        doc = html.fromstring(res.get_data(as_text=True))
        assert len(doc.xpath(
            '//h1[contains(normalize-space(), "Did you award a contract for ‘My procurement project <’?")]')) == 1
        assert len(doc.xpath('//input[@type="radio"][contains(following-sibling::label, "Yes")]')) == 1
        assert len(doc.xpath('//input[@type="radio"][contains(following-sibling::label, "No")]')) == 1
        assert len(doc.xpath(
            '//input[@type="radio"][contains(following-sibling::label, "We are still assessing services")]')) == 1
        assert len(doc.xpath('//button[normalize-space(string())=$t]', t="Save and continue")) == 1

    def test_award_contract_form_action_url_is_award_contract_url(self):
        self.login_as_buyer()

        url = '/buyers/direct-award/g-cloud/projects/1/did-you-award-contract'

        res = self.client.get(url)
        assert res.status_code == 200

        doc = html.fromstring(res.get_data(as_text=True))
        assert doc.xpath(f'boolean(//form[@action="{url}"])')

    def test_award_contract_error_if_no_input(self):
        self.login_as_buyer()

        res = self.client.post('/buyers/direct-award/g-cloud/projects/1/did-you-award-contract')

        assert res.status_code == 400

        doc = html.fromstring(res.get_data(as_text=True))
        assert len(doc.xpath('//legend[contains(normalize-space(), "Select if you have awarded your contract")]')) == 1
        errors = doc.cssselect('div.govuk-error-summary a')
        assert len(errors) == 1
        assert errors[0].text_content() == 'Select if you have awarded your contract'

    @pytest.mark.parametrize('choice, expected_redirect',
                             (('still-assessing', '/buyers/direct-award/g-cloud/projects/1'),
                              ('yes', '/buyers/direct-award/g-cloud/projects/1/which-service-won-contract'),
                              ('no', '/buyers/direct-award/g-cloud/projects/1/why-didnt-you-award-contract')))
    def test_did_you_award_contract_redirects_on_post(self, choice, expected_redirect):
        self.login_as_buyer()

        res = self.client.post('/buyers/direct-award/g-cloud/projects/1/did-you-award-contract',
                               data={'did_you_award_a_contract': choice})

        assert res.status_code == 302
        assert res.location.endswith(expected_redirect)

    def test_we_are_still_assessing_calls_api(self):
        self.login_as_buyer()

        self.client.post('/buyers/direct-award/g-cloud/projects/1/did-you-award-contract',
                         data={'did_you_award_a_contract': 'still-assessing'})

        self.data_api_client.mark_direct_award_project_as_still_assessing.assert_called_once()

    def test_still_assessing_flashes(self):
        self.login_as_buyer()

        self.client.post('/buyers/direct-award/g-cloud/projects/1/did-you-award-contract',
                         data={'did_you_award_a_contract': 'still-assessing'})

        self.assert_flashes(
            "Your response for ‘My procurement project &lt;’ has been saved. "
            "You still need to tell us the outcome when you’ve finished assessing services",
            'success'
        )

    @pytest.mark.parametrize("method", ("GET", "POST"))
    def test_invalid_framework_family(self, method):
        self.login_as_buyer()

        res = self.client.open('/buyers/direct-award/shakespeare/projects/1/did-you-award-contract', method=method)
        assert res.status_code == 404

    def test_award_contract_raises_404_if_project_is_not_accessible(self):
        self.data_api_client.get_direct_award_project.side_effect = NotFound()
        self.login_as_buyer()

        res = self.client.get('/buyers/direct-award/g-cloud/projects/314159/did-you-award-contract')
        assert res.status_code == 404

    def test_award_contract_raises_404_if_user_is_not_in_project(self):
        self.data_api_client.get_direct_award_project.return_value['project']['id'] = 314159
        self.data_api_client.get_direct_award_project.return_value['project']['users'][0]['id'] = 321
        self.login_as_buyer()

        res = self.client.get('/buyers/direct-award/g-cloud/projects/314159/did-you-award-contract')
        assert res.status_code == 404

    def test_award_contract_raises_400_if_project_is_not_locked(self):
        self.data_api_client.get_direct_award_project.return_value['project']['lockedAt'] = None
        self.login_as_buyer()

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1/did-you-award-contract')
        assert res.status_code == 400

    def test_award_contract_raises_410_if_outcome_is_completed(self):
        self.data_api_client.get_direct_award_project.return_value = \
            self._get_direct_award_project_with_completed_outcome_awarded_fixture()
        self.login_as_buyer()

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1/did-you-award-contract')
        assert res.status_code == 410

    def test_which_service_did_you_award_page_renders(self):
        self.login_as_buyer()

        res = self.client.get(
            '/buyers/direct-award/g-cloud/projects/1/which-service-won-contract')
        assert res.status_code == 200

        doc = html.fromstring(res.get_data(as_text=True))
        assert len(doc.xpath(
            '//h1[contains(normalize-space(), "Which service won the contract?")]')) == 1
        assert len(doc.xpath(
            '//input[@type="radio"][contains(following-sibling::label, "Service name")]')) == 1
        assert len(doc.xpath(
            '//span[contains(normalize-space(text()), "Supplier name")][contains(parent::label, "Service name")]')) == 1
        assert len(
            doc.xpath('//button[normalize-space(string())=$t]', t="Save and continue")) == 1

    @pytest.mark.parametrize("method", ("GET", "POST"))
    def test_which_service_did_you_award_page_invalid_framework_family(self, method):
        self.login_as_buyer()

        res = self.client.open(
            "/buyers/direct-award/shakespeare/projects/1/which-service-won-contract",
            method=method,
        )
        assert res.status_code == 404

    def test_which_service_did_you_award_page_show_zero_state_message(self):
        self.login_as_buyer()
        self.data_api_client.find_direct_award_project_services.return_value = \
            self._get_direct_award_project_services_zero_state_fixture()

        res = self.client.get(
            '/buyers/direct-award/g-cloud/projects/1/which-service-won-contract')
        assert res.status_code == 200

        html_string = res.get_data(as_text=True)

        doc = html.fromstring(html_string)
        assert len(doc.xpath(
            '//h1[contains(normalize-space(), "Which service won the contract?")]')) == 1
        assert "You cannot award this contract as there were no services matching your requirements." \
            in html_string

    def test_which_service_did_you_award_page_should_not_render_if_not_locked_renders(self):
        self.login_as_buyer()
        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_not_lock_project_fixture()

        res = self.client.get(
            '/buyers/direct-award/g-cloud/projects/1/which-service-won-contract')
        assert res.status_code == 400

    def test_which_service_did_you_award_page_creates_direct_award_project_outcome(self):
        self.login_as_buyer()
        self.client.post(
            '/buyers/direct-award/g-cloud/projects/1/which-service-won-contract',
            data={'which_service_won_the_contract': '123456789'},
        )
        self.data_api_client.create_direct_award_project_outcome_award.assert_called_once()

    def test_which_service_did_you_award_should_redirect_to_tell_us_about_contract(self):
        self.login_as_buyer()

        res = self.client.post(
            '/buyers/direct-award/g-cloud/projects/1/which-service-won-contract',
            data={'which_service_won_the_contract': '123456789'})

        assert res.status_code == 302
        assert res.location.endswith('/buyers/direct-award/g-cloud/projects/1/outcomes/1/tell-us-about-contract')

    def test_which_service_raises_410_if_outcome_is_completed(self):
        self.data_api_client.get_direct_award_project.return_value = \
            self._get_direct_award_project_with_completed_outcome_awarded_fixture()
        self.login_as_buyer()

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1/which-service-won-contract')
        assert res.status_code == 410


class TestDirectAwardTellUsAboutContract(TestDirectAwardBase):
    url = '/buyers/direct-award/g-cloud/projects/1/outcomes/1/tell-us-about-contract'

    @pytest.fixture
    def client(self):
        self.login_as_buyer()
        return self.client

    @pytest.fixture
    def xpath(self, client):
        res = client.get(self.url)
        doc = html.fromstring(res.get_data(as_text=True))
        return doc.xpath

    @pytest.fixture
    def data(self):
        return {
            'start_date-day': '31',
            'start_date-month': '12',
            'start_date-year': '2019',
            'end_date-day': '1',
            'end_date-month': '6',
            'end_date-year': '2021',
            'buying_organisation': 'Lewisham Council',
            'value_in_pounds': '100.00'
        }

    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_lock_project_fixture()
        self.data_api_client.get_outcome.return_value = self._get_direct_award_project_outcome_awarded_fixture()

    def test_tell_us_about_contract_exists(self, client):
        assert client.get(self.url).status_code == 200

    def test_tell_us_about_contract_renders(self, xpath):
        assert xpath('boolean(//h1[contains(normalize-space(), "Tell us about your contract")])')

    def test_tell_us_about_contract_form_fields(self, xpath):
        assert len(xpath('//input[@type="text"][substring-after(@name, "start_date")]')) == 3
        assert len(xpath('//input[@type="text"][substring-after(@name, "end_date")]')) == 3
        assert xpath('//input[@type="text"][contains(@name, "value_in_pounds")]')
        assert xpath('//input[@type="text"][contains(@name, "buying_organisation")]')
        assert xpath('//button[normalize-space(string())=$t]', t="Submit")

    def test_previous_page_button_exists_and_points_to_previous_page(self, xpath):
        assert xpath(
            'boolean('
            '//a[@href="/buyers/direct-award/g-cloud/projects/1/which-service-won-contract"]'
            '[contains(normalize-space(), "Previous page")])')

    def test_tell_us_about_contract_form_action_url_is_tell_us_about_contract_url(self, xpath):
        assert xpath('//form[@class="tell-us-about-contract-form"]/@action')[0] == self.url

    def test_tell_us_about_contract_raises_404_if_project_does_not_exist(self, client):
        self.data_api_client.get_direct_award_project.side_effect = HTTPError(mock.Mock(status_code=404))

        assert client.get('/buyers/direct-award/g-cloud/projects/31415/tell-us-about-contract').status_code == 404

    def test_tell_us_about_contract_raises_404_if_project_is_not_accessible(self, client):
        self.data_api_client.get_direct_award_project.return_value['project']['id'] = 314159
        self.data_api_client.get_direct_award_project.return_value['project']['users'][0]['id'] = 321

        assert client.get('/buyers/direct-award/g-cloud/projects/31415/tell-us-about-contract').status_code == 404

    @pytest.mark.parametrize("method", ("GET", "POST"))
    def test_invalid_framework_family(self, method):
        self.login_as_buyer()

        res = self.client.open(
            "/buyers/direct-award/shakespeare/projects/1/tell-us-about-contract",
            method=method,
        )
        assert res.status_code == 404

    def test_tell_us_about_contract_successful_post_redirects_to_project_overview(self, client, data):
        res = client.post(self.url, data=data)
        assert res.status_code == 302
        assert res.location.endswith('/buyers/direct-award/g-cloud/projects/1')
        self.assert_flashes("You’ve updated ‘My procurement project &lt;’", 'success')

    def test_tell_us_about_contract_post_raises_400_and_shows_validation_messages_if_no_form_input(self, client):
        res = client.post(self.url)
        xpath = html.fromstring(res.get_data(as_text=True)).xpath
        assert res.status_code == 400
        assert xpath('boolean(//div[@class="validation-masthead"])')
        assert xpath('count(//a[@class="validation-masthead-link"])') == 4
        assert xpath('count(//span[@class="validation-message"])') == 4

    @pytest.mark.parametrize('invalid_data', (
        {'start_date-year': 'year', 'start_date-month': 'mo', 'start_date-day': 'da'},
        {'end_date-year': 'year', 'end_date-month': 'mo', 'end_date-day': 'da'},
        {'value_in_pounds': 'money'},
        {'buying_organisation': ''},
    ))
    def test_invalid_data_raises_400_and_has_validation_messages_but_remains_in_form(self, client, data, invalid_data):
        data.update(invalid_data)
        res = client.post(self.url, data=data)
        assert res.status_code == 400

        xpath = html.fromstring(res.get_data(as_text=True)).xpath
        assert xpath('count(//span[@class="validation-message"])') == 1
        assert xpath('boolean(//div[@class="validation-masthead"])')
        assert xpath('count(//a[@class="validation-masthead-link"])') == 1

        for field, value in data.items():
            assert xpath(f'//input[@name="{field}"]/@value')[0] == value

    def test_if_end_date_is_before_start_date_raise_400_and_show_validation_message(self, client, data):
        data.update({'end_date-year': str(int(data['start_date-year']) - 1)})
        res = client.post(self.url, data=data)
        assert res.status_code == 400

        xpath = html.fromstring(res.get_data(as_text=True)).xpath
        assert xpath('count(//span[@class="validation-message"])') == 1
        assert xpath('boolean(//div[@class="validation-masthead"])')
        assert xpath('count(//a[@class="validation-masthead-link"])') == 1

    def test_raises_410_if_outcome_is_completed(self, client):
        self.data_api_client.get_outcome.return_value['outcome']['completed'] = True

        res = client.get(self.url)
        assert res.status_code == 410

    def test_raises_404_if_outcome_is_not_assigned_to_project(self, client):
        self.data_api_client.get_outcome.return_value['outcome']['resultOfDirectAward']['project']['id'] = 314157

        res = client.get(self.url)
        assert res.status_code == 404


class TestDirectAwardNonAwardContract(TestDirectAwardBase):
    def setup_method(self, method):
        super().setup_method(method)
        self.data_api_client.find_direct_award_project_services_iter.return_value = \
            self._get_direct_award_project_services_fixture()['services']

        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_lock_project_fixture()

    def test_which_service_did_you_award_page_renders(self):
        self.login_as_buyer()

        res = self.client.get(
            '/buyers/direct-award/g-cloud/projects/1/why-didnt-you-award-contract')
        assert res.status_code == 200

        doc = html.fromstring(res.get_data(as_text=True))
        assert len(doc.xpath(
            '//h1[contains(normalize-space(), "Why didn’t you award a contract?")]')) == 1
        assert len(doc.xpath(
            '//input[@type="radio"][contains(following-sibling::label, "The work has been cancelled")]')) == 1
        assert len(doc.xpath(
            '//span[contains(normalize-space(text()), "For example, because you no longer have the budget")]\
            [contains(parent::label, "The work has been cancelled")]')) == 1
        assert len(doc.xpath(
            '//input[@type="radio"][contains(following-sibling::label, "The work has been cancelled")]')) == 1
        assert len(doc.xpath(
            '//span[contains(normalize-space(text()), "The services in your search results did not meet your requirements")]\
            [contains(parent::label, "There were no suitable services")]')) == 1
        assert len(
            doc.xpath('//button[normalize-space(string())=$t]', t="Save and continue")) == 1

    def test_which_service_did_you_award_page_should_not_render_if_not_locked_renders(self):
        self.login_as_buyer()
        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_not_lock_project_fixture()

        res = self.client.get(
            '/buyers/direct-award/g-cloud/projects/1/why-didnt-you-award-contract')
        assert res.status_code == 400

    def test_why_did_you_not_award_page_creates_direct_award_project_outcome(self):
        self.login_as_buyer()

        self.client.post(
            '/buyers/direct-award/g-cloud/projects/1/why-didnt-you-award-contract',
            data={'why_did_you_not_award_the_contract': 'work_cancelled'}
        )
        self.data_api_client.create_direct_award_project_outcome_cancelled.assert_called_once()

        self.client.post(
            '/buyers/direct-award/g-cloud/projects/1/why-didnt-you-award-contract',
            data={'why_did_you_not_award_the_contract': 'no_suitable_services'}
        )
        self.data_api_client.create_direct_award_project_outcome_none_suitable.assert_called_once()

    def test_why_did_you_not_award_page_raises_410_if_outcome_is_completed(self):
        self.login_as_buyer()
        self.data_api_client.get_direct_award_project.return_value = \
            self._get_direct_award_project_with_completed_outcome_awarded_fixture()

        res = self.client.get(
            '/buyers/direct-award/g-cloud/projects/1/why-didnt-you-award-contract')
        assert res.status_code == 410

    @pytest.mark.parametrize("method", ("GET", "POST"))
    def test_invalid_framework_family(self, method):
        self.login_as_buyer()

        res = self.client.open(
            "/buyers/direct-award/shakespeare/projects/1/why-didnt-you-award-contract",
            method=method,
        )
        assert res.status_code == 404


class TestDirectAwardResultsPage(TestDirectAwardBase):
    def test_results_page_download_links_work(self):
        self.login_as_buyer()

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1/results')
        doc = html.fromstring(res.get_data(as_text=True))

        download_links = doc.xpath('//ul[@class="govuk-list"]//a[@class="govuk-link"]/@href')

        for download_link in download_links:
            res = self.client.get(download_link)
            assert res.status_code == 200


class TestDirectAwardDownloadResultsView(TestDirectAwardBase):
    def setup_method(self, method):
        super().setup_method(method)

        self.project_id = 1
        self.kwargs = {'project_id': 1}
        self.file_context = {
            'filename': 'test', 'sheetname': 'search results',
            'services': self._get_direct_award_project_services_fixture()['services'][:3],
        }

        self.data_api_client.find_direct_award_project_services_iter.return_value = \
            self._get_direct_award_project_services_fixture()['services']

        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_lock_project_fixture()

        self.view = DownloadResultsView()

        self._request_patch = mock.patch.object(self.view, 'request', autospec=False)
        self._request = self._request_patch.start()

        self._current_user_patch = mock.patch('app.main.views.g_cloud.current_user', autospec=True)
        self._current_user = self._current_user_patch.start()
        self._current_user.id = 123
        self._current_user.email_address = 'buyer@example.com'

        self.view._init_hook()

    def teardown_method(self, method):
        self._request_patch.stop()
        self._current_user_patch.stop()
        super().teardown_method(method)

    def test_init_hook(self):
        assert self.view.data_api_client is self.data_api_client
        assert self.view.search_api_client is self.search_api_client
        assert self.view.content_loader is content_loader

    @pytest.mark.parametrize('status_code, call_count',
                             (
                                 (200, 1),
                                 (400, 0),
                                 (404, 0),
                             ))
    def test_post_request_hook(self, status_code, call_count):
        self.view._post_request_hook((None, status_code), **self.kwargs)
        assert self.view.data_api_client.record_direct_award_project_download.call_count == call_count

    def test_determine_filetype(self):
        self.view.request.args = {'filetype': 'csv'}
        filetype = self.view.determine_filetype(self.file_context, **self.kwargs)
        assert filetype == DownloadResultsView.FILETYPES.CSV

        self.view.request.args = {'filetype': 'ods'}
        filetype = self.view.determine_filetype(self.file_context, **self.kwargs)
        assert filetype == DownloadResultsView.FILETYPES.ODS

        self.view.request.args = {'filetype': 'docx'}
        with pytest.raises(BadRequest):
            self.view.determine_filetype(self.file_context, **self.kwargs)

        self.view.request.args = {}
        with pytest.raises(BadRequest):
            self.view.determine_filetype(self.file_context, **self.kwargs)

    def test_get_project_and_search(self):
        project, search = self.view.get_project_and_search(self.project_id)

        assert project is self.view.data_api_client.get_direct_award_project.return_value['project']
        assert search is self.view.data_api_client.find_direct_award_project_searches.return_value['searches'][0]

    def test_get_project_and_search_404s_on_unauthorized_user_access(self):
        with pytest.raises(NotFound):
            self._current_user.id = sys.maxsize
            self.view.get_project_and_search(self.project_id)

    def test_get_project_and_search_400s_for_unlocked_state(self):
        with pytest.raises(BadRequest):
            self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_project_fixture()
            self.view.get_project_and_search(self.project_id)

    def test_get_project_and_search_400s_on_invalid_searches(self):
        self.data_api_client.find_direct_award_project_searches.return_value = {}
        with pytest.raises(BadRequest):
            self.view.get_project_and_search(self.project_id)

            self.data_api_client.find_direct_award_project_searches.return_value = {'searches': []}
        with pytest.raises(BadRequest):
            self.view.get_project_and_search(self.project_id)

    def test_get_file_context(self):
        with self.app.test_request_context('/'):
            file_context = self.view.get_file_context(**self.kwargs)

        assert set(file_context.keys()) == {'framework', 'search', 'project', 'questions', 'services', 'filename',
                                            'sheetname', 'locked_at', 'search_summary'}

        assert file_context['framework'] == 'G-Cloud 9'
        assert file_context['search'] == \
            self.data_api_client.find_direct_award_project_searches.return_value['searches'][0]
        assert file_context['project'] == self.data_api_client.get_direct_award_project.return_value['project']
        assert set(q.id for q in file_context['questions'].values()) == {'serviceName', 'serviceDescription', 'price'}
        assert len(file_context['services']) == 1
        assert file_context['filename'] == '2017-09-08-my-procurement-project-results'
        assert file_context['sheetname'] == "Search results"
        assert file_context['locked_at'] == 'Friday 8 September 2017 at 1:00am BST'
        assert file_context['search_summary'] == '1 result found in All categories'

    def test_get_file_data_and_column_styles(self):
        """This test will quite closely reproduce the implementation, but is the only way I can think of to tightly
        pin the content and styling that will go into the file to be downloaded. It also validates that the structure
        meets the expectations of the parent class."""
        with self.app.test_request_context('/'):
            file_context = self.view.get_file_context(**self.kwargs)
            file_rows, column_styles = self.view.get_file_data_and_column_styles(file_context)

        assert column_styles == [
            {'stylename': 'col-wide'},  # Framework/supplier name
            {'stylename': 'col-wide'},  # Search ended/service name
            {'stylename': 'col-extra-wide'},     # summary/description
            {'stylename': 'col-wide'},  # price
            {'stylename': 'col-wide'},  # service page URL
            {'stylename': 'col-wide'},  # contact name
            {'stylename': 'col-wide'},  # contact telephone
            {'stylename': 'col-extra-wide'},     # contact email
        ]

        # Test content and non-default styles.
        assert file_rows[0]['cells'] == ['Framework', 'Search ended', 'Search summary']
        assert file_rows[0]['meta']['cell_styles']['stylename'] == 'cell-header'

        assert file_rows[1]['cells'] == [file_context['framework'], file_context['locked_at'],
                                         file_context['search_summary']]
        assert file_rows[1]['meta']['row_styles']['stylename'] == 'row-tall-optimal'

        assert file_rows[2]['cells'] == []

        assert file_rows[3]['cells'] == ['Supplier name'] + [k.name for k in file_context['questions'].values()] + \
                                        ['Service page URL', 'Contact name', 'Telephone', 'Email']
        assert file_rows[3]['meta']['cell_styles']['stylename'] == 'cell-header'

        for i, file_row in enumerate(file_rows[4:]):
            assert file_row['cells'][0] == file_context['services'][i]['supplier']['name']

            for j, question in enumerate(file_context['questions'].values()):
                assert file_row['cells'][1 + j] == file_context['services'][i]['data'][question.id]

            assert file_row['cells'][j + 2].getAttribute('href').endswith('/g-cloud/services/123456789')
            assert file_row['cells'][j + 3] == file_context['services'][i]['supplier']['contact']['name']
            assert file_row['cells'][j + 4] == file_context['services'][i]['supplier']['contact']['phone']
            assert file_row['cells'][j + 5] == file_context['services'][i]['supplier']['contact']['email']

    def test_file_download(self):
        self.login_as_buyer()

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1/results/download?filetype=csv')
        assert res.status_code == 200

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1/results/download?filetype=ods')
        assert res.status_code == 200

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1/results/download?filetype=docx')
        assert res.status_code == 400


class TestPreProjectTaskList(TestDirectAwardBase):
    @pytest.mark.parametrize("logged_in_as", (None, "buyer", "supplier",))
    def test_pre_project_task_list(self, logged_in_as):
        if logged_in_as == "buyer":
            self.login_as_buyer()
        if logged_in_as == "supplier":
            self.login_as_supplier()

        res = self.client.get('/buyers/direct-award/g-cloud/start')
        assert res.status_code == 200

        doc = html.fromstring(res.get_data(as_text=True))

        breadcrumbs = doc.xpath("//div[@class='govuk-breadcrumbs']/ol/li")
        assert tuple(li.xpath("normalize-space(string())") for li in breadcrumbs) == (
            "Digital Marketplace",
            "Find cloud hosting, software and support",
        )
        assert tuple(li.xpath(".//a/@href") for li in breadcrumbs) == (
            ["/"],
            [],
        )

        assert doc.xpath("//h1[normalize-space(string())=$t]", t="Find cloud hosting, software and support")
        assert doc.xpath(
            "//head/title[starts-with(normalize-space(string()), $t)]",
            t="Find cloud hosting, software and support",
        )

        assert doc.xpath("//p[starts-with(normalize-space(string()), $t)]", t="Before you start you should")

        # there shouldn't be "Can't start yet" steps
        assert not doc.xpath(
            "//li[contains(@class, 'instruction-list-item')]"
            "[.//*[contains(@class, 'instruction-list-item-box')][normalize-space(string())=$t]]",
            t="Can’t start yet",
        )

        # but there should be more than one step shown
        steps = doc.xpath("//li[contains(@class, 'instruction-list-item')]")
        assert len(steps) > 1
        active_step = steps[0]

        assert active_step.xpath(
            ".//a[@href=$u][contains(@class, 'button-save')][normalize-space(string())=$t]",
            u="/buyers/direct-award/g-cloud/choose-lot",
            t="Start a new search",
        )

        assert active_step.xpath(
            ".//a[@href=$u][normalize-space(string())=$t]",
            u="/buyers/direct-award/g-cloud",
            t="See a list of your saved searches",
        )

    def test_invalid_framework_family(self):
        res = self.client.get('/buyers/direct-award/shakespeare/start')
        assert res.status_code == 404
