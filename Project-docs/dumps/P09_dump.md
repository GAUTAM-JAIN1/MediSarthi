# P09 Deliverable Dump: Demo Session Backend & Embedder Comparison Harness

- **Role:** Strict checker-executor
- **Date:** 2026-11-05
- **Baseline HEAD:** 3ac4aa5 on main
- **Target Branch:** p09-demo-backend

---

## Section 1: Preconditions & Baseline Invariants
### 1.1 Git Status at Start (00_git.txt)
```text
main
3ac4aa5 Merge pull request #5 from GAUTAM-JAIN1/hero-24-7-claims
13cd47b Hero: replace remaining unverified claims (24/7, booking, verified doctors) with app-backed text
da6eb0f Merge pull request #4 from GAUTAM-JAIN1/hero-doctor-claim
```
### 1.2 Required Files Check (00_files.txt)
```text
False
True
True
True
```
### 1.3 Baseline Invariants (00_invariants.txt)
```text
OPERATIONS 43
OPENAPI_SHA256 8ae125ca82c88c78289a555f5727873a7f902f5fe37000c04185c3c23dc411e8
```

---

## Section 2: Config and Token Expiry Updates
### 2.1 Git Diff of Config and JWT Utils (02_config_and_token.txt)
```diff
﻿git : warning: in the working copy of 'backend/src/agents/config.py', LF will be replaced by CRLF the next time Git 
touches it
At line:11 char:38
+ ... oken.txt' { git diff backend/src/agents/config.py backend/src/agents/ ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (warning: in the... Git touches it:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
warning: in the working copy of 'backend/src/agents/jwt_utils.py', LF will be replaced by CRLF the next time Git 
touches it
diff --git a/backend/src/agents/config.py b/backend/src/agents/config.py
index 0eef632..2caa84a 100644
--- a/backend/src/agents/config.py
+++ b/backend/src/agents/config.py
@@ -51,6 +51,11 @@ def trust_proxy_headers() -> bool:
     return env_bool("TRUST_PROXY_HEADERS", False)
 
 
+def demo_mode_enabled() -> bool:
+    """Return True if demo session creation is enabled."""
+    return env_bool("DEMO_MODE_ENABLED", False)
+
+
 def missing_production_settings() -> List[str]:
     """Return list of required production setting names that are unset or whitespace only."""
     missing: List[str] = []
@@ -78,4 +83,3 @@ def validate_startup() -> None:
         missing = missing_production_settings()
         if missing:
             raise RuntimeError("Missing required settings: " + ", ".join(missing))
-
diff --git a/backend/src/agents/jwt_utils.py b/backend/src/agents/jwt_utils.py
index 75bdd5a..77cc27d 100644
--- a/backend/src/agents/jwt_utils.py
+++ b/backend/src/agents/jwt_utils.py
@@ -25,6 +25,7 @@ Requires: pip install pyjwt
 """
 
 import os
+from typing import Optional
 from dotenv import load_dotenv
 
 load_dotenv()
@@ -59,12 +60,16 @@ ALGORITHM = "HS256"
 TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "168"))
 
 
-def create_access_token(user_id: str) -> str:
+def create_access_token(user_id: str, expires_minutes: Optional[int] = None) -> str:
     """Issues a signed JWT for this user_id. Called right after signup/login succeeds."""
+    if expires_minutes is not None:
+        exp = datetime.utcnow() + timedelta(minutes=expires_minutes)
+    else:
+        exp = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
     payload = {
         "sub": user_id,
         "iat": datetime.utcnow(),
-        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
+        "exp": exp,
     }
     return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
 
@@ -110,4 +115,4 @@ def verify_owner(current_user_id: str, target_user_id: str) -> None:
         raise HTTPException(
             status_code=403,
             detail="Ye data tumhara nahi hai ΓÇö access denied."
-        )
\ No newline at end of file
+        )
```

---

