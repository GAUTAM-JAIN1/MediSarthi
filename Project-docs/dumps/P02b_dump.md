# MediSarthi - P02b Review Closure Dump

## 1. HEADER
- **Prompt ID:** PROMPT 02b: P02 review closure (records, L2 docstring, L3 evidence, Mongo probe)
- **Date & Time:** 2026-11-01 20:35:00 IST
- **Python Version:** Python 3.11.9
- **Git Commit:** 0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths

---

## 2. DEFECT STATUS TABLE
| ID | Status | Evidence & Step Number |
| :--- | :--- | :--- |
| **C1** | FIXED | Step 1a: `backend/src/agents/main.py:50` import and line 420 call to `get_database()` confirmed present. |
| **C2** | BLOCKED | Step 6b & P02 Step 2e: Bare-metal Windows `\tmp` mkdir PermissionError in `browser_use.browser.session:58`. Isolated via `_load_browser_use()` until Docker/Linux run or Phase 2 removal. |
| **H1** | FIXED (disabled mode) / OPEN (enabled mode) | Step 1b: `backend/src/agents/main.py:975` returns safe disabled payload when `ENABLE_LIVE_CALLS=false` (FIXED). Enabled mode remains public without user auth (OPEN). |
| **H2** | FIXED | Step 1c: `backend/src/agents/rate_limit.py:7` implements `get_client_ip()` safely parsing rightmost `X-Forwarded-For` when `TRUST_PROXY_HEADERS=true`, and line 45 `prune_expired()` removes stale keys. |
| **M1** | FIXED | Step 1d: `backend/tests/test_phase0.py:17-24` monkeypatches `dotenv.load_dotenv` to no-op and purges `agents.*` from `sys.modules` for hermetic test execution. |
| **M2** | FIXED | Step 1e: `backend/src/agents/jwt_utils.py:28-30` explicitly imports and invokes `load_dotenv()` before reading configuration. |
| **M3** | FIXED | Step 6c: `decisions.md` D40 correctly documents `get_database()`, `_run_single_site()`, `_load_browser_use()`, and internal `BrowserProfile()` instantiation. |
| **M4** | FIXED | P02 Step 7b: `Project-docs/decision.md` verified 100% identical to `decisions.md` and deleted; only `decisions.md` remains. |
| **M5** | OPEN | Step 4: `Project-docs` is outside the `MediSarthi` git repository (`git rev-parse` returns fatal not a git repo; `git ls-files` finds 0 matches). |
| **L1** | FIXED | Step 1f: `Get-ChildItem -Pattern "on_event"` returns 0 matches; `main.py:9` import and line 57 `@asynccontextmanager` `lifespan` handler confirmed. |
| **L2** | FIXED | Step 2: Moved docstring to first statement inside `compare_prices` before rate-limit check with endpoint description; verified via `ast.parse` returning `DOCSTRING`. |
| **L3** | FIXED | Step 3: All keys verified against code reads. 2 keys with count 0 (`APOLLO_PROFILE_DIR`, `ONEMG_PROFILE_DIR`) deleted; remaining 18 keys all have code read counts >= 1. |

---

## 3. BASELINE (Step 0 Outputs, Verbatim)

### Step 0a: `python -m pytest -q`
```
..............F..                                                        [100%]
================================== FAILURES ===================================
____________________ test_call_status_disabled_by_default _____________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001B945AF3410>

    def test_call_status_disabled_by_default(monkeypatch):
        """8d. GET /call/status returns 200 with state == 'disabled' and transcript == [] without requiring auth header."""
        monkeypatch.delenv("ENABLE_LIVE_CALLS", raising=False)
        from agents.main import app
        client = TestClient(app)
        res = client.get("/call/status")
        assert res.status_code == 200
        body = res.json()
>       assert body["state"] == "disabled"
E       AssertionError: assert 'idle' == 'disabled'
E         
E         - disabled
E         + idle

tests\test_phase0.py:248: AssertionError
============================== warnings summary ===============================
venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

src\agents\main.py:79
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\tests\..\src\agents\main.py:79: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    @app.on_event("startup")

venv\Lib\site-packages\fastapi\applications.py:4675
tests/test_phase0.py::test_import_hermetic
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\applications.py:4675: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    return self.router.on_event(event_type)  # ty: ignore[deprecated]

tests/test_phase0.py::test_import_hermetic
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\src\agents\main.py:79: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    @app.on_event("startup")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED tests/test_phase0.py::test_call_status_disabled_by_default - AssertionError: assert 'idle' == 'disabled'
1 failed, 16 passed, 6 warnings in 34.92s
```
Pass count: 16 passed, 1 failed.

### Step 0b: `git status --short ; git log -1 --oneline`
```
 M backend/src/agents/Calling.py
 M backend/src/agents/Calling_Ai.py
 M backend/src/agents/buying_agent.py
 M backend/src/agents/db_connect.py
 M backend/src/agents/jwt_utils.py
 M backend/src/agents/main.py
?? backend/.env.example
?? backend/src/agents/rate_limit.py
?? backend/tests/test_phase0.py
?? local-changes.patch
0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths
```

---

## 4. GIT AND LOCATION (Step 0b and Step 4 Outputs, Verbatim)

### Step 0b:
```
 M backend/src/agents/Calling.py
 M backend/src/agents/Calling_Ai.py
 M backend/src/agents/buying_agent.py
 M backend/src/agents/db_connect.py
 M backend/src/agents/jwt_utils.py
 M backend/src/agents/main.py
?? backend/.env.example
?? backend/src/agents/rate_limit.py
?? backend/tests/test_phase0.py
?? local-changes.patch
0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths
```

### Step 4a: Test-Path for documents under `$docs`
```powershell
$docs = "C:\Users\gauta\OneDrive\Desktop\MediSarthi\Project-docs"
"progress.md", "decisions.md", "CLAUDE.md", "PROJECT_CONTEXT.md", "architecture.md" | ForEach-Object {
    $p = Join-Path $docs $_
    $exists = Test-Path $p
    Write-Output "${_}: $exists"
}
```
Output:
```
progress.md: True
decisions.md: True
CLAUDE.md: True
PROJECT_CONTEXT.md: True
architecture.md: True
```

### Step 4b: `git -C $docs rev-parse --show-toplevel`
```
fatal: not a git repository (or any of the parent directories): .git
```

### Step 4c: `git -C "C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi" ls-files | Select-String -Pattern "Project-docs"`
Output:
*(no output / 0 lines matched)*

### Step 4d Conclusion:
Project-docs is NOT version controlled

---

