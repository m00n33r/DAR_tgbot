from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict

class Keyboards:
    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        """Главное меню бота"""
        keyboard = [
            ['🗂 Аудитории', '📅 Забронировать'],
            ['🔎 Мои брони', '🛠 Админ-панель'],
            ['ℹ️ Помощь']
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    @staticmethod
    def get_floors_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура выбора этажа"""
        keyboard = [
            [InlineKeyboardButton("2 этаж", callback_data="floor_2")],
            [InlineKeyboardButton("3 этаж", callback_data="floor_3")],
            [InlineKeyboardButton("4 этаж", callback_data="floor_4")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_rooms_keyboard(rooms: List[Dict], floor: int) -> InlineKeyboardMarkup:
        """Клавиатура выбора аудитории на этаже"""
        keyboard = []
        for room in rooms:
            room_name = f"Аудитория {room['room_number']}"
            if room.get('name'):
                room_name = room['name']
            keyboard.append([InlineKeyboardButton(room_name, callback_data=f"room_{room['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад к этажам", callback_data="back_to_floors")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_room_details_keyboard(room_id: int) -> InlineKeyboardMarkup:
        """Клавиатура для детальной информации об аудитории"""
        keyboard = [
            [InlineKeyboardButton("📅 Забронировать эту аудиторию", callback_data=f"book_room_{room_id}")],
            [InlineKeyboardButton("🔙 Назад к аудиториям", callback_data="back_to_rooms")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_booking_confirmation_keyboard(room_id: int, start_time: str, end_time: str) -> InlineKeyboardMarkup:
        """Клавиатура подтверждения бронирования"""
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_booking_{room_id}_{start_time}_{end_time}")],
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_booking")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_admin_menu() -> InlineKeyboardMarkup:
        """Админ-панель"""
        keyboard = [
            [InlineKeyboardButton("📊 Все бронирования", callback_data="admin_all_bookings")],
            [InlineKeyboardButton("👥 Все пользователи", callback_data="admin_all_users")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_booking_management_keyboard(booking_id: int) -> InlineKeyboardMarkup:
        """Клавиатура управления бронированием для админа"""
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_confirm_{booking_id}")],
            [InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject_{booking_id}")],
            [InlineKeyboardButton("🗑 Удалить", callback_data=f"admin_delete_{booking_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_all_bookings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_cancel_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура отмены"""
        keyboard = [
            [InlineKeyboardButton("🔙 Отмена", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)