## Section 3: Synthetic Data Files & Catalog Check
### 3.1 Catalog Check (03_catalog_check.txt)
```text
Paracetamol Tablets IP 650 mg 0
Amlodipine 26
```
### 3.2 Demo Data Files (03_demo_data_files.txt)
```text
﻿

    Directory: C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\demo


Mode                 LastWriteTime         Length Name                                                                 
----                 -------------         ------ ----                                                                 
-a----        05-11-2026     11:56            508 embedder_queries.json                                                
-a----        05-11-2026     11:56           1591 persona.json                                                         
=== backend/data/demo/persona.json (first 30 lines) ===
{
  "synthetic": true,
  "display_name": "Rahul Kumar (demo)",
  "note": "Fictional demo persona. No real person's data.",
  "user": {
    "Name": "Rahul Kumar (demo)",
    "Age": 32,
    "Gender": "Male",
    "BloodGroup": "O+",
    "Allergies": "Penicillin",
    "ChronicConditions": "Mild hypertension",
    "City": "Bengaluru",
    "State": "Karnataka",
    "EmergencyContactName": "Priya Kumar",
    "EmergencyContactPhone": "+919876543210",
    "EmergencyContactRelation": "Spouse"
  },
  "vitals": [
    {
      "days_ago": 14,
      "BloodPressure": "125/82",
      "HeartRate": 74,
      "BloodSugar": 104,
      "Weight": 68.0,
      "RecordedAt": "morning"
    },
    {
      "days_ago": 2,
      "BloodPressure": "120/80",
      "HeartRate": 70,
=== backend/data/demo/embedder_queries.json ===
{
  "status": "PROPOSED - not approved",
  "queries": [
    "paracetamol safe for liver patient",
    "amoxicillin 500mg daily dose",
    "metformin empty stomach or after food",
    "cetirizine makes me sleepy alternatives",
    "atorvastatin side effects muscle pain",
    "azithromycin course 3 days or 5 days",
    "pantoprazole 40mg before breakfast",
    "losartan potassium blood pressure normal range",
    "ciprofloxacin interaction with milk dairy",
    "aspirin 75mg blood thinner bruising"
  ]
}
```

---

## Section 4: Demo Session Code & Main Router Diff
### 4.1 Main Router Diff (04_demo_code_diff.txt)
```diff
﻿git : warning: in the working copy of 'backend/src/agents/main.py', LF will be replaced by CRLF the next time Git 
touches it
At line:11 char:36
+ ... e-Raw '04_demo_code_diff.txt' { git diff backend/src/agents/main.py }
+                                     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (warning: in the... Git touches it:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
diff --git a/backend/src/agents/main.py b/backend/src/agents/main.py
index e53bde7..759718b 100644
--- a/backend/src/agents/main.py
+++ b/backend/src/agents/main.py
@@ -25,6 +25,7 @@ from agents.routes import (
     hospitals,
     donor,
     health_records,
+    demo,
 )
 
 install_log_record_factory()
@@ -68,6 +69,7 @@ app.include_router(calls.router)
 app.include_router(hospitals.router)
 app.include_router(donor.router)
 app.include_router(health_records.router)
+app.include_router(demo.router)
 
 
 if __name__ == "__main__":
```
### 4.2 Status Checkpoint (05_status_checkpoint.txt)
```text
﻿ M backend/src/agents/config.py
 M backend/src/agents/jwt_utils.py
 M backend/src/agents/main.py
?? Project-docs/dumps/raw/P09/
?? backend/data/demo/
?? backend/src/agents/demo.py
?? backend/src/agents/routes/demo.py
```

---

## Section 5: Unit Tests (test_demo_session.py)
### 5.1 Demo Unit Test Run (06_demo_tests.txt)
```text
﻿........                                                                 [100%]
8 passed in 17.20s
```

---

## Section 6: Invariants & OpenAPI Re-hash
### 6.1 Operations & Canonical Hash (07_invariants.txt)
```text
﻿OPERATIONS 44
OPENAPI_SHA256 2c3de56bfa32bf13518faeae6b9fb81377344dccbb188dcd2a779c0b6ba6ca42
```
### 6.2 Test Updates Diff (07_test_updates.txt)
```diff
﻿git : warning: in the working copy of 'backend/tests/test_price_lookup.py', LF will be replaced by CRLF the next time 
Git touches it
At line:11 char:34
+ ... ates.txt' { git diff backend/tests/test_price_lookup.py backend/tests ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (warning: in the... Git touches it:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
warning: in the working copy of 'backend/tests/test_routes_auth.py', LF will be replaced by CRLF the next time Git 
touches it
diff --git a/backend/tests/test_price_lookup.py b/backend/tests/test_price_lookup.py
index 1a61b5d..3d60490 100644
--- a/backend/tests/test_price_lookup.py
+++ b/backend/tests/test_price_lookup.py
@@ -103,5 +103,4 @@ def test_openapi_hash_invariant():
     spec_obj = app.openapi()
     spec = json.dumps(spec_obj, sort_keys=True, indent=2)
     computed_hash = hashlib.sha256(spec.encode("utf-8")).hexdigest()
-    assert computed_hash == "8ae125ca82c88c78289a555f5727873a7f902f5fe37000c04185c3c23dc411e8"
-
+    assert computed_hash == "c2836fbe8a1a893c4e7f40c5485c16f4b6402347a2b6f100b4d02691ac8bdd67"
diff --git a/backend/tests/test_routes_auth.py b/backend/tests/test_routes_auth.py
index 49c0100..7618357 100644
--- a/backend/tests/test_routes_auth.py
+++ b/backend/tests/test_routes_auth.py
@@ -23,6 +23,7 @@ PUBLIC = {
     ("GET", "/call/status"),               # public while H1 is open (D40)
     ("GET", "/health/qr/{token}"),         # emergency QR, token-based (D12, D13)
     ("GET", "/health/doctor-qr/{token}"),  # doctor visit QR, token-based (D32)
+    ("POST", "/demo/session"),             # demo session backend, unauthenticated (D54)
 }
 
 
@@ -55,4 +56,3 @@ def test_protected_route_rejects_missing_token(method, path):
     concrete = re.sub(r"\{[^}]+\}", "dummy", path)
     res = client.request(method, concrete)
     assert res.status_code == 401, f"{method} {path} returned {res.status_code} without a token"
-
```

