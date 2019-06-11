
from flask import abort
from .. import main


@main.route('/feedback', methods=["POST"])
def send_feedback():
    abort(410)
