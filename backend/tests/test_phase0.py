import os
import sys
import subprocess
import pytest

# Ensure development environment at test module load
os.environ.setdefault("APP_ENV", "development")

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from fastapi.testclient import TestClient
from agents.jwt_utils import create_access_token


def test_import_hermetic(monkeypatch):
    """1. In-process hermetic import: load_dotenv is monkeypatched to no-op, APP_ENV=development, no credentials."""
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setenv("APP_ENV", "development")
    for mod in list(sys.modules.keys()):
        if mod.startswith("agents.") or mod == "agents":
            del sys.modules[mod]
    import agents.main
    assert agents.main.app is not None


def test_subprocess_import_minimal_env():
    """1b. Subprocess import with a minimal env (APP_ENV=development plus system paths only, cwd=backend, sys.path includes src) exits 0."""
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = {
        "APP_ENV": "development",
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"),
    }
    for var in ["USERPROFILE", "HOMEDRIVE", "HOMEPATH", "WINDIR", "TEMP", "TMP"]:
        if var in os.environ:
            env[var] = os.environ[var]

    proc = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, 'src'); import agents.main; print('IMPORT_OK')"],
        cwd=backend_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"Subprocess import failed with code {proc.returncode}. Stderr: {proc.stderr}"
    assert "IMPORT_OK" in proc.stdout


def test_subprocess_import_production_fails_without_jwt_secret():
    """2. Subprocess import with APP_ENV=production and no JWT_SECRET_KEY exits non-zero, and stderr contains 'JWT_SECRET_KEY'."""
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = {
        "APP_ENV": "production",
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"),
    }
    for var in ["WINDIR", "TEMP", "TMP"]:
        if var in os.environ:
            env[var] = os.environ[var]

    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import dotenv; dotenv.load_dotenv = lambda *a, **k: False; import sys; sys.path.insert(0, 'src'); import agents.jwt_utils",
        ],
        cwd=backend_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0, "Expected non-zero exit code in production without JWT_SECRET_KEY"
    assert "JWT_SECRET_KEY" in proc.stderr


def test_cors_no_wildcard():
    """3. The app's CORS middleware has no '*' in allow_origins."""
    from agents.main import app
    cors_found = False
    for middleware in app.user_middleware:
        if middleware.cls.__name__ == "CORSMiddleware":
            cors_found = True
            origins = middleware.kwargs.get("allow_origins", [])
            assert "*" not in origins
    assert cors_found, "CORSMiddleware not found in app.user_middleware"


