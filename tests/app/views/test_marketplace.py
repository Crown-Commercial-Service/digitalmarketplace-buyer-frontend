# coding=utf-8
from flask.helpers import url_for

from datetime import datetime
from lxml import html
import pytest
import mock
from nose.tools import assert_equal, assert_true, assert_in
from six import iteritems
from six.moves.urllib.parse import urlparse, parse_qs

from ...helpers import BaseApplicationTest

from dmapiclient import APIError
from dmutils.formats import DATETIME_FORMAT


@pytest.mark.skipif(True, reason="not applicable to AU")
class TestHomepageAccountCreationVirtualPageViews(BaseApplicationTest):
    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_data_analytics_track_page_view_is_shown_if_account_created_flag_flash_message(self, data_api_client):
        with self.client.session_transaction() as session:
            session['_flashes'] = [('flag', 'account-created')]

        res = self.client.get("/")
        data = res.get_data(as_text=True)

        assert 'data-analytics="trackPageView" data-url="/vpv/?account-created=true"' in data

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_data_analytics_track_page_view_not_shown_if_no_account_created_flag_flash_message(self, data_api_client):
        res = self.client.get("/")
        data = res.get_data(as_text=True)

        assert 'data-analytics="trackPageView" data-url="/vpv/?account-created=true"' not in data


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
            'Buyers',
            'Sellers'
        ]

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_dashboard(self, data_api_client):
        data_api_client.get_buyers_count.return_value = {
            "buyers": {
                "total": 1
            }
        }

        data_api_client.get_suppliers_count.return_value = {
            "suppliers": {
                "total": 16
            }
        }

        data_api_client.get_briefs_count.return_value = {
            "briefs": {
                "total": 8,
                "open_to_all": 7,
                "open_to_one": 0,
                "open_to_selected": 1,
                "recent_brief_time_since": "26 minutes ago"
            }
        }

        res = self.client.get(self.expand_path('/'))
        assert_equal(200, res.status_code)

        data_api_client.get_buyers_count.asssert_called_once()
        data_api_client.get_suppliers_count.asssert_called_once()
        data_api_client.get_briefs_count.asssert_called_once()


