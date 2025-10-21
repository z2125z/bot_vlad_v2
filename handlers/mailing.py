from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config.config import Config
from services.mailing_service import MailingService

router = Router()

class MailingStates(StatesGroup):
    waiting_for_message = State()

@router.callback_query(F.data == "admin_new_mailing")
async def start_new_mailing(callback: types.CallbackQuery, state: FSMContext):
    if not callback.from_user.id in Config.ADMIN_IDS:
        await callback.answer("Нет доступа")
        return

    await state.set_state(MailingStates.waiting_for_message)
    await callback.message.edit_text(
        "Введите сообщение для рассылки:"
    )

@router.message(MailingStates.waiting_for_message)
async def process_mailing_message(message: types.Message, state: FSMContext, bot):
    if not message.from_user.id in Config.ADMIN_IDS:
        await message.answer("Нет доступа")
        await state.clear()
        return

    mailing_service = MailingService(bot)
    db = mailing_service.db
    
    # Сохраняем рассылку в базу
    mailing_id = db.save_mailing(message.text)
    
    # Отправляем рассылку
    success_count, total_count = await mailing_service.send_mailing(
        mailing_id, message.text
    )
    
    await message.answer(
        f"✅ Рассылка завершена!\n"
        f"Успешно отправлено: {success_count}/{total_count}"
    )
    
    await state.clear()