# src/storage.py
"""
Simple SQLite storage for users and chat history.

- users: id, name, email, password_hash
- chats: id, user_id, question, answer, created_at
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "lawbot.db")


def init_db() -> None:
    """Create DB and tables if not present."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ----------------- User helpers ----------------- #

def create_user(name: str, email: str, password: str) -> Dict[str, Any]:
    if not name or not email or not password:
        raise ValueError("Name, email and password are required.")

    password_hash = generate_password_hash(password)

    with get_conn() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name.strip(), email.strip().lower(), password_hash),
            )
        except sqlite3.IntegrityError as e:
            # email already exists
            raise ValueError("A user with this email already exists.") from e

        user_id = cur.lastrowid
        row = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    return dict(row)


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    if not email or not password:
        return None

    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()

    if row is None:
        return None

    if not check_password_hash(row["password_hash"], password):
        return None

    # return safe subset
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "created_at": row["created_at"],
    }


# ----------------- Chat helpers ----------------- #

def save_chat(user_id: Optional[int], question: str, answer: str) -> None:
    """Persist a single chat turn. If user_id is None, skip."""
    if not user_id:
        return
    if not question or not answer:
        return

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO chats (user_id, question, answer) VALUES (?, ?, ?)",
            (user_id, question, answer),
        )


def get_chats(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Return the last N chats for a user, newest last."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT question, answer, created_at
            FROM chats
            WHERE user_id = ?
            ORDER BY created_at ASC, id ASC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

    return [dict(r) for r in rows]
