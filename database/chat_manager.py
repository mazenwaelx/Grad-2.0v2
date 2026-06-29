"""
Chat and message management — Repository pattern.

``ChatRepository`` encapsulates all CRUD operations for AI chats and
messages, using the ``db_connection`` context manager for safe
resource handling and ``_SQLDialect`` for dialect differences.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional

from database.db_config import db_connection, get_dialect


class ChatRepository:
    """Repository for AI chat and message persistence."""

    # ── Chat CRUD ──────────────────────────────────────────────────
    @staticmethod
    def create(chat_id: str, user_id, title: str = "New Chat") -> bool:
        """Create a new AI chat. Returns *True* on success (or if it already exists)."""
        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO ai_chats (chat_id, user_id, title) VALUES (?, ?, ?)",
                        (chat_id, user_id, title),
                    )
                    conn.commit()
                    return True
                finally:
                    cursor.close()
        except RuntimeError:
            return False
        except Exception as e:
            error_msg = str(e)
            if "UNIQUE" in error_msg or "duplicate" in error_msg.lower():
                return True  # Already exists — not an error
            print(f"[ERROR] Failed to create chat: {e}")
            return False

    @staticmethod
    def get_by_user(user_id) -> List[Dict[str, Any]]:
        """Return all AI chats for a user, newest first."""
        try:
            with db_connection() as conn:
                dialect = get_dialect()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """SELECT chat_id, title, created_at, updated_at
                           FROM ai_chats
                           WHERE user_id = ?
                           ORDER BY updated_at DESC""",
                        (user_id,),
                    )
                    rows = cursor.fetchall()
                    return _rows_to_dicts(cursor, rows, dialect.is_sqlite)
                finally:
                    cursor.close()
        except RuntimeError:
            return []
        except Exception as e:
            print(f"[ERROR] Failed to get chats: {e}")
            return []

    @staticmethod
    def update_title(chat_id: str, title: str) -> bool:
        """Update the title of an AI chat."""
        try:
            with db_connection() as conn:
                dialect = get_dialect()
                cursor = conn.cursor()
                try:
                    ts = dialect.current_timestamp()
                    cursor.execute(
                        f"UPDATE ai_chats SET title = ?, updated_at = {ts} WHERE chat_id = ?",
                        (title, chat_id),
                    )
                    conn.commit()
                    return True
                finally:
                    cursor.close()
        except RuntimeError:
            return False
        except Exception as e:
            print(f"[ERROR] Failed to update chat title: {e}")
            return False

    @staticmethod
    def delete(chat_id: str) -> bool:
        """Delete an AI chat and all its messages (cascade)."""
        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("DELETE FROM ai_chats WHERE chat_id = ?", (chat_id,))
                    conn.commit()
                    return True
                finally:
                    cursor.close()
        except RuntimeError:
            return False
        except Exception as e:
            print(f"[ERROR] Failed to delete chat: {e}")
            return False

    # ── Message CRUD ───────────────────────────────────────────────
    @staticmethod
    def add_message(chat_id: str, role: str, content: str) -> bool:
        """Append a message to an AI chat and bump its ``updated_at``."""
        try:
            with db_connection() as conn:
                dialect = get_dialect()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO ai_messages (chat_id, role, content) VALUES (?, ?, ?)",
                        (chat_id, role, content),
                    )
                    conn.commit()

                    ts = dialect.current_timestamp()
                    cursor.execute(
                        f"UPDATE ai_chats SET updated_at = {ts} WHERE chat_id = ?",
                        (chat_id,),
                    )
                    conn.commit()
                    return True
                finally:
                    cursor.close()
        except RuntimeError:
            return False
        except Exception as e:
            print(f"[ERROR] Failed to add message: {e}")
            return False

    @staticmethod
    def get_messages(chat_id: str) -> List[Dict[str, Any]]:
        """Return all messages for a chat in chronological order."""
        try:
            with db_connection() as conn:
                dialect = get_dialect()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """SELECT role, content, created_at
                           FROM ai_messages
                           WHERE chat_id = ?
                           ORDER BY created_at ASC""",
                        (chat_id,),
                    )
                    rows = cursor.fetchall()
                    return _rows_to_dicts(cursor, rows, dialect.is_sqlite)
                finally:
                    cursor.close()
        except RuntimeError:
            return []
        except Exception as e:
            print(f"[ERROR] Failed to get messages: {e}")
            return []

    @staticmethod
    def get_recent_messages(chat_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the *limit* most recent messages (in chronological order)."""
        try:
            with db_connection() as conn:
                dialect = get_dialect()
                cursor = conn.cursor()
                try:
                    if dialect.is_sqlite:
                        cursor.execute(
                            """SELECT role, content, created_at
                               FROM ai_messages
                               WHERE chat_id = ?
                               ORDER BY created_at DESC
                               LIMIT ?""",
                            (chat_id, limit),
                        )
                    else:
                        cursor.execute(
                            """SELECT TOP (?) role, content, created_at
                               FROM ai_messages
                               WHERE chat_id = ?
                               ORDER BY created_at DESC""",
                            (limit, chat_id),
                        )

                    rows = cursor.fetchall()
                    messages = _rows_to_dicts(cursor, rows, dialect.is_sqlite)
                    return list(reversed(messages))  # chronological order
                finally:
                    cursor.close()
        except RuntimeError:
            return []
        except Exception as e:
            print(f"[ERROR] Failed to get recent messages: {e}")
            return []


# ── Helper ─────────────────────────────────────────────────────────
def _rows_to_dicts(cursor, rows, is_sqlite: bool) -> List[Dict[str, Any]]:
    """Convert database rows to a list of plain dicts."""
    if is_sqlite:
        return [dict(row) for row in rows]
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


# ── Backward-compatible free functions ─────────────────────────────
# Existing callers use ``from database.chat_manager import create_chat``
# etc. — these wrappers keep that working without any import change.

_repo = ChatRepository()

create_chat = _repo.create
get_user_chats = _repo.get_by_user
update_chat_title = _repo.update_title
delete_chat = _repo.delete
add_message = _repo.add_message
get_chat_messages = _repo.get_messages
get_recent_messages = _repo.get_recent_messages
