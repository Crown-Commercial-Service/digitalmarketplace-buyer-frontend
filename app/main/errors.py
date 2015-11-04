# coding=utf-8

from flask import render_template, current_app, request
from . import main
from ..helpers.search_helpers import get_template_data
from dmutils.apiclient import APIError


@main.app_errorhandler(APIError)
def api_error_handler(e):
    return _render_error_page(e.status_code)


@main.app_errorhandler(404)
def page_not_found(e):
    return _render_error_page(404)


@main.app_errorhandler(410)
def page_gone(e):
    return _render_error_page(410)


@main.app_errorhandler(500)
def page_not_found(e):
    return _render_error_page(500)


def _render_error_page(status_code):
    templates = {
        404: "errors/404.html",
        410: "errors/410.html",
        500: "errors/500.html",
        503: "errors/500.html",
    }
    if status_code not in templates:
        status_code = 500
    template_data = get_template_data(main, {})

    return render_template(templates[status_code], **template_data), status_code
