from .user import router as user_router
from .admin_handlers.main_menu import router as admin_main_router
from .admin_handlers.statistics import router as admin_stats_router
from .admin_handlers.mailing_creator import router as mailing_creator_router
from .admin_handlers.user_mailing import router as user_mailing_router
from .admin_handlers.excel_reports import router as excel_reports_router
from .admin_handlers.mailing_history import router as mailing_history_router
from .admin_handlers.templates_manager import router as templates_manager_router

# Собираем все роутеры
all_routers = [
    user_router,
    admin_main_router,
    admin_stats_router, 
    mailing_creator_router,
    user_mailing_router,
    excel_reports_router,
    mailing_history_router,
    templates_manager_router
]

__all__ = ['all_routers']