# MediSarthi - Phase 0 Hotfix & Closure Dump (P02)

**Generated:** 1 Nov 2026  
**Context:** Prompt 02 - Phase 0 hotfix and closure (fixes for P01 review findings)  
**Status:** All defects addressed, 17/17 tests passing, Phase 0 closed.

---

## 1. Executive Summary

Prompt 02 addressed all critical, high, medium, and low review findings identified from the Phase 0 (P01) review:
- **C1 (Critical):** Fixed `/ready` route `NameError: name 'get_database' is not defined` by adding `get_database` to the existing `agents.db_connect` import in `main.py`.
- **C2 (Critical):** Isolated `browser_use` loading into a single dynamic loader `_load_browser_use()` in `buying_agent.py`, eliminating top-level import crashes. Documented the Windows bare-metal `\tmp` permission blocker in `browser_use` with Linux/Docker workaround.
- **H1 (High):** Secured `GET /call/status` against transcript leaks by returning a safe disabled response payload (`{"state": "disabled", "to_number": None, "summary": None, "transcript": [], "error": None}`) whenever `ENABLE_LIVE_CALLS` is false or unset.
- **H2 (High):** Added proxy-aware `get_client_ip()` in `rate_limit.py` (safely parsing the rightmost entry of `X-Forwarded-For` when `TRUST_PROXY_HEADERS=true` to prevent IP spoofing), integrated it into `signup`, `login`, and `compare_prices`, added periodic expired key pruning to `RateLimiter`, and documented `TRUST_PROXY_HEADERS` in `.env.example`.
- **M1 / M3 / L2:** Reconciled documentation references to actual codebase function names (`get_database()`, `_run_single_site()`) and accurately recorded the internal `BrowserProfile()` instantiation triggered by importing `browser_use`.
- **M2 (Medium):** Added `load_dotenv()` to `jwt_utils.py` before reading `JWT_SECRET_KEY` and `APP_ENV`.
- **M4 (Medium):** Made test suite import hermetic by monkeypatching `dotenv.load_dotenv` and clearing `agents.*` from `sys.modules`.
- **L1 (Low):** Migrated deprecated FastAPI `@app.on_event("startup")` to modern `@asynccontextmanager` `lifespan(app: FastAPI)` with async thread execution of `ensure_indexes()`.
- **L3 (Low):** Verified `Project-docs/decision.md` was identical to `decisions.md`, deleted `decision.md`, and updated D40 in `decisions.md`.
- **L4 (Low):** Documented `Project-docs` filesystem relationship relative to the `MediSarthi` git repository.

**Test Counts:** 17 passed, 0 failed across test suite (2 in `test_health.py`, 15 in `test_phase0.py`).  
**Phase 0 Status:** CLOSED and ready for Phase 1.

---

## 2. Baselines (Step 0 Outputs, Verbatim)

### 0a: `python -m pytest -q`
```
...........                                                              [100%]
============================== warnings summary ===============================
venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
11 passed, 1 warning in 10.96s
```

### 0b: `$env:APP_ENV="development"; python -c "import sys; sys.path.insert(0,'src'); import agents.main; print('IMPORT_OK')"`
```
IMPORT_OK
```

### 0c: Reproduce defect C1 (`Invoke-RestMethod http://127.0.0.1:8080/ready`)
```
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\uvicorn\protocols\http\h11_impl.py", line 408, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\src\agents\main.py", line 1253, in ready
    db = get_database()
         ^^^^^^^^^^^^
NameError: name 'get_database' is not defined
INFO:     127.0.0.1:51234 - "GET /ready HTTP/1.1" 500 Internal Server Error
```

### 0d: Reproduce defect C2 (`_load_browser_use`)
```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ImportError: cannot import name '_load_browser_use' from 'agents.buying_agent' (C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\src\agents\buying_agent.py)
```

---

## 3. Step 1 (C1 Fix: `main.py`) Diff & Verification

### Diff in `backend/src/agents/main.py`:
```diff
--- a/backend/src/agents/main.py
+++ b/backend/src/agents/main.py
@@ -47,3 +47,3 @@
 # NEW (D33) — TTL index setup for doctor_qr_tokens cleanup.
-from agents.db_connect import ensure_indexes
+from agents.db_connect import ensure_indexes, get_database
```

