import os
import sys
import tempfile
import pytest

# Ensure backend directory is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Set temporary database path for tests before importing backend modules
temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
temp_db_path = temp_db.name
temp_db.close()
os.environ["DATABASE_PATH"] = temp_db_path

import database as db
from main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Session fixture to initialize and clean up test database."""
    db.DB_PATH = temp_db_path
    db.init_db(temp_db_path)
    yield temp_db_path
    try:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
    except Exception:
        pass


@pytest.fixture(autouse=True)
def clean_db_tables():
    """Clean database tables before each test for test isolation."""
    with db.get_db(temp_db_path) as conn:
        conn.execute("DELETE FROM messages;")
        conn.execute("DELETE FROM conversations;")
    yield


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client
