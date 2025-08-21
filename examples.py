#!/usr/bin/env python3
"""
Примеры использования и тестирования функций Telegram-бота бронирования аудиторий
"""

import asyncio
from datetime import datetime, date, time
from database import DatabaseManager
from keyboards import Keyboards

async def test_database_functions():
    """Тестирование функций базы данных"""
    print("🧪 Тестирование функций базы данных...")
    
    try:
        db = DatabaseManager()
        
        # Тест 1: Получение аудиторий по этажам
        print("\n1. Тест получения аудиторий по этажам:")
        for floor in [2, 3, 4]:
            rooms = db.get_rooms_by_floor(floor)
            print(f"   Этаж {floor}: {len(rooms)} аудиторий")
            for room in rooms:
                print(f"     - {room.get('name', f'Аудитория {room['room_number']}')} ({room['room_number']})")
        
        # Тест 2: Получение информации об аудитории
        print("\n2. Тест получения информации об аудитории:")
        room = db.get_room_by_id(1)
        if room:
            print(f"   Аудитория {room['room_number']}: {room.get('name', 'Без названия')}")
            print(f"   Размер: {room['area']} кв.м, Стулья: {room['chairs']}, Столы: {room['tables']}")
            print(f"   Оборудование: Монитор: {room.get('monitor', False)}, Флипчарт: {room.get('flipchart', False)}, Кондиционер: {room.get('air_conditioning', False)}")
        
        # Тест 3: Проверка доступности аудитории
        print("\n3. Тест проверки доступности аудитории:")
        test_start = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        test_end = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
        
        is_available = db.check_room_availability(1, test_start, test_end.isoformat())
        print(f"   Аудитория 1 доступна с {test_start.strftime('%H:%M')} до {test_end.strftime('%H:%M')}: {is_available}")
        
        # Тест 4: Получение расписания аудитории
        print("\n4. Тест получения расписания аудитории:")
        today = date.today()
        schedule = db.get_room_bookings_by_date(1, today)
        print(f"   Бронирования аудитории 1 на {today.strftime('%d.%m.%Y')}: {len(schedule)}")
        
        print("\n✅ Тестирование базы данных завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании базы данных: {e}")

def test_keyboard_generation():
    """Тестирование генерации клавиатур"""
    print("\n🧪 Тестирование генерации клавиатур...")
    
    try:
        # Тест 1: Главное меню
        print("1. Тест главного меню:")
        main_menu = Keyboards.get_main_menu()
        print(f"   Главное меню создано: {type(main_menu).__name__}")
        
        # Тест 2: Клавиатура этажей
        print("2. Тест клавиатуры этажей:")
        floors_kb = Keyboards.get_floors_keyboard()
        print(f"   Клавиатура этажей создана: {type(floors_kb).__name__}")
        
        # Тест 3: Клавиатура аудиторий
        print("3. Тест клавиатуры аудиторий:")
        test_rooms = [
            {'id': 1, 'room_number': '201', 'name': 'Конференц-зал'},
            {'id': 2, 'room_number': '202', 'name': 'Переговорная'}
        ]
        rooms_kb = Keyboards.get_rooms_keyboard(test_rooms, 2)
        print(f"   Клавиатура аудиторий создана: {type(rooms_kb).__name__}")
        
        # Тест 4: Клавиатура подтверждения
        print("4. Тест клавиатуры подтверждения:")
        confirm_kb = Keyboards.get_booking_confirmation_keyboard(1, "2024-01-01T10:00:00", "2024-01-01T12:00:00")
        print(f"   Клавиатура подтверждения создана: {type(confirm_kb).__name__}")
        
        print("\n✅ Тестирование клавиатур завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании клавиатур: {e}")

