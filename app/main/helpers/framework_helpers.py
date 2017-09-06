from ... import content_loader


def get_frameworks_by_slug(data_api_client):
    return {framework['slug']: framework for framework in data_api_client.find_frameworks().get('frameworks')}


def get_latest_live_framework(all_frameworks, framework_type):
    try:
        latest = max(
            (f for f in all_frameworks if f['status'] == 'live' and f['framework'] == framework_type),
            key=lambda f: f['id'],
        )
        return latest
    except ValueError:  # max of empty iterable
        return None


def get_lots_by_slug(framework_data):
    return {lot['slug']: lot for lot in framework_data['lots']}


def get_framework_description(data_api_client, framework_family):
    frameworks = data_api_client.find_frameworks().get('frameworks')
    framework = get_latest_live_framework(frameworks, framework_family)
    if framework is None:
        return ''

    content_loader.load_messages(framework['slug'], ['descriptions'])

    return content_loader.get_message(framework['slug'], 'descriptions', 'framework')
