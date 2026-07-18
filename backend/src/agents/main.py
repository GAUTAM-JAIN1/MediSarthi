#!/usr/bin/env python

import sys
import os
import re
import shutil
import asyncio
import threading
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
from agents.db_connect import ensure_indexes
# NEW (D34) — JWT issuance + the per-request ownership-verification dependency.
from agents.jwt_utils import create_access_token, get_current_user_id, verify_owner
from PIL import Image, ImageEnhance
import pytesseract


app = FastAPI(title="Medical Agent API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """(D33) Ensures the doctor_qr_tokens TTL index exists. Idempotent."""
    ensure_indexes()


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
def signup(request: SignupRequest):
    try:
        profile = signup_user(
            request.name, request.age, request.gender, request.allergies,
            request.city, request.state, request.email, request.password
        )
        token = create_access_token(profile["ID"])
        return {"user_id": profile["ID"], "name": profile["Name"], "user": profile, "access_token": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login")
def login(request: LoginRequest):
    try:
        profile = login_user(request.email, request.password)
        token = create_access_token(profile["ID"])
        return {"user_id": profile["ID"], "name": profile["Name"], "user": profile, "access_token": token}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Health Check (public) --------------------------------------------------

@app.get("/")
def health_check():
    return {"status": "active", "message": "Medical Agent API is running"}


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
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


# ---- Existing Endpoints ------------------------------------------------------

@app.post("/medicine/compare")
async def compare_prices(request: MedicineComparisonRequest):
    """
    NOT user-scoped (no user_id in the request today) — left unauthenticated
    for now. If abuse becomes a concern, add
    current_user_id: str = Depends(get_current_user_id) here too.
    """
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
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/call/status")
def call_status():
    try:
        return get_call_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/donor/{user_id}")
def donor_profile(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        return {"donor": get_donor_by_user_id(user_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/donor/{user_id}/record-donation")
def donor_record_donation(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        return {"donor": record_donation(user_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/donor/{user_id}/availability")
def donor_availability(
    user_id: str,
    available: bool,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        return {"donor": toggle_availability(user_id, available)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/donor/request/find-donors")
def donor_find_matching(
    request: FindDonorsRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    """No user_id on this request — only "must be logged in" is enforced."""
    try:
        donors = find_matching_donors(request.blood_group, request.city, request.state)
        return {"donors": donors, "count": len(donors)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)