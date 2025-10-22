import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config.config import Config
from database.db import Database
from handlers import all_routers

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
        BotCommand(command="/debug", description="Диагностика проблем")  # Добавляем диагностическую команду
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
    
    # Регистрация всех роутеров
    for router in all_routers:
        dp.include_router(router)
        logger.info(f"Роутер {router.name} зарегистрирован")
    
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