def get_latest_live_framework(all_frameworks, framework_type):
    try:
        latest = max(
            (f for f in all_frameworks if f['status'] == 'live' and f['framework'] == framework_type),
            key=lambda f: f['id'],
        )
        return latest
    except ValueError:  # max of empty iterable
        return None
