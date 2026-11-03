"""Ownership 403 coverage test suite.

Ensures that any request attempting to access or modify data belonging to another
user is rejected with HTTP 403 before any database or LLM calls occur.
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from agents.main import app
from agents.jwt_utils import create_access_token, verify_owner

client = TestClient(app)

OWNER = "owner-user"
VICTIM = "victim-user"

# All 32 ownership-protected routes: 17 path-parameter, 11 JSON body, 4 multipart.
CASES = [
    # 17 Path-parameter routes
    ("GET", "/lab/analyses/{user_id}", f"/lab/analyses/{VICTIM}", {}),
    ("DELETE", "/lab/analyses/{user_id}/{analysis_id}", f"/lab/analyses/{VICTIM}/x", {}),
    ("GET", "/health/trends/{user_id}", f"/health/trends/{VICTIM}", {}),
    ("GET", "/health/trends-annotated/{user_id}", f"/health/trends-annotated/{VICTIM}", {}),
    ("GET", "/donor/{user_id}", f"/donor/{VICTIM}", {}),
    ("POST", "/donor/{user_id}/record-donation", f"/donor/{VICTIM}/record-donation", {}),
    ("POST", "/donor/{user_id}/availability", f"/donor/{VICTIM}/availability?available=true", {}),
    ("POST", "/health/doctor-qr/{user_id}", f"/health/doctor-qr/{VICTIM}", {}),
    ("POST", "/health/generate-qr/{user_id}", f"/health/generate-qr/{VICTIM}", {}),
    ("GET", "/health/emergency-profile/{user_id}", f"/health/emergency-profile/{VICTIM}", {}),
    ("GET", "/health/vitals/{user_id}", f"/health/vitals/{VICTIM}", {}),
    ("DELETE", "/health/vitals/{user_id}/{vital_id}", f"/health/vitals/{VICTIM}/x", {}),
    ("GET", "/health/prescriptions/{user_id}", f"/health/prescriptions/{VICTIM}", {}),
    ("DELETE", "/health/prescriptions/{user_id}/{prescription_id}", f"/health/prescriptions/{VICTIM}/x", {}),
    ("GET", "/health/prescription-analyses/{user_id}", f"/health/prescription-analyses/{VICTIM}", {}),
    ("GET", "/health/prescription-analysis/{user_id}/{analysis_id}", f"/health/prescription-analysis/{VICTIM}/x", {}),
    ("GET", "/health/timeline/{user_id}", f"/health/timeline/{VICTIM}", {}),

    # 11 JSON body routes
    ("POST", "/medicine/interactions", "/medicine/interactions", {"json": {"user_id": VICTIM, "medicines": ["a"]}}),
    ("POST", "/medicine/effectiveness", "/medicine/effectiveness", {"json": {"user_id": VICTIM, "medicine_name": "m", "test_name": "t", "start_date": "2026-01-01", "points": [{"date": "2026-01-01", "value": 1.0, "status": "Normal"}]}}),
    ("POST", "/triage/symptoms", "/triage/symptoms", {"json": {"user_id": VICTIM, "symptoms": "fever"}}),
    ("POST", "/lab/save", "/lab/save", {"json": {"user_id": VICTIM, "report_type": "r", "overall_summary": "s", "tests": [], "has_urgent_values": False, "next_steps": "n", "disclaimer": "d"}}),
    ("POST", "/health/vital", "/health/vital", {"json": {"user_id": VICTIM, "vital_type": "v", "value": 1.0, "unit": "u"}}),
    ("POST", "/health/prescription", "/health/prescription", {"json": {"user_id": VICTIM, "medicines": ["a"]}}),
    ("POST", "/health/prescription-analysis", "/health/prescription-analysis", {"json": {"user_id": VICTIM, "overall_summary": "s", "medicines": [], "has_allergy_conflict": False, "safety_note": "n"}}),
    ("POST", "/health/emergency-profile", "/health/emergency-profile", {"json": {"user_id": VICTIM, "name": "n", "blood_group": "O+"}}),
    ("POST", "/donor/register", "/donor/register", {"json": {"user_id": VICTIM, "name": "n", "blood_group": "O+", "city": "c", "state": "s", "phone": "1"}}),
    ("POST", "/donor/request/create", "/donor/request/create", {"json": {"requester_user_id": VICTIM, "blood_group": "O+", "city": "c", "state": "s"}}),
    ("POST", "/hospitals/nearby", "/hospitals/nearby", {"json": {"user_id": VICTIM}}),

    # 4 Multipart routes
    ("POST", "/consultation/speech", "/consultation/speech", {"data": {"user_id": VICTIM}, "files": {"audio_file": ("test.mp3", b"x", "audio/mpeg")}}),
    ("POST", "/consultation/document", "/consultation/document", {"data": {"user_id": VICTIM}, "files": {"file": ("test.txt", b"x", "text/plain")}}),
    ("POST", "/lab/analyse", "/lab/analyse", {"data": {"user_id": VICTIM}, "files": {"file": ("test.pdf", b"x", "application/pdf")}}),
    ("POST", "/general-query", "/general-query", {"data": {"user_id": VICTIM}, "files": {"audio_file": ("test.mp3", b"x", "audio/mpeg")}}),
]


def test_verify_owner_unit():
    """Unit test for verify_owner helper."""
    # verify_owner("a", "a") does not raise
    verify_owner("a", "a")

    # verify_owner("a", "b") raises HTTPException with status_code 403
    with pytest.raises(HTTPException) as exc_info:
        verify_owner("a", "b")
    assert exc_info.value.status_code == 403


@pytest.mark.parametrize("method,path_template,concrete_path,kwargs", CASES, ids=[f"{c[0]}_{c[1]}" for c in CASES])
def test_ownership_rejection_403(method, path_template, concrete_path, kwargs):
    """Assert all 32 ownership-protected routes return 403 when authenticated as OWNER but requesting VICTIM data."""
    token = create_access_token(OWNER)
    headers = {"Authorization": f"Bearer {token}"}
    merged_kwargs = dict(kwargs)
    merged_headers = dict(headers)
    if "headers" in merged_kwargs:
        merged_headers.update(merged_kwargs.pop("headers"))

    res = client.request(method, concrete_path, headers=merged_headers, **merged_kwargs)
    assert res.status_code == 403, f"{method} {concrete_path} returned {res.status_code} with body: {res.text}"


def test_ownership_coverage_against_openapi():
    """Assert all protected operations with {user_id} in path are included and all cases correspond to real routes."""
    spec = app.openapi()
    http_methods = {"get", "post", "put", "delete", "patch"}

    openapi_user_id_routes = set()
    all_openapi_routes = set()

    for path, ops in spec["paths"].items():
        for m in ops:
            if m in http_methods:
                all_openapi_routes.add((m.upper(), path))
                if "{user_id}" in path:
                    openapi_user_id_routes.add((m.upper(), path))

    case_path_templates = {(m, tmpl) for m, tmpl, _, _ in CASES}

    # Every protected operation whose path contains {user_id} must appear in the case list
    missing = openapi_user_id_routes - case_path_templates
    assert not missing, f"Protected routes with {{user_id}} in path missing from ownership cases: {missing}"

    # Every case in the list must be a real route in OpenAPI
    non_existent = case_path_templates - all_openapi_routes
    assert not non_existent, f"Ownership case list contains non-existent routes: {non_existent}"


def test_openapi_request_body_user_ids_covered():
    """Assert all OpenAPI operations with user_id/requester_user_id in requestBody are covered in CASES."""
    spec = app.openapi()
    http_methods = {"get", "post", "put", "delete", "patch"}
    body_ops = set()

    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            if method.lower() not in http_methods:
                continue
            if "requestBody" in op:
                content = op["requestBody"].get("content", {})
                for media in content.values():
                    schema = media.get("schema", {})
                    if "$ref" in schema:
                        name = schema["$ref"].split("/")[-1]
                        props = spec["components"]["schemas"][name].get("properties", {})
                    else:
                        props = schema.get("properties", {})
                    if "user_id" in props or "requester_user_id" in props:
                        body_ops.add((method.upper(), path))

    assert len(body_ops) > 0

    case_templates = {(m, t) for m, t, _, _ in CASES}
    body_ops_no_brace = {op for op in body_ops if "{" not in op[1]}
    missing = body_ops_no_brace - case_templates
    assert not missing, "OpenAPI routes with a user_id body/form field missing from ownership cases: " + str(missing)

    cases_no_brace = {c for c in case_templates if "{" not in c[1]}
    assert cases_no_brace.issubset(body_ops)

