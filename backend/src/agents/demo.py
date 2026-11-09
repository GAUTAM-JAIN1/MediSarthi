"""
demo.py — Synthetic persona demo session logic, seeder, and expiry purge.
"""

from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import re
import secrets
import shutil
from typing import Callable, Dict, List, Optional, Union
import uuid

import bcrypt
from agents.jwt_utils import create_access_token
from agents.rate_limit import RateLimiter, get_client_ip

logger = logging.getLogger(__name__)

DEMO_TTL_SECONDS = 2 * 60 * 60  # 2 hours


class SlidingWindowRateLimiter(RateLimiter):
    """Alias for RateLimiter allowing `limit` parameter."""

    def __init__(self, limit: int = 10, window_seconds: int = 60, **kwargs):
        super().__init__(max_requests=limit, window_seconds=window_seconds, **kwargs)


DEMO_LIMITER = SlidingWindowRateLimiter(limit=10, window_seconds=60)
client_ip = get_client_ip


def _default_persona_path() -> Path:
    # Resolves to <repo_root>/backend/data/demo/persona.json
    return Path(__file__).resolve().parents[2] / "data" / "demo" / "persona.json"


def load_persona(path: Optional[str | Path] = None) -> dict:
    """Load and validate the synthetic persona JSON data.

    Refuses to load any persona file that does not have "synthetic": true.
    """
    p = Path(path) if path is not None else _default_persona_path()
    if not p.is_file():
        raise FileNotFoundError(f"Persona file not found: {p}")

    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("synthetic") is not True:
        raise ValueError("Refusing to seed non-synthetic persona data")

    return data


