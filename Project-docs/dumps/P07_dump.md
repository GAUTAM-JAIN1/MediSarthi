# P07 Dump: Scraping Removal, Catalog-Backed /medicine/compare

## 1. HEADER
- **Prompt ID:** PROMPT 07
- **Date & Time:** 2026-11-03 06:58:00 IST
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

### Step 0b: Catalog Files Existence & SHA256 Check
```powershell
Test-Path backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv ; Get-FileHash -Algorithm SHA256 backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv ; Get-FileHash -Algorithm SHA256 backend\data\catalog\janaushadhi.json
```
Output:
```
True

Algorithm       Hash                                                                   Path                            
---------       ----                                                                   ----                            
SHA256          4AC1C0E8967E16DE86AAD74B0810FC06342D5F81BBE3E27BB7C6E5D46E02C4D3       C:\Users\gauta\OneDrive\Deskt...
SHA256          E5D0B82758B702959789F67691B03BAA438C9A2BA9713237B8CF6FF14BB68D7C       C:\Users\gauta\OneDrive\Deskt...
```

---

## 3. BASELINE

### Step 1a: Baseline Pytest with Durations
```powershell
cd backend ; .\venv\Scripts\python.exe -m pytest -q --durations=10 > pytest_out.txt 2>&1 ; Get-Content pytest_out.txt -Tail 20
```
Output:
```
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================ slowest 10 durations =============================
15.02s call     tests/test_phase0.py::test_subprocess_import_minimal_env
0.83s call     tests/test_phase0.py::test_subprocess_import_production_fails_without_jwt_secret
0.15s call     tests/test_phase0.py::test_import_hermetic
0.03s call     tests/test_phase0.py::test_auth_login_rate_limit
0.02s call     tests/test_phase0.py::test_call_schedule_disabled_by_default
0.02s call     tests/test_catalog.py::test_row_count_and_unique_codes
0.02s call     tests/test_phase0.py::test_medicine_compare_rate_limit
0.01s call     tests/test_ownership.py::test_ownership_rejection_403[GET_/health/vitals/{user_id}]
0.01s call     tests/test_ownership.py::test_ownership_rejection_403[POST_/health/generate-qr/{user_id}]
0.01s call     tests/test_ownership.py::test_ownership_rejection_403[POST_/general-query]
136 passed, 2 warnings in 33.12s
```

### Step 1b: Baseline OpenAPI Check
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

---

## 4. IMPORT GRAPH

### Step 2 Output (Verbatim)
```powershell
Get-ChildItem src, tests, scripts -Recurse -Filter *.py | Select-String -Pattern "buying_agent|browser_use|playwright"
```
Output:
```
src\agents\buying_agent.py:76:BUYING_AGENT_MODEL = os.getenv("BUYING_AGENT_GROQ_MODEL", "openai/gpt-oss-120b")
src\agents\buying_agent.py:82:# unset lets Playwright use its own managed Chromium (installed into the
src\agents\buying_agent.py:83:# image via `playwright install --with-deps chromium` in the Dockerfile ?"
src\agents\buying_agent.py:87:CHROME_EXECUTABLE_PATH = os.getenv("CHROME_EXECUTABLE_PATH")  # None -> Playwright-managed Chromium
src\agents\buying_agent.py:203:def _load_browser_use():
src\agents\buying_agent.py:207:    from browser_use import Agent, Browser, ChatGroq, Tools
src\agents\buying_agent.py:231:    Agent, Browser, ChatGroq, Tools = _load_browser_use()
src\agents\buying_agent.py:234:    llm = ChatGroq(model=BUYING_AGENT_MODEL)
src\agents\buying_agent.py:270:        print(f"[buying_agent] {site_label} timed out after {PER_SITE_TIMEOUT_SECONDS}s ?" skipping this site.")
src\agents\buying_agent.py:277:        print(f"[buying_agent] {site_label} failed with an error: {e}")
src\agents\buying_agent.py:310:        print(f"[buying_agent] Skipping a malformed record from {fallback_site}: {e} | raw={raw}")
src\agents\Calling_Ai.py:21:# general-purpose replacement. Unlike buying_agent.py, this file never
src\agents\routes\medicine.py:6:from agents.buying_agent import run_comparison
```
*Note on `Calling_Ai.py:21`:* This match is an explanatory comment (`# general-purpose replacement. Unlike buying_agent.py, this file never handles images...`), not an import or code dependency. The only actual code import of `buying_agent` in the codebase was `src\agents\routes\medicine.py:6`.

