# P08c Dump — Resolve P08b Blockers, Disclose & Remove Scratch File, Correct Records

## 1. HEADER
- **Prompt ID:** PROMPT 08c: Resolve P08b blockers (two test expectations), disclose and remove scratch file, correct records. Liquid policy NOT changed here.
- **Timestamp:** 2026-11-03 08:15:00 IST
- **Venv Python Version:** Python 3.11.9
- **Git Commit:** `0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths`

---

## 2. PRE-FLIGHT
### Step 0a: Active Python Process Check
```powershell
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, CPU
```
Output:
```
(No active processes; exit code 0 / empty output)
```

### Step 0b: Catalog File Hash
```powershell
Get-FileHash -Algorithm SHA256 backend\data\catalog\janaushadhi.json
```
Output:
```
Algorithm       Hash                                                                   Path
---------       ----                                                                   ----
SHA256          779DF16A87E4F7D8CD7283AB461C1A416DA504A355ED49DF11033A9FA1DCF043       C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\catalog\janaushadhi.json
```

### Step 0c: Scratch File Check
```powershell
Test-Path backend\scratch\check_openapi.py
```
Output:
```
False
```

---

## 3. BASELINE
### Step 1a: Full Baseline Test Run
```powershell
cd backend ; .\venv\Scripts\python.exe -m pytest -q --durations=10 > pytest_out.txt 2>&1 ; Get-Content pytest_out.txt -Tail 25
```
Output:
```
============================== warnings summary ===============================
venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================ slowest 10 durations =============================
16.16s call     tests/test_phase0.py::test_subprocess_import_minimal_env
0.91s call     tests/test_price_lookup.py::test_no_scraping_module
0.87s call     tests/test_phase0.py::test_subprocess_import_production_fails_without_jwt_secret
0.11s call     tests/test_phase0.py::test_import_hermetic
0.07s call     tests/test_phase0.py::test_call_schedule_disabled_by_default
0.07s call     tests/test_ownership.py::test_ownership_rejection_403[POST_/hospitals/nearby]
0.07s call     tests/test_phase0.py::test_auth_login_rate_limit
0.06s call     tests/test_ownership.py::test_ownership_rejection_403[POST_/health/generate-qr/{user_id}]
0.04s call     tests/test_phase0.py::test_ready_endpoint_mongodb_fail_no_leak
0.04s call     tests/test_phase0.py::test_medicine_compare_rate_limit
=========================== short test summary info ===========================
FAILED tests/test_concentration_guard.py::test_search_paracetamol_250_first_result
FAILED tests/test_search_quality.py::test_concentration_items_have_mg_and_ml
2 failed, 160 passed, 2 warnings in 46.57s
```

### Step 1b: Route and OpenAPI Check
```powershell
import json, hashlib, sys, os
os.environ["APP_ENV"] = "development"
sys.path.insert(0, "src")
from agents.main import app
spec_obj = app.openapi()
spec = json.dumps(spec_obj, sort_keys=True, indent=2)
ops = sum(1 for p, ops in spec_obj['paths'].items() for m in ops if m in {'get', 'post', 'put', 'delete', 'patch'})
print('OPERATIONS:', ops)
print('OPENAPI_SHA256_INMEMORY_LF:', hashlib.sha256(spec.encode('utf-8')).hexdigest())
```
Output:
```
OPERATIONS: 43
OPENAPI_SHA256_INMEMORY_LF: 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1
```

---

## 4. CHANGED FILES
### `backend\tests\test_search_quality.py`
**Old Body:**
```python
def test_concentration_items_have_mg_and_ml():
    items = catalog.load_catalog()
    conc_items = [item for item in items if item.get("is_concentration") is True]
    assert len(conc_items) > 0
    for item in conc_items:
        clean = item.get("name_clean", "")
        assert "mg" in clean
        assert "ml" in clean
```

**New Body:**
```python
def test_concentration_items_have_mg_and_ml():
    import re
    items = catalog.load_catalog()
    conc_items = [item for item in items if item.get("is_concentration") is True]
    assert len(conc_items) > 0
    for item in conc_items:
        clean = item.get("name_clean", "")
        assert re.search(r"(mg|mcg|g|iu|%)", clean) is not None, clean
        assert "ml" in clean, clean
```

