"""
donor.py — Blood Donor System

Collections used (same medical_db on Atlas):
- donors: donor registration + badge tracking
- donation_requests: emergency blood requests

Badge thresholds:
- Bronze: 1+ donations
- Silver: 3+ donations
- Gold:  5+ donations
"""

from datetime import datetime
from agents.db_connect import get_database

DONORS_COLLECTION = "donors"
REQUESTS_COLLECTION = "donation_requests"

VALID_BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

BADGE_THRESHOLDS = {
    "Gold":   5,
    "Silver": 3,
    "Bronze": 1,
    "None":   0,
}


def _get_badge(donation_count: int) -> str:
    if donation_count >= 5:
        return "Gold"
    elif donation_count >= 3:
        return "Silver"
    elif donation_count >= 1:
        return "Bronze"
    return "None"


def _donors_col():
    return get_database()[DONORS_COLLECTION]


def _requests_col():
    return get_database()[REQUESTS_COLLECTION]


# ── Registration ──────────────────────────────────────────────────────────────

def register_donor(user_id: str, name: str, blood_group: str,
                   city: str, state: str, phone: str) -> dict:
    """
    Register a user as a blood donor.
    Raises ValueError if blood group is invalid or user already registered.
    """
    if blood_group not in VALID_BLOOD_GROUPS:
        raise ValueError(f"Invalid blood group '{blood_group}'. Must be one of {VALID_BLOOD_GROUPS}")

    col = _donors_col()
    if col.find_one({"user_id": user_id}):
        raise ValueError("You are already registered as a donor.")

    doc = {
        "user_id": user_id,
        "name": name,
        "blood_group": blood_group,
        "city": city,
        "state": state,
        "phone": phone,
        "donation_count": 0,
        "badge": "None",
        "available": True,
        "registered_at": datetime.utcnow(),
    }
    col.insert_one(doc)
    doc.pop("_id", None)
    return doc


def get_donor_by_user_id(user_id: str) -> dict:
    """Fetch donor profile by user_id. Raises ValueError if not found."""
    col = _donors_col()
    doc = col.find_one({"user_id": user_id})
    if not doc:
        raise ValueError("No donor profile found for this user.")
    doc.pop("_id", None)
    return doc


# ── Donation count + badge ────────────────────────────────────────────────────

def record_donation(user_id: str) -> dict:
    """
    Increment donation count and update badge.
    Call this after a donation is confirmed.
    """
    col = _donors_col()
    donor = col.find_one({"user_id": user_id})
    if not donor:
        raise ValueError("Donor not found.")

    new_count = donor["donation_count"] + 1
    new_badge = _get_badge(new_count)

    col.update_one(
        {"user_id": user_id},
        {"$set": {"donation_count": new_count, "badge": new_badge}}
    )

    donor["donation_count"] = new_count
    donor["badge"] = new_badge
    donor.pop("_id", None)
    return donor


def toggle_availability(user_id: str, available: bool) -> dict:
    """Mark donor as available or unavailable for donations."""
    col = _donors_col()
    col.update_one({"user_id": user_id}, {"$set": {"available": available}})
    return get_donor_by_user_id(user_id)


# ── Emergency requests ────────────────────────────────────────────────────────

def create_donation_request(requester_user_id: str, blood_group: str,
                             city: str, state: str, message: str = "") -> dict:
    """Create an emergency blood donation request."""
    if blood_group not in VALID_BLOOD_GROUPS:
        raise ValueError(f"Invalid blood group '{blood_group}'.")

    col = _requests_col()
    doc = {
        "requester_user_id": requester_user_id,
        "blood_group": blood_group,
        "city": city,
        "state": state,
        "message": message,
        "status": "open",
        "created_at": datetime.utcnow(),
    }
    result = col.insert_one(doc)
    doc["request_id"] = str(result.inserted_id)
    doc.pop("_id", None)
    return doc


def find_matching_donors(blood_group: str, city: str, state: str) -> list:
    """
    Find available donors matching the blood group in the same city/state.
    Returns list sorted by donation_count descending (most experienced first).
    """
    if blood_group not in VALID_BLOOD_GROUPS:
        raise ValueError(f"Invalid blood group '{blood_group}'.")

    col = _donors_col()
    results = col.find(
        {"blood_group": blood_group, "city": city, "available": True},
        {"_id": 0, "phone": 1, "name": 1, "badge": 1,
         "donation_count": 1, "city": 1, "state": 1}
    ).sort("donation_count", -1).limit(10)

    return list(results)