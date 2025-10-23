from .main_menu import router as admin_main_router
from .admin import router as admin_router
from .statistics import router as stats_router
from .excel_reports import router as excel_reports_router
from .mailing_creator import router as mailing_creator_router
from .templates_manager import router as templates_router
from .mailing_history import router as mailing_history_router
from .user_mailing import router as user_mailing_router

all_routers = [
    admin_main_router,
    admin_router,
    stats_router,
    excel_reports_router,
    mailing_creator_router,
    templates_router,
    mailing_history_router,
    user_mailing_router
]