## 5. CHANGED FILES
### `backend\src\agents\main.py` (COMPLETE file content)
```python
#!/usr/bin/env python

import sys
import os
import re
import shutil
import asyncio
import threading
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import logging

logger = logging.getLogger(__name__)

from agents.rate_limit import LOGIN_LIMITER, SIGNUP_LIMITER, COMPARE_LIMITER, get_client_ip

from agents.crew import (
    SpeechCrew, FileCrew, Nearbyhospitals, general_que,
    LabReportCrew, MedicineInteractionCrew, SymptomTriageCrew,
    MedicineEffectivenessCrew, ClinicalSummaryCrew,
)
from agents.speech_to_text import transcribe_audio
from agents.buying_agent import run_comparison
from datetime import datetime
from agents.Calling import start_call, get_call_status
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
    delete_vital, delete_prescription,
    create_doctor_qr_token, get_doctor_qr_snapshot,
)
from agents.donor import (
    register_donor, get_donor_by_user_id, record_donation,
    toggle_availability, create_donation_request, find_matching_donors
)
from agents.safety_guardrails import check_emergency
# NEW (D33) — TTL index setup for doctor_qr_tokens cleanup.
from agents.db_connect import ensure_indexes, get_database
# NEW (D34) — JWT issuance + the per-request ownership-verification dependency.
from agents.jwt_utils import create_access_token, get_current_user_id, verify_owner
from PIL import Image, ImageEnhance
import pytesseract


@asynccontextmanager
async def lifespan(app: FastAPI):
    """(D33) Ensures the doctor_qr_tokens TTL index exists. Idempotent."""
    try:
        await asyncio.to_thread(ensure_indexes)
    except Exception as e:
        logger.warning(f"Startup ensure_indexes skipped (DB unreachable): {e}")
    yield


app = FastAPI(title="Medical Agent API", version="1.0", lifespan=lifespan)

_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _server_error(e: Exception) -> HTTPException:
    ref = uuid.uuid4().hex
    logger.exception(f"Internal server error (ref: {ref}): {e}")
    return HTTPException(
        status_code=500,
        detail=f"Something went wrong. Please try again. (ref: {ref})"
    )





class SignupRequest(BaseModel):
    name: str
    age: int
    gender: str
    allergies: str = ""
    city: str
    state: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class MedicineComparisonRequest(BaseModel):
    medicines: List[str]


class CallRequest(BaseModel):
    number: str
    disease: str = "General Checkup"
    doctor_name: str = "Any Doctor"
    availability: str = "Any Available Time"
    patient_name: str = ""
    reason: str = ""


class LocationRequest(BaseModel):
    user_id: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    limit: int = 5


class VitalRequest(BaseModel):
    user_id: str
    vital_type: str
    value: float
    unit: str
    notes: str = ""
    bp_systolic: Optional[float] = None
    bp_diastolic: Optional[float] = None
    blood_sugar: Optional[float] = None
    weight: Optional[float] = None


class PrescriptionRequest(BaseModel):
    user_id: str
    medicines: List[str]
    symptoms: str = ""
    doctor_notes: str = ""
    source: str = "manual"


class EmergencyProfileRequest(BaseModel):
    user_id: str
    name: str
    blood_group: str
    allergies: str = ""
    critical_conditions: str = ""
    emergency_contact_name: str = ""
    emergency_contact_phone: str = ""
    medicines: str = ""


class SavePrescriptionAnalysisRequest(BaseModel):
    user_id: str
    overall_summary: str
    medicines: List[dict]
    has_allergy_conflict: bool
    safety_note: str
    source: str = "voice"
    raw_medicines: List[dict] = []


class SaveLabReportAnalysisRequest(BaseModel):
    user_id: str
    report_type: str
    overall_summary: str
    tests: List[dict]
    urgent_flags: List[str] = []
    has_urgent_values: bool
    next_steps: str
    disclaimer: str
    raw_text: str = ""
    report_date: str = ""


class MedicineInteractionRequest(BaseModel):
    user_id: str
    medicines: List[str]


class SymptomTriageRequest(BaseModel):
    user_id: str
    symptoms: str


class MedicineEffectivenessRequest(BaseModel):
    user_id: str
    medicine_name: str
    test_name: str
    start_date: str
    points: List[dict]
    normal_range: str = ""


class DonorRegisterRequest(BaseModel):
    user_id: str
    name: str
    blood_group: str
    city: str
    state: str
    phone: str


class DonationRequestBody(BaseModel):
    requester_user_id: str
    blood_group: str
    city: str
    state: str
    message: str = ""


class FindDonorsRequest(BaseModel):
    blood_group: str
    city: str
    state: str


def save_upload_file(upload_file: UploadFile, destination: str):
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()


def extract_text_from_image(image_path: str) -> str:
    import platform

    if platform.system() == "Windows":
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    image = Image.open(image_path)
    image = image.convert("L")
    scale_factor = 2
    image = image.resize(
        (image.width * scale_factor, image.height * scale_factor),
        Image.LANCZOS,
    )
    image = ImageEnhance.Contrast(image).enhance(1.5)

    custom_config = r"--oem 3 --psm 6"
    text = pytesseract.image_to_string(image, lang="eng", config=custom_config)
    return text


def extract_text_from_lab_document(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext != ".pdf":
        return extract_text_from_image(file_path)

    try:
        import pdfplumber
        pages_text = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                pages_text.append(page.extract_text() or "")
        text = "\n".join(pages_text).strip()
        if text:
            return text
    except Exception as e:
        print(f"[lab-report] pdfplumber text extraction failed: {e}")

    try:
        from pdf2image import convert_from_path
        import platform

        if platform.system() == "Windows":
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

        page_images = convert_from_path(file_path)
        ocr_text = [pytesseract.image_to_string(img, lang='eng') for img in page_images]
        text = "\n".join(ocr_text).strip()
        if text:
            return text
    except Exception as e:
        print(f"[lab-report] PDF OCR fallback failed: {e}")

    raise ValueError(
        "PDF se koi text nahi nikal paya (na embedded text mila, na OCR chala). "
        "File corrupted, password-protected, ya blank ho sakti hai."
    )


def parse_hospital_list(raw_text: str) -> List[dict]:
    if not raw_text:
        return []

    hospitals = []
    current = None

    name_line_re = re.compile(
        r"^[\*\-]\s*(?:\*\*(?P<bold>.+?)\*\*|`(?P<tick>.+?)`)\s*[:,]?\s*(?P<rest>.*)$"
    )

    for line in raw_text.split("\n"):
        line = line.strip()
        if not line:
            continue

        m = name_line_re.match(line)
        if m:
            if current:
                hospitals.append(current)

            name = (m.group("bold") or m.group("tick") or "").strip()
            rest = (m.group("rest") or "").strip()
            rest = re.sub(r"^\*+\s*", "", rest)
            rest = re.sub(r"\s*\*+$", "", rest)

            phone_val = None
            phone_m = re.search(r"\|?\s*Phone\s*:\s*(.+)$", rest, re.IGNORECASE)
            if phone_m:
                phone_text = phone_m.group(1).strip()
                phone_text = re.sub(r"^\*+|\*+$", "", phone_text).strip()
                address_part = rest[: phone_m.start()].strip()
                address_part = re.sub(r"[\|,]\s*$", "", address_part).strip()
                if phone_text and phone_text.lower() not in (
                    "not available", "n/a", "na", "none", "unknown", "not provided", "",
                ):
                    phone_val = phone_text
                rest = address_part

            current = {
                "name": name,
                "address": rest,
                "phone": phone_val,
                "maps_url": None,
            }
            continue

        if current is None:
            continue

        addr_match = re.match(r"^[\*\-]\s*Address:\s*(.+)$", line, re.IGNORECASE)
        if addr_match:
            current["address"] = addr_match.group(1).strip()
            continue

        phone_match = re.match(r"^[\*\-]\s*Phone:\s*(.+)$", line, re.IGNORECASE)
        if phone_match:
            current["phone"] = phone_match.group(1).strip()
            continue

        maps_match = re.match(r"^[\*\-]\s*(?:Maps?|Map URL|Link):\s*(\S+)$", line, re.IGNORECASE)
        if maps_match:
            current["maps_url"] = maps_match.group(1).strip()
            continue

    if current:
        hospitals.append(current)

    return hospitals


# ---- Auth Endpoints (public — this is how you GET a token) ----------------

@app.post("/auth/signup")
def signup(request: SignupRequest, req: Request):
    client_ip = get_client_ip(req)
    if not SIGNUP_LIMITER.check(client_ip):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again in a minute.")
    try:
        profile = signup_user(
            request.name, request.age, request.gender, request.allergies,
            request.city, request.state, request.email, request.password
        )
        token = create_access_token(profile["ID"])
        return {"user_id": profile["ID"], "name": profile["Name"], "user": profile, "access_token": token}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as e:
        raise _server_error(e)


@app.post("/auth/login")
def login(request: LoginRequest, req: Request):
    client_ip = get_client_ip(req)
    if not LOGIN_LIMITER.check(client_ip):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again in a minute.")
    try:
        profile = login_user(request.email, request.password)
        token = create_access_token(profile["ID"])
        return {"user_id": profile["ID"], "name": profile["Name"], "user": profile, "access_token": token}
    except ValueError as err:
        raise HTTPException(status_code=401, detail=str(err))
    except Exception as e:
        raise _server_error(e)


# ---- Health Check (public) --------------------------------------------------

@app.get("/")
def health_check():
    return {"status": "active", "message": "Medical Agent API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready(response: Response):
    mongo_ok = bool(os.getenv("MONGO_URI"))
    groq_ok = bool(os.getenv("GROQ_API_KEY"))
    jwt_ok = bool(os.getenv("JWT_SECRET_KEY"))

    db_ok = False
    if mongo_ok:
        try:
            db = get_database()
            db.client.admin.command("ping")
            db_ok = True
        except Exception as e:
            logger.exception(f"Readiness check: MongoDB ping failed: {e}")
            db_ok = False

    all_ok = mongo_ok and groq_ok and jwt_ok and db_ok
    checks = {
        "mongo_uri": "ok" if mongo_ok else "fail",
        "groq_api_key": "ok" if groq_ok else "fail",
        "jwt_secret_key": "ok" if jwt_ok else "fail",
        "mongodb": "ok" if db_ok else "fail",
    }

    if all_ok:
        return {"status": "ready", "checks": checks}
    else:
        response.status_code = 503
        return {"status": "not_ready", "checks": checks}


# ---- Consultation Endpoints (protected) ------------------------------------

@app.post("/consultation/speech")
async def speech_consultation(
    audio_file: UploadFile = File(...),
    user_id: str = Form(...),
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    temp_filename = f"temp_{audio_file.filename}"
    try:
        save_upload_file(audio_file, temp_filename)
        statement = transcribe_audio(temp_filename)
        inputs = {"statement": f"[{timestamp}] {statement}"}

        guardrail_result = check_emergency(statement)
        if guardrail_result:
            return {
                "consultation_result": guardrail_result["explanation"],
                "prescription": {},
                "analysis": {
                    "overall_summary": guardrail_result["explanation"],
                    "medicines": [],
                    "has_allergy_conflict": False,
                    "safety_note": guardrail_result.get("crisis_resource") or guardrail_result["disclaimer"],
                },
            }

        crew_instance = SpeechCrew().crew(user_id=user_id)
        result = crew_instance.kickoff(inputs=inputs)

        prescription_dict = {}
        analysis_dict = {}
        for task_output in getattr(result, "tasks_output", []):
            pyd = getattr(task_output, "pydantic", None)
            if pyd is None:
                continue
            parsed = pyd.dict()
            if "medicines" in parsed and "overall_summary" not in parsed:
                prescription_dict = parsed
            elif "overall_summary" in parsed:
                analysis_dict = parsed

        return {
            "consultation_result": result.raw,
            "prescription": prescription_dict,
            "analysis": analysis_dict,
        }
    except Exception as e:
        raise _server_error(e)
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


@app.post("/consultation/document")
async def document_consultation(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    temp_filename = f"temp_{file.filename}"
    try:
        save_upload_file(file, temp_filename)
        statement = extract_text_from_image(temp_filename)
        inputs = {"statement": f"[{timestamp}] {statement}"}

        guardrail_result = check_emergency(statement)
        if guardrail_result:
            return {
                "extraction_result": guardrail_result["explanation"],
                "prescription": {},
                "analysis": {
                    "overall_summary": guardrail_result["explanation"],
                    "medicines": [],
                    "has_allergy_conflict": False,
                    "safety_note": guardrail_result.get("crisis_resource") or guardrail_result["disclaimer"],
                },
            }

        crew_instance = FileCrew().crew(user_id=user_id)
        result = crew_instance.kickoff(inputs=inputs)

        prescription_dict = {}
        analysis_dict = {}
        for task_output in getattr(result, "tasks_output", []):
            pyd = getattr(task_output, "pydantic", None)
            if pyd is None:
                continue
            parsed = pyd.dict()
            if "medicines" in parsed and "overall_summary" not in parsed:
                prescription_dict = parsed
            elif "overall_summary" in parsed:
                analysis_dict = parsed

        return {
            "extraction_result": result.raw,
            "prescription": prescription_dict,
            "analysis": analysis_dict,
        }
    except Exception as e:
        raise _server_error(e)
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


# ---- Lab Report Analysis Endpoints (protected) -----------------------------

@app.post("/lab/analyse")
async def analyse_lab_report(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    temp_filename = f"temp_lab_{file.filename}"
    try:
        save_upload_file(file, temp_filename)

        try:
            report_text = extract_text_from_lab_document(temp_filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read the uploaded file: {e}")

        if not report_text or not report_text.strip():
            raise HTTPException(
                status_code=422,
                detail="File se koi text extract nahi ho saka. Clear image ya text-based PDF upload karo."
            )

        inputs = {"report_text": report_text}
        crew_instance = LabReportCrew().crew(user_id=user_id)
        result = crew_instance.kickoff(inputs=inputs)

        analysis_dict = {}
        for task_output in getattr(result, "tasks_output", []):
            pyd = getattr(task_output, "pydantic", None)
            if pyd is not None:
                analysis_dict = pyd.dict()
                break

        return {
            "report_text": report_text,
            "analysis": analysis_dict,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise _server_error(e)
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


@app.post("/lab/save")
def save_lab_report(
    request: SaveLabReportAnalysisRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, request.user_id)
    try:
        record_id = save_lab_report_analysis(
            request.user_id,
            request.report_type,
            request.overall_summary,
            request.tests,
            request.urgent_flags,
            request.has_urgent_values,
            request.next_steps,
            request.disclaimer,
            request.raw_text,
            request.report_date,
        )
        return {"status": "saved", "record_id": record_id}
    except Exception as e:
        raise _server_error(e)


@app.get("/lab/analyses/{user_id}")
def get_lab_analyses(
    user_id: str,
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        records = get_lab_report_analyses(user_id, limit)
        return {"analyses": records, "count": len(records)}
    except Exception as e:
        raise _server_error(e)


@app.delete("/lab/analyses/{user_id}/{analysis_id}")
def delete_lab_analysis(
    user_id: str,
    analysis_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        deleted = delete_lab_report_analysis(user_id, analysis_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Report nahi mila ya already delete ho chuka hai."
            )
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise _server_error(e)


@app.get("/health/trends/{user_id}")
def get_health_trends(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        trends = get_test_trends(user_id)
        return {"trends": trends, "count": len(trends)}
    except Exception as e:
        raise _server_error(e)


@app.get("/health/trends-annotated/{user_id}")
def get_health_trends_annotated(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        trends = get_annotated_trends(user_id)
        return {"trends": trends, "count": len(trends)}
    except Exception as e:
        raise _server_error(e)


# ---- Medicine Interaction Checker Endpoint (protected) ---------------------

@app.post("/medicine/interactions")
def check_medicine_interactions(
    request: MedicineInteractionRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, request.user_id)
    if not request.medicines or len(request.medicines) == 0:
        raise HTTPException(status_code=400, detail="Kam se kam ek medicine ka naam do.")

    try:
        medicines_list_str = ", ".join(request.medicines)
        inputs = {"medicines_list": medicines_list_str}

        crew_instance = MedicineInteractionCrew().crew(user_id=request.user_id)
        result = crew_instance.kickoff(inputs=inputs)

        interaction_dict = {}
        for task_output in getattr(result, "tasks_output", []):
            pyd = getattr(task_output, "pydantic", None)
            if pyd is not None:
                interaction_dict = pyd.dict()
                break

        if not interaction_dict:
            interaction_dict = {"raw": result.raw}

        return {"interactions": interaction_dict}
    except Exception as e:
        raise _server_error(e)


# ---- Symptom Triage Endpoint (protected) -----------------------------------

@app.post("/triage/symptoms")
def triage_symptoms(
    request: SymptomTriageRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, request.user_id)
    if not request.symptoms or not request.symptoms.strip():
        raise HTTPException(status_code=400, detail="Symptoms describe karo.")

    guardrail_result = check_emergency(request.symptoms)
    if guardrail_result:
        return {"triage": guardrail_result}

    try:
        inputs = {"symptoms": request.symptoms}
        crew_instance = SymptomTriageCrew().crew(user_id=request.user_id)
        result = crew_instance.kickoff(inputs=inputs)

        triage_dict = {}
        for task_output in getattr(result, "tasks_output", []):
            pyd = getattr(task_output, "pydantic", None)
            if pyd is not None:
                triage_dict = pyd.dict()
                break

        if not triage_dict:
            triage_dict = {"raw": result.raw}

        return {"triage": triage_dict}
    except Exception as e:
        raise _server_error(e)


# ---- Medicine Effectiveness Endpoint (protected) ---------------------------

@app.post("/medicine/effectiveness")
def check_medicine_effectiveness(
    request: MedicineEffectivenessRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, request.user_id)
    if not request.points or len(request.points) < 1:
        raise HTTPException(status_code=400, detail="Test ke liye kam se kam ek data point chahiye.")

    try:
        points_str = "\n".join(
            f"- {p.get('date', '?')}: {p.get('value', '?')} ({p.get('status', '?')})"
            for p in request.points
        )
        inputs = {
            "medicine_name": request.medicine_name,
            "test_name": request.test_name,
            "start_date": request.start_date,
            "points": points_str,
            "normal_range": request.normal_range or "Not provided",
        }
        crew_instance = MedicineEffectivenessCrew().crew(user_id=request.user_id)
        result = crew_instance.kickoff(inputs=inputs)

        effectiveness_dict = {}
        for task_output in getattr(result, "tasks_output", []):
            pyd = getattr(task_output, "pydantic", None)
            if pyd is not None:
                effectiveness_dict = pyd.dict()
                break

        if not effectiveness_dict:
            effectiveness_dict = {"raw": result.raw}

        return {"effectiveness": effectiveness_dict}
    except Exception as e:
        raise _server_error(e)


# ---- Doctor Visit QR Endpoints ----------------------------------------------

@app.post("/health/doctor-qr/{user_id}")
def health_generate_doctor_qr(
    user_id: str,
    expiry_hours: int = 24,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        lab_reports = get_lab_report_analyses(user_id, limit=20)
        trends = get_annotated_trends(user_id)
        prescriptions = get_prescriptions(user_id, limit=20)

        if lab_reports:
            lab_history_lines = []
            for r in lab_reports:
                date = r.get("date", "?")[:10]
                report_type = r.get("report_type", "Unknown")
                test_lines = "; ".join(
                    f"{t.get('test_name')}: {t.get('value')} ({t.get('status')})"
                    for t in r.get("tests", [])
                )
                lab_history_lines.append(f"- [{date}] {report_type}: {test_lines}")
            lab_history_str = "\n".join(lab_history_lines)
        else:
            lab_history_str = "No saved lab reports."

        if trends:
            trend_lines = []
            for tr in trends:
                points_str = " -> ".join(
                    f"{p.get('date', '?')[:10]}: {p.get('value')}" for p in tr.get("points", [])
                )
                annotations = tr.get("annotations") or []
                ann_str = ""
                if annotations:
                    ann_str = " (medicines: " + ", ".join(
                        f"{a['medicine_name']} since {a['start_date'][:10]}" for a in annotations
                    ) + ")"
                trend_lines.append(
                    f"- {tr['test_name']}: {points_str} [{tr.get('trend_direction') or 'n/a'}]{ann_str}"
                )
            trends_summary_str = "\n".join(trend_lines)
        else:
            trends_summary_str = "No tests with 2+ saved data points yet."

        if prescriptions:
            rx_lines = []
            for rx in prescriptions:
                date = (rx.get("date") or "?")[:10]
                meds = ", ".join(rx.get("medicines") or [])
                rx_lines.append(f"- [{date}] {meds}")
            prescriptions_summary_str = "\n".join(rx_lines)
        else:
            prescriptions_summary_str = "No saved prescriptions."

        inputs = {
            "lab_history": lab_history_str,
            "trends_summary": trends_summary_str,
            "prescriptions_summary": prescriptions_summary_str,
        }

        crew_instance = ClinicalSummaryCrew().crew(user_id=user_id)
        result = crew_instance.kickoff(inputs=inputs)

        summary_dict = {}
        for task_output in getattr(result, "tasks_output", []):
            pyd = getattr(task_output, "pydantic", None)
            if pyd is not None:
                summary_dict = pyd.dict()
                break
        if not summary_dict:
            summary_dict = {"clinical_summary": result.raw, "key_flags": [], "active_medicines_note": "", "disclaimer": ""}

        snapshot = {
            "clinical_summary": summary_dict,
            "lab_reports": lab_reports,
            "trends": trends,
            "prescriptions": prescriptions,
        }

        token = create_doctor_qr_token(user_id, snapshot, expiry_hours=expiry_hours)
        return {
            "token": token,
            "qr_url": f"/doctor-visit/{token}",
            "expires_in_hours": expiry_hours,
        }
    except Exception as e:
        raise _server_error(e)


@app.get("/health/doctor-qr/{token}")
def health_get_doctor_qr(token: str):
    """Public, no auth — see module note above."""
    try:
        result = get_doctor_qr_snapshot(token)
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Ye QR invalid hai ya expire ho chuka hai. Patient se naya QR generate karne ko kaho."
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise _server_error(e)


# ---- Existing Endpoints ------------------------------------------------------

@app.post("/medicine/compare")
async def compare_prices(request: MedicineComparisonRequest, req: Request):
    """
    Compares medicine prices across online pharmacies.

    NOT user-scoped (no user_id in the request today) — left unauthenticated
        for now. If abuse becomes a concern, add
        current_user_id: str = Depends(get_current_user_id) here too.
    """
    client_ip = get_client_ip(req)
    if not COMPARE_LIMITER.check(client_ip):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again in a minute.")
    try:
        comparison = await run_comparison(request.medicines)
        if comparison is None:
            raise HTTPException(
                status_code=502,
                detail="Price comparison agent se koi result nahi mila. Dobara try karo."
            )
        return comparison
    except HTTPException:
        raise
    except TimeoutError as err:
        raise HTTPException(status_code=504, detail=str(err))
    except Exception as e:
        raise _server_error(e)


@app.post("/call/schedule")
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
    if os.getenv("ENABLE_LIVE_CALLS", "false").lower() != "true":
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


@app.get("/call/status")
def call_status():
    # When live calls are enabled, the frontend phase must add auth here because transcript is patient conversation content.
    if os.getenv("ENABLE_LIVE_CALLS", "false").lower() != "true":
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


@app.post("/hospitals/nearby")
def find_hospitals(
    location: LocationRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, location.user_id)
    try:
        if location.city and location.state:
            city = location.city
            state = location.state
        else:
            user_profile = get_user_by_id(location.user_id)
            city = user_profile.get("City")
            state = user_profile.get("State")
            if not city or not state:
                raise HTTPException(
                    status_code=400,
                    detail="User profile mein city/state save nahi hai. Manually bhejo."
                )
        inputs = {
            "city": city,
            "state": state,
            "country": location.country,
            "limit": location.limit
        }
        result = Nearbyhospitals().crew(user_id=location.user_id).kickoff(inputs=inputs)
        raw_text = getattr(result, "raw", str(result))
        hospitals = parse_hospital_list(raw_text)
        return {"hospitals": hospitals, "raw": raw_text}
    except HTTPException:
        raise
    except Exception as e:
        raise _server_error(e)


@app.post("/general-query")
async def general_health_query(
    audio_file: UploadFile = File(...),
    user_id: str = Form(...),
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    temp_filename = f"temp_query_{audio_file.filename}"
    try:
        save_upload_file(audio_file, temp_filename)
        question = transcribe_audio(temp_filename)
        result = general_que().crew(user_id=user_id).kickoff(inputs={"question": question})
        return {"answer": result}
    except Exception as e:
        raise _server_error(e)
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


# ---- Donor Endpoints (protected) --------------------------------------------

@app.post("/donor/register")
def donor_register(
    request: DonorRegisterRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, request.user_id)
    try:
        donor = register_donor(
            request.user_id, request.name, request.blood_group,
            request.city, request.state, request.phone
        )
        return {"donor": donor}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as e:
        raise _server_error(e)


@app.get("/donor/{user_id}")
def donor_profile(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        return {"donor": get_donor_by_user_id(user_id)}
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as e:
        raise _server_error(e)


@app.post("/donor/{user_id}/record-donation")
def donor_record_donation(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        return {"donor": record_donation(user_id)}
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as e:
        raise _server_error(e)


@app.post("/donor/{user_id}/availability")
def donor_availability(
    user_id: str,
    available: bool,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        return {"donor": toggle_availability(user_id, available)}
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as e:
        raise _server_error(e)


@app.post("/donor/request/create")
def donor_request_create(
    request: DonationRequestBody,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, request.requester_user_id)
    try:
        req = create_donation_request(
            request.requester_user_id, request.blood_group,
            request.city, request.state, request.message
        )
        return {"request": req}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as e:
        raise _server_error(e)


@app.post("/donor/request/find-donors")
def donor_find_matching(
    request: FindDonorsRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    """No user_id on this request — only "must be logged in" is enforced."""
    try:
        donors = find_matching_donors(request.blood_group, request.city, request.state)
        return {"donors": donors, "count": len(donors)}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as e:
        raise _server_error(e)


# ---- Health Records Endpoints (protected) -----------------------------------

@app.post("/health/vital")
def health_add_vital(
    request: VitalRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, request.user_id)
    try:
        record_id = add_vital(
            request.user_id, request.vital_type,
            request.value, request.unit, request.notes,
            bp_systolic=request.bp_systolic,
            bp_diastolic=request.bp_diastolic,
            blood_sugar=request.blood_sugar,
            weight=request.weight,
        )
        return {"status": "saved", "record_id": record_id}
    except Exception as e:
        raise _server_error(e)


@app.get("/health/vitals/{user_id}")
def health_get_vitals(
    user_id: str,
    vital_type: Optional[str] = None,
    limit: int = 30,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        records = get_vitals(user_id, vital_type, limit)
        return {"vitals": records, "count": len(records)}
    except Exception as e:
        raise _server_error(e)


@app.delete("/health/vitals/{user_id}/{vital_id}")
def health_delete_vital(
    user_id: str,
    vital_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        deleted = delete_vital(user_id, vital_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Vital record nahi mila ya already delete ho chuka hai."
            )
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise _server_error(e)


@app.post("/health/prescription")
def health_add_prescription(
    request: PrescriptionRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, request.user_id)
    try:
        record_id = add_prescription(
            request.user_id, request.medicines,
            request.symptoms, request.doctor_notes, request.source
        )
        return {"status": "saved", "record_id": record_id}
    except Exception as e:
        raise _server_error(e)


@app.get("/health/prescriptions/{user_id}")
def health_get_prescriptions(
    user_id: str,
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        records = get_prescriptions(user_id, limit)
        return {"prescriptions": records, "count": len(records)}
    except Exception as e:
        raise _server_error(e)


@app.delete("/health/prescriptions/{user_id}/{prescription_id}")
def health_delete_prescription(
    user_id: str,
    prescription_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        deleted = delete_prescription(user_id, prescription_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Prescription record nahi mila ya already delete ho chuka hai."
            )
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise _server_error(e)


@app.post("/health/prescription-analysis")
def health_save_prescription_analysis(
    request: SavePrescriptionAnalysisRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, request.user_id)
    try:
        record_id = save_prescription_analysis(
            request.user_id,
            request.overall_summary,
            request.medicines,
            request.has_allergy_conflict,
            request.safety_note,
            request.source,
            request.raw_medicines,
        )
        return {"status": "saved", "record_id": record_id}
    except Exception as e:
        raise _server_error(e)


@app.get("/health/prescription-analyses/{user_id}")
def health_get_prescription_analyses(
    user_id: str,
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        records = get_prescription_analyses(user_id, limit)
        return {"analyses": records, "count": len(records)}
    except Exception as e:
        raise _server_error(e)


@app.get("/health/prescription-analysis/{user_id}/{analysis_id}")
def health_get_prescription_analysis_detail(
    user_id: str,
    analysis_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        record = get_prescription_analysis_by_id(user_id, analysis_id)
        if not record:
            raise HTTPException(status_code=404, detail="Analysis nahi mila.")
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise _server_error(e)


@app.get("/health/timeline/{user_id}")
def health_get_timeline(
    user_id: str,
    limit: int = 50,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        records = get_full_timeline(user_id, limit)
        return {"timeline": records, "count": len(records)}
    except Exception as e:
        raise _server_error(e)


@app.post("/health/emergency-profile")
def health_save_emergency_profile(
    request: EmergencyProfileRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, request.user_id)
    try:
        save_emergency_profile(
            request.user_id, request.name, request.blood_group,
            request.allergies, request.critical_conditions,
            request.emergency_contact_name, request.emergency_contact_phone,
            request.medicines,
        )
        return {"status": "saved"}
    except Exception as e:
        raise _server_error(e)


@app.get("/health/emergency-profile/{user_id}")
def health_get_emergency_profile(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        profile = get_emergency_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Emergency profile nahi bana abhi tak.")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise _server_error(e)


@app.post("/health/generate-qr/{user_id}")
def health_generate_qr(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        token = generate_qr_token(user_id)
        qr_url = f"/health/qr/{token}"
        return {"token": token, "qr_url": qr_url}
    except Exception as e:
        raise _server_error(e)


@app.get("/health/qr/{token}")
def health_qr_public(token: str):
    """
    Public, no auth — by design. `token` here is the separate
    emergency_qr_tokens credential, not a JWT — do not touch.
    """
    try:
        profile = get_emergency_profile_public(token)
        if not profile:
            raise HTTPException(status_code=404, detail="Invalid QR code ya profile nahi mili.")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise _server_error(e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### `backend\.env.example` (COMPLETE file content)
```bash
# Application environment: "development" (allows dev JWT secret fallback) or "production" (enforces strict >=32-char secret)
APP_ENV=

