"""
User management functions
"""
from database.db_config import get_db_connection, is_using_sqlite

def create_user(email, name, password):
    """Create a new user"""
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed"
    
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (email, name, password) VALUES (?, ?, ?)",
            (email, name, password)
        )
        connection.commit()
        return True, "User created successfully"
    except Exception as e:
        error_msg = str(e)
        if "UNIQUE" in error_msg or "duplicate" in error_msg.lower():
            return False, "Email already exists"
        return False, error_msg
    finally:
        cursor.close()
        connection.close()

def get_user(email):
    """Get user by email"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            if is_using_sqlite():
                # SQLite row_factory already returns dict-like objects
                return dict(row)
            else:
                # SQL Server - convert to dict
                columns = [column[0] for column in cursor.description]
                user = dict(zip(columns, row))
                return user
        return None
    except Exception as e:
        print(f"[ERROR] Failed to get user: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def verify_user(email, password):
    """Verify user credentials"""
    user = get_user(email)
    if user and user['password'] == password:
        return True, user
    return False, None
