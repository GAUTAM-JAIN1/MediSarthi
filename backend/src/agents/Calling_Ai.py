import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# meta-llama/llama-4-scout-17b-16e-instruct was Groq-deprecated (announced
# 17 June 2026). Switched to openai/gpt-oss-120b — Groq's own recommended
# general-purpose replacement. Unlike buying_agent.py, this file never
# handles images (pure text call-transcript reasoning), so the text-only
# gpt-oss-120b is the right fit here — no need for a multimodal model.
GROQ_MODEL = "openai/gpt-oss-120b"


def _groq(prompt: str) -> str:
    response = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=120,
    )
    return response.choices[0].message.content.strip()


def decide_reply(
    transcript_text: str,
    conversation_history: list,
    disease: str,
    doctor_name: str,
    slot: str,
    patient_name: str = "",
    reason: str = "",
) -> str:
    """
    Given what the receptionist just said + full conversation history,
    returns the AI agent's next spoken reply.

    Now takes patient_name + reason from the CallRequest (set by main.py)
    instead of calling face_recognize — user details come from auth.py.

    Runs on Groq (openai/gpt-oss-120b) because the Gemini free-tier project
    hit a hard `limit: 0` quota wall (429 errors on every call). Groq is
    also what the rest of MediSarthi (medicine price compare) already
    uses, and its latency is low enough for real-time call turns.
    """
    history_text = "\n".join(conversation_history[-10:])  # last 10 turns

    patient_info = ""
    if patient_name:
        patient_info += f"Patient name: {patient_name}\n"
    if reason:
        patient_info += f"Reason for visit: {reason}\n"
    if disease and disease != "General Checkup":
        patient_info += f"Condition/disease: {disease}\n"

    prompt = f"""You are an AI assistant calling a clinic to book an appointment.
Speak naturally and briefly — like a real caller, not a robot.

YOUR GOAL:
- Book an appointment for {slot} with {doctor_name or 'any available doctor'}.
- {patient_info.strip() or 'No specific patient details provided.'}

CONVERSATION SO FAR:
{history_text or '(just connected)'}

RECEPTIONIST JUST SAID:
"{transcript_text}"

RULES:
- Reply in 1-2 short sentences max.
- Be polite and natural — like a real person calling.
- If they ask for a name, give the patient name.
- If they ask for reason, give the reason/disease.
- If they offer a slot, confirm or counter-offer based on the preferred slot.
- If appointment is confirmed, thank them and say goodbye.
- NEVER say you are an AI unless directly asked.
- NEVER make up information that wasn't provided.

YOUR REPLY (speak directly, no quotes, no stage directions):"""

    try:
        return _groq(prompt)
    except Exception as e:
        print(f"[Calling_Ai] Groq error: {e}")
        return "I'm sorry, could you please repeat that?"


def summarize_conversation(history: list) -> str:
    """
    After the call ends, produces a summary: goal, outcome, follow-up actions.
    """
    if not history:
        return "No conversation took place."

    history_text = "\n".join(history)

    prompt = f"""Summarize this clinic call transcript briefly:

{history_text}

Provide:
1. Goal of the call
2. Outcome (appointment booked? When? With whom?)
3. Any follow-up actions needed

Keep it concise — 3-5 sentences max."""

    try:
        return _groq(prompt)
    except Exception as e:
        return f"Summary failed: {e}"