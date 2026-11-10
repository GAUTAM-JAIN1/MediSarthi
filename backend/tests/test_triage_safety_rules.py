"""
test_triage_safety_rules.py — Assert safety rules are present in symptom_triage_task.yaml
"""

from pathlib import Path
import yaml
import pytest

CONFIG_PATH = Path(__file__).resolve().parents[1] / "src" / "agents" / "config" / "symptom_triage_task.yaml"

RULE_NO_ASSUMED = (
    "SAFETY RULE (no assumed details): Do not assume the patient's age, sex, body temperature, "
    "duration of illness, number of stools, or any symptom the patient did not state. "
    "If a missing detail would change the urgency level, ask for it in the explanation and "
    "assign the higher urgency level until it is known."
)

RULE_HOME_CARE_GATE = (
    'SAFETY RULE (Home Care gate): Assign "Home Care" only if the patient has described none of the following: '
    "blood in stool or vomit, signs of dehydration (dizziness, very little urine, dry mouth), "
    "high fever, persistent vomiting, confusion, chest pain, or breathing difficulty. "
    "If any of these is unknown rather than clearly absent, do not assign Home Care."
)

RULE_NO_MED_NAMES = (
    "SAFETY RULE (no medicine names or doses): In home_care_tips and warning_signs, "
    "do not name any medicine and do not state any dose, temperature threshold, "
    "or time interval that is not in the knowledge source. "
    "Suggest that the patient ask a pharmacist or doctor about medicines."
)

GROUNDING_RULE = (
    "GROUNDING RULE: Base every statement on the knowledge source and the patient's own data provided above. "
    "If the knowledge source does not cover the symptoms or condition described, say so plainly "
    "('This is not covered in the reference material I have'), do not name a condition, do not suggest "
    "any medicine or dose, and advise the patient to see a doctor. Never state a timing, dose, or reference "
    "range that is not in the source. Do not guess."
)


def _load_triage_description() -> str:
    assert CONFIG_PATH.is_file(), f"Config file not found: {CONFIG_PATH}"
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "triage_task" in data, "triage_task not found in yaml"
    return data["triage_task"]["description"]


def test_triage_safety_rules_present():
    desc = _load_triage_description()
    assert RULE_NO_ASSUMED in desc, "RULE_NO_ASSUMED not found in description"
    assert RULE_HOME_CARE_GATE in desc, "RULE_HOME_CARE_GATE not found in description"
    assert RULE_NO_MED_NAMES in desc, "RULE_NO_MED_NAMES not found in description"


def test_grounding_rule_still_present():
    desc = _load_triage_description()
    assert GROUNDING_RULE in desc, "GROUNDING_RULE not found in description"


def test_safety_rule_count():
    desc = _load_triage_description()
    assert desc.count("SAFETY RULE") == 3
