from fastapi import APIRouter, HTTPException, Depends
from agents.jwt_utils import get_current_user_id, verify_owner
from agents.errors import _server_error
from agents.schemas import DonorRegisterRequest, DonationRequestBody, FindDonorsRequest
from agents.donor import (
    register_donor,
    get_donor_by_user_id,
    record_donation,
    toggle_availability,
    create_donation_request,
    find_matching_donors,
)

router = APIRouter()


@router.post("/donor/register")
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
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as e:
        raise _server_error(e)


@router.get("/donor/{user_id}")
def donor_profile(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        return {"donor": get_donor_by_user_id(user_id)}
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as e:
        raise _server_error(e)


@router.post("/donor/{user_id}/record-donation")
def donor_record_donation(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        return {"donor": record_donation(user_id)}
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as e:
        raise _server_error(e)


@router.post("/donor/{user_id}/availability")
def donor_availability(
    user_id: str,
    available: bool,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        return {"donor": toggle_availability(user_id, available)}
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as e:
        raise _server_error(e)


@router.post("/donor/request/create")
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
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as e:
        raise _server_error(e)


@router.post("/donor/request/find-donors")
def donor_find_matching(
    request: FindDonorsRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    """No user_id on this request — only "must be logged in" is enforced."""
    try:
        donors = find_matching_donors(request.blood_group, request.city, request.state)
        return {"donors": donors, "count": len(donors)}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as e:
        raise _server_error(e)

