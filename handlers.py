from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler, ContextTypes
from datetime import datetime, date, timedelta
from database_sqlite import DatabaseManager
from keyboards import Keyboards
from calendar_widget import booking_calendar
import locale
from itertools import groupby
import logging

# Устанавливаем русскую локаль для форматирования даты
try:
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, 'Russian_Russia.1251')


(
    CHOOSING_FLOOR, CHOOSING_ROOM, ENTERING_FULL_NAME, ENTERING_PURPOSE,
    SELECTING_DATE, ENTERING_START_TIME, ENTERING_END_TIME,
    CONFIRMING_BOOKING, ADMIN_PASSWORD, ENTERING_MANUAL_DATE
) = range(10)

# Состояния для админ-панели
(
    ADMIN_MAIN, ADMIN_ADDING_ROOM_FLOOR, ADMIN_ADDING_ROOM_NUMBER,
    ADMIN_ADDING_ROOM_NAME, ADMIN_ADDING_ROOM_CAPACITY, ADMIN_ADDING_ROOM_EQUIPMENT,
    ADMIN_ADDING_ROOM_DESCRIPTION, ADMIN_SELECT_CONTACTS_DATE, ADMIN_SELECT_DELETE_DATE,
    ADMIN_EDIT_SELECT_FLOOR, ADMIN_EDIT_SELECT_ROOM, ADMIN_EDIT_SELECT_FIELD,
    ADMIN_EDIT_SET_NEW_VALUE
) = range(10, 23)