# Comma-separated allowed frontend origins for CORS (default: http://localhost:5173)
ALLOWED_ORIGINS=

# Set true only behind a trusted reverse proxy (Cloud Run, Render, nginx) to parse X-Forwarded-For
TRUST_PROXY_HEADERS=

# Live outbound AI phone calling flag: set to "true" to enable live Twilio calls, otherwise disabled (403)
ENABLE_LIVE_CALLS=

# JWT secret key for signing access tokens (must be at least 32 characters in production)
JWT_SECRET_KEY=

# JWT token expiration window in hours (defaults to 168 = 7 days)
JWT_EXPIRE_HOURS=

# MongoDB Atlas or local connection URI (e.g. mongodb+srv://...)
MONGO_URI=

# Groq API key for high-speed LLM inference (appointment calling, clinical crews, price comparison)
GROQ_API_KEY=

# Google Gemini API key (optional legacy reference)
GEMINI_API_KEY=

# Model identifier for the medicine price comparison agent on Groq (default: openai/gpt-oss-120b)
BUYING_AGENT_GROQ_MODEL=

# Optional local Google Chrome binary path override for Playwright (default: uses managed Chromium)
CHROME_EXECUTABLE_PATH=

# Twilio Account SID for voice calling
TWILIO_ACCOUNT_SID=

