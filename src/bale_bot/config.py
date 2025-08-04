import configparser
import os

# مسیر فایل کانفیگ را به صورت داینامیک پیدا می‌کند
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini')

config = configparser.ConfigParser()
config.read(config_path)

def get_bot_token():
    """توکن ربات را از فایل کانفیگ می‌خواند."""
    return config.get('bale_bot', 'token')

def get_admin_id():
    """شناسه ادمین را برای ارسال گزارش‌ها می‌خواند."""
    try:
        return int(config.get('developer', 'admin_id'))
    except (configparser.NoOptionError, ValueError):
        return None