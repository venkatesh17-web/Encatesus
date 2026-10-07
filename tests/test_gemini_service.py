"""
Unit tests for Gemini Service module (backend/gemini_service.py).
"""

import os
import sys
import unittest
import asyncio

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import gemini_service


class TestGeminiService(unittest.TestCase):
    """Test suite for gemini_service.py helper functions."""

    def test_available_models_list(self):
        """Verify AVAILABLE_MODELS contains the required models."""
        models = gemini_service.AVAILABLE_MODELS
        self.assertIsInstance(models, list)
        self.assertGreaterEqual(len(models), 3)

        model_ids = [m["id"] for m in models]
        self.assertIn("gemini-3.5-flash-lite", model_ids)
        self.assertIn("gemini-flash-lite-latest", model_ids)
        self.assertIn("gemini-3.8-flash", model_ids)

        default_models = [m for m in models if m.get("is_default")]
        self.assertEqual(len(default_models), 1, "There should be exactly one default model")

    def test_is_gemini_configured(self):
        """Verify is_gemini_configured with custom and empty keys."""
        from unittest.mock import patch
        self.assertTrue(gemini_service.is_gemini_configured("custom-api-key"))
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            self.assertFalse(gemini_service.is_gemini_configured(""))
            self.assertFalse(gemini_service.is_gemini_configured(None))
        with patch.dict(os.environ, {"GEMINI_API_KEY": "valid-env-key"}):
            self.assertTrue(gemini_service.is_gemini_configured())

    def test_format_history_for_gemini_empty(self):
        """Test formatting history with single user prompt."""
        contents = gemini_service._format_history_for_gemini([], "Hello world")
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0]["role"], "user")
        self.assertEqual(contents[0]["parts"][0]["text"], "Hello world")

    def test_format_history_for_gemini_multi_turn(self):
        """Test formatting multi-turn conversation history."""
        messages = [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "2+2 is 4."},
        ]
        contents = gemini_service._format_history_for_gemini(messages, "What is 4+4?")
        self.assertEqual(len(contents), 3)
        self.assertEqual(contents[0]["role"], "user")
        self.assertEqual(contents[0]["parts"][0]["text"], "What is 2+2?")
        self.assertEqual(contents[1]["role"], "model")
        self.assertEqual(contents[1]["parts"][0]["text"], "2+2 is 4.")
        self.assertEqual(contents[2]["role"], "user")
        self.assertEqual(contents[2]["parts"][0]["text"], "What is 4+4?")

    def test_mock_stream_response(self):
        """Test _mock_stream_response yields non-empty string chunks."""
        async def collect_chunks():
            chunks = []
            async for chunk in gemini_service._mock_stream_response("Test prompt", reason="no_key"):
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(collect_chunks())
        self.assertGreater(len(chunks), 0)
        full_text = "".join(chunks)
        self.assertIn("Welcome to the Encatesus AI Chat", full_text)
        self.assertIn("Test prompt", full_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
