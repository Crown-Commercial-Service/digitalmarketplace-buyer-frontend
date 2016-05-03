# coding=utf-8

import mock
from nose.tools import assert_equal, assert_true, assert_in
from lxml import html
from ...helpers import BaseApplicationTest
from dmapiclient import APIError


class TestApplication(BaseApplicationTest):
    def setup(self):
        super(TestApplication, self).setup()

    def test_analytics_code_should_be_in_javascript(self):
        res = self.client.get('/static/javascripts/application.js')
        assert_equal(200, res.status_code)
        assert_true(
            'trackPageview'
            in res.get_data(as_text=True))

    def test_should_use_local_cookie_page_on_cookie_message(self):
        res = self.client.get('/')
        assert_equal(200, res.status_code)
        assert_true(
            '<p>GOV.UK uses cookies to make the site simpler. <a href="/cookies">Find out more about cookies</a></p>'
            in res.get_data(as_text=True)
        )


class TestHomepageBrowseList(BaseApplicationTest):
    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_dos_links_not_shown_when_dos_is_pending(self, data_api_client):
        with self.app.app_context():
            data_api_client.find_frameworks.return_value = {"frameworks": [
                {"slug": "digital-outcomes-and-specialists",
                 "status": "pending"}
            ]}

            res = self.client.get("/")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            link_texts = [item.text_content().strip() for item in document.cssselect('.browse-list-item a')]
            assert link_texts[0] == "Find cloud technology and support"
            assert link_texts[-2] == "Find specialists to work on digital projects"
            assert link_texts[-1] == "Digital Services"

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_dos_links_are_shown_when_dos_is_live(self, data_api_client):
        with self.app.app_context():
            data_api_client.find_frameworks.return_value = {"frameworks": [
                {"slug": "digital-outcomes-and-specialists",
                 "status": "live"}
            ]}

            res = self.client.get("/")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            link_texts = [item.text_content().strip() for item in document.cssselect('.browse-list-item a')]
            assert link_texts[0] == "Find an individual specialist"
            assert link_texts[-1] == "Buy physical datacentre space for legacy systems"
            assert "Find specialists to work on digital projects" not in link_texts

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_buyer_dashboard_link_exists_when_dos_is_live_and_buyer_logged_in(self, data_api_client):
        with self.app.app_context():
            data_api_client.find_frameworks.return_value = {"frameworks": [
                {"slug": "digital-outcomes-and-specialists",
                 "status": "live"}
            ]}
            self.login_as_buyer()

            res = self.client.get("/")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            link_texts = [item.text_content().strip() for item in document.cssselect('.browse-list-item a')]
            assert link_texts[-1] == "View your requirements and supplier responses"


