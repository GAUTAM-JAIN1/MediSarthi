# MediSarthi

## Overview

MediSarthi is an AI-powered healthcare ecosystem aimed at Indian users. It combines a multi-agent AI backend (CrewAI + Gemini) with a luxury-styled React frontend to give people one place to: talk through symptoms, get prescriptions read and explained, compare medicine prices across pharmacies, get an AI assistant to call a clinic and book an appointment, find nearby hospitals, track health records over time, carry an emergency-access QR medical ID, and participate in a blood-donor network.

The project originated as a college/personal project (two repos: `G.A.N.G.U` backend, `G.A.N.G.U-Frontend` frontend, built by the user's friend) and is being actively reworked into a portfolio-grade product under the new name **MediSarthi**, primarily to strengthen a resume for job applications.

## Vision

A trustworthy, premium-feeling AI health companion for India — not a toy demo, but something that looks and behaves like a real product: clean auth, real data persistence, sensible human-in-the-loop safeguards (e.g. never auto-purchasing medicine without explicit confirmation), and a visual identity distinct from generic "AI-generated" template look.

## Problem Statement

People juggle multiple disconnected steps when dealing with health: describing symptoms to find the right care, reading confusing prescriptions, comparing medicine prices across apps, calling clinics to book appointments, finding a nearby hospital in an emergency, remembering their own health history, and having no quick way to share critical medical info (blood group, allergies, emergency contact) with
 a stranger in a real emergency. MediSarthi consolidates these into one assistant-driven flow.

## Features

### Core (carried over from original project, re-verified)
- **Speech consultation** — user describes symptoms by voice/text (Hindi/English), CrewAI + Gemini produce guidance, can set medicine reminders.
- **Document/prescription OCR consultation** — photo of a prescription is OCR'd (Tesseract) and run through the same consultation flow.
- **Nearby hospital finder** — OpenStreetMap-based search by city/state.
- **Calendar reminders** — Google Calendar integration for medicine timing.

### Changed from original design
- **Login system** — replaced webcam face-recognition identification with standard **email + password** signup/login (bcrypt-hashed passwords in MongoDB). This was a deliberate product decision (see `decisions.md`). `face_recognize.py` and its dependency chain (`face-recognition`, `face-recognition-models`, `dlib`, `opencv-python`, `cmake`) have now been fully deleted/removed from `pyproject.toml` — confirmed no other file imported it.
- **Medicine price comparison** — browser-automation agent compares real prices across pharmacy sites; **auto-add-to-cart was removed** in favor of a human-in-the-loop "Add to cart?" confirmation step.
- **AI voice-calling agent** (Twilio + AssemblyAI + Deepgram, `ngrok` for the callback tunnel) — calls a clinic and tries to book an appointment; kept, flagged for future reliability hardening. `ngrok`'s binary was missing from the Docker image entirely until `decisions.md` D39 fixed it — worth remembering if this ever regresses in a future container rebuild.

### New — now implemented end-to-end
- **Health records dashboard** — vitals (BP, blood sugar, weight) + prescriptions combined into a single timeline, with a "Latest Vitals" summary card. Built on `health_records.py` + `HealthInfo.jsx`.
- **Emergency QR Medical ID** — fill out a one-time form (name, blood group, allergies, critical conditions, current medicines, emergency contact) on `/health-info`, generate a QR code, and anyone who scans it sees that safe subset of data **without login**, at a standalone `/emergency/:token` page with a tap-to-call emergency contact link. Full account/history still requires login.
- **Blood donor system** — donor registration (name, blood group, city, state, phone), donation count tracking, availability toggle, emergency priority blood requests, and donor matching by blood group + location. Built on `donor.py` + `Donor.jsx`.
- **Lab Report Analyser** *(live-tested, confirmed working, including PDF uploads)* — upload a lab/blood test report (photo or PDF) and get a plain-language, per-value explanation of what's normal, what's not, and what's worth asking a doctor about. `/lab-report` page. PDF handling was rebuilt to use real text extraction (`pdfplumber`, with an OCR fallback for scanned/photo PDFs) instead of an earlier bug where PDF uploads silently produced garbled output — see `decisions.md` D27.
- **Medicine Interaction Checker** *(live-tested, confirmed working)* — enter multiple medicines and check whether they're safe to take together.
- **Symptom Triage** *(live-tested, confirmed working)* — describe symptoms and get an urgency read: rest at home, see a doctor, or seek emergency care. Shares a single page with the interaction checker (`/medicine-check`).
- **Signup profile fields** — Age, Gender, City, State, Allergies now collected at signup (`Auth.jsx`), matching what the backend (`SignupRequest`, `auth.py`) already expected — real profile data instead of empty/zero placeholders.
- **Health Trends / Longitudinal Report History** *(built, chronology bug fixed, not yet fully live-tested)* — past saved lab reports shown as a real list, plus per-test line charts (e.g. Haemoglobin over time) with plain-language "improving / worsening / stable" insight, so a patient can see their own health trajectory across visits, not just one report at a time. Charts are now dated by each report's own date (extracted from the document) rather than upload time — see `decisions.md` D23 and D28.

### 🎯 Current MVP focus — Medicine Effectiveness (planned, not yet built)
The project's chosen core differentiator going forward: cross-referencing a user's own saved prescriptions against their own saved lab trends to tell them whether a medicine is working — in the right direction, at the expected pace, in plain language a non-medical person can trust — something a generic single-turn AI chat tool structurally cannot do, since it depends on this user's own data persisted across visits. Two-phase plan (direction+annotation first, pace-awareness second) — full spec in `PROJECT_CONTEXT.md` §10 and `decisions.md` D29. A "Doctor Visit QR" (time-limited QR a doctor scans to see saved history + a clinical-register summary) was also scoped but deliberately deprioritized behind this.

### 🔧 In active development
- **Medicine Effectiveness feature** — see above, `PROJECT_CONTEXT.md` §10, `decisions.md` D29. Not yet started.

## Tech Stack

**Backend** (`G.A.N.G.U` repo, Python)
- FastAPI (HTTP API)
- CrewAI (multi-agent orchestration) + Google Gemini (LLM)
- MongoDB (`pymongo`) — user accounts, health records, emergency profiles, donor data
- `face_recognition` / `dlib` — **being phased out**, replaced by `auth.py`
- Tesseract OCR (`pytesseract`) — prescription text extraction
- Twilio + AssemblyAI + Deepgram — AI voice calling agent
- `browser-use` (Playwright-based agent) — live pharmacy price scraping
- Google Calendar API (OAuth) — reminders
- `bcrypt` — password hashing
- `secrets` (stdlib) — emergency QR token generation

**Frontend** (`G.A.N.G.U-Frontend` repo, React)
- React 19 + Vite 7
- `react-router-dom` — client-side routing
- `react-icons` (Lucide set, `react-icons/lu`) — all icons
- `qrcode.react` — Emergency Medical ID QR code rendering
- Plain CSS (no Tailwind/CSS-in-JS) — custom luxury design system, CSS variables
- Fonts: Playfair Display (headings), Inter (body), Cormorant Garamond (decorative, currently unused in shipped pages)

## Folder Structure
MediSarthi/                          (user's local working folder, OneDrive-synced)

└── MediSarthi/

├── backend/                     (= G.A.N.G.U repo)

│   ├── pyproject.toml

│   ├── uv.lock

│   ├── knowledge/               (per-user profile.txt files, generated at runtime)

│   ├── medical_memory/          (CrewAI memory storage)

│   └── src/agents/

│       ├── main.py              (FastAPI app, all HTTP endpoints)

│       ├── crew.py              (CrewAI agent/crew definitions: SpeechCrew, FileCrew, Nearbyhospitals, general_que)

│       ├── auth.py              (email/password signup/login, replaces the old face_recognize.py — deleted)

│       ├── health_records.py    (vitals, prescriptions, timeline, emergency profile + QR token logic, lab report analysis history)

│       ├── donor.py              (blood donor registration, matching, donation requests)

│       ├── db_connect.py        (MongoDB connection — Mongo URI + API keys now in `.env`, secrets cleanup done pre-push)

│       ├── buying_agent.py      (browser-use price comparison agent)

 │       ├── Calling.py           (Twilio call handling)

│       ├── Calling_Ai.py        (LLM decision logic for the call agent — patched to avoid module-level face_recognize import)

│       ├── speech_to_text.py    (AssemblyAI integration)

│       ├── text_to_speech.py    (Deepgram integration)

│       ├── file_to_text.py      (Tesseract OCR)

│       ├── config/              (CrewAI agent + task YAMLs — incl. 6 new from the AGENTS audit: lab_report_agent/task.yaml, medicine_interaction_agent/task.yaml, symptom_triage_agent/task.yaml)

 │       └── tools/

│           ├── custom_tool.py

│           ├── google_cal.py

│           └── credentials.json (Google OAuth — committed to repo, currently placeholder values)

│

└── frontend/                    (= G.A.N.G.U-Frontend repo)

└── frontend/                (actual Vite project root — note the nested folder)

           ├── package.json

├── src/

│   ├── App.jsx           (BrowserRouter + 10 routes)

      │   ├── main.jsx

│   ├── index.css        (global font import + ivory background)

│   ├── hooks/

│   │   └── useUser.js   (localStorage-based session hook)

│   ├── components/

│   │   ├── Layout.jsx   (shared nav + ambient background, used by every page except EmergencyView)

│   │   └── Layout.css   (shared nav styles + reusable utility classes: .ms-card, .ms-btn-primary, etc.)

│   └── Pages/

│       ├── Hero_Page.jsx / .css       (Home — luxury hero, rotating ceramic donut nav)

      │       ├── FindMedicine.jsx / .css     (symptom search + prescription upload, wired to backend)

│       ├── Compare.jsx / .css          (price comparison, mock data, confirm-before-cart UI)

│       ├── Appointments.jsx / .css     (AI call booking form + hospital list, wired to backend)

│       ├── HealthInfo.jsx / .css       (vitals + timeline + Emergency Medical ID + QR, wired to backend)

│       ├── Auth.jsx / .css             (login/signup, wired to backend)

     │       ├── Donor.jsx / .css            (blood donor registration + matching, wired to backend)

│       ├── EmergencyView.jsx / .css    (public, no-login QR-scan landing page)

│       ├── LabReport.jsx / .css        (lab report upload + plain-language breakdown, live-tested and confirmed working; saved-report history not yet surfaced — see Health Trends roadmap item)

│       ├── MedicineCheck.jsx / .css    (medicine interaction checker + symptom triage on one page, live-tested and confirmed working)

            │       ├── Landing_page.jsx            (OLD — unused G.A.N.G.U splash screen, not deleted)

│       ├── Browse_Medicine.jsx         (OLD — unused, superseded by Compare.jsx)

│       ├── Call_Form.jsx               (OLD — unused, superseded by Appointments.jsx)

│       ├── Nearby_Hospital.jsx         (OLD — unused, superseded by Appointments.jsx)

            │       ├── Record_Form.jsx             (OLD — unused, superseded by HealthInfo.jsx)

│       └── Image_Uploader.jsx          (OLD — unused, superseded by FindMedicine.jsx)

            └── src/Animations_js/Galaxy.jsx, Animations_css/Galaxy.css  (OLD — unused WebGL starfield, never wired in)

## Setup Instructions

### Prerequisites (Windows, the user's actual environment)
- Python **3.11.x** (NOT the system's default 3.14 — CrewAI's dependency tree requires `>=3.10,<3.14`)
- Node.js (any recent version; v24 confirmed working)
- Git
- CMake (must be on PATH — install from cmake.org, not via pip)
- Visual Studio Build Tools, "Desktop development with C++" workload (required to compile `dlib` if still present as a dependency)

### Backend setup
```powershell
cd backend
py -3.11 -m venv venv          # or: uv venv --python 3.11 (creates .venv instead)
.\venv\Scripts\Activate
python -m ensurepip --upgrade  # uv-created venvs may lack pip
python -m pip install -e .
```

**Known install gotchas** (already solved once, documented for repeatability):
- `dlib==20.0.0` fails to build on Windows even with CMake + VS Build Tools installed in a normal terminal. Fix used: install a **prebuilt wheel** instead —
  `python -m pip install dlib-19.24.1-cp311-cp311-win_amd64.whl` (sourced from `github.com/z-mahmud22/Dlib_Windows_Python3.x`), then let `pip install -e .` skip rebuilding it ("Requirement already satisfied").
- `face_recognition_models` needs installing directly from GitHub: `pip install git+https://github.com/ageitgey/face_recognition_models` — but it imports `pkg_resources`, which modern `setuptools` (≥81) removed. Fix: `pip install "setuptools<81"`.
- **This entire face_recognition dependency chain is being phased out** by the `auth.py` rework — once `face_recognize.py` is fully removed, `dlib`/`face_recognition`/`face_recognition_models` can likely be dropped from `pyproject.toml` too (not yet done).

Environment variables needed (`.env`, not yet created by the user — keys to be regenerated, old ones discarded): `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `ASSEMBLY_API_KEY`, `DEEPGRAM_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, and a `MONGO_URI` (currently hardcoded in `db_connect.py` — must move to `.env`).

Run the API:
```powershell
python src/agents/main.py
# or: uvicorn agents.main:app --reload --port 8080
```

### Frontend setup
```powershell
cd frontend\frontend   # note the nested folder — the repo root only has package-lock.json
npm install
npm run dev
```

Open the printed local URL (typically `http://localhost:5173`).

## Development Workflow

1. The user runs everything locally on Windows for now — either bare-metal (`venv` + `npm run dev`) or via `docker compose up --build` (both work; Docker is closer to how it'd actually deploy). Nothing is publicly hosted/deployed yet (see "Roadmap" below).
2. **Security/secrets cleanup done** — Mongo URI, Gemini/Google/Groq API keys moved to `.env`, confirmed excluded from version control before the public push.
3. Feature work and frontend visual work are being done in tandem with Claude in conversation; **no automated tests exist yet** (see Roadmap).
4. The user's friend owns the original repos; MediSarthi is a derivative/rework, now pushed as its own public repo: **[github.com/GAUTAM-JAIN1/MediSarthi](https://github.com/GAUTAM-JAIN1/MediSarthi)** (private monorepo history squashed/cleaned before going public).

## Current Project Status

See `progress.md` for the detailed breakdown. Summary: backend environment is fully working; auth (JWT-based, `decisions.md` D37, with full signup profile fields), health records (vitals + timeline + Emergency QR Medical ID, soft-delete D35), blood donor system, price comparison, Doctor Visit QR (D32), Medicine Effectiveness (both phases, D29/D31), and all 4 CrewAI agents (Lab Report Analyser, Medicine Interaction Checker, Symptom Triage, Medicine Effectiveness) are **complete and live-tested**, including a real clinical-safety fix (duplicate-therapy false-negative for same-drug-different-brand pairs, D38). 11 frontend routes, all wired to the real backend. `face_recognize.py` and its entire dependency chain have been deleted. Security/secrets cleanup is done, Google Calendar OAuth uses a fresh dedicated Google Cloud project.

**Docker + CI — done, actively hardened.** The project runs via `docker compose up --build` (backend :8080, frontend :5173) and a GitHub Actions CI pipeline (`backend`/`frontend`/`docker-build` jobs) is fully green (`decisions.md` D36). A second round of Docker-adaptability fixes (`decisions.md` D39) closed out the remaining gaps found by actually exercising features through the container rather than just confirming it boots: the AI voice-calling feature's missing `ngrok` binary, hardcoded Windows paths in the price-comparison agent (Chrome executable path, per-site profile directories), and Ollama's container-network reachability for the RAG embedder. **Two Docker-specific items remain open:** a separate Groq model 404 in the price-comparison agent (`buying_agent.py`, not the same model as the rest of the crews), and a Groq TPM rate-limit hit on the Lab Report Analyser for unusually dense reports (surfaced by an unrelated LLM-model swap in `crew.py`) — see `PROJECT_CONTEXT.md` §6, items 12 and 14.

**Actively being planned/built next:** resolving the two open Docker/Groq items above, then deployment (a live public demo link, the last major unstarted roadmap item) — see below.

## Roadmap (resume-strengthening, not yet built)

Brainstormed and prioritized in order of discussion, not yet committed to a build order:
- **Fix the two remaining open Docker/Groq items** — `buying_agent.py`'s separate model 404 (`PROJECT_CONTEXT.md` §6 item 12) and the Lab Report Analyser's TPM rate-limit on dense reports (§6 item 14, `decisions.md` D39).
- **Deployment** — get a live public demo link (currently fully local/Windows-only, either bare-metal or via `docker compose`).
- **RAG with a real vector store** — the current `TextFileKnowledgeSource` + Ollama-embedder setup already does real semantic search (not keyword lookup — see `decisions.md` D26), but a proper vector DB (Chroma/FAISS) with more/richer reference content would be a stronger NLP/LLM-engineering story.
- **Streaming responses** for the consultation flows (SSE), instead of wait-then-full-response.
- **Automated eval-case coverage for recent bug fixes** — e.g. the duplicate-therapy scenario from D38 isn't yet in `eval_harness.py`'s `interactions` suite.
- **WhatsApp bot integration** — reuses the existing Twilio account for a WhatsApp-based entry point, strong India-relevant social-impact narrative.

Already done, kept here for history: agent evaluation harness (✅), safety guardrail layer (✅), Docker + CI (✅ D36, hardened further in D39), basic automated tests in CI (✅, though coverage is still thin — 2 tests in `test_health.py`).