"""
Database-backed chat message history for LangChain.

Implements LangChain's ``BaseChatMessageHistory`` interface using
SQL Server / SQLite as the backing store (via ``ChatRepository``).
"""
from __future__ import annotations

from typing import List, Optional

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from database.chat_manager import ChatRepository

# Maximum messages to keep in the local in-memory cache.
_MAX_CACHE_SIZE = 10


class DatabaseChatMessageHistory(BaseChatMessageHistory):
    """Chat message history stored in SQL Server / SQLite database."""

    def __init__(self, chat_id: str, user_id: Optional[int] = None) -> None:
        self._chat_id = chat_id
        self._user_id = user_id if user_id is not None else 1
        self._messages: List[BaseMessage] = []
        self._repo = ChatRepository()

        self._ensure_chat_exists()
        self._load_messages()

    # ── BaseChatMessageHistory interface ───────────────────────────
    @property
    def messages(self) -> List[BaseMessage]:
        """Return the cached messages."""
        return self._messages

    def add_message(self, message: BaseMessage) -> None:
        """Persist a message to the database and update the local cache."""
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        self._repo.add_message(self._chat_id, role, message.content)

        self._messages.append(message)
        if len(self._messages) > _MAX_CACHE_SIZE:
            self._messages = self._messages[-_MAX_CACHE_SIZE:]

    def add_user_message(self, message: str) -> None:
        """Convenience: add a user message."""
        self.add_message(HumanMessage(content=message))

    def add_ai_message(self, message: str) -> None:
        """Convenience: add an AI message."""
        self.add_message(AIMessage(content=message))

    def clear(self) -> None:
        """Clear the in-memory cache (database records are kept)."""
        self._messages = []

    # ── Private helpers ────────────────────────────────────────────
    def _ensure_chat_exists(self) -> None:
        """Create the chat row if it doesn't already exist."""
        self._repo.create(self._chat_id, self._user_id, "AI Chat")

    def _load_messages(self) -> None:
        """Load the most recent messages from the database into cache."""
        db_messages = self._repo.get_recent_messages(self._chat_id, limit=_MAX_CACHE_SIZE)
        self._messages = []
        for msg in db_messages:
            if msg["role"] == "user":
                self._messages.append(HumanMessage(content=msg["content"]))
            else:
                self._messages.append(AIMessage(content=msg["content"]))
