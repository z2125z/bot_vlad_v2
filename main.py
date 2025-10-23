import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config.config import Config
from database.db import Database

# Заменяем неправильные импорты на правильные
from handlers.user import router as user_router
from handlers.debug import router as debug_router
from admin_handlers.main_menu import router as admin_main_router
from admin_handlers.admin import router as admin_router
from admin_handlers.statistics import router as stats_router
from admin_handlers.excel_reports import router as excel_reports_router
from admin_handlers.mailing_creator import router as mailing_creator_router
from admin_handlers.templates_manager import router as templates_router
from admin_handlers.mailing_history import router as mailing_history_router
from admin_handlers.user_mailing import router as user_mailing_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def set_bot_commands(bot: Bot):
    """Установка команд бота"""
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/help", description="Получить помощь"),
        BotCommand(command="/myid", description="Узнать свой ID"),
        BotCommand(command="/admin", description="Админ-панель"),
        BotCommand(command="/debug", description="Диагностика проблем")
    ]
    await bot.set_my_commands(commands)

async def main():
    logger.info("Запуск бота...")
    
    # Проверяем конфигурацию
    try:
        Config.validate_config()
        logger.info("Конфигурация проверена успешно")
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        return
    
    # Инициализация бота и диспетчера
    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Инициализация базы данных
    db = Database()
    logger.info("База данных инициализирована")
    
    # Регистрируем роутеры в правильном порядке
    # Сначала пользовательские, потом админские
    dp.include_router(user_router)
    dp.include_router(debug_router)
    dp.include_router(admin_main_router)
    dp.include_router(admin_router)
    dp.include_router(stats_router)
    dp.include_router(excel_reports_router)
    dp.include_router(mailing_creator_router)
    dp.include_router(templates_router)
    dp.include_router(mailing_history_router)
    dp.include_router(user_mailing_router)
    
    logger.info("Все роутеры зарегистрированы")
    
    # Устанавливаем команды бота
    await set_bot_commands(bot)
    
    try:
        logger.info("Бот запущен и готов к работе")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        db.close()
        await bot.session.close()
        logger.info("Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())