import os
import sqlite3
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import List, Optional, Dict, Any

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "chat.db"))


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_db(db_path: str = DB_PATH):
    """Context manager for SQLite database connection."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    """Initialize the SQLite database with required tables and indexes."""
    with get_db(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                model TEXT NOT NULL DEFAULT 'gemini-1.5-flash',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
            ON messages(conversation_id, timestamp);
        """)


def create_conversation(
    title: str = "New Chat",
    model: str = "gemini-1.5-flash",
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new conversation record."""
    conv_id = conversation_id or str(uuid.uuid4())
    now = _utcnow_iso()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO conversations (id, title, model, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conv_id, title.strip() or "New Chat", model, now, now),
        )
    return {
        "id": conv_id,
        "title": title.strip() or "New Chat",
        "model": model,
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single conversation along with its messages."""
    with get_db() as conn:
        cur = conn.execute(
            "SELECT id, title, model, created_at, updated_at FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        
        conv = dict(row)
        msg_cur = conn.execute(
            "SELECT id, conversation_id, role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (conversation_id,),
        )
        conv["messages"] = [dict(r) for r in msg_cur.fetchall()]
        return conv


def list_conversations() -> List[Dict[str, Any]]:
    """List all conversations ordered by most recently updated."""
    with get_db() as conn:
        cur = conn.execute(
            """
            SELECT c.id, c.title, c.model, c.created_at, c.updated_at,
                   COUNT(m.id) AS message_count,
                   (SELECT content FROM messages WHERE conversation_id = c.id ORDER BY timestamp DESC LIMIT 1) AS last_message
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            """
        )
        return [dict(row) for row in cur.fetchall()]


def update_conversation_title(conversation_id: str, title: str) -> Optional[Dict[str, Any]]:
    """Update conversation title."""
    now = _utcnow_iso()
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title.strip(), now, conversation_id),
        )
        if cur.rowcount == 0:
            return None
    return get_conversation(conversation_id)


def update_conversation_timestamp(conversation_id: str) -> None:
    """Touch updated_at timestamp for a conversation."""
    now = _utcnow_iso()
    with get_db() as conn:
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )


def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation and all its messages (cascades)."""
    with get_db() as conn:
        cur = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        return cur.rowcount > 0


def add_message(
    conversation_id: str,
    role: str,
    content: str,
    message_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a message to a conversation and update conversation timestamp."""
    msg_id = message_id or str(uuid.uuid4())
    now = _utcnow_iso()
    with get_db() as conn:
        # Verify conversation exists; if not, create it automatically
        cur = conn.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
        if not cur.fetchone():
            first_title = content[:35] + ("..." if len(content) > 35 else "") if content else "New Chat"
            conn.execute(
                "INSERT INTO conversations (id, title, model, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (conversation_id, first_title, "gemini-1.5-flash", now, now),
            )
        else:
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )

        conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (msg_id, conversation_id, role, content, now),
        )

    return {
        "id": msg_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "timestamp": now,
    }


def get_messages(conversation_id: str) -> List[Dict[str, Any]]:
    """Get all messages for a conversation ordered chronologically."""
    with get_db() as conn:
        cur = conn.execute(
            "SELECT id, conversation_id, role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (conversation_id,),
        )
        return [dict(r) for r in cur.fetchall()]


# Automatically initialize DB schema on import
init_db()
