"""
test_safety_guardrails.py — Tests for safety_guardrails module.
"""

from agents.safety_guardrails import check_emergency


def test_emergency_explanation_chest_pain():
    result = check_emergency("I have chest pain while climbing stairs")
    assert result is not None
    assert result["urgency_level"] == "Visit Emergency / Go Now"
    assert result["explanation"] == (
        "This sounds like a possible emergency. Go to the nearest hospital now or call 112. Do not wait."
    )
