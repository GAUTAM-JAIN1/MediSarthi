# P04b Dump: P04 Record Closure

## 1. HEADER
- **Prompt ID:** PROMPT 04b: P04 record closure (canonical OpenAPI hash, label fix, deferred reassignment, gap record)
- **Date/Time:** 2026-11-02 08:18:00 +05:30
- **Python Version:** Python 3.11.9
- **Git Commit:** `0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths`

---

## 2. BASELINE (Step 0)

### Step 0a: Baseline Pytest Output
```powershell
cd backend
$env:APP_ENV="development"
python -m pytest -q
```
Output:
```
.....................................................                    [100%]
============================== warnings summary ===============================
venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
53 passed, 2 warnings in 26.69s
```

### Step 0b: Baseline Hashes (BEFORE)
```powershell
Get-FileHash -Algorithm SHA256 Project-docs\progress.md, Project-docs\decisions.md
```
Output:
```
Algorithm       Hash                                                               Path
---------       ----                                                               ----
SHA256          3A241535D6B23F116B8B031D08F092F5781FDF8B102E1C6DA7764DCAB9612B22   C:\Users\gauta\OneDrive\Desktop\MediSarthi\Project-docs\progress.md
SHA256          EAA329F8886D24AF7001D05DBECCDFD33B6B990F9434117EBF89DB2B56420877   C:\Users\gauta\OneDrive\Desktop\MediSarthi\Project-docs\decisions.md
```

---

## 3. CANONICAL HASH (Step 1)

### Execution Output
```powershell
@'
import json, hashlib, sys
sys.path.insert(0, "src")
from agents.main import app
spec_obj = app.openapi()
spec = json.dumps(spec_obj, sort_keys=True, indent=2)
ops = sum(1 for p, ops in spec_obj["paths"].items() for m in ops if m in {"get", "post", "put", "delete", "patch"})
print("OPERATIONS:", ops)
print("OPENAPI_SHA256_INMEMORY_LF:", hashlib.sha256(spec.encode("utf-8")).hexdigest())
'@ | python -
```
Output:
```
OPERATIONS: 43
OPENAPI_SHA256_INMEMORY_LF: 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1
```

### Reason Canonical
File hashes on disk are newline-dependent: files written on Windows default to CRLF line terminators (`\r\n`), altering the SHA256 of the byte stream (`88b004d616466b6cfb13f5088bc0cab02c3026234fb88bdd602ca3e6351e52cb`), whereas on Linux/POSIX or with explicit LF newlines, the file hash is `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`. Computing the SHA256 of the in-memory string `json.dumps(app.openapi(), sort_keys=True, indent=2)` directly encoded as UTF-8 (pure LF `\n`) isolates OpenAPI parity from platform newline conversions and provides a strictly deterministic, platform-agnostic invariant.

---

## 4. EDITS

### `Project-docs\progress.md`

#### Step 2: Header Label Fix
- **OLD:**
  ```markdown
  ## Phase 1 (Prompt 04) — Behavior-Neutral Cleanup & Auth Coverage (2 Nov 2026)
  ```
- **NEW:**
  ```markdown
  ## Prompt 04 — Behavior-Neutral Cleanup & Auth Coverage (2 Nov 2026)
  ```
- **Step 2c Verification:**
  ```powershell
  Select-String -Path Project-docs\progress.md -Pattern "Phase 1 \(Prompt 04\)"
  ```
  Output: *(empty — zero matches)*

#### Step 3: Deferred Reassignment (P04 Section Only)
- **Item 1:**
  - OLD: `- consultation loop dedupe (P05)`
  - NEW: `- consultation loop dedupe (Phase 2: service layer)`
- **Item 2:**
  - OLD: `- doctor_qr business-logic extraction (P05)`
  - NEW: `- doctor_qr business-logic extraction (Phase 2: service layer)`
- **Item 3:**
  - OLD: `- request-id logging and central config (Phase 1, P05)`
  - NEW: `- request-id logging and central config (Phase 1)`
- **Step 3 Verification:**
  ```powershell
  Select-String -Path Project-docs\progress.md -Pattern "\(P05\)"
  ```
  Output: *(empty — zero matches)*

---

### `Project-docs\decisions.md`