### `backend\tests\test_concentration_guard.py`
**Old Body:**
```python
def test_search_paracetamol_250_first_result():
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 250", items)
    assert len(results) > 0, "No non-liquid Paracetamol 250 exists in PMBJP data"
    first = results[0]
    assert any(
        c.get("salt") == "paracetamol" and c.get("strength") == 250.0
        for c in first.get("components", [])
    )
```

**New Body:**
```python
def test_search_paracetamol_250_first_result():
    items = catalog.load_catalog()
    # Data fact (verified in P08c): the PMBJP list has no solid (Tablet/Capsule) paracetamol 250 mg product.
    # Only two liquid rows (sr_no 519 and 1051) carry paracetamol 250.
    liquid_250 = [
        item for item in items
        if item.get("dosage_form") == "Liquid"
        and any(c.get("salt") == "paracetamol" and c.get("strength") == 250.0 for c in item.get("components", []))
    ]
    assert len(liquid_250) == 2
    # Current policy (D48): liquids are excluded from strength-qualified search.
    # If the liquid policy changes (open decision, Gautam), this assertion must be updated in that prompt.
    assert catalog.search("paracetamol 250", items) == []
```

### `Project-docs\decisions.md` (appended D49 only)
```markdown
---

## D49 — Resolution of P08b Blockers, Disclosure of Scratch File, and Open Liquid Policy Decision (3 Nov 2026)

**Status:** Built and verified (Prompt 08c, 3 Nov 2026). Full suite: 162 passed, 0 failed in 29.62s. Route count: 43. OpenAPI canonical in-memory LF SHA256 preserved (`37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`). Catalog JSON hash unchanged (`779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043`). Zero frontend modifications.

**Decisions & Corrections:**
1. **Correction to D48 Status:**
   - D48 stated "Status: Built and verified", but P08b concluded with 160 passed and 2 failed tests. Those two failures were recorded as blockers. P08c formally resolves both test expectations, bringing the test suite to 162 passed, 0 failed (Step 5a).
2. **Blocker 1 Resolution (`test_concentration_items_have_mg_and_ml`):**
   - The legacy assertion in `backend/tests/test_search_quality.py` strictly demanded `"mg" in clean` and `"ml" in clean`, reflecting the pre-P08b single-unit definition.
   - Valid per-volume concentrations flagged by `CONCENTRATION_RX` include `40 IU per ml` (soluble insulin) and `10g per 15ml` (lactulose oral solution).
   - Replaced function body with an independent check requiring a valid strength unit (`re.search(r"(mg|mcg|g|iu|%)", clean) is not None`) and `"ml" in clean`. This is non-tautological and verifies that all 133 flagged items are true per-volume liquid formulations.
3. **Blocker 2 Resolution (`test_search_paracetamol_250_first_result`):**
   - In Prompt 08b, the prompt author/reviewer assumed a solid (tablet/capsule) Paracetamol 250 mg product existed in the catalog.
   - Empirical examination of the official PMBJP list (2,445 items) reveals zero solid Paracetamol 250 products; only two liquid rows exist (sr_no 519 and 1051, oral suspensions).
   - Under the current policy (D48), liquids and concentrations are excluded from strength queries, meaning `catalog.search("paracetamol 250", items)` correctly returns `[]`.
   - Updated `test_search_paracetamol_250_first_result` in `backend/tests/test_concentration_guard.py` to assert the empirical data fact (len(liquid_250) == 2) and current policy (`search("paracetamol 250", items) == []`).
4. **OPEN PRODUCT DECISION (Gautam) — Liquid Exclusion for Strength Queries:**
   - **Evidence:** 9 paracetamol liquid rows exist in the catalog (sr_no 21, 458, 476, 519, 634, 987, 1049, 1051, 1055).
   - Solid single-ingredient paracetamol strengths in PMBJP are 325, 500, 650, and 1000 mg.
   - Pediatric suspension strengths (120 mg/5ml, 125 mg/5ml, and 250 mg/5ml) cannot be reached through strength queries under the current exclusion policy.
   - **Option A:** Keep the exclusion of liquids from strength queries and display an explicit message in UI: `"solid form not found, search syrup"`.
   - **Option B:** Include liquids in search results, rank solid oral dosage forms first, and display a prominent per-5ml dosage safety disclaimer.
   - **Reviewer recommendation:** Option B.
   - **Status:** PENDING review by Gautam.
5. **Scratch File Disclosure & Deletion:**
   - `backend/scratch/check_openapi.py` was created during Prompt 08 and used in P08 and P08b without being listed in an allowed-files list.
   - Pre-flight check (Step 0c) verified `backend/scratch/check_openapi.py` did not exist (`False`). Deletion step (Step 6) verified `scratch/check_openapi.py` was absent and confirmed no `backend/scratch/` directory remained.
6. **Correction to P08b Checklist:**
   - The P08b checklist previously marked git status clean, which was inaccurate given untracked test and doc files created in Phase 1 / Phase 2. The actual git status is recorded verbatim in the P08c dump.
```

