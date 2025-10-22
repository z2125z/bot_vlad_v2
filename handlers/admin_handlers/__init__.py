from .main_menu import router as main_menu_router
from .statistics import router as statistics_router
from .mailing_creator import router as mailing_creator_router
from .user_mailing import router as user_mailing_router
from .excel_reports import router as excel_reports_router
from .mailing_history import router as mailing_history_router
from .templates_manager import router as templates_manager_router

__all__ = [
    'main_menu_router', 
    'statistics_router', 
    'mailing_creator_router', 
    'user_mailing_router',
    'excel_reports_router',
    'mailing_history_router',
    'templates_manager_router'
]