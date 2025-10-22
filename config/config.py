import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot_database.db')
    
    @classmethod
    def validate_config(cls):
        """Проверка корректности конфигурации"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        if not cls.ADMIN_IDS:
            print("⚠️  WARNING: ADMIN_IDS не установлены - админ-панель будет недоступна")
        else:
            print(f"✅ ADMIN_IDS: {cls.ADMIN_IDS}")
        return True

    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Проверка является ли пользователь администратором"""
        is_admin = user_id in cls.ADMIN_IDS
        print(f"🔍 Проверка прав доступа: User {user_id} is admin: {is_admin}")
        return is_admin