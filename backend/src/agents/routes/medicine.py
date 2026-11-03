from fastapi import APIRouter, HTTPException, Depends, Request
from agents.jwt_utils import get_current_user_id, verify_owner
from agents.errors import _server_error
from agents.schemas import MedicineInteractionRequest, MedicineEffectivenessRequest, MedicineComparisonRequest
from agents.rate_limit import COMPARE_LIMITER, get_client_ip
from agents.price_lookup import run_comparison
from agents.crew import MedicineInteractionCrew, MedicineEffectivenessCrew
from agents.llm_output import first_pydantic_dict

router = APIRouter()


@router.post("/medicine/interactions")
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

        interaction_dict = first_pydantic_dict(result) or {}

        if not interaction_dict:
            interaction_dict = {"raw": result.raw}

        return {"interactions": interaction_dict}
    except Exception as e:
        raise _server_error(e)


@router.post("/medicine/effectiveness")
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

        effectiveness_dict = first_pydantic_dict(result) or {}

        if not effectiveness_dict:
            effectiveness_dict = {"raw": result.raw}

        return {"effectiveness": effectiveness_dict}
    except Exception as e:
        raise _server_error(e)


@router.post("/medicine/compare")
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

