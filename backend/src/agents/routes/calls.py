import threading
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from agents.config import live_calls_enabled
from agents.jwt_utils import get_current_user_id
from agents.errors import _server_error
from agents.schemas import CallRequest
from agents.Calling import start_call, get_call_status

router = APIRouter()


@router.post("/call/schedule")
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
    if not live_calls_enabled():
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


@router.get("/call/status")
def call_status():
    # When live calls are enabled, the frontend phase must add auth here because transcript is patient conversation content.
    if not live_calls_enabled():
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

