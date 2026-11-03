# P06 Dump: Phase 1 Close (Config Validation, Request-ID Context, Ownership 403 Coverage, Catalog Re-verification)

## 1. HEADER
- **Prompt ID:** PROMPT 06
- **Date & Time:** 2026-11-03 06:42:00 IST
- **Python Version:** Python 3.11.9 (`backend\venv\Scripts\python.exe`)
- **Git Commit:** `0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths`

---

## 2. PRE-FLIGHT

### Step 0a: Python Process Check
```powershell
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, CPU
```
Output:
```
(No active python processes found; clean state)
```

### Step 0b: PMBJP Catalog CSV Existence & SHA256 Check
```powershell
Test-Path backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv
Get-FileHash -Algorithm SHA256 backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv
```
Output:
```
True

Algorithm       Hash                                                                   Path                            
---------       ----                                                                   ----                            
SHA256          4AC1C0E8967E16DE86AAD74B0810FC06342D5F81BBE3E27BB7C6E5D46E02C4D3       C:\Users\gauta\OneDrive\Deskt...
```

---

## 3. BASELINE

### Step 1a: Baseline Pytest (Expect 88 passed)
```powershell
cd backend ; .\venv\Scripts\python.exe -m pytest -q > pytest_out.txt 2>&1 ; Get-Content pytest_out.txt -Tail 5
```
Output:
```
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
88 passed, 2 warnings in 60.91s (0:01:00)
```

### Step 1b: Route and OpenAPI Check (Canonical Baseline)
```powershell
@'
import json, hashlib, sys
sys.path.insert(0, 'src')
from agents.main import app
spec_obj = app.openapi()
spec = json.dumps(spec_obj, sort_keys=True, indent=2)
ops = sum(1 for p, ops in spec_obj['paths'].items() for m in ops if m in {'get', 'post', 'put', 'delete', 'patch'})
print('OPERATIONS:', ops)
print('OPENAPI_SHA256_INMEMORY_LF:', hashlib.sha256(spec.encode('utf-8')).hexdigest())
'@ | .\venv\Scripts\python.exe -
```
Output:
```
OPERATIONS: 43
OPENAPI_SHA256_INMEMORY_LF: 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1
```

### Step 1c: Baseline Git Status & Log
```powershell
git status --short ; git log -1 --oneline
```
Output:
```
 M backend/src/agents/Calling.py
 M backend/src/agents/Calling_Ai.py
 M backend/src/agents/buying_agent.py
 M backend/src/agents/db_connect.py
 M backend/src/agents/jwt_utils.py
 M backend/src/agents/main.py
?? backend/.env.example
?? backend/data/
?? backend/pytest_all.txt
?? backend/pytest_out.txt
?? backend/scripts/
?? backend/src/agents/catalog.py
?? backend/src/agents/errors.py
?? backend/src/agents/file_utils.py
?? backend/src/agents/hospital_parser.py
?? backend/src/agents/llm_output.py
?? backend/src/agents/rate_limit.py
?? backend/src/agents/routes/
?? backend/src/agents/schemas.py
?? backend/tests/test_catalog.py
?? backend/tests/test_phase0.py
?? backend/tests/test_routes_auth.py
?? local-changes.patch
0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths
```

---

## 4. ORDERING CHECK

