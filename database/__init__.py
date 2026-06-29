"""
Database package.

Re-exports the most commonly used symbols so callers can do::

    from database import init_database, create_chat, get_user_chats, ...
"""
from database.db_config import get_db_connection, init_database, db_connection, is_using_sqlite
from database.user_manager import create_user, get_user, verify_user, UserRepository
from database.chat_manager import (
    create_chat, get_user_chats, update_chat_title, delete_chat,
    add_message, get_chat_messages, get_recent_messages, ChatRepository,
)

__all__ = [
    # Connection helpers
    "get_db_connection",
    "db_connection",
    "init_database",
    "is_using_sqlite",
    # User operations (backward-compat functions + class)
    "create_user",
    "get_user",
    "verify_user",
    "UserRepository",
    # Chat operations (backward-compat functions + class)
    "create_chat",
    "get_user_chats",
    "update_chat_title",
    "delete_chat",
    "add_message",
    "get_chat_messages",
    "get_recent_messages",
    "ChatRepository",
]
