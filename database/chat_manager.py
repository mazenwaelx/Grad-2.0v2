"""
Chat and message management functions
"""
from database.db_config import get_db_connection, is_using_sqlite

def create_chat(chat_id, user_email, title="New Chat"):
    """Create a new chat"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO chats (chat_id, user_email, title) VALUES (?, ?, ?)",
            (chat_id, user_email, title)
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

def get_user_chats(user_email):
    """Get all chats for a user"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            """SELECT chat_id, title, created_at, updated_at 
               FROM chats 
               WHERE user_email = ? 
               ORDER BY updated_at DESC""",
            (user_email,)
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
    """Update chat title"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        if is_using_sqlite():
            cursor.execute(
                "UPDATE chats SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?",
                (title, chat_id)
            )
        else:
            cursor.execute(
                "UPDATE chats SET title = ?, updated_at = GETDATE() WHERE chat_id = ?",
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
    """Delete a chat and all its messages"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
        connection.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete chat: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def add_message(chat_id, role, content):
    """Add a message to a chat"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content)
        )
        connection.commit()
        
        # Update chat's updated_at timestamp
        if is_using_sqlite():
            cursor.execute(
                "UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?",
                (chat_id,)
            )
        else:
            cursor.execute(
                "UPDATE chats SET updated_at = GETDATE() WHERE chat_id = ?",
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
    """Get all messages for a chat"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            """SELECT role, content, created_at 
               FROM messages 
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
    """Get recent messages for a chat (for memory context)"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        
        if is_using_sqlite():
            cursor.execute(
                """SELECT role, content, created_at 
                   FROM messages 
                   WHERE chat_id = ? 
                   ORDER BY created_at DESC 
                   LIMIT ?""",
                (chat_id, limit)
            )
        else:
            cursor.execute(
                """SELECT TOP (?) role, content, created_at 
                   FROM messages 
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
