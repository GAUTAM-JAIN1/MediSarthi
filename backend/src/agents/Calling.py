import os
import json
import asyncio
import base64
import time
import threading
import subprocess
import requests
import websockets

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import PlainTextResponse
from twilio.rest import Client
import uvicorn

from agents.Calling_Ai import decide_reply, summarize_conversation
from agents.speech_to_text import connect_assemblyai, send_audio
from agents.text_to_speech import text_to_speech

load_dotenv()

# ── Internal mini-app (runs on port 8001, separate from main FastAPI on 8080) ──
# Twilio needs a public WebSocket URL for real-time audio streaming.
# This mini-app provides /twiml (TwiML webhook) and /media (WebSocket) endpoints.
# main.py's /call/schedule starts it in a background thread via start_call().
_call_app = FastAPI()

_twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# Shared call data — set by start_call() before the call is made.
# Thread-safe enough for single-call-at-a-time use case.
_CURRENT_CALL = {
    "disease": "General Checkup",
    "doctor": "Any Doctor",
    "slot": "Any Available Time",
    "patient_name": "",
    "reason": "",
}

# ── NEW: shared call status, polled by GET /call/status in main.py ───────────
# state: idle | dialing | in_call | completed | failed
_CALL_STATUS = {
    "state": "idle",
    "to_number": None,
    "summary": None,
    "transcript": [],
    "error": None,
}
_status_lock = threading.Lock()


def _set_status(**kwargs):
    with _status_lock:
        _CALL_STATUS.update(kwargs)


def get_call_status() -> dict:
    """Read-only snapshot of the current/last call's status. Used by main.py's
    GET /call/status endpoint, which the frontend polls after scheduling a call."""
    with _status_lock:
        return dict(_CALL_STATUS)


CALL_PORT = 8001  # Separate from main API (8080) — Twilio needs its own port


def _start_ngrok(port: int) -> str | None:
    """
    Launches ngrok via subprocess, waits for it to start, then fetches the
    public HTTPS URL from ngrok's local API (127.0.0.1:4040).
    Returns the URL string, or None on failure.

    NOTE: --request-header-add "ngrok-skip-browser-warning:true" is required
    on ngrok's free tier — without it, ngrok injects an HTML interstitial
    warning page on the FIRST request from any new client (including Twilio's
    webhook POST to /twiml). Twilio can't parse that HTML as TwiML, so it
    silently drops the call before your <Say> greeting ever plays.

    DEBUG MODE: stdout/stderr are NOT suppressed right now (no DEVNULL) so
    that any ngrok startup error (auth, session-limit, version, etc.) prints
    straight into this terminal. Once everything works, you can put
    `stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL` back if the noise
    bothers you.
    """
    # Kill any leftover ngrok from a previous call
    subprocess.run(
        "taskkill /IM ngrok.exe /F",
        shell=True,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )

    subprocess.Popen(
        [
            "ngrok", "http", str(port),
            "--request-header-add", "ngrok-skip-browser-warning:true",
        ]
    )
    print(f"[Calling] ngrok starting on port {port}...")

    # Give ngrok a moment, then poll its local API
    time.sleep(3)
    for attempt in range(6):
        try:
            resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=3)
            tunnels = resp.json().get("tunnels", [])
            if tunnels:
                url = tunnels[0]["public_url"]
                if url.startswith("http://"):
                    url = url.replace("http://", "https://")
                return url
        except Exception:
            pass
        time.sleep(1)

    print("[Calling] ngrok URL fetch failed — is ngrok installed and in PATH?")
    return None