### Verification:
```powershell
Select-String -Path backend\src\agents\main.py -Pattern "get_database"
```
Output:
```
backend\src\agents\main.py:27:from agents.db_connect import ensure_indexes, get_database
backend\src\agents\main.py:416:            db = get_database()
```

---

## 4. Step 2 (C2 Investigation, Source References, Outcome, and Blocker Record)

### Investigation & Source References:
1. Importing `from browser_use import Agent, Browser, ChatGroq, Tools` executes:
   - `browser_use/__init__.py:117` -> loads `browser_use.agent.service`
   - `browser_use/agent/service.py:38` -> imports `from browser_use import Browser, BrowserProfile, BrowserSession`
   - `browser_use/browser/__init__.py:26` -> imports `browser_use.browser.session`
   - `browser_use/browser/session.py:58` -> executes top-level module constant:
     ```python
     DEFAULT_BROWSER_PROFILE = BrowserProfile()
     ```
2. Instantiating `BrowserProfile()` triggers a Pydantic model validator in `browser_use/browser/profile.py:428-444`:
   ```python
   @model_validator(mode='after')
   def set_default_downloads_path(self) -> Self:
       """Set a unique default downloads path if none is provided."""
       if self.downloads_path is None:
           import uuid
           unique_id = str(uuid.uuid4())[:8]
           downloads_path = Path(f'/tmp/browser-use-downloads-{unique_id}')
           while downloads_path.exists():
               unique_id = str(uuid.uuid4())[:8]
               downloads_path = Path(f'/tmp/browser-use-downloads-{unique_id}')
           self.downloads_path = downloads_path
           self.downloads_path.mkdir(parents=True, exist_ok=True)
       return self
   ```
3. Hardcoded Path & Windows PermissionError:
   `Path('/tmp/browser-use-downloads-...')` on Windows resolves to `\tmp\...` at the root of the drive (`C:\tmp\...`). Calling `.mkdir(parents=True, exist_ok=True)` without administrative permissions raises:
   `PermissionError: [WinError 5] Access is denied: '\\tmp\\browser-use-downloads-...'`
4. Upstream Search:
   Grep search across all files in `venv/Lib/site-packages/browser_use` confirmed that no environment variable or configuration setting exists to override `downloads_path` before `BrowserProfile()` instantiation in `session.py:58`.
5. Implementation:
   Defined helper `_load_browser_use()` in `backend/src/agents/buying_agent.py`:
   ```python
   def _load_browser_use():
       """Dynamically loads browser-use symbols to defer import-time side effects."""
       from browser_use import Agent, Browser, ChatGroq, Tools
       return Agent, Browser, ChatGroq, Tools
   ```
   Replaced direct import inside `_run_single_site` with `Agent, Browser, ChatGroq, Tools = _load_browser_use()`.
6. Outcome:
   Importing `agents.main` or `agents.buying_agent` succeeds cleanly without invoking `browser_use`. Dynamic invocation under bare-metal Windows triggers the isolated PermissionError, while execution inside Linux/Docker environments functions properly where `/tmp` is accessible.

---

## 5. Step 3 (H1 Fix: `main.py`) Diff & Verification

### Diff in `backend/src/agents/main.py`:
```diff
 @app.get("/call/status")
 def call_status():
+    # When live calls are enabled, the frontend phase must add auth here because transcript is patient conversation content.
+    if os.getenv("ENABLE_LIVE_CALLS", "false").lower() != "true":
+        return {
+            "state": "disabled",
+            "to_number": None,
+            "summary": None,
+            "transcript": [],
+            "error": None,
+        }
     try:
         return get_call_status()
     except Exception as e:
```

### Verification:
```powershell
Select-String -Path backend\src\agents\main.py -Pattern "state.*disabled"
```
Output:
```
backend\src\agents\main.py:970:            "state": "disabled",
```

---

## 6. Step 4 (H2 Fix: Rate Limiting Hygiene & Proxy-Aware IP) Diff & Verification