### Step 4 Line Change in `backend/src/agents/routes/medicine.py`
- **Before:**
```python
from agents.buying_agent import run_comparison
```
- **After:**
```python
from agents.price_lookup import run_comparison
```

---

## 5. CHANGED FILES

### `backend/src/agents/price_lookup.py`
```python
"""Catalog-backed price lookup over the PMBJP list. No network. No scraping."""

from typing import Any, Dict, List, Optional

from agents import catalog

JANAUSHADHI_SITE = "PMBJP Jan Aushadhi"
MAX_RESULTS_PER_MEDICINE = 10


async def run_comparison(medicines: List[str]) -> Dict[str, Any]:
    """Catalog-backed comparison returning PMBJP Jan Aushadhi prices."""
    items = catalog.load_catalog()
    medicines_output: List[Dict[str, Any]] = []

    for raw in medicines:
        name = (raw or "").strip()
        if not name:
            continue

        hits = catalog.search(name, items)[:MAX_RESULTS_PER_MEDICINE]
        results: List[Dict[str, Any]] = []

        for h in hits:
            available = h.get("price_status") == "listed"
            notes = f"{h.get('dosage_form', '')} | list dated {h.get('source_date', '')}"
            if not available:
                notes += " | price not notified"

            result_entry = {
                "site": JANAUSHADHI_SITE,
                "product_name": h.get("name_raw", ""),
                "price": h.get("mrp"),
                "quantity": h.get("unit_size_raw", ""),
                "delivery_info": "",
                "product_url": "",
                "available": available,
                "notes": notes,
            }
            results.append(result_entry)

        best_price_site: Optional[str] = (
            JANAUSHADHI_SITE if any(r["available"] for r in results) else None
        )

        medicines_output.append(
            {
                "medicine_name": name,
                "results": results,
                "best_price_site": best_price_site,
                "fastest_delivery_site": None,
            }
        )

    return {"medicines": medicines_output}
```

### `backend/tests/test_price_lookup.py`
```python
"""Tests for agents.price_lookup module and catalog-backed price comparison."""

import asyncio
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend/src is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from agents.price_lookup import JANAUSHADHI_SITE, run_comparison
from agents.main import app
from agents.rate_limit import COMPARE_LIMITER


@pytest.fixture
def reset_compare_limiter():
    """Reset rate limiter before and after route test to prevent 429."""
    COMPARE_LIMITER.reset()
    yield
    COMPARE_LIMITER.reset()


def test_run_comparison_shape():
    res = asyncio.run(run_comparison(["Paracetamol"]))
    meds = res.get("medicines", [])
    assert len(meds) == 1
    m = meds[0]
    assert set(m.keys()) == {"medicine_name", "results", "best_price_site", "fastest_delivery_site"}
    results = m["results"]
    assert len(results) > 0

    expected_keys = {
        "site",
        "product_name",
        "price",
        "quantity",
        "delivery_info",
        "product_url",
        "available",
        "notes",
    }
    for r in results:
        assert set(r.keys()) == expected_keys
        assert r["site"] == JANAUSHADHI_SITE


def test_levothyroxine_synonym():
    res = asyncio.run(run_comparison(["Levothyroxine"]))
    results = res["medicines"][0]["results"]
    assert len(results) > 0


def test_unknown_medicine():
    res = asyncio.run(run_comparison(["Xyzzyqwerty"]))
    m = res["medicines"][0]
    assert m["results"] == []
    assert m["best_price_site"] is None


def test_not_notified_rows():
    res = asyncio.run(run_comparison(["Cetirizine"]))
    results = res["medicines"][0]["results"]
    assert len(results) > 0
    unavail = [r for r in results if not r["available"]]
    assert len(unavail) > 0
    for r in unavail:
        assert r["price"] is None
        assert "price not notified" in r["notes"]


def test_best_price_site_when_available():
    res = asyncio.run(run_comparison(["Paracetamol"]))
    m = res["medicines"][0]
    if any(r["available"] for r in m["results"]):
        assert m["best_price_site"] == JANAUSHADHI_SITE


def test_no_scraping_module():
    assert importlib.util.find_spec("agents.buying_agent") is None
    src_dir = Path(__file__).resolve().parent.parent / "src"
    for py_file in src_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        assert "browser_use" not in text, f"Found browser_use in {py_file}"
        assert "playwright" not in text, f"Found playwright in {py_file}"


def test_route_medicine_compare_200(reset_compare_limiter):
    client = TestClient(app)
    resp = client.post("/medicine/compare", json={"medicines": ["Paracetamol"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "medicines" in body


def test_openapi_hash_invariant():
    spec_obj = app.openapi()
    spec = json.dumps(spec_obj, sort_keys=True, indent=2)
    computed_hash = hashlib.sha256(spec.encode("utf-8")).hexdigest()
    assert computed_hash == "37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1"
```

