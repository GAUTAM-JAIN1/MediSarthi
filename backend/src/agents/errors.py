import uuid
import logging
from fastapi import HTTPException

from agents.request_context import current_request_id

logger = logging.getLogger("agents.errors")


def _server_error(e: Exception) -> HTTPException:
    rid = current_request_id() or uuid.uuid4().hex
    logger.exception(f"Internal server error (ref: {rid}): {e}")
    return HTTPException(
        status_code=500,
        detail=f"Something went wrong. Please try again. (ref: {rid})"
    )

