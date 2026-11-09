"""
test_demo_seed_shape.py — Unit tests verifying demo seeding aligns with the real health timeline schema.
"""

from datetime import datetime
import json
from pathlib import Path
import socket
import pytest
from bson import ObjectId

from agents.demo import create_demo_session, load_persona
from agents.health_records import get_full_timeline


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
def block_network(monkeypatch):
    """Block every socket.connect whose host is not loopback."""
    orig_connect = socket.socket.connect

    def _guarded_connect(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "::1", "localhost"):
            raise RuntimeError(f"Network calls are forbidden during catalog tests: {host}")
        return orig_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)


@pytest.fixture
def seeded_env(monkeypatch):
    """Seed demo session into FakeDB and monkeypatch health_records._get_db."""
    db = FakeDB()
    now = datetime(2026, 11, 9, 12, 0, 0)
    session = create_demo_session(db, now=now)
    user_id = session["user_id"]

    monkeypatch.setattr("agents.health_records._get_db", lambda: db)
    return db, user_id


def test_timeline_vitals_shape(seeded_env):
    """1. Every vital in the timeline has type 'vital', data.bp_systolic is int, data.blood_sugar is not None, date is a non-empty ISO string."""
    _, user_id = seeded_env
    timeline = get_full_timeline(user_id)
    vitals = [item for item in timeline if item["type"] == "vital"]

    assert len(vitals) > 0
    for v in vitals:
        assert v["type"] == "vital"
        assert isinstance(v["data"]["bp_systolic"], int)
        assert isinstance(v["data"]["bp_diastolic"], int)
        assert v["data"]["blood_sugar"] is not None
        assert isinstance(v["date"], str) and len(v["date"]) > 0
        datetime.fromisoformat(v["date"])


def test_timeline_prescriptions_shape(seeded_env):
    """2. Every prescription in the timeline has type 'prescription', data.summary is non-empty and contains a medicine name from persona.json, date is a non-empty ISO string."""
    _, user_id = seeded_env
    persona = load_persona()
    expected_med_names = set()
    for rx in persona.get("prescriptions", []):
        for med in rx.get("medicines", []):
            expected_med_names.add(med)

    timeline = get_full_timeline(user_id)
    prescriptions = [item for item in timeline if item["type"] == "prescription"]

    assert len(prescriptions) > 0
    for p in prescriptions:
        assert p["type"] == "prescription"
        summary = p["data"]["summary"]
        assert isinstance(summary, str) and len(summary) > 0
        assert any(med in summary for med in expected_med_names)
        assert isinstance(p["date"], str) and len(p["date"]) > 0
        datetime.fromisoformat(p["date"])


def test_timeline_sorted_newest_first(seeded_env):
    """3. Timeline is sorted by date, newest first."""
    _, user_id = seeded_env
    timeline = get_full_timeline(user_id)

    assert len(timeline) >= 2
    dates = [item["date"] for item in timeline]
    assert dates == sorted(dates, reverse=True)


def test_user_id_on_every_seeded_row(seeded_env):
    """4. user_id on every seeded row equals the returned user_id from create_demo_session."""
    db, user_id = seeded_env

    for col_name in ["health_vitals", "health_prescriptions", "emergency_profiles"]:
        col = db[col_name]
        assert len(col.docs) > 0
        for doc in col.docs:
            assert doc["user_id"] == user_id
            assert doc.get("is_demo") is True

