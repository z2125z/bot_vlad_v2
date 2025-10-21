from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import Database
from config.config import Config
from datetime import datetime

router = Router()
db = Database()

def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS

def get_stats_keyboard():
    """Клавиатура для разной статистики"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 Общая статистика", callback_data="stats_general"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="stats_users")
        ],
        [
            InlineKeyboardButton(text="📊 Активность", callback_data="stats_activity"),
            InlineKeyboardButton(text="📨 Рассылки", callback_data="stats_mailings")
        ],
        [
            InlineKeyboardButton(text="📈 Графики", callback_data="stats_charts"),
            InlineKeyboardButton(text="🎯 Сегменты", callback_data="stats_segments")
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
        f"🔥 <b>Активных за сегодня:</b> {stats['active_users_today']}\n"
        f"🔥 <b>Активных за неделю:</b> {stats['active_users_week']}\n"
        f"📨 <b>Всего рассылок:</b> {stats['total_mailings']}\n"
        f"✉️ <b>Отправлено сообщений:</b> {stats['total_sent_messages']}\n"
        f"✅ <b>Успешных доставок:</b> {stats['successful_deliveries']}\n"
        f"❌ <b>Неудачных отправок:</b> {stats['failed_deliveries']}\n"
        f"📊 <b>Средняя активность на пользователя:</b> {stats['avg_activity_per_user']}\n\n"
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
    
    growth_text = "\n".join([f"• {date}: +{count}" for date, count in growth_data[-5:]])  # Последние 5 дней
    
    text = (
        "👥 <b>Статистика пользователей</b>\n\n"
        f"📊 <b>Всего пользователей:</b> {stats['total_users']}\n"
        f"🆕 <b>Новых сегодня:</b> {stats['new_users_today']}\n"
        f"📈 <b>Новых за неделю:</b> {stats['new_users_week']}\n"
        f"🗓️ <b>Новых за месяц:</b> {stats['new_users_month']}\n\n"
        "📊 <b>Рост пользователей (последние 5 дней):</b>\n"
        f"{growth_text if growth_text else '• Нет данных'}"
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

@router.callback_query(F.data == "stats_activity")
async def show_activity_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    stats = db.get_detailed_stats()
    activity_data = db.get_activity_data(7)  # Активность за 7 дней
    top_users = db.get_top_active_users(5)  # Топ 5 активных пользователей
    
    activity_text = "\n".join([f"• {date}: {count} действий" for date, count in activity_data[-5:]])
    
    top_users_text = "\n".join([f"• {user[2] or user[3] or user[1]}: {user[4]} действий" for user in top_users])
    
    text = (
        "📊 <b>Статистика активности</b>\n\n"
        f"🔥 <b>Активных сегодня:</b> {stats['active_users_today']}\n"
        f"🔥 <b>Активных за неделю:</b> {stats['active_users_week']}\n"
        f"📈 <b>Средняя активность на пользователя:</b> {stats['avg_activity_per_user']}\n\n"
        "📊 <b>Активность по дням (последние 5 дней):</b>\n"
        f"{activity_text if activity_text else '• Нет данных'}\n\n"
        "🏆 <b>Топ-5 активных пользователей:</b>\n"
        f"{top_users_text if top_users_text else '• Нет данных'}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_activity")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_detailed_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "stats_mailings")
async def show_mailings_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    stats = db.get_detailed_stats()
    mailing_performance = db.get_mailing_performance()
    
    mailings_text = ""
    for mailing in mailing_performance[:5]:  # Последние 5 рассылок
        mailings_text += f"• {mailing[1]}: {mailing[3]} отправок, {mailing[4]} доставок ({mailing[5]}%)\n"
    
    text = (
        "📨 <b>Статистика рассылок</b>\n\n"
        f"📊 <b>Всего рассылок:</b> {stats['total_mailings']}\n"
        f"✉️ <b>Отправлено сообщений:</b> {stats['total_sent_messages']}\n"
        f"✅ <b>Успешных доставок:</b> {stats['successful_deliveries']}\n"
        f"❌ <b>Неудачных отправок:</b> {stats['failed_deliveries']}\n"
        f"📈 <b>Общий процент доставки:</b> {round((stats['successful_deliveries']/(stats['successful_deliveries'] + stats['failed_deliveries']))*100, 2) if (stats['successful_deliveries'] + stats['failed_deliveries']) > 0 else 0}%\n\n"
        "📊 <b>Последние 5 рассылок:</b>\n"
        f"{mailings_text if mailings_text else '• Нет данных'}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_mailings")],
        [InlineKeyboardButton(text="📨 Создать рассылку", callback_data="admin_create_mailing")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_detailed_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "stats_segments")
async def show_segments_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    segments = db.get_user_segments()
    
    text = (
        "🎯 <b>Сегменты пользователей</b>\n\n"
        f"🆕 <b>Новые пользователи (7 дней):</b> {segments['new_users']}\n"
        f"🔥 <b>Активные пользователи (7 дней):</b> {segments['active_users']}\n"
        f"💤 <b>Неактивные пользователи (30+ дней):</b> {segments['inactive_users']}\n"
        f"👤 <b>С username:</b> {segments['users_with_username']}\n"
        f"👥 <b>Без username:</b> {segments['users_without_username']}\n\n"
        "💡 <i>Используйте эти сегменты для таргетированных рассылок</i>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📨 Создать сегментную рассылку", callback_data="user_mailing_start")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_detailed_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "stats_charts")
async def show_charts_info(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    text = (
        "📈 <b>Графики и аналитика</b>\n\n"
        "📊 <b>Доступные графики:</b>\n"
        "• Рост пользователей по дням\n"
        "• Активность пользователей\n"
        "• Эффективность рассылок\n"
        "• Retention пользователей\n\n"
        "💡 <i>Для просмотра детальных графиков используйте веб-панель аналитики</i>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_charts")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_detailed_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# Обработчики для разных периодов
@router.callback_query(F.data.startswith("stats_users_"))
async def show_users_stats_period(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    days = int(callback.data.split("_")[-1])
    growth_data = db.get_user_growth_data(days)
    
    growth_text = "\n".join([f"• {date}: +{count}" for date, count in growth_data])
    
    text = (
        f"👥 <b>Рост пользователей за {days} дней</b>\n\n"
        f"{growth_text if growth_text else '• Нет данных за выбранный период'}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="7 дней", callback_data="stats_users_7"),
            InlineKeyboardButton(text="30 дней", callback_data="stats_users_30")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="stats_users")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()