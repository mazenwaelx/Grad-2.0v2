"""
Database-backed chat message history for LangChain
"""
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import List, Optional
from database.chat_manager import add_message, get_recent_messages, create_chat

class DatabaseChatMessageHistory(BaseChatMessageHistory):
    """Chat message history stored in MySQL database"""
    
    def __init__(self, chat_id: str, user_id: Optional[int] = None):
        self.chat_id = chat_id
        self.user_id = user_id if user_id is not None else 1  # Default to user_id=1 (admin/system)
        self._messages = []
        
        # Ensure chat exists before loading messages
        self._ensure_chat_exists()
        self._load_messages()
    
    def _ensure_chat_exists(self):
        """Ensure the chat exists in the database"""
        # Try to create the chat (will silently succeed if it already exists)
        create_chat(self.chat_id, self.user_id, "AI Chat")
    
    def _load_messages(self):
        """Load recent messages from database"""
        db_messages = get_recent_messages(self.chat_id, limit=10)
        self._messages = []
        for msg in db_messages:
            if msg['role'] == 'user':
                self._messages.append(HumanMessage(content=msg['content']))
            else:
                self._messages.append(AIMessage(content=msg['content']))
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Return the messages"""
        return self._messages
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the store"""
        role = 'user' if isinstance(message, HumanMessage) else 'assistant'
        content = message.content
        
        # Save to database
        add_message(self.chat_id, role, content)
        
        # Add to local cache
        self._messages.append(message)
        
        # Keep only last 10 messages in memory
        if len(self._messages) > 10:
            self._messages = self._messages[-10:]
    
    def add_user_message(self, message: str) -> None:
        """Add a user message"""
        self.add_message(HumanMessage(content=message))
    
    def add_ai_message(self, message: str) -> None:
        """Add an AI message"""
        self.add_message(AIMessage(content=message))
    
    def clear(self) -> None:
        """Clear the message history"""
        self._messages = []
        # Note: We don't delete from database, just clear local cache
