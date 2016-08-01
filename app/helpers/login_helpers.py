from flask_login import current_user
from flask import current_app, redirect, render_template, Response, url_for


def is_authenticated_workaround(user):
    # A breaking API change was made in Flask Login that makes is_authenticated into a property instead of a method.
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


def render_template_with_csrf(template_name, status_code=200, **kwargs):
    response = Response(render_template(template_name, **kwargs))

    # CSRF tokens are user-specific, even if the user isn't logged in
    response.cache_control.private = True

    max_age = current_app.config['DM_DEFAULT_CACHE_MAX_AGE']
    max_age = min(max_age, current_app.config.get('CSRF_TIME_LIMIT', max_age))
    response.cache_control.max_age = max_age

    return response, status_code