class Handlers:
    def __init__(self):
        self.db = DatabaseManager()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        # Ensure the user exists in DB using the unified user management API
        self.db.get_or_create_user(user)
        await update.message.reply_text(
            f"🎉 Добро пожаловать, {user.first_name}!\nВыберите раздел в меню:",
            reply_markup=Keyboards.get_main_menu()
        )
    
    async def show_rooms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🏢 Выберите этаж для просмотра аудиторий:",
            reply_markup=Keyboards.get_floors_keyboard()
        )
    
    async def start_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        for key in list(context.user_data.keys()):
            if key.startswith('booking_'):
                del context.user_data[key]
        await update.message.reply_text(
            "🏢 Выберите этаж для бронирования:",
            reply_markup=Keyboards.get_booking_floors_keyboard()
        )
        return CHOOSING_FLOOR

    async def show_floor_rooms_for_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        floor = int(query.data.split("_")[2])
        context.user_data['booking_floor'] = floor
        rooms = self.db.get_rooms_by_floor(floor)
        if not rooms:
            await query.edit_message_text(
                f"❌ На {floor} этаже нет доступных аудиторий.",
                reply_markup=Keyboards.get_booking_floors_keyboard()
            )
            return CHOOSING_FLOOR
        await query.edit_message_text(
            f"🏢 Выберите аудиторию на {floor} этаже:",
            reply_markup=Keyboards.get_booking_rooms_keyboard(rooms, floor)
        )
        return CHOOSING_ROOM

    async def start_booking_from_room_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        room_id = int(query.data.split("_")[3])
        room = self.db.get_room_by_id(room_id)
        if not room:
            await query.edit_message_text("❌ Аудитория не найдена.")
            return ConversationHandler.END
        for key in list(context.user_data.keys()):
            if key.startswith('booking_'):
                del context.user_data[key]
        context.user_data['booking_room_id'] = room_id
        context.user_data['booking_room'] = room
        room_name = room.get('name', f'Аудитория {room["room_number"]}')
        await query.edit_message_text(
            f"🏢 Выбрана аудитория: {room_name}\n\n👤 Введите ваше ФИО:",
            reply_markup=Keyboards.get_cancel_keyboard()
        )
        return ENTERING_FULL_NAME
    
    async def start_booking_from_room(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        room_id = int(query.data.split("_")[2])
        room = self.db.get_room_by_id(room_id)
        if not room:
            await query.edit_message_text("❌ Аудитория не найдена.")
            return CHOOSING_ROOM
        context.user_data['booking_room_id'] = room_id
        context.user_data['booking_room'] = room
        room_name = room.get('name', f'Аудитория {room["room_number"]}')
        await query.edit_message_text(
            f"🏢 Выбрана аудитория: {room_name}\n\n👤 Введите ваше ФИО:",
            reply_markup=Keyboards.get_cancel_keyboard()
        )
        return ENTERING_FULL_NAME
    
    async def enter_full_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['booking_full_name'] = update.message.text.strip()
        await update.message.reply_text("🎯 Введите цель мероприятия:", reply_markup=Keyboards.get_cancel_keyboard())
        return ENTERING_PURPOSE
    
    async def enter_purpose(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['booking_purpose'] = update.message.text.strip()
        now = datetime.now()
        calendar_markup = booking_calendar.create_calendar(year=now.year, month=now.month)
        context.user_data['calendar_context'] = 'booking_date'
        await update.message.reply_text("📅 Выберите дату мероприятия:", reply_markup=calendar_markup)
        return SELECTING_DATE

    async def request_manual_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("📅 Введите дату бронирования в формате ДД.ММ.ГГГГ:")
        return ENTERING_MANUAL_DATE

    async def handle_manual_date_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        date_text = update.message.text.strip()
        try:
            booking_date = datetime.strptime(date_text, '%d.%m.%Y').date()
            if booking_date < date.today():
                await update.message.reply_text("❌ Нельзя бронировать на прошедшую дату. Введите дату еще раз:")
                return ENTERING_MANUAL_DATE
            context.user_data['booking_date'] = booking_date
            await update.message.reply_text(f"📅 Выбрана дата: {booking_date.strftime('%d.%m.%Y')}\n\n🕐 Введите время начала (например: 14:30):")
            return ENTERING_START_TIME
        except ValueError:
            await update.message.reply_text("❌ Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ:")
            return ENTERING_MANUAL_DATE
    
    async def enter_start_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            start_time = datetime.strptime(update.message.text.strip(), '%H:%M').time()
            context.user_data['booking_start_time'] = start_time
            await update.message.reply_text("🕐 Введите время окончания (например: 16:00):")
            return ENTERING_END_TIME
        except ValueError:
            await update.message.reply_text("❌ Неверный формат времени. Введите в формате ЧЧ:ММ:")
            return ENTERING_START_TIME
    
    async def enter_end_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            end_time = datetime.strptime(update.message.text.strip(), '%H:%M').time()
            if end_time <= context.user_data['booking_start_time']:
                await update.message.reply_text("❌ Время окончания должно быть позже времени начала:")
                return ENTERING_END_TIME
            context.user_data['booking_end_time'] = end_time
            # Переход к выбору повторяемости
            await update.message.reply_text(
                "🔁 Хотите повторять бронирование?",
                reply_markup=Keyboards.get_recurrence_keyboard()
            )
            context.user_data['booking_recurrence'] = 'none'
            return SELECTING_DATE
        except ValueError:
            await update.message.reply_text("❌ Неверный формат времени. Введите в формате ЧЧ:ММ:")
            return ENTERING_END_TIME
            
    async def show_booking_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        ud = context.user_data
        room_name = ud.get('booking_room', {}).get('name', '?')
        full_name = ud.get('booking_full_name', '')
        purpose = ud.get('booking_purpose', '')
        booking_date = ud.get('booking_date')
        start_time = ud.get('booking_start_time')
        end_time = ud.get('booking_end_time')
        recurrence = ud.get('booking_recurrence', 'none')
        recurrence_until = ud.get('booking_recurrence_until')
        
        text = (
            f"📋 Сводка бронирования\n\n"
            f"🏢 Аудитория: {room_name}\n"
            f"👤 ФИО: {full_name}\n"
            f"🎯 Цель: {purpose}\n"
            f"📅 Дата: {booking_date.strftime('%d.%m.%Y')}\n"
            f"🕐 Время: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n"
            f"🔁 Повторение: {self._format_recurrence(recurrence, recurrence_until)}\n\n"
            "Все верно?"
        )
        await update.message.reply_text(text, reply_markup=Keyboards.get_booking_confirmation_keyboard())

    async def show_booking_confirmation_from_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        ud = context.user_data
        room_name = ud.get('booking_room', {}).get('name', '?')
        full_name = ud.get('booking_full_name', '')
        purpose = ud.get('booking_purpose', '')
        booking_date = ud.get('booking_date')
        start_time = ud.get('booking_start_time')
        end_time = ud.get('booking_end_time')
        recurrence = ud.get('booking_recurrence', 'none')
        recurrence_until = ud.get('booking_recurrence_until')

        text = (
            f"📋 Сводка бронирования\n\n"
            f"🏢 Аудитория: {room_name}\n"
            f"👤 ФИО: {full_name}\n"
            f"🎯 Цель: {purpose}\n"
            f"📅 Дата: {booking_date.strftime('%d.%m.%Y')}\n"
            f"🕐 Время: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n"
            f"🔁 Повторение: {self._format_recurrence(recurrence, recurrence_until)}\n\n"
            "Все верно?"
        )
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.get_booking_confirmation_keyboard())

    async def confirm_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        # Убедимся, что пользователь есть в БД
        user = update.effective_user
        self.db.get_or_create_user(user)

        # Собираем все данные из user_data
        ud = context.user_data
        room_id = ud.get('booking_room_id')
        full_name = ud.get('booking_full_name')
        purpose = ud.get('booking_purpose')
        booking_date = ud.get('booking_date')
        start_time = ud.get('booking_start_time')
        end_time = ud.get('booking_end_time')

        try:
            start_dt = datetime.combine(booking_date, start_time)
            end_dt = datetime.combine(booking_date, end_time)
            recurrence = ud.get('booking_recurrence', 'none')
            recurrence_until = ud.get('booking_recurrence_until')

            if recurrence != 'none' and recurrence_until:
                group_id = f"{user.id}-{room_id}-{int(datetime.now().timestamp())}"
                current_date = booking_date
                created = 0
                while current_date <= recurrence_until:
                    s_dt = datetime.combine(current_date, start_time)
                    e_dt = datetime.combine(current_date, end_time)
                    if self.db.check_room_availability(room_id, s_dt, e_dt):
                        self.db.create_booking(
                            user,
                            room_id,
                            full_name,
                            purpose,
                            s_dt,
                            e_dt,
                            recurrence_type=recurrence,
                            recurrence_until=datetime.combine(recurrence_until, end_time),
                            recurrence_group=group_id
                        )
                        created += 1
                    # шаг интервала
                    if recurrence == 'weekly':
                        current_date = date.fromordinal(current_date.toordinal() + 7)
                    elif recurrence == 'biweekly':
                        current_date = date.fromordinal(current_date.toordinal() + 14)
                    elif recurrence == 'monthly':
                        # переход на следующий месяц, безопасно ограничиваем днем 28
                        year = current_date.year + (current_date.month // 12)
                        month = (current_date.month % 12) + 1
                        day = min(current_date.day, 28)
                        current_date = date(year, month, day)
                await query.edit_message_text(f"✅ Создано бронирований: {created}")
            else:
                self.db.create_booking(
                    user,
                    room_id, 
                    full_name,
                    purpose,
                    start_dt,
                    end_dt
                )
                await query.edit_message_text("✅ **Бронирование подтверждено!**", parse_mode='Markdown')
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка при создании бронирования: {e}")
        finally:
            for key in list(context.user_data.keys()):
                if key.startswith('booking_'):
                    del context.user_data[key]
            return ConversationHandler.END

    def _format_recurrence(self, rec_type: str, until) -> str:
        mapping = {
            'none': 'Единоразово',
            'weekly': 'Раз в неделю',
            'biweekly': 'Раз в 2 недели',
            'monthly': 'Раз в месяц'
        }
        base = mapping.get(rec_type, 'Единоразово')
        if rec_type != 'none' and until:
            return f"{base} до {until.strftime('%d.%m.%Y')}"
        return base
            
    async def cancel_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        for key in list(context.user_data.keys()):
            if key.startswith('booking_'):
                del context.user_data[key]
        text = "❌ Операция отменена."
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.delete_message()
            await update.callback_query.message.reply_text(text, reply_markup=Keyboards.get_main_menu())
        else:
            await update.message.reply_text(text, reply_markup=Keyboards.get_main_menu())
        return ConversationHandler.END

    async def rewrite_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        for key in ['booking_full_name', 'booking_purpose', 'booking_date', 'booking_start_time', 'booking_end_time']:
            context.user_data.pop(key, None)
        room_name = context.user_data.get('booking_room', {}).get('name', '?')
        await query.edit_message_text(f"Данные сброшены. 🏢 Аудитория: {room_name}\n\n👤 Введите ваше ФИО:")
        return ENTERING_FULL_NAME
    
    async def show_my_bookings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать активные бронирования пользователя в новом формате."""
        logging.info("Entering show_my_bookings function")
        user_id = update.effective_user.id
        bookings_raw = self.db.get_user_bookings(user_id)
        logging.info(f"Got {len(bookings_raw)} bookings from DB for user {user_id}")
        
        if not bookings_raw:
            await update.message.reply_text("У вас нет активных бронирований.")
            return
        
        # Конвертируем строки в datetime объекты
        bookings = []
        for b in bookings_raw:
            b['start_time'] = datetime.fromisoformat(b['start_time'])
            b['end_time'] = datetime.fromisoformat(b['end_time'])
            bookings.append(b)

        message = "📅 **Ваши бронирования:**\n\n"
        
        # Группируем брони по дате
        grouped_bookings = groupby(bookings, lambda b: b['start_time'].date())
        
        for booking_date, group in grouped_bookings:
            # Форматируем дату (например: "16 окт")
            date_str = booking_date.strftime("%d %b").lower()
            message += f"🗓 **{date_str}**\n"
            
            for b in group:
                start_time = b['start_time'].strftime('%H:%M')
                end_time = b['end_time'].strftime('%H:%M')
                purpose = b['purpose']
                room_name = b['room_name']
                message += f"    `{start_time}`-`{end_time}` - *{room_name}*: _{purpose}_\n"
            message += "\n"
            
        await update.message.reply_text(message, parse_mode='Markdown')
        logging.info("Sent my_bookings message to user")

    async def show_all_active_bookings_calendar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['calendar_context'] = 'active_bookings'
        now = datetime.now()
        await update.message.reply_text(
            "📅 Выберите дату для просмотра бронирований:",
            reply_markup=booking_calendar.create_calendar(year=now.year, month=now.month)
        )

    async def handle_calendar_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = booking_calendar.parse_callback_data(query.data)
        action = data.get('action')
        cal_ctx = context.user_data.get('calendar_context', '')

        if action in ['prev', 'next']:
            year, month = (data['year'], data['month'])
            if action == 'prev': year, month = booking_calendar.get_prev_month(year, month)
            else: year, month = booking_calendar.get_next_month(year, month)
            await query.edit_message_reply_markup(booking_calendar.create_calendar(year=year, month=month))
            return SELECTING_DATE if cal_ctx == 'booking_date' else None

        if action == 'select':
            selected_date = date(data['year'], data['month'], data['day'])
            if cal_ctx == 'booking_date':
                context.user_data['booking_date'] = selected_date
                await query.edit_message_text(f"📅 Дата: {selected_date.strftime('%d.%m.%Y')}\n\n🕐 Введите время начала (ЧЧ:ММ):")
                return ENTERING_START_TIME
            elif cal_ctx == 'active_bookings':
                await self.show_active_bookings_for_date(update, context, selected_date)
                return None
            elif cal_ctx == 'admin_contacts':
                return await self.admin_show_contacts_for_date(update, context, selected_date)
            elif cal_ctx == 'admin_delete':
                return await self.admin_show_bookings_to_delete(update, context, selected_date)
            elif cal_ctx == 'recurrence_until':
                base_date = context.user_data.get('booking_date')
                if base_date and selected_date < base_date:
                    await query.edit_message_text(
                        "❌ Дата окончания не может быть раньше даты начала. Выберите другую дату:",
                        reply_markup=booking_calendar.create_calendar(year=base_date.year, month=base_date.month)
                    )
                    return SELECTING_DATE
                context.user_data['booking_recurrence_until'] = selected_date
                # показываем сводку через callback
                await self.show_booking_confirmation_from_callback(update, context)
                return CONFIRMING_BOOKING

        # Возвращаем нужное состояние в зависимости от контекста
        if cal_ctx == 'booking_date':
            return SELECTING_DATE
        elif cal_ctx == 'admin_contacts':
            return ADMIN_SELECT_CONTACTS_DATE
        elif cal_ctx == 'admin_delete':
            return ADMIN_SELECT_DELETE_DATE
        return None

    async def handle_recurrence_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопок выбора повторения: recurrence_none|weekly|biweekly|monthly"""
        query = update.callback_query
        await query.answer()
        data = query.data
        if not data.startswith('recurrence_'):
            return
        rec_type = data.split('_', 1)[1]  # none|weekly|biweekly|monthly
        # Нормализуем значения
        if rec_type not in ['none', 'weekly', 'biweekly', 'monthly']:
            rec_type = 'none'
        context.user_data['booking_recurrence'] = rec_type

        if rec_type == 'none':
            # Покажем сводку сразу
            await self.show_booking_confirmation_from_callback(update, context)
            return CONFIRMING_BOOKING

        # Попросим указать дату окончания повторений
        now = datetime.now()
        context.user_data['calendar_context'] = 'recurrence_until'
        await query.edit_message_text(
            "📅 Выберите дату окончания повторений (включительно):",
            reply_markup=booking_calendar.create_calendar(year=now.year, month=now.month)
        )
        return SELECTING_DATE

    async def show_active_bookings_for_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE, selected_date):
        query = update.callback_query
        bookings_raw = self.db.get_bookings_for_date(selected_date)
        if not bookings_raw:
            text = f"📋 На {selected_date.strftime('%d.%m.%Y')} нет бронирований."
        else:
            text = f"📋 Бронирования на {selected_date.strftime('%d.%m.%Y')}:\n\n"
            for b in bookings_raw:
                room = self.db.get_room_by_id(b['room_id'])
                user = self.db.get_user_by_id(b['user_id'])
                start_time_dt = datetime.fromisoformat(b['start_time'])
                end_time_dt = datetime.fromisoformat(b['end_time'])
                
                # Формируем имя пользователя
                if user:
                    first_name = user.get('first_name', '')
                    last_name = user.get('last_name', '')
                    user_full_name = f"{first_name} {last_name}".strip() or "Неизвестный"
                else:
                    user_full_name = b.get('full_name', 'Неизвестный')
                
                text += f"🏢 **{room.get('name', '?')}** ({start_time_dt.strftime('%H:%M')}-{end_time_dt.strftime('%H:%M')})\n"
                text += f"👤 {user_full_name}\n🎯 {b['purpose']}\n\n"
        await query.edit_message_text(text, reply_markup=Keyboards.get_back_to_calendar_keyboard(), parse_mode='Markdown')

    async def show_floor_rooms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        floor = int(query.data.split('_')[1])
        rooms = self.db.get_rooms_by_floor(floor)
        if not rooms:
            await query.edit_message_text(f"❌ На {floor} этаже нет аудиторий.", reply_markup=Keyboards.get_floors_keyboard())
            return
        await query.edit_message_text(f"🏢 Аудитории на {floor} этаже:", reply_markup=Keyboards.get_rooms_keyboard(rooms, floor))

    async def show_room_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        room_id = int(query.data.split('_')[1])
        room = self.db.get_room_by_id(room_id)
        if not room:
            await query.edit_message_text("❌ Аудитория не найдена.")
            return
        text = (
            f"🏢 **{room.get('name', 'Аудитория')}**\n\n"
            f"📍 **Этаж:** {room.get('floor', '-')}\n"
            f"👥 **Вместимость:** {room.get('capacity', '-')} чел.\n"
            f"🔧 **Оборудование:** {room.get('equipment', '-')}\n"
            f"📝 **Описание:** {room.get('description', '-')}"
        )
        await query.edit_message_text(text, reply_markup=Keyboards.get_room_details_keyboard(room_id), parse_mode='Markdown')
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "Справочная информация по боту DAR\n\n"
            "Этот бот предназначен для бронирования аудиторий в здании DAR.\n\n"
            "Основные команды:\n"
            "📅 Забронировать - начать процесс бронирования аудитории.\n"
            "🗂 Аудитории - просмотр списка всех доступных аудиторий по этажам.\n"
            "📅 Мои брони - просмотр ваших активных бронирований.\n"
            "📋 Активные брони - просмотр всех активных бронирований в здании.\n"
            "🛠 Админ-панель - доступ к функциям администратора (требуется пароль).\n\n"
            "Контакты для связи:\n"
            "• Системный администратор: @Serik_Murzaliev\n"
            "• По вопросам разработки: @m00n33r\n\n"
            "Если у вас возникли проблемы, пожалуйста, свяжитесь с администратором."
        )
        await update.message.reply_text(text=text)

    async def handle_text_global(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Единый обработчик текстов: пароль админа или новое значение при редактировании."""
        # приоритет: пароль админа
        if context.user_data.get('awaiting_admin_password'):
            return await self.check_admin_password(update, context)
        # затем: редактирование аудиторий
        if context.user_data.get('admin_edit_in_progress') and context.user_data.get('admin_edit_field'):
            return await self.admin_edit_set_new_value(update, context)
        # иначе игнорируем
        return
    async def handle_other_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query.data.startswith("cal_"):
            await self.handle_calendar_callback(update, context)
            return
        if query.data.startswith('recurrence_'):
            await self.handle_recurrence_callback(update, context)
            return
        await query.answer()
        if query.data.startswith("floor_"): await self.show_floor_rooms(update, context)
        elif query.data.startswith("room_"): await self.show_room_details(update, context)
        elif query.data == "back_to_floors": await query.edit_message_text("🏢 Выберите этаж:", reply_markup=Keyboards.get_floors_keyboard())
        elif query.data == "back_to_calendar":
            context.user_data['calendar_context'] = 'active_bookings'
            now = datetime.now()
            await query.edit_message_text(
                "📅 Выберите дату для просмотра бронирований:",
                reply_markup=booking_calendar.create_calendar(year=now.year, month=now.month)
            )
        elif query.data == "back_to_main":
            await query.answer()
            await query.delete_message()
            await query.message.reply_text("🏠 Главное меню:", reply_markup=Keyboards.get_main_menu())
        elif query.data == "back_to_admin":
            await self.show_admin_panel(update, context)


    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать админ-панель или запросить пароль. Работает и с message, и с callback_query."""
        query = update.callback_query
        user = update.effective_user

        async def reply(text, reply_markup):
            if query:
                await query.answer()
                await query.edit_message_text(text, reply_markup=reply_markup)
            else:
                await update.message.reply_text(text, reply_markup=reply_markup)

        if self.db.is_user_admin(user.id):
            await reply(
                "🛠 Админ-панель\n\nВыберите действие:",
                reply_markup=Keyboards.get_admin_menu()
            )
        else:
            # отметим, что ожидаем пароль админа через текст
            context.user_data['awaiting_admin_password'] = True
            await reply(
                "🔐 Для доступа к админ-панели введите пароль:",
                reply_markup=None
            )


    async def check_admin_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверить пароль администратора."""
        user_id = update.effective_user.id
        password = update.message.text.strip()

        # обрабатываем пароль только если его действительно ждут
        if not context.user_data.get('awaiting_admin_password'):
            return

        if self.db.check_admin_password(user_id, password):
            await update.message.reply_text(
                "✅ Доступ разрешен!",
                reply_markup=Keyboards.get_admin_menu()
            )
            context.user_data.pop('awaiting_admin_password', None)
        else:
            await update.message.reply_text(
                "❌ Неверный пароль. Попробуйте еще раз или вернитесь в главное меню."
            )
            # оставляем флаг, чтобы следующие сообщения также воспринимались как пароль
    
    async def exit_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выход из админ-панели."""
        query = update.callback_query
        await query.answer()
        await query.delete_message()
        await query.message.reply_text("Возвращаю в главное меню.", reply_markup=Keyboards.get_main_menu())
        return ConversationHandler.END

    async def show_admin_panel_and_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Прерывает текущий диалог (например, бронирование) и передает управление дальше."""
        for key in list(context.user_data.keys()):
            if key.startswith('booking_'):
                del context.user_data[key]
        return ConversationHandler.END

    # --- Добавление аудитории ---
    async def admin_add_room_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "➕ Добавление аудитории\n\nВыберите этаж:",
            reply_markup=Keyboards.get_add_room_keyboard()
        )
        return ADMIN_ADDING_ROOM_FLOOR
    
    async def admin_add_room_get_floor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        floor = int(query.data.split("_")[-1])
        context.user_data['admin_add_floor'] = floor
        await query.edit_message_text(f"Этаж {floor}. Теперь введите номер аудитории (например, 214):")
        return ADMIN_ADDING_ROOM_NUMBER

    async def admin_add_room_get_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['admin_add_number'] = update.message.text.strip()
        await update.message.reply_text("Введите название аудитории (например, Конференц-зал):")
        return ADMIN_ADDING_ROOM_NAME

    async def admin_add_room_get_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['admin_add_name'] = update.message.text.strip()
        await update.message.reply_text("Введите вместимость (просто число):")
        return ADMIN_ADDING_ROOM_CAPACITY

    async def admin_add_room_get_capacity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['admin_add_capacity'] = int(update.message.text.strip())
        await update.message.reply_text("Введите оборудование (через запятую):")
        return ADMIN_ADDING_ROOM_EQUIPMENT
        
    async def admin_add_room_get_equipment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['admin_add_equipment'] = update.message.text.strip()
        await update.message.reply_text("Введите краткое описание аудитории:")
        return ADMIN_ADDING_ROOM_DESCRIPTION

    async def admin_add_room_finish(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        ud = context.user_data
        success = self.db.create_room(
            room_number=ud['admin_add_number'],
            name=ud['admin_add_name'],
            floor=ud['admin_add_floor'],
            capacity=ud['admin_add_capacity'],
            equipment=ud['admin_add_equipment'],
            description=update.message.text.strip()
        )
        if success:
            await update.message.reply_text("✅ Аудитория успешно добавлена!", reply_markup=Keyboards.get_admin_menu())
        else:
            await update.message.reply_text("❌ Ошибка при добавлении аудитории.", reply_markup=Keyboards.get_admin_menu())

        # Clear admin_add_... keys
        for key in list(ud.keys()):
            if key.startswith('admin_add_'):
                del ud[key]
        return ADMIN_MAIN
        
    # --- Контакты пользователей ---
    async def admin_contacts_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        context.user_data['calendar_context'] = 'admin_contacts'
        now = datetime.now()
        await query.edit_message_text(
            "👥 Контакты пользователей\n\nВыберите дату для просмотра:",
            reply_markup=booking_calendar.create_calendar(year=now.year, month=now.month)
        )
        return ADMIN_SELECT_CONTACTS_DATE
    
    async def admin_show_contacts_for_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE, selected_date):
        query = update.callback_query
        bookings = self.db.get_bookings_for_date(selected_date)
        
        if not bookings:
            text = f"На {selected_date.strftime('%d.%m.%Y')} нет бронирований."
        else:
            text = f"📋 Бронирования на {selected_date.strftime('%d.%m.%Y')}:\n\n"
            for b in bookings:
                user = self.db.get_user_by_id(b['user_id'])
                room = self.db.get_room_by_id(b['room_id'])
                
                username = f"@{user['username']}" if user and user.get('username') else "скрыт"
                if user:
                    first_name = user.get('first_name', '')
                    last_name = user.get('last_name', '')
                    user_full_name = f"{first_name} {last_name}".strip() or "Неизвестный"
                else:
                    user_full_name = "Неизвестный"
                room_name = room.get('name', 'Неизвестная аудитория') if room else 'Неизвестная аудитория'
                
                start_time_dt = datetime.fromisoformat(b['start_time'])
                end_time_dt = datetime.fromisoformat(b['end_time'])
                
                start_time_str = start_time_dt.strftime('%H:%M')
                end_time_str = end_time_dt.strftime('%H:%M')
                
                text += f"**{room_name}** ({start_time_str}-{end_time_str})\n"
                text += f"👤 {user_full_name} ({username})\n"
                text += f"🎯 {b.get('purpose', 'Цель не указана')}\n\n"

        await query.edit_message_text(text, reply_markup=Keyboards.get_back_to_admin_keyboard(), parse_mode='Markdown')
        return ADMIN_MAIN

    # --- Удаление бронирований ---
    async def admin_delete_booking_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        context.user_data['calendar_context'] = 'admin_delete'
        now = datetime.now()
        await query.edit_message_text(
            "📅 Удаление бронирования\n\nВыберите дату для просмотра броней:",
            reply_markup=booking_calendar.create_calendar(year=now.year, month=now.month)
        )
        return ADMIN_SELECT_DELETE_DATE
    
    async def admin_show_bookings_to_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, selected_date):
        query = update.callback_query
        bookings = self.db.get_bookings_for_date(selected_date)
        context.user_data['admin_delete_date'] = selected_date

        if not bookings:
            text = f"На {selected_date.strftime('%d.%m.%Y')} нет бронирований для удаления."
            keyboard = Keyboards.get_back_to_admin_keyboard()
        else:
            text = f"Выберите бронирование для удаления на {selected_date.strftime('%d.%m.%Y')}:"
            keyboard = Keyboards.get_delete_booking_keyboard(bookings)

        await query.edit_message_text(text, reply_markup=keyboard)
        return ADMIN_MAIN

    async def admin_confirm_delete_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        booking_id = int(query.data.split("_")[-1])
        
        success = self.db.delete_booking(booking_id)
        if success:
            text = "✅ Бронирование успешно удалено."
        else:
            text = "❌ Не удалось удалить бронирование."

        # Показать обновленный список
        selected_date = context.user_data.get('admin_delete_date')
        if selected_date:
            return await self.admin_show_bookings_to_delete(update, context, selected_date)
        else:
            await query.edit_message_text(text, reply_markup=Keyboards.get_back_to_admin_keyboard())
            return ADMIN_MAIN

    # --- Редактирование аудиторий ---
    async def admin_edit_room_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "✏️ Редактирование аудитории\n\nВыберите этаж:",
            reply_markup=Keyboards.get_edit_room_floor_keyboard()
        )
        # включаем флаг редактирования, чтобы отфильтровать текстовые сообщения
        context.user_data['admin_edit_in_progress'] = True
        return ADMIN_EDIT_SELECT_FLOOR
    
    async def admin_edit_select_floor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        floor = int(query.data.split("_")[-1])
        rooms = self.db.get_rooms_by_floor(floor)
        await query.edit_message_text(
            f"Этаж {floor}. Выберите аудиторию для редактирования:",
            reply_markup=Keyboards.get_edit_room_select_keyboard(rooms)
        )
        return ADMIN_EDIT_SELECT_ROOM
    
    async def admin_edit_select_room(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        room_id = int(query.data.split("_")[-1])
        context.user_data['admin_edit_room_id'] = room_id
        room = self.db.get_room_by_id(room_id)
        
        text = f"Выбрана аудитория: *{room['name']}*\. Что вы хотите изменить?"
        await query.edit_message_text(
            text,
            reply_markup=Keyboards.get_edit_field_keyboard(room_id),
            parse_mode='MarkdownV2'
        )
        return ADMIN_EDIT_SELECT_FIELD
    
    async def admin_edit_select_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        field = query.data.split("_")[-1]
        context.user_data['admin_edit_field'] = field
        
        await query.edit_message_text(f"Введите новое значение для '{field}':")
        return ADMIN_EDIT_SET_NEW_VALUE

    async def admin_edit_set_new_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # обрабатываем только если реально в процессе редактирования
        if not context.user_data.get('admin_edit_in_progress'):
            return
        new_value = update.message.text.strip()
        room_id = context.user_data['admin_edit_room_id']
        field = context.user_data['admin_edit_field']

        success = self.db.update_room_field(room_id, field, new_value)
        if success:
            text = "✅ Данные аудитории успешно обновлены."
        else:
            text = "❌ Ошибка при обновлении."
            
        await update.message.reply_text(text, reply_markup=Keyboards.get_admin_menu())
        
        # Очистка
        for key in list(context.user_data.keys()):
            if key.startswith('admin_edit_'):
                del context.user_data[key]
        context.user_data.pop('admin_edit_in_progress', None)
                
        return ADMIN_MAIN

    # Wrapper functions for fallbacks
    async def show_rooms_and_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_rooms(update, context)
        return ConversationHandler.END
        
    async def show_my_bookings_and_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_my_bookings(update, context)
        return ConversationHandler.END

    async def show_all_active_bookings_calendar_and_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_all_active_bookings_calendar(update, context)
        return ConversationHandler.END

    async def show_help_and_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_help(update, context)
        return ConversationHandler.END
        
    async def show_admin_panel_and_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Прервать бронирование и показать админ-панель."""
        for key in list(context.user_data.keys()):
            if key.startswith('booking_'):
                del context.user_data[key]
        return await self.show_admin_panel(update, context)