### Step 5 Output (Verbatim)
```powershell
Select-String -Path src\agents\routes\*.py -Pattern "verify_owner\(" -Context 2,0
```
Output:
```
  src\agents\routes\consultation.py:18:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\consultation.py:19:):
> src\agents\routes\consultation.py:20:    verify_owner(current_user_id, user_id)
  src\agents\routes\consultation.py:72:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\consultation.py:73:):
> src\agents\routes\consultation.py:74:    verify_owner(current_user_id, user_id)
  src\agents\routes\consultation.py:126:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\consultation.py:127:):
> src\agents\routes\consultation.py:128:    verify_owner(current_user_id, user_id)
  src\agents\routes\doctor_qr.py:21:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\doctor_qr.py:22:):
> src\agents\routes\doctor_qr.py:23:    verify_owner(current_user_id, user_id)
  src\agents\routes\donor.py:20:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\donor.py:21:):
> src\agents\routes\donor.py:22:    verify_owner(current_user_id, request.user_id)
  src\agents\routes\donor.py:38:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\donor.py:39:):
> src\agents\routes\donor.py:40:    verify_owner(current_user_id, user_id)
  src\agents\routes\donor.py:52:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\donor.py:53:):
> src\agents\routes\donor.py:54:    verify_owner(current_user_id, user_id)
  src\agents\routes\donor.py:67:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\donor.py:68:):
> src\agents\routes\donor.py:69:    verify_owner(current_user_id, user_id)
  src\agents\routes\donor.py:81:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\donor.py:82:):
> src\agents\routes\donor.py:83:    verify_owner(current_user_id, request.requester_user_id)
  src\agents\routes\emergency.py:18:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\emergency.py:19:):
> src\agents\routes\emergency.py:20:    verify_owner(current_user_id, request.user_id)
  src\agents\routes\emergency.py:36:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\emergency.py:37:):
> src\agents\routes\emergency.py:38:    verify_owner(current_user_id, user_id)
  src\agents\routes\emergency.py:53:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\emergency.py:54:):
> src\agents\routes\emergency.py:55:    verify_owner(current_user_id, user_id)
  src\agents\routes\health_records.py:25:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\health_records.py:26:):
> src\agents\routes\health_records.py:27:    verify_owner(current_user_id, request.user_id)
  src\agents\routes\health_records.py:47:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\health_records.py:48:):
> src\agents\routes\health_records.py:49:    verify_owner(current_user_id, user_id)
  src\agents\routes\health_records.py:61:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\health_records.py:62:):
> src\agents\routes\health_records.py:63:    verify_owner(current_user_id, user_id)
  src\agents\routes\health_records.py:81:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\health_records.py:82:):
> src\agents\routes\health_records.py:83:    verify_owner(current_user_id, request.user_id)
  src\agents\routes\health_records.py:98:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\health_records.py:99:):
> src\agents\routes\health_records.py:100:    verify_owner(current_user_id, user_id)
  src\agents\routes\health_records.py:112:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\health_records.py:113:):
> src\agents\routes\health_records.py:114:    verify_owner(current_user_id, user_id)
  src\agents\routes\health_records.py:132:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\health_records.py:133:):
> src\agents\routes\health_records.py:134:    verify_owner(current_user_id, request.user_id)
  src\agents\routes\health_records.py:154:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\health_records.py:155:):
> src\agents\routes\health_records.py:156:    verify_owner(current_user_id, user_id)
  src\agents\routes\health_records.py:168:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\health_records.py:169:):
> src\agents\routes\health_records.py:170:    verify_owner(current_user_id, user_id)
  src\agents\routes\health_records.py:186:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\health_records.py:187:):
> src\agents\routes\health_records.py:188:    verify_owner(current_user_id, user_id)
  src\agents\routes\hospitals.py:15:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\hospitals.py:16:):
> src\agents\routes\hospitals.py:17:    verify_owner(current_user_id, location.user_id)
  src\agents\routes\lab.py:24:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\lab.py:25:):
> src\agents\routes\lab.py:26:    verify_owner(current_user_id, user_id)
  src\agents\routes\lab.py:64:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\lab.py:65:):
> src\agents\routes\lab.py:66:    verify_owner(current_user_id, request.user_id)
  src\agents\routes\lab.py:89:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\lab.py:90:):
> src\agents\routes\lab.py:91:    verify_owner(current_user_id, user_id)
  src\agents\routes\lab.py:103:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\lab.py:104:):
> src\agents\routes\lab.py:105:    verify_owner(current_user_id, user_id)
  src\agents\routes\lab.py:123:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\lab.py:124:):
> src\agents\routes\lab.py:125:    verify_owner(current_user_id, user_id)
  src\agents\routes\lab.py:136:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\lab.py:137:):
> src\agents\routes\lab.py:138:    verify_owner(current_user_id, user_id)
  src\agents\routes\medicine.py:16:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\medicine.py:17:):
> src\agents\routes\medicine.py:18:    verify_owner(current_user_id, request.user_id)
  src\agents\routes\medicine.py:42:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\medicine.py:43:):
> src\agents\routes\medicine.py:44:    verify_owner(current_user_id, request.user_id)
  src\agents\routes\triage.py:15:    current_user_id: str = Depends(get_current_user_id),
  src\agents\routes\triage.py:16:):
> src\agents\routes\triage.py:17:    verify_owner(current_user_id, request.user_id)
```

**Moves Made:** None. All 32 handlers calling `verify_owner` execute the call as the first statement after parameters, outside `try` blocks, and before any database or LLM call.

---

## 5. CATALOG RE-VERIFICATION

### Clean State Runs
- **Run 1 Output:**
```
Import completed successfully.
Total rows: 2445
Unique drug codes: 2445
Zero MRP rows: 345
No strength rows: 382
Slash strength rows: 41
Slash mismatch rows: 0
Pack count present rows: 1730
Non-medicine rows: 350
Output SHA256: e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c

Algorithm       Hash                                                                   Path                            
---------       ----                                                                   ----                            
SHA256          E5D0B82758B702959789F67691B03BAA438C9A2BA9713237B8CF6FF14BB68D7C       C:\Users\gauta\OneDrive\Deskt...
```

- **Run 2 Output:**
```
Import completed successfully.
Total rows: 2445
Unique drug codes: 2445
Zero MRP rows: 345
No strength rows: 382
Slash strength rows: 41
Slash mismatch rows: 0
Pack count present rows: 1730
Non-medicine rows: 350
Output SHA256: e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c

Algorithm       Hash                                                                   Path                            
---------       ----                                                                   ----                            
SHA256          E5D0B82758B702959789F67691B03BAA438C9A2BA9713237B8CF6FF14BB68D7C       C:\Users\gauta\OneDrive\Deskt...
```

Both hashes match the invariant `e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`.

