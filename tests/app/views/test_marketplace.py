# coding=utf-8

from datetime import datetime
from lxml import html
import pytest
import mock
from nose.tools import assert_equal, assert_true, assert_not_equals
from six import iteritems

from ...helpers import BaseApplicationTest

from dmapiclient import api_stubs
from dmutils.formats import DATETIME_FORMAT
import pendulum


class TestHomepageBrowseList(BaseApplicationTest):
    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_show_start_brief_info_page(self, data_api_client):
        with self.app.app_context():
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-service-professionals',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-professionals', allows_brief=True),
                ]
            )

            res = self.client.get(
                self.expand_path(
                    "/buyers/frameworks/digital-service-professionals/requirements/digital-professionals"
                ))
            assert res.status_code == 200
            document = html.fromstring(res.get_data(as_text=True))
            assert document.xpath('//h1')[0].text_content().strip() == "Hire a digital specialist"

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_homepage_headers(self, data_api_client):
        res = self.client.get(self.expand_path('/'))
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 200

        headers = [
            item.text_content().strip() for item in document.cssselect('article#content h2')
        ]

        assert headers == [
            'Using the Marketplace',
            'More panels and arrangements'
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

    def test_dos_brief_has_response_preview(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}/response')
                              .format(brief_id))
        assert_equal(200, res.status_code)

    def test_dos_brief_has_correct_title(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}').format(brief_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        self._assert_page_title(document)

    def test_dos_brief_has_at_least_one_section(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}').format(brief_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        section_heading = document.xpath('//h2[@class="summary-item-heading"]')[0]
        section_attributes = section_heading.xpath('following-sibling::dl')

        start_date_key = section_attributes[0].xpath('dt/td/span/text()')[2]
        start_date_value = section_attributes[0].xpath('dd/td/span/text()')[2]

        contract_length_key = section_attributes[0].xpath('dt/td/span/text()')[3]
        contract_length_value = section_attributes[0].xpath('dd/td/span/text()')[3]

        assert_equal(section_heading.get('id'), 'opportunity-attributes-1')
        assert_equal(section_heading.text.strip(), 'Overview')
        assert_equal(start_date_key, 'What is the latest start date?')
        assert_equal(start_date_value, '01/03/2016')
        assert_equal(contract_length_key, 'How long is the contract?')
        assert_equal(contract_length_value, '4 weeks')

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

    def test_cannot_apply_to_closed_brief(self):
        self.login_as_supplier()
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
        assert '25 February 2000' in document.xpath('//div[@class="callout--info"]//p')[1].text

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

    @pytest.mark.skip
    def test_unauthenticated_start_application(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))
        assert_equal(200, res.status_code)
        document = html.fromstring(res.get_data(as_text=True))

        brief_response_url = self.expand_path('/sellers/opportunities/{}/responses/create'.format(brief_id))
        assert_equal(document.xpath('//a')[10].text, "Sign in to continue")
        assert_equal(
            document.xpath('//a')[10].values()[1],
            "/login?next=/digital-service-professionals/opportunities/{}".format(brief_id)
        )

    def test_buyer_start_application(self):
        self.login_as_buyer()
        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))
        assert_equal(200, res.status_code)
        assert_not_equals(res.data.title().strip().find("/Sellers/Opportunities/1/Ask-A-Question"), -1)

    def test_supplier_start_application(self):
        self.login_as_supplier()
        # mocking that we haven't applied
        self._data_api_client.find_brief_responses.return_value = {
            "briefResponses": [],
        }

        brief_id = self.brief['briefs']['id']
        res = self.client.get(self.expand_path('/digital-service-professionals/opportunities/{}'.format(brief_id)))
        assert_equal(200, res.status_code)

        assert_not_equals(res.data.title().strip().find("/Sellers/Opportunities/1/Ask-A-Question"), -1)


