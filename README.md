# DAR Telegram Bot

Система бронирования помещений через Telegram с облачной базой данных Supabase.

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка .env файла
Создайте файл `.env` в корне проекта:
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Supabase Configuration
SUPABASE_URL=https://ioxqmtkyujutalfrsavw.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlveHFtdGt5dWp1dGFsZnJzYXZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU4MDY3NTMsImV4cCI6MjA3MTM4Mjc1M30.xtflT_hu0monV6E4_Ad3j3hZaALZ1NQhdA_BWCnL59s

# Admin Configuration
ADMIN_PASSWORD=AdminDAR
```

### 3. Настройка базы данных
```bash
python setup_final.py
```

### 4. Запуск бота
```bash
# Вариант 1: Через скрипт запуска
python start_bot.py

# Вариант 2: Напрямую
python bot.py

# Вариант 3: В фоне
nohup python bot.py > bot.log 2>&1 &
```

## 📁 Структура проекта

```
DAR_tgbot/
├── bot.py              # Основной файл бота
├── handlers.py         # Обработчики команд
├── keyboards.py        # Клавиатуры
├── database.py         # Работа с Supabase
├── config.py           # Настройки
├── setup_final.py      # Настройка данных
├── requirements.txt    # Зависимости
└── README.md          # Документация
```

## 🏢 Помещения

### 2 этаж
- 214 конференц-зал (50 человек)
- 213 Спортзал (10 человек)

### 3 этаж
- 302 переговорная (15 человек)
- 303 Центр арабского языка (15 человек)
- 306 Центр Корана (12 человек)
- 307 Центр Сиры (20 человек)
- Столовая (50 человек)

### 4 этаж
- 413 Библиотека (20 человек)
- 401-408 Аудитории (10-20 человек)
- 410 Аудитория (30 человек)
- 411 Аудитория (10 человек)

## 🎯 Команды бота

- `/start` - начать работу с ботом
- `/help` - помощь и инструкции
- `/admin` - админ-панель (пароль: AdminDAR)
- `/cancel` - отменить текущую операцию

## 🔧 Технические детали

- **База данных**: Supabase (облачная)
- **API**: HTTP REST API
- **Без паролей**: только API ключи
- **Зависимости**: минимальные (3 пакета)

## ❌ Устранение неполадок

### Ошибка "Cannot close a running event loop"
```bash
# Попробуйте один из вариантов:
python -m asyncio bot.py
# или
python bot.py &
# или
nohup python bot.py > bot.log 2>&1 &
```

### Ошибка "SUPABASE_URL не настроен"
- Убедитесь, что файл `.env` создан
- Проверьте правильность настроек

### Ошибка "Connection failed"
- Проверьте интернет-соединение
- Убедитесь, что Supabase проект активен

## 🎉 Готово!

Ваш DAR Telegram Bot готов к работе! 🚀