# coding=utf-8
from dmapiclient import APIError
from dmcontent.content_loader import QuestionNotFoundError
from dmutils.errors import render_error_page


from . import main


@main.app_errorhandler(APIError)
def api_error_handler(e):
    return render_error_page(status_code=e.status_code)


@main.app_errorhandler(QuestionNotFoundError)
def content_loader_error_handler(e):
    return render_error_page(status_code=400)
