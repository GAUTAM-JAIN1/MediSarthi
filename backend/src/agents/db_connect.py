from pymongo import MongoClient

import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
def get_database():
    client = MongoClient(MONGO_URI)
    db = client["medical_db"]
    return db


def ensure_indexes():
    """
    (D33 — Doctor Visit QR token cleanup) Ensures the doctor_qr_tokens
    collection has a TTL index on `expires_at`, so MongoDB itself deletes
    expired tokens in the background — no manual cleanup job needed.

    `expireAfterSeconds=0` means: delete the document once the CURRENT time
    passes the exact value stored in `expires_at` (as opposed to N seconds
    after document creation — we already store the precise expiry moment
    itself in that field, so 0 is correct here).

    Requires `expires_at` to be a native BSON Date (Python datetime), not a
    string — MongoDB's TTL monitor silently ignores string-typed fields.
    See health_records.py's create_doctor_qr_token()/get_doctor_qr_snapshot()
    for the corresponding storage-type fix.

    Safe to call on every app startup — create_index() is idempotent; if an
    index with the same key+options already exists, MongoDB no-ops.
    """
    db = get_database()
    db["doctor_qr_tokens"].create_index("expires_at", expireAfterSeconds=0)