### Verbatim `backend/data/catalog/import_report.json`
```json
{
  "input_sha256": "4ac1c0e8967e16de86aad74b0810fc06342d5f81bbe3e27bb7c6e5d46e02c4d3",
  "output_sha256": "e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c",
  "total_rows": 2445,
  "unique_drug_codes": 2445,
  "zero_mrp_rows": 345,
  "no_strength_rows": 382,
  "slash_strength_rows": 41,
  "slash_mismatch_rows": 0,
  "pack_count_present_rows": 1730,
  "non_medicine_rows": 350,
  "group_case_variants": [
    {
      "canonical": "Anti-Fungal",
      "variants": [
        "Anti-Fungal",
        "Anti-fungal"
      ]
    },
    {
      "canonical": "Anti-Retroviral",
      "variants": [
        "Anti-Retroviral",
        "Anti-retroviral"
      ]
    },
    {
      "canonical": "Anti-Viral",
      "variants": [
        "Anti-Viral",
        "Anti-viral"
      ]
    },
    {
      "canonical": "Hemorrhoids & Anal Fissures",
      "variants": [
        "Hemorrhoids & Anal Fissures",
        "Hemorrhoids & Anal fissures"
      ]
    },
    {
      "canonical": "Hepato-Protective",
      "variants": [
        "Hepato-Protective",
        "Hepato-protective"
      ]
    },
    {
      "canonical": "Stomatologicals",
      "variants": [
        "STOMATOLOGICALS",
        "Stomatologicals"
      ]
    }
  ],
  "duplicate_name_unit_pairs": [
    {
      "name_clean": "l-ornithine l-aspartate 150mg and pancreatin 100mg tablets",
      "unit_size_raw": "10's",
      "drug_codes": [
        "1738",
        "2040"
      ]
    }
  ]
}
```

---

## 6. CHANGED FILES

### `backend/src/agents/config.py`
```python
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
```

### `backend/src/agents/request_context.py`
```python
"""ASGI request ID middleware and request-scoped context tracking."""

import logging
import re
import uuid
from contextvars import ContextVar
from typing import Any, Callable, MutableMapping, Optional

REQUEST_ID_HEADER = b"x-request-id"
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9\-]{8,64}$")

_current_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def current_request_id() -> Optional[str]:
    """Return the current request ID from contextvar or None if not in request context."""
    return _current_request_id.get()


class RequestIdMiddleware:
    """Pure ASGI middleware to assign/propagate x-request-id."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(
        self,
        scope: MutableMapping[str, Any],
        receive: Callable[..., Any],
        send: Callable[..., Any],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming_rid: Optional[str] = None
        for key, value in scope.get("headers", []):
            if key.lower() == REQUEST_ID_HEADER:
                try:
                    incoming_rid = value.decode("latin-1")
                except Exception:
                    incoming_rid = None
                break

        if incoming_rid and _REQUEST_ID_RE.match(incoming_rid):
            rid = incoming_rid
        else:
            rid = uuid.uuid4().hex

        token = _current_request_id.set(rid)

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", rid.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            _current_request_id.reset(token)


_log_factory_installed = False


def install_log_record_factory() -> None:
    """Wrap logging.getLogRecordFactory() to inject request_id attribute. Idempotent."""
    global _log_factory_installed
    if _log_factory_installed:
        return
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        record.request_id = current_request_id() or "-"
        return record

    logging.setLogRecordFactory(record_factory)
    _log_factory_installed = True
```

### `backend/src/agents/main.py`
```python
#!/usr/bin/env python

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.config import allowed_origins, validate_startup
from agents.request_context import RequestIdMiddleware, install_log_record_factory
from agents.db_connect import ensure_indexes
from agents.errors import _server_error  # noqa: F401

from agents.routes import (
    system,
    auth,
    consultation,
    lab,
    medicine,
    triage,
    emergency,
    doctor_qr,
    calls,
    hospitals,
    donor,
    health_records,
)

install_log_record_factory()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """(D33) Ensures the doctor_qr_tokens TTL index exists. Idempotent."""
    validate_startup()
    try:
        await asyncio.to_thread(ensure_indexes)
    except Exception as e:
        logger.warning(f"Startup ensure_indexes skipped (DB unreachable): {e}")
    yield


app = FastAPI(title="Medical Agent API", version="1.0", lifespan=lifespan)

ALLOWED_ORIGINS = allowed_origins()

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(auth.router)
app.include_router(consultation.router)
app.include_router(lab.router)
app.include_router(medicine.router)
app.include_router(triage.router)
app.include_router(emergency.router)
app.include_router(doctor_qr.router)
app.include_router(calls.router)
app.include_router(hospitals.router)
app.include_router(donor.router)
app.include_router(health_records.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### `backend/src/agents/errors.py`
```python
import uuid
import logging
from fastapi import HTTPException

from agents.request_context import current_request_id

logger = logging.getLogger("agents.errors")


def _server_error(e: Exception) -> HTTPException:
    rid = current_request_id() or uuid.uuid4().hex
    logger.exception(f"Internal server error (ref: {rid}): {e}")
    return HTTPException(
        status_code=500,
        detail=f"Something went wrong. Please try again. (ref: {rid})"
    )
```

### `backend/src/agents/rate_limit.py`
```python
import time
import threading
from typing import Dict, Tuple

from agents.config import trust_proxy_headers


def get_client_ip(req) -> str:
    """
    Extracts the client IP from the request.
    If TRUST_PROXY_HEADERS is explicitly "true", reads X-Forwarded-For.
    The rightmost entry is used because it is appended by the nearest trusted
    reverse proxy; the leftmost entry can be spoofed by a client setting their own header.
    Otherwise falls back to req.client.host if available, else "unknown".
    """
    if trust_proxy_headers():
        headers = getattr(req, "headers", None)
        if headers is not None:
            # Handles starlette Headers or standard dict
            forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
            if forwarded:
                parts = [p.strip() for p in forwarded.split(",") if p.strip()]
                if parts:
                    return parts[-1]
    if hasattr(req, "client") and req.client and hasattr(req.client, "host") and req.client.host:
        return req.client.host
    return "unknown"


