#!/usr/bin/env python3
"""
Простой тест для проверки работоспособности Telegram-бота
"""

import sys
import os

def test_imports():
    """Тест импорта модулей"""
    print("🧪 Тестирование импорта модулей...")
    
    try:
        import config
        print("   ✅ config.py - OK")
    except Exception as e:
        print(f"   ❌ config.py - Ошибка: {e}")
        return False
    
    try:
        import database
        print("   ✅ database.py - OK")
    except Exception as e:
        print(f"   ❌ database.py - Ошибка: {e}")
        return False
    
    try:
        import keyboards
        print("   ✅ keyboards.py - OK")
    except Exception as e:
        print(f"   ❌ keyboards.py - Ошибка: {e}")
        return False
    
    try:
        import handlers
        print("   ✅ handlers.py - OK")
    except Exception as e:
        print(f"   ❌ handlers.py - Ошибка: {e}")
        return False
    
    try:
        import bot
        print("   ✅ bot.py - OK")
    except Exception as e:
        print(f"   ❌ bot.py - Ошибка: {e}")
        return False
    
    return True

def test_config():
    """Тест конфигурации"""
    print("\n🧪 Тестирование конфигурации...")
    
    try:
        import config
        
        # Проверяем наличие переменных окружения
        if not os.path.exists('.env'):
            print("   ⚠️ Файл .env не найден")
            print("   💡 Создайте .env файл на основе .env.example")
            return False
        
        # Проверяем, что переменные не пустые (если .env загружен)
        if hasattr(config, 'TELEGRAM_BOT_TOKEN') and config.TELEGRAM_BOT_TOKEN:
            print("   ✅ TELEGRAM_BOT_TOKEN - настроен")
        else:
            print("   ❌ TELEGRAM_BOT_TOKEN - не настроен")
            return False
        
        if hasattr(config, 'SUPABASE_URL') and config.SUPABASE_URL:
            print("   ✅ SUPABASE_URL - настроен")
        else:
            print("   ❌ SUPABASE_URL - не настроен")
            return False
        
        if hasattr(config, 'SUPABASE_KEY') and config.SUPABASE_KEY:
            print("   ✅ SUPABASE_KEY - настроен")
        else:
            print("   ❌ SUPABASE_KEY - не настроен")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при проверке конфигурации: {e}")
        return False

def test_dependencies():
    """Тест зависимостей"""
    print("\n🧪 Тестирование зависимостей...")
    
    required_packages = [
        'telegram',
        'supabase',
        'dotenv',
        'PIL'
    ]
    
    all_ok = True
    
    for package in required_packages:
        try:
            if package == 'telegram':
                import telegram
                print(f"   ✅ {package} - OK")
            elif package == 'supabase':
                import supabase
                print(f"   ✅ {package} - OK")
            elif package == 'dotenv':
                import dotenv
                print(f"   ✅ {package} - OK")
            elif package == 'PIL':
                import PIL
                print(f"   ✅ {package} - OK")
        except ImportError:
            print(f"   ❌ {package} - не установлен")
            all_ok = False
    
    return all_ok

def test_database_connection():
    """Тест подключения к базе данных"""
    print("\n🧪 Тестирование подключения к базе данных...")
    
    try:
        import config
        import database
        
        # Создаем экземпляр менеджера БД
        db = database.DatabaseManager()
        
        # Пробуем получить список аудиторий
        rooms = db.get_all_rooms()
        print(f"   ✅ Подключение к Supabase - OK")
        print(f"   📊 Найдено аудиторий: {len(rooms)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка подключения к базе данных: {e}")
        print("   💡 Проверьте:")
        print("      - Правильность SUPABASE_URL и SUPABASE_KEY")
        print("      - Статус проекта Supabase")
        print("      - Выполнение SQL-скрипта database_setup.sql")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование Telegram-бота бронирования аудиторий")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Тест 1: Импорт модулей
    if not test_imports():
        all_tests_passed = False
    
    # Тест 2: Конфигурация
    if not test_config():
        all_tests_passed = False
    
    # Тест 3: Зависимости
    if not test_dependencies():
        all_tests_passed = False
    
    # Тест 4: Подключение к БД (только если предыдущие тесты прошли)
    if all_tests_passed:
        if not test_database_connection():
            all_tests_passed = False
    
    print("\n" + "=" * 60)
    
    if all_tests_passed:
        print("🎉 Все тесты прошли успешно!")
        print("\n✅ Бот готов к запуску!")
        print("🚀 Запустите бота командой: python bot.py")
    else:
        print("❌ Некоторые тесты не прошли")
        print("\n🔧 Для исправления проблем:")
        print("1. Установите зависимости: pip install -r requirements.txt")
        print("2. Создайте и настройте .env файл")
        print("3. Настройте базу данных Supabase")
        print("4. Выполните SQL-скрипт database_setup.sql")
    
    print("\n📚 Подробные инструкции см. в README.md и DEPLOYMENT.md")

if __name__ == "__main__":
    main()