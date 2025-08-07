# src/bale_bot/config.py
import configparser
import os

config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini')

config = configparser.ConfigParser()
config.read(config_path)

def get_bot_token():
    return config.get('bale_bot', 'token')

def get_admin_id():
    try:
        return int(config.get('developer', 'admin_id'))
    except (configparser.NoOptionError, ValueError):
        return None
