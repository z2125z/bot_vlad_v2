from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.config import Config
from database.db import Database
from datetime import datetime, timedelta
import asyncio

router = Router()
db = Database()

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
            InlineKeyboardButton(text="📈 Excel отчет", callback_data="admin_excel_report"),
            InlineKeyboardButton(text="🔄 Обновить данные", callback_data="admin_refresh")
        ]
    ])
    return keyboard

async def get_dashboard_stats():
    """Получить данные для дашборда"""
    stats = db.get_detailed_stats()
    
    # Получаем данные за последние 7 дней для графика активности
    activity_data = db.get_activity_data(7)
    user_growth = db.get_user_growth_data(7)
    
    # Формируем текст дашборда
    dashboard_text = (
        "📊 <b>Дашборд активности</b>\n\n"
        f"👥 <b>Всего пользователей:</b> {stats['total_users']}\n"
        f"🆕 <b>Новых за 24ч:</b> {stats['new_users_today']}\n"
        f"🔥 <b>Активных за 24ч:</b> {stats['active_users_today']}\n\n"
        
        f"📨 <b>Рассылки:</b> {stats['total_mailings']}\n"
        f"✉️ <b>Отправлено сообщений:</b> {stats['total_sent_messages']}\n"
        f"📈 <b>Доставка:</b> {round((stats['successful_deliveries']/(stats['successful_deliveries'] + stats['failed_deliveries']))*100, 2) if (stats['successful_deliveries'] + stats['failed_deliveries']) > 0 else 0}%\n\n"
    )
    
    # Добавляем график активности (текстовый)
    if activity_data:
        dashboard_text += "📈 <b>Активность за 7 дней:</b>\n"
        for date, count in activity_data[-5:]:  # Последние 5 дней
            bar = "█" * min(count // 3, 10)  # Простой текстовый график
            dashboard_text += f"• {date}: {bar} {count}\n"
    
    dashboard_text += f"\n🕒 <b>Обновлено:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    
    return dashboard_text

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return

    dashboard_text = await get_dashboard_stats()
    
    await message.answer(
        dashboard_text,
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_refresh")
async def refresh_admin_panel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    dashboard_text = await get_dashboard_stats()
    
    await callback.message.edit_text(
        dashboard_text,
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer("✅ Данные обновлены")