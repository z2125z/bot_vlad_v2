from aiogram import Router, types
from aiogram.filters import Command
from database.db import Database
from datetime import datetime

router = Router()
db = Database()

@router.message(Command("start"))
async def start_command(message: types.Message):
    user = message.from_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    db.record_user_activity(user.id, "start")
    
    await message.answer(
        "Добро пожаловать! Этот бот предназначен для рассылки важных уведомлений."
    )

@router.message(Command("myid"))
async def get_my_id(message: types.Message):
    """Команда для получения своего ID"""
    user_id = message.from_user.id
    await message.answer(f"Ваш Telegram ID: `{user_id}`\n\nДобавьте этот ID в ADMIN_IDS в файле .env", parse_mode="Markdown")