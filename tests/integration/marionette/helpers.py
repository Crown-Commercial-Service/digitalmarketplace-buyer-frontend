from config import config


def go_home(client):
    client.navigate(config['DM_FRONTEND_URL'])
