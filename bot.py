import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
from handlers import Handlers, ENTERING_ROOM_NUMBER, ENTERING_FULL_NAME, ENTERING_PURPOSE, ENTERING_DATE, ENTERING_START_TIME, ENTERING_END_TIME, ADMIN_PASSWORD
import config
from telegram import Update

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    # Создаем экземпляр бота
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Создаем экземпляр обработчиков
    handlers = Handlers()
    
    # Обработчик команды /start
    application.add_handler(CommandHandler("start", handlers.start))
    
    # ConversationHandler для процесса бронирования
    booking_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📅 Забронировать$"), handlers.start_booking),
            CallbackQueryHandler(handlers.start_booking, pattern="^book_room_")
        ],
        states={
            ENTERING_ROOM_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.enter_room_number)
            ],
            ENTERING_FULL_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.enter_full_name)
            ],
            ENTERING_PURPOSE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.enter_purpose)
            ],
            ENTERING_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.enter_date)
            ],
            ENTERING_START_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.enter_start_time)
            ],
            ENTERING_END_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.enter_end_time)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(handlers.handle_callback, pattern="^cancel$"),
            CallbackQueryHandler(handlers.handle_callback, pattern="^cancel_booking$")
        ]
    )
    
    # ConversationHandler для проверки пароля администратора
    admin_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🛠 Админ-панель$"), handlers.show_admin_panel)
        ],
        states={
            ADMIN_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.check_admin_password)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(handlers.handle_callback, pattern="^cancel$")
        ]
    )
    
    # Добавляем ConversationHandler'ы
    application.add_handler(booking_conv_handler)
    application.add_handler(admin_conv_handler)
    
    # Обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(handlers.show_floor_rooms, pattern="^floor_"))
    application.add_handler(CallbackQueryHandler(handlers.show_room_details, pattern="^room_"))
    application.add_handler(CallbackQueryHandler(handlers.handle_callback))
    
    # Обработчики текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text))
    
    # Запускаем бота
    logger.info("Бот запускается...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")