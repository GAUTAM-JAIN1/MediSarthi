from typing import List, Optional
from pydantic import BaseModel


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