### `backend/src/agents/routes/medicine.py` (Line Change Only)
```python
# Before:
from agents.buying_agent import run_comparison

# After:
from agents.price_lookup import run_comparison
```

### `backend/tests/test_ownership.py` (Added Function Only)
```python
def test_openapi_request_body_user_ids_covered():
    """Assert all OpenAPI operations with user_id/requester_user_id in requestBody are covered in CASES."""
    spec = app.openapi()
    http_methods = {"get", "post", "put", "delete", "patch"}
    body_ops = set()

    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            if method.lower() not in http_methods:
                continue
            if "requestBody" in op:
                content = op["requestBody"].get("content", {})
                for media in content.values():
                    schema = media.get("schema", {})
                    if "$ref" in schema:
                        name = schema["$ref"].split("/")[-1]
                        props = spec["components"]["schemas"][name].get("properties", {})
                    else:
                        props = schema.get("properties", {})
                    if "user_id" in props or "requester_user_id" in props:
                        body_ops.add((method.upper(), path))

    assert len(body_ops) > 0

    case_templates = {(m, t) for m, t, _, _ in CASES}
    body_ops_no_brace = {op for op in body_ops if "{" not in op[1]}
    missing = body_ops_no_brace - case_templates
    assert not missing, "OpenAPI routes with a user_id body/form field missing from ownership cases: " + str(missing)

    cases_no_brace = {c for c in case_templates if "{" not in c[1]}
    assert cases_no_brace.issubset(body_ops)
```

