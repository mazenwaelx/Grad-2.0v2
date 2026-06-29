"""
User management — Repository pattern with secure bcrypt hashing.

``UserRepository`` encapsulates all user CRUD operations.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple, Dict, Any

import bcrypt

from database.db_config import db_connection, get_dialect


class UserRepository:
    """Repository for user persistence and authentication."""

    @staticmethod
    def create(
        email: str,
        name: str,
        password: str,
        role: str = "User",
        phone: str = "",
        city: str = "",
    ) -> Tuple[bool, str]:
        """Create a new user with bcrypt-hashed password.

        Returns ``(True, message)`` on success or ``(False, reason)`` on failure.
        """
        try:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            with db_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO Users (Email, FullName, PasswordHash, Role, Phone, City, CreatedAt) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (email, name, password_hash, role, phone, city, datetime.now()),
                    )
                    conn.commit()
                    return True, "User created successfully"
                finally:
                    cursor.close()

        except RuntimeError as e:
            return False, str(e)
        except Exception as e:
            error_msg = str(e)
            if "UNIQUE" in error_msg or "duplicate" in error_msg.lower():
                return False, "Email already exists"
            return False, error_msg

    @staticmethod
    def get_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Retrieve a user by email, or *None* if not found."""
        try:
            with db_connection() as conn:
                dialect = get_dialect()
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT * FROM Users WHERE Email = ?", (email,))
                    row = cursor.fetchone()
                    if not row:
                        return None
                    if dialect.is_sqlite:
                        return dict(row)
                    columns = [col[0] for col in cursor.description]
                    return dict(zip(columns, row))
                finally:
                    cursor.close()

        except RuntimeError:
            return None
        except Exception as e:
            print(f"[ERROR] Failed to get user: {e}")
            return None

    @staticmethod
    def verify(email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Verify user credentials.

        Returns ``(True, user_dict)`` on success or ``(False, None)`` on failure.
        """
        user = UserRepository.get_by_email(email)
        if not user:
            return False, None

        try:
            password_hash = user["PasswordHash"]
            if password_hash is None:
                return False, None

            if isinstance(password_hash, str):
                password_hash_bytes = password_hash.encode("utf-8")
            else:
                password_hash_bytes = password_hash

            if bcrypt.checkpw(password.encode("utf-8"), password_hash_bytes):
                return True, user

        except Exception as e:
            print(f"[ERROR] Password verification failed: {e}")

        return False, None


# ── Backward-compatible free functions ─────────────────────────────
_repo = UserRepository()

create_user = _repo.create
get_user = _repo.get_by_email
verify_user = _repo.verify
