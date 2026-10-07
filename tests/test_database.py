"""
Unit tests for database module (backend/database.py).
"""

import os
import sys
import tempfile
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

temp_db = tempfile.NamedTemporaryFile(suffix="_test_db.db", delete=False)
TEST_DB_PATH = temp_db.name
temp_db.close()
os.environ["DATABASE_PATH"] = TEST_DB_PATH

import database as db


class TestDatabase(unittest.TestCase):
    """Test suite for SQLite database layer."""

    def setUp(self):
        db.DB_PATH = TEST_DB_PATH
        db.init_db(TEST_DB_PATH)
        with db.get_db(TEST_DB_PATH) as conn:
            conn.execute("DELETE FROM messages;")
            conn.execute("DELETE FROM conversations;")

    def tearDown(self):
        with db.get_db(TEST_DB_PATH) as conn:
            conn.execute("DELETE FROM messages;")
            conn.execute("DELETE FROM conversations;")

    def test_init_db(self):
        """Test database initialization creates required tables."""
        with db.get_db(TEST_DB_PATH) as conn:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row["name"] for row in cur.fetchall()]
            self.assertIn("conversations", tables)
            self.assertIn("messages", tables)

    def test_create_and_get_conversation(self):
        """Test creating conversation and retrieving it with messages."""
        conv = db.create_conversation(title="Test Chat", model="gemini-2.5-flash")
        self.assertIsNotNone(conv.get("id"))
        self.assertEqual(conv.get("title"), "Test Chat")
        self.assertEqual(conv.get("model"), "gemini-2.5-flash")

        fetched = db.get_conversation(conv["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], conv["id"])
        self.assertEqual(fetched["title"], "Test Chat")
        self.assertEqual(fetched["messages"], [])

    def test_add_and_get_messages(self):
        """Test adding messages and retrieving message history."""
        conv = db.create_conversation(title="Message Test")
        conv_id = conv["id"]

        msg1 = db.add_message(conv_id, "user", "What is machine learning?")
        self.assertEqual(msg1["role"], "user")
        self.assertEqual(msg1["content"], "What is machine learning?")

        msg2 = db.add_message(conv_id, "assistant", "Machine learning is a branch of AI...")
        self.assertEqual(msg2["role"], "assistant")

        messages = db.get_messages(conv_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], "What is machine learning?")
        self.assertEqual(messages[1]["content"], "Machine learning is a branch of AI...")

    def test_update_conversation_title(self):
        """Test updating title of an existing conversation."""
        conv = db.create_conversation(title="Initial Title")
        updated = db.update_conversation_title(conv["id"], "Modified Title")
        self.assertIsNotNone(updated)
        self.assertEqual(updated["title"], "Modified Title")

        # Test updating non-existent returns None
        non_existent = db.update_conversation_title("non-existent-id", "Some Title")
        self.assertIsNone(non_existent)

    def test_delete_conversation_cascades_messages(self):
        """Test deleting conversation cascades to delete associated messages."""
        conv = db.create_conversation(title="Cascade Delete Test")
        conv_id = conv["id"]
        db.add_message(conv_id, "user", "Message to be deleted")

        deleted = db.delete_conversation(conv_id)
        self.assertTrue(deleted)

        self.assertIsNone(db.get_conversation(conv_id))
        self.assertEqual(len(db.get_messages(conv_id)), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
