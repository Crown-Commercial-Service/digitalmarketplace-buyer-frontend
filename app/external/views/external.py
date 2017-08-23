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


@external.route('/user/login')
def render_login():
    raise NotImplementedError()


@external.route('/user/logout')
def logout():
    raise NotImplementedError()