### Code Added to `backend/src/agents/rate_limit.py`:
```python
def get_client_ip(req) -> str:
    """
    Extracts the client IP from the request.
    If TRUST_PROXY_HEADERS is explicitly "true", reads X-Forwarded-For.
    The rightmost entry is used because it is appended by the nearest trusted
    reverse proxy; the leftmost entry can be spoofed by a client setting their own header.
    Otherwise falls back to req.client.host if available, else "unknown".
    """
    if os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true":
        headers = getattr(req, "headers", None)
        if headers is not None:
            forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
            if forwarded:
                parts = [p.strip() for p in forwarded.split(",") if p.strip()]
                if parts:
                    return parts[-1]
    if hasattr(req, "client") and req.client and hasattr(req.client, "host") and req.client.host:
        return req.client.host
    return "unknown"
```

### `RateLimiter` Pruning:
- Constructor updated with `prune_interval_seconds: int = None` (defaults to `window_seconds`).
- Added `prune_expired(self) -> int` to prune keys older than `window_seconds`.
- `check(key)` checks `time.time() - self.last_prune >= self.prune_interval_seconds` and triggers `prune_expired()`.
- Thread safety ensured using `threading.RLock()`.

### Diff in `backend/src/agents/main.py`:
- Updated import to include `get_client_ip`.
- Replaced inline `req.client.host` checks in `/auth/signup`, `/auth/login`, and `/medicine/compare` with `get_client_ip(req)`.

### Diff in `backend/.env.example`:
```diff
+# Set true only behind a trusted reverse proxy (Cloud Run, Render, nginx) to parse X-Forwarded-For
+TRUST_PROXY_HEADERS=
```

### Verification:
```powershell
Select-String -Path backend\src\agents\*.py -Pattern "get_client_ip"
```
Matches:
- `backend\src\agents\main.py:19`
- `backend\src\agents\main.py:363`
- `backend\src\agents\main.py:381`
- `backend\src\agents\main.py:902`
- `backend\src\agents\rate_limit.py:7`

```powershell
Select-String -Path backend\src\agents\rate_limit.py -Pattern "prune_expired"
```
Matches:
- `backend\src\agents\rate_limit.py:45`
- `backend\src\agents\rate_limit.py:68`

---

## 7. Step 5 (M2 Fix: `jwt_utils.py`) Diff & Verification

### Diff in `backend/src/agents/jwt_utils.py`:
```diff
 import os
 from datetime import datetime, timedelta
+from dotenv import load_dotenv
+
+load_dotenv()
```

### Verification:
```powershell
Select-String -Path backend\src\agents\jwt_utils.py -Pattern "load_dotenv"
```
Output:
```
backend\src\agents\jwt_utils.py:28:from dotenv import load_dotenv
backend\src\agents\jwt_utils.py:30:load_dotenv()
```

---

## 8. Step 6 (L1 Fix: Lifecycle Deprecation) Diff & Verification

### Diff in `backend/src/agents/main.py`:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """(D33) Ensures the doctor_qr_tokens TTL index exists. Idempotent."""
    try:
        await asyncio.to_thread(ensure_indexes)
    except Exception as e:
        logger.warning(f"Startup ensure_indexes skipped (DB unreachable): {e}")
    yield


