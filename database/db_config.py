"""
Smart database configuration - Uses LawyerConnectDB (same as website)
"""
import os
import queue
import threading
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration - NOW USING LAWYERCONNECT DATABASE
# ---------------------------------------------------------------------------
USE_SQLITE = None          # Determined on first connection attempt
DB_PATH = 'database/labour_law.db'
DB_SERVER = os.getenv('DB_SERVER', '.\\SQLEXPRESS')  # Match website
DB_NAME = 'LawyerConnectDB'  # CHANGED: Use same database as website
DB_DRIVER = '{ODBC Driver 17 for SQL Server}'
WORKING_CONN_STR = None

_POOL_SIZE = 5
_pool: queue.Queue = queue.Queue(maxsize=_POOL_SIZE)
_pool_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Pooled connection wrapper
# ---------------------------------------------------------------------------
class _PooledConnection:
    """Wraps a raw DB connection.  Calling .close() returns it to the pool
    instead of destroying it, so connections are reused transparently."""

    def __init__(self, conn):
        self._conn = conn

    def close(self):
        try:
            _pool.put_nowait(self._conn)
        except queue.Full:
            self._conn.close()

    def cursor(self):
        return self._conn.cursor()

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def execute(self, *args, **kwargs):
        return self._conn.execute(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._conn, name)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _detect_database():
    """Detect which database to use (runs once)."""
    global USE_SQLITE, WORKING_CONN_STR

    if USE_SQLITE is not None:
        return

    try:
        import pyodbc

        connection_strings = [
            f'DRIVER={DB_DRIVER};SERVER=(local)\\SQLEXPRESS;DATABASE=master;Trusted_Connection=yes;',
            f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE=master;Trusted_Connection=yes;',
            f'DRIVER={DB_DRIVER};SERVER=localhost,1433;DATABASE=master;Trusted_Connection=yes;',
        ]

        for conn_str in connection_strings:
            try:
                connection = pyodbc.connect(conn_str, timeout=3)
                connection.close()
                USE_SQLITE = False
                WORKING_CONN_STR = conn_str.replace('DATABASE=master', f'DATABASE={DB_NAME}')
                print("[INFO] Using SQL Server database")
                return
            except Exception:
                continue

        USE_SQLITE = True
        print("[INFO] Using SQLite database (SQL Server not available)")

    except ImportError:
        USE_SQLITE = True
        print("[INFO] Using SQLite database (pyodbc not installed)")


def _make_raw_connection():
    """Create a brand-new raw database connection."""
    if USE_SQLITE:
        import sqlite3
        os.makedirs('database', exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        import pyodbc
        return pyodbc.connect(WORKING_CONN_STR)


def _is_connection_alive(conn):
    """Check whether a pooled raw connection is still usable."""
    try:
        conn.execute("SELECT 1")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_db_connection():
    """Return a pooled connection.  The caller should call .close() when done
    (which returns the connection to the pool rather than destroying it)."""
    _detect_database()

    raw_conn = None

    # Try to grab a healthy connection from the pool
    while True:
        try:
            candidate = _pool.get_nowait()
            if _is_connection_alive(candidate):
                raw_conn = candidate
                break
            else:
                try:
                    candidate.close()
                except Exception:
                    pass
        except queue.Empty:
            break

    # No pooled connection available — create a fresh one
    if raw_conn is None:
        try:
            raw_conn = _make_raw_connection()
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return None

    return _PooledConnection(raw_conn)


def init_database():
    """Initialize AI chat tables in LawyerConnectDB (website database)."""
    _detect_database()

    connection = get_db_connection()
    if not connection:
        print("[ERROR] Cannot initialize database - no connection")
        return False

    try:
        cursor = connection.cursor()

        if USE_SQLITE:
            # SQLite tables (for fallback only)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    title TEXT DEFAULT 'New Chat',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES ai_chats(chat_id) ON DELETE CASCADE
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_chats_user_id ON ai_chats(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_messages_chat_id ON ai_messages(chat_id)")

        else:
            # SQL Server tables - integrate with LawyerConnectDB
            # Check if ai_chats table exists
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='ai_chats')
                CREATE TABLE ai_chats (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    chat_id NVARCHAR(255) UNIQUE NOT NULL,
                    user_id INT NOT NULL,
                    title NVARCHAR(500) DEFAULT 'New Chat',
                    created_at DATETIME DEFAULT GETDATE(),
                    updated_at DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (user_id) REFERENCES Users(Id) ON DELETE CASCADE
                )
            """)

            # Check if ai_messages table exists
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='ai_messages')
                CREATE TABLE ai_messages (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    chat_id NVARCHAR(255) NOT NULL,
                    role NVARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
                    content NVARCHAR(MAX) NOT NULL,
                    created_at DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (chat_id) REFERENCES ai_chats(chat_id) ON DELETE CASCADE
                )
            """)

            # Create indexes
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_ai_chats_user_id')
                CREATE INDEX idx_ai_chats_user_id ON ai_chats(user_id)
            """)

            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_ai_messages_chat_id')
                CREATE INDEX idx_ai_messages_chat_id ON ai_messages(chat_id)
            """)

        connection.commit()
        db_type = "SQLite" if USE_SQLITE else "SQL Server (LawyerConnectDB)"
        print(f"[SUCCESS] {db_type} AI chat tables initialized")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        connection.close()


def is_using_sqlite():
    """Check if using SQLite."""
    _detect_database()
    return USE_SQLITE
