"""
Chat and message management functions - Using LawyerConnectDB
"""
from database.db_config import get_db_connection, is_using_sqlite

def create_chat(chat_id, user_id, title="New Chat"):
    """Create a new AI chat for a user (using user_id from website)"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO ai_chats (chat_id, user_id, title) VALUES (?, ?, ?)",
            (chat_id, user_id, title)
        )
        connection.commit()
        return True
    except Exception as e:
        error_msg = str(e)
        if "UNIQUE" in error_msg or "duplicate" in error_msg.lower():
            return True  # Not an error, chat exists
        print(f"[ERROR] Failed to create chat: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_user_chats(user_id):
    """Get all AI chats for a user (using user_id)"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            """SELECT chat_id, title, created_at, updated_at 
               FROM ai_chats 
               WHERE user_id = ? 
               ORDER BY updated_at DESC""",
            (user_id,)
        )
        rows = cursor.fetchall()
        
        if is_using_sqlite():
            chats = [dict(row) for row in rows]
        else:
            columns = [column[0] for column in cursor.description]
            chats = [dict(zip(columns, row)) for row in rows]
        return chats
    except Exception as e:
        print(f"[ERROR] Failed to get chats: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def update_chat_title(chat_id, title):
    """Update AI chat title"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        if is_using_sqlite():
            cursor.execute(
                "UPDATE ai_chats SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?",
                (title, chat_id)
            )
        else:
            cursor.execute(
                "UPDATE ai_chats SET title = ?, updated_at = GETDATE() WHERE chat_id = ?",
                (title, chat_id)
            )
        connection.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update chat title: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def delete_chat(chat_id):
    """Delete an AI chat and all its messages"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM ai_chats WHERE chat_id = ?", (chat_id,))
        connection.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete chat: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_message(chat_id, role, content):
    """Add a message to an AI chat"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO ai_messages (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content)
        )
        connection.commit()
        
        # Update chat's updated_at timestamp
        if is_using_sqlite():
            cursor.execute(
                "UPDATE ai_chats SET updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?",
                (chat_id,)
            )
        else:
            cursor.execute(
                "UPDATE ai_chats SET updated_at = GETDATE() WHERE chat_id = ?",
                (chat_id,)
            )
        connection.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to add message: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_chat_messages(chat_id):
    """Get all messages for an AI chat"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            """SELECT role, content, created_at 
               FROM ai_messages 
               WHERE chat_id = ? 
               ORDER BY created_at ASC""",
            (chat_id,)
        )
        rows = cursor.fetchall()
        
        if is_using_sqlite():
            messages = [dict(row) for row in rows]
        else:
            columns = [column[0] for column in cursor.description]
            messages = [dict(zip(columns, row)) for row in rows]
        return messages
    except Exception as e:
        print(f"[ERROR] Failed to get messages: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def get_recent_messages(chat_id, limit=10):
    """Get recent messages for an AI chat (for memory context)"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        
        if is_using_sqlite():
            cursor.execute(
                """SELECT role, content, created_at 
                   FROM ai_messages 
                   WHERE chat_id = ? 
                   ORDER BY created_at DESC 
                   LIMIT ?""",
                (chat_id, limit)
            )
        else:
            cursor.execute(
                """SELECT TOP (?) role, content, created_at 
                   FROM ai_messages 
                   WHERE chat_id = ? 
                   ORDER BY created_at DESC""",
                (limit, chat_id)
            )
        
        rows = cursor.fetchall()
        
        if is_using_sqlite():
            messages = [dict(row) for row in rows]
        else:
            columns = [column[0] for column in cursor.description]
            messages = [dict(zip(columns, row)) for row in rows]
        
        return list(reversed(messages))  # Return in chronological order
    except Exception as e:
        print(f"[ERROR] Failed to get recent messages: {e}")
        return []
    finally:
        cursor.close()
        connection.close()
