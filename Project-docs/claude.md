# CLAUDE.md — Operating Manual for Future Claude Sessions

This file exists so a brand-new Claude conversation can pick up this project correctly, without access to the original chat history. Read this file first, then `PROJECT_CONTEXT.md`, then `progress.md`, then `decisions.md`. Only open actual source files once you know what you're looking for.

## Project Identity

- **Name:** MediSarthi (rebrand of a friend's original project, `G.A.N.G.U` / `G.A.N.G.U-Frontend`).
- **Owner/user:** A student reworking a friend's existing codebase to make it portfolio/resume-grade, primarily for job applications. Not the original author of the codebase — operates as a contributor making deliberate product + engineering improvements.
- **Tone with the user:** The user communicates in Hinglish (Hindi+English mixed, Latin script) and expects replies in the same register — casual, direct, "bhai" included naturally, short sentences. This is an established conversational pattern from the whole project history, not a one-off preference.
- **User's technical level:** Comfortable following step-by-step terminal instructions, not a Python/React expert. Explanations should stay concrete and instructional (exact commands, exact file paths) rather than abstract. When giving files, always give the COMPLETE file so the user can do a direct drop-in replace — never give partial diffs or patches.
- **Platform:** User is on **Windows**, working inside a OneDrive-synced folder. Always assume PowerShell syntax for terminal instructions. The system default Python is **3.14** — the project venv uses **Python 3.11**. Always activate venv before any pip/python command or it silently targets the wrong interpreter.

## High-Level Architecture
Frontend (React, Vite)  ──HTTP──>  Backend (FastAPI, port 8080)

                       │

                           ├── CrewAI agents (Groq LLM — see Bug 3/D18; note buying_agent.py
                           │   uses a separate Groq model via browser_use.ChatGroq, not this one)

                      ├── MongoDB Atlas (medical_db)

               │     ├── Members collection (auth)

                    │     ├── health_vitals / health_prescriptions

                                       │     ├── emergency_profiles / emergency_qr_tokens

                      │     ├── donors collection (blood donor)

                           │     └── donation_requests collection

                               ├── Twilio/AssemblyAI/Deepgram/ngrok (voice calling —
                               │   ngrok needs its own apt install in Docker, see Bug 8/D39)

           ├── browser-use/Playwright (price scraping)

                   ├── Tesseract OCR

                                       └── Google Calendar API
Frontend session strategy: `user_id` saved to **localStorage** as `ms_user_id` after login. `useUser.js` hook reads it on every page. All backend endpoints that need `user_id` receive it via FormData (file-upload endpoints) or JSON body (everything else).

## How to Start the Backend (exact working command — CORRECTED, see note below)

```powershell
cd C:\Users\gauta\OneDrive\Desktop\MediSarthi\medisarthi\backend
.\venv\Scripts\Activate
python -m uvicorn agents.main:app --host 0.0.0.0 --port 8080 --reload --app-dir src
```

Then open `http://localhost:8080` (health check) or `http://localhost:8080/docs` (interactive API docs).

**⚠️ CRITICAL — DO NOT `cd src` before running uvicorn.** This was the documented command in earlier versions of this file and it is now confirmed WRONG. Stay in `backend/` as your working directory, and use `--app-dir src` to tell uvicorn where the `agents` module lives. This is not a style preference — it fixes a real bug (see "Known Fixed Bugs" below). Running from `backend/src/` (the old way) causes a hard-to-diagnose silent failure across every CrewAI-based endpoint.

**Common mistakes:**
- Running `uvicorn` without `python -m` — picks up system Python 3.14 which doesn't have the packages.
- **Running `cd src` first and then `python -m uvicorn agents.main:app ...` without `--app-dir`** — this used to be the documented way, but it breaks CrewAI's `TextFileKnowledgeSource` file lookup (see Known Fixed Bugs). Use `--app-dir src` from `backend/` instead.
- Forgetting `.\venv\Scripts\Activate` — causes `No module named 'fastapi'` or `No module named 'uvicorn'`.
- `.env` file must live in `backend/` (the working directory uvicorn is started from), not `backend/src/`. `load_dotenv()` reads relative to CWD.

## Known Fixed Bugs (read this before debugging anything that smells similar)

### Bug 1 — "File not found: knowledge\user_<id>\profile.txt" on every CrewAI endpoint
**Root cause:** CrewAI's `TextFileKnowledgeSource` (used in `_build_crew_base()` in `crew.py`) resolves its `file_paths` as relative paths against the process's **current working directory**, using a hardcoded `"knowledge"` prefix (CrewAI internal constant `KNOWLEDGE_DIRECTORY = "knowledge"` — there is no constructor parameter to override this in CrewAI 0.203.2, confirmed by reading the installed package source). Meanwhile `auth.py`'s `get_user_knowledge_profile()` always writes the actual file to an **absolute** path: `backend/knowledge/user_<id>/profile.txt`.
As long as uvicorn was started from `backend/src/` (the old documented command), CWD was `backend/src/`, so CrewAI looked for `backend/src/knowledge/...` — which never existed — while the real file sat one level up at `backend/knowledge/...`. Every CrewAI crew (all 7 — the original 4 and the 3 new ones from the AGENTS audit) was affected, not just the new ones.
**Fix applied:** Start uvicorn from `backend/` using `--app-dir src` instead of `cd src` first. This makes CWD = `backend/`, which matches where `auth.py` actually writes the file. No code changes were needed — this was a working-directory bug, not a logic bug.
**If you ever reintroduce a `cd src` step or move the start command, this bug will silently come back.** Don't "fix" `crew.py`'s path logic instead — it's correct as written for whatever CWD it's launched from; the start command is the actual contract.

### Bug 2 — `litellm.AuthenticationError: API key not valid` on every CrewAI endpoint
**Root cause:** No `.env` file existed anywhere in the project (confirmed via recursive search), and no system environment variable was set either. `crew.py`'s `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")` was silently `None` the entire time. This means it's unverified whether the "confirmed working" status of the original 4 crews (`SpeechCrew`, `FileCrew`, `Nearbyhospitals`, `general_que`) in `progress.md` was ever actually re-tested after `.env` went missing, or whether that status predates this regression.
**Fix applied:** Created `backend/.env` (note: in `backend/`, not `backend/src/`, since that's the working directory `load_dotenv()` resolves against now) with a fresh `GEMINI_API_KEY` and `GOOGLE_API_KEY` from Google AI Studio (https://aistudio.google.com/app/apikey).
**Don't assume `.env` exists just because the code references `os.getenv(...)` everywhere — verify it's actually present and the working directory matches before debugging further upstream.**

### Note — Free tier rate limits are expected, not a bug
Gemini's free tier (`gemini-2.5-flash`) has a per-minute token quota (observed: 250,000 tokens/minute as of this session). Running several CrewAI test calls back-to-back within ~1 minute can trigger `litellm.RateLimitError: RESOURCE_EXHAUSTED`. This is NOT a code bug — wait ~30-60 seconds and retry. Don't go chasing this as a logic error.

**Update from a later session:** this quota wall became disruptive enough that the LLM provider was switched to **Groq** for at least the hospital-finder path (see Bug 3 below and `decisions.md` D18) — if you hit Gemini-specific errors going forward, first check which provider the relevant crew is actually configured to use.

### Bug 3 — LLM provider migrated Gemini → Groq (⚠️ exact scope still not re-verified — deliberately deferred)
**What happened:** Persistent Gemini free-tier quota issues (see the rate-limit note above) led to switching CrewAI's LLM provider to Groq (Llama-based models, also free). This is confirmed for the hospital-finder path (the format-drift bug below only makes sense if Groq is in play there) but **not re-verified whether this is project-wide across all 7 crews** — the exact `crew.py` LLM config and `.env` key name (`GROQ_API_KEY` or similar) weren't preserved in the handoff into the session that wrote this entry.
**Status:** User has explicitly deprioritized re-verifying this for now ("groq config baad mein verify kar lenge") in favor of the Health Trends feature and other resume-boost work. Still open, not urgent — pick up when there's a natural reason to touch `crew.py` again.
**Action for whenever it's picked up:** Open `crew.py`'s LLM/`llm=` config and `.env` to confirm the exact setup, then remove this ⚠️ once confirmed (and update `PROJECT_CONTEXT.md` §2.2 + this entry together).

### Bug 4 — Hospital list rendered blank because the parser only handled one LLM's markdown style
**Root cause:** `main.py`'s `parse_hospital_list()` was written against one LLM provider's output style (Gemini, bold markdown). After the Groq migration (Bug 3), Groq's Llama output used a different style (backticks) for the same data — the parser silently matched nothing, so the hospital list array came back empty even though the backend itself was working and the LLM had produced a real answer. This was first mistaken for "backend not restarted with new code" (also independently true at the time, which delayed finding the real cause).
**Fix applied (root-cause, not a patch):** `config/hospital_task.yaml`'s `reporting_task` now explicitly locks the exact output format instead of leaving markdown styling up to the model: `* **Hospital Name**: Address | Phone: phone-number-or-Not-available`, bold-only, one hospital per line, no extra commentary. `parse_hospital_list()` was rewritten around this locked format, with backward-compatible fallback parsing for the old Gemini-bold and Groq-backtick styles already seen. See `decisions.md` D19.
**General lesson — apply proactively to future crews:** any CrewAI task whose output is *parsed by code* (not just shown as freeform markdown to a user) should have its exact output format locked in the task YAML from the start, not left to the model's discretion. Don't wait for a format-drift bug to force this fix on a new crew — apply it upfront.

### Feature note — Hospital phone numbers via Nominatim `extratags=1` (not a bug, but related to the above)
`tools/custom_tool.py` now passes `extratags=1` to Nominatim's `/search` API, which returns OSM tags (`phone`, `contact:phone`, `contact:mobile`) for free, in the same request, when a listing has one. No new API key, no billing — see `decisions.md` D20 for why a paid API (Google Places) was deliberately not used. Coverage is partial (OSM crowdsourced data) — `parse_hospital_list()` converts `"Not available"` to `null` so the frontend's existing `h.phone &&` checks keep working correctly.

### Bug 5 — `buying_agent.py` clicked "Add to cart" automatically, violating D2
**Root cause:** An earlier version of `buying_agent.py` had its browser-use agent decide a single "winning" deal across sites and then click "Add to cart" on that site's page directly — re-introducing the exact auto-purchase behavior D2 had already explicitly ruled out, at the code level rather than anywhere visible in the frontend.
**Fix applied:** `buying_agent.py` was rewritten so the agent(s) **only ever extract and report data** (price, quantity, delivery info, product URL) — there is no code path left anywhere in the file that clicks "Add to cart," "Buy now," or any checkout-path button. "Best price"/"fastest delivery" tags are computed afterward in plain Python, not decided or acted on by the agent. `Compare.jsx`'s "Buy" action is just an outbound `<a href>` link to the pharmacy's own page. See `decisions.md` D21 — this also means D2's originally-described `idle → confirming → added` confirm-step UI was never actually built, because there's no purchase action left to confirm.
**Don't reintroduce any purchase/cart-click capability into `buying_agent.py` without an explicit, fresh conversation with the user** — this is now enforced more strictly than D2 originally required, not less.

### Bug 6 — Nested Pydantic schema crashed browser-use's `extract` tool with a `$defs` error
**Root cause:** `buying_agent.py`'s per-site agent originally used a nested Pydantic model (e.g. a list of `PharmacySiteResult` objects) as its `output_model_schema`. Pydantic generates a `$defs`/`$ref` section in the JSON schema for any nested `BaseModel`. When `use_vision=False` forced the agent onto browser-use's internal lightweight `extract` tool (used to read page text without a screenshot), that tool's schema validator didn't resolve `$defs` and raised `"Unsupported JSON Schema keyword: $defs"`. It then silently fell back to unstructured free-text extraction, returning generic page text instead of the actual product data — even though the agent had successfully navigated to the right page, which made this confusing to diagnose (the agent's *navigation* logs looked completely correct).
**Fix applied:** The per-site output schema (`SingleSiteOutput`) now uses a flat `medicines: List[Dict[str, Any]]` instead of a list of nested models. A flat dict field generates no named `$ref`/`$defs` entry, so the bug is sidestepped regardless of whether `use_vision` ends up `True`/`False`/`"auto"` later. `_to_pharmacy_result()` defensively rebuilds proper `PharmacySiteResult` objects from each raw dict afterward and skips (doesn't crash on) any malformed entry. See `decisions.md` D22.
**General lesson:** if a future browser-use `Agent`'s `output_model_schema` includes a nested Pydantic model and might ever go through the `extract` tool fallback (`use_vision` False or `"auto"`), flatten it proactively rather than waiting for the same `$defs` failure to reappear — same proactive-fix philosophy as Bug 4's lesson about locking CrewAI task output formats upfront.

### Bug 7 — `/lab/analyse` fell back to raw PDF bytes as "text" when PDF extraction failed, produced garbled analysis that looked like a knowledge-base bug
**Root cause:** `extract_text_from_image()` (PIL-based) was called unconditionally on every `/lab/analyse` upload. PIL cannot open a PDF, so it always raised on PDF uploads; the surrounding `except Exception: read raw file bytes as text` fallback then silently handed `LabReportCrew` the literal PDF binary (`%PDF-1.4 ... stream ... endobj`) as if it were the extracted report text. `LabReportCrew` correctly reported "this doesn't look like a lab report" — which reads exactly like a RAG/knowledge-base retrieval problem at first glance, and cost real debugging time confirming it wasn't before the actual raw-bytes fallback was found in `main.py`.
**Fix applied:** New `extract_text_from_lab_document(file_path)` in `main.py` — non-PDF files still go through the unchanged `extract_text_from_image()`; PDFs get `pdfplumber` direct text extraction (page by page), falling back to `pdf2image` (PDF page → image) + the same Tesseract OCR setup only when `pdfplumber` finds no embedded text (i.e. a scanned/photo-as-PDF). Raises a clean `ValueError` if neither path yields text — `/lab/analyse` converts that into an explicit `400`, never a silent raw-bytes fallback. See `decisions.md` D27.
**Don't reintroduce a bare `except: read raw bytes` fallback anywhere text extraction can fail** — a failed extraction should surface as an error, not as garbage input to an LLM. This is the same "fail loud, don't silently degrade" lesson as Bug 4/D19's parser-drift story, applied to file I/O instead of markdown parsing.
**Related, still open:** the OCR fallback path needs Poppler binaries on PATH (Windows: manual install, not yet confirmed done by the user) — only required for scanned/photo PDFs, not the tested text-based-PDF path. `PROJECT_CONTEXT.md` §6 item 5's separate Windows-only Tesseract path concern is now resolved (see Bug 8 below) — Poppler is installed via the Dockerfile's apt-get step for the Docker path specifically.

### Bug 8 — Docker adaptability round 2: `ngrok` binary missing, hardcoded Windows paths in `buying_agent.py`, Ollama unreachable from inside the container
**Root cause (three separate issues, same underlying pattern as D36's original 5 Docker fixes):** things that worked fine on bare-metal Windows dev broke silently or hard-failed once actually exercised *through* the container, not just at boot time.
1. **`ngrok` binary wasn't installed in the backend image at all** — `Calling.py`'s `/call/schedule` feature had only ever run against a native Windows ngrok install; `NGROK_AUTHTOKEN` was correctly present as an env var, but `exec: "ngrok": executable file not found in $PATH`. Same root cause also explained an earlier `curl not found` error while manually testing Ollama connectivity — neither binary ships with `python:3.11-slim` by default.
   **Fix:** added the official ngrok apt repo + `apt-get install -y ngrok curl gnupg` as a new Dockerfile layer (fixes both binaries at once). `Calling.py` also now passes `--authtoken` explicitly on the command line as a more reliable fallback.
2. **`buying_agent.py` had three hardcoded-Windows-path bugs**: `APOLLO_PROFILE_DIR`/`ONEMG_PROFILE_DIR` were literal `C:\agent_profile_...` paths (fixed to a portable construction), the Playwright launch had `executable_path="C:\\Program Files\\Google\\Chrome\\..."` hardcoded (removed — now uses the Chromium the Dockerfile already installs via `playwright install --with-deps chromium`), and the Ollama embedder URL was hardcoded to `http://localhost:11434/...` (now `os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434/...")`).
3. **Ollama wasn't reachable from inside the container** — `localhost` inside a container isn't the same network namespace as the Windows host running `ollama serve`. Fixed by setting `OLLAMA_HOST=0.0.0.0` on the host-side Ollama process (so it accepts non-loopback connections) combined with fix #2's env-var-driven URL, pointed at `host.docker.internal` instead of `localhost`.
**Don't assume a feature that only ever ran on bare-metal will "just work" in Docker** — same lesson as D36, now covering third-party CLI binaries and browser-automation executable/profile paths specifically, not just Python import-time system libraries. See `decisions.md` D39, `progress.md`'s latest session entry.
**Still open, not fixed by this round:** `buying_agent.py`'s own Groq model (`meta-llama/llama-4-scout-17b-16e-instruct`, separate from `crew.py`'s models) still 404s inside Docker — not investigated this round. Separately, a Groq TPM (8000/min) rate limit was hit on `/lab/analyse` for dense reports after `crew.py`'s model was swapped to `groq/openai/gpt-oss-120b` — retry/backoff and prompt-chunking fixes were discussed but not yet implemented. See `PROJECT_CONTEXT.md` §6 items 12 and 14.

## Coding Conventions

### Backend (Python)
- FastAPI endpoints live in `main.py`. Each endpoint: try/except wrapping core logic, raises `HTTPException` with explicit status codes on failure.
- Pydantic models for all request bodies (see `SignupRequest`, `LoginRequest`, `LocationRequest`, `VitalRequest`, `EmergencyProfileRequest`, donor request models in `main.py`).
- CrewAI logic stays in `crew.py`. Each crew class follows the `@CrewBase` + `@crew` decorator pattern.
- `crew.py` now has **7 crew classes**: original 4 (`SpeechCrew`, `FileCrew`, `Nearbyhospitals`, `general_que`) + 3 added in the AGENTS audit session (`LabReportCrew`, `MedicineInteractionCrew`, `SymptomTriageCrew`). Any new crew added in future must follow this same pattern (own YAML agent+task config pair in `config/`, `.crew(user_id)` signature).
- `user_id` is passed as a parameter directly to the `crew()` method: `def crew(self, user_id: str) -> Crew:`.
- Per-user state (CrewAI knowledge files) is keyed by `user_id`, written to `knowledge/user_<id>/profile.txt` — **always relative to `backend/`, regardless of where uvicorn's CWD ends up being. See "Known Fixed Bugs" above before touching anything related to this.**
- `auth.py` reuses `db_connect.py`'s `get_database()` directly — no second Mongo target. `health_records.py` and `donor.py` do the same.
- Secrets (Mongo URI, Gemini/Google/Groq API keys) now live in `.env` — cleanup done pre-push, don't hardcode new ones back in.
- **API response-shape rule (added after a recurring bug class):** GET endpoints that return a single record should return it **flat** (`return profile`), not wrapped (`{"profile": profile}`) — the frontend pages in this project consistently read fields off the response root, never off a nested wrapper. List endpoints (timeline, vitals list, donors list) keep their existing wrapped shape (`{"timeline": [...], "count": n}`) since the frontend already expects that wrapper there. Before adding a new GET endpoint, check the actual frontend code path that will consume it — this codebase has hit silent field-shape mismatches (wrapped vs. flat, list vs. string, `type` vs `record_type`) multiple times; matching the frontend's already-written shape is cheaper than re-deriving a "cleaner" one and then fixing it later.

### Frontend (React)
- All custom CSS classes are prefixed `ms-` (e.g. `ms-card`, `ms-btn-primary`, `ms-page-title`).
- Shared, reusable styles live in `src/components/Layout.css`. Page-specific styles in a co-located CSS file.
- Every page is wrapped in `<Layout>...</Layout>` from `src/components/Layout.jsx` — **except** `EmergencyView.jsx`, which is deliberately rendered outside `<Layout>` (no nav bar) since it's a public, login-free, distraction-free emergency-ID view.
- Icons: exclusively `react-icons/lu` (Lucide set).
- QR rendering: `qrcode.react`'s `<QRCodeSVG>` component — used in `HealthInfo.jsx` to render the emergency QR.
- React Router routes declared in `App.jsx`. Current routes (**10**): `/`, `/find-medicine`, `/compare`, `/appointments`, `/health-info`, `/auth`, `/donor`, `/emergency/:token`, `/lab-report`, `/medicine-check`.
- **Session strategy:** `useUser.js` hook (at `src/hooks/useUser.js`) reads `ms_user_id` + `ms_user_name` from localStorage. Every page that needs the user should call `const { userId, isLoggedIn, logout } = useUser()`.
- **Error-display safety rule (added after two real crashes):** FastAPI's `detail` field on a 4xx/5xx response is sometimes a plain string, sometimes a list of `{type, loc, msg, input}` validation-error objects. Never render `data.detail` directly into JSX. Every page that displays a backend error message should use a local `extractErrorMessage(detail, fallback)` helper (already present in `Auth.jsx`, `HealthInfo.jsx`, `EmergencyView.jsx`, `FindMedicine.jsx`, `LabReport.jsx`, `MedicineCheck.jsx`) before setting it into state that gets rendered. New pages with error-message display must add this same helper.
- **Filenames are case-sensitive on deploy even though Windows isn't** — match import casing exactly.

## Folder Conventions

- Backend project root: `C:\Users\gauta\OneDrive\Desktop\MediSarthi\medisarthi\backend\`
- All Python sources: `backend\src\agents\`
- `.env` file lives at `backend\.env` (NOT `backend\src\.env`) — see "How to Start the Backend" above for why this matters.
- Frontend project root: `frontend\frontend\` (**note the doubled folder name**).
- New backend modules go in `src/agents/` alongside existing files.
- New frontend pages go in `src/Pages/`, new shared components in `src/components/`, new hooks in `src/hooks/`.

## Auth Flow (COMPLETE — how it works end to end)

1. User goes to `/auth` → sees `Auth.jsx` (Login/Signup tabs).
2. On success, backend returns `{ user_id, name, ... }`.
3. Frontend saves `ms_user_id` and `ms_user_name` to localStorage.
4. User is redirected to `/` (home).
5. Any page calls `useUser()` hook to get `userId`.
6. When making API calls, pass `userId` in FormData (file uploads) or JSON body (`user_id` field) as appropriate per endpoint.
7. Logout: `useUser().logout()` clears localStorage and redirects to `/auth`.

## UI Rules — Design System (do not deviate without explicit user request)

**Design tokens (CSS variables, defined in `Layout.css`):**
```css
--ms-bg-primary: #F6F1EA;     /* warm ivory page background */
--ms-bg-secondary: #EEE6DC;   /* secondary/active nav background */
--ms-white-card: #FFFFFF;
--ms-text-primary: #111111;
--ms-text-secondary: #6B625D;
--ms-luxury-brown: #9C6B45;   /* primary accent */
--ms-soft-gold: #D7B895;      /* secondary accent, particles, borders */
--ms-dark-navy: #0F1720;      /* used only for dark feature cards on light bg */
--ms-btn: #6F472D;            /* primary button background */
```

**Typography:** Playfair Display for headings, Inter for body.

**Signature visual element:** Rotating "ceramic donut" — 6 SVG pie-segments in `Hero_Page.jsx`'s `DONUT_PATHS` and `SEGMENTS` arrays — reuse, don't regenerate.

**Never reintroduce:** dark-mode-by-default pages, glassmorphism/heavy blur, generic purple-to-blue gradients, sidebar navigation.

## Backend Rules

- Don't reintroduce face-recognition-based identification.
- Don't add any "add to cart"/purchase capability to `buying_agent.py` or anywhere else — the app never touches a cart at all, not even behind a confirm step (see Known Fixed Bugs Bug 5, `decisions.md` D21).
- All 7 crew classes in `crew.py` take `user_id: str` on `.crew()`.
- **`face_recognize.py` has been deleted** (confirmed no other file imported it — only comment references remained in `auth.py`/`Calling_Ai.py`). `face-recognition`, `face-recognition-models`, `dlib`, `opencv-python`, and `cmake` were also removed from `pyproject.toml` since nothing in the codebase uses `cv2`/`dlib` anymore. Don't reintroduce any of this without a fresh, explicit reason.
- Emergency profile fields (`allergies`, `critical_conditions`, `medicines`) are stored as **plain strings**, not lists — deliberate, matches the single-text-input frontend UI. Don't "improve" these back into `List[str]` without updating both `HealthInfo.jsx` and `EmergencyView.jsx` together.
- Don't reintroduce a `cd src` step into the backend start command — see "Known Fixed Bugs" above. The current `--app-dir src` approach is deliberate and fixes a real bug, not a style choice.

## Things That Must NEVER Change (without explicit, fresh user confirmation)

1. The visual design system (colors, fonts, donut ring concept, ivory/ceramic aesthetic).
2. Email+password auth instead of face recognition.
3. No automated purchase/cart action of any kind in `buying_agent.py` or anywhere else — the app never adds anything to a cart on the user's behalf, full stop (stronger than the original "confirm before cart" framing; see Known Fixed Bugs Bug 5 and `decisions.md` D21).
4. Keeping the AI voice-calling feature and live price-scraping feature.
5. The `ms-` CSS class prefix and the `Layout`-wraps-every-page pattern (except `EmergencyView.jsx`, intentionally Layout-free).
6. localStorage-based session (`ms_user_id`) — this is the decided session strategy.
7. Emergency profile data as plain strings + flat (unwrapped) GET response shape for single-record endpoints.
8. The `--app-dir src` backend start command (see Known Fixed Bugs) — this is a verified bug fix, not a preference.
9. `config/hospital_task.yaml`'s locked hospital-list output format (see Known Fixed Bugs, Bug 4) — don't loosen this back to freeform `markdown: true` without re-checking `parse_hospital_list()` first; this is a verified bug fix, not a style preference.

## Documentation Reading Order

1. `CLAUDE.md` (this file) — orientation and rules.
2. `PROJECT_CONTEXT.md` — dense technical reference.
3. `progress.md` — what's done, what's half-done, what's next.
4. `decisions.md` — the *why* behind unusual choices.
5. Only then, open actual source files.

## Common Mistakes to Avoid

- Don't assume `pip`/`python` point at the right interpreter — always activate venv first.
- **Don't `cd src` before running uvicorn** — use `--app-dir src` from `backend/` instead (see Known Fixed Bugs).
- Mongo URI + API keys are now in `.env` (secrets cleanup done pre-push) — don't hardcode credentials back into `db_connect.py` or anywhere else.
- Don't add new npm/pip dependencies casually — flag heavy native deps to the user.
- Don't silently rename existing CrewAI class/method names (`Nearbyhospitals`, `general_que`).
- Don't regenerate the donut-ring geometry from scratch.
- Don't assume a new backend endpoint's response shape — check what the already-written frontend page expects to consume, then match it (see Coding Conventions above). This exact class of bug (wrapped vs flat, list vs string, key-name mismatch) has happened repeatedly in this project (Auth.jsx, HealthInfo.jsx vitals, emergency-profile).
- Don't assume `.env` exists just because code reads `os.getenv(...)` — verify the file is actually present at `backend/.env` before debugging further (see Known Fixed Bugs, Bug 2).
- If you see "File not found: knowledge\user_<id>\profile.txt" or a Gemini "API key not valid" error, go straight to "Known Fixed Bugs" above instead of re-diagnosing from scratch.
- If the hospital list comes back empty/blank on the frontend even though the backend looks fine, go straight to "Known Fixed Bugs" Bug 4 (parser/LLM-format-drift) instead of re-diagnosing from scratch — don't assume it's a backend-not-restarted issue without first checking the output format actually matches what `parse_hospital_list()` expects.
- Always give COMPLETE files — never partial diffs.

## How Future Claude Sessions Should Continue Development

1. Read this file + `PROJECT_CONTEXT.md` + `progress.md` fully before writing any code.
2. **Current active thread (as of this update): Docker adaptability, round 2 — MOSTLY DONE (D39), two Groq-related items still open.** `ngrok` binary install, hardcoded Windows paths in `buying_agent.py` (Chrome executable, profile dirs), and Ollama container-networking (`host.docker.internal` + `OLLAMA_HOST=0.0.0.0`) are all fixed and pushed to GitHub (commit `0ae8532`). **Two things to pick up next:** (a) `buying_agent.py`'s own Groq model (`meta-llama/llama-4-scout-17b-16e-instruct`) still 404s inside Docker — not yet root-caused, separate from the model `crew.py` uses; (b) a Groq 8000-TPM rate limit was hit on `/lab/analyse` for dense reports after `crew.py`'s model was swapped to `groq/openai/gpt-oss-120b` — retry/backoff and/or prompt-chunking fixes were discussed but not implemented yet. See `decisions.md` D39, `PROJECT_CONTEXT.md` §6 items 12/14, and `progress.md`'s latest session entry for full detail. Medicine Effectiveness (both phases) and the Medicine Interaction Checker's duplicate-therapy safety fix (D38) are both done and live-tested — don't re-raise those unless something looks broken.
3. **Already resolved, don't re-raise unless something looks broken:** signup form fields (age/gender/city/state/allergies — done in `Auth.jsx`), `face_recognize.py` + its dependency chain (deleted), security/secrets cleanup (done), Google Calendar OAuth (fresh project, done), FindMedicine.jsx UI redesign (done), all 4 CrewAI agents (Lab Report Analyser, Medicine Interaction Checker, Symptom Triage, Medicine Effectiveness) live-tested and confirmed, safety guardrails (D24), agent eval harness (D25), RAG shared knowledge base (D26), Health Trends feature (D23) including its PDF-extraction bug (D27) and report-date chronology bug (D28), Doctor Visit QR (D32, built not yet live-tested), JWT auth (D37, live-tested on bare-metal), soft-delete (D35), Docker + CI first round (D36, container boots clean, CI green) and second round (D39, see above).
4. **Deliberately deferred, not forgotten:** which reasoning led to `crew.py`'s Groq model swap (`llama-3.3-70b-versatile` → `openai/gpt-oss-120b`) was never written up as its own decision record — worth doing if it isn't documented elsewhere, especially since that swap is what surfaced the new TPM rate-limit issue above. Confirming Poppler is on PATH for the scanned-PDF OCR fallback on bare-metal Windows (Bug 7) — not urgent, only affects photo-as-PDF uploads outside Docker (the Docker path already has Poppler via apt-get). A cosmetic mojibake em-dash encoding issue in a few comment/print strings — flagged during D39's diff review, not fixed.
5. Longer-term roadmap, order changed multiple times per the user's explicit direction — current order (see `README.md` "Roadmap" and `PROJECT_CONTEXT.md` §5): fix the two open Docker/Groq items above → deployment (a live public demo link, the last major unstarted item). Also still brainstormed-not-built: streaming consultation responses, a WhatsApp bot entry point, an automated eval-case for D38's duplicate-therapy fix.
6. When user pastes terminal output, diagnose precisely from the actual error text — don't guess field names, ask for the relevant source file(s) if not already available. Check "Known Fixed Bugs" above first in case it's a repeat.
7. Keep responses in Hinglish.
8. Always give COMPLETE file content for drop-in replace.