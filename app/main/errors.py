# coding=utf-8
from dmapiclient import APIError
from dmutils.errors import render_error_page

from . import main


@main.app_errorhandler(APIError)
def api_error_handler(e):
    return render_error_page(e.status_code)


@main.app_errorhandler(410)
def page_gone(e):
    # TODO: handle 410 errors in dmutils.flask_init
    return render_error_page(410)


@main.app_errorhandler(500)
def service_unavailable(e):
    # Add error message to template context for 500s
    return render_error_page(500, error_message=e.response)
