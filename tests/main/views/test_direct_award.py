from lxml import html
from html import escape as html_escape
import mock
import pytest

from dmcontent.content_loader import ContentLoader
from app import search_api_client
from app.main.views.g_cloud import data_api_client
from ...helpers import BaseApplicationTest


class TestDirectAward(BaseApplicationTest):
    def setup_method(self, method):
        super(TestDirectAward, self).setup_method(method)

        self._search_api_client_patch = mock.patch('app.main.views.g_cloud.search_api_client', autospec=True)
        self._search_api_client = self._search_api_client_patch.start()

        self._search_api_client_presenters_patch = mock.patch('app.main.presenters.search_presenters.search_api_client',
                                                              autospec=True)
        self._search_api_client_presenters = self._search_api_client_presenters_patch.start()
        self._search_api_client_presenters.aggregate_services.return_value = \
            self._get_fixture_data('g9_aggregations_fixture.json')

        self._search_api_client.get_index_from_search_api_url.return_value = 'g-cloud-9'

        self.g9_search_results = self._get_g9_search_results_fixture_data()

        data_api_client.get_direct_award_project = mock.Mock()
        data_api_client.get_direct_award_project.return_value = self._get_direct_award_project_fixture()

        data_api_client.get_framework = mock.Mock()
        data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-9')

        data_api_client.find_direct_award_project_searches = mock.Mock()
        data_api_client.find_direct_award_project_searches.return_value = \
            self._get_direct_award_project_searches_fixture()

    def teardown_method(self, method):
        self._search_api_client_patch.stop()
        self._search_api_client_presenters_patch.stop()

    def test_renders_save_search_button(self):
        self._search_api_client.search_services.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search')
        assert res.status_code == 200

        doc = html.fromstring(res.get_data(as_text=True))
        assert len(doc.xpath('//button[@id="save-search"'
                             ' and @formaction="/buyers/direct-award/g-cloud/save-search"]')) == 1

    def test_save_search_redirects_to_login(self):
        res = self.client.get('/buyers/direct-award/g-cloud/save-search?lot=cloud-software')
        assert res.status_code == 302
        assert res.location == 'http://localhost/user/login?next=' \
                               '%2Fbuyers%2Fdirect-award%2Fg-cloud%2Fsave-search%3Flot%3Dcloud-software'

    def test_save_search_renders_summary_on_page(self):
        self.login_as_buyer()
        self._search_api_client.search_services.return_value = self.g9_search_results

        res = self.client.get('/buyers/direct-award/g-cloud/save-search?lot=cloud-software')
        assert res.status_code == 200

        summary = self.find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1150</span> results found in <em>Cloud software</em>' in summary


