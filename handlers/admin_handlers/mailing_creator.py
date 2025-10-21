from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.config import Config
from services.mailing_service import MailingService
import html
from datetime import datetime

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS

class MailingCreation(StatesGroup):
    waiting_for_title = State()
    waiting_for_message = State()
    waiting_for_confirmation = State()
    waiting_for_audience = State()

def get_mailing_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Текст", callback_data="mailing_type_text"),
            InlineKeyboardButton(text="🖼️ Текст + Фото", callback_data="mailing_type_photo")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_refresh")
        ]
    ])

def get_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить рассылку", callback_data="confirm_mailing"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_mailing")
        ],
        [
            InlineKeyboardButton(text="🎯 Изменить аудиторию", callback_data="change_audience")
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_mailing")
        ]
    ])

def get_audience_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Все пользователи", callback_data="audience_all"),
            InlineKeyboardButton(text="🔥 Активные", callback_data="audience_active_week")
        ],
        [
            InlineKeyboardButton(text="🆕 Новые (сегодня)", callback_data="audience_new_today"),
            InlineKeyboardButton(text="📈 Новые (неделя)", callback_data="audience_new_week")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_create_mailing")
        ]
    ])

@router.callback_query(F.data == "admin_create_mailing")
async def start_mailing_creation(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    await state.set_state(MailingCreation.waiting_for_title)
    await callback.message.edit_text(
        "📝 <b>Создание новой рассылки</b>\n\n"
        "Введите заголовок для рассылки:",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(MailingCreation.waiting_for_title)
async def process_mailing_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(MailingCreation.waiting_for_message)
    
    await message.answer(
        "📝 <b>Введите текст рассылки:</b>\n\n"
        "Вы можете использовать HTML-разметку для форматирования.\n"
        "Примеры тегов:\n"
        "• <code>&lt;b&gt;жирный текст&lt;/b&gt;</code>\n"
        "• <code>&lt;i&gt;курсив&lt;/i&gt;</code>\n"
        "• <code>&lt;u&gt;подчеркивание&lt;/u&gt;</code>\n"
        "• <code>&lt;a href='URL'&gt;ссылка&lt;/a&gt;</code>",
        parse_mode="HTML"
    )

@router.message(MailingCreation.waiting_for_message)
async def process_mailing_message(message: types.Message, state: FSMContext):
    await state.update_data(message_text=message.html_text, message_type='text')
    await state.set_state(MailingCreation.waiting_for_audience)
    
    data = await state.get_data()
    
    # Показываем предпросмотр и выбираем аудиторию
    preview_text = (
        "👁️ <b>Предпросмотр рассылки:</b>\n\n"
        f"<b>Заголовок:</b> {data['title']}\n"
        f"<b>Текст:</b>\n{data['message_text'][:500]}{'...' if len(data['message_text']) > 500 else ''}\n\n"
        "🎯 <b>Теперь выберите целевую аудиторию:</b>"
    )
    
    await message.answer(preview_text, reply_markup=get_audience_keyboard(), parse_mode="HTML")

@router.callback_query(MailingCreation.waiting_for_audience, F.data.startswith("audience_"))
async def select_audience(callback: types.CallbackQuery, state: FSMContext):
    audience_type = callback.data.replace("audience_", "")
    audience_names = {
        "all": "👥 Все пользователи",
        "active_week": "🔥 Активные за неделю", 
        "new_today": "🆕 Новые сегодня",
        "new_week": "📈 Новые за неделю"
    }
    
    audience_count = await get_audience_count(audience_type)
    
    await state.update_data(audience_type=audience_type)
    await state.set_state(MailingCreation.waiting_for_confirmation)
    
    data = await state.get_data()
    
    # Финальный предпросмотр с подтверждением
    preview_text = (
        "👁️ <b>Предпросмотр рассылки:</b>\n\n"
        f"<b>Заголовок:</b> {data['title']}\n"
        f"<b>Аудитория:</b> {audience_names.get(audience_type)} ({audience_count} пользователей)\n"
        f"<b>Текст:</b>\n{data['message_text'][:500]}{'...' if len(data['message_text']) > 500 else ''}\n\n"
        "✅ <b>Подтвердите отправку или отредактируйте сообщение</b>"
    )
    
    await callback.message.edit_text(preview_text, reply_markup=get_confirmation_keyboard(), parse_mode="HTML")
    await callback.answer()

async def get_audience_count(audience_type):
    """Получить количество пользователей в выбранной аудитории"""
    from database.db import Database
    db = Database()
    
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

@router.callback_query(F.data == "confirm_mailing")
async def confirm_mailing(callback: types.CallbackQuery, state: FSMContext, bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    data = await state.get_data()
    mailing_service = MailingService(bot)
    
    # Показываем уведомление о начале рассылки
    await callback.message.edit_text(
        "📨 <b>Рассылка запущена...</b>\n\n"
        "⏳ Отправляем сообщения пользователям...",
        parse_mode="HTML"
    )
    
    # Сохраняем рассылку в базу
    mailing_id = mailing_service.db.save_mailing(
        data['title'],
        data['message_text'], 
        data.get('message_type', 'text'),
        data.get('audience_type', 'all')
    )
    
    # Отправляем рассылку
    success_count, total_count = await mailing_service.send_mailing(
        mailing_id, 
        data['message_text'],
        data.get('message_type', 'text'),
        data.get('audience_type', 'all')
    )
    
    delivery_rate = round((success_count/total_count)*100, 2) if total_count > 0 else 0
    
    await callback.message.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📨 <b>Заголовок:</b> {data['title']}\n"
        f"🎯 <b>Аудитория:</b> {data.get('audience_type', 'all')}\n"
        f"✅ <b>Успешно отправлено:</b> {success_count}/{total_count}\n"
        f"📊 <b>Процент доставки:</b> {delivery_rate}%\n\n"
        f"📅 <b>Время отправки:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика рассылок", callback_data="stats_mailings")],
            [InlineKeyboardButton(text="📨 Новая рассылка", callback_data="admin_create_mailing")],
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_refresh")]
        ]),
        parse_mode="HTML"
    )
    
    await state.clear()

@router.callback_query(F.data == "edit_mailing")
async def edit_mailing(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MailingCreation.waiting_for_message)
    await callback.message.edit_text(
        "✏️ <b>Редактирование рассылки</b>\n\n"
        "Введите новый текст рассылки:",
        parse_mode="HTML"
    )

@router.callback_query(F.data == "change_audience")
async def change_audience(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MailingCreation.waiting_for_audience)
    await callback.message.edit_text(
        "🎯 <b>Выбор аудитории</b>\n\n"
        "Выберите целевую аудиторию для рассылки:",
        reply_markup=get_audience_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "cancel_mailing")
async def cancel_mailing(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Создание рассылки отменено</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_refresh")]
        ]),
        parse_mode="HTML"
    )