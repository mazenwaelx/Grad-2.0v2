"""
Database configuration with connection pooling.

Supports SQL Server (via pyodbc) with SQLite as a fallback.
Uses the LawyerConnectDB database (same as the website).
"""
from __future__ import annotations

import os
import queue
import threading
from contextlib import contextmanager
from typing import Optional, Generator

from dotenv import load_dotenv

load_dotenv()

# ── Configuration constants ────────────────────────────────────────
DB_PATH = "database/labour_law.db"
DB_SERVER = os.getenv("DB_SERVER", ".\\SQLEXPRESS")
DB_NAME = "LawyerConnectDB"
DB_DRIVER = "{ODBC Driver 17 for SQL Server}"


# ── Pooled connection wrapper ──────────────────────────────────────
class PooledConnection:
    """Wraps a raw DB connection.

    Calling ``.close()`` returns the connection to the pool instead of
    destroying it, so connections are reused transparently.
    """

    def __init__(self, raw_conn, pool: "ConnectionPool"):
        self._conn = raw_conn
        self._pool = pool

    def close(self) -> None:
        """Return the connection to the pool (or close it if the pool is full)."""
        try:
            self._pool._pool.put_nowait(self._conn)
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


# ── Connection pool ────────────────────────────────────────────────
class ConnectionPool:
    """Thread-safe database connection pool.

    Automatically detects whether SQL Server is available and falls
    back to SQLite when it is not.
    """

    _POOL_SIZE = 5

    def __init__(self) -> None:
        self._pool: queue.Queue = queue.Queue(maxsize=self._POOL_SIZE)
        self._lock = threading.Lock()
        self._use_sqlite: Optional[bool] = None
        self._working_conn_str: Optional[str] = None

    # ── Public API ─────────────────────────────────────────────────
    @property
    def is_sqlite(self) -> bool:
        """Return *True* if the pool is using SQLite."""
        self._detect_database()
        return self._use_sqlite  # type: ignore[return-value]

    def get_connection(self) -> Optional[PooledConnection]:
        """Return a pooled connection (or *None* on failure).

        The caller **must** call ``.close()`` when done — which returns
        the underlying connection to the pool rather than destroying it.
        """
        self._detect_database()

        raw_conn = self._acquire_from_pool()

        if raw_conn is None:
            try:
                raw_conn = self._make_raw_connection()
            except Exception as e:
                print(f"[ERROR] Database connection failed: {e}")
                return None

        return PooledConnection(raw_conn, self)

    # ── Internal helpers ───────────────────────────────────────────
    def _detect_database(self) -> None:
        """Detect which database backend to use (runs once)."""
        if self._use_sqlite is not None:
            return

        with self._lock:
            if self._use_sqlite is not None:
                return  # another thread won the race

            try:
                import pyodbc

                connection_strings = [
                    f"DRIVER={DB_DRIVER};SERVER=(local)\\SQLEXPRESS;DATABASE=master;Trusted_Connection=yes;",
                    f"DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE=master;Trusted_Connection=yes;",
                    f"DRIVER={DB_DRIVER};SERVER=localhost,1433;DATABASE=master;Trusted_Connection=yes;",
                ]

                for conn_str in connection_strings:
                    try:
                        connection = pyodbc.connect(conn_str, timeout=3)
                        connection.close()
                        self._use_sqlite = False
                        self._working_conn_str = conn_str.replace(
                            "DATABASE=master", f"DATABASE={DB_NAME}"
                        )
                        print("[INFO] Using SQL Server database")
                        return
                    except pyodbc.Error:
                        continue

                self._use_sqlite = True
                print("[INFO] Using SQLite database (SQL Server not available)")

            except ImportError:
                self._use_sqlite = True
                print("[INFO] Using SQLite database (pyodbc not installed)")

    def _make_raw_connection(self):
        """Create a brand-new raw database connection."""
        if self._use_sqlite:
            import sqlite3

            os.makedirs("database", exist_ok=True)
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

        import pyodbc

        return pyodbc.connect(self._working_conn_str)

    def _is_alive(self, conn) -> bool:
        """Check whether a pooled raw connection is still usable."""
        try:
            conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _acquire_from_pool(self):
        """Try to grab a healthy connection from the pool."""
        while True:
            try:
                candidate = self._pool.get_nowait()
                if self._is_alive(candidate):
                    return candidate
                # Stale connection — discard it
                try:
                    candidate.close()
                except Exception:
                    pass
            except queue.Empty:
                return None