def test_call_schedule_disabled_by_default(monkeypatch):
    """4. POST /call/schedule with a valid token returns 403 when ENABLE_LIVE_CALLS is unset."""
    monkeypatch.delenv("ENABLE_LIVE_CALLS", raising=False)
    from agents.main import app
    token = create_access_token("test-user-id")
    client = TestClient(app)
    res = client.post(
        "/call/schedule",
        json={"number": "+1234567890", "disease": "fever", "doctor_name": "Dr. Rao", "slot": "10am"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "Live calling is disabled in this environment."


@pytest.fixture
def reset_compare_limiter():
    from agents.rate_limit import COMPARE_LIMITER
    COMPARE_LIMITER.reset()
    yield
    COMPARE_LIMITER.reset()


def test_medicine_compare_rate_limit(monkeypatch, reset_compare_limiter):
    """5. POST /medicine/compare: 5 requests return non-429, and the 6th returns 429. Mock compare function."""
    from agents.main import app

    async def mock_run_comparison(medicines):
        return {"results": []}

    monkeypatch.setattr("agents.routes.medicine.run_comparison", mock_run_comparison)
    client = TestClient(app)
    for _ in range(5):
        res = client.post("/medicine/compare", json={"medicines": ["Paracetamol"]})
        assert res.status_code != 429
    res_6th = client.post("/medicine/compare", json={"medicines": ["Paracetamol"]})
    assert res_6th.status_code == 429
    assert res_6th.json()["detail"] == "Too many attempts. Try again in a minute."


@pytest.fixture
def reset_login_limiter():
    from agents.rate_limit import LOGIN_LIMITER
    LOGIN_LIMITER.reset()
    yield
    LOGIN_LIMITER.reset()


def test_auth_login_rate_limit(monkeypatch, reset_login_limiter):
    """6. POST /auth/login: patch agents.main.login_user to raise ValueError. 10 requests return non-429. The 11th returns 429."""
    from agents.main import app

    def mock_login(email, password):
        raise ValueError("Invalid credentials")

    monkeypatch.setattr("agents.routes.auth.login_user", mock_login)
    client = TestClient(app)
    for _ in range(10):
        res = client.post("/auth/login", json={"email": "test@example.com", "password": "pass"})
        assert res.status_code != 429
    res_11th = client.post("/auth/login", json={"email": "test@example.com", "password": "pass"})
    assert res_11th.status_code == 429
    assert res_11th.json()["detail"] == "Too many attempts. Try again in a minute."


def test_server_error_sanitizes_detail():
    """7. _server_error(ValueError('secret-internal-detail')) returns status 500, and detail does not contain 'secret-internal-detail'."""
    from agents.main import _server_error
    err = _server_error(ValueError("secret-internal-detail"))
    assert err.status_code == 500
    assert "secret-internal-detail" not in err.detail
    assert "(ref:" in err.detail


def test_health_endpoint(monkeypatch):
    """8. GET /health returns 200 with {'status': 'ok'} with no Mongo or Groq env vars set."""
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    from agents.main import app
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_ready_endpoint_fails_when_no_mongo_uri(monkeypatch):
    """9. GET /ready returns 503 when MONGO_URI is not set. Make no network call."""
    monkeypatch.delenv("MONGO_URI", raising=False)
    from agents.main import app
    client = TestClient(app)
    res = client.get("/ready")
    assert res.status_code == 503
    body = res.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["mongo_uri"] == "fail"


def test_ready_endpoint_success(monkeypatch):
    """8b. GET /ready returns 200 with checks.mongodb == 'ok' when db.command('ping') succeeds."""
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("GROQ_API_KEY", "gsk-mock")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-at-least-32-chars-long")
    from agents.main import app

    class FakeAdmin:
        def command(self, cmd):
            return {"ok": 1}

    class FakeClient:
        admin = FakeAdmin()

    class FakeDB:
        client = FakeClient()

    monkeypatch.setattr("agents.routes.system.get_database", lambda: FakeDB())
    client = TestClient(app)
    res = client.get("/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ready"
    assert body["checks"]["mongodb"] == "ok"


def test_ready_endpoint_mongodb_fail_no_leak(monkeypatch):
    """8c. GET /ready returns 503 with checks.mongodb == 'fail' when db.command('ping') raises, without leaking error."""
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("GROQ_API_KEY", "gsk-mock")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-at-least-32-chars-long")
    from agents.main import app

    class FailingAdmin:
        def command(self, cmd):
            raise Exception("internal secret details")

    class FailingClient:
        admin = FailingAdmin()

    class FailingDB:
        client = FailingClient()

    monkeypatch.setattr("agents.routes.system.get_database", lambda: FailingDB())
    client = TestClient(app)
    res = client.get("/ready")
    assert res.status_code == 503
    body = res.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["mongodb"] == "fail"
    assert "internal secret details" not in res.text


def test_call_status_disabled_by_default(monkeypatch):
    """8d. GET /call/status returns 200 with state == 'disabled' and transcript == [] without requiring auth header."""
    monkeypatch.delenv("ENABLE_LIVE_CALLS", raising=False)
    from agents.main import app
    client = TestClient(app)
    res = client.get("/call/status")
    assert res.status_code == 200
    body = res.json()
    assert body["state"] == "disabled"
    assert body["transcript"] == []
    assert body["to_number"] is None
    assert body["summary"] is None
    assert body["error"] is None


def test_get_client_ip(monkeypatch):
    """8e. Test get_client_ip proxy-aware parsing and fallbacks."""
    from agents.rate_limit import get_client_ip

    class DummyClient:
        host = "127.0.0.1"

    class DummyRequest:
        def __init__(self, headers=None, client=None):
            self.headers = headers or {}
            self.client = client

    # With TRUST_PROXY_HEADERS="true": parse rightmost IP from X-Forwarded-For
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")
    req_proxy = DummyRequest(headers={"x-forwarded-for": "1.1.1.1, 2.2.2.2"}, client=DummyClient())
    assert get_client_ip(req_proxy) == "2.2.2.2"

    # With TRUST_PROXY_HEADERS unset / false: fall back to client.host
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    assert get_client_ip(req_proxy) == "127.0.0.1"

    # Client None fallback to "unknown"
    req_none = DummyRequest(headers={}, client=None)
    assert get_client_ip(req_none) == "unknown"


def test_rate_limiter_prunes_expired(monkeypatch):
    """8f. Test RateLimiter prunes expired keys when window expires."""
    import time
    from agents.rate_limit import RateLimiter

    current_time = 1000.0

    def fake_time():
        return current_time

    monkeypatch.setattr(time, "time", fake_time)
    limiter = RateLimiter(max_requests=5, window_seconds=1, prune_interval_seconds=0)
    assert limiter.check("ip-1") is True
    assert limiter.check("ip-2") is True
    assert "ip-1" in limiter.requests
    assert "ip-2" in limiter.requests

    # Advance time by 2 seconds
    current_time += 2.0
    pruned = limiter.prune_expired()
    assert pruned == 2
    assert "ip-1" not in limiter.requests
    assert "ip-2" not in limiter.requests
