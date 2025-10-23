from .user_handlers.user import router as user_router
from .user_handlers.debug import router as debug_router
from .admin_handlers.main_menu import router as admin_main_router
from .admin_handlers.admin import router as admin_router
from .admin_handlers.statistics import router as stats_router
from .admin_handlers.excel_reports import router as excel_reports_router
from .admin_handlers.mailing_creator import router as mailing_creator_router
from .admin_handlers.templates_manager import router as templates_router
from .admin_handlers.mailing_history import router as mailing_history_router
from .admin_handlers.user_mailing import router as user_mailing_router

all_routers = [
    user_router,
    debug_router,
    admin_main_router,
    admin_router,
    stats_router,
    excel_reports_router,
    mailing_creator_router,
    templates_router,
    mailing_history_router,
    user_mailing_router
]