from aiogram import Router, types
from aiogram.filters import Command
from database.db import Database

router = Router()
db = Database()

@router.message(Command("start"))
async def start_command(message: types.Message):
    user = message.from_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    db.record_user_activity(user.id, "start")
    
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Этот бот предназначен для рассылки важных уведомлений и обновлений.\n\n"
        "📋 <b>Доступные команды:</b>\n"
        "/start - Запустить бота\n"
        "/help - Получить помощь\n"
        "/myid - Узнать свой ID\n\n"
        "⚡ <b>Будьте на связи!</b>",
        parse_mode="HTML"
    )

@router.message(Command("help"))
async def help_command(message: types.Message):
    db.record_user_activity(message.from_user.id, "help")
    
    await message.answer(
        "ℹ️ <b>Помощь по боту</b>\n\n"
        "Этот бот предоставляет:\n"
        "• 📨 Получение важных уведомлений\n"
        "• 🔔 Своевременные обновления\n"
        "• 📊 Статистику активности\n\n"
        "Если у вас есть вопросы или проблемы, обратитесь к администратору.\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Перезапустить бота\n"
        "/help - Показать эту справку",
        parse_mode="HTML"
    )

@router.message(Command("myid"))
async def get_my_id(message: types.Message):
    """Команда для получения своего ID"""
    user_id = message.from_user.id
    await message.answer(
        f"🆔 <b>Ваш Telegram ID:</b> <code>{user_id}</code>\n\n"
        "Этот ID может понадобиться администратору для предоставления доступа.",
        parse_mode="HTML"
    )

@router.message()
async def track_user_activity(message: types.Message):
    """Отслеживаем активность пользователей"""
    if message.from_user:
        db.record_user_activity(message.from_user.id, "message")
        
        # Отвечаем на неизвестные команды
        if message.text and message.text.startswith('/'):
            await message.answer(
                "❌ <b>Неизвестная команда</b>\n\n"
                "Используйте /help для просмотра доступных команд.",
                parse_mode="HTML"
            )