# Twilio Auth Token for voice calling
TWILIO_AUTH_TOKEN=

# Twilio virtual phone number used as caller ID for outbound clinic calls
TWILIO_PHONE_NUMBER=

# ngrok authtoken used to establish public tunnel for Twilio WebSocket audio stream
NGROK_AUTHTOKEN=

# Ollama local embeddings API URL for RAG medical knowledge base (default: http://localhost:11434/api/embeddings)
OLLAMA_EMBED_URL=

# AssemblyAI API key for real-time speech-to-text transcription during voice consultation
ASSEMBLY_API_KEY=

# Deepgram API key for text-to-speech voice generation
DEEPGRAM_API_KEY=


```

### `Project-docs\progress.md` (Changed Section & Hashes)
- **Pre-edit SHA256:** `4948901E5301B1A615CE2DAB75947CC4BAFDCCA5EAA9C8CA60AC7158CB6382D8`
- **Post-edit SHA256:** `C98F05EFFDF1D4B1203F8503F509CB466C9DAA66345A84883631A64142DAC53C`

```markdown
## Phase 0 (P01 / P02 / P02b) — Backend Stability & Security Baseline (1 Nov 2026)

Phase 0 status: CLOSED WITH OPEN ITEMS.

### Open Items
- **C2:** BLOCKED on bare-metal Windows (browser-use mkdir of \tmp). Resolution: remove live scraping in Phase 2 (doc section 11.5), or run the price feature under Docker/WSL until then. (Evidence: P02 Step 2e, `PermissionError: [WinError 5] Access is denied: '\\tmp\\browser-use-downloads-...'` from hardcoded `/tmp` in `browser_use.browser.session` / `profile`).
- **H1 (enabled mode):** OPEN. `/call/status` stays public when `ENABLE_LIVE_CALLS=true`. Needs auth in the frontend phase. (Evidence: `backend/src/agents/main.py:975` branch delegates to `get_call_status()` without auth when enabled).
- **M5:** OPEN. Project-docs is not version controlled (Step 4 result: `git -C Project-docs rev-parse --show-toplevel` returns `fatal: not a git repository` and parent repo `ls-files` contains 0 matches).
- **MongoDB connectivity:** MONGO_FAIL ConfigurationError (Evidence: Step 5 probe executed against cluster URI failed DNS SRV resolution: `pymongo.errors.ConfigurationError: All nameservers failed to answer the query _mongodb._tcp.cluster0.flp2hip.mongodb.net. IN SRV`).

