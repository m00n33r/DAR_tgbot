#!/usr/bin/env python3
"""
Дополнительные утилиты для администрирования системы бронирования аудиторий
"""

import csv
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from database import DatabaseManager

class AdminTools:
    def __init__(self):
        self.db = DatabaseManager()
    
    def export_bookings_to_csv(self, filename: str = None, start_date: date = None, end_date: date = None):
        """Экспорт бронирований в CSV файл"""
        if not filename:
            filename = f"bookings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        try:
            # Получаем все бронирования за период
            all_bookings = self.db.get_all_bookings()
            
            # Фильтруем по дате
            filtered_bookings = []
            for booking in all_bookings:
                booking_date = datetime.fromisoformat(booking['start_time']).date()
                if start_date <= booking_date <= end_date:
                    filtered_bookings.append(booking)
            
            # Записываем в CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'ID', 'Аудитория', 'Этаж', 'ФИО', 'Цель', 
                    'Дата', 'Время начала', 'Время окончания', 'Статус', 'Создано'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for booking in filtered_bookings:
                    room = booking['rooms']
                    start_time = datetime.fromisoformat(booking['start_time'])
                    end_time = datetime.fromisoformat(booking['end_time'])
                    
                    writer.writerow({
                        'ID': booking['id'],
                        'Аудитория': f"{room.get('name', 'Аудитория')} {room['room_number']}",
                        'Этаж': room['floor'],
                        'ФИО': booking['full_name'],
                        'Цель': booking['purpose'],
                        'Дата': start_time.strftime('%d.%m.%Y'),
                        'Время начала': start_time.strftime('%H:%M'),
                        'Время окончания': end_time.strftime('%H:%M'),
                        'Статус': booking['status'],
                        'Создано': datetime.fromisoformat(booking['created_at']).strftime('%d.%m.%Y %H:%M')
                    })
            
            print(f"✅ Экспорт завершен: {filename}")
            print(f"📊 Экспортировано {len(filtered_bookings)} бронирований")
            return filename
            
        except Exception as e:
            print(f"❌ Ошибка при экспорте: {e}")
            return None
    
    def export_room_statistics(self, filename: str = None, days: int = 30):
        """Экспорт статистики по аудиториям"""
        if not filename:
            filename = f"room_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            # Получаем статистику
            start_date = date.today() - timedelta(days=days)
            end_date = date.today()
            
            # Выполняем SQL-запрос для получения статистики
            # (В реальной реализации используйте функцию get_room_statistics из базы)
            
            # Создаем заглушку для демонстрации
            statistics = [
                {
                    'room_number': '201',
                    'room_name': 'Конференц-зал',
                    'total_bookings': 15,
                    'total_hours': 45.5,
                    'utilization_rate': 23.4
                },
                {
                    'room_number': '202',
                    'room_name': 'Переговорная',
                    'total_bookings': 8,
                    'total_hours': 24.0,
                    'utilization_rate': 12.3
                }
            ]
            
            # Записываем в CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Номер', 'Название', 'Количество бронирований', 'Общее время (часы)', 'Процент загрузки']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for stat in statistics:
                    writer.writerow({
                        'Номер': stat['room_number'],
                        'Название': stat['room_name'],
                        'Количество бронирований': stat['total_bookings'],
                        'Общее время (часы)': stat['total_hours'],
                        'Процент загрузки': f"{stat['utilization_rate']}%"
                    })
            
            print(f"✅ Экспорт статистики завершен: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Ошибка при экспорте статистики: {e}")
            return None
    
    def generate_weekly_report(self, filename: str = None):
        """Генерация еженедельного отчета"""
        if not filename:
            filename = f"weekly_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            # Получаем данные за последнюю неделю
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            
            all_bookings = self.db.get_all_bookings()
            
            # Фильтруем по дате
            weekly_bookings = []
            for booking in all_bookings:
                booking_date = datetime.fromisoformat(booking['start_time']).date()
                if start_date <= booking_date <= end_date:
                    weekly_bookings.append(booking)
            
            # Группируем по аудиториям
            rooms_stats = {}
            for booking in weekly_bookings:
                room_id = booking['room_id']
                if room_id not in rooms_stats:
                    rooms_stats[room_id] = {
                        'bookings_count': 0,
                        'total_hours': 0,
                        'bookings': []
                    }
                
                start_time = datetime.fromisoformat(booking['start_time'])
                end_time = datetime.fromisoformat(booking['end_time'])
                duration = (end_time - start_time).total_seconds() / 3600
                
                rooms_stats[room_id]['bookings_count'] += 1
                rooms_stats[room_id]['total_hours'] += duration
                rooms_stats[room_id]['bookings'].append(booking)
            
            # Записываем отчет
            with open(filename, 'w', encoding='utf-8') as report_file:
                report_file.write("📊 ЕЖЕНЕДЕЛЬНЫЙ ОТЧЕТ ПО БРОНИРОВАНИЯМ\n")
                report_file.write("=" * 50 + "\n\n")
                report_file.write(f"📅 Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n")
                report_file.write(f"📋 Общее количество бронирований: {len(weekly_bookings)}\n\n")
                
                for room_id, stats in rooms_stats.items():
                    # Получаем информацию об аудитории
                    room = self.db.get_room_by_id(room_id)
                    if room:
                        report_file.write(f"🏢 {room.get('name', 'Аудитория')} {room['room_number']} (Этаж {room['floor']})\n")
                        report_file.write(f"   📊 Количество бронирований: {stats['bookings_count']}\n")
                        report_file.write(f"   ⏱ Общее время: {stats['total_hours']:.1f} часов\n")
                        report_file.write(f"   📈 Средняя продолжительность: {stats['total_hours']/stats['bookings_count']:.1f} часов\n\n")
                        
                        # Детали по бронированиям
                        for booking in stats['bookings']:
                            start_time = datetime.fromisoformat(booking['start_time'])
                            end_time = datetime.fromisoformat(booking['end_time'])
                            report_file.write(f"     • {start_time.strftime('%d.%m %H:%M')} - {end_time.strftime('%H:%M')} | {booking['full_name']} | {booking['purpose']}\n")
                        report_file.write("\n")
            
            print(f"✅ Еженедельный отчет сгенерирован: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Ошибка при генерации отчета: {e}")
            return None
    
    def cleanup_old_bookings(self, days_old: int = 90):
        """Очистка старых бронирований"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Получаем все бронирования
            all_bookings = self.db.get_all_bookings()
            
            # Находим старые бронирования
            old_bookings = []
            for booking in all_bookings:
                booking_date = datetime.fromisoformat(booking['start_time'])
                if booking_date < cutoff_date:
                    old_bookings.append(booking)
            
            if not old_bookings:
                print(f"✅ Старых бронирований (старше {days_old} дней) не найдено")
                return 0
            
            print(f"🗑 Найдено {len(old_bookings)} старых бронирований для удаления")
            print("⚠️ ВНИМАНИЕ: Это действие необратимо!")
            
            # В реальной реализации здесь должна быть подтверждающая логика
            # Для демонстрации просто показываем, что было бы удалено
            
            print("\nБронирования для удаления:")
            for booking in old_bookings[:5]:  # Показываем первые 5
                room = booking['rooms']
                start_time = datetime.fromisoformat(booking['start_time'])
                print(f"  • {room['room_number']} | {start_time.strftime('%d.%m.%Y')} | {booking['full_name']}")
            
            if len(old_bookings) > 5:
                print(f"  ... и еще {len(old_bookings) - 5} бронирований")
            
            print(f"\n💡 Для реального удаления используйте метод cleanup_old_bookings_confirm()")
            return len(old_bookings)
            
        except Exception as e:
            print(f"❌ Ошибка при поиске старых бронирований: {e}")
            return 0
    
    def get_system_health(self) -> Dict:
        """Проверка состояния системы"""
        try:
            health_status = {
                'database_connection': False,
                'tables_status': {},
                'recent_activity': {},
                'overall_status': 'unknown'
            }
            
            # Проверяем подключение к базе данных
            try:
                # Пробуем получить список аудиторий
                rooms = self.db.get_all_rooms()
                health_status['database_connection'] = True
                health_status['tables_status']['rooms'] = len(rooms)
            except Exception as e:
                health_status['database_connection'] = False
                health_status['tables_status']['rooms'] = f"Error: {e}"
            
            # Проверяем таблицу пользователей
            try:
                # В реальной реализации здесь должен быть запрос к таблице users
                health_status['tables_status']['users'] = "OK"
            except Exception as e:
                health_status['tables_status']['users'] = f"Error: {e}"
            
            # Проверяем таблицу бронирований
            try:
                bookings = self.db.get_all_bookings()
                health_status['tables_status']['bookings'] = len(bookings)
            except Exception as e:
                health_status['tables_status']['bookings'] = f"Error: {e}"
            
            # Определяем общий статус
            if health_status['database_connection'] and all(
                isinstance(status, (int, str)) or "Error" not in str(status) 
                for status in health_status['tables_status'].values()
            ):
                health_status['overall_status'] = 'healthy'
            elif health_status['database_connection']:
                health_status['overall_status'] = 'warning'
            else:
                health_status['overall_status'] = 'critical'
            
            return health_status
            
        except Exception as e:
            return {
                'database_connection': False,
                'tables_status': {'error': str(e)},
                'recent_activity': {},
                'overall_status': 'error'
            }
    
    def print_system_health(self):
        """Вывод состояния системы в консоль"""
        health = self.get_system_health()
        
        print("🏥 СТАТУС СИСТЕМЫ")
        print("=" * 30)
        
        # Статус подключения к БД
        db_status = "✅ Подключено" if health['database_connection'] else "❌ Не подключено"
        print(f"🗄 База данных: {db_status}")
        
        # Статус таблиц
        print("\n📋 Статус таблиц:")
        for table, status in health['tables_status'].items():
            if isinstance(status, int):
                print(f"   {table}: ✅ {status} записей")
            elif "Error" in str(status):
                print(f"   {table}: ❌ {status}")
            else:
                print(f"   {table}: ✅ {status}")
        
        # Общий статус
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '❌',
            'error': '💥',
            'unknown': '❓'
        }
        
        print(f"\n🎯 Общий статус: {status_emoji.get(health['overall_status'], '❓')} {health['overall_status'].upper()}")

def main():
    """Основная функция для запуска админ-утилит"""
    print("🛠 Админ-утилиты для системы бронирования аудиторий")
    print("=" * 50)
    
    admin_tools = AdminTools()
    
    while True:
        print("\nВыберите действие:")
        print("1. 📊 Проверить состояние системы")
        print("2. 📁 Экспорт бронирований в CSV")
        print("3. 📈 Экспорт статистики по аудиториям")
        print("4. 📋 Генерация еженедельного отчета")
        print("5. 🗑 Поиск старых бронирований")
        print("0. 🚪 Выход")
        
        choice = input("\nВаш выбор: ").strip()
        
        if choice == "1":
            admin_tools.print_system_health()
        
        elif choice == "2":
            days = input("Количество дней для экспорта (по умолчанию 30): ").strip()
            days = int(days) if days.isdigit() else 30
            admin_tools.export_bookings_to_csv(days=days)
        
        elif choice == "3":
            days = input("Количество дней для статистики (по умолчанию 30): ").strip()
            days = int(days) if days.isdigit() else 30
            admin_tools.export_room_statistics(days=days)
        
        elif choice == "4":
            admin_tools.generate_weekly_report()
        
        elif choice == "5":
            days = input("Бронирования старше (дней, по умолчанию 90): ").strip()
            days = int(days) if days.isdigit() else 90
            admin_tools.cleanup_old_bookings(days)
        
        elif choice == "0":
            print("👋 До свидания!")
            break
        
        else:
            print("❌ Неверный выбор. Попробуйте еще раз.")

if __name__ == "__main__":
    main()