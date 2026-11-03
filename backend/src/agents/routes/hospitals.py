from fastapi import APIRouter, HTTPException, Depends
from agents.jwt_utils import get_current_user_id, verify_owner
from agents.errors import _server_error
from agents.schemas import LocationRequest
from agents.auth import get_user_by_id
from agents.crew import Nearbyhospitals
from agents.hospital_parser import parse_hospital_list

router = APIRouter()


@router.post("/hospitals/nearby")
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