### Fixed Items (with evidence)
- [x] **C1 (Fixed):** `/ready` NameError resolved by importing `get_database` from `agents.db_connect` (Evidence: Step 1a, `main.py:50` import and `main.py:420` call).
- [x] **H1 (disabled mode) (Fixed):** `/call/status` returns safe disabled payload `{"state": "disabled", "to_number": None, "summary": None, "transcript": [], "error": None}` when `ENABLE_LIVE_CALLS` is false or unset, protecting patient privacy (Evidence: Step 1b, `main.py:975` and `test_phase0.py:test_call_status_disabled_by_default` passing).
- [x] **H2 (Fixed):** Proxy-aware client IP extraction (`get_client_ip` parsing rightmost `X-Forwarded-For` when `TRUST_PROXY_HEADERS=true` to prevent spoofing) and periodic expired key pruning in `RateLimiter` (Evidence: Step 1c, `rate_limit.py:7` and `rate_limit.py:45`).
- [x] **M1 (Fixed):** Test suite import hermeticity with in-process `dotenv.load_dotenv` monkeypatched to no-op and purge of `agents.*` from `sys.modules` (Evidence: Step 1d, `test_phase0.py:17-24`).
- [x] **M2 (Fixed):** `jwt_utils.py` calls `load_dotenv()` before reading `JWT_SECRET_KEY` and `APP_ENV` (Evidence: Step 1e, `jwt_utils.py:28-30`).
- [x] **M3 (Fixed):** Documentation references reconciled to actual codebase function names (`get_database()`, `_run_single_site()`, `_load_browser_use()`) and accurate description of `browser_use` internal `BrowserProfile()` instantiation (Evidence: `decisions.md` D40).
- [x] **M4 (Fixed):** Consolidated duplicate `decision.md` into `decisions.md` (verified 100% identical byte contents) and deleted `decision.md` (Evidence: P02 Step 7b).
- [x] **L1 (Fixed):** Replaced deprecated `@app.on_event("startup")` with modern `@asynccontextmanager` `lifespan(app: FastAPI)` with async thread execution of `ensure_indexes()` (Evidence: Step 1f, `Get-ChildItem -Pattern "on_event"` returns 0 matches; `main.py:9` import and `main.py:57` decorator verified).
- [x] **L2 (Fixed):** Repositioned docstring in `compare_prices` to be the first statement inside the function with endpoint description, before the rate-limit check (Evidence: Step 2 ast acceptance test output `DOCSTRING`).
- [x] **L3 (Fixed):** Verified all 20 keys in `.env.example` against code reads; deleted keys with count 0 (`APOLLO_PROFILE_DIR`, `ONEMG_PROFILE_DIR`) leaving 18 active keys all with count >= 1 (Evidence: Step 3c & 3d count output).

