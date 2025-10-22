from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext  # ДОБАВИТЬ ЭТОТ ИМПОРТ
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import Database
from config.config import Config
from services.mailing_service import MailingService
from datetime import datetime  # ДОБАВИТЬ ЭТОТ ИМПОРТ

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

def get_templates_keyboard(templates, page=0, templates_per_page=5):
    """Создает клавиатуру для списка шаблонов"""
    start_idx = page * templates_per_page
    end_idx = start_idx + templates_per_page
    current_templates = templates[start_idx:end_idx]
    
    buttons = []
    for template in current_templates:
        media_icon = "🖼️" if template['media_type'] else "📝"
        button_text = f"{media_icon} {template['title'][:30]}{'...' if len(template['title']) > 30 else ''}"
        buttons.append([InlineKeyboardButton(
            text=button_text, 
            callback_data=f"template_{template['id']}"
        )])
    
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"templates_page_{page-1}"))
    
    if end_idx < len(templates):
        navigation_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"templates_page_{page+1}"))
    
    if navigation_buttons:
        buttons.append(navigation_buttons)
    
    buttons.append([InlineKeyboardButton(text="📨 Создать новый", callback_data="admin_create_mailing")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_refresh")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data == "admin_templates")
async def show_templates_list(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    templates = db.get_all_templates()
    
    if not templates:
        await safe_edit_message(
            callback,
            "📁 <b>Шаблоны рассылок</b>\n\n"
            "У вас пока нет сохраненных шаблонов.\n\n"
            "Создайте первый шаблон в конструкторе рассылок!",
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📨 Создать шаблон", callback_data="admin_create_mailing")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_refresh")]
            ])
        )
        return

    await safe_edit_message(
        callback,
        f"📁 <b>Шаблоны рассылок</b>\n\n"
        f"Всего шаблонов: {len(templates)}\n"
        "Выберите шаблон для просмотра или отправки:",
        get_templates_keyboard(templates)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("templates_page_"))
async def show_templates_page(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    page = int(callback.data.split("_")[-1])
    templates = db.get_all_templates()
    
    await safe_edit_message(
        callback,
        f"📁 <b>Шаблоны рассылок</b>\n\n"
        f"Страница {page + 1}\n"
        "Выберите шаблон для просмотра или отправки:",
        get_templates_keyboard(templates, page)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("template_"))
async def show_template_details(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    template_id = int(callback.data.split("_")[1])
    template = db.get_template_by_id(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден")
        return

    # Генерируем описание шаблона
    media_info = ""
    if template['media_type']:
        media_types = {
            "photo": "🖼️ Фото",
            "video": "📹 Видео",
            "document": "📄 Документ",
            "audio": "🎵 Аудио", 
            "voice": "🎤 Голосовое",
            "animation": "🎭 GIF/Анимация"
        }
        media_info = f"<b>Медиа:</b> {media_types.get(template['media_type'])}\n"
    
    text = (
        f"📄 <b>Шаблон #{template['id']}</b>\n\n"
        f"<b>Заголовок:</b> {template['title']}\n"
        f"{media_info}"
        f"<b>Текст:</b>\n{template['message_text'][:300]}{'...' if len(template['message_text']) > 300 else ''}\n\n"
        f"<b>Создан:</b> {template['created_at'][:16]}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📨 Отправить рассылку", callback_data=f"send_template_{template_id}")],
        [InlineKeyboardButton(text="👁️ Предпросмотр", callback_data=f"preview_template_{template_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_template_{template_id}")],
        [InlineKeyboardButton(text="🔙 К списку шаблонов", callback_data="admin_templates")]
    ])
    
    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("preview_template_"))
