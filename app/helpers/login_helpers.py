from flask_login import current_user
from flask import redirect, url_for, current_app


def is_authenticated_workaround(user):
    # A breaking API change was made in Flask Login that makes a is_authenticated into a property, instead of a method.
    # FIXME: migrate dmutils to the new API and remove this workaround
    v = user.is_authenticated
    if type(v) is bool:
        return v
    return v()


def redirect_logged_in_user(next_url=None):
    site_url_prefix = current_app.config['URL_PREFIX']
    if is_authenticated_workaround(current_user):
        if next_url and next_url.startswith(site_url_prefix):
            return redirect(next_url)
        else:
            return redirect(url_for('.supplier_search'))

    return redirect(url_for('.index'))