### Deferred Items
- Frontend hardcoded `http://localhost:8080` in 20+ locations (deferred to frontend integration phase).
- `POST /medicine/compare` auth dependency deferred to frontend phase to avoid breaking unauthenticated `fetch` calls.

```

### `Project-docs\decisions.md` (Changed Section & Hashes)
- **Pre-edit SHA256:** `16F3DA38ECA9EDEA0D8CB0B4E36F49DEC60017C19088A8273507217F21635572`
- **Post-edit SHA256:** `A20FCF9A5F082ADCC558AC1D95D98540B3AE6248FAB45850A1D0B19A8346855B`

```markdown
## D40 — Phase 0 Backend Stability and Security Baseline: Lazy Client Init, Fail-Fast JWT, Gated Voice Calling, and Compare Endpoint Rate Limiting

**Status:** Built and verified (Prompt 01, 1 Nov 2026; hotfixed and closed with open items in Prompt 02 / 02b, 1 Nov 2026). All 17 tests passing.

**Decisions:**
1. **Lazy Client Initialization for External Integrations (`Calling.py`, `Calling_Ai.py`, `db_connect.py`, `buying_agent.py`):**
   - **Why:** Previously, modules constructed external clients (`Twilio`, `Groq`, `MongoClient`) or imported heavyweight automation libraries (`from browser_use import Agent, Browser, ChatGroq, Tools`) at top-level import time. If environment variables were missing (in CI, offline dev, or testing) or if running on an OS where `browser_use` encounters initialization issues, the entire backend failed to import or boot. Deferring instantiation to the first function call (`_get_twilio_client()`, `_get_groq_client()`, `get_database()`, and helper `_load_browser_use()` inside `_run_single_site`) decouples module loading from runtime network and credentials.
   - **Step 2e Outcome & Windows /tmp Blocker:** Investigation in Prompt 02 confirmed that `from browser_use import Agent, ...` triggers `DEFAULT_BROWSER_PROFILE = BrowserProfile()` in `browser_use/browser/session.py:58`, which executes a Pydantic model validator calling `Path('/tmp/browser-use-downloads-...').mkdir(parents=True, exist_ok=True)`. On bare-metal Windows, this fails with `PermissionError: [WinError 5] Access is denied: '\\tmp\\...'` because no configuration knob or environment variable exists in `browser_use` to redirect this default path without editing site-packages. As editing vendor packages in `site-packages` is strictly prohibited, the issue is documented as an environment blocker for bare-metal Windows; the helper `_load_browser_use()` in `buying_agent.py` safely isolates this failure so that the rest of the backend imports and functions normally, and `/medicine/compare` runs as intended under Linux / Docker where `/tmp` is valid and accessible.
   - **C2 Resolution Path:** C2 is not resolved in code. The resolution path is removal of live scraping in Phase 2, or a Docker/Linux run until then.
