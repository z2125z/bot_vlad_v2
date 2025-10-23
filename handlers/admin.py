from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.config import Config
from database.db import Database

router = Router()
db = Database()

def is_admin(user_id: int) -> bool:
    print(f"🔍 Проверка админских прав для {user_id}, ADMIN_IDS: {Config.ADMIN_IDS}")
    return user_id in Config.ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    user_id = message.from_user.id
    print(f"🎯 Команда /admin получена от пользователя {user_id}")
    
    if not is_admin(user_id):
        print(f"❌ Пользователь {user_id} не является администратором")
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return

    print(f"✅ Пользователь {user_id} имеет доступ к админ-панели")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📨 Новая рассылка", callback_data="admin_new_mailing")],
        [InlineKeyboardButton(text="📋 История рассылок", callback_data="admin_mailing_history")]
    ])
    
    await message.answer("🛠️ Панель администратора:", reply_markup=keyboard)

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return

    user_count = db.get_user_count()
    mailings = db.get_all_mailings()
    total_mailings = len(mailings)
    
    stats_text = f"""
📊 Статистика бота:

👥 Пользователей: {user_count}
📨 Всего рассылок: {total_mailings}

Последние 5 рассылок:
"""
    
    for mailing in mailings[:5]:
        stats_text += f"\n📝 {mailing[1][:50]}... (Отправлено: {mailing[4]})"
    
    await callback.message.edit_text(stats_text)

@router.callback_query(F.data == "admin_mailing_history")
async def show_mailing_history(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return

    mailings = db.get_all_mailings()
    
    if not mailings:
        await callback.message.edit_text("История рассылок пуста.")
        return

    text = "📋 История рассылок:\n\n"
    for mailing in mailings[:10]:
        text += f"ID: {mailing[0]}\n"
        text += f"Текст: {mailing[1][:100]}...\n"
        text += f"Отправлено: {mailing[4]} пользователей\n"
        text += f"Дата: {mailing[3]}\n"
        text += "─" * 30 + "\n"
    
    await callback.message.edit_text(text)