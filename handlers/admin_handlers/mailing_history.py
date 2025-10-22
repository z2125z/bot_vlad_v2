from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import Database
from config.config import Config

router = Router()
db = Database()

def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS

async def safe_edit_message(callback: types.CallbackQuery, text: str, keyboard: InlineKeyboardMarkup = None):
    """Безопасное редактирование сообщения"""
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer()
        else:
            print(f"Ошибка при редактировании сообщения: {e}")
            await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "admin_mailing_history")
async def show_mailing_history(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    mailings = db.get_all_mailings()
    
    if not mailings:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📨 Создать первую рассылку", callback_data="admin_create_mailing")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_refresh")]
        ])
        
        await safe_edit_message(
            callback,
            "📋 <b>История рассылок</b>\n\n"
            "Рассылок пока не было.\n"
            "Создайте первую рассылку!",
            keyboard
        )
        return

    text = "📋 <b>История рассылок</b>\n\n"
    
    for mailing in mailings[:10]:  # Показываем последние 10 рассылок
        delivery_rate = round((mailing['delivered_count'] / mailing['sent_count']) * 100, 2) if mailing['sent_count'] > 0 else 0
        
        text += f"📨 <b>ID {mailing['id']}</b>\n"
        text += f"• <b>Заголовок:</b> {mailing['title'] or 'Без заголовка'}\n"
        text += f"• <b>Тип:</b> {mailing['message_type']}\n"
        text += f"• <b>Аудитория:</b> {mailing['audience_type']}\n"
        text += f"• <b>Отправлено:</b> {mailing['sent_count']} сообщений\n"
        text += f"• <b>Доставлено:</b> {mailing['delivered_count']} сообщений\n"
        text += f"• <b>Эффективность:</b> {delivery_rate}%\n"
        text += f"• <b>Дата:</b> {mailing['created_at'][:16]}\n"
        text += "─" * 30 + "\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Excel отчет по рассылкам", callback_data="admin_excel_report")],
        [InlineKeyboardButton(text="📨 Новая рассылка", callback_data="admin_create_mailing")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_refresh")]
    ])
    
    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

@router.callback_query(F.data == "admin_mailing_stats")
async def show_mailing_detailed_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    mailing_performance = db.get_mailing_performance()
    
    if not mailing_performance:
        await safe_edit_message(
            callback,
            "📊 <b>Статистика рассылок</b>\n\n"
            "Нет данных о рассылках.",
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_mailing_history")]
            ])
        )
        return

    text = "📊 <b>Детальная статистика рассылок</b>\n\n"
    
    total_sent = 0
    total_delivered = 0
    
    for perf in mailing_performance[:10]:  # Последние 10 рассылок
        text += f"📨 <b>{perf['title']}</b>\n"
        text += f"• Отправлено: {perf['sent_count']}\n"
        text += f"• Доставлено: {perf['delivered_count']}\n"
        text += f"• Эффективность: {perf['delivery_rate']}%\n"
        text += f"• Дата: {perf['created_at'][:16]}\n"
        text += "─" * 30 + "\n"
        
        total_sent += perf['sent_count']
        total_delivered += perf['delivered_count']
    
    overall_rate = round((total_delivered / total_sent) * 100, 2) if total_sent > 0 else 0
    
    text += f"\n<b>Общая статистика:</b>\n"
    text += f"• Всего отправлено: {total_sent}\n"
    text += f"• Всего доставлено: {total_delivered}\n"
    text += f"• Общая эффективность: {overall_rate}%"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Excel отчет", callback_data="admin_excel_report")],
        [InlineKeyboardButton(text="🔙 К истории рассылок", callback_data="admin_mailing_history")]
    ])
    
    await safe_edit_message(callback, text, keyboard)
    await callback.answer()