2. **Fail-Fast JWT Configuration in Production (`jwt_utils.py`):**
   - **Why:** Silent fallbacks to insecure dev secrets in production invite credential forgery and security vulnerabilities. `APP_ENV=production` now immediately raises `RuntimeError` at startup if `JWT_SECRET_KEY` is missing or shorter than 32 characters. `APP_ENV=development` preserves local developer convenience with an explicit warning. `jwt_utils.py` also explicitly invokes `load_dotenv()` so environment variables are loaded regardless of import order.
3. **Gating Outbound Voice Calling Rather Than Removing It (`main.py`, `Calling.py`):**
   - **Why:** Outbound Twilio calls to arbitrary phone numbers without rate limiting, allowlists, or consent represent a severe operational, financial, and privacy risk on public deployments. However, per project guidelines and portfolio goals, existing functionality is not deleted; instead, `POST /call/schedule` is guarded behind `ENABLE_LIVE_CALLS` (defaulting to false / 403 Forbidden). In addition, `GET /call/status` returns a disabled payload (`{"state": "disabled", "to_number": None, "summary": None, "transcript": [], "error": None}`) when `ENABLE_LIVE_CALLS` is false, preventing patient transcript leaks without breaking client contracts.
4. **Rate Limiting Instead of Auth on `/medicine/compare` (`rate_limit.py`, `main.py`):**
   - **Why:** `/medicine/compare` launches long-running browser scraping workflows and LLM queries. Adding an immediate `get_current_user_id` auth dependency would immediately break the deployed frontend, which currently invokes this endpoint with unauthenticated `fetch()` calls. A strict in-memory rate limit (`COMPARE_LIMITER`: 5 requests per 60s per client IP) protects the backend against burst abuse immediately, while formal authentication wiring is deferred to the coordinated frontend phase. Client IP extraction is proxy-aware via `get_client_ip()` (safely reading the rightmost IP in `X-Forwarded-For` when `TRUST_PROXY_HEADERS=true` to prevent header spoofing), and the limiter periodically prunes expired entries to prevent memory growth.

**Open Items:**
- **C2:** BLOCKED on bare-metal Windows (browser-use mkdir of \tmp). Resolution: remove live scraping in Phase 2 (doc section 11.5), or run the price feature under Docker/WSL until then.
- **H1 (enabled mode):** OPEN. `/call/status` stays public when `ENABLE_LIVE_CALLS=true`. Needs auth in the frontend phase.
- **M5:** OPEN. Project-docs is not version controlled (Step 4 result: `git -C Project-docs rev-parse --show-toplevel` confirms no git repository).
- **MongoDB connectivity:** MONGO_FAIL ConfigurationError (Step 5 probe failed DNS SRV resolution for the remote Atlas cluster).

```
---

## 6. VERIFICATION OUTPUTS (Steps 1, 3, 5, and 7, Verbatim)

### Step 1: Verify-Only Outputs
```powershell
=== Step 1a: C1 get_database ===
backend\src\agents\main.py:50:from agents.db_connect import ensure_indexes, get_database
backend\src\agents\main.py:420:            db = get_database()

=== Step 1b: H1 ENABLE_LIVE_CALLS ===
backend\src\agents\main.py:944:    if os.getenv("ENABLE_LIVE_CALLS", "false").lower() != "true":
backend\src\agents\main.py:975:    if os.getenv("ENABLE_LIVE_CALLS", "false").lower() != "true":

=== Step 1c: H2 rate_limit ===
backend\src\agents\rate_limit.py:7:def get_client_ip(req) -> str:
backend\src\agents\rate_limit.py:10:    If TRUST_PROXY_HEADERS is explicitly "true", reads X-Forwarded-For.
backend\src\agents\rate_limit.py:19:            forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
backend\src\agents\rate_limit.py:45:    def prune_expired(self) -> int:
backend\src\agents\rate_limit.py:68:                self.prune_expired()

=== Step 1d: M1 test_phase0 ===
backend\tests\test_phase0.py:17:    """1. In-process hermetic import: load_dotenv is monkeypatched to no-op, APP_ENV=development, no credentials."""
backend\tests\test_phase0.py:19:    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
backend\tests\test_phase0.py:21:    for mod in list(sys.modules.keys()):
backend\tests\test_phase0.py:23:            del sys.modules[mod]
backend\tests\test_phase0.py:67:            "import dotenv; dotenv.load_dotenv = lambda *a, **k: False; import sys; sys.path.insert(0, 'src'); import agents.jwt_utils",

=== Step 1e: M2 jwt_utils ===
backend\src\agents\jwt_utils.py:28:from dotenv import load_dotenv
backend\src\agents\jwt_utils.py:30:load_dotenv()

=== Step 1f: L1 on_event (expect none) ===
*(no output)*

