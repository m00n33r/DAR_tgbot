from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict
from database_sqlite import DatabaseManager
from datetime import datetime

class Keyboards:
    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        """Главное меню бота"""
        keyboard = [
            ['🗂 Аудитории', '📅 Забронировать'],
            ['📅 Мои брони', '📋 Активные брони'],
            ['🛠 Админ-панель', 'ℹ️ Помощь']
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
            room_name = room.get('name', f'Аудитория {room.get("id", "?")}')
            keyboard.append([InlineKeyboardButton(room_name, callback_data=f"room_{room['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад к этажам", callback_data="back_to_floors")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_room_details_keyboard(room_id: int) -> InlineKeyboardMarkup:
        """Клавиатура для детальной информации об аудитории"""
        keyboard = [
            [InlineKeyboardButton("📅 Забронировать аудиторию", callback_data=f"book_room_details_{room_id}")],
            [InlineKeyboardButton("⬅️ Назад к списку аудиторий", callback_data="back_to_rooms")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_room_booking_details_keyboard(room_id: int) -> InlineKeyboardMarkup:
        """Клавиатура для детальной информации об аудитории при бронировании"""
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить бронирование", callback_data=f"book_room_{room_id}")],
            [InlineKeyboardButton("🔙 Назад к аудиториям", callback_data="back_to_booking_rooms")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_booking_confirmation_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура подтверждения бронирования"""
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_booking")],
            [InlineKeyboardButton("✏️ Переписать", callback_data="rewrite_booking")],
            [InlineKeyboardButton("❌ Отклонить", callback_data="cancel_booking")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_admin_menu():
        """Возвращает клавиатуру для админ-панели."""
        keyboard = [
            [InlineKeyboardButton("✏️ Редактировать аудитории", callback_data='admin_edit_rooms')],
            [InlineKeyboardButton("➕ Добавить аудиторию", callback_data='admin_add_room')],
            [InlineKeyboardButton("👥 Контакты пользователей", callback_data='admin_user_contacts')],
            [InlineKeyboardButton("📅 Удалить бронирование", callback_data='admin_booking_delete_menu')],
            [InlineKeyboardButton("🚪 Выйти из админ-панели", callback_data='exit_admin')]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_add_room_keyboard():
        """Возвращает клавиатуру для выбора этажа при добавлении аудитории."""
        floors = DatabaseManager().get_floors()
        keyboard = []
        for floor in floors:
            keyboard.append([InlineKeyboardButton(f"{floor} этаж", callback_data=f"admin_add_floor_{floor}")])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_admin")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_delete_booking_keyboard(bookings):
        """Возвращает клавиатуру для выбора брони для удаления."""
        keyboard = []
        for b in bookings:
            start_time = datetime.fromisoformat(b['start_time']).strftime('%H:%M')
            room_name = b['room_name']
            button_text = f"❌ {room_name} ({start_time}) - {b['full_name']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"admin_confirm_delete_{b['id']}")])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_admin")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_edit_room_floor_keyboard():
        """Возвращает клавиатуру для выбора этажа для редактирования."""
        floors = DatabaseManager().get_floors()
        keyboard = []
        for floor in floors:
            keyboard.append([InlineKeyboardButton(f"{floor} этаж", callback_data=f"admin_edit_floor_{floor}")])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_admin")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_edit_room_select_keyboard(rooms):
        """Возвращает клавиатуру для выбора аудитории для редактирования."""
        keyboard = []
        for room in rooms:
            keyboard.append([InlineKeyboardButton(room['name'], callback_data=f"admin_edit_room_{room['id']}")])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_admin")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_edit_field_keyboard(room_id):
        """Возвращает клавиатуру для выбора поля для редактирования."""
        keyboard = [
            [InlineKeyboardButton("Название", callback_data=f"admin_edit_field_name")],
            [InlineKeyboardButton("Описание", callback_data=f"admin_edit_field_description")],
            [InlineKeyboardButton("Вместимость", callback_data=f"admin_edit_field_capacity")],
            [InlineKeyboardButton("Оборудование", callback_data=f"admin_edit_field_equipment")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_admin")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_back_to_admin_keyboard():
        """Возвращает клавиатуру для возврата в главное меню админки."""
        keyboard = [
            [InlineKeyboardButton("⬅️ Назад в админ-панель", callback_data='back_to_admin')]
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
    
    @staticmethod
    def get_rooms_management_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура управления аудиториями"""
        keyboard = [
            [InlineKeyboardButton("📋 Список аудиторий", callback_data="admin_list_rooms")],
            [InlineKeyboardButton("➕ Добавить аудиторию", callback_data="admin_add_room")],
            [InlineKeyboardButton("🔙 Назад в админ-панель", callback_data="back_to_admin")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_room_management_keyboard(room_id: int) -> InlineKeyboardMarkup:
        """Клавиатура управления конкретной аудиторией"""
        keyboard = [
            [InlineKeyboardButton("✏️ Редактировать", callback_data=f"admin_edit_room_{room_id}")],
            [InlineKeyboardButton("🗑 Удалить", callback_data=f"admin_delete_room_{room_id}")],
            [InlineKeyboardButton("🔙 Назад к списку", callback_data="admin_list_rooms")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_users_list_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура списка пользователей"""
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в админ-панель", callback_data="back_to_admin")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_user_details_keyboard(user_id: int) -> InlineKeyboardMarkup:
        """Клавиатура детальной информации о пользователе"""
        keyboard = [
            [InlineKeyboardButton("📞 Получить контакт", callback_data=f"admin_get_contact_{user_id}")],
            [InlineKeyboardButton("🔙 Назад к списку", callback_data="admin_all_users")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_room_bookings_keyboard(room_id: int) -> InlineKeyboardMarkup:
        """Клавиатура для аудитории с бронированиями"""
        keyboard = [
            [InlineKeyboardButton("📅 Забронировать эту аудиторию", callback_data=f"book_room_{room_id}")],
            [InlineKeyboardButton("🔙 Назад к аудиториям", callback_data="rooms")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_active_bookings_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для активных бронирований"""
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="active_bookings")],
            [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_active_bookings_date_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для активных бронирований на конкретную дату"""
        keyboard = [
            [InlineKeyboardButton("📅 Выбрать другую дату", callback_data="active_bookings")],
            [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_booking_floors_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура выбора этажа для бронирования"""
        keyboard = [
            [InlineKeyboardButton("2 этаж", callback_data="book_floor_2")],
            [InlineKeyboardButton("3 этаж", callback_data="book_floor_3")],
            [InlineKeyboardButton("4 этаж", callback_data="book_floor_4")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_booking_rooms_keyboard(rooms: List[Dict], floor: int) -> InlineKeyboardMarkup:
        """Клавиатура выбора аудитории для бронирования"""
        keyboard = []
        for room in rooms:
            room_name = room.get('name', f'Аудитория {room.get("id", "?")}')
            keyboard.append([InlineKeyboardButton(room_name, callback_data=f"book_room_{room['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад к этажам", callback_data="back_to_floors")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_edit_rooms_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для редактирования аудиторий"""
        keyboard = [
            [InlineKeyboardButton("2️⃣ Второй этаж", callback_data="admin_edit_floor_2")],
            [InlineKeyboardButton("3️⃣ Третий этаж", callback_data="admin_edit_floor_3")],
            [InlineKeyboardButton("4️⃣ Четвертый этаж", callback_data="admin_edit_floor_4")],
            [InlineKeyboardButton("🔙 Назад в админ-панель", callback_data="back_to_admin")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_delete_rooms_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для удаления аудиторий"""
        keyboard = [
            [InlineKeyboardButton("2️⃣ Второй этаж", callback_data="admin_delete_floor_2")],
            [InlineKeyboardButton("3️⃣ Третий этаж", callback_data="admin_delete_floor_3")],
            [InlineKeyboardButton("4️⃣ Четвертый этаж", callback_data="admin_delete_floor_4")],
            [InlineKeyboardButton("🔙 Назад в админ-панель", callback_data="back_to_admin")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_room_edit_keyboard(room_id: int) -> InlineKeyboardMarkup:
        """Клавиатура для редактирования конкретной аудитории"""
        keyboard = [
            [InlineKeyboardButton("📝 Редактировать название", callback_data=f"admin_edit_room_name_{room_id}")],
            [InlineKeyboardButton("👥 Редактировать вместимость", callback_data=f"admin_edit_room_capacity_{room_id}")],
            [InlineKeyboardButton("🔧 Редактировать оборудование", callback_data=f"admin_edit_room_equipment_{room_id}")],
            [InlineKeyboardButton("📄 Редактировать описание", callback_data=f"admin_edit_room_description_{room_id}")],
            [InlineKeyboardButton("💾 Сохранить изменения", callback_data=f"admin_save_room_{room_id}")],
            [InlineKeyboardButton("🔙 Назад к аудиториям", callback_data="admin_edit_rooms")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_room_delete_confirm_keyboard(room_id: int) -> InlineKeyboardMarkup:
        """Клавиатура подтверждения удаления аудитории"""
        keyboard = [
            [InlineKeyboardButton("✅ Да, удалить", callback_data=f"admin_confirm_delete_room_{room_id}")],
            [InlineKeyboardButton("❌ Отмена", callback_data="admin_delete_room")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_user_contacts_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для просмотра контактов пользователей"""
        keyboard = [
            [InlineKeyboardButton("📅 Выбрать дату", callback_data="admin_select_date_contacts")],
            [InlineKeyboardButton("🔙 Назад в админ-панель", callback_data="back_to_admin")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_back_to_admin_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для возврата в админ-панель"""
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в админ-панель", callback_data="back_to_admin")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_booking_floors_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура выбора этажа для бронирования"""
        keyboard = [
            [InlineKeyboardButton("2 этаж", callback_data="book_floor_2")],
            [InlineKeyboardButton("3 этаж", callback_data="book_floor_3")],
            [InlineKeyboardButton("4 этаж", callback_data="book_floor_4")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_booking_rooms_keyboard(rooms: List[Dict], floor: int) -> InlineKeyboardMarkup:
        """Клавиатура выбора аудитории для бронирования"""
        keyboard = []
        for room in rooms:
            room_name = room.get('name', f'Аудитория {room.get("id", "?")}')
            keyboard.append([InlineKeyboardButton(room_name, callback_data=f"book_room_{room['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад к этажам", callback_data="back_to_booking_floors")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_room_booking_details_keyboard(room_id: int) -> InlineKeyboardMarkup:
        """Клавиатура для детальной информации об аудитории при бронировании"""
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить бронирование", callback_data=f"book_room_{room_id}")],
            [InlineKeyboardButton("🔙 Назад к аудиториям", callback_data="back_to_booking_rooms")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_back_to_calendar_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для возврата к календарю выбора даты."""
        keyboard = [
            [InlineKeyboardButton("📅 Выбрать другую дату", callback_data="back_to_calendar")],
            [InlineKeyboardButton("Главное меню", callback_data="back_to_main")]
        ]
        return InlineKeyboardMarkup(keyboard)