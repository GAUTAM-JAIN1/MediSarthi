"""
health_records.py — MediSarthi health records backend
MongoDB collections: health_vitals, health_prescriptions, emergency_profiles,
emergency_qr_tokens, prescription_analyses, lab_report_analyses (medical_db)
"""

import secrets
from datetime import datetime
from bson import ObjectId


def _get_db():
    """Lazy load — sirf tab connect karo jab actually zaroorat ho."""
    from agents.db_connect import get_database
    db = get_database()
    if db is None:
        raise RuntimeError("Database connection unavailable")
    return db


def _serialize(doc):
    """MongoDB doc ko JSON-safe dict mein convert karo."""
    if doc is None:
        return None
    doc = dict(doc)
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    if "user_id" in doc:
        doc["user_id"] = str(doc["user_id"])
    return doc


# ── Vitals ───────────────────────────────────────────────────────────────────

def add_vital(
    user_id: str,
    vital_type: str,
    value: float,
    unit: str,
    notes: str = "",
    bp_systolic: float = None,
    bp_diastolic: float = None,
    blood_sugar: float = None,
    weight: float = None,
) -> str:
    """
    Naya vital record add karo. Generic vital_type/value/unit ke saath-saath
    granular fields (BP/sugar/weight) bhi store karte hain.
    Returns: inserted record's id (string).
    """
    db = _get_db()
    collection = db["health_vitals"]

    doc = {
        "user_id": user_id,
        "vital_type": vital_type,
        "value": value,
        "unit": unit,
        "notes": notes,
        "bp_systolic": bp_systolic,
        "bp_diastolic": bp_diastolic,
        "blood_sugar": blood_sugar,
        "weight": weight,
        "date": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
    }

    result = collection.insert_one(doc)
    return str(result.inserted_id)


def get_vitals(user_id: str, vital_type: str = None, limit: int = 30) -> list:
    """Ek user ke vitals fetch karo, optionally type se filter karke."""
    db = _get_db()
    collection = db["health_vitals"]

    query = {"user_id": user_id}
    if vital_type:
        query["vital_type"] = vital_type

    cursor = collection.find(query, sort=[("date", -1)], limit=limit)
    return [_serialize(doc) for doc in cursor]


# ── Prescriptions ─────────────────────────────────────────────────────────────

def add_prescription(
    user_id: str,
    medicines: list,
    symptoms: str = "",
    doctor_notes: str = "",
    source: str = "manual",
) -> str:
    """Prescription record add karo (manual entry ya AI consultation se)."""
    db = _get_db()
    collection = db["health_prescriptions"]

    doc = {
        "user_id": user_id,
        "medicines": medicines or [],
        "symptoms": symptoms,
        "doctor_notes": doctor_notes,
        "source": source,
        "date": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
    }

    result = collection.insert_one(doc)
    return str(result.inserted_id)


def get_prescriptions(user_id: str, limit: int = 20) -> list:
    """Ek user ke prescriptions fetch karo."""
    db = _get_db()
    collection = db["health_prescriptions"]

    cursor = collection.find({"user_id": user_id}, sort=[("date", -1)], limit=limit)
    return [_serialize(doc) for doc in cursor]


# ── Prescription analysis ─────────────────────────────────────────────────────
#
# Permission-based save — consultation chalne se record apne aap save NAHI hota.
# Sirf jab user explicitly confirm kare tabhi save hota hai.

def save_prescription_analysis(
    user_id: str,
    overall_summary: str,
    medicines: list,
    has_allergy_conflict: bool,
    safety_note: str,
    source: str = "voice",
    raw_medicines: list = None,
) -> str:
    """Prescription analysis permanently save karo — sirf user confirmation ke baad."""
    db = _get_db()
    collection = db["prescription_analyses"]

    doc = {
        "user_id": user_id,
        "overall_summary": overall_summary or "",
        "medicines": medicines or [],
        "has_allergy_conflict": bool(has_allergy_conflict),
        "safety_note": safety_note or "",
        "source": source,
        "raw_medicines": raw_medicines or [],
        "date": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
    }

    result = collection.insert_one(doc)
    return str(result.inserted_id)


def get_prescription_analyses(user_id: str, limit: int = 20) -> list:
    """Ek user ke saare saved prescription analyses fetch karo (newest first)."""
    db = _get_db()
    collection = db["prescription_analyses"]

    cursor = collection.find({"user_id": user_id}, sort=[("date", -1)], limit=limit)
    return [_serialize(doc) for doc in cursor]


def get_prescription_analysis_by_id(user_id: str, analysis_id: str) -> dict:
    """Ek specific saved analysis fetch karo (detail view ke liye)."""
    db = _get_db()
    collection = db["prescription_analyses"]

    try:
        oid = ObjectId(analysis_id)
    except Exception:
        return None

    doc = collection.find_one({"_id": oid, "user_id": user_id})
    return _serialize(doc)


# ── Lab report analysis (NEW) ─────────────────────────────────────────────────
#
# Same permission-gated pattern as prescription_analyses.
# User uploads lab report → AI analyses it → result shown in UI.
# Nothing saved to DB until user taps "Save to records".

