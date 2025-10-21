from database.db import Database
from aiogram import Bot
from aiogram.types import Message
import asyncio

class MailingService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = Database()

    async def send_mailing(self, mailing_id: int, message_text: str, message_type: str = 'text'):
        users = self.db.get_all_users()
        success_count = 0
        
        for user in users:
            try:
                user_id = user[1]  # user_id находится во второй колонке
                await self.bot.send_message(chat_id=user_id, text=message_text)
                self.db.record_sent_mailing(mailing_id, user_id)
                success_count += 1
                await asyncio.sleep(0.1)  # Задержка чтобы не превысить лимиты Telegram
            except Exception as e:
                print(f"Failed to send message to user {user_id}: {e}")
        
        return success_count, len(users)