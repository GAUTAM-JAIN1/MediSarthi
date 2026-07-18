"""
medicine_test_map.py — MediSarthi Medicine Effectiveness feature (phase 1)

Static medicine -> tracked test(s) mapping. Deliberately NOT an LLM call —
which tests a given medicine should move is a fixed clinical fact, not
something that needs to be inferred fresh per request. See decisions.md D29
for the full reasoning ("static dict beats LLM-inferred here").

How this is used: health_records.py's annotated-trends join looks up each
saved prescription's medicine name here (case-insensitive, see
resolve_tracked_tests() below) to find which of the user's lab test trends
that medicine is expected to affect, then attaches the prescription's
start_time to those specific trends as a chart annotation.

Coverage: ~30 common medicines across the therapy areas already reflected in
this project's sample data and reference files (diabetes, thyroid, lipid,
blood pressure, anaemia, general). Not exhaustive — see resolve_tracked_tests()
for the honest fallback behavior when a medicine isn't listed.

Matching a medicine name to a key: prescriptions store free-text medicine
names (e.g. "Metformin 500mg", "Tab. Glycomet-SR 500"), not a coded drug ID.
resolve_tracked_tests() does a lowercase substring match against each entry's
`aliases` list rather than requiring an exact match, so "Metformin 500mg
twice daily" still matches the "metformin" entry. This is intentionally
forgiving rather than strict, since a missed match just means no annotation
appears (graceful) whereas a wrong match could mislabel a trend — aliases are
kept specific (generic + common brand names) rather than broad to keep the
false-positive risk low.
"""

from typing import List, Optional


# Each entry: canonical generic name -> {
#   "aliases": [lowercase strings to substring-match against a prescription's
#               medicine name — generic name + common Indian brand names],
#   "tracks": [test_name strings, matching the LabTestResult.test_name values
#              LabReportCrew actually outputs — see lab_reference_ranges.txt
#              and lab_report_task.yaml for the same naming convention],
# }
MEDICINE_TEST_MAP = {
    # ── Diabetes ──────────────────────────────────────────────────────────
    "metformin": {
        "aliases": ["metformin", "glycomet", "glucophage"],
        "tracks": ["Fasting Blood Sugar", "Postprandial Blood Sugar", "HbA1c"],
    },
    "glimepiride": {
        "aliases": ["glimepiride", "amaryl", "glimy"],
        "tracks": ["Fasting Blood Sugar", "Postprandial Blood Sugar", "HbA1c"],
    },
    "gliclazide": {
        "aliases": ["gliclazide", "diamicron"],
        "tracks": ["Fasting Blood Sugar", "Postprandial Blood Sugar", "HbA1c"],
    },
    "sitagliptin": {
        "aliases": ["sitagliptin", "januvia", "istavel"],
        "tracks": ["Fasting Blood Sugar", "HbA1c"],
    },
    "insulin": {
        "aliases": ["insulin", "lantus", "human mixtard", "novorapid", "huminsulin"],
        "tracks": ["Fasting Blood Sugar", "Postprandial Blood Sugar", "HbA1c"],
    },
    "empagliflozin": {
        "aliases": ["empagliflozin", "jardiance"],
        "tracks": ["Fasting Blood Sugar", "HbA1c"],
    },

    # ── Thyroid ───────────────────────────────────────────────────────────
    "levothyroxine": {
        "aliases": ["levothyroxine", "thyronorm", "eltroxin", "thyrox"],
        "tracks": ["TSH", "Free T3", "Free T4"],
    },
    "carbimazole": {
        "aliases": ["carbimazole", "neo-mercazole"],
        "tracks": ["TSH", "Free T3", "Free T4"],
    },

    # ── Lipid / cholesterol ───────────────────────────────────────────────
    "atorvastatin": {
        "aliases": ["atorvastatin", "atorva", "lipitor", "storvas"],
        "tracks": ["Total Cholesterol", "LDL Cholesterol", "HDL Cholesterol", "Triglycerides"],
    },
    "rosuvastatin": {
        "aliases": ["rosuvastatin", "rosuvas", "crestor"],
        "tracks": ["Total Cholesterol", "LDL Cholesterol", "HDL Cholesterol", "Triglycerides"],
    },
    "fenofibrate": {
        "aliases": ["fenofibrate", "lipicard", "tricor"],
        "tracks": ["Triglycerides", "HDL Cholesterol"],
    },

    # ── Blood pressure (not usually tracked via lab report, listed for
    #    completeness in case vitals get joined into this same feature
    #    later — kidney panel is the relevant lab-side effect to watch) ───
    "amlodipine": {
        "aliases": ["amlodipine", "amlopres", "amlodac", "norvasc"],
        "tracks": ["Creatinine"],
    },
    "losartan": {
        "aliases": ["losartan", "losar", "cozaar"],
        "tracks": ["Creatinine", "Blood Urea"],
    },
    "telmisartan": {
        "aliases": ["telmisartan", "telma", "micardis"],
        "tracks": ["Creatinine", "Blood Urea"],
    },
    "enalapril": {
        "aliases": ["enalapril", "envas"],
        "tracks": ["Creatinine", "Blood Urea"],
    },

    # ── Anaemia / iron ────────────────────────────────────────────────────
    "iron supplement": {
        "aliases": ["ferrous sulphate", "ferrous ascorbate", "livogen", "fefol", "orofer", "ferium"],
        "tracks": ["Hemoglobin", "Ferritin", "Iron"],
    },
    "folic acid": {
        "aliases": ["folic acid", "folvite"],
        "tracks": ["Hemoglobin"],
    },
    "vitamin b12": {
        "aliases": ["methylcobalamin", "mecobalamin", "cobadex", "neurobion"],
        "tracks": ["Vitamin B12", "Hemoglobin"],
    },
    "vitamin d": {
        "aliases": ["cholecalciferol", "calcirol", "uprise-d3", "d3 must"],
        "tracks": ["Vitamin D"],
    },

    # ── Liver / gout ──────────────────────────────────────────────────────
    "allopurinol": {
        "aliases": ["allopurinol", "zyloric"],
        "tracks": ["Uric Acid"],
    },
    "febuxostat": {
        "aliases": ["febuxostat", "febutaz"],
        "tracks": ["Uric Acid"],
    },
    "silymarin": {
        "aliases": ["silymarin", "liv 52", "livogen forte"],
        "tracks": ["SGPT", "SGOT", "Bilirubin"],
    },

    # ── Kidney (specific renal-support medicines) ────────────────────────
    "sodium bicarbonate": {
        "aliases": ["sodium bicarbonate", "shobicarb"],
        "tracks": ["Creatinine", "Blood Urea"],
    },
}


def resolve_tracked_tests(medicine_name: str) -> Optional[List[str]]:
    """
    Given a free-text medicine name (as stored in a saved prescription,
    e.g. "Metformin 500mg" or "Tab. Glycomet-SR"), return the list of
    test_name strings this medicine is expected to affect, or None if the
    medicine isn't in MEDICINE_TEST_MAP.

    Matching is case-insensitive substring matching against each entry's
    `aliases` — see the module docstring for why this is deliberately
    forgiving rather than an exact match.

    Returns None (not an empty list) when nothing matches, so callers can
    distinguish "known medicine, tracks nothing new" (not currently possible
    given the data above, but kept as a clean distinction) from "medicine
    not in our reference at all" if that distinction ever matters upstream.
    """
    if not medicine_name:
        return None

    name_lower = medicine_name.strip().lower()

    for entry in MEDICINE_TEST_MAP.values():
        for alias in entry["aliases"]:
            if alias in name_lower:
                return entry["tracks"]

    return None