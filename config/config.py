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
            print("⚠️  ADMIN_IDS не установлены - админ-панель будет недоступна")
        return True