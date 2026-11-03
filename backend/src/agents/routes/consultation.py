import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Depends
from agents.jwt_utils import get_current_user_id, verify_owner
from agents.errors import _server_error
from agents.file_utils import save_upload_file, extract_text_from_image
from agents.speech_to_text import transcribe_audio
from agents.safety_guardrails import check_emergency
from agents.crew import SpeechCrew, FileCrew, general_que

router = APIRouter()


@router.post("/consultation/speech")
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


@router.post("/consultation/document")
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


@router.post("/general-query")
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

