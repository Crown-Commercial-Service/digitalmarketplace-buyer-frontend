from flask import Blueprint

external = Blueprint('external', __name__)


@external.route('/buyers')
def buyer_dashboard():
    raise NotImplementedError()


@external.route('/buyers/create')
def create_buyer_account():
    raise NotImplementedError()


@external.route('/buyers/create')
def submit_create_buyer_account():
    raise NotImplementedError()


@external.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>')
def info_page_for_starting_a_brief(framework_slug, lot_slug):
    raise NotImplementedError()


@external.route('/buyers/frameworks/<framework_slug>/requirements/user-research-studios')
def studios_start_page(framework_slug):
    raise NotImplementedError()


@external.route('/suppliers/opportunities/<brief_id>/responses/start')
def start_brief_response(brief_id):
    raise NotImplementedError()


@external.route('/suppliers/opportunities/<brief_id>/responses/result')
def brief_response_result(brief_id):
    raise NotImplementedError()
