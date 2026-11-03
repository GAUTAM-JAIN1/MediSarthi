from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from agents.jwt_utils import get_current_user_id, verify_owner
from agents.errors import _server_error
from agents.schemas import VitalRequest, PrescriptionRequest, SavePrescriptionAnalysisRequest
from agents.health_records import (
    add_vital,
    get_vitals,
    delete_vital,
    add_prescription,
    get_prescriptions,
    delete_prescription,
    save_prescription_analysis,
    get_prescription_analyses,
    get_prescription_analysis_by_id,
    get_full_timeline,
)

router = APIRouter()


@router.post("/health/vital")
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


@router.get("/health/vitals/{user_id}")
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


@router.delete("/health/vitals/{user_id}/{vital_id}")
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


@router.post("/health/prescription")
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


@router.get("/health/prescriptions/{user_id}")
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


@router.delete("/health/prescriptions/{user_id}/{prescription_id}")
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


@router.post("/health/prescription-analysis")
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


@router.get("/health/prescription-analyses/{user_id}")
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


@router.get("/health/prescription-analysis/{user_id}/{analysis_id}")
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


@router.get("/health/timeline/{user_id}")
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

