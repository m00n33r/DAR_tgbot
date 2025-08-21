from supabase import create_client, Client
from typing import List, Dict, Optional
from datetime import datetime, date, time
import config

class DatabaseManager:
    def __init__(self):
        self.supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    
    # Методы для работы с аудиториями
    def get_rooms_by_floor(self, floor: int) -> List[Dict]:
        """Получить все аудитории на определенном этаже"""
        response = self.supabase.table('rooms').select('*').eq('floor', floor).execute()
        return response.data
    
    def get_room_by_id(self, room_id: int) -> Optional[Dict]:
        """Получить аудиторию по ID"""
        response = self.supabase.table('rooms').select('*').eq('id', room_id).execute()
        return response.data[0] if response.data else None
    
    def get_all_rooms(self) -> List[Dict]:
        """Получить все аудитории"""
        response = self.supabase.table('rooms').select('*').execute()
        return response.data
    
    # Методы для работы с бронированиями
    def create_booking(self, user_id: int, room_id: int, full_name: str, 
                       purpose: str, start_time: datetime, end_time: datetime) -> Dict:
        """Создать новое бронирование"""
        booking_data = {
            'user_id': user_id,
            'room_id': room_id,
            'full_name': full_name,
            'purpose': purpose,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'status': 'confirmed'
        }
        response = self.supabase.table('bookings').insert(booking_data).execute()
        return response.data[0] if response.data else None
    
    def get_user_bookings(self, user_id: int) -> List[Dict]:
        """Получить бронирования пользователя (только предстоящие)"""
        now = datetime.now().isoformat()
        response = self.supabase.table('bookings').select('*, rooms(*)').eq('user_id', user_id).gte('start_time', now).execute()
        return response.data
    
    def get_room_bookings_by_date(self, room_id: int, booking_date: date) -> List[Dict]:
        """Получить все бронирования аудитории на определенную дату"""
        start_of_day = datetime.combine(booking_date, time.min).isoformat()
        end_of_day = datetime.combine(booking_date, time.max).isoformat()
        
        response = self.supabase.table('bookings').select('*').eq('room_id', room_id).gte('start_time', start_of_day).lte('start_time', end_of_day).execute()
        return response.data
    
    def check_room_availability(self, room_id: int, start_time: datetime, end_time: str) -> bool:
        """Проверить доступность аудитории в указанное время"""
        # Проверяем пересечения с существующими бронированиями
        response = self.supabase.table('bookings').select('*').eq('room_id', room_id).eq('status', 'confirmed').execute()
        
        for booking in response.data:
            existing_start = datetime.fromisoformat(booking['start_time'])
            existing_end = datetime.fromisoformat(booking['end_time'])
            
            # Проверяем пересечение временных интервалов
            if (start_time < existing_end and end_time > existing_start):
                return False
        
        return True
    
    def get_all_bookings(self) -> List[Dict]:
        """Получить все бронирования (для админов)"""
        response = self.supabase.table('bookings').select('*, rooms(*)').execute()
        return response.data
    
    def update_booking_status(self, booking_id: int, status: str) -> Dict:
        """Обновить статус бронирования"""
        response = self.supabase.table('bookings').update({'status': status}).eq('id', booking_id).execute()
        return response.data[0] if response.data else None
    
    def delete_booking(self, booking_id: int) -> bool:
        """Удалить бронирование"""
        response = self.supabase.table('bookings').delete().eq('id', booking_id).execute()
        return len(response.data) > 0
    
    # Методы для работы с пользователями
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Получить пользователя по Telegram ID"""
        response = self.supabase.table('users').select('*').eq('telegram_id', telegram_id).execute()
        return response.data[0] if response.data else None
    
    def create_user(self, telegram_id: int, username: str, full_name: str) -> Dict:
        """Создать нового пользователя"""
        user_data = {
            'telegram_id': telegram_id,
            'username': username,
            'full_name': full_name,
            'is_admin': False
        }
        response = self.supabase.table('users').insert(user_data).execute()
        return response.data[0] if response.data else None
    
    def check_admin_password(self, telegram_id: int, password: str) -> bool:
        """Проверить пароль администратора"""
        if password == config.ADMIN_PASSWORD:
            # Обновляем статус пользователя на админа
            self.supabase.table('users').update({'is_admin': True}).eq('telegram_id', telegram_id).execute()
            return True
        return False
    
    def is_user_admin(self, telegram_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        user = self.get_user_by_telegram_id(telegram_id)
        return user.get('is_admin', False) if user else False