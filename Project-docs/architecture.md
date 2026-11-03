# architecture.md — MediSarthi System Architecture

This is the bird's-eye companion to `PROJECT_CONTEXT.md`. Where that file is
the exhaustive reference (exact function signatures, full endpoint table,
per-file detail), this file answers "how does the system fit together" —
layers, data flow, request lifecycle, and the design principles that show up
repeatedly across `decisions.md`. Read this first for orientation, then
`PROJECT_CONTEXT.md` when you need the precise current state of a specific
file or endpoint.

---

## 1. What MediSarthi is

A personal health assistant web app: symptom consultation (voice/photo),
prescription analysis, lab report analysis with trend tracking over time,
medicine price comparison, nearby hospital search, blood donor matching, and
two QR-based sharing mechanisms (permanent emergency ID, time-limited doctor
visit summary). Originally forked from a friend's project, substantially
reworked since — see `decisions.md` D1 onward for the reasoning behind each
major change.

**Primary goal:** resume/portfolio value through a considered engineering
narrative, not maximum feature count. This shows up throughout the codebase
as a preference for explainable tradeoffs over flashy-but-unconsidered
choices (see D1, D2 for the clearest examples).

---

## 2. High-level system diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  Browser (React SPA, Vite)                                          │
│                                                                       │
│   Pages (src/Pages/*.jsx) ── each owns its own useState, no global   │
│   state library. Login session lives in localStorage (useUser.js).  │
│                                                                       │
│   Two pages deliberately sit OUTSIDE <Layout> and need no login:    │
│   EmergencyView.jsx (/emergency/:token), DoctorVisitView.jsx        │
│   (/doctor-visit/:token) — both meant to be opened by someone with  │
│   no MediSarthi account, scanning a QR code.                        │
└───────────────────────────┬───────────────────────────────────────┘
                             │ fetch() — plain REST, JSON bodies,
                             │ no client library, CORS allow-all
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FastAPI backend (main.py) — single process, port 8080              │
│                                                                       │
│   Every route handler: thin. Parses request → calls a module        │
│   function or kicks off a CrewAI crew → shapes the response →       │
│   returns JSON. No business logic lives in main.py itself.          │
└───────┬───────────────────────┬───────────────────────┬─────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌────────────────────┐   ┌──────────────────────┐
│ Data modules   │    │ CrewAI agents      │   │ External services    │
│ (agents/*.py)  │    │ (crew.py, 9 crews) │   │                       │
│                │    │                    │   │ Groq (LLM, all crews)│
│ auth.py        │    │ Each @CrewBase     │   │ Ollama (local embed- │
│ health_records │    │ class: agent(s) +  │   │   der for RAG)       │
│   .py          │    │ task(s) + a        │   │ AssemblyAI (speech-  │
│ donor.py       │    │ .crew(user_id)     │   │   to-text)            │
│ db_connect.py  │    │ that returns a     │   │ Deepgram (text-to-   │
│                │    │ configured Crew.   │   │   speech)             │
│ Talk to Mongo  │    │                    │   │ Tesseract OCR (local)│
│ directly via   │    │ See §5 below for   │   │ Twilio (calls)        │
│ get_database() │    │ the shared-setup   │   │ Google Calendar API  │
│                │    │ pattern.           │   │ browser-use + Groq   │
│                │    │                    │   │   (price comparison, │
│                │    │                    │   │   real Chrome        │
│                │    │                    │   │   automation)         │
└───────┬────────┘    └──────────┬─────────┘   └───────────────────────┘
        │                        │
        ▼                        ▼
┌────────────────────────────────────────────┐
│  MongoDB Atlas — single database:           │
│  medical_db                                 │
│                                              │
│  Members, health_vitals,                    │
│  health_prescriptions, emergency_profiles,  │
│  emergency_qr_tokens, prescription_analyses,│
│  lab_report_analyses, doctor_qr_tokens      │
└──────────────────────────────────────────────┘
```

---

## 3. Backend layers

### 3.1 Entry point — `main.py`

FastAPI app, one process. Route handlers are deliberately thin: parse the
request into a Pydantic model, call into a data module (`health_records.py`,
`auth.py`, `donor.py`) or kick off a CrewAI crew, shape the return value,
done. No handler contains real business logic — that lives in the module or
the crew it calls.

Two request shapes recur throughout:
- **Simple CRUD** (vitals, prescriptions, emergency profile) → straight to a
  `health_records.py` function, no LLM involved.
- **LLM-backed** (consultation, lab analysis, interaction check, triage,
  effectiveness, clinical summary) → builds an `inputs` dict, instantiates a
  `SomeCrew().crew(user_id=...)`, calls `.kickoff(inputs=...)`, then walks
  `result.tasks_output` looking for a `.pydantic` attribute to extract the
  structured output. This exact extraction loop is copy-pasted at every
  crew call site rather than factored into a helper — flagged as a
  small available cleanup, not yet done.

### 3.2 Data modules (`agents/*.py`, non-crew)

- **`db_connect.py`** — single `get_database()` function, returns the
  `medical_db` Atlas database. Every other data module imports this; there
  is no second Mongo target anywhere in the project.
- **`auth.py`** — email+password (bcrypt), `Members` collection. Also owns
  `get_user_knowledge_profile(user_id)`, which every crew calls to write
  that user's `knowledge/user_<id>/profile.txt` before running.
- **`health_records.py`** — the largest data module by far. Owns 7 of the
  8 non-auth collections (everything except `Members`). See §6 below for
  the collection-by-collection breakdown.
- **`donor.py`** — blood donor registration, availability, matching by
  blood group + city + state.

### 3.3 CrewAI layer (`crew.py`)

9 `@CrewBase` classes as of this session. Every one follows the same shape:

```python
@CrewBase
class SomeCrew:
    agents_config = 'config/some_agent.yaml'
    tasks_config = 'config/some_task.yaml'

    @agent
    def some_agent(self) -> Agent: ...

    @task
    def some_task(self) -> Task: ...

    @crew
    def crew(self, user_id: str) -> Crew:
        knowledge_sources, embedder = _build_crew_base(user_id, "crew_name", ...)
        return Crew(agents=..., tasks=..., ...)
```

**`_build_crew_base(user_id, crew_name, inject_allergies=False,
shared_kb_files=None)`** is the one shared helper every crew calls. It:
1. Resolves the user's profile via `auth.get_user_knowledge_profile`.
2. Optionally injects known allergies into that profile file (for crews
   that need allergy-aware reasoning — prescription analysis, interaction
   checking, clinical summaries).
3. Sets a **per-crew** ChromaDB storage subfolder
   (`medical_memory/{user_id}/{crew_name}`) — this isolation matters: early
   on, all crews for one user shared one memory store, so one crew's
   agent could surface another crew's unrelated past results (see the
   fix note in `crew.py`'s own docstring).
4. Optionally attaches a second, SHARED (non-user-specific) knowledge
   source pointing at a curated reference file in `knowledge/medical_kb/`
   — this is the RAG mechanism (D26). 4 of the 9 crews use it:

| Crew | Shared reference file(s) |
|---|---|
| `LabReportCrew` | `lab_reference_ranges.txt` |
| `MedicineInteractionCrew` | `drug_interactions.txt` |
| `SymptomTriageCrew` | `symptom_red_flags.txt` |
| `MedicineEffectivenessCrew` | `test_direction_reference.txt`, `medicine_response_timelines.txt` |
| `ClinicalSummaryCrew` | `lab_reference_ranges.txt`, `test_direction_reference.txt` |

All 9 crews use `groq/llama-3.3-70b-versatile` (migrated off Gemini's
free-tier rate limit — see `crew.py`'s own migration comment). Embeddings
for RAG use a local Ollama model (`mxbai-embed-large`), not a Groq/OpenAI
embedding endpoint.

**Every crew output is a Pydantic model** (`output_pydantic=...` on the
task), never free-form text parsed after the fact — this was a deliberate
choice (D23) specifically so numeric/structured fields (chart values,
booleans, enums) come straight from the LLM's structured output instead of
being regex-extracted from a display string afterward.

### 3.4 External services

Groq (all LLM calls — two different models in play: `crew.py`'s CrewAI
crews use one, `buying_agent.py` uses another via `browser_use.ChatGroq`,
see D39/`PROJECT_CONTEXT.md` §6 items 12/14 for open issues with both),
Ollama (local embeddings only, reachable from inside Docker via
`host.docker.internal` + `OLLAMA_HOST=0.0.0.0` on the host process, D39),
AssemblyAI (speech-to-text), Deepgram (text-to-speech), Tesseract (OCR,
local binary — Windows path only used when `platform.system() ==
"Windows"`, PATH-resolved binary on Linux/Docker otherwise), `ngrok`
(tunnel for the AI voice-calling callback, installed via apt in the
Dockerfile as of D39), Twilio (phone calls), Google Calendar API (medicine
reminders), `browser-use` + Groq (real Chrome automation for price
comparison — see D21/D22 for why this is extraction-only with zero
purchase capability; Chromium is Playwright-installed, not a hardcoded
system Chrome path, as of D39).

---

## 4. Frontend layers

React SPA (Vite), `react-router-dom` for routing, no global state library —
every page owns its own `useState`. `useUser.js` is the one piece of
cross-page state, reading `ms_user_id`/`ms_user_name` from `localStorage`.

**`Layout.jsx`** wraps every page except the two public QR-landing pages
(`EmergencyView.jsx`, `DoctorVisitView.jsx`) — those are meant to be opened
by someone with no account and no reason to see the nav bar.

**Design tokens** live in `Layout.css` as CSS variables (`--ms-bg-primary`,
`--ms-luxury-brown`, etc. — see `PROJECT_CONTEXT.md` §4 for the full list).
Every page's CSS reuses these rather than redefining colors locally.

**Recurring frontend pattern — `extractErrorMessage(detail, fallback)`**:
FastAPI's validation error `detail` field is sometimes a string, sometimes
an array of `{type, loc, msg, input}` objects. This helper normalizes both
shapes to a plain string so no page ever crashes trying to render an error
object directly. Copy-pasted into most pages that call the backend rather
than imported from a shared module — a known, accepted duplication.

---

## 5. Request lifecycle — two representative flows

### 5.1 Simple CRUD (e.g. saving a vital)

```
HealthInfo.jsx  --POST /health/vital-->  main.py (health_add_vital)
                                              |
                                              v
                                     health_records.add_vital()
                                              |
                                              v
                                     health_vitals.insert_one()
                                              |
                                              v
                                    {status: "saved", record_id}
                                              |
                                              v
                              frontend re-fetches the timeline
```

No LLM involved. Fast, synchronous, single round trip.

### 5.2 LLM-backed (e.g. Doctor Visit QR generation, D32 — the most
involved flow in the system, touches every layer)

```
HealthInfo.jsx: user clicks "Doctor Visit QR Generate karo"
        |
        v
POST /health/doctor-qr/{user_id}
        |
        v
main.py gathers 3 things from health_records.py:
  - get_lab_report_analyses(user_id)   (Mongo read)
  - get_annotated_trends(user_id)      (Mongo read + medicine_test_map join)
  - get_prescriptions(user_id)         (Mongo read)
        |
        v
main.py formats all 3 into plain-text blocks for the LLM prompt
        |
        v
ClinicalSummaryCrew().crew(user_id).kickoff(inputs={...})
        |
        v
  _build_crew_base() runs first:
    - loads user profile, injects allergies
    - sets per-crew memory storage dir
    - attaches 2 shared reference files (RAG)
        |
        v
  crewai.Task runs against groq/llama-3.3-70b-versatile,
  grounded via Ollama-embedded retrieval over the shared KB files
        |
        v
  Structured output: ClinicalSummaryOutput
  (clinical_summary, key_flags, active_medicines_note, disclaimer)
        |
        v
main.py bundles {clinical_summary, lab_reports, trends, prescriptions}
into one "snapshot" dict
        |
        v
health_records.create_doctor_qr_token(user_id, snapshot, expiry_hours=24)
  -> inserts into doctor_qr_tokens, returns a fresh token
        |
        v
Response: {token, qr_url, expires_in_hours}
        |
        v
HealthInfo.jsx renders a QR encoding /doctor-visit/{token}


-- later, a doctor scans the QR on their own phone --

GET /health/doctor-qr/{token}   (no auth, no user_id needed)
        |
        v
health_records.get_doctor_qr_snapshot(token)
  - looks up the token doc
  - checks expires_at against now — returns None if expired
  - returns the cached snapshot (NO new LLM call)
        |
        v
DoctorVisitView.jsx renders it
```

The key architectural point this flow illustrates: **the LLM call happens
once, at generation time, not on every scan.** This "snapshot, not live
lookup" pattern is deliberate (see `decisions.md` D32) and is the opposite
of how the older Emergency QR works (`get_emergency_profile_public()` reads
the *live* profile on every scan, since there's no LLM step to amortize
there).

---

## 6. Data model — MongoDB collections (`medical_db`)

| Collection | Owner module | Written by | Read by |
|---|---|---|---|
| `Members` | `auth.py` | signup | login, every crew's `get_user_knowledge_profile` |
| `health_vitals` | `health_records.py` | `add_vital` | `get_vitals`, `get_full_timeline` |
| `health_prescriptions` | `health_records.py` | `add_prescription` | `get_prescriptions`, `get_full_timeline`, `get_annotated_trends` (medicine annotations), Doctor Visit QR snapshot |
| `emergency_profiles` | `health_records.py` | `save_emergency_profile` | `get_emergency_profile`, `get_emergency_profile_public` |
| `emergency_qr_tokens` | `health_records.py` | `generate_qr_token` | `get_emergency_profile` (merge), `get_emergency_profile_public` |
| `prescription_analyses` | `health_records.py` | `save_prescription_analysis` (permission-gated — only on explicit user confirm) | `get_prescription_analyses`, `get_prescription_analysis_by_id` |
| `lab_report_analyses` | `health_records.py` | `save_lab_report_analysis` (permission-gated) | `get_lab_report_analyses`, `get_test_trends`/`get_annotated_trends`, Doctor Visit QR snapshot |
| `doctor_qr_tokens` | `health_records.py` | `create_doctor_qr_token` **(NEW, D32)** | `get_doctor_qr_snapshot` |

**Permission-gated save pattern** (`prescription_analyses`,
`lab_report_analyses`): running a consultation or lab analysis never
auto-saves anything. The AI produces a result, the frontend shows it, and
only an explicit user action ("Save to records") calls the save endpoint.
This is deliberate — an analysis the user is just previewing shouldn't
silently become a permanent record.

**Two different QR-token lifetimes, deliberately** (see D32 for the full
reasoning): `emergency_qr_tokens` is permanent (one token per user,
regenerating replaces it) and exposes a narrow, low-sensitivity subset.
`doctor_qr_tokens` is time-limited (24h default), never replaces a prior
token on regenerate, and exposes the full clinical picture. These are not
two configurations of one mechanism — they're intentionally separate
collections with different exposure scope, because the token itself (not
just the app's rendering of it) determines what a lost/leaked QR reveals.

---

## 7. Recurring design principles

These show up repeatedly across `decisions.md` and are worth naming
explicitly, since a future change that violates one of them is usually a
sign something needs re-checking against the original reasoning:

1. **Structured LLM output over post-hoc parsing.** Every crew task uses
   `output_pydantic`. Numeric/chart-ready fields (`numeric_value`,
   `direction_correct`, etc.) come from the schema, never regex-extracted
   from prose afterward (D23).
2. **Static facts stay static; only genuinely uncertain judgment goes to
   an LLM.** The medicine↔test mapping (`medicine_test_map.py`) is a plain
   Python dict, not an LLM call — which medicines affect which tests is a
   fixed clinical fact, not something worth re-deriving (and risking
   hallucinating) on every request (D29).
3. **On-demand LLM calls over pre-computed ones, when the user might not
   look.** Medicine Effectiveness (D31) and Doctor Visit QR (D32) both
   avoid firing an LLM call automatically on page load — either gated
   behind an explicit button (effectiveness) or fired once at a clear
   user action (QR generation), never once per render of data the user
   may never open.
4. **Permission-gated persistence for AI output.** Nothing an agent
   produces is saved to the database without an explicit user action
   (§6 above). Previewing an analysis is free; keeping it is a choice.
5. **Separate token/data scope by sensitivity and lifetime, not by
   reusing one mechanism with more flags.** Emergency QR vs. Doctor Visit
   QR (D32) is the clearest example — different exposure scope and
   different lifetime means a genuinely separate collection and token
   type, not an extra field on the existing one.
6. **Human-in-the-loop for anything real-world-consequential.** The price
   comparison agent (`buying_agent.py`) can read and report prices but has
   no purchase capability at all — not "confirm before buying," but
   "cannot buy," full stop (D2, D21).
7. **Honest about what's built vs. what's tested.** Throughout
   `decisions.md`, "built" and "live-tested" are tracked as separate
   states (see D28, D31, D32) — a feature isn't treated as done until a
   human has actually exercised it against real data, not just until the
   code compiles/runs without error.

---

## 8. Known architectural gaps (not fixed, flagged deliberately)

- **~~No JWT/session mechanism~~ — RESOLVED (D37).** JWT auth (HS256,
  7-day expiry) is now live: `get_current_user_id` FastAPI dependency
  on 30+ endpoints, `authFetch` frontend wrapper. No refresh-token flow
  and no server-side revocation/blocklist — a leaked token stays valid
  until it naturally expires. Accepted tradeoff, not yet revisited.
- **No global error boundary or shared API client on the frontend.** Every
  page hand-rolls its own `fetch()` calls and `extractErrorMessage()`
  copy. Works, but means a backend response-shape change has to be
  updated in N places.
- **Crew-output extraction loop duplicated at every call site in
  `main.py`** (the `for task_output in result.tasks_output: ...` pattern)
  rather than factored into one helper.
- **~~Hardcoded Windows-only Tesseract path~~ — RESOLVED, was already
  correct.** `file_to_text.py` guards it behind
  `platform.system() == "Windows"`, falling through to the PATH-resolved
  binary on Linux/Docker (installed via `apt-get install tesseract-ocr`).
- **Docker + CI is done (D36), hardened with a second round of fixes
  (D39: `ngrok` binary, hardcoded Chrome/profile paths in
  `buying_agent.py`, Ollama container networking) — but two Docker/Groq
  items remain open:** `buying_agent.py`'s own Groq model 404s inside the
  container (separate model from the rest of the crews, not yet
  root-caused), and the Lab Report Analyser hits an 8000-TPM Groq rate
  limit on unusually dense reports after an unrelated model swap in
  `crew.py`. Neither blocks normal-sized requests. See `PROJECT_CONTEXT.md`
  §6 items 12 and 14, `decisions.md` D39.
- **No token-cleanup job** for either `emergency_qr_tokens` (less of an
  issue, one per user, upserted) or `doctor_qr_tokens` (more of one —
  every generate is a new document, expired ones just stop resolving but
  are never deleted).
- **Two shared-KB file path assumptions never independently re-verified**
  — `MedicineEffectivenessCrew` and `ClinicalSummaryCrew` both assume
  `test_direction_reference.txt` lives at
  `knowledge/medical_kb/test_direction_reference.txt`. Worth one
  verification pass covering both.

See `PROJECT_CONTEXT.md` §6 and §11 for the full, current list with more
detail on each.

---

## 9. Where to look next

- **Exact current endpoint table, function signatures, per-file status:**
  `PROJECT_CONTEXT.md`.
- **Why a specific non-obvious choice was made, alternatives considered,
  tradeoffs accepted:** `decisions.md` (chronological, D1 → D39 as of this
  writing).
- **What's done vs. in-progress right now:** `progress.md`.
- **Working conventions, house rules, things that must never change
  without explicit confirmation:** `CLAUDE.md`.