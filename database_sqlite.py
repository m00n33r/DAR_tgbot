"""
Реализация DatabaseManager с использованием SQLite
Простая и надежная альтернатива Supabase
"""

import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime, date, time
import config
import os

class DatabaseManager:
    def __init__(self, db_path: str = "dar_bot.db"):
        """Инициализация подключения к SQLite базе данных"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Создание таблиц базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Создаем таблицу пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_admin BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Создаем таблицу аудиторий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_number TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    floor INTEGER NOT NULL,
                    capacity INTEGER,
                    equipment TEXT,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создаем таблицу бронирований
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    room_id INTEGER NOT NULL,
                    full_name TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (room_id) REFERENCES rooms (id)
                )
            ''')
            
            # Создаем индексы для оптимизации
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rooms_floor ON rooms(floor)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookings_room_time ON bookings(room_id, start_time, end_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id)')
            
            conn.commit()
            
            # Добавляем тестовые данные, если база пустая
            self._add_sample_data(cursor)
    
    def _add_sample_data(self, cursor):
        """Добавление тестовых данных"""
        # Проверяем, есть ли уже данные
        cursor.execute('SELECT COUNT(*) FROM rooms')
        if cursor.fetchone()[0] > 0:
            return
        
        # Добавляем реальные аудитории
        sample_rooms = [
            # 2 этаж
            (214, '214 Конференц-зал', 2, 50, '12 столов, 40 стульев, флипчарт, проектор, колонки 2 шт, радиомикрофон 2 шт, пульт микшерный', 'Конференц-зал на 50 человек'),
            (213, '213 Спортзал', 2, 10, '2 груши, турник, брусья', 'Спортзал на 10 человек'),
            
            # 3 этаж
            (302, '302 Переговорная', 3, 15, 'Wifi, большой прямоугольный стол, 8 стульев, монитор 55", доска, 2 дивана', 'Переговорная на 15 человек'),
            (303, '303 Центр арабского языка', 3, 15, 'Круглый стол, 12 стульев, 2 кресла, монитор 55", доска', 'Центр арабского языка на 15 человек'),
            (306, '306 Центр Корана', 3, 12, 'Круглый стол, монитор 55", доска, 12 стульев', 'Центр Корана на 12 человек'),
            (307, '307 Центр Сиры', 3, 20, 'Электронная доска (USB, hdmi, wifi), 15 стульев', 'Центр Сиры на 20 человек'),
            (308, '308 Столовая', 3, 50, 'Столы и стулья, большой экран 65"*4', 'Столовая на 50 человек'),
            
            # 4 этаж
            (401, '401 Аудитория', 4, 20, '9 столов, 18 стульев, электронная доска/монитор 65", доска', 'Аудитория на 20 человек'),
            (402, '402 Аудитория', 4, 20, '9 столов, 18 стульев, электронная доска/монитор 65", доска', 'Аудитория на 20 человек'),
            (403, '403 Аудитория', 4, 20, '9 столов, 18 стульев, электронная доска/монитор 65", доска', 'Аудитория на 20 человек'),
            (404, '404 Аудитория', 4, 10, '4 стола, 10 стульев, монитор', 'Аудитория на 10 человек'),
            (405, '405 Аудитория', 4, 20, '9 столов, 18 стульев, электронная доска/монитор 65", доска', 'Аудитория на 20 человек'),
            (406, '406 Аудитория', 4, 20, '9 столов, 18 стульев, электронная доска/монитор 65", доска', 'Аудитория на 20 человек'),
            (407, '407 Аудитория', 4, 10, '4 стола, 10 стульев, монитор', 'Аудитория на 10 человек'),
            (408, '408 Аудитория', 4, 20, '9 столов, 18 стульев, электронная доска/монитор 65", доска', 'Аудитория на 20 человек'),
            (410, '410 Аудитория', 4, 30, '12 столов, 25 стульев, проектор, электронная доска, доска', 'Аудитория на 30 человек'),
            (411, '411 Аудитория', 4, 10, 'Круглый стол, 10 стульев, монитор 55"', 'Аудитория на 10 человек'),
            (413, '413 Библиотека', 4, 20, 'Круглый стол на 15 человек, 15 стульев, книжные полки, монитор 65", доска, проектор', 'Библиотека на 20 человек'),
        ]
        
        cursor.executemany('''
            INSERT INTO rooms (room_number, name, floor, capacity, equipment, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_rooms)
    
    def _get_connection(self):
        """Получить подключение к базе данных"""
        conn = sqlite3.connect(self.db_path)
        # Включаем проверку внешних ключей
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _execute_query(self, query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False):
        """Выполнить SQL запрос"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch_one:
                    result = cursor.fetchone()
                    return dict(result) if result else None
                elif fetch_all:
                    results = cursor.fetchall()
                    return [dict(row) for row in results] if results else []
                else:
                    return cursor.lastrowid
        except Exception as e:
            print(f"Ошибка выполнения запроса: {e}")
            return None if fetch_one or fetch_all else False
    
    # Методы для работы с аудиториями
    def get_rooms_by_floor(self, floor: int) -> List[Dict]:
        """Получить все аудитории на определенном этаже"""
        query = "SELECT * FROM rooms WHERE floor = ? AND is_active = TRUE ORDER BY room_number"
        return self._execute_query(query, (floor,), fetch_all=True)
    
    def get_room_by_id(self, room_id: int) -> Optional[Dict]:
        """Получить аудиторию по ID"""
        query = "SELECT * FROM rooms WHERE id = ? AND is_active = TRUE"
        return self._execute_query(query, (room_id,), fetch_one=True)
    
    def get_all_rooms(self) -> List[Dict]:
        """Получить все аудитории"""
        query = "SELECT * FROM rooms WHERE is_active = TRUE ORDER BY floor, room_number"
        return self._execute_query(query, fetch_all=True)
    
    # --- ЕДИНЫЙ БЛОК ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ---

    def get_user_by_id(self, user_id: int):
        """Получает пользователя по ID (telegram_id)."""
        query = "SELECT * FROM users WHERE id = ?"
        return self._execute_query(query, (user_id,), fetch_one=True)

    def get_or_create_user(self, user):
        """Получает или создает пользователя в базе данных."""
        db_user = self.get_user_by_id(user.id)
        if db_user:
            return db_user
        
        query = "INSERT OR IGNORE INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?)"
        self._execute_query(query, (user.id, user.username, user.first_name, user.last_name))
        return self.get_user_by_id(user.id)

    def check_admin_password(self, telegram_id: int, password: str) -> bool:
        """Проверить пароль администратора"""
        if password == config.ADMIN_PASSWORD:
            query = "UPDATE users SET is_admin = TRUE WHERE id = ?"
            self._execute_query(query, (telegram_id,))
            return self.is_user_admin(telegram_id)
        return False
    
    def is_user_admin(self, telegram_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        user = self.get_user_by_id(telegram_id)
        return user.get('is_admin', False) if user else False

    # --- КОНЕЦ БЛОКА РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ---
    
    def get_bookings_for_date(self, selected_date: date) -> List[Dict]:
        """Получить все подтвержденные бронирования на определенную дату."""
        start_of_day = datetime.combine(selected_date, time.min).isoformat()
        end_of_day = datetime.combine(selected_date, time.max).isoformat()
        query = """
            SELECT b.*, r.name as room_name
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            WHERE b.status = 'confirmed' 
            AND b.start_time BETWEEN ? AND ?
            ORDER BY b.start_time
        """
        return self._execute_query(query, (start_of_day, end_of_day), fetch_all=True)

    # Методы для управления аудиториями (админ)
    def add_room(self, room_number: str, name: str, floor: int, capacity: int, 
                 equipment: str = "", description: str = "") -> Dict:
        """Добавить новую аудиторию"""
        query = '''
            INSERT INTO rooms (room_number, name, floor, capacity, equipment, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        room_id = self._execute_query(query, (room_number, name, floor, capacity, equipment, description, True))
        
        if room_id:
            return self.get_room_by_id(room_id)
        return {}
    
    
    def delete_room(self, room_id: int) -> bool:
        """Удалить аудиторию (мягкое удаление)"""
        query = "UPDATE rooms SET is_active = FALSE WHERE id = ?"
        return self._execute_query(query, (room_id,)) is not False
    
    def get_all_users_with_bookings(self) -> List[Dict]:
        """Получить всех пользователей с их бронированиями"""
        query = '''
            SELECT DISTINCT u.*, 
                   COUNT(b.id) as booking_count,
                   GROUP_CONCAT(DISTINCT r.name) as booked_rooms
            FROM users u
            LEFT JOIN bookings b ON u.id = b.user_id
            LEFT JOIN rooms r ON b.room_id = r.id
            WHERE b.id IS NOT NULL
            GROUP BY u.id
            ORDER BY u.created_at DESC
        '''
        return self._execute_query(query, fetch_all=True)
    
    def get_user_contact_info(self, user_id: int) -> Optional[Dict]:
        """Получить контактную информацию пользователя"""
        query = '''
            SELECT u.*, 
                   COUNT(b.id) as booking_count,
                   GROUP_CONCAT(DISTINCT r.name) as booked_rooms,
                   GROUP_CONCAT(DISTINCT b.start_time) as booking_times
            FROM users u
            LEFT JOIN bookings b ON u.id = b.user_id
            LEFT JOIN rooms r ON b.room_id = r.id
            WHERE u.id = ?
            GROUP BY u.id
        '''
        return self._execute_query(query, (user_id,), fetch_one=True)
    
    # Методы для работы с бронированиями
    def create_booking(self, user, room_id: int, full_name: str, 
                       purpose: str, start_time: datetime, end_time: datetime) -> Dict:
        """Создать новое бронирование"""
        db_user = self.get_or_create_user(user)
        if not db_user:
            print("❌ Не удалось получить/создать пользователя")
            return {}

        try:
            # Проверяем существование аудитории
            room = self.get_room_by_id(room_id)
            if not room:
                print(f"❌ Аудитория с ID {room_id} не найдена")
                return {}

            query = '''
                INSERT INTO bookings (user_id, room_id, full_name, purpose, start_time, end_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            
            booking_id = self._execute_query(query, (
                db_user['id'],
                room_id,
                full_name,
                purpose,
                start_time.isoformat(),
                end_time.isoformat(),
                'confirmed'
            ))
            
            if booking_id:
                print(f"✅ Бронирование создано с ID: {booking_id}")
                return self.get_booking_by_id(booking_id)
            else:
                print(f"❌ Ошибка создания бронирования")
                return {}
        except Exception as e:
            print(f"❌ Ошибка при создании бронирования: {e}")
            return {}
    
    def get_booking_by_id(self, booking_id: int) -> Optional[Dict]:
        """Получить бронирование по ID"""
        query = '''
            SELECT b.*, r.name as room_name, r.room_number, u.full_name as user_full_name
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            JOIN users u ON b.user_id = u.id
            WHERE b.id = ?
        '''
        return self._execute_query(query, (booking_id,), fetch_one=True)
    
    def get_user_bookings(self, telegram_id: int) -> List[Dict]:
        """Получить бронирования пользователя (только предстоящие)"""
        user = self.get_user_by_id(telegram_id)
        if not user:
            return []
        
        now = datetime.now().isoformat()
        query = '''
            SELECT b.*, r.name as room_name, r.room_number
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            WHERE b.user_id = ? AND b.start_time >= ? AND b.status = 'confirmed'
            ORDER BY b.start_time
        '''
        return self._execute_query(query, (user['id'], now), fetch_all=True)
    
    def get_room_bookings_by_date(self, room_id: int, booking_date: date) -> List[Dict]:
        """Получить все бронирования аудитории на определенную дату"""
        start_of_day = datetime.combine(booking_date, time.min).isoformat()
        end_of_day = datetime.combine(booking_date, time.max).isoformat()
        
        query = '''
            SELECT b.*, u.full_name as user_full_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            WHERE b.room_id = ? AND b.start_time >= ? AND b.start_time <= ? AND b.status = 'confirmed'
            ORDER BY b.start_time
        '''
        return self._execute_query(query, (room_id, start_of_day, end_of_day), fetch_all=True)
    
    def check_room_availability(self, room_id: int, start_time: datetime, end_time: datetime) -> bool:
        """Проверить доступность аудитории в указанное время"""
        query = '''
            SELECT COUNT(*) FROM bookings 
            WHERE room_id = ? AND status = 'confirmed' 
            AND NOT (end_time <= ? OR start_time >= ?)
        '''
        
        result = self._execute_query(query, (
            room_id, 
            start_time.isoformat(), end_time.isoformat()
        ), fetch_one=True)
        
        return result['COUNT(*)'] == 0 if result else True
    
    def get_all_bookings(self) -> List[Dict]:
        """Получить все бронирования (для админов)"""
        query = '''
            SELECT b.*, r.name as room_name, r.room_number, u.full_name as user_full_name
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            JOIN users u ON b.user_id = u.id
            ORDER BY b.created_at DESC
        '''
        return self._execute_query(query, fetch_all=True)
    
    def update_booking_status(self, booking_id: int, status: str) -> Dict:
        """Обновить статус бронирования"""
        query = "UPDATE bookings SET status = ? WHERE id = ?"
        if self._execute_query(query, (status, booking_id)) is not False:
            return self.get_booking_by_id(booking_id)
        return {}

    def delete_booking(self, booking_id: int) -> bool:
        """Удалить бронирование"""
        query = "DELETE FROM bookings WHERE id = ?"
        return self._execute_query(query, (booking_id,))

    def update_room(self, room_id: int, **kwargs) -> bool:
        """Обновить данные аудитории"""
        if not kwargs:
            return False
        
        # Строим динамический запрос UPDATE
        set_clauses = []
        values = []
        
        for field, value in kwargs.items():
            if field in ['name', 'room_number', 'floor', 'capacity', 'equipment', 'description', 'is_active']:
                set_clauses.append(f"{field} = ?")
                values.append(value)
        
        if not set_clauses:
            return False
        
        values.append(room_id)
        query = f"UPDATE rooms SET {', '.join(set_clauses)} WHERE id = ?"
        
        return self._execute_query(query, tuple(values))
    
    def create_room(self, room_number: str, name: str, floor: int, capacity: int = None, 
                   equipment: str = None, description: str = None) -> bool:
        """Создать новую аудиторию"""
        query = '''
            INSERT INTO rooms (room_number, name, floor, capacity, equipment, description)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        
        try:
            room_id = self._execute_query(query, (
                room_number,
                name,
                floor,
                capacity,
                equipment or '',
                description or ''
            ))
            return room_id is not False
        except Exception as e:
            print(f"❌ Ошибка при создании аудитории: {e}")
            return False

    def update_room_field(self, room_id, field, value):
        """Обновляет определенное поле для аудитории."""
        if field not in ['name', 'description', 'capacity', 'equipment']:
            return False
        try:
            query = f"UPDATE rooms SET {field} = ? WHERE id = ?"
            self._execute_query(query, (value, room_id))
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False