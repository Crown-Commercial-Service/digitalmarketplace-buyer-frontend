# coding=utf-8

from flask import render_template
from . import main
from dmapiclient import APIError


@main.app_errorhandler(APIError)
def api_error_handler(e):
    return _render_error_page(e.status_code)


@main.app_errorhandler(404)
def page_not_found(e):
    return _render_error_page(404)


@main.app_errorhandler(500)
def internal_server_error(e):
    return _render_error_page(500)


@main.app_errorhandler(503)
def service_unavailable(e):
    return _render_error_page(503, e.response)


def _render_error_page(status_code, error_message=None):
    templates = {
        404: "errors/404.html",
        500: "errors/500.html",
        503: "errors/500.html",
    }
    if status_code not in templates:
        status_code = 500

    return render_template(templates[status_code],
                           error_message=error_message,
                           **dict(main.config['BASE_TEMPLATE_DATA'])), status_code
