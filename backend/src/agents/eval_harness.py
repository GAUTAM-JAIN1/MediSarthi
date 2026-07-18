"""
eval_harness.py — Agent evaluation harness for MediSarthi.

WHY THIS EXISTS
----------------
Most "AI features" in a portfolio project are only ever checked by hand
("I tried a few prompts, looked fine"). This script gives MediSarthi a
repeatable, automated way to answer: "if I change a prompt/model/keyword
list, did anything that used to work silently break?"

Three suites, in increasing cost:

1. guardrails   — safety_guardrails.check_emergency(). No LLM call, no cost,
                   runs in milliseconds. This is a pure regression suite:
                   every red-flag phrase that should trigger the guardrail,
                   and every benign phrase that should NOT, gets checked on
                   every run. Safe to run constantly (e.g. in CI later).

2. triage       — SymptomTriageCrew. Real LLM calls. Checks whether the
                   crew's urgency_level lands in the *expected bucket* for
                   a small set of hand-labeled symptom descriptions.

3. interactions — MedicineInteractionCrew. Real LLM calls. Checks whether
                   the crew correctly flags (or doesn't flag) a dangerous
                   interaction for a small set of known medicine pairs.

LabReportCrew is deliberately NOT covered here — it takes an image/PDF as
input, not plain text, so it doesn't fit this harness's text-in/JSON-out
shape without also faking file uploads. Can be added later with a small
set of saved sample report images if wanted.

FULLY VERIFIED (as of this version) against actual crew.py, symptom_triage_task.yaml,
and medicine_interaction_task.yaml — no placeholders remain:

  1. `kickoff(inputs={...})` keys — confirmed: SymptomTriageCrew's task template uses
     `{symptoms}`; MedicineInteractionCrew's task template uses `{medicines_list}`
     (passed as a comma-joined string, not a raw Python list, so it reads naturally
     inside the prompt).
  2. `urgency_level` enum — confirmed exactly `'Home Care'`, `'See a Doctor Soon'`,
     `'Visit Emergency / Go Now'` (crew.py's `SymptomTriageOutput`).
  3. Interaction conflict field — confirmed `has_major_interaction` (not
     `has_interaction`) on `MedicineInteractionOutput`.

Everything else (timing, pass/fail bucketing, report generation) works
regardless of those two fixes.

USAGE
-----
    python eval_harness.py                       # run all 3 suites
    python eval_harness.py --suite guardrails     # just the free/fast one
    python eval_harness.py --suite triage --user-id <mongo_user_id>
    python eval_harness.py --suite interactions --user-id <mongo_user_id>

`--user-id` is required for the triage/interactions suites because both
crews' `.crew(user_id=...)` loads a real user profile (see auth.py
`get_user_knowledge_profile`). Use any existing test account's user_id.

ENVIRONMENT PREREQUISITES (confirmed from crew.py, for the triage/interactions
suites only — the guardrails suite needs none of this):
  - `GROQ_API_KEY` in `backend/.env` (all crews now run on
    `groq/llama-3.3-70b-versatile`, confirmed in crew.py's Groq-migration note).
  - Ollama running locally with `mxbai-embed-large` pulled — `_build_crew_base()`
    points every crew's embedder at `http://localhost:11434/api/embeddings`.
    If Ollama isn't running, kickoff() will raise and the harness will record
    it as a failed case with the error message rather than crashing the run.
  - A small delay (3s) is inserted between sequential triage/interaction
    cases since every crew is capped at `max_rpm=3` — avoids spurious 429s
    when running several cases back-to-back in one process.

OUTPUT
------
Prints a pass/fail table + summary stats to stdout, and writes a full
JSON report to `eval_report_<timestamp>.json` in the same folder (one
snapshot per run, so you can diff behavior across sessions/model changes).
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

# --- Suite 1: safety guardrails (no LLM, always safe to run) ---------------
from safety_guardrails import check_emergency

REPORT_DIR = Path(__file__).parent


# =============================================================================
# TEST CASES — edit/extend these freely, this is the actual "eval set"
# =============================================================================

GUARDRAIL_CASES = [
    # (label, input_text, expect_triggered)
    ("chest_pain_en", "I have severe chest pain and it won't go away", True),
    ("chest_pain_hi", "seene mein bahut tez dard ho raha hai", True),
    ("breathing_en", "I can't breathe properly since this morning", True),
    ("breathing_hi", "saans nahi aa rahi thik se", True),
    ("suicidal_en", "I want to end my life, I can't take this anymore", True),
    ("stroke_signs", "my face suddenly feels droopy and I can't speak clearly", True),
    ("heavy_bleeding", "there is heavy bleeding that won't stop", True),
    ("pregnancy_emergency", "baby has not moved since yesterday", True),
    # negatives — must NOT trigger, this is the false-positive check
    ("mild_headache", "I have had a mild headache since yesterday", False),
    ("common_cold", "runny nose and mild cough for two days", False),
    ("tired", "feeling a bit tired after work today", False),
    ("mild_stomach", "slight stomach ache after lunch", False),
]

TRIAGE_CASES = [
    # (label, symptom_text, expected_urgency_bucket)
    # NOTE: expected values must match SymptomTriageOutput's real enum —
    # verify against crew.py before trusting failures here.
    ("clear_emergency", "sudden crushing chest pain radiating to my left arm, sweating heavily",
     "Visit Emergency / Go Now"),
    ("moderate_concern", "fever of 102F for 3 days that isn't going down with medicine",
     "See a Doctor Soon"),
    ("mild_self_care", "mild sore throat and slight cough, no fever, started yesterday",
     "Home Care"),
]

INTERACTION_CASES = [
    # (label, medicines_list, expect_conflict)
    ("warfarin_aspirin", ["Warfarin", "Aspirin"], True),
    ("ssri_maoi", ["Fluoxetine", "Phenelzine"], True),
    ("paracetamol_vitc", ["Paracetamol", "Vitamin C"], False),
    ("metformin_alone_pair", ["Metformin", "Multivitamin"], False),
]


# =============================================================================
# SUITE RUNNERS
# =============================================================================

def run_guardrail_suite():
    results = []
    for label, text, expect_triggered in GUARDRAIL_CASES:
        start = time.perf_counter()
        result = check_emergency(text)
        elapsed_ms = (time.perf_counter() - start) * 1000
        triggered = bool(result and result.get("guardrail_triggered"))
        passed = triggered == expect_triggered
        results.append({
            "label": label,
            "input": text,
            "expected_triggered": expect_triggered,
            "actual_triggered": triggered,
            "passed": passed,
            "latency_ms": round(elapsed_ms, 3),
        })
    return results


def run_triage_case(label, symptom_text, expected_bucket, user_id):
    from crew import SymptomTriageCrew  # lazy import — avoid CrewAI cost for guardrail-only runs

    start = time.perf_counter()
    try:
        crew_instance = SymptomTriageCrew().crew(user_id=user_id)
        # confirmed against symptom_triage_task.yaml: template placeholder is {symptoms}
        output = crew_instance.kickoff(inputs={"symptoms": symptom_text})
        elapsed_ms = (time.perf_counter() - start) * 1000
        actual = getattr(output, "urgency_level", None) or (
            output.get("urgency_level") if isinstance(output, dict) else None
        )
        passed = actual == expected_bucket
        error = None
    except Exception as exc:  # noqa: BLE001 — eval harness, want to record and continue
        elapsed_ms = (time.perf_counter() - start) * 1000
        actual = None
        passed = False
        error = str(exc)

    return {
        "label": label,
        "input": symptom_text,
        "expected_urgency_level": expected_bucket,
        "actual_urgency_level": actual,
        "passed": passed,
        "latency_ms": round(elapsed_ms, 3),
        "error": error,
    }


def run_interaction_case(label, medicines, expect_conflict, user_id):
    from crew import MedicineInteractionCrew

    start = time.perf_counter()
    try:
        crew_instance = MedicineInteractionCrew().crew(user_id=user_id)
        # confirmed against medicine_interaction_task.yaml: template placeholder is
        # {medicines_list} — pass a clean comma-joined string, not a raw Python list,
        # so it reads naturally inside the prompt template.
        medicines_str = ", ".join(medicines)
        output = crew_instance.kickoff(inputs={"medicines_list": medicines_str})
        elapsed_ms = (time.perf_counter() - start) * 1000
        # confirmed against crew.py MedicineInteractionOutput: field is has_major_interaction
        actual = getattr(output, "has_major_interaction", None)
        if actual is None and isinstance(output, dict):
            actual = output.get("has_major_interaction")
        passed = bool(actual) == expect_conflict
        error = None
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - start) * 1000
        actual = None
        passed = False
        error = str(exc)

    return {
        "label": label,
        "medicines": medicines,
        "expected_conflict": expect_conflict,
        "actual_conflict": actual,
        "passed": passed,
        "latency_ms": round(elapsed_ms, 3),
        "error": error,
    }


def run_triage_suite(user_id):
    results = []
    for i, (label, text, expected) in enumerate(TRIAGE_CASES):
        if i > 0:
            time.sleep(3)  # crews are capped at max_rpm=3 (Groq free tier) — avoid 429s
        results.append(run_triage_case(label, text, expected, user_id))
    return results


def run_interaction_suite(user_id):
    results = []
    for i, (label, meds, expect) in enumerate(INTERACTION_CASES):
        if i > 0:
            time.sleep(3)  # same max_rpm=3 consideration as triage suite
        results.append(run_interaction_case(label, meds, expect, user_id))
    return results


# =============================================================================
# REPORTING
# =============================================================================

def summarize(suite_name, results):
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    latencies = [r["latency_ms"] for r in results]
    avg_latency = sum(latencies) / total if total else 0.0
    return {
        "suite": suite_name,
        "total": total,
        "passed": passed,
        "accuracy_pct": round(100 * passed / total, 1) if total else 0.0,
        "avg_latency_ms": round(avg_latency, 3),
        "min_latency_ms": round(min(latencies), 3) if latencies else 0.0,
        "max_latency_ms": round(max(latencies), 3) if latencies else 0.0,
        "results": results,
    }


def print_suite(summary):
    print(f"\n=== {summary['suite']} ===")
    for r in summary["results"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['label']:<22} {r['latency_ms']:>8.2f} ms", end="")
        if r.get("error"):
            print(f"   error: {r['error']}")
        else:
            print()
    print(
        f"  -> {summary['passed']}/{summary['total']} passed "
        f"({summary['accuracy_pct']}%), avg latency {summary['avg_latency_ms']} ms"
    )


def main():
    parser = argparse.ArgumentParser(description="MediSarthi agent eval harness")
    parser.add_argument(
        "--suite",
        choices=["all", "guardrails", "triage", "interactions"],
        default="all",
    )
    parser.add_argument(
        "--user-id",
        default=None,
        help="Existing Mongo user_id — required for triage/interactions suites",
    )
    args = parser.parse_args()

    need_llm = args.suite in ("all", "triage", "interactions")
    if need_llm and not args.user_id:
        parser.error("--user-id is required for the triage/interactions suites (LLM crews need a real user profile)")

    summaries = []

    if args.suite in ("all", "guardrails"):
        summaries.append(summarize("guardrails", run_guardrail_suite()))

    if args.suite in ("all", "triage"):
        summaries.append(summarize("triage", run_triage_suite(args.user_id)))

    if args.suite in ("all", "interactions"):
        summaries.append(summarize("interactions", run_interaction_suite(args.user_id)))

    for s in summaries:
        print_suite(s)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suites": summaries,
    }
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"eval_report_{ts}.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\nFull report written to {report_path}")


if __name__ == "__main__":
    main()