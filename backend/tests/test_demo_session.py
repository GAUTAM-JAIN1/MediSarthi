"""
test_demo_session.py — Unit tests for demo session creation, token expiry,
data seeding, expiration purge, and rate limiting.
"""

from datetime import datetime, timedelta
import json
import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
import jwt

from agents.main import app
from agents.demo import (
    DEMO_LIMITER,
    DEMO_TTL_SECONDS,
    create_demo_session,
    load_persona,
    purge_expired_demo_users,
)
from agents.jwt_utils import create_access_token, decode_access_token


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def limit(self, n: int):
        return FakeCursor(self.docs[:n])

    def __iter__(self):
        return iter(self.docs)

    def __len__(self):
        return len(self.docs)


class FakeCollection:
    def __init__(self):
        self.docs = []

    def insert_one(self, doc):
        d = dict(doc)
        if "_id" not in d:
            d["_id"] = ObjectId()
        self.docs.append(d)

        class Result:
            inserted_id = d["_id"]

        return Result()

    def find(self, query=None, projection=None):
        query = query or {}
        matches = []
        for d in self.docs:
            matched = True
            for k, v in query.items():
                if isinstance(v, dict):
                    if "$lt" in v:
                        val = d.get(k)
                        if val is None or not (val < v["$lt"]):
                            matched = False
                    if "$in" in v:
                        val = d.get(k)
                        if val not in v["$in"]:
                            matched = False
                elif d.get(k) != v:
                    matched = False
            if matched:
                matches.append(d)
        return FakeCursor(matches)

    def find_one(self, query=None):
        cursor = self.find(query)
        if cursor.docs:
            return cursor.docs[0]
        return None

    def delete_many(self, query=None):
        query = query or {}
        remaining = []
        deleted = 0
        for d in self.docs:
            matched = True
            for k, v in query.items():
                if isinstance(v, dict):
                    if "$in" in v:
                        val = d.get(k)
                        if val not in v["$in"]:
                            matched = False
                elif d.get(k) != v:
                    matched = False
            if matched:
                deleted += 1
            else:
                remaining.append(d)
        self.docs = remaining

        class Result:
            deleted_count = deleted

        return Result()

    def count_documents(self, query=None):
        return len(self.find(query).docs)


class FakeDB:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name: str):
        if name not in self.collections:
            self.collections[name] = FakeCollection()
        return self.collections[name]


@pytest.fixture(autouse=True)
def mock_startup_and_reset(monkeypatch):
    DEMO_LIMITER.reset()
    monkeypatch.setattr("agents.main.ensure_indexes", lambda: None)
    yield
    DEMO_LIMITER.reset()


