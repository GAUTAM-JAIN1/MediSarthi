#!/usr/bin/env python

import sys
import os
import re
import shutil
import asyncio
import threading
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import existing logic
from agents.crew import (
    SpeechCrew, FileCrew, Nearbyhospitals, general_que,
    LabReportCrew, MedicineInteractionCrew, SymptomTriageCrew
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
)
from agents.donor import (
    register_donor, get_donor_by_user_id, record_donation,
    toggle_availability, create_donation_request, find_matching_donors
)
from PIL import Image
import pytesseract


# Initialize FastAPI
app = FastAPI(title="Medical Agent API", version="1.0")

# Allow CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Pydantic Models --------------------------------------------------------

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
    patient_name: str = ""   # NEW - passed directly from frontend form
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


# NEW - Save lab report analysis (permission-gated, same pattern as prescription analysis)
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


# NEW - Medicine interaction check request
class MedicineInteractionRequest(BaseModel):
    user_id: str
    medicines: List[str]


# NEW - Symptom triage request
class SymptomTriageRequest(BaseModel):
    user_id: str
    symptoms: str


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


# ---- Helper Functions --------------------------------------------------------

def save_upload_file(upload_file: UploadFile, destination: str):
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()


def extract_text_from_image(image_path: str) -> str:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang='eng')
    return text


def parse_hospital_list(raw_text: str) -> List[dict]:
    """
    Fixes the "hospitals blank in frontend" bug.

    Nearbyhospitals' crew.kickoff() returns a CrewOutput whose .raw is a
    markdown bullet list. The frontend expects `hospitals` to be a JSON
    array of {name, address, phone, maps_url} objects so it can `.map()`
    over them - handing it the raw CrewOutput (or even just the markdown
    string) makes `.map()` throw and the whole section renders blank with
    no visible error.

    IMPORTANT - the exact markdown style is NOT stable across LLM providers.
    Formats observed from this same crew so far:

      Current locked format (hospital_task.yaml now explicitly enforces this,
      added when we wired phone numbers through from custom_tool.py):
        * **Civil Hospital**: NH352A, Ward 17, Jind, Haryana, 126102, India | Phone: +91-9034567890
        * **Raj Hospital**: NH709A, Bhatnagar Colony, Jind, Haryana, 126102, India | Phone: Not available

      Gemini style seen before the format was locked down (bold name, inline
      colon-separated address, no phone segment):
        *   **Govt. Hospital**: NH352A, Ward 17, Jind, Haryana, 126100, India

      Groq/Llama style seen before the format was locked down (backtick name,
      comma-separated *italic* address, no phone segment):
        * `Veterinary Hospital`, *Dhatrath, Auto Stand, Main Street, Jind, Haryana, India*

    There's also an older multi-line fallback style this was originally
    written against (name-only bullet, "Address:"/"Phone:" on following
    lines) - kept working in case the agent's phrasing ever reverts to it.

    This parser handles all of the above without caring which LLM produced
    the output - it looks for a bulleted line whose first token is a name
    wrapped in **bold** OR `backticks`, treats whatever comes after an
    optional ':' or ',' as the remainder, pulls out a trailing "| Phone: ..."
    segment if present (mapping "Not available"/"N/A"/etc. to None), strips
    wrapping *italic* markers from what's left as the address, and falls
    back to separate Address:/Phone: lines for anything left unset.
    """
    if not raw_text:
        return []

    hospitals = []
    current = None

    # Matches: "*   **Name**: rest..."  OR  "* `Name`, rest..."  OR  "*   **Name**" alone.
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
            # strip wrapping *italic* markers around the inline address, if any
            rest = re.sub(r"^\*+\s*", "", rest)
            rest = re.sub(r"\s*\*+$", "", rest)

            # Pull a trailing "| Phone: ..." (or just "Phone: ...") segment out
            # of the remainder, if the locked format produced one. Anything
            # meaning "no number on file" maps to None instead of a literal
            # string, so the frontend's `h.phone &&` checks keep working.
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


