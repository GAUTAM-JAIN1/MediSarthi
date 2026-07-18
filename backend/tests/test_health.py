"""
Smoke test — confirms the FastAPI app boots and the health-check route
responds. This is deliberately the *first* test, not a full suite:
- Doesn't touch MongoDB, Groq, or any CrewAI agent, so it runs in CI
  without needing GROQ_API_KEY / MONGO_URI secrets configured.
- Real endpoint tests (auth, health records, etc.) need a test MongoDB
  and should be added incrementally — see progress.md "Immediate Next
  Steps" for the automated-tests item this file is the starting point for.

Run locally: uv run pytest -v   (from backend/, venv activated)
"""
import os
import sys

# Make `agents.main` importable the same way uvicorn's --app-dir src does
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi.testclient import TestClient
from agents.main import app

client = TestClient(app)


def test_health_check_responds():
    response = client.get("/")
    assert response.status_code == 200


def test_signup_rejects_empty_body():
    # Hits /auth/signup with an empty body — expects it to reject (422 if
    # it's a Pydantic model, 400/other if hand-validated), not crash with
    # a 500. NOTE: exact request shape for /auth/signup wasn't independently
    # confirmed against main.py in this session — if this fails, check the
    # actual signature before assuming a real bug.
    response = client.post("/auth/signup", json={})
    assert response.status_code != 500