@pytest.fixture
def fake_db(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr("agents.routes.demo.get_database", lambda: db)
    monkeypatch.setattr("agents.auth._get_collection", lambda: db["Members"])
    return db


def test_demo_session_disabled_returns_403(monkeypatch, fake_db):
    """When DEMO_MODE_ENABLED is unset or false, POST /demo/session returns 403."""
    monkeypatch.delenv("DEMO_MODE_ENABLED", raising=False)
    client = TestClient(app)
    response = client.post("/demo/session")
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


def test_demo_session_enabled_creates_user_and_token(monkeypatch, fake_db):
    """When enabled, POST /demo/session returns 200 with session details and valid token."""
    monkeypatch.setenv("DEMO_MODE_ENABLED", "true")
    client = TestClient(app)
    response = client.post("/demo/session")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"]
    assert data["name"] == "Rahul Kumar (demo)"
    assert data["is_demo"] is True
    assert data["expires_at"].endswith("Z")

    # Verify token decodes to user_id
    decoded_uid = decode_access_token(data["access_token"])
    assert decoded_uid == data["user_id"]


def test_demo_token_expiry_is_short(monkeypatch):
    """Demo token expires in ~7200 seconds, compared to 7 days for standard tokens."""
    token = create_access_token("test-demo-user", expires_minutes=120)
    payload = jwt.decode(token, options={"verify_signature": False})
    duration = payload["exp"] - payload["iat"]
    assert abs(duration - 7200) <= 5

    # Standard token comparison (7 days = 604800 seconds)
    std_token = create_access_token("test-std-user")
    std_payload = jwt.decode(std_token, options={"verify_signature": False})
    std_duration = std_payload["exp"] - std_payload["iat"]
    assert std_duration == 7 * 24 * 3600


def test_demo_session_seeds_vitals_and_prescriptions(monkeypatch, fake_db):
    """Demo session creation populates Members, vitals, prescriptions, and emergency profile."""
    monkeypatch.setenv("DEMO_MODE_ENABLED", "true")
    client = TestClient(app)
    res = client.post("/demo/session")
    assert res.status_code == 200
    user_id = res.json()["user_id"]

    # Members doc
    member = fake_db["Members"].find_one({"_id": ObjectId(user_id)})
    assert member is not None
    assert member["is_demo"] is True
    assert member["demo_expires_at"] > datetime.utcnow()

    # Vitals
    vitals = list(fake_db["health_vitals"].find({"user_id": user_id}))
    assert len(vitals) == 2
    for v in vitals:
        assert v["is_demo"] is True
        assert v["created_at"] < datetime.utcnow()

    # Prescriptions
    rxs = list(fake_db["health_prescriptions"].find({"user_id": user_id}))
    assert len(rxs) == 2
    med_names = {r["MedicineName"] for r in rxs}
    assert "Paracetamol Tablets IP 650 mg" in med_names
    assert "Amlodipine" in med_names

    # Emergency profile
    ep = fake_db["emergency_profiles"].find_one({"user_id": user_id})
    assert ep is not None
    assert ep["FullName"] == "Rahul Kumar"
    assert ep["BloodGroup"] == "O+"
    assert ep["is_demo"] is True


def test_purge_deletes_expired_and_preserves_active(fake_db):
    """purge_expired_demo_users removes expired demo records but leaves active and real users."""
    now = datetime.utcnow()
    past = now - timedelta(hours=1)
    future = now + timedelta(hours=1)

    # 1. Expired demo user
    exp_id = ObjectId()
    fake_db["Members"].insert_one({
        "_id": exp_id,
        "is_demo": True,
        "demo_expires_at": past,
        "Name": "Expired Demo",
    })
    fake_db["health_vitals"].insert_one({"user_id": str(exp_id), "is_demo": True})
    fake_db["health_prescriptions"].insert_one({"user_id": str(exp_id), "is_demo": True})
    fake_db["emergency_profiles"].insert_one({"user_id": str(exp_id), "is_demo": True})

    # 2. Active demo user
    act_id = ObjectId()
    fake_db["Members"].insert_one({
        "_id": act_id,
        "is_demo": True,
        "demo_expires_at": future,
        "Name": "Active Demo",
    })
    fake_db["health_vitals"].insert_one({"user_id": str(act_id), "is_demo": True})
    fake_db["health_prescriptions"].insert_one({"user_id": str(act_id), "is_demo": True})

    # 3. Real user (no is_demo)
    real_id = ObjectId()
    fake_db["Members"].insert_one({
        "_id": real_id,
        "Name": "Real User",
    })
    fake_db["health_vitals"].insert_one({"user_id": str(real_id)})

    # Run purge
    deleted_count = purge_expired_demo_users(fake_db, now=now)
    assert deleted_count == 1

    # Verify expired demo user is gone
    assert fake_db["Members"].find_one({"_id": exp_id}) is None
    assert fake_db["health_vitals"].find_one({"user_id": str(exp_id)}) is None
    assert fake_db["health_prescriptions"].find_one({"user_id": str(exp_id)}) is None
    assert fake_db["emergency_profiles"].find_one({"user_id": str(exp_id)}) is None

    # Verify active demo user remains
    assert fake_db["Members"].find_one({"_id": act_id}) is not None
    assert fake_db["health_vitals"].find_one({"user_id": str(act_id)}) is not None

    # Verify real user remains
    assert fake_db["Members"].find_one({"_id": real_id}) is not None
    assert fake_db["health_vitals"].find_one({"user_id": str(real_id)}) is not None


def test_load_persona_rejects_non_synthetic(tmp_path):
    """load_persona raises ValueError if synthetic is not True."""
    bad_file = tmp_path / "persona_bad.json"
    bad_file.write_text(json.dumps({"synthetic": False, "Name": "Real Person"}), encoding="utf-8")

    with pytest.raises(ValueError, match="non-synthetic"):
        load_persona(bad_file)


def test_demo_session_rate_limiter(monkeypatch, fake_db):
    """11th demo session request within 60s window returns HTTP 429."""
    monkeypatch.setenv("DEMO_MODE_ENABLED", "true")
    client = TestClient(app)

    for i in range(10):
        res = client.post("/demo/session")
        assert res.status_code == 200, f"Request {i+1} failed"

    # 11th request exceeds limit
    res_11 = client.post("/demo/session")
    assert res_11.status_code == 429
    assert "Too many demo sessions" in res_11.json()["detail"]


def test_demo_password_cannot_be_used_for_login(monkeypatch, fake_db):
    """The random discarded demo password cannot be guessed or used for auth login."""
    monkeypatch.setenv("DEMO_MODE_ENABLED", "true")
    client = TestClient(app)
    res = client.post("/demo/session")
    assert res.status_code == 200
    user_id = res.json()["user_id"]

    member = fake_db["Members"].find_one({"_id": ObjectId(user_id)})
    demo_email = member["Email"]

    # Try logging in with arbitrary passwords
    for pw in ["", "password", "demo123", "secret"]:
        login_res = client.post("/auth/login", json={"email": demo_email, "password": pw})
        assert login_res.status_code == 401