class TestBriefApplicationScenarios(BaseApplicationTest):
    def setup(self):
        super(TestBriefApplicationScenarios, self).setup()

        self._data_api_client = mock.patch(
            'app.main.views.marketplace.data_api_client'
        ).start()

        self.application = self._get_supplier_application_data()
        self.application['application']['supplier']['domains']['unassessed'] = []
        self.application['application']['supplier']['domains']['assessed'] = []
        self._data_api_client.get_application_by_id.return_value = self.application
        self._data_api_client.req.applications().get.return_value = self.application

        self.supplier = self._get_supplier_fixture2_data()
        self._data_api_client.get_supplier.return_value = self.supplier
        self.supplier['supplier']['products'] = []
        self.supplier['supplier']['is_recruiter'] = 'false'
        self.supplier['supplier']['domains']['legacy'] = []

        self._data_api_client.find_brief_responses.return_value = {'briefResponses': []}
        self.briefs = self._get_dos_brief_fixture_data()
        self._data_api_client.get_brief.return_value = self.briefs
        self.domain_name = {
            'domain': {
                'name': 'A Brief Domain'
            }
        }
        self.brief = self.briefs.get('briefs')
        self.brief['id'] = '1'
        self.brief['areaOfExpertise'] = 'User research and design'
        self.brief["frameworkName"] = "Digital Marketplace"
        self.brief["frameworkSlug"] = "digital-marketplace"
        self.brief["links"] = {
            "framework": "http://localhost:5000/frameworks/digital-marketplace",
        }
        self.brief['status'] = 'live'
        self.brief['lot'] = 'digital-professionals'

    def teardown(self):
        self._data_api_client.stop()

    @pytest.mark.skip
    def test_no_account_no_application(self):
        self.login_as_supplier()

        self.supplier['supplier'] = None
        self._data_api_client.get_supplier.return_value = self.supplier
        self.application['application'] = None
        self._data_api_client.req.applications().get.return_value = self.application

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Update your profile')

        choose_domain_url = document.xpath('//a')[10].get('href')
        assert_equal(choose_domain_url, '/sellers/application')

    @pytest.mark.skip
    def test_submitted_app_outcome(self):
        self.login_as_supplier()

        self.supplier['supplier']['application_id'] = 391
        self.supplier['supplier']['domains']['assessed'] = []
        self.supplier['supplier']['domains']['unassessed'] = []
        self.supplier['supplier']['products'] = []

        self.application['application']['supplier'] = self.supplier['supplier']
        self.application['application']['status'] = 'submitted'

        self.brief['lot'] = 'digital-outcome'

        self._data_api_client.req.applications().get.return_value = self.application

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Request an assessment')

        choose_domain_url = document.xpath('//a')[10].get('href')
        assert_equal(choose_domain_url, "/sellers/opportunities/{}/assessment/status".format(
            self.brief['id']
            )
        )

    @pytest.mark.skip
    def test_submitted_app_dp(self):
        self.login_as_supplier()

        self.supplier['supplier']['domains']['assessed'] = []
        self.supplier['supplier']['domains']['unassessed'] = []
        self.supplier['supplier']['products'] = []

        self.application['application']['supplier'] = self.supplier['supplier']
        self.application['application']['status'] = 'submitted'

        self.brief['lot'] = 'digital-professionals'

        self._data_api_client.req.applications().get.return_value = self.application

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Request an assessment')

        choose_domain_url = document.xpath('//a')[10].get('href')
        assert_equal(choose_domain_url, "/sellers/opportunities/{}/assessment/status".format(
            self.brief['id']
            )
        )

    @pytest.mark.skip
    def test_existing_seller_submitted_app_outcome(self):
        self.login_as_supplier()

        self.supplier['supplier']['application_id'] = 391
        self.supplier['supplier']['domains']['assessed'] = []
        self.supplier['supplier']['domains']['unassessed'] = []
        self.supplier['supplier']['products'] = []
        self.supplier['supplier']['frameworks'] = [{'framework_id': 6}, ]

        self.application['application']['supplier'] = self.supplier['supplier']
        self.application['application']['status'] = 'submitted'

        self.brief['lot'] = 'digital-outcome'

        self._data_api_client.req.applications().get.return_value = self.application

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Update your profile')

        choose_domain_url = document.xpath('//a')[10].get('href')
        assert_equal(choose_domain_url, "/sellers/application")

    @pytest.mark.skip
    def test_existing_seller_submitted_app_dp(self):
        self.login_as_supplier()

        self.supplier['supplier']['application_id'] = 391
        self.supplier['supplier']['domains']['assessed'] = []
        self.supplier['supplier']['domains']['unassessed'] = []
        self.supplier['supplier']['products'] = []
        self.supplier['supplier']['frameworks'] = [{'framework_id': 6}, ]

        self.application['application']['supplier'] = self.supplier['supplier']
        self.application['application']['status'] = 'submitted'

        self.brief['lot'] = 'digital-professionals'

        self._data_api_client.req.applications().get.return_value = self.application

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Update your profile')

        choose_domain_url = document.xpath('//a')[10].get('href')
        assert_equal(choose_domain_url, "/sellers/application")

    @pytest.mark.skip
    def test_has_brief_responses_outcome(self):
        self.login_as_supplier()

        self._data_api_client.find_brief_responses.return_value = {
            'briefResponses': ['firstResponse']
        }
        self.brief['status'] = 'live'
        self.brief['sellerSelector'] = 'not a restricted brief'
        self.brief['lot'] = 'digital-outcome'

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )

        document = html.fromstring(res.get_data(as_text=True))
        assert_equal(
            document.xpath('//a')[10].text, 'View your application'
        )

    @pytest.mark.skip
    def test_has_brief_responses_specialists_view(self):
        self.login_as_supplier()

        self._data_api_client.find_brief_responses.return_value = {
            'briefResponses': ['firstResponse', 'secondResponse', 'thirdResponse']
        }
        self.brief['status'] = 'live'
        self.brief['sellerSelector'] = 'not a restricted brief'
        self.brief['lot'] = 'digital-professionals'

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )

        document = html.fromstring(res.get_data(as_text=True))
        assert_equal(
            document.xpath('//a')[10].text, 'View your application'
        )

    @pytest.mark.skip
    def test_has_brief_responses_specialists_edit(self):
        self.login_as_supplier()

        self._data_api_client.find_brief_responses.return_value = {
            'briefResponses': ['firstResponse']
        }
        self.brief['status'] = 'live'
        self.brief['sellerSelector'] = 'not a restricted brief'
        self.brief['lot'] = 'digital-professionals'
        self.brief['dates']['published_date'] = '1/1/2019'

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )

        document = html.fromstring(res.get_data(as_text=True))
        assert_equal(
            document.xpath('//a')[10].text, 'Edit application'
        )

    @pytest.mark.skip
    def test_aoe_dp_no_casestudies(self):
        self.login_as_supplier()

        self.supplier['supplier']['domains']['assessed'] = []
        self.supplier['supplier']['domains']['unassessed'] = []
        self.supplier['supplier']['products'] = []

        self._data_api_client.get_domain.return_value = self.domain_name
        self._data_api_client.req.assessments().supplier().get.return_value = {
            'unassessed': [],
            'assessed': []
        }

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))
        assert_equal(
            document.xpath('//h2')[9].text, 'Have you got expertise in {}?'.format(
                self.brief['areaOfExpertise']
            )
        )

        brief_scenario_button_text = document.xpath('//a')[11].text
        assert_equal(brief_scenario_button_text, 'Update your profile')

        choose_domain_url = document.xpath('//a')[11].get('href')
        assert_equal(choose_domain_url, '/supplier/{}'.format(
            self.supplier['supplier']['code']
        ))

    @pytest.mark.skip
    def test_products_dp_no_casestudies(self):
        self.login_as_supplier()

        self.supplier['supplier']['domains']['assessed'] = []
        self.supplier['supplier']['domains']['unassessed'] = []
        self.supplier['supplier']['products'] = ['fxx', '458', 'f40' 'California']
        self.supplier['supplier']['services'] = []

        self._data_api_client.get_domain.return_value = self.domain_name
        self._data_api_client.req.assessments().supplier().get.return_value = {
            'unassessed': [],
            'assessed': []
        }

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        assert_equal(
            document.xpath('//h2')[9].text, 'Have you got expertise in {}?'.format(
                self.brief['areaOfExpertise']
            )
        )

        brief_scenario_button_text = document.xpath('//a')[11].text
        assert_equal(brief_scenario_button_text, 'Update your profile')

        choose_domain_url = document.xpath('//a')[11].get('href')
        assert_equal(choose_domain_url, '/supplier/{}'.format(
            self.supplier['supplier']['code']
        ))

    @pytest.mark.skip
    def test_recruiter_dp_no_casestudies(self):
        self.login_as_supplier()

        self.supplier['supplier']['domains']['assessed'] = []
        self.supplier['supplier']['domains']['unassessed'] = []
        self.supplier['supplier']['is_recruiter'] = 'true'
        self.supplier['supplier']['recruiter_info'] = {
            "Cyber security": {
                "active_candidates": "10",
                "database_size": "400",
                "margin": "20",
                "markup": "20",
                "placed_candidates": "2"
            },
        }
        self._data_api_client.get_domain.return_value = self.domain_name
        self._data_api_client.req.assessments().supplier().get.return_value = {
            'unassessed': [],
            'assessed': []
        }

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        assert_equal(
            document.xpath('//h2')[9].text, 'Have you got expertise in {}?'.format(
                self.brief['areaOfExpertise']
            )
        )

        brief_scenario_button_text = document.xpath('//a')[11].text
        assert_equal(brief_scenario_button_text, 'Update your profile')

        choose_domain_url = document.xpath('//a')[11].get('href')
        assert_equal(choose_domain_url, '/supplier/{}'.format(
            self.supplier['supplier']['code']
        ))

    @pytest.mark.skip
    def test_products_outcome_no_casestudies(self):
        self.login_as_supplier()

        self.supplier['supplier']['products'] = ['shift', 'seven', 'axo']
        self.supplier['supplier']['domains']['unassessed'] = []
        self.supplier['supplier']['domains']['assessed'] = []
        self.supplier['supplier']['services'] = []
        self.brief['lot'] = 'digital-outcome'

        self._data_api_client.req.assessments().supplier().get.return_value = {
            'unassessed': [],
            'assessed': []
        }

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))
        assert_equal(document.xpath('//h2')[9].text, 'What services do you offer?')

        brief_scenario_button_text = document.xpath('//a')[11].text
        assert_equal(brief_scenario_button_text, 'Update your profile')

        choose_domain_url = document.xpath('//a')[11].get('href')
        assert_equal(choose_domain_url, '/supplier/{}'.format(self.supplier['supplier']['code']))

    @pytest.mark.skip
    def test_aoe_dp_inreview(self):
        self.login_as_supplier()

        # aoe_seller
        self.supplier['supplier']['domains']['unassessed'] = [self.brief['areaOfExpertise'], ]
        self._data_api_client.get_domain.return_value = self.domain_name
        self._data_api_client.req.assessments().supplier().get.return_value = {
            'unassessed': [self.brief['areaOfExpertise'], ],
            'assessed': []
        }

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Request an assessment')

        choose_domain_url = document.xpath('//a')[10].get('href')
        assert_equal(choose_domain_url, '/sellers/opportunities/1/assessment/status')

    @pytest.mark.skip
    def test_recruiter_dp_inreview(self):
        self.login_as_supplier()

        self.supplier['supplier']['domains']['unassessed'] = [self.brief['areaOfExpertise'], ]
        self.supplier['supplier']['is_recruiter'] = 'true'
        self.supplier['supplier']['recruiter_info'] = {
            "User research and design": {
                "active_candidates": "10",
                "database_size": "400",
                "margin": "20",
                "markup": "20",
                "placed_candidates": "2"
            },
        }
        self._data_api_client.get_domain.return_value = self.domain_name
        self._data_api_client.req.assessments().supplier().get.return_value = {
            'unassessed': [self.brief['areaOfExpertise'], ],
            'assessed': []
        }

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Request an assessment')

        choose_domain_url = document.xpath('//a')[10].get('href')
        assert_equal(choose_domain_url, '/sellers/opportunities/{}/assessment/status'.format(
            self.brief['id']
        ))

    @pytest.mark.skip
    def test_all_outcome_inreview(self):
        self.login_as_supplier()

        self.brief['lot'] = 'digital-outcome'
        self.supplier['supplier']['domains']['assessed'] = []
        self.supplier['supplier']['domains']['unassessed'] = ["Nunchuk skills", ]
        self.supplier['supplier']['products'] = ['this', 'and', 'the other thing']
        self.supplier['supplier']['is_recruiter'] = 'true'
        self._data_api_client.req.assessments().supplier().get.return_value = {
            'unassessed': ["Nunchuk skills", ],
            'assessed': []
        }

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Request an assessment')

        choose_domain_url = document.xpath('//a')[10].get('href')
        assert_equal(choose_domain_url, "/sellers/opportunities/{}/assessment/status".format(
            self.brief['id']
            )
        )

    @pytest.mark.skip
    def test_aeo_professional_not_assessed(self):
        self.login_as_supplier()

        self.supplier['supplier']['domains']['unassessed'] = [self.brief['areaOfExpertise'], ]
        self.supplier['supplier']['domains']['assessed'] = []
        self._data_api_client.req.domain().get.return_value = {"domain": {"id": 1}}
        self._data_api_client.req.assessments().supplier().get.return_value = {
            'unassessed': [],
            'assessed': []
        }

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Request an assessment')

        choose_domain_url = document.xpath('//a')[10].get('href')
        assert_equal(choose_domain_url, "/sellers/opportunities/{}/assessment/1".format(
            self.brief['id']
            )
        )

    @pytest.mark.skip
    def test_recruiter_dp_not_assessed(self):
        self.login_as_supplier()
        self.supplier['supplier']['domains']['assessed'] = []
        self.supplier['supplier']['domains']['unassessed'] = ["User research and design"]
        self.supplier['supplier']['is_recruiter'] = 'true'
        self.supplier['supplier']['recruiter_info'] = {
            "User research and design": {
                "active_candidates": "10",
                "database_size": "400",
                "margin": "20",
                "markup": "20",
                "placed_candidates": "2"
            },
        }
        self._data_api_client.get_domain.return_value = self.domain_name
        self._data_api_client.req.domain().get.return_value = {"domain": {"id": 1}}
        self._data_api_client.req.assessments().supplier().get.return_value = {
            'unassessed': [],
            'assessed': []
        }

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Request an assessment')

        choose_domain_url = document.xpath('//a')[10].get('href')
        assert_equal(choose_domain_url, '/sellers/opportunities/1/assessment/1')

    @pytest.mark.skip
    def test_all_outcome_all_unassessed(self):
        self.login_as_supplier()

        self.supplier['supplier']['domains']['assessed'] = []
        self.supplier['supplier']['domains']['unassessed'] = [self.brief['areaOfExpertise'], ]
        self.supplier['supplier']['products'] = ['burgers', 'pizza', 'crumpets']
        self.supplier['supplier']['is_recruiter'] = 'true'
        self.brief['lot'] = 'digital-outcome'
        self._data_api_client.req.assessments().supplier().get.return_value = {
            'unassessed': [],
            'assessed': []
        }

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Request an assessment')

        choose_domain_url = document.xpath('//a')[10].get('href')
        assert_equal(choose_domain_url, "/sellers/opportunities/{}/assessment/choose".format(
            self.brief['id']
            )
        )

    @pytest.mark.skip
    def test_approved_and_assessed_outcome(self):
        self.login_as_supplier()

        self.supplier['supplier']['domains']['unassessed'] = [self.brief['areaOfExpertise'], ]
        self.supplier['supplier']['products'] = ['burgers', 'pizza', 'crumpets']
        self.supplier['supplier']['is_recruiter'] = 'true'
        self.brief['lot'] = 'digital-outcome'
        self.brief['areaOfExpertise'] = 'User research and design'
        self._data_api_client.req.assessments().supplier().get.return_value = {
            'unassessed': [],
            'assessed': ['Anything', ]
        }

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Apply Now')

        response_create_url = document.xpath('//a')[10].get('href')
        assert_equal(response_create_url, '/2/brief/{}/respond'.format(self.brief['id']))

    @pytest.mark.skip
    def test_approved_and_assessed_dp(self):
        self.login_as_supplier()

        self.supplier['supplier']['domains']['unassessed'] = [self.brief['areaOfExpertise'], ]
        self.supplier['supplier']['products'] = ['burgers', 'pizza', 'crumpets']
        self.supplier['supplier']['is_recruiter'] = 'true'
        self.brief['lot'] = 'digital-professionals'
        self.brief['areaOfExpertise'] = 'User research and design'
        self.brief['dates']['published_date'] = '1/1/2019'
        self._data_api_client.req.assessments().supplier().get.return_value = {
            'unassessed': [],
            'assessed': [self.brief['areaOfExpertise'], ]
        }

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))

        brief_scenario_button_text = document.xpath('//a')[10].text
        assert_equal(brief_scenario_button_text, 'Apply Now')

        response_create_url = document.xpath('//a')[10].get('href')
        assert_equal(response_create_url, '/2/brief/{}/specialist/respond'.format(self.brief['id']))

    def test_one_seller_restricted_brief(self):
        self.login_as_supplier()
        self.brief['sellerSelector'] = 'oneSeller'

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))
        assert_equal(document.xpath(
            '//h3[@id="is_restricted_brief"]')[0].text,
             "Only invited sellers can apply for an 'Open to one' or 'Open to selected'\n"
             "                opportunity."
            )

    def test_some_sellers_restricted_brief(self):
        self.login_as_supplier()
        self.brief['sellerSelector'] = 'someSellers'

        res = self.client.get(
            self.expand_path('/digital-marketplace/opportunities/{}')
                .format(self.brief['id'])
        )
        document = html.fromstring(res.get_data(as_text=True))
        assert_equal(document.xpath(
            '//h3[@id="is_restricted_brief"]')[0].text,
             "Only invited sellers can apply for an 'Open to one' or 'Open to selected'\n"
             "                opportunity."
            )


class TestCatalogueOfBriefsPage(BaseApplicationTest):
    def setup(self):
        pytest.skip('/opportunities has been redirected to /2/opportunities')

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
            "per_page": 75
        }
        assert set(self._data_api_client.find_briefs.call_args[1]["status"].split(",")) == {"live", "closed"}
        assert set(self._data_api_client.find_briefs.call_args[1]["lot"].split(",")) == {
            "lot-one",
            "lot-three",
            "lot-four",
        }

        heading = document.xpath('normalize-space(//h1/text())')
        assert heading == "Opportunities"
        # to-do: fix this test
        # assert 'lot 1, lot 3 and lot 4' in document.xpath(
        #     "normalize-space(//div[@class='marketplace-paragraph']/p/text())"
        # )

        ss_elem = document.xpath("//p[@class='search-summary']")[0]
        assert self._normalize_whitespace(self._squashed_element_text(ss_elem)) == "%s opportunities" % \
                                                                                   self.briefs['meta']['total']

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