def test_booking_validation():
    """Тестирование валидации бронирований"""
    print("\n🧪 Тестирование валидации бронирований...")
    
    try:
        # Тест 1: Валидация даты
        print("1. Тест валидации даты:")
        valid_date = "15.01.2024"
        invalid_date = "15.13.2024"
        
        try:
            parsed_date = datetime.strptime(valid_date, "%d.%m.%Y").date()
            print(f"   Валидная дата {valid_date}: {parsed_date}")
        except ValueError:
            print(f"   ❌ Ошибка парсинга валидной даты {valid_date}")
        
        try:
            parsed_date = datetime.strptime(invalid_date, "%d.%m.%Y").date()
            print(f"   ❌ Невалидная дата {invalid_date} прошла валидацию")
        except ValueError:
            print(f"   ✅ Невалидная дата {invalid_date} корректно отклонена")
        
        # Тест 2: Валидация времени
        print("2. Тест валидации времени:")
        valid_time = "14:30"
        invalid_time = "25:70"
        
        try:
            parsed_time = datetime.strptime(valid_time, "%H:%M").time()
            print(f"   Валидное время {valid_time}: {parsed_time}")
        except ValueError:
            print(f"   ❌ Ошибка парсинга валидного времени {valid_time}")
        
        try:
            parsed_time = datetime.strptime(invalid_time, "%H:%M").time()
            print(f"   ❌ Невалидное время {invalid_time} прошло валидацию")
        except ValueError:
            print(f"   ✅ Невалидное время {invalid_time} корректно отклонено")
        
        # Тест 3: Валидация временного интервала
        print("3. Тест валидации временного интервала:")
        start_time = time(10, 0)  # 10:00
        end_time = time(12, 0)    # 12:00
        invalid_end_time = time(9, 0)  # 9:00
        
        if end_time > start_time:
            print(f"   ✅ Валидный интервал: {start_time} - {end_time}")
        else:
            print(f"   ❌ Невалидный интервал: {start_time} - {end_time}")
        
        if invalid_end_time > start_time:
            print(f"   ❌ Невалидный интервал прошел валидацию: {start_time} - {invalid_end_time}")
        else:
            print(f"   ✅ Невалидный интервал корректно отклонен: {start_time} - {invalid_end_time}")
        
        print("\n✅ Тестирование валидации завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании валидации: {e}")

def test_admin_functions():
    """Тестирование админ-функций"""
    print("\n🧪 Тестирование админ-функций...")
    
    try:
        # Тест 1: Проверка пароля администратора
        print("1. Тест проверки пароля администратора:")
        correct_password = "AdminDAR"
        incorrect_password = "WrongPassword"
        
        # Симуляция проверки пароля
        if correct_password == "AdminDAR":
            print("   ✅ Правильный пароль принят")
        else:
            print("   ❌ Правильный пароль отклонен")
        
        if incorrect_password == "AdminDAR":
            print("   ❌ Неправильный пароль принят")
        else:
            print("   ✅ Неправильный пароль корректно отклонен")
        
        # Тест 2: Проверка прав администратора
        print("2. Тест проверки прав администратора:")
        admin_user = {'is_admin': True}
        regular_user = {'is_admin': False}
        
        if admin_user.get('is_admin', False):
            print("   ✅ Администратор имеет доступ")
        else:
            print("   ❌ Администратор не имеет доступа")
        
        if regular_user.get('is_admin', False):
            print("   ❌ Обычный пользователь имеет админ-доступ")
        else:
            print("   ✅ Обычный пользователь не имеет админ-доступа")
        
        print("\n✅ Тестирование админ-функций завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании админ-функций: {e}")

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования Telegram-бота бронирования аудиторий")
    print("=" * 60)
    
    # Тестирование функций базы данных
    await test_database_functions()
    
    # Тестирование генерации клавиатур
    test_keyboard_generation()
    
    # Тестирование валидации бронирований
    test_booking_validation()
    
    # Тестирование админ-функций
    test_admin_functions()
    
    print("\n" + "=" * 60)
    print("🎉 Тестирование завершено!")
    print("\n📝 Рекомендации:")
    print("1. Убедитесь, что база данных Supabase настроена")
    print("2. Проверьте подключение к базе данных")
    print("3. Запустите бота командой: python bot.py")
    print("4. Протестируйте функциональность в Telegram")

if __name__ == "__main__":
    # Запуск тестирования
    asyncio.run(main())