class TestStaticMarketplacePages(BaseApplicationTest):
    def setup(self):
        super(TestStaticMarketplacePages, self).setup()
        self.terms_manager.load_versions(self.app)

    def test_toc_page(self):
        res = self.client.get(self.expand_path('/terms-of-use'))
        assert_equal(200, res.status_code)
        assert_true(
            'TermsofUse'
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
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}').format(brief_id))
        assert_equal(404, res.status_code)

    def test_dos_brief_has_correct_title(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}').format(brief_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        self._assert_page_title(document)

    def test_dos_brief_pdf(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/opportunity_{}.pdf')
                              .format(brief_id))
        assert_equal(200, res.status_code)
        assert_equal(res.mimetype, 'application/pdf')

    @pytest.mark.skipif(True, reason="test failing on AU CI server")
    def test_dos_brief_has_important_dates(self):
        brief_id = self.brief['briefs']['id']
        self.brief['briefs']['clarificationQuestionsClosedAt'] = "2016-03-10T11:08:28.054129Z"
        self.brief['briefs']['applicationsClosedAt'] = "2016-03-11T11:08:28.054129Z"
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}').format(brief_id))
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
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}').format(brief_id))
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
        assert_equal(start_date_key[0], 'What is the latest start date?')
        assert_equal(start_date_value[0], '01/03/2016')
        assert_equal(contract_length_key[0], 'How long is the contract?')
        assert_equal(contract_length_value[0], '4 weeks')

    def test_dos_brief_has_question_and_answer_session_details_link(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}').format(brief_id))

        document = html.fromstring(res.get_data(as_text=True))
        qa_session_url = self.expand_path('/sellers/opportunities/{}/question-and-answer-session'.format(brief_id))
        qa_session_link_text = document.xpath('//a[@href="{}"]/text()'.format(qa_session_url))[0].strip()

        assert qa_session_link_text == "Sign in to view question and answer session details"

    def test_dos_brief_question_and_answer_session_details_hidden_when_questions_closed(self):
        closed_timestamp = datetime.strftime(datetime(2015, 1, 1), DATETIME_FORMAT)
        self.brief['briefs']['clarificationQuestionsAreClosed'] = True
        self.brief['briefs']['clarificationQuestionsClosedAt'] = closed_timestamp
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{})'.format(brief_id)))

        assert "/question-and-answer-session" not in res.get_data(as_text=True)

    def test_dos_brief_question_and_answer_session_details_hidden_when_empty(self):
        del self.brief['briefs']['questionAndAnswerSessionDetails']
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))

        assert "/question-and-answer-session" not in res.get_data(as_text=True)

    def test_dos_brief_has_questions_and_answers(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        xpath = '//h2[@id="clarification-questions"]/following-sibling::table/tbody/tr'
        clarification_questions = document.xpath(xpath)

        number = clarification_questions[0].xpath('td[1]/span/span/text()')[0].strip()
        question = clarification_questions[0].xpath('td[1]/span/text()')[0].strip()
        answer = clarification_questions[0].xpath('td[2]/span/text()')[0].strip()
        qa_url = self.expand_path('/sellers/opportunities/{}/ask-a-question'.format(brief_id))
        qa_link_text = document.xpath('//a[@href="{}"]/text()'.format(qa_url))[0].strip()

        assert_equal(number, "1.")
        assert_equal(question, "Why?")
        assert_equal(answer, "Because")
        assert_equal(qa_link_text, "Sign in to ask a question")

    def test_dos_brief_has_different_link_text_for_logged_in_supplier(self):
        self.login_as_supplier()
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        qa_url = self.expand_path('/sellers/opportunities/{}/ask-a-question'.format(brief_id))
        qa_link_text = document.xpath('//a[@href="{}"]/text()'.format(qa_url))[0]

        assert_equal(qa_link_text.strip(), "Ask a question")

    def test_can_apply_to_live_brief(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        brief_response_url = self.expand_path('/sellers/opportunities/{}/responses/create'.format(brief_id))
        apply_links = document.xpath('//a[@href="{}"]'.format(brief_response_url))
        assert len(apply_links) == 2

    def test_cannot_apply_to_closed_brief(self):
        brief = self.brief.copy()
        brief['briefs']['status'] = "closed"
        brief['briefs']['publishedAt'] = "2000-01-25T12:00:00.000000Z"
        brief['briefs']['applicationsClosedAt'] = "2000-02-25T12:00:00.000000Z"
        self._data_api_client.get_brief.return_value = brief
        brief_id = brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        brief_response_url = self.expand_path('/sellers/opportunities/{}/responses/create'.format(brief_id))
        apply_links = document.xpath('//a[@href="{}"]'.format(brief_response_url))
        assert len(apply_links) == 0
        assert '25 February 2000' in document.xpath('//div[@class="callout--info"]')[0][1].text_content()

    def test_dos_brief_specialist_role_displays_label(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))

        assert 'agileCoach' not in res.get_data(as_text=True)
        assert 'Agile Coach' in res.get_data(as_text=True)

    def _assert_view_application(self, document, brief_id):
        assert len(document.xpath(
            '//a[@href="{0}"][contains(normalize-space(text()), normalize-space("{1}"))]'.format(
                self.expand_path('/sellers/opportunities/{}/responses/result'.format(brief_id)),
                "View your application",
            )
        )) == 1

    def test_unauthenticated_start_application(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        brief_response_url = self.expand_path('/sellers/opportunities/{}/responses/create'.format(brief_id))
        assert len(document.xpath(
            '//a[@href="{0}"][contains(normalize-space(text()), normalize-space("{1}"))]'.format(
                brief_response_url,
                "Apply Now",
            )
        )) == 1

    def test_buyer_start_application(self):
        self.login_as_buyer()
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        brief_response_url = self.expand_path('/sellers/opportunities/{}/responses/create'.format(brief_id))
        assert len(document.xpath(
            '//a[@href="{0}"][contains(normalize-space(text()), normalize-space("{1}"))]'.format(
                brief_response_url,
                "Apply Now",
            )
        )) == 1

    def test_supplier_start_application(self):
        self.login_as_supplier()
        # mocking that we haven't applied
        self._data_api_client.find_brief_responses.return_value = {
            "briefResponses": [],
        }
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        brief_response_url = self.expand_path('/sellers/opportunities/{}/responses/create'.format(brief_id))
        assert len(document.xpath(
            '//a[@href="{0}"][contains(normalize-space(text()), normalize-space("{1}"))]'.format(
                brief_response_url,
                "Apply Now",
            )
        )) == 1

    def test_supplier_applied_view_application(self):
        self.login_as_supplier()
        # mocking that we have applied
        self._data_api_client.find_brief_responses.return_value = {
            "briefResponses": [{"lazy": "mock"}],
        }
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        self._assert_view_application(document, brief_id)


class TestCatalogueOfBriefsPage(BaseApplicationTest):
    def setup(self):
        super(TestCatalogueOfBriefsPage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.views.marketplace.data_api_client'
        ).start()

        self.briefs = self._get_dos_brief_fixture_data(multi=True)
        self._data_api_client.find_briefs.return_value = self.briefs

        self._data_api_client.get_framework.return_value = {'frameworks': {
            'name': "Digital Service Professionals",
            'slug': "digital-service-professionals",
            'lots': [
                {'name': 'Lot 1', 'slug': 'lot-one', 'allowsBrief': True},
                {'name': 'Lot 2', 'slug': 'lot-two', 'allowsBrief': False},
                {'name': 'Lot 3', 'slug': 'lot-three', 'allowsBrief': True},
                {'name': 'Lot 4', 'slug': 'lot-four', 'allowsBrief': True},
            ]
        }}

    def teardown(self):
        self._data_api_client.stop()

    def test_catalogue_of_briefs_page(self):
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities'))
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        self._data_api_client.get_framework.assert_called_once_with("digital-service-professionals")
        regular_args = {
            k: v for k, v in iteritems(self._data_api_client.find_briefs.call_args[1]) if k not in ("status", "lot",)
        }
        assert regular_args == {
            "framework": "digital-service-professionals",
            "page": 1,
            "human": True,
            "per_page": 500
        }
        assert set(self._data_api_client.find_briefs.call_args[1]["status"].split(",")) == {"live", "closed"}
        assert set(self._data_api_client.find_briefs.call_args[1]["lot"].split(",")) == {
            "lot-one",
            "lot-three",
            "lot-four",
        }

        heading = document.xpath('normalize-space(//h1/text())')
        assert heading == "Latest opportunities"
        # to-do: fix this test
        # assert 'lot 1, lot 3 and lot 4' in document.xpath(
        #     "normalize-space(//div[@class='marketplace-paragraph']/p/text())"
        # )

        ss_elem = document.xpath("//p[@class='search-summary']")[0]
        assert self._normalize_whitespace(self._squashed_element_text(ss_elem)) == "%s opportunities" % \
                                                                                   self.briefs['meta']['total']

    def test_catalogue_of_briefs_page_filtered(self):
        with self.app.app_context():
            original_url = url_for('main.list_opportunities', framework_slug='digital-service-professionals') + \
                "?page=2&status=live&lot=lot-one&lot=lot-three"

        res = self.client.get(original_url)
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        self._data_api_client.get_framework.assert_called_once_with("digital-service-professionals")
        regular_args = {
            k: v for k, v in iteritems(self._data_api_client.find_briefs.call_args[1]) if k not in ("status", "lot",)
        }
        assert regular_args == {
            "framework": "digital-service-professionals",
            "page": 2,
            "human": True,
            "per_page": 500
        }
        assert set(self._data_api_client.find_briefs.call_args[1]["status"].split(",")) == {"live"}
        assert set(self._data_api_client.find_briefs.call_args[1]["lot"].split(",")) == {"lot-one", "lot-three"}

        heading = document.xpath('normalize-space(//h1/text())')
        assert heading == "Latest opportunities"
        # to-do: fix this test
        # assert 'lot 1, lot 3 and lot 4' in document.xpath(
        #     "normalize-space(//div[@class='marketplace-paragraph']/p/text())"
        # )

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
        assert (parsed_original_url.path == parsed_prev_url.path == parsed_next_url.path) or \
            '' == parsed_prev_url.path == parsed_next_url.path

        def normalize_qs(qs):
            return {
                k: set(v) for k, v
                in iteritems(parse_qs(qs))
                if k != "page"
            }

        assert normalize_qs(parsed_original_url.query) == \
            normalize_qs(parsed_next_url.query) == \
            normalize_qs(parsed_prev_url.query)

        ss_elem = document.xpath("//p[@class='search-summary']")[0]
        assert self._normalize_whitespace(self._squashed_element_text(ss_elem)) == "3 results"

    def test_catalogue_of_briefs_page_filtered_all_options_selected(self):
        with self.app.app_context():
            original_url = url_for('main.list_opportunities', framework_slug='digital-service-professionals') + \
                "?page=2&status=live&lot=lot-one&lot=lot-three&status=closed&lot=lot-four"

        res = self.client.get(original_url)
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        self._data_api_client.get_framework.assert_called_once_with("digital-service-professionals")
        regular_args = {
            k: v for k, v in iteritems(self._data_api_client.find_briefs.call_args[1]) if k not in ("status", "lot",)
        }
        assert regular_args == {
            "framework": "digital-service-professionals",
            "page": 2,
            "human": True,
            "per_page": 500
        }
        assert set(self._data_api_client.find_briefs.call_args[1]["status"].split(",")) == {"live", "closed"}
        assert set(self._data_api_client.find_briefs.call_args[1]["lot"].split(",")) == {
            "lot-one",
            "lot-three",
            "lot-four",
        }

        heading = document.xpath('normalize-space(//h1/text())')
        assert heading == "Latest opportunities"
        # to-do: fix this test
        # assert 'lot 1, lot 3 and lot 4' in document.xpath(
        #     "normalize-space(//div[@class='marketplace-paragraph']/p/text())"
        # )

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
        parsed_prev_url = urlparse(document.xpath("//li[@class='previous']/a/@href")[0])

        def normalize_qs(qs):
            return {k: set(v) for k, v in iteritems(parse_qs(qs)) if k != "page"}

        assert normalize_qs(parsed_original_url.query) == normalize_qs(parsed_prev_url.query) == \
            normalize_qs(parsed_next_url.query)

        ss_elem = document.xpath("//p[@class='search-summary']")[0]
        assert self._normalize_whitespace(self._squashed_element_text(ss_elem)) == "3 results"

    def test_catalogue_of_briefs_page_loads_as_buyer(self):
        self.login_as_buyer()
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities'))
        assert_equal(200, res.status_code)

    def test_catalogue_of_briefs_400_if_invalid_status(self):
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities'
                                               '?status=pining-for-fjords'))
        assert res.status_code == 400

    def test_catalogue_of_briefs_page_shows_pagination_if_more_pages(self):
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities?page=2'))
        assert_equal(200, res.status_code)
        page = res.get_data(as_text=True)
        document = html.fromstring(page)

        assert '<li class="previous">' in page
        assert '<li class="next">' in page
        prev_url = str(document.xpath('string(//li[@class="previous"]/a/@href)'))
        next_url = str(document.xpath('string(//li[@class="next"]/a/@href)'))
        assert prev_url.endswith('?page=1')
        assert next_url.endswith('?page=3')

    def test_no_pagination_if_no_more_pages(self):
        self.briefs['meta']['per_page'] = self.briefs['meta']['total']

        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities'))
        assert_equal(200, res.status_code)
        page = res.get_data(as_text=True)

        assert '<li class="previous">' not in page
        assert '<li class="next">' not in page

    def test_catalogue_of_briefs_page_404_for_framework_that_does_not_exist(self):
        self._data_api_client.get_framework.return_value = {'frameworks': {}}
        res = self.client.get(self.expand_path('/digital-giraffes-and-monkeys/opportunities'))

        assert_equal(404, res.status_code)
        self._data_api_client.get_framework.assert_called_once_with('digital-giraffes-and-monkeys')