async def preview_template(callback: types.CallbackQuery, bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    template_id = int(callback.data.split("_")[2])
    template = db.get_template_by_id(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден")
        return

    try:
        # Отправляем предпросмотр администратору
        if template['media_type'] and template['media_file_id']:
            # Отправляем медиа с текстом как подпись
            media_methods = {
                'photo': bot.send_photo,
                'video': bot.send_video,
                'document': bot.send_document,
                'audio': bot.send_audio,
                'voice': bot.send_voice,
                'animation': bot.send_animation
            }
            
            if template['media_type'] in media_methods:
                await media_methods[template['media_type']](
                    chat_id=callback.from_user.id,
                    **{template['media_type']: template['media_file_id']},
                    caption=template['message_text'],
                    parse_mode='HTML'
                )
        else:
            # Отправляем только текст
            await bot.send_message(
                chat_id=callback.from_user.id,
                text=template['message_text'],
                parse_mode='HTML'
            )
        
        await callback.answer("👁️ Предпросмотр отправлен в личные сообщения")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка предпросмотра: {str(e)}")

@router.callback_query(F.data.startswith("send_template_"))
async def send_template_mailing(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    template_id = int(callback.data.split("_")[2])
    template = db.get_template_by_id(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден")
        return

    # Сохраняем данные шаблона в состоянии для отправки
    await state.update_data(
        title=template['title'],
        message_text=template['message_text'],
        message_type=template['message_type'],
        media_type=template['media_type'],
        media_file_id=template['media_file_id'],
        template_id=template_id
    )
    
    # Показываем выбор аудитории
    audience_count = await get_audience_count('all')
    
    text = (
        f"📨 <b>Отправка шаблона:</b> {template['title']}\n\n"
        f"📝 <b>Тип:</b> {template['message_type']}\n"
        f"👥 <b>Доступно пользователей:</b> {audience_count}\n\n"
        "🎯 <b>Выберите целевую аудиторию:</b>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Все пользователи", callback_data=f"send_audience_all_{template_id}"),
            InlineKeyboardButton(text="🔥 Активные", callback_data=f"send_audience_active_week_{template_id}")
        ],
        [
            InlineKeyboardButton(text="🆕 Новые (сегодня)", callback_data=f"send_audience_new_today_{template_id}"),
            InlineKeyboardButton(text="📈 Новые (неделя)", callback_data=f"send_audience_new_week_{template_id}")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"template_{template_id}")]
    ])
    
    await safe_edit_message(callback, text, keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("send_audience_"))
async def send_template_to_audience(callback: types.CallbackQuery, bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    parts = callback.data.split("_")
    audience_type = parts[2]
    template_id = int(parts[3])
    
    template = db.get_template_by_id(template_id)
    if not template:
        await callback.answer("❌ Шаблон не найден")
        return

    mailing_service = MailingService(bot)
    
    # Показываем уведомление о начале рассылки
    await callback.message.edit_text(
        "📨 <b>Рассылка запущена...</b>\n\n"
        "⏳ Отправляем сообщения пользователям...",
        parse_mode="HTML"
    )
    
    # Сохраняем рассылку (не как шаблон)
    mailing_id = db.save_mailing(
        title=template['title'],
        message_text=template['message_text'],
        message_type=template['message_type'],
        media_type=template['media_type'],
        media_file_id=template['media_file_id'],
        audience_type=audience_type,
        is_template=False
    )
    
    # Отправляем рассылку
    success_count, total_count = await mailing_service.send_mailing(
        mailing_id, 
        template['message_text'],
        template['message_type'],
        template['media_type'],
        template['media_file_id'],
        audience_type
    )
    
    delivery_rate = round((success_count/total_count)*100, 2) if total_count > 0 else 0
    
    await callback.message.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📨 <b>Шаблон:</b> {template['title']}\n"
        f"🎯 <b>Аудитория:</b> {audience_type}\n"
        f"✅ <b>Успешно отправлено:</b> {success_count}/{total_count}\n"
        f"📊 <b>Процент доставки:</b> {delivery_rate}%\n\n"
        f"📅 <b>Время отправки:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика рассылок", callback_data="stats_mailings")],
            [InlineKeyboardButton(text="📁 Другие шаблоны", callback_data="admin_templates")],
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_refresh")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("delete_template_"))
async def delete_template(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    template_id = int(callback.data.split("_")[2])
    template = db.get_template_by_id(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден")
        return

    # Удаляем шаблон (помечаем как не-шаблон)
    db.update_template_status(template_id, False)
    
    await callback.answer("✅ Шаблон удален")
    await show_templates_list(callback)

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