import os
from dotenv import load_dotenv

load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 482981606
BOT_USERNAME = "sessionspamerbot"

# Настройки сессий
SESSIONS_DIR = 'sessions'
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')

# Прокси настройки
PROXY = {
    'proxy_type': 'socks5',  # socks4, socks5, http
    'addr': '221.202.27.194',
    'port': 10807,
    'username': '',
    'password': '',
    'rdns': True
}

USE_PROXY = False  # Включить прокси для всех подключений

# Настройки спама
SPAM_DURATION_REGULAR = 10
SPAM_DURATION_PREMIUM = 15
DELAY_REGULAR = 0.1
DELAY_PREMIUM = 0.5
MAX_CONCURRENT_ACCOUNTS = 10
BATCH_SIZE = 5

# Подписки и цены
REGULAR_SUB_PRICE = 500
PREMIUM_SUB_PRICE = 1000
REFERRAL_REWARD = 5
SUB_DURATION_DAYS = 7

# CD на рассылку
CD_REGULAR = 1800
CD_PREMIUM = 600

# Подпись
SPAM_SIGNATURE = "\n\nSPAMED BY @sessionspamerbot"

# База данных
DB_FILE = "users.db"