def create_demo_session(
    db,
    now: Optional[datetime] = None,
    make_token: Optional[Callable[[str, int], str]] = None,
    persona_path: Optional[str | Path] = None,
) -> Dict[str, any]:
    """Seed a synthetic persona into the database and return session credentials."""
    if now is None:
        now = datetime.utcnow()

    persona = load_persona(persona_path)
    expires_at = now + timedelta(seconds=DEMO_TTL_SECONDS)

    demo_id_str = uuid.uuid4().hex[:12]
    email = f"demo_{demo_id_str}@medisarthi.demo"

    # Password is randomly generated and hashed, cannot be used for login, discarded immediately.
    rand_pw = secrets.token_urlsafe(32)
    hashed_pw = bcrypt.hashpw(rand_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    user_fields = dict(persona.get("user", {}))
    user_doc = {
        **user_fields,
        "Email": email,
        "Password": hashed_pw,
        "is_demo": True,
        "demo_expires_at": expires_at,
        "created_at": now,
    }

    res = db["Members"].insert_one(user_doc)
    user_id = str(getattr(res, "inserted_id", None) or user_doc.get("_id"))

    # Seed vitals
    for v in persona.get("vitals", []):
        days_ago = v.get("days_ago", 0)
        v_created = now - timedelta(days=days_ago)
        bp_sys = v.get("bp_systolic")
        bp_dia = v.get("bp_diastolic")
        if (bp_sys is None or bp_dia is None) and "BloodPressure" in v:
            parts = str(v["BloodPressure"]).split("/")
            if len(parts) == 2:
                try:
                    bp_sys = int(parts[0].strip())
                    bp_dia = int(parts[1].strip())
                except ValueError:
                    pass
        db["health_vitals"].insert_one({
            "user_id": user_id,
            "bp_systolic": int(bp_sys) if bp_sys is not None else None,
            "bp_diastolic": int(bp_dia) if bp_dia is not None else None,
            "blood_sugar": v.get("blood_sugar"),
            "weight": v.get("weight"),
            "notes": v.get("notes", ""),
            "date": v_created.isoformat(),
            "created_at": v_created,
            "is_demo": True,
        })

    # Seed prescriptions
    for p in persona.get("prescriptions", []):
        days_ago = p.get("days_ago", 0)
        p_created = now - timedelta(days=days_ago)
        meds = p.get("medicines")
        if meds is None and "MedicineName" in p:
            meds = [p["MedicineName"]]
        elif not isinstance(meds, list):
            meds = [str(meds)] if meds else []
        db["health_prescriptions"].insert_one({
            "user_id": user_id,
            "medicines": meds,
            "symptoms": p.get("symptoms", ""),
            "doctor_notes": p.get("doctor_notes", ""),
            "source": "demo",
            "date": p_created.isoformat(),
            "created_at": p_created,
            "is_demo": True,
        })

    # Seed emergency profile
    if "emergency_profile" in persona:
        db["emergency_profiles"].insert_one({
            "user_id": user_id,
            **persona["emergency_profile"],
            "created_at": now,
            "is_demo": True,
        })

    # Issue access token
    expires_minutes = DEMO_TTL_SECONDS // 60
    if make_token is not None:
        token = make_token(user_id, expires_minutes=expires_minutes)
    else:
        token = create_access_token(user_id, expires_minutes=expires_minutes)

    return {
        "user_id": user_id,
        "name": user_fields.get("Name", "Rahul Kumar (demo)"),
        "email": email,
        "access_token": token,
        "expires_at": expires_at.isoformat() + "Z",
        "is_demo": True,
    }


class PurgeResult(dict):
    """Result dict subclass that also compares equal to integer users_purged count for backward compatibility."""

    def __eq__(self, other):
        if isinstance(other, int):
            return self.get("users_purged") == other
        return super().__eq__(other)

    def __int__(self):
        return int(self.get("users_purged", 0))


def _user_knowledge_targets(user_id: str, knowledge_root: Path) -> List[Path]:
    """Return verified existing knowledge paths on disk for a given user.

    Validates that user_id is a valid 24-character hexadecimal ObjectId string.
    Generates candidates strictly from discovered templates:
      - user_{user_id} (directory)
      - user_{user_id}/profile.txt (file)
    Ensures resolved candidates reside strictly inside knowledge_root and
    are not knowledge_root/medical_kb. Only returns existing paths.
    """
    if not isinstance(user_id, str):
        return []
    if not re.fullmatch(r"^[0-9a-fA-F]{24}$", user_id):
        return []

    root_resolved = Path(knowledge_root).resolve()
    medical_kb_resolved = (root_resolved / "medical_kb").resolve()

    candidates = [
        root_resolved / f"user_{user_id}",
        root_resolved / f"user_{user_id}" / "profile.txt",
    ]

    targets = []
    for cand in candidates:
        if not cand.exists():
            continue
        try:
            cand_resolved = cand.resolve()
        except OSError:
            continue
        try:
            cand_resolved.relative_to(root_resolved)
        except ValueError:
            continue
        if cand_resolved == root_resolved:
            continue
        if cand_resolved == medical_kb_resolved or medical_kb_resolved in cand_resolved.parents:
            continue
        if cand_resolved not in targets:
            targets.append(cand_resolved)

    return targets


def purge_expired_demo_users(
    db,
    now: Optional[datetime] = None,
    batch: int = 200,
    knowledge_root: Optional[Path] = None,
) -> Dict[str, int]:
    """Purge expired demo users, all their associated Mongo records, and crew knowledge files.

    Returns a dict with 'users_purged', 'files_removed', and 'file_errors'.
    """
    if now is None:
        now = datetime.utcnow()

    if knowledge_root is None:
        knowledge_root = Path(__file__).resolve().parents[2] / "knowledge"
    else:
        knowledge_root = Path(knowledge_root)

    cursor = db["Members"].find(
        {"is_demo": True, "demo_expires_at": {"$lt": now}},
        {"_id": 1},
    ).limit(batch)

    expired_ids = [doc["_id"] for doc in cursor]
    if not expired_ids:
        return PurgeResult({"users_purged": 0, "files_removed": 0, "file_errors": 0})

    expired_str_ids = [str(x) for x in expired_ids]

    collections_with_user_id = [
        "health_vitals",
        "health_prescriptions",
        "emergency_profiles",
        "emergency_qr_tokens",
        "prescription_analyses",
        "lab_report_analyses",
        "blood_donors",
        "doctor_qr_tokens",
    ]

    for col in collections_with_user_id:
        try:
            db[col].delete_many({"user_id": {"$in": expired_str_ids}})
        except Exception as e:
            logger.warning("Error deleting records from %s for expired demo users: %s", col, e)

    db["Members"].delete_many({"_id": {"$in": expired_ids}})

    files_removed = 0
    file_errors = 0

    for uid in expired_str_ids:
        targets = _user_knowledge_targets(uid, knowledge_root)
        for target in targets:
            if not target.exists():
                continue
            try:
                if target.is_dir():
                    shutil.rmtree(target)
                    files_removed += 1
                elif target.is_file():
                    target.unlink()
                    files_removed += 1
            except OSError:
                file_errors += 1

    return PurgeResult({
        "users_purged": len(expired_ids),
        "files_removed": files_removed,
        "file_errors": file_errors,
    })

