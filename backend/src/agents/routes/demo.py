"""
demo.py — Demo session endpoint.
"""

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from agents.config import demo_mode_enabled
from agents.db_connect import get_database
from agents.demo import DEMO_LIMITER, create_demo_session, purge_expired_demo_users
from agents.errors import _server_error
from agents.rate_limit import get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["Demo"])


class DemoSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    is_demo: bool = True
    expires_at: str


@router.post("/session", response_model=DemoSessionResponse)
def post_demo_session(request: Request):
    """Create a temporary demo session seeded with synthetic persona data."""
    if not demo_mode_enabled():
        raise HTTPException(status_code=403, detail="Demo mode is disabled.")

    client_ip = get_client_ip(request)
    if not DEMO_LIMITER.check(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many demo sessions created. Try again in a minute.",
        )

    db = get_database()
    try:
        purge_expired_demo_users(db)
    except Exception as e:
        logger.warning("Opportunistic demo purge failed: %s", e)

    try:
        session = create_demo_session(db)
        return {
            "access_token": session["access_token"],
            "token_type": "bearer",
            "user_id": session["user_id"],
            "name": session["name"],
            "is_demo": True,
            "expires_at": session["expires_at"],
        }
    except Exception as e:
        raise _server_error(e)

