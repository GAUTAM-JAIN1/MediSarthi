import os
import re
import sys

import pytest

os.environ.setdefault("APP_ENV", "development")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from fastapi.testclient import TestClient
from agents.main import app

HTTP_METHODS = {"get", "post", "put", "delete", "patch"}

# Routes that are public by decision. Every entry must reference its decision.
PUBLIC = {
    ("GET", "/"),                          # system (D40)
    ("GET", "/health"),                    # system (D40)
    ("GET", "/ready"),                     # system (D40)
    ("POST", "/auth/signup"),              # auth (D37)
    ("POST", "/auth/login"),               # auth (D37)
    ("POST", "/medicine/compare"),         # public, rate-limited (D40, frontend phase adds auth)
    ("GET", "/call/status"),               # public while H1 is open (D40)
    ("GET", "/health/qr/{token}"),         # emergency QR, token-based (D12, D13)
    ("GET", "/health/doctor-qr/{token}"),  # doctor visit QR, token-based (D32)
    ("POST", "/demo/session"),             # demo session backend, unauthenticated (D54)
}


def _operations():
    spec = app.openapi()
    found = set()
    for path, ops in spec["paths"].items():
        for method in ops:
            if method in HTTP_METHODS:
                found.add((method.upper(), path))
    return found


ALL_OPS = _operations()
PROTECTED = sorted(ALL_OPS - PUBLIC)


def test_public_allowlist_matches_real_routes():
    missing = PUBLIC - ALL_OPS
    assert not missing, f"PUBLIC lists routes that do not exist: {missing}"


def test_protected_route_count_is_sane():
    assert len(PROTECTED) >= 30, f"Only {len(PROTECTED)} protected routes found; route extraction likely broke."


@pytest.mark.parametrize("method,path", PROTECTED)
def test_protected_route_rejects_missing_token(method, path):
    client = TestClient(app)
    concrete = re.sub(r"\{[^}]+\}", "dummy", path)
    res = client.request(method, concrete)
    assert res.status_code == 401, f"{method} {path} returned {res.status_code} without a token"
