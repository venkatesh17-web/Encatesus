"""
Automated Test Suite for Gemini AI Chat Application Backend & Frontend.

Covers:
1. Health Check endpoint (/api/health)
2. Models endpoint (/api/models)
3. Conversations CRUD endpoints (/api/conversations)
4. Streaming chat endpoint (/api/chat/stream) with SSE chunks verification
5. Frontend static serving at / and /index.html
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, AsyncMock
from typing import List, Dict, Any

# Ensure backend directory is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Configure temporary test database
temp_db = tempfile.NamedTemporaryFile(suffix="_test_api.db", delete=False)
TEST_DB_PATH = temp_db.name
temp_db.close()
os.environ["DATABASE_PATH"] = TEST_DB_PATH

import database as db
import gemini_service
from main import app
from fastapi.testclient import TestClient


def parse_sse_events(response_text: str) -> List[Dict[str, Any]]:
    """Helper to parse Server-Sent Events (SSE) data stream into JSON objects."""
    events = []
    for line in response_text.split("\n"):
        line = line.strip()
        if line.startswith("data:"):
            data_content = line[len("data:"):].strip()
            if data_content:
                try:
                    events.append(json.loads(data_content))
                except json.JSONDecodeError:
                    pass
    return events


class TestHealthEndpoint(unittest.TestCase):
    """Test suite for /api/health."""

    def setUp(self):
        db.DB_PATH = TEST_DB_PATH
        db.init_db(TEST_DB_PATH)
        self.client = TestClient(app)

    def test_health_check_default(self):
        """Verify health check returns ok status and models count."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("gemini_configured", data)
        self.assertIsInstance(data.get("gemini_configured"), bool)
        self.assertGreaterEqual(data.get("models_count", 0), 3)

    def test_health_check_with_custom_header(self):
        """Verify health check recognizes custom API key header."""
        headers = {"x-gemini-api-key": "test-valid-custom-key-12345"}
        response = self.client.get("/api/health", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertTrue(data.get("gemini_configured"))


class TestModelsEndpoint(unittest.TestCase):
    """Test suite for /api/models."""

    def setUp(self):
        self.client = TestClient(app)

    def test_get_models_list(self):
        """Verify models endpoint returns valid list of models with required fields."""
        response = self.client.get("/api/models")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("models", data)
        models = data["models"]
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)

        # Verify model object structure
        model_ids = [m.get("id") for m in models]
        self.assertIn("gemini-3.5-flash-lite", model_ids)
        
        for m in models:
            self.assertIn("id", m)
            self.assertIn("name", m)
            self.assertIn("description", m)
            self.assertIn("is_default", m)
            self.assertIsInstance(m["is_default"], bool)