class TestDirectAwardProjectOverview(BaseApplicationTest):
    def setup_method(self, method):
        super(TestDirectAwardProjectOverview, self).setup_method(method)

        self._search_api_client_patch = mock.patch('app.main.views.g_cloud.search_api_client', autospec=True)
        self._search_api_client = self._search_api_client_patch.start()

        self._search_api_client.get_frontend_params_from_search_api_url.return_value = (('q', 'accelerator'), )

        self._search_api_client_presenters_patch = mock.patch(
            'app.main.presenters.search_presenters.search_api_client',
            autospec=True)
        self._search_api_client_presenters = self._search_api_client_presenters_patch.start()
        self._search_api_client_presenters.aggregate_services.return_value = \
            self._get_fixture_data('g9_aggregations_fixture.json')

        self.g9_search_results = self._get_g9_search_results_fixture_data()

        data_api_client.get_direct_award_project = mock.Mock()
        data_api_client.get_direct_award_project.return_value = self._get_direct_award_project_fixture()

        data_api_client.get_framework = mock.Mock()
        data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-9')

        data_api_client.find_direct_award_project_searches = mock.Mock()
        data_api_client.find_direct_award_project_searches.return_value = \
            self._get_direct_award_project_searches_fixture()

        self.login_as_buyer()

        self.content_loader = ContentLoader('tests/fixtures/content')
        self.content_loader.load_messages('g9', ['urls'])

    def teardown_method(self, method):
        self._search_api_client_patch.stop()
        self._search_api_client_presenters_patch.stop()

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
        return self._task_has_box(tasklist, task, style='inactive', text='Can\'t start yet')

    def _task_search_saved(self, tasklist, task):
        return self._task_has_box(tasklist, task, style='complete', text='Search saved on Tuesday 29 August 2017'
                                                                         ' at 7:00am GMT')

    def _task_search_ended(self, tasklist, task):
        return self._task_has_box(tasklist, task, style='complete', text='Search ended on Tuesday 29 August 2017'
                                                                         ' at 7:00am GMT')

    def _task_search_downloaded(self, tasklist, task):
        return self._task_has_box(tasklist, task, style='complete', text='Shortlist downloaded')

    def _cannot_start_from_task(self, tasklist, cannot_start_from):
        return all([self._task_cannot_start_yet(tasklist, task + 1) is ((task + 1) >= cannot_start_from)
                    for task in range(len(tasklist))])

    def test_view_project_page_shows_title(self):
        self.login_as_buyer()

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

        item_headings = ['Prepare your requirements', 'Search for services', 'Review services', 'Create a shortlist',
                         'Compare services', 'Award a contract', 'Publish the contract',
                         'Complete the customer benefits record form']

        tasklist = doc.xpath('//li[@class="instruction-list-item divider"]')

        for i, item in enumerate(tasklist):
            assert item.xpath('h2/span/text()')[0].startswith(str(i + 1))
            assert item.xpath('h2/text()')[0] == item_headings[i]

    def test_overview_renders_links_common_to_all_states(self):
        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[@class="instruction-list-item divider"]')

        # Step 1 should link to the guidance for preparing requirements.
        assert self._task_has_link(tasklist, 1, 'https://www.gov.uk/guidance/talking-to-suppliers-before-you-buy-'
                                                'digital-marketplace-services') is True

        # Step 5 should link to guidance on comparing services.
        buyer_guide_compare_services_url = self.content_loader.get_message('g9', 'urls',
                                                                           'buyers_guide_compare_services_url')
        assert self._task_has_link(tasklist, 5, buyer_guide_compare_services_url) is True

        # Step 6 has links to downloading call-off contracts and how to award contracts.
        call_off_contract_url = self.content_loader.get_message('g9', 'urls', 'call_off_contract_url')
        assert self._task_has_link(tasklist, 6, call_off_contract_url) is True
        assert self._task_has_link(tasklist, 6, "https://www.gov.uk/guidance/how-to-award-a-contract"
                                                "-when-you-buy-services") is True

        # Step 7 has a link to Contracts Finder
        assert self._task_has_link(tasklist, 7, "https://www.gov.uk/contracts-finder") is True

        # Step 8 has a link to framework customer benefits form and customer benefits form email address.
        customer_benefits_record_form_url = self.content_loader.get_message('g9', 'urls',
                                                                            'customer_benefits_record_form_url')
        customer_benefits_record_form_email = self.content_loader.get_message('g9', 'urls',
                                                                              'customer_benefits_record_form_email')
        assert self._task_has_link(tasklist, 8, customer_benefits_record_form_url) is True
        assert self._task_has_link(tasklist, 8, 'mailto:{}'.format(customer_benefits_record_form_email)) is True

    def test_overview_renders_specific_elements_for_no_search_state(self):
        searches = self._get_direct_award_project_searches_fixture()

        searches['searches'] = []

        data_api_client.find_direct_award_project_searches.return_value = searches

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[@class="instruction-list-item divider"]')

        assert self._task_has_link(tasklist, 2, '/g-cloud/search') is True
        assert self._task_has_link(tasklist, 3, '/g-cloud/search') is False
        assert self._task_has_link(tasklist, 4, '/buyers/direct-award/g-cloud/projects/1/end-search') is False

        assert self._cannot_start_from_task(tasklist, 3) is True

    def test_overview_renders_specific_elements_for_search_created_state(self):
        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[@class="instruction-list-item divider"]')

        assert self._task_has_link(tasklist, 2, '/g-cloud/search?q=accelerator') is True
        assert self._task_has_link(tasklist, 3, '/g-cloud/search?q=accelerator') is True
        assert self._task_has_link(tasklist, 4, '/buyers/direct-award/g-cloud/projects/1/end-search') is True

        assert self._cannot_start_from_task(tasklist, 5) is True

        assert doc.xpath('//p[contains(@class, "search-summary")]')[0].text_content() == '1 result found containing '\
                                                                                         'accelerator in All categories'
        assert self._task_search_saved(tasklist, 2) is True

    def test_overview_renders_specific_elements_for_search_ended_state(self):
        searches = self._get_direct_award_project_searches_fixture()
        for search in searches['searches']:
            search['searchedAt'] = search['createdAt']

        data_api_client.find_direct_award_project_searches.return_value = searches

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[@class="instruction-list-item divider"]')

        assert self._task_has_link(tasklist, 2, '/g-cloud/search?q=accelerator') is True
        assert self._task_has_link(tasklist, 3, '/g-cloud/search?q=accelerator') is False
        assert self._task_search_ended(tasklist, 4) is True
        assert self._task_has_link(tasklist, 5,
                                   '/buyers/direct-award/g-cloud/projects/1/download-shortlist') is True

        assert self._cannot_start_from_task(tasklist, 6) is True

    def test_overview_renders_specific_elements_for_search_downloaded_state(self):
        searches = self._get_direct_award_project_searches_fixture()
        for search in searches['searches']:
            search['searchedAt'] = search['createdAt']

        project = self._get_direct_award_project_fixture()
        project['project']['downloadedAt'] = project['project']['createdAt']
        data_api_client.get_direct_award_project.return_value = project

        data_api_client.find_direct_award_project_searches.return_value = searches

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)

        tasklist = doc.xpath('//li[@class="instruction-list-item divider"]')

        assert self._task_has_link(tasklist, 2, '/g-cloud/search?q=accelerator') is True
        assert self._task_has_link(tasklist, 3, '/g-cloud/search?q=accelerator') is False
        assert self._task_search_downloaded(tasklist, 5) is True
        assert self._task_has_link(tasklist, 5,
                                   '/buyers/direct-award/g-cloud/projects/1/download-shortlist') is True

        assert self._cannot_start_from_task(tasklist, 9) is True


