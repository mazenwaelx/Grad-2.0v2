"""
User management functions with secure password hashing
"""
import bcrypt
from database.db_config import get_db_connection, is_using_sqlite

def create_user(email, name, password):
    """Create a new user with bcrypt hashed password"""
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed"
    
    try:
        # Hash the password using bcrypt (secure!)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cursor = connection.cursor()
        # Use PascalCase for SQL Server columns: Name, Email, Password
        cursor.execute(
            "INSERT INTO Users (Email, Name, Password) VALUES (?, ?, ?)",
            (email, name, password_hash)
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
        # Use PascalCase: Email
        cursor.execute("SELECT * FROM Users WHERE Email = ?", (email,))
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
    """Verify user credentials using bcrypt (secure!)"""
    user = get_user(email)
    if not user:
        return False, None
    
    try:
        # Use PascalCase: Password
        password_hash = user['Password']
        # Handle both bytes and string from database
        if isinstance(password_hash, str):
            password_hash = password_hash.encode('utf-8')
        
        # Use bcrypt to verify password securely
        if bcrypt.checkpw(password.encode('utf-8'), password_hash):
            return True, user
    except Exception as e:
        print(f"[ERROR] Password verification failed: {e}")
    
    return False, None
