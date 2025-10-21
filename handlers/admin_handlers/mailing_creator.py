from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.config import Config
from services.mailing_service import MailingService

router = Router()

class MailingCreation(StatesGroup):
    waiting_for_title = State()
    waiting_for_message = State()
    waiting_for_confirmation = State()
    waiting_for_media = State()

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
            InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_mailing"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_mailing")
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_mailing")
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
        "Вы можете использовать HTML-разметку для форматирования.",
        parse_mode="HTML"
    )

@router.message(MailingCreation.waiting_for_message)
async def process_mailing_message(message: types.Message, state: FSMContext):
    await state.update_data(message_text=message.text, message_type='text')
    await state.set_state(MailingCreation.waiting_for_confirmation)
    
    data = await state.get_data()
    
    # Показываем предпросмотр
    preview_text = (
        "👁️ <b>Предпросмотр рассылки:</b>\n\n"
        f"<b>Заголовок:</b> {data['title']}\n"
        f"<b>Текст:</b>\n{data['message_text']}\n\n"
        "✅ <i>Подтвердите отправку или отредактируйте сообщение</i>"
    )
    
    await message.answer(preview_text, reply_markup=get_confirmation_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "confirm_mailing")
async def confirm_mailing(callback: types.CallbackQuery, state: FSMContext, bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    data = await state.get_data()
    mailing_service = MailingService(bot)
    
    # Сохраняем рассылку в базу
    mailing_id = mailing_service.db.save_mailing(
        data['message_text'], 
        data.get('message_type', 'text')
    )
    
    # Отправляем рассылку
    success_count, total_count = await mailing_service.send_mailing(
        mailing_id, 
        data['message_text']
    )
    
    await callback.message.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📨 <b>Заголовок:</b> {data['title']}\n"
        f"✅ <b>Успешно отправлено:</b> {success_count}/{total_count}\n"
        f"📊 <b>Процент доставки:</b> {round((success_count/total_count)*100, 2) if total_count > 0 else 0}%",
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