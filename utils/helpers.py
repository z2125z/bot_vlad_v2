from typing import List

def format_user_list(users: List) -> str:
    if not users:
        return "Пользователей нет"
    
    formatted = "Список пользователей:\n\n"
    for user in users:
        formatted += f"ID: {user[1]}\n"
        formatted += f"Имя: {user[3] or 'Не указано'}\n"
        formatted += f"Username: @{user[2] or 'Не указан'}\n"
        formatted += "─" * 20 + "\n"
    
    return formatted