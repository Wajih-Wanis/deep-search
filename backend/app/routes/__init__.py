# This file organizes route registration
from .auth import auth_bp
from .chats import chats_bp
from .ai import ai_bp
from .config import config_bp

__all__ = ['auth_bp', 'chats_bp', 'ai_bp', 'config_bp']