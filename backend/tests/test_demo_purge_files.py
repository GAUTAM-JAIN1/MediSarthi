"""
test_demo_purge_files.py — Unit tests for demo purge path safety and knowledge file removal.
"""

from datetime import datetime, timedelta
import os
from pathlib import Path
import shutil
import socket
import pytest
from bson import ObjectId

from agents.demo import (
    _user_knowledge_targets,
    purge_expired_demo_users,
)


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


def test_demo_user_files_purged_non_demo_stays(tmp_path):
    """1. A demo user with a created target directory and a file: purge removes it. A non-demo user with the same pattern stays."""
    db = FakeDB()
    now = datetime.utcnow()
    past = now - timedelta(hours=1)

    demo_id = ObjectId()
    db["Members"].insert_one({
        "_id": demo_id,
        "is_demo": True,
        "demo_expires_at": past,
        "Name": "Demo User",
    })

    non_demo_id = ObjectId()
    db["Members"].insert_one({
        "_id": non_demo_id,
        "is_demo": False,
        "Name": "Real User",
    })

    demo_dir = tmp_path / f"user_{demo_id}"
    demo_dir.mkdir(parents=True, exist_ok=True)
    demo_file = demo_dir / "profile.txt"
    demo_file.write_text("demo patient profile", encoding="utf-8")

    non_demo_dir = tmp_path / f"user_{non_demo_id}"
    non_demo_dir.mkdir(parents=True, exist_ok=True)
    non_demo_file = non_demo_dir / "profile.txt"
    non_demo_file.write_text("real patient profile", encoding="utf-8")

    res = purge_expired_demo_users(db, now=now, knowledge_root=tmp_path)

    assert res["users_purged"] == 1
    assert not demo_dir.exists()
    assert not demo_file.exists()

    assert non_demo_dir.exists()
    assert non_demo_file.exists()


def test_traversal_user_id_returns_empty_and_deletes_nothing(tmp_path):
    """2. User id '..': _user_knowledge_targets returns [] and nothing is deleted."""
    sentinel = tmp_path / "sentinel.txt"
    sentinel.write_text("important system file", encoding="utf-8")

    assert _user_knowledge_targets("..", tmp_path) == []
    assert _user_knowledge_targets("../..", tmp_path) == []
    assert _user_knowledge_targets("user_..", tmp_path) == []
    assert _user_knowledge_targets("not_a_valid_hex_id", tmp_path) == []

    assert sentinel.exists()


def test_medical_kb_never_deleted(tmp_path):
    """3. medical_kb under tmp_path is never deleted. If symlinks cannot be created in this environment, record NOT VERIFIED for this item. Do not skip it silently."""
    medical_kb = tmp_path / "medical_kb"
    medical_kb.mkdir(parents=True, exist_ok=True)
    kb_file = medical_kb / "drug_interactions.txt"
    kb_file.write_text("drug interaction reference base", encoding="utf-8")

    demo_id = ObjectId()
    demo_str = str(demo_id)
    symlink_target = tmp_path / f"user_{demo_str}"

    try:
        os.symlink(medical_kb, symlink_target, target_is_directory=True)
    except OSError:
        # Prompt 09d Step 3a.3: If symlinks cannot be created in this environment, record NOT VERIFIED for this item.
        pytest.skip("Symlink privilege not held on Windows (WinError 1314); symlink guard NOT VERIFIED in OS, recorded in claims table")

    targets = _user_knowledge_targets(demo_str, tmp_path)
    assert medical_kb.resolve() not in targets
    assert targets == []

    db = FakeDB()
    now = datetime.utcnow()
    db["Members"].insert_one({
        "_id": demo_id,
        "is_demo": True,
        "demo_expires_at": now - timedelta(hours=1),
    })

    purge_expired_demo_users(db, now=now, knowledge_root=tmp_path)

    assert medical_kb.exists()
    assert kb_file.exists()


def test_batch_limit_respected(tmp_path):
    """4. Three expired demo users, batch=2: exactly 2 purged."""
    db = FakeDB()
    now = datetime.utcnow()
    past = now - timedelta(hours=1)

    ids = [ObjectId(), ObjectId(), ObjectId()]
    for uid in ids:
        db["Members"].insert_one({
            "_id": uid,
            "is_demo": True,
            "demo_expires_at": past,
            "Name": f"Demo {uid}",
        })
        u_dir = tmp_path / f"user_{uid}"
        u_dir.mkdir(parents=True, exist_ok=True)
        (u_dir / "profile.txt").write_text("dummy", encoding="utf-8")

    res = purge_expired_demo_users(db, now=now, batch=2, knowledge_root=tmp_path)

    assert res["users_purged"] == 2
    assert db["Members"].count_documents({"is_demo": True}) == 1


def test_rmtree_oserror_counted_and_does_not_escape(monkeypatch, tmp_path):
    """5. shutil.rmtree raises OSError for one user (monkeypatch): file_errors >= 1, the other demo user is still purged, no exception escapes."""
    db = FakeDB()
    now = datetime.utcnow()
    past = now - timedelta(hours=1)

    u1 = ObjectId()
    u2 = ObjectId()

    for uid in [u1, u2]:
        db["Members"].insert_one({
            "_id": uid,
            "is_demo": True,
            "demo_expires_at": past,
            "Name": f"Demo {uid}",
        })
        u_dir = tmp_path / f"user_{uid}"
        u_dir.mkdir(parents=True, exist_ok=True)
        (u_dir / "profile.txt").write_text("dummy", encoding="utf-8")

    orig_rmtree = shutil.rmtree

    def mock_rmtree(path, *args, **kwargs):
        if f"user_{u1}" in str(path):
            raise OSError("Simulated disk error")
        return orig_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(shutil, "rmtree", mock_rmtree)

    res = purge_expired_demo_users(db, now=now, knowledge_root=tmp_path)

    assert res["file_errors"] >= 1
    assert res["users_purged"] == 2
    assert (tmp_path / f"user_{u1}").exists()  # Orphan folder remains on disk due to simulated OSError
    assert not (tmp_path / f"user_{u2}").exists()
    assert db["Members"].count_documents({"is_demo": True}) == 0
