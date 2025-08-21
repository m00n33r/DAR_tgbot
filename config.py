import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Admin Password
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'AdminDAR')

# Проверяем обязательные переменные
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env файле")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL не установлен в .env файле")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY не установлен в .env файле")