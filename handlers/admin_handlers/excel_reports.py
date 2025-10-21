from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from config.config import Config
from services.excel_report_service import ExcelReportService
import os
import asyncio
from datetime import datetime  # ДОБАВИТЬ ИМПОРТ

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS

async def safe_edit_message(callback: types.CallbackQuery, text: str, keyboard: InlineKeyboardMarkup = None):
    """Безопасное редактирование сообщения с обработкой ошибки 'message not modified'"""
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer()
        else:
            print(f"Ошибка при редактировании сообщения: {e}")
            await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "admin_excel_report")
async def generate_excel_report(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    # Показываем сообщение о начале генерации
    await safe_edit_message(
        callback,
        "📊 <b>Генерация Excel отчета</b>\n\n"
        "⏳ Собираем данные и формируем отчет...\n"
        "Это может занять несколько секунд.",
        None
    )

    # Генерируем отчет в отдельном потоке
    report_service = ExcelReportService()
    
    try:
        # Запускаем генерацию отчета
        filename = await asyncio.get_event_loop().run_in_executor(
            None, report_service.generate_comprehensive_report
        )
        
        if filename and os.path.exists(filename):
            # Очищаем старые отчеты
            report_service.cleanup_old_reports(keep_last=3)
            
            # Отправляем файл
            file = FSInputFile(filename)
            await callback.message.answer_document(
                document=file,
                caption=(
                    "📊 <b>Полный отчет по боту</b>\n\n"
                    "Файл содержит:\n"
                    "• Общую статистику\n"
                    "• Данные пользователей\n"
                    "• Активность и аналитику\n"
                    "• Статистику рассылок\n"
                    "• Сегменты пользователей\n\n"
                    f"📅 Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                ),
                parse_mode="HTML"
            )
            
            # Удаляем временный файл после отправки
            try:
                os.remove(filename)
            except:
                pass
                
            await callback.answer("✅ Отчет успешно сгенерирован")
        else:
            await safe_edit_message(
                callback,
                "❌ <b>Ошибка генерации отчета</b>\n\n"
                "Не удалось создать Excel файл. Попробуйте позже.",
                None
            )
            await callback.answer("❌ Ошибка генерации")
            
    except Exception as e:
        await safe_edit_message(
            callback,
            f"❌ <b>Ошибка генерации отчета</b>\n\n"
            f"Произошла ошибка: {str(e)}",
            None
        )
        await callback.answer("❌ Ошибка генерации")