### Appended to `Project-docs/decisions.md` (D46)
```markdown
---

## D46 — Scraping Removal and Catalog-Backed Medicine Comparison (3 Nov 2026)

**Status:** Built and verified (Prompt 07, 3 Nov 2026). All 145 automated tests passing (136 baseline + 8 new price lookup tests + 1 new ownership requestBody coverage test). Route count: 43. OpenAPI canonical in-memory LF SHA256 preserved (`37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`). Zero frontend modifications.

**Decisions:**
1. **Scraping Removal & Catalog-Backed Replacement (`agents.price_lookup`):**
   - Live scraping (`buying_agent.py`) via `browser_use` and Playwright was removed. Scraping was excessively slow (60–240s per call), token-heavy, prone to anti-bot blocks/timeouts on Apollo/1mg, and blocked on Windows due to the hardcoded `\tmp` directory creation in `browser_use` (C2).
   - Replaced by deterministic, offline catalog lookups over the official PMBJP product list via `catalog.search` (`agents.catalog`). Responses now return in sub-second time with zero LLM/browser overhead.
2. **Deliberate Behavior Changes:**
   - `/medicine/compare` no longer scrapes third-party pharmacy websites. It returns generic prices from the 2 Nov 2026 PMBJP Jan Aushadhi product list.
   - When no catalog match is found, `/medicine/compare` returns HTTP 200 with an empty `results: []` list. Previously, it returned HTTP 502 when both scraping targets failed.
   - The returned `site` label is `"PMBJP Jan Aushadhi"`. `price` is the generic MRP from the list (`null` if unnotified). Delivery information is `""`. Brand prices and savings percentages are not computed at this layer (deferred to brand mapping).
3. **C2 Status (Closed in Code):**
   - The Windows `\tmp` permission bug (C2) is completely resolved in application code: `browser_use` and `playwright` are no longer imported anywhere in `backend/src/`.
   - Remaining package entries in `pyproject.toml`, `uv.lock`, and the Playwright installation layer in `Dockerfile` are preserved without change for now; their removal is deferred to the deployment cleanup prompt.
4. **Corrections to D45:**
   - Withdrew the statement that `validate_startup()` logs warnings in development mode; in development mode `validate_startup()` performs no missing-setting checks.
   - Clarified the ownership test count: exactly 32 route cases (17 path-parameter, 11 JSON body, 4 multipart) plus 1 unit test and 1 OpenAPI path coverage test (total 34 tests in P06).
   - P07 added `test_openapi_request_body_user_ids_covered` to inspect OpenAPI `requestBody` schemas, validating that every route with `user_id` or `requester_user_id` in its payload is tested.
5. **Known Limits & Deferred Items:**
   - Brand names (e.g. Dolo 650) do not match generic salts until the brand-to-generic mapping is implemented (P08).
   - Strength-qualified queries (e.g. "paracetamol 650") do not match generic salt names directly.
   - Price per unit is not normalized across dosage forms (e.g., comparing syrup ml vs tablet units).
   - `x-request-id` header exposure to browser clients requires `Access-Control-Expose-Headers`, which will be added during the frontend integration phase.
```

### Appended to `Project-docs/progress.md` (P07)
```markdown
---

## Prompt 07 — Scraping Removal & Catalog-Backed Price Lookup (3 Nov 2026)

Prompt 07 status: CLOSED.

### Completed Work
- [x] **Catalog-Backed Price Lookup (`agents.price_lookup`):**
  - Created pure in-memory module querying PMBJP catalog data without network access.
  - Generates exact response shape matching previous `/medicine/compare` structure (`site: "PMBJP Jan Aushadhi"`, `product_name`, `price`, `quantity`, `delivery_info`, `product_url`, `available`, `notes`).
- [x] **Router Update (`routes/medicine.py`):**
  - Replaced import of `run_comparison` from `buying_agent` with `agents.price_lookup`.
- [x] **Scraping Removal & C2 Closure:**
  - Deleted `backend/src/agents/buying_agent.py`.
  - Zero imports or references to `browser_use` or `playwright` remain across `backend/src/`.
  - C2 (browser-use Windows `\tmp` permission error) is CLOSED in code.
- [x] **Ownership Suite Enhancement (`test_ownership.py`):**
  - Added `test_openapi_request_body_user_ids_covered` verifying that every route with `user_id` or `requester_user_id` in its requestBody schema is explicitly covered in ownership test cases.
- [x] **Price Lookup Test Suite (`tests/test_price_lookup.py`):**
  - Added 8 comprehensive offline tests verifying response shape, synonym lookup, unknown drug fallback, not-notified MRP rows, best price site logic, absence of scraping dependencies in `src`, 200 OK route execution, and OpenAPI hash preservation.
- [x] **Test Suite & Invariants:**
  - Full test suite: **145 passed, 0 failed** in 29.12s (136 baseline + 8 price lookup + 1 ownership requestBody coverage).
  - Route count: 43 (0 new routes added).
  - OpenAPI canonical in-memory LF SHA256 preserved: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
  - Catalog SHA256 invariant preserved: `e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`.
  - Live smoke test confirmed sub-second `/medicine/compare` execution with 10 catalog-backed results for Paracetamol.

### Deferred Items
- Brand seed dataset, brand-to-generic mapping, and savings calculation (P08).
- Strength-aware query matching and cross-form price normalization (P08).
- Removal of `browser_use` and `playwright` from `pyproject.toml`, `uv.lock`, and `Dockerfile` (deployment cleanup prompt).
- Error contract (Phase 2).
- `Access-Control-Expose-Headers` for `x-request-id` (frontend phase).
- Frontend Compare page adjustments to use static catalog (frontend phase).
- H1 (`/call/status` public when calls are enabled).
- M5 (`Project-docs` not under version control).
- Decision on committing `backend/data/`.
- `is_medicine` non-medicine groups review (Gautam).
```

