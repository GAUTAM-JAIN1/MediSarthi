"""Tests for agents.config module."""

import pytest
from agents.config import (
    env_bool,
    allowed_origins,
    validate_startup,
    live_calls_enabled,
    is_development,
    app_env,
    trust_proxy_headers,
)


def test_env_bool(monkeypatch):
    monkeypatch.setenv("TEST_FLAG", "TRUE")
    assert env_bool("TEST_FLAG") is True

    monkeypatch.setenv("TEST_FLAG", "yes")
    assert env_bool("TEST_FLAG") is True

    monkeypatch.setenv("TEST_FLAG", "0")
    assert env_bool("TEST_FLAG") is False

    monkeypatch.delenv("TEST_FLAG", raising=False)
    assert env_bool("TEST_FLAG") is False
    assert env_bool("TEST_FLAG", default=True) is True


def test_allowed_origins(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", " http://a.com , ,http://b.com ")
    assert allowed_origins() == ["http://a.com", "http://b.com"]

    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    assert allowed_origins() == ["http://localhost:5173"]

    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:5173,*")
    with pytest.raises(ValueError, match="Wildcard origins are not allowed"):
        allowed_origins()


def test_validate_startup_production_missing_secrets(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:5173")
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        validate_startup()

    msg = str(exc_info.value)
    assert "Missing required settings" in msg
    assert "MONGO_URI" in msg
    assert "GROQ_API_KEY" in msg
    assert "JWT_SECRET_KEY" in msg

    # Set GROQ_API_KEY to a secret value, keep MONGO_URI unset:
    secret_val = "secret-groq-value-123"
    monkeypatch.setenv("GROQ_API_KEY", secret_val)
    with pytest.raises(RuntimeError) as exc_info2:
        validate_startup()

    msg2 = str(exc_info2.value)
    assert secret_val not in msg2
    assert "MONGO_URI" in msg2


def test_validate_startup_development(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:5173")
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    # Should not raise any exception in development mode
    validate_startup()
    assert is_development() is True
    assert app_env() == "development"


def test_validate_startup_invalid_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging")
    with pytest.raises(RuntimeError, match="APP_ENV must be development or production"):
        validate_startup()


def test_live_calls_enabled_call_time(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_CALLS", "true")
    assert live_calls_enabled() is True

    monkeypatch.delenv("ENABLE_LIVE_CALLS", raising=False)
    assert live_calls_enabled() is False


def test_trust_proxy_headers(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "1")
    assert trust_proxy_headers() is True

    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    assert trust_proxy_headers() is False

