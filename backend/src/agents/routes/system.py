import os
import logging
from fastapi import APIRouter, Response
from agents.db_connect import get_database

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def health_check():
    return {"status": "active", "message": "Medical Agent API is running"}


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready(response: Response):
    mongo_ok = bool(os.getenv("MONGO_URI"))
    groq_ok = bool(os.getenv("GROQ_API_KEY"))
    jwt_ok = bool(os.getenv("JWT_SECRET_KEY"))

    db_ok = False
    if mongo_ok:
        try:
            db = get_database()
            db.client.admin.command("ping")
            db_ok = True
        except Exception as e:
            logger.exception(f"Readiness check: MongoDB ping failed: {e}")
            db_ok = False

    all_ok = mongo_ok and groq_ok and jwt_ok and db_ok
    checks = {
        "mongo_uri": "ok" if mongo_ok else "fail",
        "groq_api_key": "ok" if groq_ok else "fail",
        "jwt_secret_key": "ok" if jwt_ok else "fail",
        "mongodb": "ok" if db_ok else "fail",
    }

    if all_ok:
        return {"status": "ready", "checks": checks}
    else:
        response.status_code = 503
        return {"status": "not_ready", "checks": checks}