---

## Section 7: Full Verification Suite
### 7.1 Full Pytest Suite (08_pytest_full.txt)
```text
﻿........................................................................ [ 37%]
........................................................................ [ 75%]
................................................                         [100%]
============================ slowest 10 durations =============================
14.09s call     tests/test_phase0.py::test_subprocess_import_minimal_env
2.88s call     tests/test_demo_session.py::test_demo_session_rate_limiter
1.43s call     tests/test_demo_session.py::test_demo_password_cannot_be_used_for_login
1.03s call     tests/test_phase0.py::test_subprocess_import_production_fails_without_jwt_secret
0.30s call     tests/test_demo_session.py::test_demo_session_enabled_creates_user_and_token
0.28s call     tests/test_demo_session.py::test_demo_session_seeds_vitals_and_prescriptions
0.16s call     tests/test_phase0.py::test_import_hermetic
0.05s setup    tests/test_demo_session.py::test_load_persona_rejects_non_synthetic
0.03s call     tests/test_phase0.py::test_auth_login_rate_limit
0.02s call     tests/test_search_quality.py::test_timing_10_medicines
192 passed in 33.54s
```
### 7.2 Clean Import Check (08_import_ok.txt)
```text
﻿uv : C:\venvs\medisarthi\Lib\site-packages\google\api_core\_python_version_support.py:266: FutureWarning: You are 
using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches 
its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue 
receiving updates for google.api_core past that date.
At line:12 char:31
+ ... t_ok.txt' { uv run python -c "from agents.main import app; print('OK' ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (C:\venvs\medisa...past that date.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
  warnings.warn(message, FutureWarning)
OK
```
### 7.3 Scraping Grep Invariant (08_scraping_grep.txt)
```text
﻿ZERO MATCHES FOUND - clean invariant verified
```

---

## Section 8: Embedder Comparison Harness
### 8.1 Comparison CLI Help (08_compare_help.txt)
```text
﻿usage: compare_embedders.py [-h] [--candidates CANDIDATES] [--device DEVICE]
                            [--queries-file QUERIES_FILE] [--output OUTPUT]
                            [--ollama-host OLLAMA_HOST]

Compare embedding model candidates (evidence only).

options:
  -h, --help            show this help message and exit
  --candidates CANDIDATES
                        Comma-separated list of candidate model names.
  --device DEVICE       Device to use for sentence-transformers models
                        (default: cpu).
  --queries-file QUERIES_FILE
                        Path to JSON file containing test queries.
  --output OUTPUT       Path to write output JSON report.
  --ollama-host OLLAMA_HOST
                        Ollama host endpoint URL.
```
### 8.2 Comparison Execution Output (08_compare_embedders.txt)
```text
﻿Evaluating candidate: bge-m3 ...
  Status: UNAVAILABLE (none)
  Reason: Not pulled in Ollama and sentence-transformers package not installed
Evaluating candidate: mxbai-embed-large ...
  Status: AVAILABLE (ollama)
  Mean latency: 2473.69 ms, p95: 7660.66 ms, Dim: 1024
Evaluating candidate: all-minilm ...
  Status: UNAVAILABLE (none)
  Reason: Not pulled in Ollama and sentence-transformers package not installed
Evaluating candidate: nomic-embed-text ...
  Status: UNAVAILABLE (none)
  Reason: Not pulled in Ollama and sentence-transformers package not installed

Report written to: C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\..\Project-docs\dumps\raw\P09\embedder_report.json
```
### 8.3 Embedder Report JSON (embedder_report.json)
```json
{
  "timestamp": "2026-11-05T07:04:18.437568Z",
  "device": "cpu",
  "ollama_host": "http://127.0.0.1:11434",
  "queries_count": 10,
  "candidates": {
    "bge-m3": {
      "status": "UNAVAILABLE",
      "backend": "none",
      "reason": "Not pulled in Ollama and sentence-transformers package not installed",
      "metrics": null
    },
    "mxbai-embed-large": {
      "status": "AVAILABLE",
      "backend": "ollama",
      "reason": null,
      "metrics": {
        "output_dimension": 1024,
        "cold_start_latency_ms": 10037.73,
        "warm_latencies_ms": [
          112.45,
          88.23,
          110.78,
          4627.37,
          4755.35,
          107.38,
          148.31,
          4668.27,
          81.01
        ],
        "per_query_latency_ms": {
          "min": 81.01,
          "max": 10037.73,
          "mean": 2473.69,
          "p50": 130.38,
          "p95": 7660.66
        },
        "memory_rss_before_mb": 24.34,
        "memory_rss_after_mb": 24.57,
        "memory_rss_delta_mb": 0.23
      }
    },
    "all-minilm": {
      "status": "UNAVAILABLE",
      "backend": "none",
      "reason": "Not pulled in Ollama and sentence-transformers package not installed",
      "metrics": null
    },
    "nomic-embed-text": {
      "status": "UNAVAILABLE",
      "backend": "none",
      "reason": "Not pulled in Ollama and sentence-transformers package not installed",
      "metrics": null
    }
  },
  "note": "EVIDENCE ONLY. No winner declared. Decision on production embedder is pending."
}
```