def save_lab_report_analysis(
    user_id: str,
    report_type: str,
    overall_summary: str,
    tests: list,
    urgent_flags: list,
    has_urgent_values: bool,
    next_steps: str,
    disclaimer: str,
    raw_text: str = "",
) -> str:
    """
    Lab report analysis permanently save karo — sirf user confirmation ke baad.

    Args:
        user_id: konsa user.
        report_type: CBC, Lipid Profile, etc.
        overall_summary: plain-language overall picture.
        tests: list of dicts — har dict mein test_name/value/normal_range/status/
               plain_explanation/action_needed.
        urgent_flags: list of test names that are Critical Low/High.
        has_urgent_values: bool.
        next_steps: overall recommendation.
        disclaimer: AI reminder text.
        raw_text: original OCR text (optional, for reference).

    Returns: inserted record's id (string).
    """
    db = _get_db()
    collection = db["lab_report_analyses"]

    doc = {
        "user_id": user_id,
        "report_type": report_type or "Unknown",
        "overall_summary": overall_summary or "",
        "tests": tests or [],
        "urgent_flags": urgent_flags or [],
        "has_urgent_values": bool(has_urgent_values),
        "next_steps": next_steps or "",
        "disclaimer": disclaimer or "",
        "raw_text": raw_text or "",
        "date": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
    }

    result = collection.insert_one(doc)
    return str(result.inserted_id)


def get_lab_report_analyses(user_id: str, limit: int = 20) -> list:
    """
    Ek user ke saare saved lab report analyses fetch karo (newest first).
    Returns: list of analysis dicts.
    """
    db = _get_db()
    collection = db["lab_report_analyses"]

    cursor = collection.find({"user_id": user_id}, sort=[("date", -1)], limit=limit)
    return [_serialize(doc) for doc in cursor]


def get_lab_report_analysis_by_id(user_id: str, analysis_id: str) -> dict:
    """Ek specific lab report analysis fetch karo."""
    db = _get_db()
    collection = db["lab_report_analyses"]

    try:
        oid = ObjectId(analysis_id)
    except Exception:
        return None

    doc = collection.find_one({"_id": oid, "user_id": user_id})
    return _serialize(doc)


# ── Combined timeline ─────────────────────────────────────────────────────────

def get_full_timeline(user_id: str, limit: int = 50) -> list:
    """
    Vitals + prescriptions dono ko mila ke ek timeline banao, date descending.
    Har entry: {_id, type, date, data: {...}} — HealthInfo.jsx isi exact shape ko consume karta hai.
    """
    db = _get_db()

    vitals_cursor = db["health_vitals"].find({"user_id": user_id})
    prescriptions_cursor = db["health_prescriptions"].find({"user_id": user_id})

    timeline = []
    for doc in vitals_cursor:
        item = _serialize(doc)
        timeline.append({
            "_id": item.get("_id"),
            "type": "vital",
            "date": item.get("date"),
            "data": {
                "bp_systolic": item.get("bp_systolic"),
                "bp_diastolic": item.get("bp_diastolic"),
                "blood_sugar": item.get("blood_sugar"),
                "weight": item.get("weight"),
                "notes": item.get("notes"),
            },
        })
    for doc in prescriptions_cursor:
        item = _serialize(doc)
        medicines_list = item.get("medicines") or []
        summary = ", ".join(medicines_list) if medicines_list else item.get("symptoms", "")
        timeline.append({
            "_id": item.get("_id"),
            "type": "prescription",
            "date": item.get("date"),
            "data": {
                "summary": summary,
                "notes": item.get("doctor_notes", ""),
            },
        })

    timeline.sort(key=lambda x: x.get("date") or "", reverse=True)
    return timeline[:limit]


# ── Emergency profile ─────────────────────────────────────────────────────────

def save_emergency_profile(
    user_id: str,
    name: str,
    blood_group: str,
    allergies: str,
    critical_conditions: str,
    emergency_contact_name: str,
    emergency_contact_phone: str,
    medicines: str,
) -> None:
    """Emergency profile save/update karo (upsert)."""
    db = _get_db()
    collection = db["emergency_profiles"]

    doc = {
        "user_id": user_id,
        "name": name,
        "blood_group": blood_group,
        "allergies": allergies or "",
        "critical_conditions": critical_conditions or "",
        "emergency_contact_name": emergency_contact_name or "",
        "emergency_contact_phone": emergency_contact_phone or "",
        "medicines": medicines or "",
        "updated_at": datetime.utcnow().isoformat(),
    }

    collection.update_one(
        {"user_id": user_id},
        {"$set": doc, "$setOnInsert": {"created_at": datetime.utcnow().isoformat()}},
        upsert=True,
    )


def get_emergency_profile(user_id: str) -> dict:
    """
    Ek user ka emergency profile fetch karo (login required context mein).
    Saath mein existing QR token bhi merge karta hai.
    Returns: profile dict ya None.
    """
    db = _get_db()
    doc = db["emergency_profiles"].find_one({"user_id": user_id})
    profile = _serialize(doc)

    if profile:
        token_doc = db["emergency_qr_tokens"].find_one({"user_id": user_id})
        profile["qr_token"] = token_doc["token"] if token_doc else None

    return profile


def get_emergency_profile_public(token: str) -> dict:
    """QR token se emergency profile fetch karo — bina login ke (public access)."""
    db = _get_db()
    qr_collection = db["emergency_qr_tokens"]

    token_doc = qr_collection.find_one({"token": token})
    if not token_doc:
        return None

    profile_collection = db["emergency_profiles"]
    profile = profile_collection.find_one({"user_id": token_doc["user_id"]})
    return _serialize(profile)


def generate_qr_token(user_id: str) -> str:
    """Ek user ke liye naya QR token generate karo. Purana replace ho jayega."""
    db = _get_db()
    collection = db["emergency_qr_tokens"]

    token = secrets.token_urlsafe(16)

    collection.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "token": token,
            "created_at": datetime.utcnow().isoformat(),
        }},
        upsert=True,
    )
    return token