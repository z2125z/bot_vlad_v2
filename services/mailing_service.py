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

    async def send_mailing(self, mailing_id: int, message_text: str, message_type: str = 'text', 
                          media_type: str = None, media_file_id: str = None, audience_type: str = 'all'):
        # Получаем пользователей по выбранной аудитории
        users = self.db.get_users_by_audience(audience_type)
        success_count = 0
        total_users = len(users)
        
        if total_users == 0:
            logger.warning(f"Нет пользователей в аудитории: {audience_type}")
            return 0, 0
        
        # Методы для отправки разных типов сообщений
        send_methods = {
            'photo': self.bot.send_photo,
            'video': self.bot.send_video,
            'document': self.bot.send_document,
            'audio': self.bot.send_audio,
            'voice': self.bot.send_voice,
            'animation': self.bot.send_animation,
            'text': self.bot.send_message
        }
        
        for i, user in enumerate(users):
            try:
                user_id = user['user_id']
                
                if media_type and media_file_id and media_type in send_methods:
                    # Отправляем медиа с текстом как подпись
                    if media_type != 'text':
                        await send_methods[media_type](
                            chat_id=user_id,
                            **{media_type: media_file_id},
                            caption=message_text,
                            parse_mode='HTML'
                        )
                    else:
                        await send_methods['text'](
                            chat_id=user_id,
                            text=message_text,
                            parse_mode='HTML'
                        )
                else:
                    # Отправляем только текст
                    await send_methods['text'](
                        chat_id=user_id,
                        text=message_text,
                        parse_mode='HTML'
                    )
                
                self.db.record_sent_mailing(mailing_id, user_id, 'sent')
                success_count += 1
                
                # Небольшая задержка чтобы не превысить лимиты Telegram
                await asyncio.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
                self.db.record_sent_mailing(mailing_id, user_id, 'failed')
        
        # Обновляем статистику рассылки
        self.db.update_mailing_stats(mailing_id, success_count)
        
        logger.info(f"Рассылка {mailing_id} завершена. Успешно: {success_count}/{total_users}")
        return success_count, total_users