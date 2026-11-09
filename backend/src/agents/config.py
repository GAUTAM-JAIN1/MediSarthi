"""Configuration helper functions for MediSarthi agents.

Reads environment variables at call time to support runtime environment
changes and clean test monkeypatching.
"""

import os
from typing import List

_TRUE = {"1", "true", "yes", "on"}

DEFAULT_ORIGINS = "http://localhost:5173"

REQUIRED_PRODUCTION_SETTINGS: List[str] = ["MONGO_URI", "GROQ_API_KEY", "JWT_SECRET_KEY"]


def env_bool(name: str, default: bool = False) -> bool:
    """Return boolean evaluation of environment variable, or default if unset/empty."""
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return default
    return val.strip().lower() in _TRUE


def app_env() -> str:
    """Return current application environment (development or production)."""
    return os.getenv("APP_ENV", "production").strip().lower()


def is_development() -> bool:
    """Return True if APP_ENV is development."""
    return app_env() == "development"


def allowed_origins() -> List[str]:
    """Parse comma-separated ALLOWED_ORIGINS. Reject wildcard origins."""
    raw = os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS)
    origins = [part.strip() for part in raw.split(",") if part.strip()]
    if "*" in origins:
        raise ValueError("Wildcard origins are not allowed")
    return origins


def live_calls_enabled() -> bool:
    """Return True if live phone calls via Twilio/Vapi are enabled."""
    return env_bool("ENABLE_LIVE_CALLS", False)


def trust_proxy_headers() -> bool:
    """Return True if X-Forwarded-For should be trusted for client IP."""
    return env_bool("TRUST_PROXY_HEADERS", False)


def demo_mode_enabled() -> bool:
    """Return True if demo session creation is enabled."""
    return env_bool("DEMO_MODE_ENABLED", False)


def missing_production_settings() -> List[str]:
    """Return list of required production setting names that are unset or whitespace only."""
    missing: List[str] = []
    for name in REQUIRED_PRODUCTION_SETTINGS:
        val = os.getenv(name)
        if val is None or val.strip() == "":
            missing.append(name)
    return missing


def validate_startup() -> None:
    """Validate environment settings at application startup.

    - Validates allowed origins (rejecting wildcards).
    - Ensures APP_ENV is 'development' or 'production'.
    - In production, ensures all REQUIRED_PRODUCTION_SETTINGS are present.
      Error message contains variable names only, never values.
    """
    allowed_origins()
    env = app_env()
    if env not in {"development", "production"}:
        raise RuntimeError("APP_ENV must be development or production")

    if env == "production":
        missing = missing_production_settings()
        if missing:
            raise RuntimeError("Missing required settings: " + ", ".join(missing))
