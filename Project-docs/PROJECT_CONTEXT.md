# PROJECT_CONTEXT.md — Canonical Technical Reference

**This is the single source of truth for MediSarthi's exact technical state** — exact function signatures, endpoint tables, per-file detail. It supersedes any partial explanation of the same facts in `README.md`, `CLAUDE.md`, or `progress.md` — those files intentionally keep things brief and point back here for full detail. If anything ever appears to conflict between files, trust this one and treat the others as needing a fix.

**New companion doc: `architecture.md`** (added alongside this file, same session as D32) — a bird's-eye system view (layers, data flow, request lifecycle, design principles) for onboarding/orientation. This file (`PROJECT_CONTEXT.md`) stays the exhaustive reference; `architecture.md` is the "how does this fit together" read that doesn't require re-deriving the shape of the system from an endpoint table.

Read `CLAUDE.md` first for orientation and rules, then `architecture.md` for the system shape, then this file for the actual technical state, then `progress.md` for status, then `decisions.md` for the reasoning behind non-obvious choices.

---

## 1. Repos & Local Paths

- **New public repo (current source of truth for what's pushed):** [github.com/GAUTAM-JAIN1/MediSarthi](https://github.com/GAUTAM-JAIN1/MediSarthi) — monorepo (backend + frontend together), public, secrets cleaned before push.
- Original repos this was forked/reworked from: backend `https://github.com/Tanishq-garg-2007/G.A.N.G.U`, frontend `https://github.com/Tanishq-garg-2007/G.A.N.G.U-Frontend` (friend's repos, kept for historical reference only — MediSarthi is the actively developed one now).
- Full backend path: `C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\` (local Windows, OneDrive-synced — verify exact casing against the actual folder if a command fails on a case-sensitive path assumption).
- All Python sources: `backend\src\agents\`.
- Frontend project root: `frontend\frontend\` (**doubled folder name** — the outer `frontend/` only contains `package-lock.json`). Always verify `package.json` is present before running `npm` commands.

## 2. Backend Architecture

### 2.1 Entry point — `src/agents/main.py`

FastAPI app running on port 8080. All endpoints and their current wiring status:

| Method | Path | Handler function | CrewAI class / module used | `user_id` wiring |
|---|---|---|---|---|
| GET | `/` | `health_check` | — | n/a |
| POST | `/auth/signup` | `signup` | — | n/a (creates the user_id) |
| POST | `/auth/login` | `login` | — | n/a (returns the user_id) |
| POST | `/consultation/speech` | `speech_consultation` | `SpeechCrew` | ✅ `user_id: str = Form(...)`, passed as `SpeechCrew().crew(user_id=user_id)` |
| POST | `/consultation/document` | `document_consultation` | `FileCrew` | ✅ same pattern |
| POST | `/medicine/compare` | `compare_prices` | — (calls `buying_agent.run_comparison`) | n/a. `buying_agent.py` rewritten extraction-only, parallel 2-site (1mg + Apollo) — see §2.9 + `decisions.md` D21/D22. Wired to `Compare.jsx`, **live-tested and confirmed working.** |
| POST | `/call/schedule` | `schedule_call` | — (calls `Calling.start_call` in thread) | n/a |
| POST | `/hospitals/nearby` | `find_hospitals` | `Nearbyhospitals` | ✅ `LocationRequest{user_id, city?, state?, country, limit}`. Each hospital object can now include a `phone` field (string or `null`) — see §2.2 for the format-lock + free-phone-via-extratags note. |
| POST | `/general-query` | `general_health_query` | `general_que` | ✅ `user_id: str = Form(...)` |
| POST | `/donor/register` | `donor_register` | `donor.py` | ✅ `DonorRegisterRequest{user_id, ...}` |
| GET | `/donor/{user_id}` | `donor_profile` | `donor.py` | ✅ path param |
| POST | `/donor/{user_id}/record-donation` | `donor_record_donation` | `donor.py` | ✅ path param |
| POST | `/donor/{user_id}/availability` | `donor_availability` | `donor.py` | ✅ path param + query bool |
| POST | `/donor/request/create` | `donor_request_create` | `donor.py` | ✅ `requester_user_id` |
| POST | `/donor/request/find-donors` | `donor_find_matching` | `donor.py` | n/a (matches by blood group/city/state) |
| POST | `/health/vital` | `health_add_vital` | `health_records.py` | ✅ `VitalRequest{user_id, ...}` |
| GET | `/health/vitals/{user_id}` | `health_get_vitals` | `health_records.py` | ✅ path param |
| POST | `/health/prescription` | `health_add_prescription` | `health_records.py` | ✅ `PrescriptionRequest{user_id, ...}` |
| GET | `/health/prescriptions/{user_id}` | `health_get_prescriptions` | `health_records.py` | ✅ path param |
| GET | `/health/timeline/{user_id}` | `health_get_timeline` | `health_records.py` | ✅ path param. Returns `{"timeline": [{_id, type, date, data: {...}}], "count": n}` |
| POST | `/health/emergency-profile` | `health_save_emergency_profile` | `health_records.py` | ✅ `EmergencyProfileRequest{user_id, ...}` |
| GET | `/health/emergency-profile/{user_id}` | `health_get_emergency_profile` | `health_records.py` | ✅ path param. Returns the profile **flat** (not wrapped), includes `qr_token` if one exists. 404 if no profile saved yet (normal on first visit). |
| POST | `/health/generate-qr/{user_id}` | `health_generate_qr` | `health_records.py` | ✅ path param. Returns `{"token": ..., "qr_url": "/health/qr/{token}"}` |
| GET | `/health/qr/{token}` | `health_qr_public` | `health_records.py` | n/a (public, no auth) — returns the profile **flat**, 404 if token invalid/missing |
| POST | `/lab/analyse` | `analyse_lab_report` (name approximate) | `LabReportCrew` | ✅ live-tested, confirmed working. Also `POST /lab/save` (explicit save), `GET /lab/analyses/{user_id}` (saved-report history — now consumed by `LabReport.jsx`), and new `GET /health/trends/{user_id}` (per-test trend series, Health Trends feature, `decisions.md` D23). |
| DELETE | `/lab/analyses/{user_id}/{analysis_id}` | `delete_lab_analysis` | `health_records.py` | ✅ live-tested (D30). Scoped to `user_id` — hard delete, no soft-delete/undo. 404 if already deleted/invalid. |
| GET | `/health/trends-annotated/{user_id}` | `get_health_trends_annotated` | `health_records.py` (`get_annotated_trends`) | ✅ live-tested (D29 phase 1). Same shape as `/health/trends/{user_id}` plus an `annotations` list per trend (medicine name + start date, via `medicine_test_map.py`). |
| POST | `/medicine/interactions` | `check_medicine_interaction` (name approximate) | `MedicineInteractionCrew` | ✅ live-tested, confirmed working. |
| POST | `/triage/symptoms` | `symptom_triage` (name approximate) | `SymptomTriageCrew` | ✅ live-tested, confirmed working. |
| POST | `/medicine/effectiveness` | `check_medicine_effectiveness` | `MedicineEffectivenessCrew` | ✅ live-tested (D31, Medicine Effectiveness phase 2). On-demand per annotation, not pre-computed — takes `points` the frontend already fetched from `/health/trends-annotated/{user_id}`, no extra DB read. |
| POST | `/health/doctor-qr/{user_id}` | `health_generate_doctor_qr` | `ClinicalSummaryCrew` | ⚠️ **NEW this session (D32), not yet live-tested.** Gathers lab reports + annotated trends + prescriptions, runs `ClinicalSummaryCrew` once, stores the result as a snapshot behind a fresh 24h token. Returns `{token, qr_url, expires_in_hours}`. |
| GET | `/health/doctor-qr/{token}` | `health_get_doctor_qr` | `health_records.py` (`get_doctor_qr_snapshot`) | ⚠️ **NEW this session (D32), not yet live-tested.** Public, no auth — returns the cached snapshot, 404 if token invalid/expired. |

**Update:** the 3 rows above were previously flagged ⚠️ as unverified reconstructions. The user has since confirmed all 3 agents are fully live-tested and working end-to-end. The exact real paths (`/lab/analyse`, `/medicine/interactions`, `/triage/symptoms`) were confirmed against actual `main.py` code in an earlier session (see `progress.md`) — only the exact Python handler function *names* above remain approximate (cosmetic detail, doesn't affect behavior).

All endpoints in this table are confirmed working. No broken endpoints remain.

Imports at the top of `main.py` (current, post-D32):
```python
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from agents.crew import (
    SpeechCrew, FileCrew, Nearbyhospitals, general_que,
    LabReportCrew, MedicineInteractionCrew, SymptomTriageCrew,
    MedicineEffectivenessCrew, ClinicalSummaryCrew,
)
from agents.auth import signup_user, login_user, get_user_by_id
from agents.health_records import (
    add_vital, get_vitals, add_prescription, get_prescriptions,
    get_full_timeline, save_emergency_profile, get_emergency_profile,
    get_emergency_profile_public, generate_qr_token,
    save_prescription_analysis, get_prescription_analyses,
    get_prescription_analysis_by_id,
    save_lab_report_analysis, get_lab_report_analyses,
    get_test_trends, get_annotated_trends,
    delete_lab_report_analysis,
    create_doctor_qr_token, get_doctor_qr_snapshot,
)
from agents.donor import (
    register_donor, get_donor_by_user_id, record_donation,
    toggle_availability, create_donation_request, find_matching_donors
)
# face_recognize import was REMOVED entirely
```

### 2.2 CrewAI logic — `src/agents/crew.py`

**✅ RESOLVED — LLM provider confirmed (was previously flagged ⚠️ needing re-verification):** `crew.py`'s own migration comment confirms all 7 crews were moved off `gemini/gemini-2.5-flash` to `groq/llama-3.3-70b-versatile` project-wide (Gemini's free-tier daily request cap made iterative testing unworkable) — not just the hospital-finder path as an earlier session doc speculated. Every `Agent(...)`'s `llm=LLM(...)` call across all 7 crews uses `groq/llama-3.3-70b-versatile`. `GEMINI_API_KEY` is still loaded at the top of `crew.py` in case anything else needs it, but no `LLM()` call in this file uses it anymore. `GROQ_API_KEY` must exist in `backend/.env` for any crew to run.

Four crew classes, each `@CrewBase`-decorated. All four `.crew()` methods take `user_id: str`:

```python
from agents.auth import get_user_knowledge_profile  # NOT face_recognize anymore

@crew
def crew(self, user_id: str) -> Crew:
    user_data, profile_file = get_user_knowledge_profile(user_id)
    # ... sets up storage_dir, knowledge_source, returns Crew(...)
```

Classes: `SpeechCrew`, `FileCrew`, `Nearbyhospitals`, `general_que`. Note inconsistent casing on the last two — this is pre-existing, do not rename without explicit instruction.

**3 new crew classes added (AGENTS audit session — see `decisions.md` D15):** `LabReportCrew`, `MedicineInteractionCrew`, `SymptomTriageCrew`. Each follows the same `@CrewBase` + `@crew` pattern and takes `user_id: str` on `.crew()`, consistent with the 4 originals. Backed by 6 new YAML configs in `config/`: `lab_report_agent.yaml`, `lab_report_task.yaml`, `medicine_interaction_agent.yaml`, `medicine_interaction_task.yaml`, `symptom_triage_agent.yaml`, `symptom_triage_task.yaml`.

**2 more crew classes added since (D29 phase 2, D32):** `MedicineEffectivenessCrew` (direction+pace verdict on a medicine's effect on a tracked test, RAG-grounded against `test_direction_reference.txt` + `medicine_response_timelines.txt`) and `ClinicalSummaryCrew` (Doctor Visit QR feature — terse clinical-register summary for a doctor, RAG-grounded against `lab_reference_ranges.txt` + `test_direction_reference.txt`). Same `@CrewBase` pattern, backed by `config/medicine_effectiveness_agent.yaml`/`_task.yaml` and `config/clinical_summary_agent.yaml`/`_task.yaml` respectively.

**Full current agent inventory (9 crew classes now):** `doctor`, `Medical_Data_Extractor`, `care_coordinator`, `prescription_analyst`, `hospital_finder`, `hospital_reporter`, `home_health_assistant`, `lab_report_analyst`, `interaction_checker`, `triage_nurse`, `effectiveness_analyst`, `clinical_summarizer`.

**Hospital list output format — locked (see `decisions.md` D19):** `config/hospital_task.yaml`'s `reporting_task` no longer leaves markdown styling up to the LLM. It now mandates exactly: `* **Hospital Name**: Address | Phone: phone-number-or-Not-available`, one hospital per line, bold-only name, no backticks/italics, no extra commentary before/after the list. This was a root-cause fix for a recurring bug where different LLM providers (Gemini bold vs Groq backtick) formatted the list differently and broke `main.py`'s `parse_hospital_list()`. The parser was also rewritten to handle this locked format while staying backward-compatible with the older Gemini/Groq styles.

**Hospital phone numbers — free, via Nominatim `extratags=1` (see `decisions.md` D20):** `tools/custom_tool.py`'s `MyCustomTool` now passes `extratags=1` to the Nominatim `/search` API call, which returns each result's OSM tags (`phone`, `contact:phone`, `contact:mobile`) when present, in the same request — no extra API call, no cost, no new credentials. Coverage is partial since not every OSM hospital entry has a phone tag; those come back `Phone: Not available` and `parse_hospital_list()` converts that string to `null` for the frontend.

### 2.3 `src/agents/auth.py`

Built from scratch. Replaces `face_recognize.py` as the identification mechanism.

**MongoDB setup:** Reuses `db_connect.py`'s existing `get_database()` function directly — same Atlas cluster, same `medical_db` database. Collection: `Members`. No second Mongo target.

```python
from agents.db_connect import get_database
COLLECTION_NAME = "Members"
```

Functions:
- `_get_collection()` — returns the `Members` collection via `get_database()`.
- `_hash_password(plain) -> bytes` / `_verify_password(plain, hashed) -> bool` — bcrypt wrappers.
- `build_user_profile(doc) -> dict` — maps a Mongo doc to the stable shape:
```python
  {"ID": str, "Name": ..., "Age": ..., "Gender": ..., "Allergies": ..., "City": ..., "State": ..., "Email": ...}
```
  This shape deliberately matches what `face_recognize.py`'s old `user_data` dict provided (see `decisions.md` D10).
- `signup_user(name, age, gender, allergies, city, state, email, password) -> dict` — raises `ValueError` if email already registered.
- `login_user(email, password) -> dict` — raises `ValueError` on missing account or wrong password.
- `get_user_by_id(user_id) -> dict` — looks up by Mongo `ObjectId` string.
- `get_user_knowledge_profile(user_id) -> (user_data, profile_file_path)` — direct replacement for the old zero-arg face-scan function. Resolves `project_root` via `Path(__file__).resolve().parents[2]` (= `backend/`), writes `knowledge/user_<id>/profile.txt`. Returns same 2-tuple shape `crew.py` expects.

### 2.4 `src/agents/health_records.py` (NEW — now complete and verified)

MongoDB collections used (all in `medical_db`, same database as everything else): `health_vitals`, `health_prescriptions`, `emergency_profiles`, `emergency_qr_tokens`, `prescription_analyses`, `lab_report_analyses`, and — **new as of D32** — `doctor_qr_tokens`.

Functions:
- `add_vital(user_id, vital_type, value, unit, notes="", bp_systolic=None, bp_diastolic=None, blood_sugar=None, weight=None) -> str` — stores both a generic `vital_type/value/unit` shape AND the granular BP/sugar/weight fields the frontend's "Add Vital" form actually sends, in one document.
- `get_vitals(user_id, vital_type=None, limit=30) -> list`
- `add_prescription(user_id, medicines: list, symptoms="", doctor_notes="", source="manual") -> str`
- `get_prescriptions(user_id, limit=20) -> list`
- `get_full_timeline(user_id, limit=50) -> list` — merges vitals + prescriptions into one list, each item shaped `{_id, type, date, data: {...}}`. `type` is `"vital"` or `"prescription"` (renamed from an earlier `record_type` key that didn't match what `HealthInfo.jsx` reads). `data` is nested (`data.bp_systolic`, `data.summary`, etc.) to match the frontend exactly.
- `save_emergency_profile(user_id, name, blood_group, allergies, critical_conditions, emergency_contact_name, emergency_contact_phone, medicines) -> None` — upsert. `allergies`, `critical_conditions`, `medicines` are **plain strings**, not lists (matches the frontend's single-text-input UI; see `decisions.md` D12).
- `get_emergency_profile(user_id) -> dict | None` — also looks up `emergency_qr_tokens` and merges in `qr_token` if one exists, so the frontend can restore a previously generated QR after a page reload.
- `get_emergency_profile_public(token) -> dict | None` — public lookup, no auth, used by `/health/qr/{token}`.
- `generate_qr_token(user_id) -> str` — `secrets.token_urlsafe(16)`, upserted into `emergency_qr_tokens`; regenerating replaces the previous token (old QR codes become invalid).
- `save_lab_report_analysis(user_id, ..., report_date="") -> str` — persists a `LabReportCrew` run, verified/live-tested (D27, D28). `date` is resolved via `_resolve_report_date()` (below), not save-time.
- `get_lab_report_analyses(user_id, limit=20) -> list` — fetch a user's past lab report analyses.
- `get_lab_report_analysis_by_id(user_id, analysis_id) -> dict | None`
- `delete_lab_report_analysis(user_id, analysis_id) -> bool` **(D30)** — scoped to `user_id`, hard delete, no soft-delete/undo. Frontend confirmation ("type DELETE") happens before this is ever called.
- `_resolve_report_date(report_date) -> str` **(D28)** — resolves a saved lab report's chronological `date` from the LLM-extracted `report_date` (ISO `YYYY-MM-DD`) if parseable, else falls back to save-time (`utcnow()`).
- `get_test_trends(user_id, min_points=2) -> list` — per-test chronological series across saved reports, for the Health Trends chart. Sorted so currently-abnormal tests come first.
- `get_annotated_trends(user_id, min_points=2) -> list` **(D29 phase 1)** — same shape as `get_test_trends()` plus an `annotations` list per trend (`{medicine_name, start_date}`), joined from saved prescriptions via `medicine_test_map.resolve_tracked_tests()`. Deliberately a separate function so `get_test_trends()`/`/health/trends/{user_id}` stay unchanged.
- `save_prescription_analysis(...)` / `get_prescription_analyses(...)` / `get_prescription_analysis_by_id(...)` — same permission-gated pattern as lab reports, for `SpeechCrew`/`FileCrew` consultation results.
- **`create_doctor_qr_token(user_id, snapshot, expiry_hours=24) -> str`** **(NEW, D32)** — stores a pre-built snapshot (clinical summary + lab history + trends + prescriptions, built in `main.py` to avoid a circular import with `crew.py`) behind a fresh token in `doctor_qr_tokens`. Regenerating does NOT replace the previous token (unlike `generate_qr_token`).
- **`get_doctor_qr_snapshot(token) -> dict | None`** **(NEW, D32)** — public lookup, checks `expires_at` and returns `None` if expired (record not deleted, just stops resolving — no cleanup job exists yet, see `decisions.md` D32 "Known open items").

### 2.5 `src/agents/donor.py` (NEW — complete and verified)

Functions backing the 6 donor endpoints in §2.1: `register_donor`, `get_donor_by_user_id`, `record_donation`, `toggle_availability`, `create_donation_request`, `find_matching_donors`. Donor matching is by blood group + city + state. Donation-count tracking and availability toggle confirmed working live.

### 2.6 `src/agents/db_connect.py` (unchanged, reused by auth.py / health_records.py / donor.py)

```python
from pymongo import MongoClient
MONGO_URI = "mongodb+srv://<user>:<password>@cluster0.441o7q2.mongodb.net/"

def get_database():
    client = MongoClient(MONGO_URI)
    db = client["medical_db"]
    return db
```

Note: **Resolved.** Atlas URI moved to `.env`, no longer hardcoded — see `decisions.md` D9 for the original reasoning on why this was deferred, and the "Latest session" note in `progress.md` for when it was actually done. Database name is `medical_db`.

### 2.7 `src/agents/face_recognize.py` — DELETED

Confirmed (via grep across `main.py`, `crew.py`, `auth.py`, `Calling.py`, `Calling_Ai.py`) that no file had an actual `import` statement referencing it — only comment-references in `auth.py`/`Calling_Ai.py` explaining what replaced it. File deleted; its dependency chain (`face-recognition`, `face-recognition-models`, `dlib`, `opencv-python`, `cmake`) removed from `pyproject.toml` since nothing uses `cv2`/`dlib` anywhere in the backend.

### 2.8 `src/agents/Calling_Ai.py`

Historically called `face_recognize()` at **module import time**, which crashed the server on startup with a `face_recognition_models` error. Already fixed before `face_recognize.py` was deleted (wrapped inside a `_get_user_details()`-style function, only called when an actual call is triggered) — user details now come from `auth.py` instead, confirmed via grep that no import of `face_recognize` remains anywhere in this file. The `import google.generativeai as genai` FutureWarning is harmless — the library still works, just deprecated.

### 2.9 Other backend modules (not touched, documented for completeness)

- `buying_agent.py` — **rewritten, extraction-only, confirmed working** (see `decisions.md` D21, D22). Two `browser-use` `Agent` instances run in parallel via `asyncio.gather`, one against 1mg, one against Apollo Pharmacy, each with its own Chrome profile directory (portable path construction now, no longer hardcoded — was `C:\agent_profile_1mg`/`C:\agent_profile_apollo`, fixed in D39 since two Chrome instances can't share one `--user-data-dir` and the Windows literals broke inside Docker) and its own 150-second timeout. Neither agent has any purchase/add-to-cart capability — they only read and report `{site, product_name, price, quantity, delivery_info, product_url, available, notes}` per medicine. "Best price" / "fastest delivery" tags are computed afterward in plain Python (`_attach_best_tags()`), not decided by the agent. Uses `browser_use.ChatGroq` (`meta-llama/llama-4-scout-17b-16e-instruct`) to drive the browser — needs `GROQ_API_KEY` in `.env` (confirmed present/working via live test on bare-metal; this model's own Docker 404 issue, §6 item 12, is still open and was NOT touched by D39). The hardcoded Windows Chrome `executable_path` previously pointed the Playwright launch at `C:\Program Files\Google\Chrome\Application\chrome.exe` — removed in D39, now uses the Chromium binary the Dockerfile already installs via `playwright install --with-deps chromium`. Has a FastAPI endpoint (`/medicine/compare`) that wraps `run_comparison()` directly, not through CrewAI.
  - **Known fixed bug:** the per-site agent's structured-output schema (`SingleSiteOutput`) deliberately uses a flat `List[Dict[str, Any]]` instead of nested Pydantic models, to work around a real `$defs`-schema crash in browser-use's internal `extract` tool fallback (hit when `use_vision=False`). See `decisions.md` D22 and `CLAUDE.md` Known Fixed Bugs.
- `Calling.py` — Twilio call orchestration.
- `speech_to_text.py` — AssemblyAI integration.
- `text_to_speech.py` — Deepgram integration.
- `file_to_text.py` — Tesseract OCR; hardcoded Windows path (`C:\Program Files\Tesseract-OCR\tesseract.exe`).
- `tools/custom_tool.py`, `tools/google_cal.py` — CrewAI custom tools, Google Calendar OAuth.
- `tools/credentials.json` — committed Google OAuth file; values are placeholder/redacted currently.

### 2.10 Python/Environment specifics

- Required Python: `>=3.10,<3.14` per `pyproject.toml`. User's machine default is Python 3.14; a separate **Python 3.11.9** was installed side-by-side specifically for this project (`py -3.11`).
- Venv location: `backend\venv\`
- Install sequence that works:
  1. `py -3.11 -m venv venv` then activate.
  2. `python -m ensurepip --upgrade` if pip is missing.
  3. Install dlib prebuilt wheel: `dlib-19.24.1-cp311-cp311-win_amd64.whl` from `github.com/z-mahmud22/Dlib_Windows_Python3.x`.
  4. `python -m pip install git+https://github.com/ageitgey/face_recognition_models`
  5. `python -m pip install "setuptools<81"` (for pkg_resources compatibility).
  6. `python -m pip install -e .`
  7. `python -m pip install fastapi uvicorn` (these were missing from pyproject.toml, installed separately).

## 3. Frontend Architecture

### 3.1 App structure — `src/App.jsx`

```jsx
<BrowserRouter>
  <Routes>
    <Route path="/" element={<Hero_Page />} />
    <Route path="/find-medicine" element={<FindMedicine />} />
    <Route path="/compare" element={<Compare />} />
    <Route path="/appointments" element={<Appointments />} />
    <Route path="/health-info" element={<HealthInfo />} />
    <Route path="/auth" element={<Auth />} />
    <Route path="/donor" element={<Donor />} />
    <Route path="/emergency/:token" element={<EmergencyView />} />
    <Route path="/lab-report" element={<LabReport />} />
    <Route path="/medicine-check" element={<MedicineCheck />} />
    <Route path="/doctor-visit/:token" element={<DoctorVisitView />} />
  </Routes>
</BrowserRouter>
```

**11 routes total** (was 10) after D32 added `/doctor-visit/:token` (`DoctorVisitView.jsx`, new this session).

`/emergency/:token` and `/doctor-visit/:token` are both intentionally outside any nav-bar wrapping (`EmergencyView.jsx` and `DoctorVisitView.jsx` do not use `<Layout>`) — each is meant to be opened by someone without a MediSarthi account (a stranger in an emergency, or a doctor scanning a visit QR), with zero distraction and no login wall.

### 3.2 Shared layout — `src/components/Layout.jsx` + `Layout.css`

Exports: `default Layout({ children })`, `LogoMark({ size, accent, center })`, `GoldParticles({ count })`, `AmbientBackground()`. Every page is wrapped in `<Layout>` **except** `EmergencyView.jsx`.

`Layout.css` holds all CSS design-token variables and shared utility classes: `.ms-page-header`, `.ms-card`, `.ms-btn-primary`, `.ms-btn-secondary`, `.ms-input`, `.ms-field`, `.ms-empty-state`, etc.

### 3.3 Pages (current wiring status)

- **`Hero_Page.jsx`** — Rotating ceramic donut, feature cards, stats bar, trust row. No backend calls.
- **`Auth.jsx`** — Login/Signup, wired to `/auth/signup` + `/auth/login`. Has the `extractErrorMessage()` safety helper (see `CLAUDE.md`).
- **`FindMedicine.jsx`** — Wired to `/consultation/speech` and `/consultation/document`.
- **`Compare.jsx`** — Wired to the real `/medicine/compare` endpoint, **confirmed working via live test.** No mock data remains. "Buy" action is a plain outbound link to the pharmacy's product page (Google search fallback if no direct URL was captured) — no cart interaction, no confirm step, since `buying_agent.py` never has purchase capability at all (see `decisions.md` D21, which supersedes D2's originally-described `idle → confirming → added` state machine). Has a rotating-status + elapsed-timer progress UI for the genuinely-long (1-3 min) real-browser wait.
- **`Appointments.jsx`** — Wired to `/hospitals/nearby` and the calling endpoint. `prefillFromHospital()` auto-fills the call form's phone number field (and highlights it via `.select()`) when a hospital has a real phone number (see §2.2), falling back to focus-only on an empty field when it doesn't.
- **`HealthInfo.jsx`** — Wired to vitals + timeline + Emergency Medical ID + QR endpoints. Has `extractErrorMessage()` at multiple call sites. **New this session (D32):** a second, separate "Doctor Visit QR" card next to the Emergency Medical ID card, wired to `POST /health/doctor-qr/{user_id}`. Deliberately does not auto-generate on load or restore a token across sessions (unlike the Emergency QR) — every click makes a fresh snapshot. ⚠️ Not yet live-tested.
- **`Donor.jsx`** — Wired to all 6 donor endpoints.
- **`EmergencyView.jsx`** — Wired to `/health/qr/{token}` (public, no auth). Has `extractErrorMessage()`.
- **`LabReport.jsx`** — Wired to `/lab/analyse` + `/lab/save`, **live-tested and confirmed working.** Also fetches `GET /lab/analyses/{user_id}` (saved-report history) and `GET /health/trends-annotated/{user_id}` (per-test trend charts + medicine annotations, D29 phase 1) in a "Your Health History & Trends" section. Has a delete flow per saved report (trash icon → "type DELETE to confirm" → `DELETE /lab/analyses/{user_id}/{analysis_id}`, D30, live-tested) and an `EffectivenessCard` per annotation, gated behind an explicit button, calling `POST /medicine/effectiveness` (D31 phase 2, live-tested).
- **`MedicineCheck.jsx`** — Single page, two tools: Medicine Interaction Checker (top) + Symptom Triage (bottom), wired to `/medicine/interactions` and `/triage/symptoms`, **live-tested and confirmed working.**
- **`DoctorVisitView.jsx`** **(NEW, D32)** — Public page, no `<Layout>`, no auth. Wired to `GET /health/doctor-qr/{token}`. Renders the cached snapshot: clinical summary + key flags, lab history, trends, prescriptions, expiry timestamp. Has `extractErrorMessage()`, same pattern as `EmergencyView.jsx`. ⚠️ Not yet live-tested.

### 3.4 Dead/unused frontend files (present, not imported, not deleted)

`Landing_page.jsx`, `Browse_Medicine.jsx`, `Call_Form.jsx`, `Nearby_Hospital.jsx`, `Record_Form.jsx`, `Image_Uploader.jsx`, `Animations_js/Galaxy.jsx`, `Animations_css/Galaxy.css`.

## 4. Design System Reference

```css
--ms-bg-primary: #F6F1EA;
--ms-bg-secondary: #EEE6DC;
--ms-white-card: #FFFFFF;
--ms-text-primary: #111111;
--ms-text-secondary: #6B625D;
--ms-luxury-brown: #9C6B45;
--ms-soft-gold: #D7B895;
--ms-dark-navy: #0F1720;
--ms-btn: #6F472D;
```

Typography: Playfair Display (headings/stat numbers), Inter (body). Cormorant Garamond imported but unused in shipped classes — keep the import.

## 5. Remaining Not-Yet-Built / Partial Work

- **`Appointments.jsx` phone auto-fill** — code written, not yet confirmed live by the user (see `progress.md`).
- **Tier 2 agents from the AGENTS audit brainstorm, deferred not rejected:** `DietAdvisor`, `MentalWellnessAgent` (see `decisions.md` D15).
- **Longer-term roadmap, current state:** safety guardrails (✅ built) → agent eval harness (✅ built, verified) → RAG with shared knowledge base (✅ built) → Lab report PDF extraction bug (✅ fixed + live-tested) → Health Trends report_date chronology bug (✅ fixed + live-tested) → Medicine Effectiveness phases 1 & 2 (✅ both live-tested, D29/D31) → Delete Lab Report Analysis (✅ live-tested, D30) → Doctor Visit QR (✅ built, D32) → JWT auth (✅ built + live-tested, D37) → Soft-delete for health records (✅ built, D35) → Docker + CI (✅ container boots clean, CI fully green, D36) → Medicine Interaction Checker duplicate-therapy safety fix (✅ built + live-tested, D38) → **Docker adaptability round 2 (✅ mostly done, D39): ngrok binary + hardcoded Chrome/profile paths in `buying_agent.py` + Ollama container networking all fixed, pushed to GitHub — but surfaced a NEW open item, a Groq TPM rate limit on dense `/lab/analyse` calls (§6 item 14), and `buying_agent.py`'s own separate Groq 404 (§6 item 12) remains unaddressed**. Deployment (actually hosting it somewhere public) is the next item not yet started. Still brainstormed-not-built: streaming consultation responses, a WhatsApp bot entry point. See `README.md` "Roadmap".
- **Safety guardrails layer — BUILT, user-tested status not confirmed in this doc.** `safety_guardrails.py` (`check_emergency()`) regex-checks symptom/consultation text for red-flag phrases before any LLM call, wired into `/triage/symptoms`, `/consultation/speech`, `/consultation/document`. See `decisions.md` D24.
- **Agent eval harness — BUILT and fully verified against actual `crew.py`/task YAMLs, not yet run by the user.** `eval_harness.py`: `guardrails` suite (zero LLM cost), `triage` suite (`SymptomTriageCrew`), `interactions` suite (`MedicineInteractionCrew`). `LabReportCrew` excluded (image/PDF input). See `decisions.md` D25.
- **RAG: shared knowledge base — BUILT this session, not yet tested.** `crew.py`'s `_build_crew_base()` now returns a list of knowledge sources with an optional `shared_kb_files` param. Wired into `LabReportCrew` (`lab_reference_ranges.txt`), `MedicineInteractionCrew` (`drug_interactions.txt`), `SymptomTriageCrew` (`symptom_red_flags.txt`) — each alongside the existing per-user profile source. **Correction to earlier framing:** the pre-existing `TextFileKnowledgeSource`+Ollama-embedder setup was already real embedding-based semantic search, not keyword lookup — the actual gap was thin retrievable content, not the retrieval mechanism. See `decisions.md` D26.
- **`range_low`/`range_high` shaded normal-range band on Health Trends charts** — deliberately dropped from this session's build to keep schema/prompt smaller (see `decisions.md` D23). Can be added the same way later if wanted.
- **Doctor Visit QR — BUILT this session (D32), NOT yet live-tested.** New `doctor_qr_tokens` collection, `ClinicalSummaryCrew`, 2 new endpoints, `DoctorVisitView.jsx`, new card in `HealthInfo.jsx`. See §10 for full detail and §11 for open items (no token-cleanup job yet, unconfirmed shared-KB file path).

## 6. Known Bugs / Issues

1. **~~`face_recognize.py` not yet deleted~~ — RESOLVED.** File deleted, confirmed no other file imported it. Dependency chain (`face-recognition`, `face-recognition-models`, `dlib`, `opencv-python`, `cmake`) also removed from `pyproject.toml`.
2. **`Calling_Ai.py` uses deprecated `google.generativeai`** — shows FutureWarning on startup. Harmless for now, should eventually migrate to `google.genai` package.
3. **~~Hardcoded MongoDB Atlas credentials in `db_connect.py`~~ — RESOLVED.** Moved to `.env`, confirmed excluded from version control before the public push (see `decisions.md` D9).
4. **`tools/credentials.json`** (Google OAuth) — now backed by a fresh, dedicated Google Cloud project (organization-linkage issue resolved).
5. **~~Hardcoded Windows-only Tesseract path~~ — RESOLVED, was already correct.** `file_to_text.py` guards the Windows-only path (`C:\Program Files\Tesseract-OCR\tesseract.exe`) behind `if platform.system() == "Windows":`, falling through to the PATH-resolved `tesseract` binary (installed via `apt-get install tesseract-ocr` in the Dockerfile) on Linux/Docker. Confirmed via direct file review this session — an earlier doc pass had this flagged as still-open in error.
6. **~~Compare.jsx still mock data~~ — RESOLVED.** Wired to a real, rewritten `buying_agent.py` and confirmed working via live test. See §3.3, §2.9, and `decisions.md` D21/D22.
7. **~~No session/auth-token mechanism on frontend~~ — RESOLVED (D37).** JWT auth (HS256, 7-day expiry) now live: `get_current_user_id` dependency on 30+ endpoints, `authFetch` wrapper + `ms_token` on the frontend. Verified on bare-metal (login 200, unauthorized 401); full flow not yet independently re-confirmed specifically through Docker — see item 12 below.
8. **~~Saved lab report history not surfaced anywhere in the frontend~~ — RESOLVED.** Health Trends feature built this session — `LabReport.jsx` now calls `GET /lab/analyses/{user_id}` for a real saved-reports list, plus new per-test trend charts via `GET /health/trends/{user_id}`. See §5 note and `decisions.md` D23. Not yet live-tested by the user with 2+ saved reports.
9. **~~`/lab/analyse` fell back to raw PDF bytes as text when PDF extraction failed~~ — RESOLVED, live-tested twice.** `extract_text_from_image()` (PIL-based) always raised on PDFs; the old `except` block silently read raw file bytes as "text," which `LabReportCrew` correctly flagged as garbled/not-a-lab-report — looked like a knowledge-base problem, was actually an extraction bug. Fixed with new `extract_text_from_lab_document()`: `pdfplumber` for text-based PDFs, `pdf2image`+Tesseract OCR fallback for scanned/photo PDFs. See `decisions.md` D27.
10. **~~Health Trends chart plotted every report on its upload date, not its actual report date~~ — RESOLVED, not yet live-tested with the fix in place.** `save_lab_report_analysis()` always used save-time (`datetime.utcnow()`) for the chronological `date` field `get_test_trends()` sorts/charts by. Two reports uploaded on the same real day (for testing) showed identical dates on the chart even though one was printed with a date 2 months apart. Fixed by threading a new `report_date` field (LLM-extracted from the document text, ISO `YYYY-MM-DD`, or `null`) through `lab_report_task.yaml` → `crew.py` → `main.py` → `health_records.py`'s new `_resolve_report_date()` → `LabReport.jsx`. See `decisions.md` D28.
11. **~~Medicine Interaction Checker gave a false "safe" verdict for two brand names of the same drug~~ — RESOLVED, live-tested.** "Paracetamol" + "Dolo 650" previously returned no interaction; fixed with a new prompt step (identify active ingredients first, flag shared-ingredient pairs as Duplicate Therapy) plus a brand→generic mapping section added to `drug_interactions.txt`. See `decisions.md` D38.
12. **STILL OPEN — Groq model 404 inside Docker, breaking medicine price comparison.** `buying_agent.py`'s configured model (`meta-llama/llama-4-scout-17b-16e-instruct`) is returning 404s during Docker validation, causing both the Apollo and 1mg scraping crews to fail. Not yet root-caused, and **not touched by D39** — D39 fixed other `buying_agent.py` Docker-adaptability bugs (hardcoded Chrome/profile-dir paths) but did not investigate this model 404 specifically. Could be a Groq-side model rename/deprecation or something Docker-environment-specific (stale model string, missing env var in the container). Still the top-priority open Docker item for the price-comparison feature specifically.
13. **~~Ollama RAG connection failure inside Docker~~ — RESOLVED (D39), not independently re-confirmed via a direct connectivity check.** Fixed by setting `OLLAMA_HOST=0.0.0.0` on the host-side `ollama serve` process and making the embedder URL configurable (`OLLAMA_EMBED_URL` env var, falling back to `http://localhost:11434/...`) instead of hardcoded. A full `LabReportCrew` run reached the LLM-call stage inside the container afterward, implying the RAG/embedder step ahead of it succeeded — but the direct `docker compose exec backend curl http://host.docker.internal:11434/api/tags` check wasn't captured with its actual output in this session's docs. Worth one explicit re-confirmation pass.
14. **NEW, OPEN — Groq TPM rate limit hit on `/lab/analyse` for dense reports.** Discovered while testing D39's fixes: `crew.py`'s Groq model was swapped (all 13 `LLM(...)` sites) from `groq/llama-3.3-70b-versatile` to `groq/openai/gpt-oss-120b` at some point (reasoning not re-derived this session, no dedicated decision record yet — worth writing one up if the "why" isn't already documented elsewhere). That model is capped at **8000 TPM** on the current Groq tier; a single `/lab/analyse` call combining the full `LabReportCrew` prompt template with a dense multi-panel report's extracted text requested 5447 tokens against an already-used 3201 in the same minute, tripping `litellm.RateLimitError`. Mitigations discussed (retry/backoff, prompt/panel chunking, `CREWAI_TRACING_ENABLED=false` to skip the no-TTY interactive trace prompt) — **none implemented yet.** See `decisions.md` D39.
15. **NEW, cosmetic, OPEN — mojibake em-dash in a handful of comment/print strings.** A few lines in `buying_agent.py`/`file_to_text.py`-adjacent files have `—` rendered as `├óΓé¼ΓÇ¥` from an encoding mismatch somewhere in the edit history. Purely cosmetic (comments/log strings, not logic), flagged during D39's pre-push diff review but not fixed.

## 7. State Management (Frontend)

No global state library. Each page manages its own local `useState`. Login session is tracked via `useUser.js` reading `ms_user_id`/`ms_user_name` from localStorage (decided — see `decisions.md` and `CLAUDE.md`'s "must never change" list). **Since D37 (JWT auth):** `useUser.js` also stores the issued JWT as `ms_token` and exposes a shared `authFetch` wrapper that attaches it as a bearer token — added alongside the original keys, not a replacement for them.

## 8. Authentication (Backend, current state) — UPDATED, JWT now live (D37)

- Email + password, bcrypt-hashed, stored in `Members` collection in `medical_db` on Atlas. `login_user()`/`signup_user()` still return a profile dict with an `ID` — unchanged.
- **JWT issuance now real, not pending.** `jwt_utils.py` issues HS256 tokens (PyJWT), 7-day expiry, signed with `JWT_SECRET_KEY` from `.env` (falls back to an insecure logged default if unset — must be set for anything beyond local testing, see `decisions.md` D36 fix #5). `/auth/login` and `/auth/signup` return the token alongside the profile dict.
- **`get_current_user_id`** is a FastAPI dependency applied to 30+ endpoints in `main.py`, validating the `Authorization: Bearer <token>` header and resolving the caller's user id — replacing the old "trust whatever `user_id` the client sends" model (D11) for those endpoints. Deliberately public/unauthenticated endpoints (by design, not oversight): `/auth/login`, `/auth/signup`, `GET /health/qr/{token}`, `GET /doctor-visit`/`/health/doctor-qr/{token}`.
- **Frontend:** `useUser.js` exports a shared `authFetch` wrapper that attaches the bearer token automatically; token stored as `ms_token` in localStorage, alongside (not replacing) the pre-existing `ms_user_id`/`ms_user_name` keys. All six main page components (`HealthInfo.jsx`, `LabReport.jsx`, `MedicineCheck.jsx`, `FindMedicine.jsx`, `Appointments.jsx`, `Donor.jsx`) call through `authFetch`.
- **Verified:** login → 200 with token, protected endpoint without token → 401 (bare-metal, confirmed). Full flow not yet independently re-run specifically inside the Docker container (see §5/§6 and `progress.md`'s open follow-up) — worth a final explicit pass.
- See `decisions.md` D37 for the full retroactive decision writeup (this was built and tested in an earlier session but only got a formal decision record during this doc-update pass).

## 9. Important Function/Endpoint Quick Index

| Name | File | Purpose |
|---|---|---|
| `signup_user` | `auth.py` | Create account |
| `login_user` | `auth.py` | Verify credentials |
| `get_user_by_id` | `auth.py` | Fetch profile by Mongo ObjectId string |
| `get_user_knowledge_profile` | `auth.py` | Write per-user `profile.txt`, return `(user_data, path)` |
| `build_user_profile` | `auth.py` | Internal: Mongo doc → stable profile dict |
| `get_database` | `db_connect.py` | Returns `medical_db` from Atlas — reused everywhere |
| `add_vital` | `health_records.py` | Save a vital record (generic + granular BP/sugar/weight fields) |
| `get_vitals` | `health_records.py` | Fetch a user's vitals |
| `add_prescription` / `get_prescriptions` | `health_records.py` | Prescription records |
| `get_full_timeline` | `health_records.py` | Merged vitals+prescriptions timeline, `{type, date, data}` shape |
| `save_emergency_profile` | `health_records.py` | Upsert emergency profile (strings, not lists) |
| `get_emergency_profile` | `health_records.py` | Fetch profile + merged `qr_token` |
| `get_emergency_profile_public` | `health_records.py` | Public lookup by QR token |
| `generate_qr_token` | `health_records.py` | New/replacement QR token for a user |
| `save_lab_report_analysis` / `get_lab_report_analyses` | `health_records.py` | Persist/fetch Lab Report Analyser results. `save_lab_report_analysis` now takes `report_date` (see `_resolve_report_date`) |
| `_resolve_report_date` | `health_records.py` | **(NEW)** Resolves a saved lab report's chronological `date` from the LLM-extracted `report_date` if parseable, else save-time fallback |
| `get_test_trends` | `health_records.py` | Per-test chronological series across saved reports, for the Health Trends chart — now chronologically correct per `_resolve_report_date` |
| `extract_text_from_lab_document` | `main.py` | **(NEW)** Routes lab report file extraction: images → existing `extract_text_from_image`; PDFs → `pdfplumber`, falling back to `pdf2image`+Tesseract OCR for scanned/photo PDFs |
| `register_donor` / `get_donor_by_user_id` / `record_donation` / `toggle_availability` | `donor.py` | Donor lifecycle |
| `create_donation_request` / `find_matching_donors` | `donor.py` | Emergency blood request + matching |
| `SpeechCrew.crew(user_id)` | `crew.py` | Voice consultation crew |
| `FileCrew.crew(user_id)` | `crew.py` | Document/prescription consultation crew |
| `Nearbyhospitals.crew(user_id)` | `crew.py` | Hospital search crew |
| `general_que.crew(user_id)` | `crew.py` | General Q&A crew |
| `LabReportCrew.crew(user_id)` | `crew.py` | Lab report plain-language analysis crew |
| `MedicineInteractionCrew.crew(user_id)` | `crew.py` | Medicine interaction-check crew |
| `SymptomTriageCrew.crew(user_id)` | `crew.py` | Symptom urgency-triage crew |
| `MedicineEffectivenessCrew.crew(user_id)` | `crew.py` | **(D29 phase 2/D31)** Direction+pace verdict crew |
| `ClinicalSummaryCrew.crew(user_id)` | `crew.py` | **(D32, NEW)** Terse clinical-register summary crew for Doctor Visit QR |
| `delete_lab_report_analysis` | `health_records.py` | **(D30)** Hard-delete a saved lab report, scoped to `user_id` |
| `get_annotated_trends` | `health_records.py` | **(D29 phase 1)** `get_test_trends()` + medicine-start annotations |
| `create_doctor_qr_token` / `get_doctor_qr_snapshot` | `health_records.py` | **(D32, NEW)** Doctor Visit QR token lifecycle |
| `delete_lab_analysis` | `main.py` | `DELETE /lab/analyses/{user_id}/{analysis_id}` handler (D30) |
| `get_health_trends_annotated` | `main.py` | `GET /health/trends-annotated/{user_id}` handler (D29) |
| `check_medicine_effectiveness` | `main.py` | `POST /medicine/effectiveness` handler (D31) |
| `health_generate_doctor_qr` / `health_get_doctor_qr` | `main.py` | **(D32, NEW)** `POST`/`GET /health/doctor-qr/...` handlers |
| `signup` / `login` | `main.py` | `/auth/signup`, `/auth/login` handlers — now also issue a JWT (D37) |
| `create_access_token` / `get_current_user_id` | `jwt_utils.py` | **(D37, NEW)** Issues HS256 tokens (7-day expiry); FastAPI dependency validating the bearer token, applied to 30+ endpoints |
| `speech_consultation` / `document_consultation` | `main.py` | Consultation handlers |
| `find_hospitals` | `main.py` | `/hospitals/nearby` handler |
| `general_health_query` | `main.py` | `/general-query` handler |
| `compare_prices` | `main.py` | `/medicine/compare` handler |
| `schedule_call` | `main.py` | `/call/schedule` handler |
| `health_add_vital` / `health_get_vitals` / `health_add_prescription` / `health_get_prescriptions` / `health_get_timeline` | `main.py` | Health records handlers |
| `health_save_emergency_profile` / `health_get_emergency_profile` / `health_generate_qr` / `health_qr_public` | `main.py` | Emergency QR handlers |
| `donor_register` / `donor_profile` / `donor_record_donation` / `donor_availability` / `donor_request_create` / `donor_find_matching` | `main.py` | Donor handlers |

## 10. Medicine Effectiveness feature — implementation plan (chosen MVP focus, NOT yet built)

See `decisions.md` D29 for full reasoning. Summary reference for implementation:

**Goal:** cross-reference a user's own saved prescriptions (`health_prescriptions`, via `get_prescriptions`) against their own saved lab trends (`lab_report_analyses`, via `get_test_trends`) to answer, per test: is the value moving the medically correct direction, is it moving at the expected pace for that medicine, and should the user mention it to their doctor — with a plain-language "why." Chosen specifically because this requires two of *this user's own* persisted records that only exist because MediSarthi already saves data across visits — not reproducible by a single-turn chat tool.

### Phase 1 — direction + start-date annotation (build first)

| Component | File | Notes |
|---|---|---|
| Direction reference | `knowledge/medical_kb/test_direction_reference.txt` (NEW) | Same pattern as D26's 3 existing reference files. Per-test: which direction is "improving" (e.g. Hemoglobin higher-is-better up to normal, FBS lower-is-better, Platelet Count must-stay-in-range). |
| Medicine↔test mapping | likely a new dict in `health_records.py` or a new small module | Static Python dict, ~20-30 common medicines (Metformin → [FBS, HbA1c], Levothyroxine → [TSH], etc.) — NOT an LLM call, this is a fixed clinical fact per medicine (see D29 for why static beats LLM-inferred here). |
| Backend join | new function, likely `get_test_trends()` extended or a new `get_annotated_trends()` in `health_records.py` | For each trend with 2+ points, check saved prescriptions for a mapped medicine; if found, attach `{medicine_name, start_date}` annotation to that trend's response. |
| Frontend chart marker | `TestTrendChart` in `LabReport.jsx` | Vertical dashed marker line at the medicine-start date + small label, plus an auto-computed "↓/↑ X since `<medicine>` started" badge above the chart. Mockup already shown to and approved by the user this session (orange/coral marker, blue trend line, matches existing SVG chart style). Direction sign for the badge (is a drop "good") should come from the backend (informed by `test_direction_reference.txt`), not be hardcoded per-test in the frontend. |

### Phase 2 — pace-awareness (build after phase 1 ships and is confirmed working)

| Component | File | Notes |
|---|---|---|
| Timeline reference | `knowledge/medical_kb/medicine_response_timelines.txt` (NEW) | Expected response window per medicine/test pair (e.g. Metformin→FBS: 1-2 weeks; Metformin→HbA1c: 8-12 weeks since it's a 3-month rolling average; Levothyroxine→TSH: 6-8 weeks). Higher research/curation effort than phase 1's direction file — this is why it's phase 2. |
| New schema | `crew.py` | `MedicineEffectivenessOutput`: `medicine_name`, `target_test`, `days_since_start`, `direction_correct: bool`, `pace_verdict` ("on track" / "slower than typical, still within expected window" / "not responding as expected"), `plain_explanation`, `doctor_talk_recommended: bool`, `disclaimer`. |
| New crew | `crew.py` | `MedicineEffectivenessCrew` — RAG-grounds against both `test_direction_reference.txt` and `medicine_response_timelines.txt` (reuse `_build_crew_base`'s `shared_kb_files` param, same as the 3 D26 crews). |
| New endpoint | `main.py` | Something like `GET /health/medicine-effectiveness/{user_id}` or computed inline as part of `/health/trends/{user_id}`'s response — not yet decided, pick when phase 2 starts. |

### Doctor Visit QR — ✅ BUILT (D32), not yet live-tested

Originally sketched and deprioritized behind Medicine Effectiveness; picked back up and built after Medicine Effectiveness (phases 1 & 2) and Delete Lab Report Analysis all shipped and were live-tested. Full reasoning and implementation detail in `decisions.md` D32 — summary:

- **New collection `doctor_qr_tokens`**, separate from `emergency_qr_tokens` (time-limited, 24h default, full clinical picture — vs. the Emergency QR's permanent, narrow-subset scope).
- **Snapshot, not live lookup** — the clinical summary + lab history + trends + prescriptions are captured once at generation time (`POST /health/doctor-qr/{user_id}`) and served as-is on every scan (`GET /health/doctor-qr/{token}`), so the LLM call happens once per QR generated, not once per scan.
- **`ClinicalSummaryCrew` + `ClinicalSummaryOutput`** (`crew.py`) — deliberately separate from `LabReportCrew`/`LabReportAnalysisOutput`; produces terse clinical-register text (e.g. "Hb 9.6 (down trend, 2mo), FBS 118 (improving on Metformin)") rather than reusing the patient-facing `overall_summary`. RAG-grounded against `lab_reference_ranges.txt` + `test_direction_reference.txt`.
- **`DoctorVisitView.jsx`** (`/doctor-visit/:token`, no `<Layout>`, no auth) + a new "Doctor Visit QR" card in `HealthInfo.jsx` (separate from, not merged into, the Emergency Medical ID card).
- **Known open items** (see D32 for full detail): no cleanup job for expired tokens yet; `ClinicalSummaryCrew`'s shared-KB file path for `test_direction_reference.txt` is assumed, not independently re-confirmed (same open item already flagged for `MedicineEffectivenessCrew`).
- **Test order before treating this as confirmed working** is spelled out in D32 — not yet run by the user as of this doc's last update.

## 11. Open Questions (not yet decided)

- Should `auth.py` eventually get JWT token issuance for proper session management? — open, on the longer-term roadmap.
- Will `DietAdvisor` and `MentalWellnessAgent` (Tier 2 from the AGENTS audit) get built later? — deferred, not decided either way.
- **Roadmap, current state:** safety guardrails ✅ (D24) → agent eval harness ✅ (D25) → RAG ✅ (D26) → PDF extraction fix ✅ live-tested (D27) → report_date chronology fix ✅ live-tested (D28) → Medicine Effectiveness phases 1 & 2 ✅ both live-tested (D29, D31) → Delete Lab Report Analysis ✅ live-tested (D30) → **Doctor Visit QR ✅ built, NOT yet live-tested (D32)** → Docker + CI + automated tests — **the one remaining roadmap item, not started.**
- ✅ Exact endpoint shape for Medicine Effectiveness phase 2 — RESOLVED (D31): `POST /medicine/effectiveness`, on-demand per annotation, forwards data the frontend already fetched rather than re-reading the DB.
- How to keep the medicine↔test static dict maintainable as it grows — static dict vs. LLM-suggested-at-prescription-time (see D29 "Future implications"). Still open.
- ✅ Groq LLM config scope in `crew.py` — RESOLVED: confirmed project-wide (`groq/llama-3.3-70b-versatile`) across all 9 crews now, directly from `crew.py`'s own migration comment.
- **`test_direction_reference.txt` shared-KB path** — `MedicineEffectivenessCrew` (D31) and `ClinicalSummaryCrew` (D32) both assume `knowledge/medical_kb/test_direction_reference.txt`, matching the other shared reference files' location. Neither assumption has been independently re-confirmed against the actual file layout in a live session yet — worth a single verification pass covering both crews at once.
- **No cleanup job for expired `doctor_qr_tokens` documents** (D32) — they simply stop resolving past `expires_at`, never deleted. Same deferred-follow-up shape as D30's flagged soft-delete/purge idea for lab reports. Not urgent at current scale.
- **Doctor Visit QR has not been live-tested yet** — see `decisions.md` D32 for the suggested test order (generate → verify tone → verify no-login access → verify expiry behavior) before treating it as confirmed working, same as any other "built this session" item in this doc.