class RateLimiter:
    """
    In-memory fixed-window rate limiter guarded by a lock with periodic pruning.
    """

    def __init__(self, max_requests: int, window_seconds: int, prune_interval_seconds: int = None):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.prune_interval_seconds = (
            prune_interval_seconds if prune_interval_seconds is not None else window_seconds
        )
        self.lock = threading.RLock()
        self.last_prune = time.time()
        # key -> (window_start_timestamp, request_count)
        self.requests: Dict[str, Tuple[float, int]] = {}

    def prune_expired(self) -> int:
        """
        Removes keys whose (now - start_time) >= window_seconds.
        Returns the number of keys pruned.
        """
        with self.lock:
            now = time.time()
            expired = [
                k for k, (start, _) in self.requests.items()
                if (now - start) >= self.window_seconds
            ]
            for k in expired:
                del self.requests[k]
            return len(expired)

    def check(self, key: str) -> bool:
        """
        Checks whether a request with `key` is allowed under the rate limit.
        Returns True if allowed, False if the limit is exceeded.
        """
        now = time.time()
        with self.lock:
            if (now - self.last_prune) >= self.prune_interval_seconds:
                self.prune_expired()
                self.last_prune = now

            if key not in self.requests:
                self.requests[key] = (now, 1)
                return True

            start_time, count = self.requests[key]
            if now - start_time >= self.window_seconds:
                # Window expired, start a new window
                self.requests[key] = (now, 1)
                return True

            if count < self.max_requests:
                self.requests[key] = (start_time, count + 1)
                return True

            # Limit exceeded for this window
            return False

    def reset(self) -> None:
        """Clears all stored rate limit history. Used in test fixtures."""
        with self.lock:
            self.requests.clear()
            self.last_prune = time.time()


# Module-level limiters per requirement 2d:
LOGIN_LIMITER = RateLimiter(max_requests=10, window_seconds=60)
SIGNUP_LIMITER = RateLimiter(max_requests=10, window_seconds=60)
COMPARE_LIMITER = RateLimiter(max_requests=5, window_seconds=60)
```

### `backend/src/agents/routes/calls.py`
```python
import threading
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from agents.config import live_calls_enabled
from agents.jwt_utils import get_current_user_id
from agents.errors import _server_error
from agents.schemas import CallRequest
from agents.Calling import start_call, get_call_status

router = APIRouter()


@router.post("/call/schedule")
def schedule_call(
    request: CallRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
):
    """
    NEW (D34): requires a valid logged-in user (this triggers a real
    outbound AI phone call) — no user_id field on CallRequest to check
    ownership against, so this only enforces "someone is logged in."
    """
    if not live_calls_enabled():
        raise HTTPException(status_code=403, detail="Live calling is disabled in this environment.")

    if not request.number or not request.number.strip():
        raise HTTPException(status_code=400, detail="Phone number zaroori hai.")

    try:
        thread = threading.Thread(
            target=start_call,
            args=(
                request.number,
                request.disease,
                request.doctor_name,
                request.availability,
                request.patient_name,
                request.reason,
            ),
            daemon=True,
        )
        thread.start()
        return {
            "status": "initiated",
            "message": f"AI agent {request.number} pe call kar raha hai - yeh 30-60 seconds mein connect hoga.",
        }
    except Exception as e:
        raise _server_error(e)


@router.get("/call/status")
def call_status():
    # When live calls are enabled, the frontend phase must add auth here because transcript is patient conversation content.
    if not live_calls_enabled():
        return {
            "state": "disabled",
            "to_number": None,
            "summary": None,
            "transcript": [],
            "error": None,
        }
    try:
        return get_call_status()
    except Exception as e:
        raise _server_error(e)