class TestConversationsCRUD(unittest.TestCase):
    """Test suite for Conversations CRUD endpoints."""

    def setUp(self):
        db.DB_PATH = TEST_DB_PATH
        db.init_db(TEST_DB_PATH)
        # Clear tables
        with db.get_db(TEST_DB_PATH) as conn:
            conn.execute("DELETE FROM messages;")
            conn.execute("DELETE FROM conversations;")
        self.client = TestClient(app)

    def test_create_conversation_default(self):
        """Test creating a conversation with default attributes."""
        response = self.client.post("/api/conversations", json={})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data.get("title"), "New Chat")
        self.assertEqual(data.get("model"), "gemini-1.5-flash")
        self.assertEqual(data.get("messages"), [])

    def test_create_conversation_custom(self):
        """Test creating a conversation with custom title and model."""
        payload = {
            "title": "Quantum Physics Research",
            "model": "gemini-1.5-pro"
        }
        response = self.client.post("/api/conversations", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data.get("title"), "Quantum Physics Research")
        self.assertEqual(data.get("model"), "gemini-1.5-pro")

    def test_list_conversations(self):
        """Test listing multiple conversations."""
        # Create two conversations
        self.client.post("/api/conversations", json={"title": "Chat 1"})
        self.client.post("/api/conversations", json={"title": "Chat 2"})

        response = self.client.get("/api/conversations")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("conversations", data)
        convs = data["conversations"]
        self.assertEqual(len(convs), 2)
        titles = [c["title"] for c in convs]
        self.assertIn("Chat 1", titles)
        self.assertIn("Chat 2", titles)

    def test_get_conversation_by_id(self):
        """Test retrieving a single conversation by ID with message history."""
        # Create conversation
        create_res = self.client.post("/api/conversations", json={"title": "Detail Chat"})
        conv_id = create_res.json()["id"]

        # Add messages directly via db
        db.add_message(conv_id, "user", "Hello there")
        db.add_message(conv_id, "assistant", "General Kenobi!")

        response = self.client.get(f"/api/conversations/{conv_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], conv_id)
        self.assertEqual(data["title"], "Detail Chat")
        self.assertEqual(len(data["messages"]), 2)
        self.assertEqual(data["messages"][0]["role"], "user")
        self.assertEqual(data["messages"][0]["content"], "Hello there")
        self.assertEqual(data["messages"][1]["role"], "assistant")
        self.assertEqual(data["messages"][1]["content"], "General Kenobi!")

    def test_get_conversation_not_found(self):
        """Test retrieving a non-existent conversation returns 404."""
        response = self.client.get("/api/conversations/non-existent-uuid-12345")
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    def test_update_conversation_title(self):
        """Test updating conversation title."""
        create_res = self.client.post("/api/conversations", json={"title": "Original Title"})
        conv_id = create_res.json()["id"]

        update_res = self.client.patch(f"/api/conversations/{conv_id}", json={"title": "Updated Title"})
        self.assertEqual(update_res.status_code, 200)
        updated_data = update_res.json()
        self.assertEqual(updated_data["title"], "Updated Title")

        # Verify update persisted
        get_res = self.client.get(f"/api/conversations/{conv_id}")
        self.assertEqual(get_res.json()["title"], "Updated Title")

    def test_update_conversation_not_found(self):
        """Test updating non-existent conversation returns 404."""
        response = self.client.patch("/api/conversations/unknown-id", json={"title": "New Title"})
        self.assertEqual(response.status_code, 404)

    def test_update_conversation_validation_error(self):
        """Test updating conversation with empty title returns 422."""
        create_res = self.client.post("/api/conversations", json={"title": "Valid Title"})
        conv_id = create_res.json()["id"]

        response = self.client.patch(f"/api/conversations/{conv_id}", json={"title": ""})
        self.assertEqual(response.status_code, 422)

    def test_delete_conversation(self):
        """Test deleting conversation removes it and its messages."""
        create_res = self.client.post("/api/conversations", json={"title": "To Delete"})
        conv_id = create_res.json()["id"]
        db.add_message(conv_id, "user", "Test message")

        delete_res = self.client.delete(f"/api/conversations/{conv_id}")
        self.assertEqual(delete_res.status_code, 200)
        self.assertEqual(delete_res.json().get("status"), "deleted")
        self.assertEqual(delete_res.json().get("id"), conv_id)

        # Verify get returns 404
        get_res = self.client.get(f"/api/conversations/{conv_id}")
        self.assertEqual(get_res.status_code, 404)

        # Verify messages are deleted
        messages = db.get_messages(conv_id)
        self.assertEqual(len(messages), 0)

    def test_delete_conversation_not_found(self):
        """Test deleting non-existent conversation returns 404."""
        response = self.client.delete("/api/conversations/unknown-id-xyz")
        self.assertEqual(response.status_code, 404)


class TestChatStreamingSSE(unittest.TestCase):
    """Test suite for SSE Streaming endpoint /api/chat/stream."""

    def setUp(self):
        db.DB_PATH = TEST_DB_PATH
        db.init_db(TEST_DB_PATH)
        with db.get_db(TEST_DB_PATH) as conn:
            conn.execute("DELETE FROM messages;")
            conn.execute("DELETE FROM conversations;")
        self.client = TestClient(app)

    def test_stream_new_conversation_mock_mode(self):
        """Test chat streaming creates conversation and yields start, chunk, and done events."""
        payload = {
            "message": "Hello Gemini, tell me about algorithms",
            "model": "gemini-1.5-flash"
        }
        
        response = self.client.post("/api/chat/stream", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers.get("content-type", ""))

        events = parse_sse_events(response.text)
        self.assertGreaterEqual(len(events), 3, "Expected at least start, chunk, and done events")

        # 1. Start event
        start_event = events[0]
        self.assertEqual(start_event.get("type"), "start")
        self.assertTrue(start_event.get("is_new"))
        conv_id = start_event.get("conversation_id")
        self.assertIsNotNone(conv_id)
        self.assertEqual(start_event.get("user_message", {}).get("content"), payload["message"])

        # 2. Chunk events
        chunk_events = [e for e in events if e.get("type") == "chunk"]
        self.assertGreater(len(chunk_events), 0)
        for chunk in chunk_events:
            self.assertIn("content", chunk)
            self.assertIsInstance(chunk["content"], str)

        # 3. Done event
        done_event = events[-1]
        self.assertEqual(done_event.get("type"), "done")
        self.assertEqual(done_event.get("conversation_id"), conv_id)
        asst_msg = done_event.get("message")
        self.assertIsNotNone(asst_msg)
        self.assertEqual(asst_msg.get("role"), "assistant")
        self.assertGreater(len(asst_msg.get("content", "")), 0)

        # 4. Verify DB persistence
        conv = db.get_conversation(conv_id)
        self.assertIsNotNone(conv)
        self.assertEqual(len(conv["messages"]), 2)
        self.assertEqual(conv["messages"][0]["role"], "user")
        self.assertEqual(conv["messages"][1]["role"], "assistant")

    def test_stream_existing_conversation(self):
        """Test chat streaming with an existing conversation ID."""
        # Pre-create conversation
        conv = db.create_conversation(title="Pre-existing Chat", model="gemini-1.5-flash")
        conv_id = conv["id"]

        payload = {
            "conversation_id": conv_id,
            "message": "Follow up question",
            "model": "gemini-1.5-flash"
        }

        response = self.client.post("/api/chat/stream", json=payload)
        self.assertEqual(response.status_code, 200)

        events = parse_sse_events(response.text)
        start_event = events[0]
        self.assertEqual(start_event.get("type"), "start")
        self.assertFalse(start_event.get("is_new"))
        self.assertEqual(start_event.get("conversation_id"), conv_id)

        # Verify DB messages count
        messages = db.get_messages(conv_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], "Follow up question")

    def test_stream_with_mocked_gemini_generator(self):
        """Test chat streaming with mock generator yielding specific tokens."""
        async def mock_generator(*args, **kwargs):
            tokens = ["Python ", "is ", "a ", "powerful ", "programming ", "language."]
            for token in tokens:
                yield token

        with patch("gemini_service.stream_gemini_response", side_effect=mock_generator):
            payload = {
                "message": "What is Python?",
                "model": "gemini-2.5-flash"
            }
            response = self.client.post("/api/chat/stream", json=payload)
            self.assertEqual(response.status_code, 200)

            events = parse_sse_events(response.text)
            chunks = [e["content"] for e in events if e.get("type") == "chunk"]
            expected_tokens = ["Python ", "is ", "a ", "powerful ", "programming ", "language."]
            self.assertEqual(chunks, expected_tokens)

            done_event = [e for e in events if e.get("type") == "done"][0]
            self.assertEqual(done_event["message"]["content"], "Python is a powerful programming language.")

    def test_stream_error_handling(self):
        """Test streaming error gracefully emits error event before done event."""
        async def mock_error_generator(*args, **kwargs):
            yield "Starting..."
            raise RuntimeError("Simulated Gemini API failure")

        with patch("gemini_service.stream_gemini_response", side_effect=mock_error_generator):
            payload = {
                "message": "Trigger error test",
                "model": "gemini-1.5-flash"
            }
            response = self.client.post("/api/chat/stream", json=payload)
            self.assertEqual(response.status_code, 200)

            events = parse_sse_events(response.text)
            error_events = [e for e in events if e.get("type") == "error"]
            self.assertEqual(len(error_events), 1)
            self.assertIn("Simulated Gemini API failure", error_events[0]["error"])

            done_events = [e for e in events if e.get("type") == "done"]
            self.assertEqual(len(done_events), 1)

    def test_stream_validation_failure(self):
        """Test streaming with empty message returns 422 Unprocessable Entity."""
        response = self.client.post("/api/chat/stream", json={"message": ""})
        self.assertEqual(response.status_code, 422)


class TestFrontendServing(unittest.TestCase):
    """Test suite for static frontend asset and page serving."""

    def setUp(self):
        self.client = TestClient(app)

    def test_root_serves_index_html(self):
        """GET / should serve index.html with HTML Content-Type."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("Encatesus AI Chat", response.text)

    def test_index_html_explicit_route(self):
        """GET /index.html should serve index.html."""
        response = self.client.get("/index.html")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("<!DOCTYPE html>", response.text)

    def test_static_css_serving(self):
        """GET /css/styles.css should serve CSS stylesheet."""
        response = self.client.get("/css/styles.css")
        self.assertEqual(response.status_code, 200)
        self.assertIn("var(--bg-main)", response.text)

    def test_static_js_serving(self):
        """GET /js/app.js should serve application JavaScript."""
        response = self.client.get("/js/app.js")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Encatesus", response.text)

    def test_api_404_not_routed_to_frontend(self):
        """GET /api/nonexistent should return 404 API error rather than index.html."""
        response = self.client.get("/api/unknown-endpoint-xyz")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data.get("detail"), "API endpoint not found")


if __name__ == "__main__":
    unittest.main(verbosity=2)
