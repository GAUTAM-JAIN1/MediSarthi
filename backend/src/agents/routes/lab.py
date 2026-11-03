import os
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from agents.jwt_utils import get_current_user_id, verify_owner
from agents.errors import _server_error
from agents.schemas import SaveLabReportAnalysisRequest
from agents.file_utils import save_upload_file, extract_text_from_lab_document
from agents.crew import LabReportCrew
from agents.llm_output import first_pydantic_dict
from agents.health_records import (
    save_lab_report_analysis,
    get_lab_report_analyses,
    delete_lab_report_analysis,
    get_test_trends,
    get_annotated_trends,
)

router = APIRouter()


@router.post("/lab/analyse")
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

        analysis_dict = first_pydantic_dict(result) or {}

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


@router.post("/lab/save")
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


@router.get("/lab/analyses/{user_id}")
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


@router.delete("/lab/analyses/{user_id}/{analysis_id}")
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


@router.get("/health/trends/{user_id}")
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


@router.get("/health/trends-annotated/{user_id}")
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

