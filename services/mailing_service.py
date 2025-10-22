from database.db import Database
from aiogram import Bot
from aiogram.types import Message
import asyncio
import logging

logger = logging.getLogger(__name__)

class MailingService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = Database()

    async def send_mailing(self, mailing_id: int, message_text: str, message_type: str = 'text', audience_type: str = 'all'):
        # Получаем пользователей по выбранной аудитории
        users = self.db.get_users_by_audience(audience_type)
        success_count = 0
        total_users = len(users)
        
        if total_users == 0:
            logger.warning(f"Нет пользователей в аудитории: {audience_type}")
            return 0, 0
        
        # Обновляем сообщение о прогрессе
        progress_message = None
        try:
            # Здесь можно добавить отправку сообщения о начале рассылки
            # progress_message = await self.bot.send_message(chat_id=admin_id, text=f"📨 Начинаем рассылку...\nАудитория: {total_users} пользователей")
            pass
        except:
            pass
        
        for i, user in enumerate(users):
            try:
                user_id = user['user_id']
                await self.bot.send_message(
                    chat_id=user_id, 
                    text=message_text,
                    parse_mode='HTML'
                )
                self.db.record_sent_mailing(mailing_id, user_id, 'sent')
                success_count += 1
                
                # Обновляем прогресс каждые 10 отправок
                if progress_message and i % 10 == 0:
                    progress = round((i / total_users) * 100, 1)
                    try:
                        await progress_message.edit_text(
                            f"📨 Рассылка в процессе...\n"
                            f"Прогресс: {progress}%\n"
                            f"Отправлено: {i}/{total_users}"
                        )
                    except:
                        pass
                
                await asyncio.sleep(0.05)  # Уменьшаем задержку для скорости
                
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
                self.db.record_sent_mailing(mailing_id, user_id, 'failed')
        
        # Обновляем статистику рассылки
        self.db.update_mailing_stats(mailing_id, success_count)
        
        # Закрываем сообщение о прогрессе
        if progress_message:
            try:
                await progress_message.delete()
            except:
                pass
        
        logger.info(f"Рассылка {mailing_id} завершена. Успешно: {success_count}/{total_users}")
        return success_count, total_users