# ---- Auth Endpoints --------------------------------------------------------

@app.post("/auth/signup")
def signup(request: SignupRequest):
    try:
        profile = signup_user(
            request.name, request.age, request.gender, request.allergies,
            request.city, request.state, request.email, request.password
        )
        return {"user_id": profile["ID"], "name": profile["Name"], "user": profile}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login")
def login(request: LoginRequest):
    try:
        profile = login_user(request.email, request.password)
        return {"user_id": profile["ID"], "name": profile["Name"], "user": profile}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Health Check --------------------------------------------------------

@app.get("/")
def health_check():
    return {"status": "active", "message": "Medical Agent API is running"}


# ---- Consultation Endpoints --------------------------------------------------------

@app.post("/consultation/speech")
async def speech_consultation(audio_file: UploadFile = File(...), user_id: str = Form(...)):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    temp_filename = f"temp_{audio_file.filename}"
    try:
        save_upload_file(audio_file, temp_filename)
        statement = transcribe_audio(temp_filename)
        inputs = {"statement": f"[{timestamp}] {statement}"}

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
async def document_consultation(file: UploadFile = File(...), user_id: str = Form(...)):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    temp_filename = f"temp_{file.filename}"
    try:
        save_upload_file(file, temp_filename)
        statement = extract_text_from_image(temp_filename)
        inputs = {"statement": f"[{timestamp}] {statement}"}

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


# ---- Lab Report Analysis Endpoint --------------------------------------------------------

