"""
safety_guardrails.py — fast, hardcoded keyword check that runs BEFORE any
LLM call on user-described symptoms or consultation statements.

Why this exists (see decisions.md D24): an LLM can be slow, can occasionally
under-triage a genuinely urgent description, and every LLM call costs a
network round-trip. For a small, well-known set of red-flag phrases (chest
pain, can't breathe, suicidal ideation, etc.) there is no reason to wait on
a model at all — we can answer instantly and tell the person to get real
help right now.

IMPORTANT — what this is and isn't:
- This is a coarse, keyword-based first-pass safety net, NOT a diagnostic
  tool and NOT a replacement for the LLM triage agent. It only ever
  upgrades urgency (fires early on obvious red flags); it never downgrades
  or overrides a careful assessment for anything that doesn't match.
- A real clinical deployment would need a doctor/clinical safety reviewer
  to sign off on and expand this keyword list before shipping to real
  patients. Here it demonstrates the "safety layer sits in front of the
  model, not just inside the prompt" pattern for a healthcare AI project.
- English + common Hinglish/Hindi (Latin-script) phrasing is covered since
  that's how MediSarthi's users actually type/speak.
"""

import re

# Each category maps to a list of regex patterns (case-insensitive). Keep
# patterns specific enough to avoid false positives on casual mentions
# ("I had a headache yesterday" should NOT fire "worst headache of my life").
EMERGENCY_PATTERNS = {
    "cardiac": [
        r"chest pain", r"chest.*tight", r"seene mein dard", r"seene me dard",
        r"heart attack", r"crushing pain.*chest",
    ],
    "respiratory": [
        r"can'?t breathe", r"cannot breathe", r"difficulty breathing",
        r"saans nahi aa rahi", r"saans lene mein takleef", r"choking",
        r"lips?.*turning blue", r"turning blue",
    ],
    "neurological": [
        r"\bstroke\b", r"face.*droop", r"slurred speech", r"sudden numbness",
        r"can'?t move (my |his |her )?(arm|leg|side|face)",
        r"worst headache of (my|his|her) life", r"loss of consciousness",
        r"\bunconscious\b", r"\bseizure\b", r"fits aa rahe", r"\bbehosh\b",
    ],
    "bleeding": [
        r"heavy bleeding", r"bleeding (won'?t|will not|does not) stop",
        r"coughing (up )?blood", r"vomiting blood",
        r"blood in (my |his |her )?(vomit|stool)",
        r"khoon (ruk nahi raha|nikal raha)",
    ],
    "allergic": [
        r"anaphyla", r"throat.*(swelling|closing)", r"swollen tongue",
        r"severe allergic reaction",
    ],
    "obstetric": [
        r"water broke", r"baby.*(not mov|stopped mov)",
        r"heavy bleeding.*pregnan", r"severe (abdominal )?pain.*pregnan",
    ],
    "mental_health_crisis": [
        r"\bsuicid", r"kill myself", r"end my life", r"want to die",
        r"don'?t want to (live|be alive)", r"khudkushi",
        r"marna chahta hoon", r"marna chahti hoon", r"self.?harm",
    ],
}

_COMPILED_PATTERNS = {
    category: [re.compile(p, re.IGNORECASE) for p in patterns]
    for category, patterns in EMERGENCY_PATTERNS.items()
}

CRISIS_RESOURCE_NOTE = (
    "Agar tum khud ko nuksaan pahunchane ke baare mein soch rahe ho, please abhi "
    "KIRAN Mental Health Helpline — 1800-599-0019 (free, 24/7, India) — par call "
    "karo, ya kisi trusted insaan ke paas jaake baat karo. Tum akele nahi ho."
)


def check_emergency(text: str) -> dict | None:
    """
    Scans `text` (raw symptom description / transcribed statement) for
    red-flag phrases BEFORE it's ever sent to an LLM.

    Returns None if nothing matches — caller should proceed with the normal
    LLM-based flow exactly as before.

    Returns a dict shaped like `SymptomTriageOutput` (see crew.py) if a
    red flag matches, so callers can drop it straight into a `{"triage": ...}`
    response with zero frontend changes needed. Callers that need a
    different response shape (e.g. the consultation endpoints, which return
    a prescription-analysis shape) should read `explanation`/`disclaimer`
    off this dict and map them into their own response shape.
    """
    if not text or not text.strip():
        return None

    matched_category = None
    matched_phrase = None
    for category, patterns in _COMPILED_PATTERNS.items():
        for pattern in patterns:
            m = pattern.search(text)
            if m:
                matched_category = category
                matched_phrase = m.group(0)
                break
        if matched_category:
            break

    if not matched_category:
        return None

    is_mental_health = matched_category == "mental_health_crisis"

    if is_mental_health:
        headline = "Please reach out for support right now."
        explanation = (
            "Jo tumne share kiya hai wo bohot serious lag raha hai. Is jaisi situation mein "
            "sabse important cheez hai turant kisi se baat karna — AI response ka wait mat karo."
        )
        disclaimer = (
            "Ye ek automated keyword-based safety check hai, professional mental health "
            "assessment nahi. Please turant helpline ya kisi trusted insaan se contact karo."
        )
    else:
        headline = "This sounds like it could be a medical emergency."
        explanation = (
            "Jo symptoms tumne describe kiye hain unmein kuch red-flag words hain jo turant "
            "medical attention maangte hain. Isse AI se analyse karwane ke bajaye abhi real "
            "help lena zyada zaroori hai."
        )
        disclaimer = (
            "Ye ek automated keyword-based safety check hai, poori medical assessment nahi. "
            "Turant nearest hospital jao ya emergency services (112) ko call karo."
        )

    return {
        "guardrail_triggered": True,
        "matched_category": matched_category,
        "matched_phrase": matched_phrase,
        "urgency_level": "Visit Emergency / Go Now" if not is_mental_health else "Seek Immediate Support",
        "urgency_color": "red",
        "headline": headline,
        "explanation": explanation,
        "flags": [{"symptom": matched_phrase, "reason": "Matched a red-flag phrase in our safety check."}],
        "home_care_tips": [],
        "warning_signs": [] if is_mental_health else ["Any worsening of the above — do not wait, go now."],
        "disclaimer": disclaimer,
        "crisis_resource": CRISIS_RESOURCE_NOTE if is_mental_health else None,
    }