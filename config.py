import os
from dotenv import load_dotenv
from pathlib import Path

# Загрузка .env файла
load_dotenv()

# Базовая директория
BASE_DIR = Path(__file__).parent

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_IDS = os.getenv('TELEGRAM_CHAT_IDS', '').split(',')

# Настройки прокси (только для Telegram)
PROXY_USER = os.getenv('PROXY_USER', '')
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD', '')
PROXY_HOST = os.getenv('PROXY_HOST', '')
PROXY_PORT = os.getenv('PROXY_PORT', '')
PROXY_TYPE = os.getenv('PROXY_TYPE', 'socks5')

# Формируем URL прокси для Telegram
if PROXY_HOST and PROXY_PORT:
    if PROXY_USER and PROXY_PASSWORD:
        TELEGRAM_PROXY_URL = f"{PROXY_TYPE}://{PROXY_USER}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
    else:
        TELEGRAM_PROXY_URL = f"{PROXY_TYPE}://{PROXY_HOST}:{PROXY_PORT}"
else:
    TELEGRAM_PROXY_URL = None

# Wialon
WIALON_HOST = os.getenv('WIALON_HOST', 'https://app.wialonlocal.online')
WIALON_TOKEN = os.getenv('WIALON_TOKEN', '')

API_URL = f"{WIALON_HOST}/wialon/ajax.html"

# Папка для данных
DATA_FOLDER = BASE_DIR / "data"

# Настройки для ТО (запасные, если нет данных из JSON)
MAINTENANCE_INTERVAL_KM = int(os.getenv('MAINTENANCE_INTERVAL_KM', 10000))
MAINTENANCE_INTERVAL_HOURS = int(os.getenv('MAINTENANCE_INTERVAL_HOURS', 500))
MAINTENANCE_WARNING_KM = int(os.getenv('MAINTENANCE_WARNING_KM', 1000))
MAINTENANCE_WARNING_HOURS = int(os.getenv('MAINTENANCE_WARNING_HOURS', 50))

CHECK_INTERVAL_HOURS = int(os.getenv('CHECK_INTERVAL_HOURS', 24))