```

### `backend/tests/test_config.py`
```python
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
```

### `backend/tests/test_request_context.py`
```python
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
```

### `backend/tests/test_ownership.py`
```python
"""Ownership 403 coverage test suite.

Ensures that any request attempting to access or modify data belonging to another
user is rejected with HTTP 403 before any database or LLM calls occur.
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from agents.main import app
from agents.jwt_utils import create_access_token, verify_owner

client = TestClient(app)

OWNER = "owner-user"
VICTIM = "victim-user"

# All 32 ownership-protected routes: 17 path-parameter, 11 JSON body, 4 multipart.
CASES = [
    # 17 Path-parameter routes
    ("GET", "/lab/analyses/{user_id}", f"/lab/analyses/{VICTIM}", {}),
    ("DELETE", "/lab/analyses/{user_id}/{analysis_id}", f"/lab/analyses/{VICTIM}/x", {}),
    ("GET", "/health/trends/{user_id}", f"/health/trends/{VICTIM}", {}),
    ("GET", "/health/trends-annotated/{user_id}", f"/health/trends-annotated/{VICTIM}", {}),
    ("GET", "/donor/{user_id}", f"/donor/{VICTIM}", {}),
    ("POST", "/donor/{user_id}/record-donation", f"/donor/{VICTIM}/record-donation", {}),
    ("POST", "/donor/{user_id}/availability", f"/donor/{VICTIM}/availability?available=true", {}),
    ("POST", "/health/doctor-qr/{user_id}", f"/health/doctor-qr/{VICTIM}", {}),
    ("POST", "/health/generate-qr/{user_id}", f"/health/generate-qr/{VICTIM}", {}),
    ("GET", "/health/emergency-profile/{user_id}", f"/health/emergency-profile/{VICTIM}", {}),
    ("GET", "/health/vitals/{user_id}", f"/health/vitals/{VICTIM}", {}),
    ("DELETE", "/health/vitals/{user_id}/{vital_id}", f"/health/vitals/{VICTIM}/x", {}),
    ("GET", "/health/prescriptions/{user_id}", f"/health/prescriptions/{VICTIM}", {}),
    ("DELETE", "/health/prescriptions/{user_id}/{prescription_id}", f"/health/prescriptions/{VICTIM}/x", {}),
    ("GET", "/health/prescription-analyses/{user_id}", f"/health/prescription-analyses/{VICTIM}", {}),
    ("GET", "/health/prescription-analysis/{user_id}/{analysis_id}", f"/health/prescription-analysis/{VICTIM}/x", {}),
    ("GET", "/health/timeline/{user_id}", f"/health/timeline/{VICTIM}", {}),

    # 11 JSON body routes
    ("POST", "/medicine/interactions", "/medicine/interactions", {"json": {"user_id": VICTIM, "medicines": ["a"]}}),
    ("POST", "/medicine/effectiveness", "/medicine/effectiveness", {"json": {"user_id": VICTIM, "medicine_name": "m", "test_name": "t", "start_date": "2026-01-01", "points": [{"date": "2026-01-01", "value": 1.0, "status": "Normal"}]}}),
    ("POST", "/triage/symptoms", "/triage/symptoms", {"json": {"user_id": VICTIM, "symptoms": "fever"}}),
    ("POST", "/lab/save", "/lab/save", {"json": {"user_id": VICTIM, "report_type": "r", "overall_summary": "s", "tests": [], "has_urgent_values": False, "next_steps": "n", "disclaimer": "d"}}),
    ("POST", "/health/vital", "/health/vital", {"json": {"user_id": VICTIM, "vital_type": "v", "value": 1.0, "unit": "u"}}),
    ("POST", "/health/prescription", "/health/prescription", {"json": {"user_id": VICTIM, "medicines": ["a"]}}),
    ("POST", "/health/prescription-analysis", "/health/prescription-analysis", {"json": {"user_id": VICTIM, "overall_summary": "s", "medicines": [], "has_allergy_conflict": False, "safety_note": "n"}}),
    ("POST", "/health/emergency-profile", "/health/emergency-profile", {"json": {"user_id": VICTIM, "name": "n", "blood_group": "O+"}}),
    ("POST", "/donor/register", "/donor/register", {"json": {"user_id": VICTIM, "name": "n", "blood_group": "O+", "city": "c", "state": "s", "phone": "1"}}),
    ("POST", "/donor/request/create", "/donor/request/create", {"json": {"requester_user_id": VICTIM, "blood_group": "O+", "city": "c", "state": "s"}}),
    ("POST", "/hospitals/nearby", "/hospitals/nearby", {"json": {"user_id": VICTIM}}),

    # 4 Multipart routes
    ("POST", "/consultation/speech", "/consultation/speech", {"data": {"user_id": VICTIM}, "files": {"audio_file": ("test.mp3", b"x", "audio/mpeg")}}),
    ("POST", "/consultation/document", "/consultation/document", {"data": {"user_id": VICTIM}, "files": {"file": ("test.txt", b"x", "text/plain")}}),
    ("POST", "/lab/analyse", "/lab/analyse", {"data": {"user_id": VICTIM}, "files": {"file": ("test.pdf", b"x", "application/pdf")}}),
    ("POST", "/general-query", "/general-query", {"data": {"user_id": VICTIM}, "files": {"audio_file": ("test.mp3", b"x", "audio/mpeg")}}),
]


def test_verify_owner_unit():
    """Unit test for verify_owner helper."""
    # verify_owner("a", "a") does not raise
    verify_owner("a", "a")

    # verify_owner("a", "b") raises HTTPException with status_code 403
    with pytest.raises(HTTPException) as exc_info:
        verify_owner("a", "b")
    assert exc_info.value.status_code == 403


@pytest.mark.parametrize("method,path_template,concrete_path,kwargs", CASES, ids=[f"{c[0]}_{c[1]}" for c in CASES])
def test_ownership_rejection_403(method, path_template, concrete_path, kwargs):
    """Assert all 32 ownership-protected routes return 403 when authenticated as OWNER but requesting VICTIM data."""
    token = create_access_token(OWNER)
    headers = {"Authorization": f"Bearer {token}"}
    merged_kwargs = dict(kwargs)
    merged_headers = dict(headers)
    if "headers" in merged_kwargs:
        merged_headers.update(merged_kwargs.pop("headers"))

    res = client.request(method, concrete_path, headers=merged_headers, **merged_kwargs)
    assert res.status_code == 403, f"{method} {concrete_path} returned {res.status_code} with body: {res.text}"


def test_ownership_coverage_against_openapi():
    """Assert all protected operations with {user_id} in path are included and all cases correspond to real routes."""
    spec = app.openapi()
    http_methods = {"get", "post", "put", "delete", "patch"}

    openapi_user_id_routes = set()
    all_openapi_routes = set()

    for path, ops in spec["paths"].items():
        for m in ops:
            if m in http_methods:
                all_openapi_routes.add((m.upper(), path))
                if "{user_id}" in path:
                    openapi_user_id_routes.add((m.upper(), path))

    case_path_templates = {(m, tmpl) for m, tmpl, _, _ in CASES}

    # Every protected operation whose path contains {user_id} must appear in the case list
    missing = openapi_user_id_routes - case_path_templates
    assert not missing, f"Protected routes with {{user_id}} in path missing from ownership cases: {missing}"

    # Every case in the list must be a real route in OpenAPI
    non_existent = case_path_templates - all_openapi_routes
    assert not non_existent, f"Ownership case list contains non-existent routes: {non_existent}"
```

---

### Appended to `Project-docs/decisions.md` (D45)
```markdown
---

## D45 — Phase 1 Close: Configuration Validation, Request ID Propagation, Ownership 403 Coverage, and Catalog Re-verification (3 Nov 2026)

**Status:** Built and verified (Prompt 06, 3 Nov 2026). All 136 automated tests passing (88 baseline + 48 new tests). Route count: 43. OpenAPI canonical in-memory LF SHA256 preserved (`37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`). Zero frontend modifications.

**Decisions:**
1. **Configuration Architecture & Read-at-Call-Time Rule (`agents.config`):**
   - Environment variables are read dynamically at call time rather than module import time via `env_bool`, `app_env`, `is_development`, `allowed_origins`, `live_calls_enabled`, and `trust_proxy_headers`.
   - This eliminates stale cached settings, supports runtime environment adjustments, and enables clean test isolation using pytest's `monkeypatch`.
   - Origin parsing rejects wildcard origins (`*`) by raising `ValueError`.
2. **Production Startup Validation (`validate_startup`):**
   - Applications enforce configuration sanity in `main.py`'s `lifespan` before database indexing.
   - `APP_ENV` must be strictly `development` or `production`.
   - In `production`, all `REQUIRED_PRODUCTION_SETTINGS` (`["MONGO_URI", "GROQ_API_KEY", "JWT_SECRET_KEY"]`) must be non-empty and non-whitespace.
   - On missing configuration, `RuntimeError` is raised with setting names only. Secret values are never printed, logged, or included in error messages.
   - In `development`, missing settings log warnings or use local fallbacks without crashing the app.
3. **ASGI Request ID Middleware & Log Record Factory (`agents.request_context`):**
   - Implemented pure ASGI `RequestIdMiddleware` attached as the inner layer before `CORSMiddleware` (ensuring CORS remains the outer boundary).
   - Validates incoming `x-request-id` headers against `^[A-Za-z0-9\-]{8,64}$`. Valid IDs are preserved and propagated; missing, invalid, or oversized IDs are replaced with a newly generated 32-character hexadecimal UUID (`uuid.uuid4().hex`).
   - The request ID is stored in a context variable (`_current_request_id`) and injected into response headers.
   - `install_log_record_factory()` hooks into standard Python `logging` to attach `record.request_id` (`"-"` outside requests).
   - `_server_error` in `agents.errors` utilizes `current_request_id() or uuid.uuid4().hex`, maintaining the exact client contract `Something went wrong. Please try again. (ref: <rid>)`.
4. **Deferred Error Response Contract:**
   - Standardizing error response bodies to RFC 7807 / FastAPI JSON contracts is explicitly deferred to Phase 2. The React frontend's `extractErrorMessage` relies on existing detail formats; changing them without simultaneous frontend updates would regress user-facing error reporting.
5. **Ownership Check Ordering Rule & Automated Coverage (`test_ownership.py`):**
   - Architectural rule: In any protected route handling user data, `verify_owner(current_user_id, target_user_id)` must be invoked as the first statement after parameters, outside any `try` block, and strictly prior to any database or LLM operation.
   - Verification across all route modules confirmed all 32 existing handlers are 100% compliant; zero line moves were necessary.
   - Created `tests/test_ownership.py` with 34 tests:
     - Unit test for `verify_owner`.
     - Parametrized tests covering all 32 ownership-protected routes (17 path-parameter routes, 11 JSON body routes, and 4 multipart routes), verifying each returns HTTP 403 Forbidden when an authenticated user attempts to access or mutate another user's data.
     - Automated coverage assertion against `app.openapi()` ensuring every protected operation with `{user_id}` in its path is included in the test suite and corresponds to a real route.
6. **P05b Deviation Record:**
   - In Prompt 05b, `load_catalog.cache_clear()` was added to `tests/test_catalog.py` to prevent stale memory caching across re-import tests. While behavior-neutral, this change was not explicitly recorded in P05b and is documented here for audit completeness.
7. **Catalog Re-verification from Clean State:**
   - Evaluated two consecutive clean-state runs of `scripts/import_janaushadhi.py` starting with all generated catalog files deleted.
   - Both runs produced identical output hashes: `e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`, verifying deterministic reproducible catalog normalization.
```

### Appended to `Project-docs/progress.md` (P06)
```markdown
---

## Prompt 06 — Phase 1 Close: Config Validation, Request-ID Context, Ownership 403 Coverage, and Catalog Re-verification (3 Nov 2026)

Phase 1 status: CLOSED, except the error contract (deferred to Phase 2).

### Completed Work
- [x] **Central Configuration Module (`agents.config`):**
  - Read-at-call-time functions: `env_bool`, `app_env`, `is_development`, `allowed_origins`, `live_calls_enabled`, and `trust_proxy_headers`.
  - Wildcard origins explicitly rejected with `ValueError`.
  - `validate_startup()` enforces valid `APP_ENV` and checks presence of `REQUIRED_PRODUCTION_SETTINGS` (`MONGO_URI`, `GROQ_API_KEY`, `JWT_SECRET_KEY`) in production mode, reporting variable names only (never secret values).
- [x] **Request ID Context & ASGI Middleware (`agents.request_context`):**
  - Pure ASGI `RequestIdMiddleware` assigns/propagates `x-request-id` headers (validating format `^[A-Za-z0-9\-]{8,64}$`, generating 32-hex UUID on missing/invalid).
  - Context variable `_current_request_id` tracks active ID across async request boundaries.
  - `install_log_record_factory()` attaches `request_id` (`"-"` outside requests) to all Python logging records.
  - `_server_error` in `agents.errors` uses `current_request_id()` to maintain correlation while preserving the client detail contract.
- [x] **Rate Limit & Calls Router Configuration Updates:**
  - `get_client_ip` in `rate_limit.py` uses `trust_proxy_headers()` from `agents.config`; unused `os` import removed.
  - `schedule_call` and `call_status` in `routes/calls.py` use `live_calls_enabled()` from `agents.config`; unused `os` import removed.
- [x] **Ownership Ordering Verification:**
  - Audited all 32 route handlers calling `verify_owner`. Confirmed 100% compliance: `verify_owner` is the first statement outside `try` blocks and precedes any database/LLM calls. Zero line moves needed.
- [x] **Ownership 403 Automated Coverage Suite (`tests/test_ownership.py`):**
  - Unit test for `verify_owner`.
  - 32 parameterized test cases covering 17 path-parameter routes, 11 JSON body routes, and 4 multipart routes, asserting HTTP 403 Forbidden when authenticated as `owner-user` requesting `victim-user` data.
  - Dynamic coverage test asserting every protected route with `{user_id}` in OpenAPI is covered and all test cases map to real routes.
- [x] **Clean-State Catalog Re-verification:**
  - Deleted generated catalog files and ran `scripts/import_janaushadhi.py` twice consecutively from scratch.
  - Both runs yielded identical output SHA256: `e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`.
- [x] **Test Suite & Invariants:**
  - Full test suite: **136 passed, 0 failed** (88 baseline + 48 new tests across `test_config.py`, `test_request_context.py`, and `test_ownership.py`).
  - Route count: 43 (0 new routes added).
  - OpenAPI canonical in-memory LF SHA256 preserved: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
  - Zero network library imports in `catalog.py`.
  - Live smoke test confirmed `/health` with `x-request-id` header (`89018dfd23ed438bbaf5d24385c9d453`) and `/ready` with status `ready`.

### Deviations
- P05b unrecorded deviation noted: `load_catalog.cache_clear()` was added to `tests/test_catalog.py` to prevent stale memory caching across re-import tests; documented in D45.

### Deferred Items (Phase 2 & Beyond)
- Error contract (Phase 2, coordinated with frontend `extractErrorMessage`).
- Concentration notation (`mg/5 ml`) and comma-splitting limitations in catalog parser.
- Brand MRP seed dataset and savings calculation (P07).
- `/catalog/search` HTTP route (P07).
- Removal of live scraping (`buying_agent.py`) and `browser_use` dependency (P07).
- Frontend Compare page adjustments to use static catalog.
- `is_medicine` non-medicine groups review (Gautam).
- H1 (`/call/status` public when calls are enabled).
- C2 (`browser_use` Windows `\tmp`).
- M5 (`Project-docs` not under version control).
- Decision on committing `backend/data/`.

### Constraints for P07
- Concentration rows (for example `"mg/5 ml"`) must not match a tablet strength.
- `dosage_form` is checked first in any brand mapping.
```

---

## 7. VERIFICATION (Step 9 Outputs, Verbatim)

### Step 9a: Full Test Suite
```powershell
.\venv\Scripts\python.exe -m pytest -q > pytest_all.txt 2>&1 ; Get-Content pytest_all.txt -Tail 5
```
Output:
```
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
136 passed, 2 warnings in 123.42s (0:02:03)
```

### Step 9b: Subprocess Import Check
```powershell
$env:APP_ENV="development"; .\venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); import agents.main; print('IMPORT_OK')"
```
Output:
```
IMPORT_OK
```

### Step 9c: Route Count and OpenAPI Check
```powershell
@'
import json, hashlib, sys
sys.path.insert(0, 'src')
from agents.main import app
spec_obj = app.openapi()
spec = json.dumps(spec_obj, sort_keys=True, indent=2)
ops = sum(1 for p, ops in spec_obj['paths'].items() for m in ops if m in {'get', 'post', 'put', 'delete', 'patch'})
print('OPERATIONS:', ops)
print('OPENAPI_SHA256_INMEMORY_LF:', hashlib.sha256(spec.encode('utf-8')).hexdigest())
'@ | .\venv\Scripts\python.exe -
```
Output:
```
OPERATIONS: 43
OPENAPI_SHA256_INMEMORY_LF: 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1
```

### Step 9d: Network Import Check in `catalog.py`
```powershell
Select-String -Path src\agents\catalog.py -Pattern "requests|urllib|httpx|socket"
```
Output:
```
(No matches found)
```

### Step 9e: `os.getenv` Check in `routes/calls.py`
```powershell
Select-String -Path src\agents\routes\calls.py -Pattern "os.getenv"
```
Output:
```
(No matches found)
```

### Step 9f: Live Smoke Test
```powershell
=== 1. Invoke-RestMethod /health ===
status : ok

=== 2. Invoke-WebRequest /health Headers ===
x-request-id: 89018dfd23ed438bbaf5d24385c9d453
Content-Length: 15
Content-Type: application/json
Date: Tue, 03 Nov 2026 01:10:57 GMT
Server: uvicorn

=== 3. Invoke-RestMethod /ready ===
status : ready
checks : @{mongo_uri=ok; groq_api_key=ok; jwt_secret_key=ok; mongodb=ok}
```
**Recorded `x-request-id` header:** `89018dfd23ed438bbaf5d24385c9d453`

### Step 9g: Git Status & Verification of Deletion
```powershell
git status --short
```
Output:
```
 M backend/src/agents/Calling.py
 M backend/src/agents/Calling_Ai.py
 M backend/src/agents/buying_agent.py
 M backend/src/agents/db_connect.py
 M backend/src/agents/jwt_utils.py
 M backend/src/agents/main.py
?? backend/.env.example
?? backend/data/
?? backend/pytest_out.txt
?? backend/scripts/
?? backend/src/agents/catalog.py
?? backend/src/agents/config.py
?? backend/src/agents/errors.py
?? backend/src/agents/file_utils.py
?? backend/src/agents/hospital_parser.py
?? backend/src/agents/llm_output.py
?? backend/src/agents/rate_limit.py
?? backend/src/agents/request_context.py
?? backend/src/agents/routes/
?? backend/src/agents/schemas.py
?? backend/tests/test_catalog.py
?? backend/tests/test_config.py
?? backend/tests/test_ownership.py
?? backend/tests/test_phase0.py
?? backend/tests/test_request_context.py
?? backend/tests/test_routes_auth.py
?? local-changes.patch
```
`backend\pytest_all.txt` confirmed absent.

---

## 8. DELETIONS

- **Step 7g:** `Remove-Item import_run1.txt, import_run2.txt` -> verified `Test-Path` returned `False` for both.
- **Step 10:** `Remove-Item pytest_all.txt` -> verified `Test-Path` returned `False`.

---

## 9. CHECKLIST

- [x] Step 0: Pre-flight verified 0 active python processes and PMBJP CSV SHA256 `4AC1C0E8967E16DE86AAD74B0810FC06342D5F81BBE3E27BB7C6E5D46E02C4D3`.
- [x] Step 1: Baseline verified 88 passing tests, 43 routes, and OpenAPI SHA256 `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
- [x] Step 2: Created `backend/src/agents/config.py` with call-time env helpers and safe production startup validation.
- [x] Step 3: Created `backend/src/agents/request_context.py` with ASGI `RequestIdMiddleware` and idempotent logging factory.
- [x] Step 4: Updated `errors.py`, `rate_limit.py`, and `routes/calls.py` to use `request_context` and `config`; removed unused `os` imports.
- [x] Step 5: Audited all 32 `verify_owner` handlers in routes; confirmed 100% compliance with zero moves needed.
- [x] Step 6: Updated `main.py` with `allowed_origins()`, `RequestIdMiddleware` before CORS, and `validate_startup()` in lifespan.
- [x] Step 7: Clean-state re-verification executed twice yielding identical hash `e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`; import run files deleted.
- [x] Step 8: Created test suites: `test_config.py` (7 tests), `test_request_context.py` (7 tests), `test_ownership.py` (34 tests including 32 ownership 403 cases).
- [x] Step 9: Final verification: 136 tests passed, `IMPORT_OK` in subprocess, 43 operations and OpenAPI invariant intact, zero network imports in `catalog.py`, zero `os.getenv` in `calls.py`, live smoke test verified `x-request-id: 89018dfd23ed438bbaf5d24385c9d453`.
- [x] Step 10: Deleted `backend\pytest_all.txt`.
- [x] Step 11: Appended decision D45 to `decisions.md` and P06 entry to `progress.md`.
- [x] Step 12: Generated comprehensive dump at `Project-docs/dumps/P06_dump.md`.

---

## 10. DEVIATIONS AND BLOCKERS

- **Blockers:** None.
- **Deviations:**
  - Step 5 required zero moves (all 32 handlers already strictly compliant).
  - P05b unrecorded deviation recorded in D45 and P06 entry: `load_catalog.cache_clear()` was added to `tests/test_catalog.py` to prevent stale memory caching across re-import tests; documented for full audit fidelity.

---

## 11. DEFERRED (Not Changed Here)

- Error response contract (RFC 7807 / standard JSON detail) — deferred to Phase 2 with frontend coordination (`extractErrorMessage`).
- Catalog parser concentration notation (`250 mg/5 ml` keeps `250.0 mg`) and comma-splitting limitations.
- Brand MRP seed dataset and savings calculation (P07).
- `/catalog/search` HTTP route (P07).
- Removal of live scraping (`buying_agent.py`) and `browser_use` dependency (P07).
- Frontend Compare page adjustments to use static catalog (frontend phase).
- `is_medicine` non-medicine groups review (Gautam).
- H1: `/call/status` public when calls are enabled.
- C2: `browser_use` Windows `\tmp` permission blocker.
- M5: `Project-docs` not under version control.
- Decision on committing `backend/data/` to git repository.