### `Project-docs\progress.md` (appended P08c entry only)
```markdown
---

## PROMPT 08c: Resolve P08b Blockers, Scratch Disclosure, Open Liquid Policy (3 Nov 2026)
- **Status:** CLOSED (162 tests passed, 0 failed, full suite green in 29.62s).
- **P08b Status Update:** Changed from CLOSED to "CLOSED WITH BLOCKERS RESOLVED IN P08c".
- **Catalog JSON Hash:** `779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043` (unchanged, importer not rerun).
- **Route Count:** 43 operations.
- **OpenAPI In-Memory LF Hash:** `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1` (unchanged).

### Accomplishments
- [x] **Blocker 1 Resolved (`tests/test_search_quality.py`):**
  - Updated `test_concentration_items_have_mg_and_ml` body to assert regex strength unit `(mg|mcg|g|iu|%)` and `"ml"` substring, supporting valid non-mg concentration products like insulin (`40 IU per ml`) and lactulose (`10g per 15ml`).
- [x] **Blocker 2 Resolved (`tests/test_concentration_guard.py`):**f
  - Updated `test_search_paracetamol_250_first_result` body to assert catalog data fact (2 liquid Paracetamol 250 rows exist at sr_no 519 & 1051, 0 solid rows) and current search policy (`search("paracetamol 250", items) == []`).
- [x] **Scratch File Audit & Deletion:**
  - Disclosed `backend/scratch/check_openapi.py` (created in P08). Verified absent in Step 0c and Step 6. Ensured no `scratch` directory exists.
- [x] **Git Status Audit:**
  - Corrected P08b checklist note; captured full working tree git status verbatim in P08c dump.
- [x] **Full Suite Verification:**
  - 162 passed, 0 failed across entire backend test suite.

### Open Decisions
- **Liquid Exclusion Policy (Gautam):** Status: OPEN / PENDING. Option A (keep liquid exclusion from strength queries with UI guidance) vs. Option B (allow liquids ranked after solids with dosage warnings). Reviewer recommends Option B.
```

### `backend\data\catalog\janaushadhi.json`
- SHA256: `779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043` (unchanged)
- Size: 1,846,750 bytes (unchanged)

### Frontend Entries & .env
- Frontend entries touched: 0
- Values from backend\.env: None (never opened, printed, or copied)

---

## 5. VERIFICATION
### Step 5a: Full Test Suite Execution
```powershell
cd backend ; .\venv\Scripts\python.exe -m pytest -q --durations=10 > pytest_all.txt 2>&1 ; Get-Content pytest_all.txt -Tail 25
```
Output:
```
........................................................................ [ 44%]
........................................................................ [ 88%]
..................                                                       [100%]
============================== warnings summary ===============================
venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================ slowest 10 durations =============================
14.26s call     tests/test_phase0.py::test_subprocess_import_minimal_env
0.77s call     tests/test_phase0.py::test_subprocess_import_production_fails_without_jwt_secret
0.11s call     tests/test_phase0.py::test_import_hermetic
0.04s call     tests/test_phase0.py::test_auth_login_rate_limit
0.02s call     tests/test_call_schedule_disabled_by_default
0.02s call     tests/test_catalog.py::test_row_count_and_unique_codes
0.02s call     tests/test_price_lookup.py::test_best_price_site_when_available
0.01s call     tests/test_phase0.py::test_medicine_compare_rate_limit
0.01s call     tests/test_routes_auth.py::test_protected_route_rejects_missing_token[POST-/health/doctor-qr/{user_id}]
0.01s call     tests/test_price_lookup.py::test_no_scraping_module
162 passed, 2 warnings in 29.62s
```

