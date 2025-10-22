from aiogram import types
from aiogram.types import InlineKeyboardMarkup

async def safe_edit_message(callback: types.CallbackQuery, text: str, keyboard: InlineKeyboardMarkup = None):
    """Безопасное редактирование сообщения с обработкой ошибки 'message not modified'"""
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        return True
    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer()
            return True
        else:
            print(f"Ошибка при редактировании сообщения: {e}")
            await callback.answer("Произошла ошибка", show_alert=True)
            return False