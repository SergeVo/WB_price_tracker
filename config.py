import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Периодичность проверки цен (в минутах)
CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '180'))  # По умолчанию 3 часа

# Базовый URL Wildberries
WB_BASE_URL = 'https://www.wildberries.ru'

# Заголовки для запросов
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
} 