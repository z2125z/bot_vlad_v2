import asyncio
import logging
from aiogram import Bot, Dispatcher
from config.config import Config
from database.db import Database
from handlers import user, admin, mailing

async def main():
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Инициализация бота и диспетчера
    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Инициализация базы данных
    db = Database()
    
    # Регистрация роутеров
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(mailing.router)
    
    try:
        await dp.start_polling(bot)
    finally:
        db.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())