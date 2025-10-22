from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext  
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.config import Config
from database.db import Database

router = Router()
db = Database()

class UserMailing(StatesGroup):
    selecting_audience = State()
    writing_message = State()
    confirmation = State()

def get_audience_selection_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Все пользователи", callback_data="audience_all"),
            InlineKeyboardButton(text="🔥 Активные (неделя)", callback_data="audience_active_week")
        ],
        [
            InlineKeyboardButton(text="🆕 Новые (сегодня)", callback_data="audience_new_today"),
            InlineKeyboardButton(text="📈 Новые (неделя)", callback_data="audience_new_week")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_refresh")
        ]
    ])

@router.callback_query(F.data == "admin_users_management")
async def user_management_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📨 Рассылка пользователям", callback_data="user_mailing_start"),
            InlineKeyboardButton(text="📊 Статистика пользователей", callback_data="stats_users")
        ],
        [
            InlineKeyboardButton(text="👥 Список пользователей", callback_data="user_list"),
            InlineKeyboardButton(text="📈 График роста", callback_data="user_growth_chart")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_refresh")
        ]
    ])
    
    await callback.message.edit_text(
        "👥 <b>Управление пользователями</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "user_mailing_start")
async def start_user_mailing(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    await state.set_state(UserMailing.selecting_audience)
    
    stats = db.get_detailed_stats()
    
    await callback.message.edit_text(
        "📨 <b>Рассылка пользователям</b>\n\n"
        f"📊 <b>Статистика аудитории:</b>\n"
        f"• Всего пользователей: {stats['total_users']}\n"
        f"• Новых сегодня: {stats['new_users_today']}\n"
        f"• Активных за неделю: {stats['active_users_week']}\n\n"
        "Выберите целевую аудиторию для рассылки:",
        reply_markup=get_audience_selection_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(UserMailing.selecting_audience, F.data.startswith("audience_"))
async def select_audience(callback: types.CallbackQuery, state: FSMContext):
    audience_type = callback.data.replace("audience_", "")
    audience_names = {
        "all": "все пользователи",
        "active_week": "активные за неделю",
        "new_today": "новые сегодня",
        "new_week": "новые за неделю"
    }
    
    await state.update_data(audience_type=audience_type)
    await state.set_state(UserMailing.writing_message)
    
    await callback.message.edit_text(
        f"🎯 <b>Целевая аудитория:</b> {audience_names.get(audience_type, audience_type)}\n\n"
        "📝 <b>Введите сообщение для рассылки:</b>\n"
        "Вы можете использовать HTML-разметку.",
        parse_mode="HTML"
    )

@router.message(UserMailing.writing_message)
async def process_user_mailing_message(message: types.Message, state: FSMContext):
    await state.update_data(message_text=message.text)
    await state.set_state(UserMailing.confirmation)
    
    data = await state.get_data()
    
    # Получаем количество пользователей в выбранной аудитории
    user_count = await get_audience_count(data['audience_type'])
    
    await message.answer(
        f"👁️ <b>Предпросмотр рассылки</b>\n\n"
        f"🎯 <b>Аудитория:</b> {data['audience_type']} ({user_count} пользователей)\n"
        f"📝 <b>Сообщение:</b>\n{data['message_text']}\n\n"
        "✅ <i>Подтвердите отправку</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_user_mailing"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_user_mailing")
            ]
        ]),
        parse_mode="HTML"
    )

async def get_audience_count(audience_type):
    """Получить количество пользователей в выбранной аудитории"""
    if audience_type == "all":
        return db.get_user_count()
    elif audience_type == "active_week":
        stats = db.get_detailed_stats()
        return stats['active_users_week']
    elif audience_type == "new_today":
        stats = db.get_detailed_stats()
        return stats['new_users_today']
    elif audience_type == "new_week":
        stats = db.get_detailed_stats()
        return stats['new_users_week']
    return 0