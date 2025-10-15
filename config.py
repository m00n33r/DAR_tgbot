import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# SQLite Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'dar_bot.db')

# Admin Password
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'AdminDAR')

# Проверяем обязательные переменные
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env файле")