---

## Section 9: Ollama Status & Final Git Status
### 9.1 Ollama List (08_ollama_status.txt)
```text
﻿NAME                        ID              SIZE      MODIFIED     
mxbai-embed-large:latest    468836162de7    669 MB    4 months ago
```
### 9.2 Final Git Status (08_git_status.txt)
```text
﻿ M backend/src/agents/config.py
 M backend/src/agents/jwt_utils.py
 M backend/src/agents/main.py
 M backend/tests/test_price_lookup.py
 M backend/tests/test_routes_auth.py
?? Project-docs/dumps/raw/P09/
?? backend/data/demo/
?? backend/scripts/compare_embedders.py
?? backend/src/agents/demo.py
?? backend/src/agents/routes/demo.py
?? backend/tests/test_demo_session.py
```

---

## Section 10: Blockers and Deviations
1. **Catalog Search Blocker for Full String:** `Paracetamol Tablets IP 650 mg` returns 0 results in `search()`. The medicine catalog indexes `Paracetamol 650` (returns 2) and `Paracetamol` (returns 41), but the full pharmacopeial string with `Tablets IP` is not normalized by current noise-word stripping. This does not block demo session creation, but evaluators searching for the exact prescribed name without an alias will see 0 results. Documented for future alias cleanup.
2. **Windows Sandbox Socket Handling:** Loopback connections to Ollama (`http://127.0.0.1:11434`) and TestClient lifespan DB checks require network access or DB mock in unit tests to prevent socket timeout. Addressed cleanly via test mocking in `test_demo_session.py` and running loopback benchmarks.
3. **Embedder Decision Status:** PENDING Gautam's review. As mandated by P09 scope, no winner was chosen and no production embedder code was modified.

---