---

## 6. VERIFICATION (Step 7 Outputs, Verbatim)

### Step 7a: Full Pytest Suite with Durations
```powershell
.\venv\Scripts\python.exe -m pytest -q --durations=10 > pytest_all.txt 2>&1 ; Get-Content pytest_all.txt -Tail 20
```
Output:
```
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================ slowest 10 durations =============================
14.64s call     tests/test_phase0.py::test_subprocess_import_minimal_env
1.09s call     tests/test_phase0.py::test_subprocess_import_production_fails_without_jwt_secret
0.11s call     tests/test_phase0.py::test_import_hermetic
0.03s call     tests/test_phase0.py::test_auth_login_rate_limit
0.03s call     tests/test_catalog.py::test_row_count_and_unique_codes
0.02s call     tests/test_phase0.py::test_call_schedule_disabled_by_default
0.01s call     tests/test_phase0.py::test_medicine_compare_rate_limit
0.01s call     tests/test_price_lookup.py::test_no_scraping_module
0.01s call     tests/test_ownership.py::test_ownership_rejection_403[POST_/hospitals/nearby]
0.01s call     tests/test_health.py::test_health_check_responds
145 passed, 2 warnings in 29.12s
```

### Step 7b: Subprocess Import Check
```powershell
$env:APP_ENV="development"; .\venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); import agents.main; print('IMPORT_OK')"
```
Output:
```
IMPORT_OK
```

### Step 7c: Route and OpenAPI Check
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

### Step 7d: Verification of Zero `browser_use` or `playwright` References in `src`
```powershell
Get-ChildItem src -Recurse -Filter *.py | Select-String -Pattern "browser_use|playwright"
```
Output:
```
(No matches found)
```

### Step 7e: Live Smoke Test for `/medicine/compare` (First 2 Results)
```powershell
=== 1. Invoke-RestMethod /ready ===


status : ready
checks : @{mongo_uri=ok; groq_api_key=ok; jwt_secret_key=ok; mongodb=ok}



=== 2. Invoke-RestMethod /medicine/compare ===
{
    "medicines":  [
                      {
                          "medicine_name":  "Paracetamol",
                          "results":  [
                                          {
                                              "site":  "PMBJP Jan Aushadhi",
                                              "product_name":  "Paracetamol Tablets IP 500 mg",
                                              "price":  6.56,
                                              "quantity":  "10\u0027s",
                                              "delivery_info":  "",
                                              "product_url":  "",
                                              "available":  true,
                                              "notes":  "Tablet | list dated 2026-11-02"
                                          },
                                          {
                                              "site":  "PMBJP Jan Aushadhi",
                                              "product_name":  "Paracetamol 325mg and Dicyclomine Hydrochloride 20mg Tablets",
                                              "price":  7.5,
                                              "quantity":  "10\u0027s",
                                              "delivery_info":  "",
                                              "product_url":  "",
                                              "available":  true,
                                              "notes":  "Tablet | list dated 2026-11-02"
                                          }
```

