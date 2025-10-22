from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext  # Этот импорт должен быть
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from config.config import Config
from services.mailing_service import MailingService
from database.db import Database
from datetime import datetime  # Этот импорт должен быть
import os

router = Router()
db = Database()

def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMIN_IDS

class MailingCreation(StatesGroup):
    waiting_for_title = State()
    waiting_for_message = State()
    waiting_for_media = State()
    waiting_for_media_type = State()
    waiting_for_confirmation = State()
    waiting_for_audience = State()

def get_media_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🖼️ Фото", callback_data="media_photo"),
            InlineKeyboardButton(text="📹 Видео", callback_data="media_video")
        ],
        [
            InlineKeyboardButton(text="📄 Документ", callback_data="media_document"),
            InlineKeyboardButton(text="🎵 Аудио", callback_data="media_audio")
        ],
        [
            InlineKeyboardButton(text="🎤 Голосовое", callback_data="media_voice"),
            InlineKeyboardButton(text="🎭 GIF/Анимация", callback_data="media_animation")
        ],
        [
            InlineKeyboardButton(text="📝 Только текст", callback_data="media_none"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="cancel_mailing")
        ]
    ])

def get_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💾 Сохранить шаблон", callback_data="save_template"),
            InlineKeyboardButton(text="📨 Отправить сейчас", callback_data="send_now")
        ],
        [
            InlineKeyboardButton(text="✏️ Редактировать текст", callback_data="edit_text"),
            InlineKeyboardButton(text="🖼️ Изменить медиа", callback_data="edit_media")
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
        "Введите заголовок для рассылки (будет использоваться для поиска в шаблонах):",
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
    await state.update_data(message_text=message.html_text)
    await state.set_state(MailingCreation.waiting_for_media_type)
    
    await message.answer(
        "🎨 <b>Выберите тип медиа-вложения:</b>\n\n"
        "Вы можете добавить фото, видео, документ, аудио, голосовое сообщение или GIF-анимацию.",
        reply_markup=get_media_type_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(MailingCreation.waiting_for_media_type, F.data.startswith("media_"))
async def select_media_type(callback: types.CallbackQuery, state: FSMContext):
    media_type = callback.data.replace("media_", "")
    
    if media_type == "none":
        await state.update_data(media_type=None, media_file_id=None)
        await state.set_state(MailingCreation.waiting_for_audience)
        await process_audience_selection(callback, state)
        return
    
    await state.update_data(media_type=media_type)
    await state.set_state(MailingCreation.waiting_for_media)
    
    media_types = {
        "photo": "🖼️ Фото",
        "video": "📹 Видео", 
        "document": "📄 Документ",
        "audio": "🎵 Аудио",
        "voice": "🎤 Голосовое сообщение",
        "animation": "🎭 GIF/Анимация"
    }
    
    await callback.message.edit_text(
        f"📤 <b>Отправьте {media_types[media_type]}:</b>\n\n"
        "Просто загрузите файл в этот чат. Бот сохранит его для рассылки.",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(MailingCreation.waiting_for_media)
async def process_media_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    media_type = data.get('media_type')
    
    file_id = None
    message_type = 'text'
    
    try:
        if media_type == "photo" and message.photo:
            file_id = message.photo[-1].file_id
            message_type = 'photo'
        elif media_type == "video" and message.video:
            file_id = message.video.file_id
            message_type = 'video'
        elif media_type == "document" and message.document:
            file_id = message.document.file_id
            message_type = 'document'
        elif media_type == "audio" and message.audio:
            file_id = message.audio.file_id
            message_type = 'audio'
        elif media_type == "voice" and message.voice:
            file_id = message.voice.file_id
            message_type = 'voice'
        elif media_type == "animation" and message.animation:
            file_id = message.animation.file_id
            message_type = 'animation'
        
        if file_id:
            await state.update_data(media_file_id=file_id, message_type=message_type)
            await state.set_state(MailingCreation.waiting_for_audience)
            await process_audience_selection(message, state)
        else:
            await message.answer(
                "❌ <b>Неверный тип файла</b>\n\n"
                f"Ожидается {media_type}. Попробуйте еще раз или выберите другой тип медиа.",
                parse_mode="HTML",
                reply_markup=get_media_type_keyboard()
            )
            await state.set_state(MailingCreation.waiting_for_media_type)
            
    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка загрузки медиа:</b> {str(e)}\n\n"
            "Попробуйте еще раз или выберите другой тип медиа.",
            parse_mode="HTML",
            reply_markup=get_media_type_keyboard()
        )
        await state.set_state(MailingCreation.waiting_for_media_type)

async def process_audience_selection(update, state: FSMContext):
    """Обработка выбора аудитории"""
    if isinstance(update, types.CallbackQuery):
        message = update.message
    else:
        message = update
    
    data = await state.get_data()
    
    # Показываем предпросмотр
    preview_text = await generate_preview_text(data)
    
    await message.answer(
        preview_text,
        reply_markup=get_audience_keyboard(),
        parse_mode="HTML"
    )

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
    preview_text = await generate_preview_text(data, audience_type, audience_count)
    
    await callback.message.edit_text(
        preview_text,
        reply_markup=get_confirmation_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

async def generate_preview_text(data, audience_type=None, audience_count=None):
    """Генерирует текст предпросмотра рассылки"""
    text = "👁️ <b>Предпросмотр рассылки</b>\n\n"
    text += f"<b>Заголовок:</b> {data['title']}\n"
    
    if audience_type and audience_count is not None:
        audience_names = {
            "all": "👥 Все пользователи",
            "active_week": "🔥 Активные за неделю", 
            "new_today": "🆕 Новые сегодня",
            "new_week": "📈 Новые за неделю"
        }
        text += f"<b>Аудитория:</b> {audience_names.get(audience_type)} ({audience_count} пользователей)\n"
    
    media_type = data.get('media_type')
    if media_type:
        media_types = {
            "photo": "🖼️ Фото",
            "video": "📹 Видео",
            "document": "📄 Документ", 
            "audio": "🎵 Аудио",
            "voice": "🎤 Голосовое",
            "animation": "🎭 GIF/Анимация"
        }
        text += f"<b>Медиа:</b> {media_types.get(media_type, media_type)}\n"
    
    text += f"<b>Текст:</b>\n{data['message_text'][:500]}{'...' if len(data['message_text']) > 500 else ''}\n\n"
    
    if audience_type:
        text += "✅ <b>Подтвердите создание рассылки</b>"
    else:
        text += "🎯 <b>Теперь выберите целевую аудиторию:</b>"
    
    return text

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

@router.callback_query(F.data == "save_template")
async def save_as_template(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return

    data = await state.get_data()
    
    # Сохраняем как шаблон
    template_id = db.save_mailing(
        title=data['title'],
        message_text=data['message_text'],
        message_type=data.get('message_type', 'text'),
        media_type=data.get('media_type'),
        media_file_id=data.get('media_file_id'),
        audience_type=data.get('audience_type', 'all'),
        is_template=True
    )
    
    await callback.message.edit_text(
        f"💾 <b>Шаблон сохранен!</b>\n\n"
        f"📝 <b>Заголовок:</b> {data['title']}\n"
        f"🆔 <b>ID шаблона:</b> {template_id}\n\n"
        "Теперь вы можете использовать этот шаблон для рассылок в разделе \"📁 Шаблоны рассылок\".",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📨 Отправить сейчас", callback_data="send_now")],
            [InlineKeyboardButton(text="📁 Мои шаблоны", callback_data="admin_templates")],
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_refresh")]
        ]),
        parse_mode="HTML"
    )
    
    await state.clear()

@router.callback_query(F.data == "send_now")
async def send_mailing_now(callback: types.CallbackQuery, state: FSMContext, bot):
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
    
    # Сохраняем рассылку (не как шаблон)
    mailing_id = db.save_mailing(
        title=data['title'],
        message_text=data['message_text'],
        message_type=data.get('message_type', 'text'),
        media_type=data.get('media_type'),
        media_file_id=data.get('media_file_id'),
        audience_type=data.get('audience_type', 'all'),
        is_template=False
    )
    
    # Отправляем рассылку
    success_count, total_count = await mailing_service.send_mailing(
        mailing_id, 
        data['message_text'],
        data.get('message_type', 'text'),
        data.get('media_type'),
        data.get('media_file_id'),
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

@router.callback_query(F.data == "edit_text")
async def edit_mailing_text(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MailingCreation.waiting_for_message)
    await callback.message.edit_text(
        "✏️ <b>Редактирование текста рассылки</b>\n\n"
        "Введите новый текст рассылки:",
        parse_mode="HTML"
    )

@router.callback_query(F.data == "edit_media")
async def edit_mailing_media(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MailingCreation.waiting_for_media_type)
    await callback.message.edit_text(
        "🎨 <b>Изменение медиа-вложения</b>\n\n"
        "Выберите новый тип медиа:",
        reply_markup=get_media_type_keyboard(),
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