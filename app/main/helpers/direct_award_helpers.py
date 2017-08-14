def is_direct_award_project_accessible(project, user_id):
    return any([user['id'] == user_id for user in project['users']])
