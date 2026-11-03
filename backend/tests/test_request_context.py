"""Tests for agents.request_context and request ID propagation."""

import logging
import re
from fastapi.testclient import TestClient

from agents.main import app
from agents.request_context import (
    _current_request_id,
    install_log_record_factory,
)
from agents.errors import _server_error

client = TestClient(app)

_HEX_32_RE = re.compile(r"^[0-9a-f]{32}$")


def test_health_generates_request_id():
    resp = client.get("/health")
    assert resp.status_code == 200
    rid = resp.headers.get("x-request-id")
    assert rid is not None
    assert _HEX_32_RE.match(rid) is not None


def test_health_reuses_valid_custom_request_id():
    custom_id = "abcdef123456"
    resp = client.get("/health", headers={"X-Request-ID": custom_id})
    assert resp.status_code == 200
    assert resp.headers.get("x-request-id") == custom_id


def test_health_replaces_invalid_characters_request_id():
    bad_id = "bad id!"
    resp = client.get("/health", headers={"X-Request-ID": bad_id})
    assert resp.status_code == 200
    rid = resp.headers.get("x-request-id")
    assert rid != bad_id
    assert _HEX_32_RE.match(rid) is not None


def test_health_replaces_oversized_request_id():
    long_id = "a" * 70
    resp = client.get("/health", headers={"X-Request-ID": long_id})
    assert resp.status_code == 200
    rid = resp.headers.get("x-request-id")
    assert rid != long_id
    assert _HEX_32_RE.match(rid) is not None


def test_server_error_uses_current_request_id():
    token = _current_request_id.set("req-abc12345")
    try:
        err = _server_error(ValueError("x"))
        assert "req-abc12345" in err.detail
    finally:
        _current_request_id.reset(token)


def test_server_error_outside_request_generates_hex_ref():
    err = _server_error(ValueError("outside"))
    match = re.search(r"\(ref: ([0-9a-f]{32})\)", err.detail)
    assert match is not None


def test_install_log_record_factory_outside_request():
    install_log_record_factory()
    logger = logging.getLogger("t")
    record = logger.makeRecord("t", logging.INFO, "fn", 1, "msg", (), None)
    assert hasattr(record, "request_id")
    assert record.request_id == "-"