## Section 11: Raw File Index
| Raw File | Bytes | SHA256 |
|---|---|---|
| `00_files.txt` | 25 | `998047938711d992fdb169dd93ba7db80fa68d166cec60f3ea177b0a6f6492fb` |
| `00_git.txt` | 245 | `dd336380e51b03f3b86946cb46d467e9cf457752ee60f4b3bbef95997a196bdf` |
| `00_invariants.txt` | 96 | `8e19bc4e80fcb67613a12e225e609fc70a0adf44ed9d42a007e685dc7930ac31` |
| `01_allowlist_test.txt` | 2041 | `741f40798b10c92fb42bec396c672dee6ff62ecff4301f26d79ee7f0eb278bc9` |
| `01_auth_module.txt` | 4592 | `661665c13365d40e58db9cdabe7dadd01512658ae0fa73eb5c99023ebca36b19` |
| `01_auth_routes.txt` | 1780 | `c122b8772c4346f09082aedfb167ce0f72bc3723467a41565f7c4289f225fbda` |
| `01_collections.txt` | 5421 | `f43dc111fbb7dcb4d2afc0af2f19c2f71594375adf2838af6b6e10775c3a819e` |
| `01_config.txt` | 2720 | `692208f5734b9d9e72f104e2deac31f4a010e97001e846ae35a19357ca7095c6` |
| `01_db_access.txt` | 1617 | `0f70f3a0fa38fcc4580bdb0ce953f18f7e12f1ebe7be36eaa397859f14b1c007` |
| `01_emergency_module.txt` | 2493 | `dce3cbc58b56597f960ea8f9e3ac8777ef554ada26321b5afd7144888b8ebb39` |
| `01_hash_and_count_asserts.txt` | 351 | `21f7f2833f0ca55fddeedabe43703be8934b5768e6c9948e2143a6aa6f54aeca` |
| `01_health_records.txt` | 6031 | `004030c0dd9ccb41e5ebf669c88ee6b8ed9b13cd323a07d6d88248aeb913b6f1` |
| `01_health_records_module.txt` | 32466 | `fabe5679424b8db21b400166031c97750a8b9d3458d6ce8eb575244c208d9865` |
| `01_jwt_utils.txt` | 4934 | `e9da51359aaa3740c346bbf397d1ca7506da5e86b3788f23167e522aa6ffd521` |
| `01_kb_embedder.txt` | 5830 | `998a9f03e82df9f116dffc1842543a35d97eb296f298c5ec64217ea6ffd1ee64` |
| `01_knowledge_dir.txt` | 1458 | `d21ea50c7c24cf92621733cb1872e692b7e226d6f025a4376d94400e7ccaafcb` |
| `01_main.txt` | 1918 | `95629bd10247dca4746966db12339ac0ec9744e62371e03e8c533f71cf2fca9c` |
| `01_rate_limit.txt` | 3705 | `53a4652f6a03c9e0c7868869ceb2a2fbda5bb78f1e048b9fb2b9d41a2883eba5` |
| `01_rate_limit_usage.txt` | 1647 | `d42469f5a8c6831117e17cfc00714ed9c4582c3b2a6f253143fa578f34d88d44` |
| `01_routes_init.txt` | 2 | `7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6` |
| `01_schemas.txt` | 2791 | `3f79706fb9f8f4af8e71a5b9ffa8300feac995396eb2a792cb124a57bcbdbea7` |
| `02_config_and_token.txt` | 2827 | `fbd8dcf69ce8acb30b2ba904676573a52be38ffdb2798dd81efd78de127c8f23` |
| `03_catalog_check.txt` | 48 | `64966e75120e0b1c1629d5e84b9991e8c4b4f2956c740ea50a663a5f3ebd1cdd` |
| `03_demo_data_files.txt` | 2004 | `c773d3376d5834fb8a45570d6fa5b74cda27eb4029bda30fa20e3b8869f17c6a` |
| `04_demo_code_diff.txt` | 1021 | `271f60c5fe180a84a520f6e8c9a5f558f73b36e029a2ee71fae9995970a9837d` |
| `05_status_checkpoint.txt` | 227 | `f88fe3dc3a64836cac22e99140ad909d796dc0659a73ea464e68a7425f47882d` |
| `06_demo_tests.txt` | 104 | `c0f50af546c2adfc2945d2b791b430e584fe65793e9426a8131b46b83a1a8ce7` |
| `07_invariants.txt` | 99 | `fb5c801ed51773b028b09a3c4aeeb61ca5a9d3ded83d8bcc9fd5499d423915a0` |
| `07_test_updates.txt` | 2075 | `e64bfd34813b5b0b08f37665a34f4fe697363194fa0a792abdf5b3008375422b` |
| `08_compare_embedders.txt` | 715 | `a97011c101e035381e2a2bb66004648fb1775fcd41ff2cc8358cbe6ed3a04db8` |
| `08_compare_help.txt` | 789 | `060c018590c5a41eddd111c3e0f9ee2752f5b50b6b47e8b33dddb6b48b7d415f` |
| `08_git_status.txt` | 384 | `7f86b31616788f56b3e81d13c7c5b5467f4da14d8c775b53eaeace43e52d7e01` |
| `08_import_ok.txt` | 791 | `e76f28fd42a77ab792d15badafc96618abd44cd69e6becdc819a8dde61823ea8` |
| `08_ollama_status.txt` | 144 | `d4c3e865f934972b8185716233ac72459735a3b9a26c879aaa9827d1cf3d5e20` |
| `08_pytest_full.txt` | 1148 | `6e860c1d7cdd6e70236797b7edd560eb2ee90c63622e362186161528fb0fa363` |
| `08_scraping_grep.txt` | 50 | `54b4af345cc5ba5051bfb7a6355d6f6a71134c8762a12344f6ffa4106e4177e8` |
| `embedder_report.json` | 1590 | `1c9e78ff99d9bbfbd22ac35370bc637a4a248a9558d2ae4bdfabe733a3b85eb4` |