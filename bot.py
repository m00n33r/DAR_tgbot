#!/usr/bin/env python3
"""
DAR Telegram Bot - Бот для бронирования аудиторий
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from handlers import (
    Handlers,
    CHOOSING_FLOOR,
    CHOOSING_ROOM,
    ENTERING_FULL_NAME,
    ENTERING_PURPOSE,
    SELECTING_DATE,
    ENTERING_START_TIME,
    ENTERING_END_TIME,
    CONFIRMING_BOOKING,
    ADMIN_PASSWORD,
    ENTERING_MANUAL_DATE,
    # Admin states
    ADMIN_MAIN, ADMIN_ADDING_ROOM_FLOOR, ADMIN_ADDING_ROOM_NUMBER,
    ADMIN_ADDING_ROOM_NAME, ADMIN_ADDING_ROOM_CAPACITY, ADMIN_ADDING_ROOM_EQUIPMENT,
    ADMIN_ADDING_ROOM_DESCRIPTION, ADMIN_SELECT_CONTACTS_DATE, ADMIN_SELECT_DELETE_DATE,
    ADMIN_EDIT_SELECT_FLOOR, ADMIN_EDIT_SELECT_ROOM, ADMIN_EDIT_SELECT_FIELD, ADMIN_EDIT_SET_NEW_VALUE
)
import config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция"""
    # Создаем приложение
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Создаем ЕДИНЫЙ экземпляр обработчиков
    handlers = Handlers()

    # Вложенный ConversationHandler для админ-панели
    admin_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🛠 Админ-панель$'), handlers.show_admin_panel)],
        states={
            ADMIN_MAIN: [
                CallbackQueryHandler(handlers.admin_add_room_start, pattern='^admin_add_room$'),
                CallbackQueryHandler(handlers.admin_contacts_start, pattern='^admin_user_contacts$'),
                CallbackQueryHandler(handlers.admin_delete_booking_start, pattern='^admin_booking_delete_menu$'),
                CallbackQueryHandler(handlers.admin_edit_room_start, pattern='^admin_edit_rooms$'),
                CallbackQueryHandler(handlers.admin_confirm_delete_booking, pattern='^admin_confirm_delete_')
            ],
            ADMIN_ADDING_ROOM_FLOOR: [CallbackQueryHandler(handlers.admin_add_room_get_floor, pattern='^admin_add_floor_')],
            ADMIN_ADDING_ROOM_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.admin_add_room_get_number)],
            ADMIN_ADDING_ROOM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.admin_add_room_get_name)],
            ADMIN_ADDING_ROOM_CAPACITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.admin_add_room_get_capacity)],
            ADMIN_ADDING_ROOM_EQUIPMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.admin_add_room_get_equipment)],
            ADMIN_ADDING_ROOM_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.admin_add_room_finish)],
            ADMIN_SELECT_CONTACTS_DATE: [CallbackQueryHandler(handlers.handle_calendar_callback, pattern='^cal_')],
            ADMIN_SELECT_DELETE_DATE: [CallbackQueryHandler(handlers.handle_calendar_callback, pattern='^cal_')],
            ADMIN_EDIT_SELECT_FLOOR: [CallbackQueryHandler(handlers.admin_edit_select_floor, pattern='^admin_edit_floor_')],
            ADMIN_EDIT_SELECT_ROOM: [CallbackQueryHandler(handlers.admin_edit_select_room, pattern='^admin_edit_room_')],
            ADMIN_EDIT_SELECT_FIELD: [CallbackQueryHandler(handlers.admin_edit_select_field, pattern='^admin_edit_field_')],
            ADMIN_EDIT_SET_NEW_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.admin_edit_set_new_value)],
        },
        fallbacks=[
            CallbackQueryHandler(handlers.exit_admin_panel, pattern='^exit_admin$'),
            CallbackQueryHandler(handlers.show_admin_panel, pattern='^back_to_admin$'),
            CallbackQueryHandler(handlers.show_admin_panel, pattern='^cal_cancel$'),
            MessageHandler(filters.Regex('^🛠 Админ-панель$'), handlers.show_admin_panel),
        ],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END
        }
    )

    # ConversationHandler для процесса бронирования
    booking_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^📅 Забронировать$'), handlers.start_booking),
            CallbackQueryHandler(handlers.start_booking_from_room_details, pattern='^book_room_details_')
        ],
        states={
            CHOOSING_FLOOR: [CallbackQueryHandler(handlers.show_floor_rooms_for_booking, pattern='^book_floor_')],
            CHOOSING_ROOM: [CallbackQueryHandler(handlers.start_booking_from_room, pattern='^book_room_')],
            ENTERING_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.enter_full_name)],
            ENTERING_PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.enter_purpose)],
            SELECTING_DATE: [
                CallbackQueryHandler(handlers.request_manual_date, pattern='^cal_manual$'),
                CallbackQueryHandler(handlers.handle_calendar_callback, pattern='^cal_')
            ],
            ENTERING_MANUAL_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_manual_date_input)],
            ENTERING_START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.enter_start_time)],
            ENTERING_END_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.enter_end_time)],
            CONFIRMING_BOOKING: [
                CallbackQueryHandler(handlers.confirm_booking, pattern='^confirm_booking$'),
                CallbackQueryHandler(handlers.rewrite_booking, pattern='^rewrite_booking$'),
            ],
            ADMIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.check_admin_password)],
        },
        fallbacks=[
            CallbackQueryHandler(handlers.cancel_booking, pattern='^cancel_booking$'),
            CallbackQueryHandler(handlers.cancel_booking, pattern='^cal_cancel$'),
            CommandHandler('cancel', handlers.cancel_booking),
            MessageHandler(filters.Regex('^🗂 Аудитории$'), handlers.show_rooms_and_cancel),
            MessageHandler(filters.Regex('^📅 Мои брони$'), handlers.show_my_bookings_and_cancel),
            MessageHandler(filters.Regex('^📋 Активные брони$'), handlers.show_all_active_bookings_calendar_and_cancel),
            MessageHandler(filters.Regex('^ℹ️ Помощь$'), handlers.show_help_and_cancel),
            MessageHandler(filters.Regex('^🛠 Админ-панель$'), handlers.show_admin_panel_and_cancel),
        ],
    )

    application.add_handler(booking_conv_handler)
    
    # Обычные обработчики
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(MessageHandler(filters.Regex('^🗂 Аудитории$'), handlers.show_rooms))
    application.add_handler(MessageHandler(filters.Regex('^📅 Мои брони$'), handlers.show_my_bookings))
    application.add_handler(MessageHandler(filters.Regex('^📋 Активные брони$'), handlers.show_all_active_bookings_calendar))
    application.add_handler(MessageHandler(filters.Regex('^ℹ️ Помощь$'), handlers.show_help))
    
    # ConversationHandler админ-панели теперь основной способ входа
    application.add_handler(admin_conv_handler)
    
    # Важно: этот обработчик должен идти после ConversationHandler, чтобы не перехватывать его callback'и
    application.add_handler(CallbackQueryHandler(handlers.handle_other_callbacks))

    # Запуск бота
    logger.info("🚀 DAR Telegram Bot запускается...")
    logger.info("✅ Бот готов к работе!")
    
    application.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")