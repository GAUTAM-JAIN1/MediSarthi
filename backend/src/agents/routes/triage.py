from fastapi import APIRouter, HTTPException, Depends
from agents.jwt_utils import get_current_user_id, verify_owner
from agents.errors import _server_error
from agents.schemas import SymptomTriageRequest
from agents.safety_guardrails import check_emergency
from agents.crew import SymptomTriageCrew
from agents.llm_output import first_pydantic_dict

router = APIRouter()


@router.post("/triage/symptoms")
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

        triage_dict = first_pydantic_dict(result) or {}

        if not triage_dict:
            triage_dict = {"raw": result.raw}

        return {"triage": triage_dict}
    except Exception as e:
        raise _server_error(e)