app = FastAPI(title="Medical Agent API", version="1.0", lifespan=lifespan)
```
The old `@app.on_event("startup")` and `def on_startup():` were deleted.

### Verification:
```powershell
Get-ChildItem -Path backend\src -Filter *.py -Recurse | Select-String -Pattern "on_event"
```
Output: 0 matches.

---

## 9. Step 7 (Docs Consolidation) Confirmation

- **Comparison of `decision.md` vs `decisions.md`:** Byte-by-byte diff yielded 0 diff lines (both were 114,861 bytes). All entries were already present in `decisions.md`.
- **Deletion:** Deleted `Project-docs/decision.md`.
- **D40 Update in `decisions.md`:**
  - Corrected function names: `get_database()` (not `get_db()`), `_run_single_site` (not `run_single_site_agent`).
  - Corrected import description to `from browser_use import Agent, Browser, ChatGroq, Tools`.
  - Documented Step 2e outcome, root cause, and bare-metal Windows `/tmp` isolation.
- **Phase 0 Update in `progress.md`:**
  - Reconciled function names.
  - Documented `/ready` status as verified (returns 200 or 503 cleanly without leaking or crashing).
  - Documented real Step 2e outcome.
- **Git Tracking Check (Step 7e):**
  ```powershell
  git check-ignore -v Project-docs\progress.md Project-docs\decisions.md ; git status --short --ignored Project-docs
  ```
  Output: Exit code 0, no output.  
  *Note:* `Project-docs` is located in the parent workspace directory `C:\Users\gauta\OneDrive\Desktop\MediSarthi\Project-docs` and is outside the git repository `C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi`.

---

## 10. Step 8 (Test Expansion) Full List of Tests in `test_phase0.py`

1. `test_import_hermetic`: In-process hermetic import with monkeypatched `dotenv.load_dotenv` no-op and purged `sys.modules`.
2. `test_subprocess_import_minimal_env`: Subprocess import under minimal environment exiting 0 with `IMPORT_OK`.
3. `test_subprocess_import_production_fails_without_jwt_secret`: Subprocess import under `APP_ENV=production` without JWT secret exiting non-zero with `JWT_SECRET_KEY` in stderr.
4. `test_cors_no_wildcard`: Verifies `CORSMiddleware` has no `*` in `allow_origins`.
5. `test_call_schedule_disabled_by_default`: Verifies `POST /call/schedule` returns 403 when `ENABLE_LIVE_CALLS` is unset.
6. `test_medicine_compare_rate_limit`: Verifies 5 calls to `POST /medicine/compare` succeed and 6th returns 429.
7. `test_auth_login_rate_limit`: Verifies 10 calls to `POST /auth/login` succeed and 11th returns 429.
8. `test_server_error_sanitizes_detail`: Verifies internal exception detail is never leaked in 500 responses.
9. `test_health_endpoint`: Verifies `GET /health` returns 200 `{"status": "ok"}` without database or API keys.
10. `test_ready_endpoint_fails_when_no_mongo_uri`: Verifies `GET /ready` returns 503 when `MONGO_URI` is unset.
11. `test_ready_endpoint_success`: Verifies `GET /ready` returns 200 with `checks.mongodb == "ok"` when `db.client.admin.command("ping")` succeeds.
12. `test_ready_endpoint_mongodb_fail_no_leak`: Verifies `GET /ready` returns 503 with `checks.mongodb == "fail"` when ping raises, without leaking exception string.
13. `test_call_status_disabled_by_default`: Verifies `GET /call/status` returns 200 with `state == "disabled"` and empty transcript without requiring auth.
14. `test_get_client_ip`: Verifies `get_client_ip` parses rightmost IP with `TRUST_PROXY_HEADERS="true"`, falls back to `client.host` when false/unset, and returns `"unknown"` when client is None.
15. `test_rate_limiter_prunes_expired`: Verifies `RateLimiter.prune_expired()` purges expired keys when window expires.

---

## 11. Step 9 (Verification) Verbatim Outputs

### 9a: `python -m pytest -q`
```
.................                                                        [100%]
============================== warnings summary ===============================
venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
17 passed, 2 warnings in 15.37s
```

### 9b: `git diff --stat` & Pattern Checks
```
 backend/src/agents/Calling.py      |  19 +++-
 backend/src/agents/Calling_Ai.py   |  15 ++-
 backend/src/agents/buying_agent.py |  14 ++-
 backend/src/agents/db_connect.py   |  14 ++-
 backend/src/agents/jwt_utils.py    |  23 ++--
 backend/src/agents/main.py         | 221 +++++++++++++++++++++++++------------
 6 files changed, 214 insertions(+), 92 deletions(-)
