from aiogram import Router, types
from aiogram.filters import Command
from database.db import Database

router = Router()
db = Database()

@router.message(Command("start"))
async def start_command(message: types.Message):
    user = message.from_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    await message.answer(
        "Добро пожаловать! Этот бот предназначен для рассылки важных уведомлений."
    )