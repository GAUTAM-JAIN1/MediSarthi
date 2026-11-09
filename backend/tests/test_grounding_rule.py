"""
test_grounding_rule.py — Verify the verbatim grounding rule is present in all target task YAMLs.
"""

from pathlib import Path
import yaml
import pytest

CONFIG_DIR = Path(__file__).resolve().parents[1] / "src" / "agents" / "config"

GROUNDING_RULE = (
    "GROUNDING RULE: Base every statement on the knowledge source and the patient's own data provided above. "
    "If the knowledge source does not contain the information needed to answer, say so plainly "
    "(for example: 'This is not covered in the reference material I have') instead of answering from memory. "
    "Never state a dose, timing, interaction, or reference range that is not in the source. Do not guess."
)

TARGET_CONFIGS = [
    ("clinical_summary_task.yaml", "clinical_summary_task", "clinical_summary_agent.yaml"),
    ("lab_report_task.yaml", "lab_analysis_task", "lab_report_agent.yaml"),
    ("medicine_effectiveness_task.yaml", "effectiveness_task", "medicine_effectiveness_agent.yaml"),
    ("medicine_interaction_task.yaml", "interaction_check_task", "medicine_interaction_agent.yaml"),
]


def _load_yaml(filename: str) -> dict:
    p = CONFIG_DIR / filename
    assert p.is_file(), f"Config file not found: {p}"
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_target_files_count():
    """Assert target files count matches the 4 discovered invent-constrained task files."""
    assert len(TARGET_CONFIGS) == 4


@pytest.mark.parametrize("task_file,task_key,agent_file", TARGET_CONFIGS)
def test_grounding_rule_in_task_description(task_file, task_key, agent_file):
    data = _load_yaml(task_file)
    assert task_key in data, f"Key {task_key} not in {task_file}"
    desc = data[task_key]["description"]
    assert GROUNDING_RULE in desc, f"GROUNDING_RULE not in {task_file} description"

    agent_data = _load_yaml(agent_file)
    for agent_key, agent in agent_data.items():
        assert GROUNDING_RULE not in agent.get("backstory", ""), (
            f"GROUNDING_RULE mistakenly placed in agent backstory: {agent_file}:{agent_key}"
        )