### Step 7f: Git Status
```powershell
git status --short
```
Output:
```
 M backend/src/agents/Calling.py
 M backend/src/agents/Calling_Ai.py
 D backend/src/agents/buying_agent.py
 M backend/src/agents/db_connect.py
 M backend/src/agents/jwt_utils.py
 M backend/src/agents/main.py
?? backend/.env.example
?? backend/data/
?? backend/scripts/
?? backend/src/agents/catalog.py
?? backend/src/agents/config.py
?? backend/src/agents/errors.py
?? backend/src/agents/file_utils.py
?? backend/src/agents/hospital_parser.py
?? backend/src/agents/llm_output.py
?? backend/src/agents/price_lookup.py
?? backend/src/agents/rate_limit.py
?? backend/src/agents/request_context.py
?? backend/src/agents/routes/
?? backend/src/agents/schemas.py
?? backend/tests/test_catalog.py
?? backend/tests/test_config.py
?? backend/tests/test_ownership.py
?? backend/tests/test_phase0.py
?? backend/tests/test_price_lookup.py
?? backend/tests/test_request_context.py
?? backend/tests/test_routes_auth.py
?? local-changes.patch
```

---

## 7. DELETIONS

- **Step 5a:** `Remove-Item src\agents\buying_agent.py` -> verified `Test-Path` returned `False`.
- **Step 8:**
  - `pytest_out.txt deleted`
  - `pytest_all.txt deleted`
  - `pytest_price.txt did not exist`

---

## 8. CHECKLIST

- [x] Step 0: Pre-flight verified 0 active python processes, CSV SHA256 `4AC1C0E8967E16DE86AAD74B0810FC06342D5F81BBE3E27BB7C6E5D46E02C4D3`, and JSON SHA256 `E5D0B82758B702959789F67691B03BAA438C9A2BA9713237B8CF6FF14BB68d7c`.
- [x] Step 1: Baseline verified 136 tests passed, 43 routes, and OpenAPI SHA256 `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
- [x] Step 2: Import graph check completed; confirmed only `routes/medicine.py` had an import dependency.
- [x] Step 3: Implemented `agents.price_lookup` with catalog-backed lookup and zero network/scraping dependencies.
- [x] Step 4: Updated single import line in `routes/medicine.py`.
- [x] Step 5: Deleted `buying_agent.py`; verified zero `browser_use|playwright` occurrences in `src`.
- [x] Step 6: Created `test_price_lookup.py` (8 tests) and appended `test_openapi_request_body_user_ids_covered` to `test_ownership.py`.
- [x] Step 7: Final verification passed: 145 tests passed in 29.12s, `IMPORT_OK` in subprocess, 43 operations and OpenAPI invariant intact, zero browser_use/playwright in src, live smoke test confirmed 10 catalog results in <1s.
- [x] Step 8: Deleted temporary output text files (`pytest_out.txt`, `pytest_all.txt`).
- [x] Step 9: Appended decision D46 to `decisions.md` and P07 entry to `progress.md`.
- [x] Step 10: Generated dump report at `Project-docs/dumps/P07_dump.md`.

---

## 9. DEVIATIONS AND BLOCKERS

- **Blockers:** None.
- **Deviations:** None.
- **Duration Analysis (Slowest Tests from Step 7a):**
  1. `14.64s`: `tests/test_phase0.py::test_subprocess_import_minimal_env` — full FastAPI application subprocess cold import.
  2. `1.09s`: `tests/test_phase0.py::test_subprocess_import_production_fails_without_jwt_secret` — subprocess production startup error validation.
  3. `0.11s`: `tests/test_phase0.py::test_import_hermetic` — in-process hermetic import validation with sys.modules reload.
  All other 142 tests completed in <= 0.03 seconds each. Total execution duration was 29.12s.

---

## 10. DEFERRED

- Brand seed and savings (P08)
- Strength-aware query matching (P08)
- Cross-form price normalization (P08)
- Playwright dependency and Dockerfile removal (deployment prompt)
- H1: `/call/status` public when calls are enabled
- M5: `Project-docs` not under version control
- Decision on committing `backend\data`
- `is_medicine` review (Gautam)
- Concentration notation and comma-split limits
- `x-request-id` exposure via `Access-Control-Expose-Headers` (frontend phase)
- Frontend Compare page update (frontend phase)

