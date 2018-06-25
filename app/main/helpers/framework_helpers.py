from flask import abort

from dmapiclient import HTTPError

from ... import content_loader


def get_frameworks_by_slug(data_api_client):
    return {framework['slug']: framework for framework in data_api_client.find_frameworks().get('frameworks')}


def get_latest_live_framework(all_frameworks, framework_family):
    try:
        latest = max(
            (f for f in all_frameworks if f['status'] == 'live' and f['framework'] == framework_family),
            key=lambda f: f['id'],
        )
        return latest
    except ValueError:  # max of empty iterable
        return None


def get_latest_live_framework_or_404(all_frameworks, framework_family):
    latest_live_framework = get_latest_live_framework(all_frameworks, framework_family)

    if not latest_live_framework:
        abort(404, f"No latest framework found for `{framework_family}` family")

    return latest_live_framework


def get_lots_by_slug(framework_data):
    return {lot['slug']: lot for lot in framework_data['lots']}


def get_framework_description(data_api_client, framework_family):
    frameworks = data_api_client.find_frameworks().get('frameworks')
    framework = get_latest_live_framework(frameworks, framework_family)
    if framework is None:
        return ''

    content_loader.load_messages(framework['slug'], ['descriptions'])

    return content_loader.get_message(framework['slug'], 'descriptions', 'framework')


def abort_if_not_further_competition_framework(framework):
    if not framework['hasFurtherCompetition']:
        abort(404, f"Framework `{framework}` does not support further competition.")


def get_framework_or_500(client, framework_slug, logger=None):
    """Return a 500 if a framework is not found that we explicitly expect to be there"""
    try:
        return client.get_framework(framework_slug)['frameworks']
    except HTTPError as e:
        if e.status_code == 404:
            if logger:
                logger.error(
                    "Framework not found. Error: {error}, framework_slug: {framework_slug}",
                    extra={'error': str(e), 'framework_slug': framework_slug}
                )
            abort(500, f'Framework not found: {framework_slug}')
        else:
            raise
