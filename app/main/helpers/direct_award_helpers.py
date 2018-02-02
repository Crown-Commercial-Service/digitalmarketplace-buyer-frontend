from operator import itemgetter

from app import data_api_client


def is_direct_award_project_accessible(project, user_id):
    return any([user['id'] == user_id for user in project['users']])


def get_direct_award_projects(user_id, return_type="all", sort_by_key=None, latest_first=None):
    projects = data_api_client.find_direct_award_projects(user_id, latest_first=latest_first).get('projects', [])

    res = {
        "open_projects": [],
        "closed_projects": [],
    }

    for project in projects:
        if project['lockedAt'] is None:
            res['open_projects'].append(project)
        else:
            res['closed_projects'].append(project)

    if return_type == "all":
        if sort_by_key:
            res['open_projects'].sort(key=itemgetter(sort_by_key))
            res['closed_projects'].sort(key=itemgetter(sort_by_key))

        return res
    else:
        if sort_by_key:
            res[return_type].sort(key=itemgetter(sort_by_key))
        return res[return_type]