class TestHomepageSidebarMessage(BaseApplicationTest):
    def setup(self):
        super(TestHomepageSidebarMessage, self).setup()

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

    @mock.patch('app.main.views.marketplace.data_api_client')
    def _load_homepage(self, framework_slugs_and_statuses, framework_messages, data_api_client):

        data_api_client.find_frameworks.return_value = self._find_frameworks(framework_slugs_and_statuses)
        res = self.client.get('/')
        assert_equal(200, res.status_code)
        response_data = res.get_data(as_text=True)

        if framework_messages:
            self._assert_message_container_is_not_empty(response_data)
            for message in framework_messages:
                assert_in(message, response_data)
        else:
            self._assert_message_container_is_empty(response_data)

    def test_homepage_sidebar_message_exists_dos_coming(self):

        framework_slugs_and_statuses = [
            ('g-cloud-7', 'pending'),
            ('digital-outcomes-and-specialists', 'coming')
        ]
        framework_messages = [
            u"Become a Digital Outcomes and Specialists supplier",
            u"Digital Outcomes and Specialists will be open for applications soon."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

    def test_homepage_sidebar_message_exists_dos_open(self):

        framework_slugs_and_statuses = [
            ('g-cloud-7', 'pending'),
            ('digital-outcomes-and-specialists', 'open')
        ]
        framework_messages = [
            u"Become a Digital Outcomes and Specialists supplier",
            u"Digital Outcomes and Specialists is open for applications."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

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
            u"The application deadline is 5pm BST, 21 June 2016."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

    def test_homepage_sidebar_message_exists_g_cloud_7_pending(self):

        framework_slugs_and_statuses = [
            ('g-cloud-7', 'pending')
        ]
        framework_messages = [
            u"G‑Cloud 7 is closed for applications",
            u"G‑Cloud 7 services will be available from 23 November 2015."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

    @mock.patch('app.main.views.marketplace.data_api_client')
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
        assert 'View your services and account information' not in sidebar_link_texts

    @mock.patch('app.main.views.marketplace.data_api_client')
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
        assert 'View your services and account information' in sidebar_link_texts
        assert 'Create a supplier account' not in sidebar_link_texts

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_no_homepage_sidebar_messages_are_shown_to_not_logged_in_users_before_dos_is_live(self, data_api_client):
        data_api_client.find_frameworks.return_value = self._find_frameworks([
            ('digital-outcomes-and-specialists', 'standstill')
        ])
        res = self.client.get('/')

        assert res.status_code == 200
        self._assert_message_container_is_empty(res.get_data(as_text=True))

    def test_homepage_sidebar_message_doesnt_exist_without_frameworks(self):
        framework_slugs_and_statuses = [
            ('g-cloud-2', 'expired'),
            ('g-cloud-3', 'expired'),
            ('g-cloud-4', 'expired')
        ]

        # there are no messages
        self._load_homepage(framework_slugs_and_statuses, None)

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_api_error_message_doesnt_exist(self, data_api_client):

        data_api_client.find_frameworks.side_effect = APIError()
        res = self.client.get('/')
        assert_equal(200, res.status_code)
        self._assert_message_container_is_empty(res.get_data(as_text=True))

    # here we've given an valid framework with a valid status but there is no message.yml file to read from
    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_g_cloud_6_open_blows_up(self, data_api_client):
        framework_slugs_and_statuses = [
            ('g-cloud-6', 'open')
        ]

        data_api_client.find_frameworks.return_value = self._find_frameworks(framework_slugs_and_statuses)
        res = self.client.get('/')
        assert_equal(500, res.status_code)


class TestStaticMarketplacePages(BaseApplicationTest):
    def setup(self):
        super(TestStaticMarketplacePages, self).setup()

    def test_cookie_page(self):
        res = self.client.get('/cookies')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>Cookies</h1>'
            in self._strip_whitespace(res.get_data(as_text=True))
        )

    def test_cookie_page(self):
        res = self.client.get('/terms-and-conditions')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>Termsandconditions</h1>'
            in self._strip_whitespace(res.get_data(as_text=True))
        )


class TestBriefPage(BaseApplicationTest):

    def setup(self):
        super(TestBriefPage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.views.marketplace.data_api_client'
        ).start()

        self.brief = self._get_dos_brief_fixture_data()
        self._data_api_client.get_brief.return_value = self.brief

    def teardown(self):
        self._data_api_client.stop()

    def _assert_page_title(self, document):
        brief_title = self.brief['briefs']['title']
        brief_organisation = self.brief['briefs']['organisation']

        page_heading = document.xpath('//header[@class="page-heading-smaller"]')[0]
        page_heading_h1 = page_heading.xpath('h1/text()')[0]
        page_heading_context = page_heading.xpath('p[@class="context"]/text()')[0]

    def test_dos_brief_404s_if_brief_is_draft(self):
        self.brief['briefs']['status'] = 'draft'
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert_equal(404, res.status_code)

    def test_dos_brief_has_correct_title(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        self._assert_page_title(document)

    def test_dos_brief_has_important_dates(self):
        brief_id = self.brief['briefs']['id']
        self.brief['briefs']['clarificationQuestionsClosedAt'] = "2016-03-10T11:08:28.054129Z"
        self.brief['briefs']['applicationsClosedAt'] = "2016-03-11T11:08:28.054129Z"
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        brief_important_dates = document.xpath(
            '(//table[@class="summary-item-body"])[1]/tbody/tr')

        assert_equal(len(brief_important_dates), 3)
        assert_true(brief_important_dates[0].xpath(
            'td[@class="summary-item-field-first"]')[0].text_content().strip(), "Published")
        assert_true(brief_important_dates[0].xpath(
            'td[@class="summary-item-field"]')[0].text_content().strip(), "Thursday 25 February 2016")
        assert_true(brief_important_dates[1].xpath(
            'td[@class="summary-item-field-first"]')[0].text_content().strip(), "Deadline for asking questions")
        assert_true(brief_important_dates[1].xpath(
            'td[@class="summary-item-field"]')[0].text_content().strip(), "Thursday 10 March 2016")
        assert_true(brief_important_dates[2].xpath(
            'td[@class="summary-item-field-first"]')[0].text_content().strip(), "Closing date for applications")
        assert_true(brief_important_dates[2].xpath(
            'td[@class="summary-item-field"]')[0].text_content().strip(), "Thursday 11 March 2016")

    def test_dos_brief_has_at_least_one_section(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        section_heading = document.xpath('//h2[@class="summary-item-heading"]')[0]
        section_attributes = section_heading.xpath('following-sibling::table[1]/tbody/tr')

        start_date_key = section_attributes[2].xpath('td[1]/span/text()')
        start_date_value = section_attributes[2].xpath('td[2]/span/text()')

        contract_length_key = section_attributes[3].xpath('td[1]/span/text()')
        contract_length_value = section_attributes[3].xpath('td[2]/span/text()')

        assert_equal(section_heading.get('id'), 'opportunity-attributes-1')
        assert_equal(section_heading.text.strip(), 'Overview')
        assert_equal(start_date_key[0], 'Latest start date')
        assert_equal(start_date_value[0], '01/03/2016')
        assert_equal(contract_length_key[0], 'Expected contract length')
        assert_equal(contract_length_value[0], '4 weeks')

    def test_dos_brief_has_question_and_answer_session_details_link(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))

        document = html.fromstring(res.get_data(as_text=True))
        qa_session_link_text = document.xpath(
            '//a[@href="/suppliers/opportunities/{}/question-and-answer-session"]/text()'.format(brief_id)
        )[0].strip()

        assert qa_session_link_text == "Log in to view question and answer session details"

    def test_dos_brief_question_and_answer_session_details_hidden_when_questions_closed(self):
        self.brief['briefs']['clarificationQuestionsAreClosed'] = True
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))

        assert "/question-and-answer-session" not in res.get_data(as_text=True)

    def test_dos_brief_question_and_answer_session_details_hidden_when_empty(self):
        del self.brief['briefs']['questionAndAnswerSessionDetails']
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))

        assert "/question-and-answer-session" not in res.get_data(as_text=True)

    def test_dos_brief_has_questions_and_answers(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        xpath = '//h2[@id="clarification-questions"]/following-sibling::table/tbody/tr'
        clarification_questions = document.xpath(xpath)

        number = clarification_questions[0].xpath('td[1]/span/span/text()')[0].strip()
        question = clarification_questions[0].xpath('td[1]/span/text()')[0].strip()
        answer = clarification_questions[0].xpath('td[2]/span/text()')[0].strip()
        qa_link_text = document.xpath('//a[@href="/suppliers/opportunities/{}/ask-a-question"]/text()'
                                      .format(brief_id))[0].strip()

        assert_equal(number, "1.")
        assert_equal(question, "Why?")
        assert_equal(answer, "Because")
        assert_equal(qa_link_text, "Log in to ask a question")

    def test_dos_brief_has_different_link_text_for_logged_in_supplier(self):
        self.login_as_supplier()
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        qa_link_text = document.xpath('//a[@href="/suppliers/opportunities/{}/ask-a-question"]/text()'
                                      .format(brief_id))[0]

        assert_equal(qa_link_text.strip(), "Ask a question")

    def test_can_apply_to_live_brief(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        apply_links = document.xpath('//a[@href="/suppliers/opportunities/{}/responses/create"]'.format(brief_id))
        assert len(apply_links) == 1

    def test_cannot_apply_to_closed_brief(self):
        brief = self.brief.copy()
        brief['briefs']['status'] = "closed"
        brief['briefs']['publishedAt'] = "2000-01-25T12:00:00.000000Z"
        brief['briefs']['applicationsClosedAt'] = "2000-02-25T12:00:00.000000Z"
        self._data_api_client.get_brief.return_value = brief
        brief_id = brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        apply_links = document.xpath('//a[@href="/suppliers/opportunities/{}/responses/create"]'.format(brief_id))
        assert len(apply_links) == 0
        assert '25 February 2000' in document.xpath('//p[@class="banner-message"]')[0].text_content()

    def test_dos_brief_specialist_role_displays_label(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))

        assert 'qualityAssurance' not in res.get_data(as_text=True)
        assert 'Quality assurance analyst' in res.get_data(as_text=True)


class TestCatalogueOfBriefsPage(BaseApplicationTest):
    def setup(self):
        super(TestCatalogueOfBriefsPage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.views.marketplace.data_api_client'
        ).start()

        self.briefs = self._get_dos_brief_fixture_data(multi=True)
        self._data_api_client.find_briefs.return_value = self.briefs

    def teardown(self):
        self._data_api_client.stop()

    def test_catalogue_of_briefs_page(self):
        self._data_api_client.get_framework.return_value = {'frameworks': {
            'name': "Digital Outcomes and Specialists",
            'lots': [
                {'name': 'Lot 1', 'allowsBrief': True},
                {'name': 'Lot 2', 'allowsBrief': False},
                {'name': 'Lot 3', 'allowsBrief': True}
            ]
        }}
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        heading = document.xpath('//h1/text()')[0].strip()
        assert heading == "Digital Outcomes and Specialists opportunities"
        assert 'lot 1, lot 3' in document.xpath('//div[@class="marketplace-paragraph"]/p/text()')[0]

    def test_catalogue_of_briefs_page_shows_pagination_if_more_pages(self):
        res = self.client.get('/digital-outcomes-and-specialists/opportunities')
        assert_equal(200, res.status_code)
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
        assert_equal(200, res.status_code)
        page = res.get_data(as_text=True)

        assert '<li class="previous">' not in page
        assert '<li class="next">' not in page

    def test_catalogue_of_briefs_page_404_for_framework_that_does_not_exist(self):
        self._data_api_client.get_framework.return_value = {'frameworks': {}}
        res = self.client.get('/digital-giraffes-and-monkeys/opportunities')

        assert_equal(404, res.status_code)
        self._data_api_client.get_framework.assert_called_once_with('digital-giraffes-and-monkeys')
