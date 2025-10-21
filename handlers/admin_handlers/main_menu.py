from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.config import Config

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS

def get_admin_main_menu():
    """Главное меню админа"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Расширенная статистика", callback_data="admin_detailed_stats"),
            InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users_management")
        ],
        [
            InlineKeyboardButton(text="📨 Создать рассылку", callback_data="admin_create_mailing"),
            InlineKeyboardButton(text="📋 История рассылок", callback_data="admin_mailing_history")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить данные", callback_data="admin_refresh")
        ]
    ])
    return keyboard

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    print(f"Команда /admin получена от пользователя {message.from_user.id}")  # Для отладки
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return

    await message.answer(
        "👨‍💻 <b>Админ-панель</b>\n\n"
        "Выберите раздел для управления ботом:",
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_refresh")
async def refresh_admin_panel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    await callback.message.edit_text(
        "👨‍💻 <b>Админ-панель</b>\n\n"
        "Выберите раздел для управления ботом:",
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer("✅ Данные обновлены")