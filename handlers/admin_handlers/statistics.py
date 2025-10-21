from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import Database
from config.config import Config

router = Router()
db = Database()

def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS

def get_stats_keyboard():
    """Клавиатура для разной статистики"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 Общая статистика", callback_data="stats_general"),
            InlineKeyboardButton(text="👥 Статистика пользователей", callback_data="stats_users")
        ],
        [
            InlineKeyboardButton(text="📊 Активность", callback_data="stats_activity"),
            InlineKeyboardButton(text="📨 Статистика рассылок", callback_data="stats_mailings")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_refresh")
        ]
    ])

@router.callback_query(F.data == "admin_detailed_stats")
async def show_detailed_stats_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    await callback.message.edit_text(
        "📊 <b>Расширенная статистика</b>\n\n"
        "Выберите тип статистики для просмотра:",
        reply_markup=get_stats_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "stats_general")
async def show_general_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    stats = db.get_detailed_stats()
    
    text = (
        "📊 <b>Общая статистика бота</b>\n\n"
        f"👥 <b>Всего пользователей:</b> {stats['total_users']}\n"
        f"🆕 <b>Новых сегодня:</b> {stats['new_users_today']}\n"
        f"📈 <b>Новых за неделю:</b> {stats['new_users_week']}\n"
        f"🗓️ <b>Новых за месяц:</b> {stats['new_users_month']}\n\n"
        f"🔥 <b>Активных пользователей (неделя):</b> {stats['active_users_week']}\n"
        f"📨 <b>Всего рассылок:</b> {stats['total_mailings']}\n"
        f"✉️ <b>Отправлено сообщений:</b> {stats['total_sent_messages']}\n\n"
        f"📅 <b>Дата обновления:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_general")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_detailed_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "stats_users")
async def show_users_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    stats = db.get_detailed_stats()
    growth_data = db.get_user_growth_data(7)  # Рост за 7 дней
    
    growth_text = "\n".join([f"{date}: +{count}" for date, count in growth_data[-5:]])  # Последние 5 дней
    
    text = (
        "👥 <b>Статистика пользователей</b>\n\n"
        f"📊 <b>Всего пользователей:</b> {stats['total_users']}\n"
        f"🆕 <b>Новых сегодня:</b> {stats['new_users_today']}\n"
        f"📈 <b>Новых за неделю:</b> {stats['new_users_week']}\n"
        f"🗓️ <b>Новых за месяц:</b> {stats['new_users_month']}\n\n"
        "📊 <b>Рост пользователей (последние 5 дней):</b>\n"
        f"{growth_text if growth_text else 'Нет данных'}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="7 дней", callback_data="stats_users_7"),
            InlineKeyboardButton(text="30 дней", callback_data="stats_users_30")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_detailed_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()