- **BEFORE Hash:** `EAA329F8886D24AF7001D05DBECCDFD33B6B990F9434117EBF89DB2B56420877`
- **Appended Content (Step 4):**
  ```markdown
  ---

  ## D42 — Addendum: OpenAPI Parity Policy and Known Test Gaps (2 Nov 2026)

  **Canonical OpenAPI invariant:** `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`. This is the SHA256 of the in-memory `json.dumps(app.openapi(), sort_keys=True, indent=2)` encoded as UTF-8 (LF). File hashes depend on the platform newline and are not used as invariants.

  **Correction:** the P03 dump labelled the on-disk file hash as the in-memory hash. The P03 route and OpenAPI parity still holds, because the before and after files were written by the same method. The record is corrected here.

  **Known gaps in `test_routes_auth.py` (not covered yet):**
  - Invalid or expired token on protected routes (expected 401). Only the missing-token case is tested.
  - Ownership: a valid token for user A requesting user B's data (expected 403 via `verify_owner`). Not tested. Planned for Phase 1.
  - Public allowlist entries are checked for existence only, not for their decision reference at runtime.
  ```
- **AFTER Hash:** `005DB5D9F4EB6836C25CD40078D06EEF175E0DC0DE6978D8A84475B97CAFAF3E`

---

## 5. VERIFICATION (Step 5)

### Step 5a: Pytest Suite Run
```powershell
python -m pytest -q
```
Output:
```
.....................................................                    [100%]
============================== warnings summary ===============================
venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
53 passed, 2 warnings in 32.03s
```

### Step 5b: Subprocess Import Check
```powershell
$env:APP_ENV="development"; python -c "import sys; sys.path.insert(0,'src'); import agents.main; print('IMPORT_OK')"
```
Output:
```
IMPORT_OK
```

### Step 5c: Route Parity Comparison
```powershell
Compare-Object (Get-Content Project-docs\dumps\P03_routes_before.txt) (Get-Content Project-docs\dumps\P04_routes_after.txt)
```
Output: *(empty — zero diff)*

### Step 5d: Canonical Hash Re-verification
```powershell
@'
import json, hashlib, sys
sys.path.insert(0, "src")
from agents.main import app
spec_obj = app.openapi()
spec = json.dumps(spec_obj, sort_keys=True, indent=2)
ops = sum(1 for p, ops in spec_obj["paths"].items() for m in ops if m in {"get", "post", "put", "delete", "patch"})
print("OPERATIONS:", ops)
print("OPENAPI_SHA256_INMEMORY_LF:", hashlib.sha256(spec.encode("utf-8")).hexdigest())
'@ | python -
```
Output:
```
OPERATIONS: 43
OPENAPI_SHA256_INMEMORY_LF: 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1
```

### Step 5e: Final Hashes (AFTER)
```powershell
Get-FileHash -Algorithm SHA256 Project-docs\progress.md, Project-docs\decisions.md
```
Output:
```
Algorithm       Hash                                                               Path
---------       ----                                                               ----
SHA256          DF28A1DFF9447F2B561A78AC4B7DD89D4E34512EAD82C753EA651E407EF3ABCF   C:\Users\gauta\OneDrive\Desktop\MediSarthi\Project-docs\progress.md
SHA256          005DB5D9F4EB6836C25CD40078D06EEF175E0DC0DE6978D8A84475B97CAFAF3E   C:\Users\gauta\OneDrive\Desktop\MediSarthi\Project-docs\decisions.md
```

---

## 6. CHECKLIST
- [x] Step 0: Baseline tests pass (53 passed in 26.69s), BEFORE file hashes recorded.
- [x] Step 1: Canonical in-memory LF OpenAPI hash calculated: OPERATIONS 43, HASH `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
- [x] Step 2: `progress.md` header line updated from `Phase 1 (Prompt 04)` to `Prompt 04`; Step 2c verification confirmed 0 matches.
- [x] Step 3: Deferred items in P04 section reassigned to Phase 1 / Phase 2; Step 3 search for `(P05)` confirmed 0 matches.
- [x] Step 4: D42 Addendum appended to `decisions.md` documenting OpenAPI parity policy and test gaps; AFTER hash captured.
- [x] Step 5: Post-edit verification passed (53 passed in 32.03s, `IMPORT_OK`, route parity empty diff, canonical hash identical, AFTER file hashes captured).
- [x] Step 6: `Project-docs\dumps\P04b_dump.md` created with all required sections.

---

## 7. DEVIATIONS AND BLOCKERS
None

