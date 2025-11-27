"""核心功能模块。

导出核心功能类，包括浏览器控制、消息处理、会话管理和多账号管理。
"""

from src.core.browser_controller import BrowserController
from src.core.message_handler import MessageHandler
from src.core.session_manager import SessionManager
from src.core.multi_account_manager import MultiAccountManager
from src.core.message_router import MessageRouter

__all__ = [
    "BrowserController",
    "MessageHandler",
    "SessionManager",
    "MultiAccountManager",
    "MessageRouter",
]
