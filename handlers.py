from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, date, time
import re
from database import DatabaseManager
from keyboards import Keyboards

# Состояния для ConversationHandler
CHOOSING_FLOOR, CHOOSING_ROOM, ENTERING_ROOM_NUMBER, ENTERING_FULL_NAME, ENTERING_PURPOSE, ENTERING_DATE, ENTERING_START_TIME, ENTERING_END_TIME, ADMIN_PASSWORD = range(9)

class Handlers:
    def __init__(self):
        self.db = DatabaseManager()
        self.user_states = {}  # Хранение состояния пользователей
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        telegram_id = user.id
        
        # Проверяем, существует ли пользователь в базе
        db_user = self.db.get_user_by_telegram_id(telegram_id)
        if not db_user:
            # Создаем нового пользователя
            self.db.create_user(telegram_id, user.username, user.first_name)
        
        welcome_text = f"""
🎉 Добро пожаловать в бот бронирования аудиторий КЦ «Дар»!

👋 Привет, {user.first_name}!

Выберите нужный раздел в главном меню:
🗂 Аудитории - информация о доступных аудиториях
📅 Забронировать - забронировать аудиторию
🔎 Мои брони - ваши активные брони
🛠 Админ-панель - управление системой (только для администраторов)
ℹ️ Помощь - справка по использованию бота
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=Keyboards.get_main_menu()
        )
    
    async def show_rooms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать выбор этажа для просмотра аудиторий"""
        await update.message.reply_text(
            "🏢 Выберите этаж для просмотра аудиторий:",
            reply_markup=Keyboards.get_floors_keyboard()
        )
    
    async def show_floor_rooms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать аудитории на выбранном этаже"""
        query = update.callback_query
        await query.answer()
        
        floor = int(query.data.split('_')[1])
        rooms = self.db.get_rooms_by_floor(floor)
        
        if not rooms:
            await query.edit_message_text(
                f"❌ На {floor} этаже нет доступных аудиторий.",
                reply_markup=Keyboards.get_floors_keyboard()
            )
            return
        
        # Сохраняем выбранный этаж в контексте
        context.user_data['selected_floor'] = floor
        context.user_data['rooms'] = rooms
        
        await query.edit_message_text(
            f"🏢 Аудитории на {floor} этаже:",
            reply_markup=Keyboards.get_rooms_keyboard(rooms, floor)
        )
    
    async def show_room_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать детальную информацию об аудитории"""
        query = update.callback_query
        await query.answer()
        
        room_id = int(query.data.split('_')[1])
        room = self.db.get_room_by_id(room_id)
        
        if not room:
            await query.edit_message_text("❌ Аудитория не найдена.")
            return
        
        # Формируем описание аудитории
        description = f"""
🏢 **{room.get('name', f'Аудитория {room['room_number']}')}**

📏 **Размер:** {room['area']} кв.м
🪑 **Мебель:** {room['chairs']} стульев, {room['tables']} столов

**Оборудование:**
"""
        
        if room.get('monitor'):
            description += "🖥 Монитор\n"
        if room.get('flipchart'):
            description += "📋 Флипчарт\n"
        if room.get('air_conditioning'):
            description += "🧊 Кондиционер\n"
        
        if room.get('comments'):
            description += f"\n📝 **Комментарии:** {room['comments']}"
        
        # Добавляем фото, если есть
        if room.get('photo_url'):
            await query.edit_message_text(
                description,
                reply_markup=Keyboards.get_room_details_keyboard(room_id),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                description,
                reply_markup=Keyboards.get_room_details_keyboard(room_id),
                parse_mode='Markdown'
            )
    
    async def start_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать процесс бронирования"""
        query = update.callback_query
        await query.answer()
        
        if 'book_room_' in query.data:
            room_id = int(query.data.split('_')[2])
            context.user_data['booking_room_id'] = room_id
        else:
            # Если пользователь выбрал "Забронировать" из главного меню
            await query.edit_message_text(
                "🏢 Введите номер аудитории для бронирования:",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return ENTERING_ROOM_NUMBER
        
        await query.edit_message_text(
            "👤 Введите ваше ФИО:",
            reply_markup=Keyboards.get_cancel_keyboard()
        )
        return ENTERING_FULL_NAME
    
    async def enter_room_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода номера аудитории"""
        room_number = update.message.text.strip()
        
        # Ищем аудиторию по номеру
        all_rooms = self.db.get_all_rooms()
        room = None
        for r in all_rooms:
            if str(r['room_number']) == room_number:
                room = r
                break
        
        if not room:
            await update.message.reply_text(
                "❌ Аудитория с таким номером не найдена. Попробуйте еще раз:",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return ENTERING_ROOM_NUMBER
        
        context.user_data['booking_room_id'] = room['id']
        await update.message.reply_text(
            "👤 Введите ваше ФИО:",
            reply_markup=Keyboards.get_cancel_keyboard()
        )
        return ENTERING_FULL_NAME
    
    async def enter_full_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода ФИО"""
        full_name = update.message.text.strip()
        context.user_data['full_name'] = full_name
        
        await update.message.reply_text(
            "🎯 Введите цель мероприятия:",
            reply_markup=Keyboards.get_cancel_keyboard()
        )
        return ENTERING_PURPOSE
    
    async def enter_purpose(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода цели мероприятия"""
        purpose = update.message.text.strip()
        context.user_data['purpose'] = purpose
        
        await update.message.reply_text(
            "📅 Введите дату бронирования (формат: ДД.ММ.ГГГГ):",
            reply_markup=Keyboards.get_cancel_keyboard()
        )
        return ENTERING_DATE
    
    async def enter_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода даты"""
        date_str = update.message.text.strip()
        
        try:
            booking_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            if booking_date < date.today():
                await update.message.reply_text(
                    "❌ Нельзя бронировать аудиторию на прошедшую дату. Попробуйте еще раз:",
                    reply_markup=Keyboards.get_cancel_keyboard()
                )
                return ENTERING_DATE
            
            context.user_data['booking_date'] = booking_date
            await update.message.reply_text(
                "🕐 Введите время начала (формат: ЧЧ:ММ):",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return ENTERING_START_TIME
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ:",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return ENTERING_DATE
    
    async def enter_start_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода времени начала"""
        time_str = update.message.text.strip()
        
        try:
            start_time = datetime.strptime(time_str, "%H:%M").time()
            context.user_data['start_time'] = start_time
            
            await update.message.reply_text(
                "🕐 Введите время окончания (формат: ЧЧ:ММ):",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return ENTERING_END_TIME
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат времени. Используйте формат ЧЧ:ММ:",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return ENTERING_START_TIME
    
    async def enter_end_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода времени окончания"""
        time_str = update.message.text.strip()
        
        try:
            end_time = datetime.strptime(time_str, "%H:%M").time()
            start_time = context.user_data['start_time']
            
            if end_time <= start_time:
                await update.message.reply_text(
                    "❌ Время окончания должно быть позже времени начала. Попробуйте еще раз:",
                    reply_markup=Keyboards.get_cancel_keyboard()
                )
                return ENTERING_END_TIME
            
            # Проверяем доступность аудитории
            room_id = context.user_data['booking_room_id']
            booking_date = context.user_data['booking_date']
            start_datetime = datetime.combine(booking_date, start_time)
            end_datetime = datetime.combine(booking_date, end_time)
            
            if not self.db.check_room_availability(room_id, start_datetime, end_datetime.isoformat()):
                await update.message.reply_text(
                    "❌ Аудитория уже забронирована на это время. Выберите другое время:",
                    reply_markup=Keyboards.get_cancel_keyboard()
                )
                return ENTERING_START_TIME
            
            # Показываем подтверждение
            room = self.db.get_room_by_id(room_id)
            room_name = room.get('name', f"Аудитория {room['room_number']}")
            
            confirmation_text = f"""
📋 **Подтверждение бронирования**

🏢 **Аудитория:** {room_name}
👤 **ФИО:** {context.user_data['full_name']}
🎯 **Цель:** {context.user_data['purpose']}
📅 **Дата:** {booking_date.strftime('%d.%m.%Y')}
🕐 **Время:** {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}

Подтвердите бронирование:
            """
            
            await update.message.reply_text(
                confirmation_text,
                reply_markup=Keyboards.get_booking_confirmation_keyboard(
                    room_id, 
                    start_datetime.isoformat(), 
                    end_datetime.isoformat()
                ),
                parse_mode='Markdown'
            )
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат времени. Используйте формат ЧЧ:ММ:",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return ENTERING_END_TIME
    
    async def confirm_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Подтверждение бронирования"""
        query = update.callback_query
        await query.answer()
        
        # Парсим данные из callback_data
        data_parts = query.data.split('_')
        room_id = int(data_parts[2])
        start_time = datetime.fromisoformat(data_parts[3])
        end_time = datetime.fromisoformat(data_parts[4])
        
        user_id = update.effective_user.id
        full_name = context.user_data.get('full_name', '')
        purpose = context.user_data.get('purpose', '')
        
        # Создаем бронирование
        booking = self.db.create_booking(user_id, room_id, full_name, purpose, start_time, end_time)
        
        if booking:
            room = self.db.get_room_by_id(room_id)
            room_name = room.get('name', f"Аудитория {room['room_number']}")
            
            success_text = f"""
✅ **Бронирование подтверждено!**

🏢 **Аудитория:** {room_name}
👤 **ФИО:** {full_name}
🎯 **Цель:** {purpose}
📅 **Дата:** {start_time.strftime('%d.%m.%Y')}
🕐 **Время:** {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}

Ваша заявка принята и обрабатывается.
            """
            
            await query.edit_message_text(
                success_text,
                reply_markup=Keyboards.get_main_menu(),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ Ошибка при создании бронирования. Попробуйте еще раз.",
                reply_markup=Keyboards.get_main_menu()
            )
    
    async def show_my_bookings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать бронирования пользователя"""
        user_id = update.effective_user.id
        bookings = self.db.get_user_bookings(user_id)
        
        if not bookings:
            await update.message.reply_text(
                "📭 У вас нет активных бронирований.",
                reply_markup=Keyboards.get_main_menu()
            )
            return
        
        # Группируем бронирования по дате
        bookings_by_date = {}
        for booking in bookings:
            start_time = datetime.fromisoformat(booking['start_time'])
            date_key = start_time.strftime('%d.%m.%Y')
            if date_key not in bookings_by_date:
                bookings_by_date[date_key] = []
            bookings_by_date[date_key].append(booking)
        
        # Формируем текст
        text = "📋 **Ваши активные бронирования:**\n\n"
        
        for date_key in sorted(bookings_by_date.keys()):
            text += f"📅 **{date_key}:**\n"
            for booking in bookings_by_date[date_key]:
                room = booking['rooms']
                room_name = room.get('name', f"Аудитория {room['room_number']}")
                start_time = datetime.fromisoformat(booking['start_time'])
                end_time = datetime.fromisoformat(booking['end_time'])
                
                text += f"  🏢 {room_name}\n"
                text += f"  🕐 {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n"
                text += f"  🎯 {booking['purpose']}\n\n"
        
        await update.message.reply_text(
            text,
            reply_markup=Keyboards.get_main_menu(),
            parse_mode='Markdown'
        )
    
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать админ-панель"""
        user_id = update.effective_user.id
        
        if self.db.is_user_admin(user_id):
            await update.message.reply_text(
                "🛠 **Админ-панель**\n\nВыберите действие:",
                reply_markup=Keyboards.get_admin_menu(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "🔐 Для доступа к админ-панели введите пароль администратора:",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return ADMIN_PASSWORD
    
    async def check_admin_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверка пароля администратора"""
        password = update.message.text.strip()
        user_id = update.effective_user.id
        
        if self.db.check_admin_password(user_id, password):
            await update.message.reply_text(
                "✅ Доступ разрешен! Добро пожаловать в админ-панель.",
                reply_markup=Keyboards.get_admin_menu()
            )
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                "❌ Неверный пароль. Попробуйте еще раз или нажмите Отмена:",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return ADMIN_PASSWORD
    
    async def show_all_bookings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать все бронирования (для админов)"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        if not self.db.is_user_admin(user_id):
            await query.edit_message_text("❌ Доступ запрещен.")
            return
        
        bookings = self.db.get_all_bookings()
        
        if not bookings:
            await query.edit_message_text(
                "📭 Нет активных бронирований.",
                reply_markup=Keyboards.get_admin_menu()
            )
            return
        
        # Показываем первые 10 бронирований
        text = "📊 **Все бронирования:**\n\n"
        
        for i, booking in enumerate(bookings[:10]):
            room = booking['rooms']
            room_name = room.get('name', f"Аудитория {room['room_number']}")
            start_time = datetime.fromisoformat(booking['start_time'])
            end_time = datetime.fromisoformat(booking['end_time'])
            
            text += f"{i+1}. 🏢 {room_name}\n"
            text += f"   👤 {booking['full_name']}\n"
            text += f"   📅 {start_time.strftime('%d.%m.%Y %H:%M')} - {end_time.strftime('%H:%M')}\n"
            text += f"   🎯 {booking['purpose']}\n"
            text += f"   📊 Статус: {booking['status']}\n\n"
        
        if len(bookings) > 10:
            text += f"... и еще {len(bookings) - 10} бронирований"
        
        await query.edit_message_text(
            text,
            reply_markup=Keyboards.get_admin_menu(),
            parse_mode='Markdown'
        )
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать справку"""
        help_text = """
ℹ️ **Справка по использованию бота**

🗂 **Аудитории** - просмотр информации о доступных аудиториях по этажам
📅 **Забронировать** - забронировать аудиторию на определенное время
🔎 **Мои брони** - просмотр ваших активных бронирований
🛠 **Админ-панель** - управление системой (требует пароль администратора)

**Как забронировать аудиторию:**
1. Выберите "📅 Забронировать"
2. Введите номер аудитории
3. Укажите ваше ФИО
4. Опишите цель мероприятия
5. Выберите дату и время
6. Подтвердите бронирование

**Поддержка:** Обратитесь к администратору системы
        """
        
        await update.message.reply_text(
            help_text,
            reply_markup=Keyboards.get_main_menu(),
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback-запросов"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_to_main":
            await query.edit_message_text(
                "🏠 Главное меню:",
                reply_markup=Keyboards.get_main_menu()
            )
        elif query.data == "back_to_floors":
            await query.edit_message_text(
                "🏢 Выберите этаж для просмотра аудиторий:",
                reply_markup=Keyboards.get_floors_keyboard()
            )
        elif query.data == "back_to_rooms":
            floor = context.user_data.get('selected_floor', 2)
            rooms = context.user_data.get('rooms', [])
            await query.edit_message_text(
                f"🏢 Аудитории на {floor} этаже:",
                reply_markup=Keyboards.get_rooms_keyboard(rooms, floor)
            )
        elif query.data == "cancel":
            await query.edit_message_text(
                "❌ Операция отменена.",
                reply_markup=Keyboards.get_main_menu()
            )
        elif query.data == "cancel_booking":
            await query.edit_message_text(
                "❌ Бронирование отменено.",
                reply_markup=Keyboards.get_main_menu()
            )
        elif query.data.startswith("admin_all_bookings"):
            await self.show_all_bookings(update, context)
        elif query.data.startswith("admin_all_users"):
            await query.edit_message_text(
                "👥 **Все пользователи**\n\nФункция в разработке.",
                reply_markup=Keyboards.get_admin_menu(),
                parse_mode='Markdown'
            )
        elif query.data.startswith("confirm_booking"):
            await self.confirm_booking(update, context)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        text = update.message.text
        
        if text == "🗂 Аудитории":
            await self.show_rooms(update, context)
        elif text == "📅 Забронировать":
            await update.message.reply_text(
                "🏢 Введите номер аудитории для бронирования:",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return ENTERING_ROOM_NUMBER
        elif text == "🔎 Мои брони":
            await self.show_my_bookings(update, context)
        elif text == "🛠 Админ-панель":
            await self.show_admin_panel(update, context)
        elif text == "ℹ️ Помощь":
            await self.show_help(update, context)
        else:
            # Если это не команда меню, проверяем состояние пользователя
            user_id = update.effective_user.id
            if user_id in self.user_states:
                # Обрабатываем ввод в зависимости от состояния
                pass
            else:
                await update.message.reply_text(
                    "Выберите действие из главного меню:",
                    reply_markup=Keyboards.get_main_menu()
                )