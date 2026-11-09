"""
jwt_utils.py — JWT issuance and verification for MediSarthi.

FIX (D34 — auth/authorization hole): previously every endpoint trusted
whatever `user_id` a client sent (as a path param, form field, or body
field) with zero proof that the request was actually made by that user.
Anyone who learned/guessed another user's Mongo ObjectId could read or
delete their vitals, prescriptions, lab reports, etc. — there was
identification (a user_id string) but no authentication or authorization.

This module adds a signed JWT, issued at signup/login, that the frontend
must send back on every subsequent request as:
    Authorization: Bearer <token>

Deliberately NOT changing any existing endpoint's URL shape or body/form
field names (still `/health/vitals/{user_id}`, still `user_id` in request
bodies) — main.py instead adds a dependency that decodes the token and
CHECKS that the token's user matches the user_id being requested/acted on,
returning 401/403 otherwise. This keeps the diff mechanical and avoids a
simultaneous full rewrite of every frontend page's fetch calls; the token
is the new source of truth for "who is this," the existing user_id fields
become "who do you claim to be, and it must match."

Requires: pip install pyjwt
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
from datetime import datetime, timedelta

import jwt
from fastapi import Header, HTTPException

# In production this MUST come from an environment variable — never commit
# a real secret. Falls back to a fixed dev-only value so the app doesn't
# crash if JWT_SECRET_KEY isn't set locally, but logs a loud warning so this
# is never silently shipped as-is.
APP_ENV = os.getenv("APP_ENV", "production").lower()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    if APP_ENV == "development":
        SECRET_KEY = "dev-only-insecure-secret-change-me"
        print(
            "[jwt_utils] WARNING: JWT_SECRET_KEY not set in environment or shorter than 32 characters — using "
            "an insecure development default. Set JWT_SECRET_KEY before deploying "
            "anywhere real users will use this."
        )
    else:
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to at least 32 characters. For local development only, set APP_ENV=development."
        )

ALGORITHM = "HS256"
# 7 days by default — long enough that users aren't annoyingly logged out
# constantly on a personal-health app they might open once a week, short
# enough that a leaked token doesn't stay valid forever. Override via env.
TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "168"))


def create_access_token(user_id: str, expires_minutes: Optional[int] = None) -> str:
    """Issues a signed JWT for this user_id. Called right after signup/login succeeds."""
    if expires_minutes is not None:
        exp = datetime.utcnow() + timedelta(minutes=expires_minutes)
    else:
        exp = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": exp,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """
    Verifies a token's signature and expiry, returns the embedded user_id.
    Raises HTTPException(401) on any problem — expired, tampered, malformed.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expire ho gaya hai. Dobara login karo.")
    except (jwt.InvalidTokenError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid ya corrupted session token.")


def get_current_user_id(authorization: str = Header(None)) -> str:
    """
    FastAPI dependency — reads the `Authorization: Bearer <token>` header,
    verifies it, and returns the user_id it belongs to. Use as:
        current_user_id: str = Depends(get_current_user_id)
    on any endpoint that touches a specific user's data.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Login required — Authorization header missing ya galat format mein hai."
        )
    token = authorization.split(" ", 1)[1].strip()
    return decode_access_token(token)


def verify_owner(current_user_id: str, target_user_id: str) -> None:
    """
    Raises 403 if the logged-in user (from the token) doesn't match the
    user_id whose data is being requested/modified. Small shared helper so
    every endpoint doesn't repeat the same if-check with slightly different
    wording.
    """
    if current_user_id != target_user_id:
        raise HTTPException(
            status_code=403,
            detail="Ye data tumhara nahi hai — access denied."
        )
