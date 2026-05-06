"""
Database package
"""
from database.db_config import get_db_connection, init_database
from database.user_manager import create_user, get_user, verify_user
from database.chat_manager import (
    create_chat, get_user_chats, update_chat_title, delete_chat,
    add_message, get_chat_messages, get_recent_messages
)

__all__ = [
    'get_db_connection',
    'init_database',
    'create_user',
    'get_user',
    'verify_user',
    'create_chat',
    'get_user_chats',
    'update_chat_title',
    'delete_chat',
    'add_message',
    'get_chat_messages',
    'get_recent_messages'
]
