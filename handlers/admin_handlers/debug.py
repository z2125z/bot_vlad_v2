from aiogram import Router, types
from aiogram.filters import Command
from config.config import Config

router = Router()

@router.message(Command("debug"))
async def debug_command(message: types.Message):
    """Команда для диагностики проблем"""
    user_id = message.from_user.id
    is_user_admin = user_id in Config.ADMIN_IDS
    
    debug_info = (
        f"🔧 <b>Диагностическая информация</b>\n\n"
        f"👤 <b>Ваш ID:</b> <code>{user_id}</code>\n"
        f"👑 <b>Статус администратора:</b> {'✅ Да' if is_user_admin else '❌ Нет'}\n"
        f"📋 <b>ADMIN_IDS из config:</b> {Config.ADMIN_IDS}\n"
        f"🔍 <b>Тип ADMIN_IDS:</b> {type(Config.ADMIN_IDS)}\n"
        f"🔍 <b>Тип вашего ID:</b> {type(user_id)}\n"
    )
    
    await message.answer(debug_info, parse_mode="HTML")