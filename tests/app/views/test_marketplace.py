# coding=utf-8

import mock
from nose.tools import assert_equal, assert_true, assert_in
from lxml import html
from ...helpers import BaseApplicationTest
from dmapiclient import APIError
import pytest


class TestApplication(BaseApplicationTest):
    def setup(self):
        super(TestApplication, self).setup()

    def test_analytics_code_should_be_in_javascript(self):
        res = self.client.get(self.expand_path('/static/javascripts/application.js'))
        assert_equal(200, res.status_code)
        assert_true(
            'trackPageview'
            in res.get_data(as_text=True))


class TestHomepageBrowseList(BaseApplicationTest):
    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_homepage_headers(self, data_api_client):
        res = self.client.get(self.expand_path('/'))
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        headers = [
            item.text_content().strip() for item in document.cssselect('article#content h2')
        ]

        assert headers == [
            'Government buyers',
            'Sellers',
            'Learn more',
        ]


class TestStaticMarketplacePages(BaseApplicationTest):
    def setup(self):
        super(TestStaticMarketplacePages, self).setup()

    def test_cookie_page(self):
        res = self.client.get(self.expand_path('/cookies'))
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>Cookies</h1>'
            in self._strip_whitespace(res.get_data(as_text=True))
        )

    def test_cookie_page(self):
        res = self.client.get(self.expand_path('/terms-and-conditions'))
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>Termsandconditions</h1>'
            in self._strip_whitespace(res.get_data(as_text=True))
        )


@pytest.mark.skip(reason='Briefs not in Australian version')
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


@pytest.mark.skip(reason='Briefs not in Australian version')
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
        assert 'lot 1 and lot 3' in document.xpath('//div[@class="marketplace-paragraph"]/p/text()')[0]

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