@_call_app.post("/twiml", response_class=PlainTextResponse)
async def twiml_webhook():
    """
    Twilio calls this URL right after connecting. Returns TwiML that greets
    the clinic receptionist and opens a media stream back to /media.
    """
    ngrok_url = os.environ.get("_MEDISARTHI_NGROK_URL", "")
    ws_host = ngrok_url.replace("https://", "").replace("http://", "")

    greeting = (
        f"Hello, this is MediSarthi AI assistant calling on behalf of "
        f"{_CURRENT_CALL['patient_name'] or 'a patient'}. "
        f"I would like to book an appointment. Please hold for a moment."
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">{greeting}</Say>
  <Connect>
    <Stream url="wss://{ws_host}/media" />
  </Connect>
</Response>""".strip()


@_call_app.websocket("/media")
async def media_stream(websocket: WebSocket):
    """
    Real-time bidirectional audio bridge:
      Twilio (phone) ──mulaw/8kHz──> AssemblyAI (transcription)
        AssemblyAI transcript ──> Gemini (decide reply)
          Gemini reply ──> Deepgram TTS ──> Twilio (phone)
    """
    await websocket.accept()
    print("[Calling] Twilio media stream connected.")
    _set_status(state="in_call")

    ws_aai = await connect_assemblyai()
    stream_sid = None
    history = []

    async def _listen_transcripts():
        nonlocal stream_sid, history
        while True:
            try:
                raw = await ws_aai.recv()
                msg = json.loads(raw)

                # AssemblyAI v3 streaming sends Turn events
                if msg.get("type") == "Turn" and msg.get("end_of_turn"):
                    transcript = msg.get("transcript", "").strip()
                    if not transcript:
                        continue

                    print(f"[Calling] Receptionist: {transcript}")
                    history.append(f"Receptionist: {transcript}")

                    reply = decide_reply(
                        transcript_text=transcript,
                        conversation_history=history,
                        disease=_CURRENT_CALL["disease"],
                        doctor_name=_CURRENT_CALL["doctor"],
                        slot=_CURRENT_CALL["slot"],
                        patient_name=_CURRENT_CALL["patient_name"],
                        reason=_CURRENT_CALL["reason"],
                    )
                    print(f"[Calling] AI: {reply}")
                    history.append(f"AI: {reply}")

                    # Keep history bounded
                    if len(history) > 20:
                        history = history[-15:]

                    # Live-update the shared transcript while the call is still
                    # in progress, so a poller can show partial progress too.
                    _set_status(transcript=list(history))

                    audio_bytes = text_to_speech(reply)
                    if audio_bytes and stream_sid:
                        payload = base64.b64encode(audio_bytes).decode("utf-8")
                        await websocket.send_text(json.dumps({
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": payload},
                        }))

            except Exception as e:
                print(f"[Calling] Transcript listener error: {e}")
                break

    listener = asyncio.create_task(_listen_transcripts())
    audio_buffer = bytearray()
    MIN_CHUNK = 1000  # bytes — batch audio before sending to AssemblyAI

    try:
        async for raw_msg in websocket.iter_text():
            msg = json.loads(raw_msg)
            event = msg.get("event")

            if event == "start":
                stream_sid = msg["start"]["streamSid"]
                print(f"[Calling] Stream SID: {stream_sid}")

            elif event == "media":
                chunk = base64.b64decode(msg["media"]["payload"])
                audio_buffer.extend(chunk)
                if len(audio_buffer) >= MIN_CHUNK:
                    await send_audio(ws_aai, bytes(audio_buffer))
                    audio_buffer.clear()

            elif event == "stop":
                print("[Calling] Stream ended by Twilio.")
                break

    finally:
        summary = summarize_conversation(history)
        print(f"[Calling] Call summary:\n{summary}")
        _set_status(state="completed", summary=summary, transcript=list(history))
        listener.cancel()
        try:
            await ws_aai.close()
        except Exception:
            pass
        try:
            await websocket.close()
        except Exception:
            pass


def _trigger_call(to_number: str, ngrok_url: str):
    """
    Waits for the mini-server to be ready, then places the Twilio call.
    Runs in a daemon thread so it doesn't block uvicorn's startup.
    """
    time.sleep(4)  # Let uvicorn finish starting
    print(f"[Calling] Placing call to {to_number}...")
    try:
        call = _twilio_client.calls.create(
            to=to_number,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            url=f"{ngrok_url}/twiml",
        )
        print(f"[Calling] Call placed — SID: {call.sid}")
    except Exception as e:
        print(f"[Calling] Failed to place call: {e}")
        _set_status(state="failed", error=f"Twilio call place nahi ho saka: {e}")


def start_call(
    number: str,
    disease: str,
    doctor_name: str,
    availability: str,
    patient_name: str = "",
    reason: str = "",
):
    """
    Entry point called by main.py's /call/schedule endpoint (in a thread).
    1. Resets shared call status for this new call.
    2. Starts ngrok tunnel.
    3. Sets shared call data.
    4. Launches the Twilio call in another thread.
    5. Starts the mini uvicorn server (blocks this thread until the call ends).
    """
    _set_status(
        state="dialing",
        to_number=number,
        summary=None,
        transcript=[],
        error=None,
    )

    ngrok_url = _start_ngrok(CALL_PORT)
    if not ngrok_url:
        print("[Calling] Cannot start call — ngrok failed.")
        _set_status(
            state="failed",
            error="ngrok tunnel start nahi ho saka — ngrok installed/PATH mein hai check karo.",
        )
        return

    print(f"[Calling] ngrok tunnel: {ngrok_url}")
    os.environ["_MEDISARTHI_NGROK_URL"] = ngrok_url

    # Store call context
    _CURRENT_CALL["disease"] = disease
    _CURRENT_CALL["doctor"] = doctor_name
    _CURRENT_CALL["slot"] = availability
    _CURRENT_CALL["patient_name"] = patient_name
    _CURRENT_CALL["reason"] = reason

    # Place the actual Twilio call after server starts
    threading.Thread(
        target=_trigger_call,
        args=(number, ngrok_url),
        daemon=True,
    ).start()

    # Block this thread running the mini-server (call ends → server can stop)
    uvicorn.run(_call_app, host="127.0.0.1", port=CALL_PORT, log_level="warning")