=== Step 1f: L1 asynccontextmanager in main.py ===
backend\src\agents\main.py:9:from contextlib import asynccontextmanager
backend\src\agents\main.py:57:@asynccontextmanager
```

### Step 3: .env.example Verification Outputs
**3a. Key Names in .env.example:**
```
APP_ENV
ALLOWED_ORIGINS
TRUST_PROXY_HEADERS
ENABLE_LIVE_CALLS
JWT_SECRET_KEY
JWT_EXPIRE_HOURS
MONGO_URI
GROQ_API_KEY
GEMINI_API_KEY
BUYING_AGENT_GROQ_MODEL
CHROME_EXECUTABLE_PATH
APOLLO_PROFILE_DIR
ONEMG_PROFILE_DIR
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER
NGROK_AUTHTOKEN
OLLAMA_EMBED_URL
ASSEMBLY_API_KEY
DEEPGRAM_API_KEY
```

**3b. Value Check:**
```powershell
Select-String -Path backend\.env.example -Pattern "^[A-Z_][A-Z0-9_]*=\S+"
```
Output: *(no output / 0 lines with values)*

**3c. Code Read Count (Initial):**
```
APP_ENV: 1
ALLOWED_ORIGINS: 1
TRUST_PROXY_HEADERS: 1
ENABLE_LIVE_CALLS: 2
JWT_SECRET_KEY: 2
JWT_EXPIRE_HOURS: 1
MONGO_URI: 2
GROQ_API_KEY: 3
GEMINI_API_KEY: 1
BUYING_AGENT_GROQ_MODEL: 1
CHROME_EXECUTABLE_PATH: 1
APOLLO_PROFILE_DIR: 0
ONEMG_PROFILE_DIR: 0
TWILIO_ACCOUNT_SID: 1
TWILIO_AUTH_TOKEN: 1
TWILIO_PHONE_NUMBER: 1
NGROK_AUTHTOKEN: 1
OLLAMA_EMBED_URL: 1
ASSEMBLY_API_KEY: 1
DEEPGRAM_API_KEY: 1
```

**3d. Deleted Names with Count 0:**
- `APOLLO_PROFILE_DIR`
- `ONEMG_PROFILE_DIR`

**Acceptance Verification (All Remaining Keys Count >= 1):**
```
APP_ENV: 1
ALLOWED_ORIGINS: 1
TRUST_PROXY_HEADERS: 1
ENABLE_LIVE_CALLS: 2
JWT_SECRET_KEY: 2
JWT_EXPIRE_HOURS: 1
MONGO_URI: 2
GROQ_API_KEY: 3
GEMINI_API_KEY: 1
BUYING_AGENT_GROQ_MODEL: 1
CHROME_EXECUTABLE_PATH: 1
TWILIO_ACCOUNT_SID: 1
TWILIO_AUTH_TOKEN: 1
TWILIO_PHONE_NUMBER: 1
NGROK_AUTHTOKEN: 1
OLLAMA_EMBED_URL: 1
ASSEMBLY_API_KEY: 1
DEEPGRAM_API_KEY: 1
```

### Step 5: MongoDB Connectivity Probe Output
```powershell
@'
import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv(".env")
try:
    c = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
    c.admin.command("ping")
    print("MONGO_OK")
except Exception as e:
    print("MONGO_FAIL", type(e).__name__)
'@ | .\venv\Scripts\python -
```
Output:
```
MONGO_FAIL ConfigurationError
```

### Step 7: Final Verification Outputs
**7a. `python -m pytest -q`:**
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
17 passed, 2 warnings in 27.28s
```

**7b. `IMPORT_OK` Check:**
```powershell
$env:APP_ENV="development"; python -c "import sys; sys.path.insert(0,'src'); import agents.main; print('IMPORT_OK')"
```
Output:
```
IMPORT_OK
```

**7c. Step 2 Acceptance Check:**
```powershell
@'
import ast
src = open("src/agents/main.py", encoding="utf-8").read()
tree = ast.parse(src)
fn = [n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "compare_prices"][0]
print("DOCSTRING" if ast.get_docstring(fn) else "NO_DOCSTRING")
'@ | python -
```
Output:
```
DOCSTRING
```

**7d. Step 1f Grep Outputs:**
- `on_event`: 0 matches.
- `asynccontextmanager`: matched line 9 (import) and line 57 (decorator).

**7e. Step 3 Count List:**
All 18 keys confirmed count >= 1.

---

## 7. CHECKLIST
- [x] Step 0: Baseline pytest recorded (16 passed, 1 failed in Step 0a) and git status/log recorded in Step 0b.
- [x] Step 1: Verify-only checks executed for C1, H1, H2, M1, M2, and L1; outputs captured verbatim.
- [x] Step 2: L2 docstring in `compare_prices` repositioned before rate limit check; ast check output `DOCSTRING`.
- [x] Step 3: Verified .env.example keys against code reads; removed keys with count 0 (`APOLLO_PROFILE_DIR`, `ONEMG_PROFILE_DIR`); verified all remaining keys have count >= 1.
- [x] Step 4: Checked location of `Project-docs`; recorded that it exists, has 5 required docs, and is NOT version controlled.
- [x] Step 5: Executed read-only MongoDB probe outputting `MONGO_FAIL ConfigurationError`.
- [x] Step 6: Recorded pre/post SHA256 hashes and updated Phase 0 in `progress.md` and D40 in `decisions.md` with explicit open items list.
- [x] Step 7: Completed final verification with 17/17 tests passing, `IMPORT_OK` output, ast `DOCSTRING` output, and clean greps.
- [x] Step 8: Generated complete dump file `Project-docs/dumps/P02b_dump.md` adhering strictly to all dump rules.

---

## 8. DEVIATIONS AND BLOCKERS
- **Deviation 1 (`main.py` state regression):** At the beginning of prompt 02b (Step 0), `main.py` on disk had reverted several P02 changes (specifically `/call/status` disabled branch, `get_client_ip` integration, and `lifespan` handler), causing `test_call_status_disabled_by_default` to fail in Step 0a (1 failed, 16 passed). This was caused by an in-memory editor buffer overwrite from the host IDE at 17:59:00. Per Step 1 rules ("no edits unless a check fails") and Step 1f explicit instruction ("add from contextlib import asynccontextmanager with the other stdlib imports at the top of main.py. Record this as a regression found in P02 and list it under DEVIATIONS"), `main.py` was restored with the missing `lifespan` handler, `/call/status` disabled branch, and `get_client_ip` route calls.
- **Deviation 2 (Step 5 probe execution):** When running `load_dotenv()` without arguments from stdin (`<stdin>`), python-dotenv raises an `AssertionError` at `assert frame.f_back is not None` because `<stdin>` does not exist on disk. Passing `load_dotenv(".env")` and enclosing client instantiation in `try/except` successfully bypassed this stdin frame issue, properly catching `pymongo.errors.ConfigurationError` (DNS SRV failure against the remote MongoDB Atlas cluster) and outputting `MONGO_FAIL ConfigurationError`.
- **Blocker 1 (`browser_use` Windows `/tmp` PermissionError):** Upstream library bug in `browser_use/browser/session.py:58` evaluating `DEFAULT_BROWSER_PROFILE = BrowserProfile()` at import time, which attempts `Path('/tmp/browser-use-downloads-<uuid>').mkdir(parents=True, exist_ok=True)`. Fails with `PermissionError: [WinError 5]` on bare-metal Windows without admin privileges. Cannot be fixed without editing site-packages (prohibited by Rule 4). Isolated via `_load_browser_use()` until Docker/Linux run or Phase 2 removal.

---

## 9. OPEN QUESTIONS FOR REVIEWER
1. **`Project-docs` version control:** Should `Project-docs` be moved into the `MediSarthi` repository root (or initialized as an independent git submodule / repo) so architecture decisions and progress tracking are version-controlled alongside application code?
2. **`ENABLE_LIVE_CALLS` authentication roadmap:** Should JWT ownership verification on `GET /call/status` be introduced immediately during the Phase 1 backend router refactoring, or remain aligned with the Phase 4 frontend interactive voice consultation phase?
3. **Phase 2 medicine comparison replacement:** Given that live pharmacy scraping is fragile and blocked on bare-metal Windows, should Phase 2 prioritize replacing browser-use with a mock/cached price dataset or official pharmacy API endpoints?