# ── Module-level singleton ─────────────────────────────────────────
_pool = ConnectionPool()


def get_connection_pool() -> ConnectionPool:
    """Return the global connection pool instance."""
    return _pool


# ── Context manager ────────────────────────────────────────────────
@contextmanager
def db_connection() -> Generator[PooledConnection, None, None]:
    """Context manager that provides a pooled database connection.

    Usage::

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.commit()
            cursor.close()

    The connection is returned to the pool when the block exits.
    Raises ``RuntimeError`` if the connection could not be obtained.
    """
    conn = _pool.get_connection()
    if conn is None:
        raise RuntimeError("Could not obtain a database connection")
    try:
        yield conn
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


# ── Backward-compatible public API ─────────────────────────────────
def get_db_connection() -> Optional[PooledConnection]:
    """Return a pooled connection (backward-compatible wrapper)."""
    return _pool.get_connection()


def is_using_sqlite() -> bool:
    """Return *True* if the system is using SQLite."""
    return _pool.is_sqlite


def init_database() -> bool:
    """Initialise AI chat tables in the database."""
    return _DatabaseInitializer(_pool).run()


# ── SQL dialect strategy ───────────────────────────────────────────
class _SQLDialect:
    """Provides SQL fragments that differ between SQLite and SQL Server."""

    def __init__(self, use_sqlite: bool):
        self._sqlite = use_sqlite

    def current_timestamp(self) -> str:
        return "CURRENT_TIMESTAMP" if self._sqlite else "GETDATE()"

    def limit_clause(self, n: int, param_name: str = "?") -> str:
        """Return a limit fragment. For SQL Server, use ``TOP``."""
        if self._sqlite:
            return f"LIMIT {param_name}"
        return ""  # SQL Server uses TOP in SELECT

    @property
    def is_sqlite(self) -> bool:
        return self._sqlite


def get_dialect() -> _SQLDialect:
    """Return the SQL dialect for the current database backend."""
    return _SQLDialect(_pool.is_sqlite)


# ── Database initializer ───────────────────────────────────────────
class _DatabaseInitializer:
    """Creates the AI chat tables if they don't exist."""

    def __init__(self, pool: ConnectionPool):
        self._pool = pool

    def run(self) -> bool:
        """Create tables and indexes. Returns *True* on success."""
        conn = self._pool.get_connection()
        if not conn:
            print("[ERROR] Cannot initialize database - no connection")
            return False

        try:
            cursor = conn.cursor()

            if self._pool.is_sqlite:
                self._create_sqlite_tables(cursor)
            else:
                self._create_sqlserver_tables(cursor)

            conn.commit()
            db_type = "SQLite" if self._pool.is_sqlite else "SQL Server (LawyerConnectDB)"
            print(f"[SUCCESS] {db_type} AI chat tables initialized")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to initialize database: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            cursor.close()
            conn.close()

    # ── SQLite schema ──────────────────────────────────────────────
    @staticmethod
    def _create_sqlite_tables(cursor) -> None:
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
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ai_chats_user_id ON ai_chats(user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ai_messages_chat_id ON ai_messages(chat_id)"
        )

    # ── SQL Server schema ──────────────────────────────────────────
    @staticmethod
    def _create_sqlserver_tables(cursor) -> None:
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
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_ai_chats_user_id')
            CREATE INDEX idx_ai_chats_user_id ON ai_chats(user_id)
        """)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_ai_messages_chat_id')
            CREATE INDEX idx_ai_messages_chat_id ON ai_messages(chat_id)
        """)