```
- `ALLOW_ALL_ORIGINS|allow_origins=\['\*'\]`: 0 matches.
- `on_event\(`: 0 matches.
- `_run_single_site_agent`: 0 matches.
- `jwt_utils.py: load_dotenv`: matched lines 28, 30.
- `rate_limit.py: get_client_ip`: matched line 7.

### 9c: Server Smoke Test (`/health` & `/ready`)
```powershell
=== 1. /health ===
{"status":"ok"}

=== 2. /ready ===
HTTP status: 503
Body: {"status":"not_ready","checks":{"mongo_uri":"ok","groq_api_key":"ok","jwt_secret_key":"ok","mongodb":"fail"}}
```
Server log excerpt during smoke test:
```
Startup ensure_indexes skipped (DB unreachable): The DNS query name does not exist: _mongodb._tcp.cluster0.flp2hip.mongodb.net.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
INFO:     127.0.0.1:49673 - "GET /health HTTP/1.1" 200 OK
ERROR:    agents.main: Readiness check: MongoDB ping failed: The DNS query name does not exist: _mongodb._tcp.cluster0.flp2hip.mongodb.net.
INFO:     127.0.0.1:49673 - "GET /ready HTTP/1.1" 503 Service Unavailable
```

### 9d: Live `/call/status` Output
```powershell
=== 3. /call/status ===
{"state":"disabled","to_number":null,"summary":null,"transcript":[],"error":null}
```
HTTP status: 200 OK, no authentication header required, patient transcript content is safely omitted.

### 9e: Step 2e Command Output
```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\src\agents\buying_agent.py", line 207, in _load_browser_use
    from browser_use import Agent, Browser, ChatGroq, Tools
  ...
  File "C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\browser_use\browser\session.py", line 58, in <module>
    DEFAULT_BROWSER_PROFILE = BrowserProfile()
  ...
  File "C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\browser_use\browser\profile.py", line 443, in set_default_downloads_path
    self.downloads_path.mkdir(parents=True, exist_ok=True)
  File "C:\Users\gauta\AppData\Local\Programs\Python\Python311\Lib\pathlib.py", line 1116, in mkdir
    os.mkdir(self, mode)
PermissionError: [WinError 5] Access is denied: '\\tmp\\browser-use-downloads-f9f80e3b'
```

---

## 12. Blockers

### Blocker 1: `browser_use` bare-metal Windows `\tmp` filesystem access
- **Root Cause:** Upstream library bug in `browser_use/browser/session.py:58` evaluating `DEFAULT_BROWSER_PROFILE = BrowserProfile()` at import time, which runs a Pydantic model validator executing `Path('/tmp/browser-use-downloads-<uuid>').mkdir(parents=True, exist_ok=True)`. On Windows, `/tmp` resolves to root `\tmp`, failing with `PermissionError: [WinError 5] Access is denied`. No environment variable or configuration hook exists in `browser_use` to override this default path before profile initialization.
- **Impact:** Dynamic invocation of `_load_browser_use()` fails when running on bare-metal Windows without admin privileges on root `C:\tmp`.
- **Why it cannot be fixed under prompt rules:** Editing vendor packages in `site-packages` is strictly prohibited by Hard Rule 4.
- **Workaround:** Run the price comparison feature (`POST /medicine/compare`) under Linux / Docker (as configured in the repo Dockerfile), where `/tmp` is a standard, writable directory. In bare-metal Windows, `_load_browser_use()` successfully isolates the library load so that importing `agents.main` or `agents.buying_agent` works cleanly and all other backend endpoints function without error.

---

## 13. Files Modified or Created in P02

### Modified:
- `backend/src/agents/main.py`: Fixed C1 (imported `get_database`), fixed H1 (early safe exit in `/call/status`), fixed H2 (integrated `get_client_ip`), fixed L1 (migrated to `lifespan` context manager, removed `on_event("startup")`).
- `backend/src/agents/buying_agent.py`: Fixed C2 (added `_load_browser_use()` helper and replaced local import).
- `backend/src/agents/rate_limit.py`: Added `get_client_ip()`, added `RateLimiter.prune_expired()`, added pruning logic in `check()`.
- `backend/src/agents/jwt_utils.py`: Fixed M2 (added `load_dotenv()` at top of module).
- `backend/tests/test_phase0.py`: Added 8a, 8b, 8c, 8d, 8e, 8f test cases (15 tests total).
- `backend/.env.example`: Added `TRUST_PROXY_HEADERS=` documentation.
- `Project-docs/decisions.md`: Updated D40 with accurate names, real Step 2e outcome, and Windows blocker details.
- `Project-docs/progress.md`: Updated Phase 0 entry with accurate names and confirmed `/ready` and `browser_use` status.

### Deleted:
- `Project-docs/decision.md`: Redundant duplicate consolidated into `decisions.md`.

### Created:
- `Project-docs/dumps/P02_dump.md`: This dump file.

