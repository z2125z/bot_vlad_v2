from database.db import Database
from aiogram import Bot
from aiogram.types import Message
import asyncio
import html
from datetime import datetime

class MailingService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = Database()

    async def send_mailing(self, mailing_id: int, message_text: str, message_type: str = 'text', audience_type: str = 'all'):
        # Получаем пользователей по выбранной аудитории
        users = self.db.get_users_by_audience(audience_type)
        success_count = 0
        
        for user in users:
            try:
                user_id = user['user_id']  # Используем словарь благодаря row_factory
                await self.bot.send_message(
                    chat_id=user_id, 
                    text=message_text,
                    parse_mode='HTML'
                )
                self.db.record_sent_mailing(mailing_id, user_id, 'sent')
                success_count += 1
                await asyncio.sleep(0.05)  # Уменьшаем задержку для скорости
            except Exception as e:
                print(f"Failed to send message to user {user_id}: {e}")
                self.db.record_sent_mailing(mailing_id, user_id, 'failed')
        
        # Обновляем статистику рассылки
        self.db.update_mailing_stats(mailing_id, success_count)
        
        return success_count, len(users)