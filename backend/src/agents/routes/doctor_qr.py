from fastapi import APIRouter, HTTPException, Depends
from agents.jwt_utils import get_current_user_id, verify_owner
from agents.errors import _server_error
from agents.crew import ClinicalSummaryCrew
from agents.llm_output import first_pydantic_dict
from agents.health_records import (
    get_lab_report_analyses,
    get_annotated_trends,
    get_prescriptions,
    create_doctor_qr_token,
    get_doctor_qr_snapshot,
)

router = APIRouter()


@router.post("/health/doctor-qr/{user_id}")
def health_generate_doctor_qr(
    user_id: str,
    expiry_hours: int = 24,
    current_user_id: str = Depends(get_current_user_id),
):
    verify_owner(current_user_id, user_id)
    try:
        lab_reports = get_lab_report_analyses(user_id, limit=20)
        trends = get_annotated_trends(user_id)
        prescriptions = get_prescriptions(user_id, limit=20)

        if lab_reports:
            lab_history_lines = []
            for r in lab_reports:
                date = r.get("date", "?")[:10]
                report_type = r.get("report_type", "Unknown")
                test_lines = "; ".join(
                    f"{t.get('test_name')}: {t.get('value')} ({t.get('status')})"
                    for t in r.get("tests", [])
                )
                lab_history_lines.append(f"- [{date}] {report_type}: {test_lines}")
            lab_history_str = "\n".join(lab_history_lines)
        else:
            lab_history_str = "No saved lab reports."

        if trends:
            trend_lines = []
            for tr in trends:
                points_str = " -> ".join(
                    f"{p.get('date', '?')[:10]}: {p.get('value')}" for p in tr.get("points", [])
                )
                annotations = tr.get("annotations") or []
                ann_str = ""
                if annotations:
                    ann_str = " (medicines: " + ", ".join(
                        f"{a['medicine_name']} since {a['start_date'][:10]}" for a in annotations
                    ) + ")"
                trend_lines.append(
                    f"- {tr['test_name']}: {points_str} [{tr.get('trend_direction') or 'n/a'}]{ann_str}"
                )
            trends_summary_str = "\n".join(trend_lines)
        else:
            trends_summary_str = "No tests with 2+ saved data points yet."

        if prescriptions:
            rx_lines = []
            for rx in prescriptions:
                date = (rx.get("date") or "?")[:10]
                meds = ", ".join(rx.get("medicines") or [])
                rx_lines.append(f"- [{date}] {meds}")
            prescriptions_summary_str = "\n".join(rx_lines)
        else:
            prescriptions_summary_str = "No saved prescriptions."

        inputs = {
            "lab_history": lab_history_str,
            "trends_summary": trends_summary_str,
            "prescriptions_summary": prescriptions_summary_str,
        }

        crew_instance = ClinicalSummaryCrew().crew(user_id=user_id)
        result = crew_instance.kickoff(inputs=inputs)

        summary_dict = first_pydantic_dict(result) or {}
        if not summary_dict:
            summary_dict = {"clinical_summary": result.raw, "key_flags": [], "active_medicines_note": "", "disclaimer": ""}

        snapshot = {
            "clinical_summary": summary_dict,
            "lab_reports": lab_reports,
            "trends": trends,
            "prescriptions": prescriptions,
        }

        token = create_doctor_qr_token(user_id, snapshot, expiry_hours=expiry_hours)
        return {
            "token": token,
            "qr_url": f"/doctor-visit/{token}",
            "expires_in_hours": expiry_hours,
        }
    except Exception as e:
        raise _server_error(e)


@router.get("/health/doctor-qr/{token}")
def health_get_doctor_qr(token: str):
    """Public, no auth — see module note above."""
    try:
        result = get_doctor_qr_snapshot(token)
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Ye QR invalid hai ya expire ho chuka hai. Patient se naya QR generate karne ko kaho."
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise _server_error(e)