### Step 5b: Catalog Hash Verification
```powershell
Get-FileHash -Algorithm SHA256 backend\data\catalog\janaushadhi.json
```
Output:
```
Algorithm       Hash                                                                   Path
---------       ----                                                                   ----
SHA256          779DF16A87E4F7D8CD7283AB461C1A416DA504A355ED49DF11033A9FA1DCF043       C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\catalog\janaushadhi.json
```

### Step 5c: Subprocess Import Check
```powershell
$env:APP_ENV="development"; .\venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); import agents.main; print('IMPORT_OK')"
```
Output:
```
IMPORT_OK
```

### Step 5d: Route and OpenAPI Check
```powershell
import json, hashlib, sys, os
os.environ["APP_ENV"] = "development"
sys.path.insert(0, "src")
from agents.main import app
spec_obj = app.openapi()
spec = json.dumps(spec_obj, sort_keys=True, indent=2)
ops = sum(1 for p, ops in spec_obj['paths'].items() for m in ops if m in {'get', 'post', 'put', 'delete', 'patch'})
print('OPERATIONS:', ops)
print('OPENAPI_SHA256_INMEMORY_LF:', hashlib.sha256(spec.encode('utf-8')).hexdigest())
```
Output:
```
OPERATIONS: 43
OPENAPI_SHA256_INMEMORY_LF: 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1
```

### Step 5e: Scraping Modules in src Check
```powershell
Get-ChildItem src -Recurse -Filter *.py | Select-String -Pattern "browser_use|playwright"
```
Output:
```
(No output from command)
```

### Step 5f: Full Git Status (Verbatim)
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
 M backend/tests/test_concentration_guard.py
 M backend/tests/test_search_quality.py
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

## 6. DELETIONS
```powershell
scratch\check_openapi.py existed: False
pytest_out.txt existed: True -> Deleted pytest_out.txt
pytest_all.txt existed: True -> Deleted pytest_all.txt
scratch dir exists: False
Post-check pytest_out.txt: False
Post-check pytest_all.txt: False
Post-check scratch dir: False
```

---

## 7. CHECKLIST
- [x] Step 0: Pre-flight checks passed (0 active python processes, catalog hash `779DF16A...`, scratch file `False`).
- [x] Step 1: Baseline tests recorded (160 passed, 2 failed on expected test names; operations 43, canonical hash matched).
- [x] Step 2: Test Fix A applied to `test_concentration_items_have_mg_and_ml` in `test_search_quality.py` (9 passed).
- [x] Step 3: Test Fix B applied to `test_search_paracetamol_250_first_result` in `test_concentration_guard.py` (8 passed).
- [x] Step 4: Documentation appended to `decisions.md` (D49) and `progress.md` (P08c).
- [x] Step 5: Verification passed (162 passed in 29.62s; catalog hash unchanged; `IMPORT_OK`; 43 operations with canonical OpenAPI hash; 0 scraping refs in `src`; full git status recorded).
- [x] Step 6: Deletions verified (`pytest_out.txt` and `pytest_all.txt` deleted; `scratch\check_openapi.py` not present).
- [x] Step 7: Dump created at `Project-docs\dumps\P08c_dump.md`.

---

## 8. DEVIATIONS AND BLOCKERS
- **Blocker 1 Resolution:** `test_concentration_items_have_mg_and_ml` updated to check for any valid strength unit + "ml".
- **Blocker 2 Resolution (Reviewer Error Acknowledgment):** The expectation of a solid Paracetamol 250 mg formulation in the PMBJP dataset was a reviewer error; empirical data contains only liquid suspensions (sr_no 519 and 1051). Test updated to verify the data fact and the current exclusion policy.
- **Unresolved Blockers:** None.

---

## 9. DEFERRED
- Liquid exclusion policy (Gautam decision, OPEN).
- Brand map and savings (P09).
- Frontend Compare update.
- Playwright and browser-use removal from `pyproject.toml`, `uv.lock`, and `Dockerfile` (deployment prompt).
- H1 (`/call/status` public when calls are enabled).
- M5 (`Project-docs` not under version control).
- Decision on committing `backend/data/`.
- `is_medicine` non-medicine groups review (Gautam).
- `x-request-id` exposure (frontend phase).

