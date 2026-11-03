#!/usr/bin/env python

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.config import allowed_origins, validate_startup
from agents.request_context import RequestIdMiddleware, install_log_record_factory
from agents.db_connect import ensure_indexes
from agents.errors import _server_error  # noqa: F401

from agents.routes import (
    system,
    auth,
    consultation,
    lab,
    medicine,
    triage,
    emergency,
    doctor_qr,
    calls,
    hospitals,
    donor,
    health_records,
)

install_log_record_factory()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """(D33) Ensures the doctor_qr_tokens TTL index exists. Idempotent."""
    validate_startup()
    try:
        await asyncio.to_thread(ensure_indexes)
    except Exception as e:
        logger.warning(f"Startup ensure_indexes skipped (DB unreachable): {e}")
    yield


app = FastAPI(title="Medical Agent API", version="1.0", lifespan=lifespan)

ALLOWED_ORIGINS = allowed_origins()

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(auth.router)
app.include_router(consultation.router)
app.include_router(lab.router)
app.include_router(medicine.router)
app.include_router(triage.router)
app.include_router(emergency.router)
app.include_router(doctor_qr.router)
app.include_router(calls.router)
app.include_router(hospitals.router)
app.include_router(donor.router)
app.include_router(health_records.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