class TestDirectAwardURLGeneration(BaseApplicationTest):
    """This class has been separated out from above because we only want to mock a couple of methods on the API clients,
    not all of them (like the class above)"""
    def setup_method(self, method):
        super(TestDirectAwardURLGeneration, self).setup_method(method)

        self.g9_search_results = self._get_g9_search_results_fixture_data()

        search_api_client.search_services = mock.Mock()
        search_api_client.search_services.return_value = self.g9_search_results

        data_api_client.get_framework = mock.Mock()
        data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-9')

        data_api_client.get_direct_award_project = mock.Mock()
        data_api_client.get_direct_award_project.return_value = self._get_direct_award_project_fixture()

        data_api_client.find_direct_award_project_searches = mock.Mock()
        data_api_client.find_direct_award_project_searches.return_value = \
            self._get_direct_award_project_searches_fixture()

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

        search_api_client._get = mock.Mock()
        search_api_client._get.return_value = self._get_search_results_fixture_data()

        project_searches = data_api_client.find_direct_award_project_searches.return_value
        project_searches['searches'][0]['searchUrl'] = search_api_url

        res = self.client.get('/buyers/direct-award/g-cloud/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)
        assert html_escape(frontend_url) in body
        assert len(doc.xpath('//a[@href="{}"]'.format(frontend_url)))
