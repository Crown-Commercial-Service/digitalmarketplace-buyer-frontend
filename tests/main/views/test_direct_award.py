from dateutil import parser
import sys
from urllib.parse import quote_plus, urlparse

from html import escape as html_escape
from lxml import html
import mock
import pytest
from werkzeug.exceptions import BadRequest, NotFound

from dmapiclient import HTTPError
from dmcontent.content_loader import ContentLoader

from app import search_api_client, content_loader
from app.main.views.g_cloud import DownloadResultsView, END_SEARCH_LIMIT, TOO_MANY_RESULTS_MESSAGE
from ...helpers import BaseApplicationTest


class TestDirectAwardBase(BaseApplicationTest):
    def setup_method(self, method):
        super().setup_method(method)
        self._search_api_client_patch = mock.patch('app.main.views.g_cloud.search_api_client', autospec=True)
        self._search_api_client = self._search_api_client_patch.start()
        self._search_api_client.aggregate.return_value = \
            self._get_fixture_data('g9_aggregations_fixture.json')

        self._search_api_client.get_index_from_search_api_url.return_value = 'g-cloud-9'

        self._search_api_client_presenters_patch = mock.patch('app.main.presenters.search_presenters.search_api_client',
                                                              new=self._search_api_client)
        self._search_api_client_presenters = self._search_api_client_presenters_patch.start()

        self._search_api_client_helpers_patch = \
            mock.patch('app.main.helpers.search_save_helpers.search_api_client', new=self._search_api_client)
        self._search_api_client_helpers = self._search_api_client_helpers_patch.start()

        self.g9_search_results = self._get_g9_search_results_fixture_data()

        self.data_api_client_patch = mock.patch('app.main.views.g_cloud.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.data_api_client.find_frameworks.return_value = self._get_frameworks_list_fixture_data()
        self.data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-9')

        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_project_fixture()
        self.data_api_client.find_direct_award_projects.return_value = self._get_direct_award_project_list_fixture()
        self.data_api_client.find_direct_award_project_searches.return_value = \
            self._get_direct_award_project_searches_fixture()

    def teardown_method(self, method):
        self._search_api_client_patch.stop()
        self._search_api_client_presenters_patch.stop()
        self._search_api_client_helpers_patch.stop()

        self.data_api_client_patch.stop()
        super().teardown_method(method)


class TestDirectAward(TestDirectAwardBase):
    @classmethod
    def setup_class(cls):

        cls.SAVE_SEARCH_OVERVIEW_URL = '/buyers/direct-award/g-cloud'
        cls.SAVE_SEARCH_URL = '/buyers/direct-award/g-cloud/save-search'
        cls.SIMPLE_SEARCH_PARAMS = 'lot=cloud-software'
        cls.SEARCH_URL = '/g-cloud/search?' + cls.SIMPLE_SEARCH_PARAMS
        cls.PROJECT_CREATE_URL = '/buyers/direct-award/g-cloud/projects/create'
        cls.SIMPLE_SAVE_SEARCH_URL = '{}?search_query={}'.format(
            cls.SAVE_SEARCH_URL, quote_plus(cls.SIMPLE_SEARCH_PARAMS))
        cls.SEARCH_API_URL = 'g-cloud-9/services/search'

    def test_renders_saved_search_overview(self):
        self.login_as_buyer()
        res = self.client.get(self.SAVE_SEARCH_OVERVIEW_URL)
        assert res.status_code == 200

        result_html = res.get_data(as_text=True)
        doc = html.fromstring(result_html)
        page_header = doc.xpath('//*[@id="content"]/div/header/h1')[0].text.strip()

        assert page_header == "Your saved searches"
        assert page_header in doc.xpath('/html/head/title')[0].text.strip()
        assert doc.xpath('//*[@id="searching_table"]')[0].text.strip() == "Searching"
        assert doc.xpath('//*[@id="search_ended_table"]')[0].text.strip() == "Search ended"

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

    def test_renders_save_search_button(self):
        self._search_api_client.search.return_value = self.g9_search_results

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
        self._search_api_client.search.return_value = self.g9_search_results

        res = self.client.get(self.SIMPLE_SAVE_SEARCH_URL)

        assert res.status_code == 200

        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1150</span> results found in <em>Cloud software</em>' in summary

    def _save_search(self, name, save_search_selection="new_search"):
        self.login_as_buyer()
        self._search_api_client.search.return_value = self.g9_search_results
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
        assert "Names must be between 1 and 100 characters" in html

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


class TestDirectAwardProjectOverview(TestDirectAwardBase):
    def setup_method(self, method):
        super().setup_method(method)

        self._search_api_client.get_frontend_params_from_search_api_url.return_value = (('q', 'accelerator'), )

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

    def _task_has_box(self, tasklist, task, style, text):
        if task <= 0:
            raise ValueError()

        box = tasklist[task - 1].xpath('.//p[@class="instruction-list-item-box {}"'
                                       ' and normalize-space(text())="{}"]'.format(style, text))
        return len(box) == 1

    def _task_cannot_start_yet(self, tasklist, task):
        return self._task_has_box(tasklist, task, style='inactive', text='Can’t start yet')

    def _task_search_ended(self, tasklist, task):
        return self._task_has_box(tasklist, task, style='complete', text='Search ended on Tuesday 29 August 2017'
                                                                         ' at 8:00am BST')

    def _task_search_downloaded(self, tasklist, task):
        return self._task_has_box(tasklist, task, style='complete', text='Search results downloaded')

    def _cannot_start_from_task(self, tasklist, cannot_start_from):
        return all([self._task_cannot_start_yet(tasklist, task + 1) is ((task + 1) >= cannot_start_from)
                    for task in range(len(tasklist))])

    def test_view_project_page_shows_title(self):
        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')

        doc = html.fromstring(res.get_data(as_text=True))
        project_name = self._get_direct_award_project_fixture()['project']['name']
        assert len(doc.xpath('//h1[contains(normalize-space(text()), "{}")]'.format(project_name))) == 1

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

        item_headings = ['Save a search', 'Export your results', 'Download your search results',
                         'Award a contract', 'Complete the Customer Benefits Record form']

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
        assert self._task_has_link(tasklist, 1, 'https://www.gov.uk/guidance/how-to-buy-digital-marketplace-'
                                                'services-fairly')

        # Step 3 should link to guidance on comparing services.
        buyer_guide_compare_services_url = self.content_loader.get_message('g9', 'urls',
                                                                           'buyers_guide_compare_services_url')
        assert self._task_has_link(tasklist, 3, buyer_guide_compare_services_url)

        # Step 5 has a link to framework customer benefits form and customer benefits form email address.
        customer_benefits_record_form_url = self.content_loader.get_message('g9', 'urls',
                                                                            'customer_benefits_record_form_url')
        customer_benefits_record_form_email = self.content_loader.get_message('g9', 'urls',
                                                                              'customer_benefits_record_form_email')
        assert self._task_has_link(tasklist, 5, customer_benefits_record_form_url)
        assert self._task_has_link(tasklist, 5, 'mailto:{}'.format(customer_benefits_record_form_email))

    def test_overview_renders_specific_elements_for_no_search_state(self):
        searches = self._get_direct_award_project_searches_fixture()

        searches['searches'] = []

        self.data_api_client.find_direct_award_project_searches.return_value = searches

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[contains(@class, "instruction-list-item")]')

        assert self._task_has_link(tasklist, 1, '/g-cloud/search')
        assert self._task_has_link(tasklist, 2, '/buyers/direct-award/g-cloud/projects/1/end-search') is False

        assert self._cannot_start_from_task(tasklist, 2)

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
        assert self._task_search_ended(tasklist, 2)
        assert self._task_has_link(tasklist, 3,
                                   '/buyers/direct-award/g-cloud/projects/1/results')

        assert self._task_has_link(tasklist, 4,
                                   '/buyers/direct-award/g-cloud/projects/1/did-you-award-contract') is False

    def test_overview_renders_specific_elements_for_search_downloaded_state(self):
        searches = self._get_direct_award_project_searches_fixture()
        for search in searches['searches']:
            search['searchedAt'] = search['createdAt']

        project = self._get_direct_award_project_fixture()
        project['project']['downloadedAt'] = project['project']['createdAt']
        self.data_api_client.get_direct_award_project.return_value = project

        self.data_api_client.find_direct_award_project_searches.return_value = searches

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[contains(@class, "instruction-list-item")]')

        assert self._task_has_link(tasklist, 1, '/g-cloud/search?q=accelerator') is False
        assert self._task_search_downloaded(tasklist, 3)
        assert self._task_has_link(tasklist, 3,
                                   '/buyers/direct-award/g-cloud/projects/1/results')

        assert self._cannot_start_from_task(tasklist, 5)


class TestDirectAwardURLGeneration(BaseApplicationTest):
    """This class has been separated out from above because we only want to mock a couple of methods on the API clients,
    not all of them (like the class above)"""
    def setup_method(self, method):
        super().setup_method(method)

        self.data_api_client_patch = mock.patch('app.main.views.g_cloud.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.data_api_client.find_frameworks.return_value = self._get_frameworks_list_fixture_data()
        self.data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-9')

        self.data_api_client.get_direct_award_project.return_value = self._get_direct_award_project_fixture()
        self.data_api_client.find_direct_award_project_searches.return_value = \
            self._get_direct_award_project_searches_fixture()

    def teardown_method(self, method):
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
    def test_search_api_urls_convert_to_correct_frontend_urls(self, search_api_url, frontend_url):
        self.login_as_buyer()

        with mock.patch.object(search_api_client, 'search') as search_patch, \
                mock.patch.object(search_api_client, '_get') as _get_patch:

            search_patch.return_value = self._get_g9_search_results_fixture_data()
            _get_patch.return_value = self._get_search_results_fixture_data()

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
        assert len(doc.xpath('//h1[contains(normalize-space(), "End your search")]')) == 1

    def test_end_search_page_renders_error_when_results_more_than_limit(self):
        self.login_as_buyer()

        self._search_api_client_helpers._get.return_value = {
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

    def test_end_search_redirects_to_project_page(self):
        self.login_as_buyer()

        self.data_api_client.lock_direct_award_project.return_value = self._get_direct_award_lock_project_fixture()

        res = self.client.post('/buyers/direct-award/g-cloud/projects/1/end-search')

        assert res.status_code == 302
        assert res.location.endswith('/buyers/direct-award/g-cloud/projects/1')


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
            '//h1[contains(normalize-space(), "Did you award a contract for ‘My procurement project’?")]')) == 1
        assert len(doc.xpath('//input[@type="radio"][contains(following-sibling::label, "Yes")]')) == 1
        assert len(doc.xpath('//input[@type="radio"][contains(following-sibling::label, "No")]')) == 1
        assert len(doc.xpath(
            '//input[@type="radio"][contains(following-sibling::label, "We are still assessing services")]')) == 1
        assert len(doc.xpath('//input[@type="submit"][@value="Save and continue"]')) == 1

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
        assert len(doc.xpath('//legend[contains(normalize-space(), "You need to answer this question.")]')) == 1
        assert doc.xpath('boolean(//div[@class="validation-masthead"])')
        assert doc.xpath('count(//div[@class="validation-masthead"]/a[@class="validation-masthead-link"])') == 1

    @pytest.mark.parametrize('choice, expected_redirect',
                             (('still-assessing', '/buyers/direct-award/g-cloud/projects/1'),
                              ('yes', '/buyers/direct-award/g-cloud/projects/1/which-service-won-contract'),
                              ('no', '/buyers/direct-award/g-cloud/projects/1/why-didnt-you-award-contract')))
    def test_award_contract_we_are_still_assessing_redirects_on_post(self, choice, expected_redirect):
        self.login_as_buyer()

        res = self.client.post('/buyers/direct-award/g-cloud/projects/1/did-you-award-contract',
                               data={'did_you_award_a_contract': choice})

        assert res.status_code == 302
        assert res.location.endswith(expected_redirect)

    def test_award_contract_raises_404_if_project_is_not_accessible(self):
        self.data_api_client.get_direct_award_project.side_effect = HTTPError(mock.Mock(status_code=404))
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
            doc.xpath('//input[@type="submit"][@value="Save and continue"]')) == 1

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
        assert xpath('count(//input[@type="text"][substring-after(@name, "start_date")])') == 3
        assert xpath('count(//input[@type="text"][substring-after(@name, "end_date")])') == 3
        assert xpath('boolean(//input[@type="text"][contains(@name, "value_in_pounds")])')
        assert xpath('boolean(//input[@type="text"][contains(@name, "buying_organisation")])')
        assert xpath('boolean(//input[@type="submit"][@value="Submit"])')

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

    def test_tell_us_about_contract_successful_post_redirects_to_project_overview(self, client, data):
        res = client.post(self.url, data=data)
        assert res.status_code == 302
        assert res.location.endswith('/buyers/direct-award/g-cloud/projects/1')
        self.assert_flashes("You’ve updated ‘My procurement project’", 'success')

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
            doc.xpath('//input[@type="submit"][@value="Save and continue"]')) == 1

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


class TestDirectAwardResultsPage(TestDirectAwardBase):
    def test_results_page_download_links_work(self):
        self.login_as_buyer()

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1/results')
        doc = html.fromstring(res.get_data(as_text=True))

        download_links = doc.xpath('//ul[@class="document-list"]//a[@class="document-link-with-icon"]/@href')

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
        assert self.view.search_api_client is self._search_api_client
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
