"""
Integration tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Aegis Learning Assistant" in response.json()["service"]

def test_read_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_ask_invalid_user_id():
    response = client.post("/ask", json={"user_id": "invalid@id!", "query": "hello"})
    assert response.status_code == 400
    assert "Invalid user ID format" in response.json()["detail"]

def test_get_profile_invalid_id():
    response = client.get("/profile/invalid%20id")
    assert response.status_code == 400
    assert "Invalid user ID format" in response.json()["detail"]

def test_get_profile_valid_id():
    # Because db is mocked without auth, it will return a default profile
    response = client.get("/profile/test_user_123")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user_123"
    assert "learning_style" in data
    assert "pace" in data

def test_quiz_generation_no_concept():
    # Asking for a quiz without setting a topic first
    response = client.post("/quiz", json={"user_id": "test_user_123"})
    assert response.status_code == 400
    assert "No concept specified" in response.json()["detail"]
    
def test_quiz_generation_with_concept():
    response = client.post("/quiz", json={"user_id": "test_user_123", "concept": "Python"})
    assert response.status_code == 200
    data = response.json()
    assert data["concept"] == "Python"
    assert "questions" in data
    assert len(data["questions"]) > 0