@app.post("/lab/analyse")
async def analyse_lab_report(file: UploadFile = File(...), user_id: str = Form(...)):
    """
    Accepts a lab report image (JPG/PNG) or PDF, extracts text via OCR,
    then runs LabReportCrew to produce a plain-language analysis.

    Returns: {report_text, analysis} where analysis is a LabReportAnalysisOutput dict.
    Analysis is NOT saved to DB until user calls /lab/save explicitly.
    """
    temp_filename = f"temp_lab_{file.filename}"
    try:
        save_upload_file(file, temp_filename)

        # Extract text - Tesseract for images, fallback for PDFs
        try:
            report_text = extract_text_from_image(temp_filename)
        except Exception:
            # If image open fails (e.g. PDF), try reading raw text as fallback
            with open(temp_filename, "r", errors="ignore") as f:
                report_text = f.read()

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
def save_lab_report(request: SaveLabReportAnalysisRequest):
    """
    Permission-gated save - called only when user explicitly taps "Save to records".
    Stores analysis in lab_report_analyses collection.
    """
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
        )
        return {"status": "saved", "record_id": record_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/lab/analyses/{user_id}")
def get_lab_analyses(user_id: str, limit: int = 20):
    """List all saved lab report analyses for a user."""
    try:
        records = get_lab_report_analyses(user_id, limit)
        return {"analyses": records, "count": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Medicine Interaction Checker Endpoint --------------------------------------------------------

@app.post("/medicine/interactions")
def check_medicine_interactions(request: MedicineInteractionRequest):
    """
    Checks a list of medicines for drug-drug interactions and allergy conflicts.
    Returns a MedicineInteractionOutput dict.
    This is a synchronous, fast endpoint - no file upload needed.
    """
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


# ---- Symptom Triage Endpoint --------------------------------------------------------

@app.post("/triage/symptoms")
def triage_symptoms(request: SymptomTriageRequest):
    """
    Takes a symptom description and returns a triage assessment:
    Home Care / See Doctor Soon / Visit Emergency.
    Fast single-agent crew - no file upload, no calendar.
    """
    if not request.symptoms or not request.symptoms.strip():
        raise HTTPException(status_code=400, detail="Symptoms describe karo.")

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


# ---- Existing Endpoints --------------------------------------------------------

@app.post("/medicine/compare")
async def compare_prices(request: MedicineComparisonRequest):
    """
    Searches each requested medicine across 1mg and Apollo Pharmacy and
    returns structured price + delivery data for every site, plus a
    best_price_site / fastest_delivery_site tag per medicine.

    IMPORTANT: this never adds anything to a cart - extraction only.
    The frontend is responsible for showing a link to the actual pharmacy
    site if the user wants to buy; nothing is purchased on the user's
    behalf at any point in this flow.
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
def schedule_call(request: CallRequest, background_tasks: BackgroundTasks):
    """
    Starts the AI calling agent in a background thread.
    The agent: starts ngrok -> places Twilio call -> does real-time conversation
    via AssemblyAI (STT) + LLM (reply) + Deepgram (TTS).

    Returns immediately - call happens asynchronously. Poll GET /call/status
    afterwards to get the live state and, once state == "completed", the
    final conversation summary.
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
    """
    Returns the shared in-memory call status set by agents/Calling.py:
    {state, to_number, summary, transcript, error}

    state is one of: idle | dialing | in_call | completed | failed.
    Frontend should poll this every few seconds after /call/schedule until
    state is "completed" or "failed", then display `summary` (and stop polling).
    """
    try:
        return get_call_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/hospitals/nearby")
def find_hospitals(location: LocationRequest):
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
async def general_health_query(audio_file: UploadFile = File(...), user_id: str = Form(...)):
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


# ---- Donor Endpoints --------------------------------------------------------

@app.post("/donor/register")
def donor_register(request: DonorRegisterRequest):
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
def donor_profile(user_id: str):
    try:
        return {"donor": get_donor_by_user_id(user_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/donor/{user_id}/record-donation")
def donor_record_donation(user_id: str):
    try:
        return {"donor": record_donation(user_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/donor/{user_id}/availability")
def donor_availability(user_id: str, available: bool):
    try:
        return {"donor": toggle_availability(user_id, available)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/donor/request/create")
def donor_request_create(request: DonationRequestBody):
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
def donor_find_matching(request: FindDonorsRequest):
    try:
        donors = find_matching_donors(request.blood_group, request.city, request.state)
        return {"donors": donors, "count": len(donors)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Health Records Endpoints --------------------------------------------------------

@app.post("/health/vital")
def health_add_vital(request: VitalRequest):
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
def health_get_vitals(user_id: str, vital_type: Optional[str] = None, limit: int = 30):
    try:
        records = get_vitals(user_id, vital_type, limit)
        return {"vitals": records, "count": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/health/prescription")
def health_add_prescription(request: PrescriptionRequest):
    try:
        record_id = add_prescription(
            request.user_id, request.medicines,
            request.symptoms, request.doctor_notes, request.source
        )
        return {"status": "saved", "record_id": record_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/prescriptions/{user_id}")
def health_get_prescriptions(user_id: str, limit: int = 20):
    try:
        records = get_prescriptions(user_id, limit)
        return {"prescriptions": records, "count": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/health/prescription-analysis")
def health_save_prescription_analysis(request: SavePrescriptionAnalysisRequest):
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
def health_get_prescription_analyses(user_id: str, limit: int = 20):
    try:
        records = get_prescription_analyses(user_id, limit)
        return {"analyses": records, "count": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/prescription-analysis/{user_id}/{analysis_id}")
def health_get_prescription_analysis_detail(user_id: str, analysis_id: str):
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
def health_get_timeline(user_id: str, limit: int = 50):
    try:
        records = get_full_timeline(user_id, limit)
        return {"timeline": records, "count": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/health/emergency-profile")
def health_save_emergency_profile(request: EmergencyProfileRequest):
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
def health_get_emergency_profile(user_id: str):
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
def health_generate_qr(user_id: str):
    try:
        token = generate_qr_token(user_id)
        qr_url = f"/health/qr/{token}"
        return {"token": token, "qr_url": qr_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/qr/{token}")
def health_qr_public(token: str):
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