rogress.md

## 🆕 Latest session — Docker adaptability fixes: ngrok binary, hardcoded Windows paths removed, Ollama container networking confirmed, Groq model swap surfaces a new TPM rate-limit issue

Direct continuation of the previous session's "Docker E2E validation (in progress)" work below — same D36 thread, closing out most of what that session left open.

- [x] **Ollama RAG connectivity inside Docker — fixed and confirmed working.** Previous session's item 13 (open, non-urgent) is resolved: the embedder now reaches Ollama via `host.docker.internal:11434` instead of `localhost`, with `OLLAMA_HOST=0.0.0.0` set on the Windows-host `ollama serve` process so it accepts connections from the Docker network. Confirmed indirectly — a full `LabReportCrew` run against a dense multi-panel sample report reached the LLM call stage inside the container (RAG knowledge-source loading, which depends on the Ollama embedder, did not error out beforehand). The direct `curl`/`urllib` connectivity check itself (`docker compose exec backend curl http://host.docker.internal:11434/api/tags`) was run but its raw output wasn't captured in this doc-update pass — worth a quick explicit re-confirmation next session if anything about RAG grounding looks off.
- [x] **`docker compose up --build` — full rebuild confirmed successful**, including the `playwright install --with-deps chromium` step (Chromium + FFMPEG + Headless Shell, ~174MB) completing cleanly and `Uvicorn running on http://0.0.0.0:8080` starting with no import-time crash. Backend health check (`GET /`) returned `200 {"status":"active",...}`.
- [x] **`/call/schedule` (AI voice-calling feature, `Calling.py`) — root-caused and fixed: `ngrok` binary was never installed inside the backend image.** The container could reach `NGROK_AUTHTOKEN` fine (env var confirmed present via `printenv`), but `ngrok`/`curl` weren't on `$PATH` at all (`exec: "ngrok": executable file not found in $PATH`) — the feature previously only ever ran against a native Windows ngrok install, which obviously isn't present inside a Linux container. Fixed by adding the official ngrok apt repo + `apt-get install -y ngrok curl gnupg` as a new `RUN` layer in `backend/Dockerfile` (also incidentally fixes the earlier `curl not found` errors hit while testing Ollama connectivity, same root cause). `Calling.py` itself also now passes `--authtoken` explicitly on the ngrok command line as a fallback, instead of relying solely on the `NGROK_AUTHTOKEN` env var being picked up automatically.
- [x] **Three hardcoded-Windows-path bugs in `buying_agent.py` fixed — these were real Docker-adaptability blockers, not code-quality nitpicks:**
  - `APOLLO_PROFILE_DIR`/`ONEMG_PROFILE_DIR` were hardcoded to `C:\agent_profile_apollo` / `C:\agent_profile_1mg` — meaningless inside a Linux container (and a real bug on bare-metal too, per the fix's own comment).
  - `executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"` was hardcoded for the `browser-use`/Playwright launch — removed entirely, letting Playwright use its own installed Chromium (the one `playwright install --with-deps chromium` downloads in the Dockerfile) instead of pointing at a Windows-only binary path that doesn't exist in the container.
  - The Ollama embedder URL (`"http://localhost:11434/api/embeddings"`, hardcoded) is now read from `os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434/api/embeddings")` — same class of fix as the connectivity item above, now configurable per-environment instead of assuming bare-metal `localhost`.
  - **Confirmed already correct, no change needed:** `file_to_text.py`'s Tesseract path was already guarded behind `if platform.system() == "Windows":` before this session — verified by direct file review, this was a false alarm from an earlier doc pass (see `PROJECT_CONTEXT.md` §6 item 5, now marked resolved).
- [x] **`crew.py`'s Groq model swapped at all 13 `LLM(...)` call sites**, from `groq/llama-3.3-70b-versatile` to `groq/openai/gpt-oss-120b`. Reason for the swap wasn't re-derived in detail during this session (carried over from earlier work) — flagged here rather than assumed, since it's a meaningful behavior change worth its own decision record if the reasoning isn't already written up elsewhere.
- [ ] **NEW issue surfaced by the model swap above, not yet fixed: Groq TPM (tokens-per-minute) rate limit hit on `/lab/analyse`.** `POST /lab/analyse` against the dense multi-panel sample report (7 test panels + a long free-text clinical impression) returned `500 Internal Server Error` — root cause confirmed from the log: `litellm.RateLimitError: ... tokens per minute (TPM): Limit 8000, Used 3201, Requested 5447`. The org's Groq tier caps `openai/gpt-oss-120b` at 8000 TPM, and one call combining the full `LabReportCrew` system-prompt template (the long per-field instruction block: `test_name`/`value`/`status`/`action_needed`/etc.) plus a large extracted report's text pushes a single request over that limit on dense reports.
  - **Fixes suggested this session, none yet applied or tested:** (1) `num_retries`/backoff on the `litellm`/CrewAI LLM call so transient rate-limit hits self-heal; (2) trim/restructure the prompt so the long instruction block isn't resent in full for every call (static system message vs. variable content), or chunk very large reports panel-by-panel with results merged afterward, to keep any single call under 8000 tokens; (3) disable CrewAI's interactive tracing prompt (`Would you like to view your execution traces? [y/N] (20s timeout)`) via `CREWAI_TRACING_ENABLED=false`, since it has no TTY to answer in a container and adds up to 20s of dead time per crew run even though it doesn't currently cause a hard failure.
  - **Not yet confirmed:** whether the org is on Groq's free/on-demand tier (in which case chunking is a real requirement for any report this dense) or a paid dev tier (in which case backoff alone may be enough) — worth checking before deciding which fix to prioritize.
- [x] **Repo pushed to GitHub, secrets/paths reviewed first.** Full manual diff review before pushing: `git diff | Select-String` scans for API keys/tokens (clean — only `os.getenv(...)` references, no literal values), Windows-hardcoded paths (all resolved per above, except the already-correct conditional Tesseract path), and a mojibake encoding artifact in 2-3 comment/print strings (`—` em-dash rendered as `├óΓé¼ΓÇ¥` — cosmetic only, not fixed this session, flagged for a future cleanup pass). One untracked local helper script (`dump_docker_fixes.ps1`, used to bulk-collect files for this chat session) was deleted rather than committed — not part of the product. Pushed as commit `0ae8532` on top of `0824aa7`/`f46812d`, 10 files changed (271 insertions, 106 deletions): `backend/Dockerfile`, `backend/knowledge/medical_kb/drug_interactions.txt`, `backend/src/agents/Calling.py`, `Calling_Ai.py`, `buying_agent.py`, `config/medicine_interaction_task.yaml`, `crew.py`, `file_to_text.py`, `main.py`, `docker-compose.yml`.
  - **Also done:** the ngrok authtoken that had appeared in plaintext earlier in this chat session was regenerated via the ngrok dashboard, since it had been exposed in conversation even though it was never actually committed to git.

## Previous session — Docker E2E validation (in progress) + Medicine Interaction Checker duplicate-therapy bug FIXED + LIVE-TESTED ✅

- [x] **Medicine Interaction Checker — real safety bug found and fixed: false "safe" verdict for two brand names of the same drug.** Checking "Paracetamol" + "Dolo 650" together previously returned no interaction / safe-combination, which is wrong and unsafe — Dolo 650 *is* paracetamol under a brand name, so this is double-dosing, not a drug-drug interaction. Root-caused to two gaps: `medicine_interaction_task.yaml`'s prompt never asked the agent to check for shared active ingredients before pairwise-checking, and `drug_interactions.txt` (the RAG reference file) had no Indian brand→generic mapping at all. Fixed both layers: added a "Step 0 — identify active ingredients first" step to the task prompt (flags shared-ingredient pairs as a **Duplicate Therapy** finding, severity Major, with the safe daily limit stated), and added a brand↔generic mapping section to `drug_interactions.txt` (Dolo 650/Crocin/Calpol → Paracetamol, Combiflam/Brufen → Ibuprofen, etc.) so the fix doesn't rely on the LLM's own recall alone. **Re-tested by the user — "interaction shi work kr gya," confirmed working.** See `decisions.md` D38.
  - **Not yet done:** no automated eval case added to `eval_harness.py`'s `interactions` suite for this specific scenario — worth adding so this can't silently regress later.
- [x] **JWT auth given its own decision record (retroactive).** Work itself was already built and live-tested in an earlier session (bare-metal login 200 / unauthorized 401) but had never been written up as a D-numbered decision — closed as part of this session's doc-update pass. See `decisions.md` D37 for the full writeup (HS256, 7-day expiry, `get_current_user_id` dependency, `authFetch` frontend wrapper, `ms_token` in localStorage).
- [ ] **End-to-end Docker validation of previously-bare-metal-confirmed features — in progress, not complete.** Carried over from the Docker+CI work (D36): the container itself boots clean and CI is green, but re-exercising every feature specifically *through* the container (not just confirming it boots) is still underway.
  - **Open blocker:** the Groq model used by `buying_agent.py` (`meta-llama/llama-4-scout-17b-16e-instruct`) is returning 404 errors inside this validation pass, which is breaking the Apollo and 1mg medicine-price-comparison crews specifically. Not yet root-caused — worth checking whether this is a Groq-side model deprecation/rename (worth a quick Groq model-list check) versus something Docker-environment-specific (e.g. a stale/cached model string, missing env var inside the container). Flagging rather than guessing further without checking the actual error response.
  - **Secondary, non-urgent:** an Ollama RAG connection failure inside Docker — the embedder (`mxbai-embed-large` via Ollama) that the D26 RAG setup relies on isn't reachable from inside the container the way it is on bare-metal (likely `localhost` vs. the Docker network's host-reachable address, e.g. `host.docker.internal`, but not yet confirmed). Deliberately deprioritized behind the Groq 404 issue since it doesn't block the currently-tested feature set.
  - **Confirmed working through Docker this session:** Medicine Interaction Checker (`/medicine/interactions` → 200 OK, verified with the Duplicate Therapy fix above).
  - **Still to re-verify through the container specifically** (per the existing D36/progress.md follow-ups, still open): the full JWT signup/login/401 flow, and the rest of the feature set beyond what's listed above.

## Previous session — Medicine Effectiveness Phase 2 BUILT + LIVE-TESTED ✅ ("its working perfectly" — user confirmed)

- [x] **Medicine Effectiveness Phase 2 — fully built and confirmed working.** Adds pace-awareness on top of Phase 1's direction-only annotations — see `decisions.md` D29 for the full two-phase plan and D31 for this phase's own decision record.
  - **New reference file:** `medicine_response_timelines.txt` (`knowledge/medical_kb/`) — expected response windows per medicine/test pair, covering all ~30 medicines in `medicine_test_map.py`. Honest about uncertainty where a precise window isn't well established (e.g. Silymarin, Sodium bicarbonate) rather than inventing one.
  - **New crew:** `MedicineEffectivenessCrew` (`crew.py`) + `MedicineEffectivenessOutput` schema (`direction_correct`, `pace_verdict`, `plain_explanation`, `doctor_talk_recommended`, `disclaimer`) + `medicine_effectiveness_agent.yaml` / `medicine_effectiveness_task.yaml`. RAG-grounded against `test_direction_reference.txt` (direction — reused from phase 1) and the new `medicine_response_timelines.txt` (pace), same shared_kb_files pattern as `LabReportCrew`/`MedicineInteractionCrew`/`SymptomTriageCrew`.
  - **New backend endpoint:** `POST /medicine/effectiveness` — takes `{user_id, medicine_name, test_name, start_date, points, normal_range}` (points forwarded from what the frontend already has from `/health/trends-annotated/{user_id}`, no extra DB read) and returns a `MedicineEffectivenessOutput`. Deliberately on-demand, not pre-computed for every trend on every page load — avoids an LLM call per chart render.
  - **Frontend:** new `EffectivenessCard` component in `LabReport.jsx`, rendered per annotation below `TrendDeltaBadges` — deliberately a **separate card**, not merged into the delta badge (per explicit user direction this session), since the badge is a free client-side computation and this needs a real LLM call. Shown behind an explicit "Check `<medicine>`'s response pace" button per annotation. New CSS block in `LabReport-effectiveness-styles.css` (appended to `LabReport.css`).
  - **Live-tested by the user** against the same real `Metformin` data from the Phase 1 test session — **user directly confirmed "its working perfectly."**
  - **Known assumption flagged, not yet independently re-verified:** `MedicineEffectivenessCrew` assumes `test_direction_reference.txt` (Phase 1's own reference file) lives at `knowledge/medical_kb/test_direction_reference.txt`, matching where the other three shared reference files already live. This wasn't re-confirmed against Phase 1's actual file layout in this session — if Phase 1 put it somewhere else, the `shared_kb_files` path in `MedicineEffectivenessCrew.crew()` needs a one-line fix. Worth double-checking next session if anything about the pace verdicts looks off (e.g. RAG not finding direction context).
  - **Medicine Effectiveness feature (both phases) is now fully complete.**

## Previous session — Medicine Effectiveness Phase 1 BUILT + LIVE-TESTED ✅ + Delete Lab Report feature BUILT + LIVE-TESTED ✅

- [x] **Medicine Effectiveness Phase 1 — fully built, wired, and confirmed working end-to-end with real data.** This was the top-priority MVP-differentiator item carried over from the previous session (see `decisions.md` D29).
  - **Backend:** `test_direction_reference.txt` + a static medicine↔test mapping dict (`medicine_test_map.py`, ~22 medicines) added. New `get_annotated_trends(user_id)` in `health_records.py` (extends the existing `get_test_trends()`) cross-references a user's saved `health_prescriptions` against their saved lab trends — for each trend with 2+ points, if a mapped medicine has a saved prescription, attaches `{medicine_name, start_date}` to that trend's `annotations` array. New `GET /health/trends-annotated/{user_id}` endpoint in `main.py` exposes this (kept as a separate endpoint alongside the older `/health/trends/{user_id}`, not a breaking change to it).
  - **Frontend (`LabReport.jsx` + `LabReport.css`):** `TestTrendChart` now renders a dashed coral vertical marker line at the medicine's `start_date` (when the trend has a matching annotation), a small medicine-name label above the line, and an auto-computed "Since `<medicine>`: `<before>` → `<after>`" delta badge pill above the chart, computed from the nearest data points before/after the start date.
  - **Live-tested by the user with real data:** added a real `Metformin` prescription via `/docs` Swagger UI (`POST /health/prescription`, response `{"status": "saved", "record_id": "..."}`), which fell chronologically between two already-uploaded/saved lab reports (6 Jul and 5 Sept). Confirmed on-screen: dashed marker line + "Metformin" label + delta badge all rendered correctly on both `Fasting Blood Sugar` and `HbA1c` cards — **user directly confirmed "dikh rha h sb."**
  - **Not yet built:** Phase 2 (`medicine_response_timelines.txt` + `MedicineEffectivenessCrew` for pace-awareness) — see `decisions.md` D29 for the full phase 2 plan, still the next priority item.

- [x] **Delete Lab Report Analysis feature — built and live-tested.** Added a way to delete a saved lab report analysis, with a lightweight confirmation step (user explicitly chose **"type DELETE to confirm"** over a PIN, when asked).
  - **Backend:** `delete_lab_report_analysis(user_id, analysis_id)` added to `health_records.py`, scoped to `user_id` so cross-user deletes aren't possible. New `DELETE /lab/analyses/{user_id}/{analysis_id}` endpoint in `main.py`.
  - **Frontend:** `LabReport.jsx` — trash icon next to each saved report's chevron in `PastReportItem`; clicking it opens an inline panel requiring the user to type `DELETE` exactly (Delete button stays disabled until the text matches). On confirm, the report disappears from the list immediately (locally-first), then both the saved-reports list and the annotated-trends data are re-fetched in the background — because removing a report can drop a test below the 2-point minimum needed for a chart, or shift which annotation/badge is shown.
  - **Deliberately not built:** no undo/soft-delete — it's a real `delete_one()`, permanent once confirmed. Flagged as an easy follow-up (soft-delete flag + timed purge) if wanted later, not built proactively.
  - **Debugging note from this session (worth keeping in mind if this ever regresses):** user initially hit a 404 "Not Found" after confirming a delete. Root cause wasn't diagnosed in detail in this doc (resolved before a Network-tab trace was needed — likely a stale/not-yet-restarted backend after the new route was added, based on the pattern), but flagged here in case it recurs: **always confirm the backend was restarted after adding a new route**, and check `/docs` shows the new endpoint listed, before assuming a logic bug in the delete function itself.

## Previous session — Lab Report PDF extraction bug fixed (✅ live-tested) + Health Trends report_date chronology fixed (built, not yet live-tested) + Medicine Effectiveness feature planned (not yet built)

- [x] **PDF lab report extraction bug — FIXED and live-tested by the user.** `/lab/analyse` previously called `extract_text_from_image()` (PIL-based) for every upload; for PDFs this always raised (PIL can't open a PDF), and the `except` block silently fell back to reading the raw file bytes as text — sending garbled `%PDF-1.4 ... stream ... endobj` binary straight to `LabReportCrew`, which correctly (but unhelpfully) reported "this doesn't look like a lab report."
  - New `extract_text_from_lab_document()` in `main.py`: non-PDF files still go through the unchanged `extract_text_from_image()` OCR path; PDFs get real text extraction via `pdfplumber` first, falling back to `pdf2image` + Tesseract OCR (page-by-page) only if no embedded text is found (i.e. a scanned/photo-as-PDF). Raises a clean `ValueError` instead of ever falling back to raw bytes.
  - `/lab/analyse` handler now calls this new function and turns any failure into a proper `400`, instead of silently degrading.
  - New deps: `pdf2image` (installed this session; `pdfplumber` was already present as a `pdfplumber` dependency). **Poppler binaries still need to be on PATH on Windows for the scanned/photo-PDF OCR fallback path** — not yet confirmed installed by the user; the text-based-PDF path (pdfplumber) does not need it and is the one that's been tested.
  - **Live-tested twice** with synthetic reportlab-generated sample PDFs — both times the analysis correctly extracted real values (Hemoglobin, Fasting Blood Sugar, HbA1c, TSH) with specific numbers and reference ranges, not generic text.
  - See `decisions.md` D27.

- [x] **Health Trends chart date bug — FIXED, not yet live-tested with the fix in place.** Discovered via a user screenshot: two saved lab reports (uploaded back-to-back for testing) both showed "7 Jul 2026" on the Health Trends chart and in the saved-reports list, even though the second synthetic report's own printed date was "05-Sep-2026". Root cause: `save_lab_report_analysis()` always used `datetime.utcnow()` (save/upload time) for the record's `date` field, which `get_test_trends()` sorts and charts by — so upload time, not the report's actual date, drove the X-axis.
  - Full chain updated: `lab_report_task.yaml` (agent instructed to find any date on the document — report/collection/printed date, prefer collection date — and normalise to ISO `YYYY-MM-DD`, or `null` if none found) → `crew.py` (`LabReportAnalysisOutput.report_date: Optional[str]`, new field) → `main.py` (`SaveLabReportAnalysisRequest.report_date`, passed through in `/lab/save`) → `health_records.py` (new `_resolve_report_date()` helper — uses the report's own date if it parses as `YYYY-MM-DD`, silently falls back to save-time otherwise, matching the old behavior as a safe default) → `LabReport.jsx` (`handleSave`'s payload now forwards `analysis.report_date`).
  - **Not yet re-tested end-to-end by the user with all 5 files replaced** — needs the second sample report (05-Sep-2026) re-uploaded/re-analysed/re-saved to confirm the saved-reports list and trend chart now show two different dates instead of one.
  - See `decisions.md` D28.

- [ ] **Medicine Effectiveness feature — discussed and scoped this session, NOT YET BUILT.** User wants prescription analysis + Health Trends to be the project's core MVP/differentiator (explicit goal: "koi ye na kehde ki ye to AI bhi karleta hai" — needs to be something a generic ChatGPT-style single-turn tool structurally cannot do, which cross-referencing a user's own saved prescriptions against their own saved lab trends achieves). Full plan captured in `decisions.md` D29 and `PROJECT_CONTEXT.md` §10. Two-phase build, phase 1 not started:
  - **Phase 1 (next):** `test_direction_reference.txt` (which direction is "improving" per test — e.g. lower FBS is better, higher Hemoglobin is better up to normal range) + a medicine↔test mapping (which medicines should move which tests) + a medicine-start-date annotation marker on the existing `TestTrendChart` SVG in `LabReport.jsx`, plus an auto-computed "↓/↑ X since <medicine> started" badge.
  - **Phase 2 (after phase 1 works):** `medicine_response_timelines.txt` (expected pace of response per medicine, e.g. Metformin's effect on FBS shows in 1-2 weeks but HbA1c takes 8-12 weeks since it's a 3-month average) + new `MedicineEffectivenessCrew`/`MedicineEffectivenessOutput` schema that reasons about direction + pace together and produces a plain-language verdict + doctor-talk recommendation with a "why" a non-medical user can trust.
  - **Doctor QR / clinical-summary-on-scan idea (discussed, explicitly deprioritized this session in favor of the above being the MVP focus)** — architecture sketch preserved in `decisions.md` D29 for later: a separate, time-limited "Doctor Visit QR" token type (distinct from the existing permanent Emergency QR, for data-exposure-scope reasons) that would show a doctor-facing clinical summary. Not started.



## Previous session — RAG: shared knowledge base wired into 3 crews (roadmap order changed — RAG now before Docker+tests)

User changed the roadmap order: **guardrails ✅ → eval harness ✅ → RAG (this session) → Docker+CI+tests** (deployment still last).

**What shipped:**
- **Correction to earlier framing:** the existing `TextFileKnowledgeSource` + Ollama `mxbai-embed-large` embedder setup was already real embedding-based semantic search (Chroma under the hood), not "keyword-ish lookup" as an earlier session summary said. The real gap was that there was nothing substantial to retrieve beyond a thin per-user `profile.txt`.
- New shared, non-user-specific knowledge base, 3 files: `knowledge/medical_kb/drug_interactions.txt`, `lab_reference_ranges.txt`, `symptom_red_flags.txt` — hand-curated general reference content (not from a licensed medical DB, honestly scoped the same way as D24's guardrail keyword list).
- `crew.py`'s `_build_crew_base()` now returns a *list* of knowledge sources and takes an optional `shared_kb_files` param. Wired into exactly 3 crews (the same 3 targeted by the eval harness): `LabReportCrew` → `lab_reference_ranges.txt`, `MedicineInteractionCrew` → `drug_interactions.txt`, `SymptomTriageCrew` → `symptom_red_flags.txt`.
- `SymptomTriageCrew`'s reference file deliberately doesn't restate the hardcoded guardrail's emergency keyword list — it's written for the wider, greyer range of cases the guardrail doesn't try to catch.
- Full reasoning, scope, and the framing correction in `decisions.md` D26.
- Not yet tested by the user (needs Ollama running locally, same prerequisite as before this session — nothing new required beyond it).

## Previous session — Agent eval harness built (roadmap item 2 of 4)

**What shipped:**
- New `eval_harness.py` — standalone script, three suites:
  - `guardrails` — regression-tests `check_emergency()` against 8 red-flag phrases (expect trigger) + 4 benign phrases (expect no trigger). Zero LLM cost, safe to run anytime.
  - `triage` — runs `SymptomTriageCrew` against 3 labeled symptom descriptions, checks `urgency_level` matches an expected bucket.
  - `interactions` — runs `MedicineInteractionCrew` against 4 known medicine pairs (2 dangerous, 2 safe), checks `has_interaction` matches expectation.
- Every run prints a pass/fail table + accuracy % + avg/min/max latency per suite, and writes a timestamped JSON report (`eval_report_<timestamp>.json`) so results can be diffed across sessions.
- `LabReportCrew` deliberately excluded — takes image/PDF input, doesn't fit the text-in/JSON-out shape this harness scores. See `decisions.md` D25.
- **✅ Fully verified this session against the actual `crew.py`, `symptom_triage_task.yaml`, and `medicine_interaction_task.yaml`** — the `kickoff(inputs={...})` keys (`symptoms`, `medicines_list`), the `urgency_level` enum, and the `has_major_interaction` field name are all confirmed, no placeholders remain in the script.
- Not yet run by the user.

## Previous session — Safety guardrails layer built (roadmap item 1 of 4)

User picked an order for the "make it resume-grade" roadmap: **guardrails → eval harness → Docker+tests → RAG** (deployment deliberately last). This session built item 1.

**What shipped:**
- New `safety_guardrails.py` — `check_emergency(text)` regex-matches red-flag phrases (chest pain, can't breathe, stroke signs, heavy bleeding, suicidal ideation, obstetric emergencies — English + common Hinglish/Hindi) and returns an emergency response shaped exactly like `SymptomTriageOutput`.
- Wired into **three** endpoints, checked before the LLM crew is ever called: `/triage/symptoms`, `/consultation/speech`, `/consultation/document`. If it matches, the endpoint returns instantly — no LLM round-trip, no cost, no risk of a model under-triaging an unambiguous emergency.
- Zero frontend changes needed — the guardrail's output shape matches what `TriageResultCard` and `PrescriptionAnalysisCard` already render.
- Full reasoning + scope/limitations honestly documented in `decisions.md` D24 (this is a keyword-based first-pass net, not a diagnostic tool — a real deployment would need clinical review of the keyword list).
- Not yet live-tested by the user.

**Previous session — Health Trends / Report History feature built:**



The feature scoped in `decisions.md` D23 last session is now built end-to-end, backend + frontend, on the existing Lab Report page (no new route added, per user's request to stop adding pages).

**What shipped:**
- **Backend:** `LabTestResult` (`crew.py`) now has a `numeric_value: Optional[float]` field; `lab_report_task.yaml` instructs the agent to fill it (null for qualitative results like "Positive"/"Trace"). New `get_test_trends(user_id)` in `health_records.py` groups all of a user's saved `lab_report_analyses` tests by `test_name` into chronological series, only keeping tests seen in 2+ reports, sorted so currently-abnormal tests surface first. New `GET /health/trends/{user_id}` endpoint in `main.py` exposes this.
- **Frontend (`LabReport.jsx` + `LabReport.css`, same file — no new page):** a new "Your Health History & Trends" section, always visible to logged-in users regardless of what's currently uploaded. It has two parts: (1) a real saved-reports list — this also fixes the long-standing "history disappears on reload" bug, since it finally calls the already-existing `GET /lab/analyses/{user_id}`; (2) per-test trend cards with a small hand-rolled inline SVG line chart (color-coded dots by status, no new chart library dependency) plus a plain-language line like "10.2 g/dL → 11.8 g/dL → 13.1 g/dL — it's now back within the normal range." Tests without a clean numeric value fall back to a status-chip timeline instead of a line. Saving a new report now bumps a refresh key so the section refetches without a reload.
- Two small, deliberate deviations from the original D23 plan — see `decisions.md` D23 "Built (this session)" note: skipped `range_low`/`range_high` (shaded band) for now, and used a custom SVG chart instead of adding `recharts` as a dependency.

**Previous session — Cleanup sprint complete + repo public:**

**Completed:**
- **Repo pushed public:** [github.com/GAUTAM-JAIN1/MediSarthi](https://github.com/GAUTAM-JAIN1/MediSarthi) — clean history, no secrets committed, polished README.
- **`face_recognize.py` deleted.** Confirmed via grep across `main.py`, `crew.py`, `auth.py`, `Calling.py`, `Calling_Ai.py` that nothing actually imports it (`auth.py`/`Calling_Ai.py` only had comment-references explaining what replaced it). Also removed its now-unused dependency chain from `pyproject.toml`: `face-recognition`, `face-recognition-models`, `dlib` (implied), `opencv-python` (confirmed zero `cv2` usage anywhere in the backend), and `cmake` (was only needed to build `dlib`).
- **Signup form fields added.** `Auth.jsx` was sending `age: 0, gender: "", city: "", state: ""` placeholders even though the backend (`SignupRequest`, `auth.py`) already required real values. Added Age (number input), Gender (dropdown), City, State (2-column rows) and an optional Allergies field, plus signup-mode validation. New `.ms-auth-row` / `.ms-auth-select` CSS added to `Auth.css`, matching the existing design system exactly.
- **3 new CrewAI agents (Lab Report Analyser, Medicine Interaction Checker, Symptom Triage) — user confirmed all fully live-tested and working**, closing out the last ⚠️ caveat that had been carried in `PROJECT_CONTEXT.md`'s endpoint table since the AGENTS audit session.
- **Google Calendar OAuth fixed** — new dedicated Google Cloud project created to avoid the organization-linkage issue that was blocking it.
- **FindMedicine.jsx UI redesign done** — orbital symptom-bubble map, three-column layout.
- **Security/secrets cleanup confirmed done** by the user ahead of the public push.

**Now built this session** — see "🆕 Latest session" section above. (Was: "Planned next: Health Trends / Report History feature" — kept here for history of how it was scoped.)

**Also discussed, longer-term roadmap (not committed to a build order yet):** deployment, RAG with a real vector store (replacing the plain-text knowledge-file lookup), an agent evaluation harness, a safety-guardrail layer, streaming consultation responses, Docker + CI, automated tests, a WhatsApp bot entry point. See `README.md`'s "Roadmap" section.

**Resolved this session (was previously deferred):** the exact Groq LLM config scope across all 7 crews in `crew.py` — confirmed project-wide via `crew.py`'s own migration comment when the file was shared this session (see `CLAUDE.md` Known Fixed Bugs Bug 3, now closed).

---

## Previous session — Compare.jsx confirmed wired + live-tested (price comparison feature is DONE)

`Compare.jsx` is no longer mock data — it's wired to a real `/medicine/compare` endpoint backed by a substantially rewritten `buying_agent.py`, and **the user has live-tested it and confirmed it's working.** This closes out the single remaining item from the original 10-feature scope (see `decisions.md` D5, D21, D22). Key points:

- `buying_agent.py` now runs two parallel browser-use agents (one for 1mg, one for Apollo Pharmacy), each extraction-only — neither ever clicks "Add to cart" or any purchase-path button, under any circumstances. This is D2 enforced at the code level, not just a frontend confirm dialog.
- `Compare.jsx`'s "Buy" action is a plain outbound link to the pharmacy's product page (Google search fallback if no direct URL was captured) — no cart, no confirm step needed, because the app never touches a cart at all. This **supersedes** the `idle → confirming → added` state machine originally described in `decisions.md` D2 — see the update note added to D2 and the new D21.
- Real bug fixed along the way: a nested Pydantic schema crashed browser-use's internal `extract` tool with a `$defs` schema error when `use_vision=False`; fixed by flattening the per-site agent's output schema to `List[Dict[str, Any]]`, with defensive rebuilding into proper `PharmacySiteResult` objects afterward. See `decisions.md` D22.
- Uses `browser_use`'s `ChatGroq` (`meta-llama/llama-4-scout-17b-16e-instruct`) to drive the browser agent — this needs `GROQ_API_KEY` in `.env`; since the live test passed, this key is confirmed present and working.
- `Compare.jsx` has a real progress UI for the genuinely-long (1-3 min) wait — rotating status messages + elapsed-time counter, instead of one static "please wait" line.

**Files involved:** `backend/src/agents/buying_agent.py`, `backend/src/agents/main.py` (`/medicine/compare` endpoint, unchanged), `frontend/frontend/src/Pages/Compare.jsx`, `frontend/frontend/src/Pages/Compare.css`.

---

## 🆕 Previous session — LLM provider migration (Gemini → Groq, for CrewAI agents) + hospital parser format-lock + free phone numbers

**What happened, in order:**
1. Gemini's free-tier per-minute quota (previously just a "wait 30-60s and retry" annoyance, see the older note below) became disruptive enough during repeated testing that the LLM provider was switched to **Groq** (Llama-based models, also free-tier) for CrewAI agents.
   ⚠️ **Not fully verified in this doc yet** — the exact `crew.py` LLM config (model string, whether `GROQ_API_KEY` was added to `.env`, and whether this is project-wide across all 7 crews or only the hospital-finder path) wasn't preserved in the handoff into this session. Treat as functionally confirmed (hospitals now load correctly, live-tested) but **open `crew.py` + `.env` to confirm the exact config before treating it as settled** — same caveat style as the 3 AGENTS-audit endpoints below.
2. Switching providers caused a **real parsing bug**: Groq's Llama output styled hospital list items differently (backticks) than Gemini's (bold markdown), and `main.py`'s `parse_hospital_list()` only handled the old style → hospital list rendered blank on the frontend even though the backend was returning data. This was first misdiagnosed as "backend not restarted with new code" (also true, compounding the symptom) before the real format-mismatch was found.
3. **Root-cause fix applied** (not just a patch): instead of leaving the LLM free to choose its own markdown style, `hospital_task.yaml`'s `reporting_task` now **strictly locks the output format**: `* **Hospital Name**: Address | Phone: phone-number-or-Not-available`, one hospital per line, bold-only, no backticks/italics, no extra commentary. `parse_hospital_list()` was rewritten to parse this exact format reliably while staying backward-compatible with the old Groq-backtick and Gemini-bold styles it had already seen.
4. **Phone numbers added — for free.** `custom_tool.py`'s `MyCustomTool` (Nominatim OpenStreetMap search) now sends `extratags=1` in its request params. This makes Nominatim return each result's raw OSM tags (`phone`, `contact:phone`, `contact:mobile`) when the listing has one, **at no extra cost and no extra API call** — no need for a paid API like Google Places. Coverage is partial (OSM is crowdsourced; many smaller/private hospitals have no phone tag at all) — those show `Phone: Not available` and the frontend falls back to its old manual-entry behavior.
5. **`Appointments.jsx` updated:** `prefillFromHospital(h)` now fills the call-form number field with `h.phone` when present (and `.select()`s it to visually highlight that it was auto-filled), and falls back to just focusing the empty field (old behavior) when no phone is available.

**Files changed this session (4):** `backend/src/agents/main.py`, `backend/src/agents/tools/custom_tool.py`, `backend/src/agents/config/hospital_agent.yaml`, `backend/src/agents/config/hospital_task.yaml`, plus `frontend/frontend/src/Pages/Appointments.jsx`.

**Status:** Hospital list loading + Book Call number-highlight behavior confirmed working live by the user. Auto-fill-on-real-phone-number behavior was just implemented — **not yet confirmed live by the user as of this doc update**, re-test and confirm after replacing `Appointments.jsx`.

See `decisions.md` D17–D20 for the reasoning, and `CLAUDE.md`'s "Known Fixed Bugs" for the bug-fix writeups (Bugs 3 & 4).

---

Last updated: **Live-testing + bug-fix session** — the 3 new CrewAI agents (Lab Report Analyser, Medicine Interaction Checker, Symptom Triage) from the AGENTS audit session were live-tested end-to-end via `/docs` (Swagger UI) and are now **CONFIRMED WORKING**. Two real bugs were found and fixed in the process — both were environment/setup issues, not logic bugs, and both affected ALL 7 CrewAI crews (not just the 3 new ones). See "Bug fixes this session" below before re-debugging anything that looks similar.

## ✅ Completed

### Environment & tooling
- [x] Python 3.11.9 installed side-by-side with system Python 3.14.
- [x] CMake, Visual Studio Build Tools installed.
- [x] `dlib` installed via prebuilt wheel.
- [x] Full backend dependency tree installed via `pip install -e .`.
- [x] `fastapi` and `uvicorn` installed separately in venv.
- [x] Backend confirmed running on port 8080.
- [x] `react-router-dom` installed in the frontend.
- [x] `qrcode.react` installed in the frontend (used for Emergency QR rendering).
- [x] MongoDB Atlas: user's own fresh cluster created (independent of the
      friend/original-repo's cluster). `db_connect.py` updated with new `MONGO_URI`.
      Network Access set to Allow Anywhere (0.0.0.0/0) — fine for dev, must be
      tightened before any real deployment.
- [x] **NEW — `backend/.env` created this session.** Contains `GEMINI_API_KEY` +
      `GOOGLE_API_KEY` from a fresh Google AI Studio key. No `.env` file existed
      anywhere in the project before this session (confirmed via recursive
      filesystem search) — see "Bug fixes this session" below.

### 🔧 Bug fixes this session (CRITICAL — read before debugging anything similar)

Two environment bugs were found while live-testing the 3 new agents. **Both affected
all 7 CrewAI crews equally** (the original 4 + the 3 new ones) — meaning the
"confirmed working end-to-end" status on `SpeechCrew`/`FileCrew`/`Nearbyhospitals`/
`general_que` earlier in this doc predates these bugs and was not re-verified
against them. They are very likely fine since those flows go through the exact same
`_build_crew_base()` and `.env` loading path that's now fixed, but worth knowing this
gap exists.

1. **`FileNotFoundError: knowledge\user_<id>\profile.txt`** — every CrewAI endpoint
   failed with this. Root cause: CrewAI's `TextFileKnowledgeSource` (CrewAI 0.203.2,
   verified against installed package source) resolves its file path as
   `"knowledge/" + relative_path`, resolved against the process's **current working
   directory** — there is no constructor override for this. `auth.py`'s
   `get_user_knowledge_profile()` always writes the real file to the **absolute**
   path `backend/knowledge/user_<id>/profile.txt`. As long as the backend was
   started the old documented way (`cd src` then `python -m uvicorn agents.main:app`),
   the working directory was `backend/src/`, so CrewAI looked in
   `backend/src/knowledge/...` — which never existed.
   **Fix: changed the backend start command** (see below + `CLAUDE.md`) to run
   from `backend/` using `--app-dir src` instead of `cd src` first. No code changes
   were needed in `crew.py` or `auth.py` — this was purely a working-directory
   mismatch.

2. **`litellm.AuthenticationError: API key not valid`** — after fixing bug #1,
   every CrewAI endpoint then failed with this. Root cause: no `.env` file existed
   anywhere in the project, and no system environment variable was set either —
   `GEMINI_API_KEY` was silently `None` the whole time.
   **Fix: created `backend/.env`** (in `backend/`, not `backend/src/`, since the
   corrected start command makes `backend/` the working directory `load_dotenv()`
   resolves against) with a fresh key from https://aistudio.google.com/app/apikey.

3. **Note, not a bug (superseded — see top of this doc):** Gemini's free tier (`gemini-2.5-flash`) has a per-minute
   token quota. Running 2-3 test calls back-to-back can trigger
   `litellm.RateLimitError: RESOURCE_EXHAUSTED`. This was originally "expected
   free-tier behavior, wait and retry," but in a later session this same quota
   wall became disruptive enough that the LLM provider was switched to Groq —
   see the "🆕 Latest session" section at the top of this file.

### IMPORTANT — How to start the backend server (CORRECTED this session)
```powershell
cd C:\Users\gauta\OneDrive\Desktop\MediSarthi\medisarthi\backend
.\venv\Scripts\Activate
python -m uvicorn agents.main:app --host 0.0.0.0 --port 8080 --reload --app-dir src
```
**Do NOT `cd src` first** — this is the old, now-confirmed-broken way (see bug #1
above). Stay in `backend/`, use `--app-dir src`. `.env` must also live in `backend/`,
not `backend/src/`.

### Product decisions
- [x] Face recognition → removed, replaced with email+password.
- [x] Auto-add-to-cart → removed, replaced with explicit user confirmation.
- [x] AI voice-calling agent → kept, future polish pending.
- [x] Live price-comparison agent → kept as-is.

### Frontend (ALL PAGES DONE + WIRED)
- [x] Full luxury design system (ivory/ceramic, Playfair+Inter, brown/gold).
- [x] Rotating SVG donut-ring hero component.
- [x] **10 routes in App.jsx**: `/`, `/find-medicine`, `/compare`, `/appointments`,
      `/health-info`, `/auth`, `/donor`, `/emergency/:token`, `/lab-report`,
      `/medicine-check`.
- [x] **Layout.jsx + Layout.css** — Nav shows logged-in user name + Logout button.
      "Donor", "Lab Report", "Safety Check" links added to NAV_LINKS.
- [x] **Auth.jsx + Auth.css** — Login/Signup. Sends JSON body, has a safe
      `extractErrorMessage()` helper that converts backend error shapes (string,
      array of {msg}, object) into a plain string before rendering — this pattern
      was later reused in `HealthInfo.jsx`, `EmergencyView.jsx`, `FindMedicine.jsx`,
      `LabReport.jsx`, `MedicineCheck.jsx`.
      - **RESOLVED:** signup form now collects Age, Gender, City, State, and
        optional Allergies alongside Name/Email/Password, matching what
        `SignupRequest`/`auth.py` already expected. See "🆕 Latest session" at
        top of this doc.
- [x] **useUser.js hook** — reads localStorage, provides userId, userName, isLoggedIn, logout().
- [x] **Appointments.jsx** — WIRED: /hospitals/nearby + /call/schedule. Hospital
      list now also shows real phone numbers where OSM has one (see "🆕 Latest
      session" at top of this doc). `prefillFromHospital()` auto-fills the call
      form's number field when a hospital has a phone, and highlights it
      (`.select()`); falls back to focus-only on an empty field when no phone
      is available. **Auto-fill behavior pending live confirmation from user.**
- [x] **HealthInfo.jsx** — FULLY WIRED, CONFIRMED WORKING END-TO-END:
  - GET `/health/timeline/{user_id}`, POST `/health/vital` — vitals save AND
    display both work correctly.
  - **Emergency Medical ID card**: form (name, blood group, allergies,
    critical conditions, current medicines, emergency contact name+phone) +
    "Save Emergency Profile" button + "Generate QR" button + rendered QR
    (`qrcode.react`'s `<QRCodeSVG>`) encoding `/emergency/{token}`.
  - **CONFIRMED WORKING END-TO-END**: saved emergency profile, generated QR,
    scanned/opened QR URL in incognito, saw correct info without login, QR
    persists correctly across page reloads.
- [x] **FindMedicine.jsx** — WIRED TO REAL BACKEND (text/voice/document consultation).
- [x] **EmergencyView.jsx** — public page (no login, rendered outside `<Layout>`,
      no nav bar), route `/emergency/:token`, fetches `/health/qr/{token}`, shows
      name/blood group/critical conditions/allergies/medicines/emergency contact
      (with `tel:` link), safe error handling. **CONFIRMED WORKING.**
- [x] **Donor.jsx + Donor.css** — blood donor page, fully wired & tested (register,
      profile card, availability toggle, record donation, find matching donors,
      emergency blood request). **CONFIRMED WORKING END-TO-END.**
- [x] Hero_Page — UI done. Compare — UI done, **wired to real backend, confirmed working** (see "🆕 Latest session" at top of this doc — moved out of mock-data status).
- [x] **`LabReport.jsx` + `LabReport.css`** — lab report (blood test photo/PDF)
      upload page, calls `/lab/analyse`, shows plain-language explanation per test
      value with expandable cards, urgent-value banner, save-to-records action.
      Route `/lab-report`. **Backend endpoint live-tested this session and
      confirmed wired correctly — request/response shape matches what the crew
      and frontend both expect.** (One live end-to-end run hit a transient free-tier
      rate limit, not a bug — see "Bug fixes this session" note #3. Re-run after a
      short wait to get a full real response if you want final visual confirmation
      in the browser.)
- [x] **`MedicineCheck.jsx` + `MedicineCheck.css`** — single page combining two
      tools: Medicine Interaction Checker (top) + Symptom Triage (bottom).
      Route `/medicine-check`.
      **CONFIRMED WORKING END-TO-END this session** — live-tested via `/docs`:
        - Symptom Triage: real test (fever, headache, no cough) returned a
          correctly-shaped `Home Care` assessment with India-relevant home care
          tips (ORS, nimbu paani), accurate warning signs, and proper disclaimer.
        - Medicine Interaction Checker: real test caught that "Paracetamol" and
          "Dolo 650mg" share the same active ingredient (acetaminophen) and
          correctly flagged it `Contraindicated` with a clear, actionable
          recommendation — genuinely correct safety catch, not just a
          well-shaped response.
- [x] **`App.jsx`** — 2 routes added (`/lab-report`, `/medicine-check`) → **10 routes
      total**.
- [x] **`Layout.jsx`** — 2 new nav links added for the above routes.

### Backend — auth (COMPLETE, verified working end-to-end)
- [x] `auth.py` — signup/login with bcrypt, MongoDB Members collection.
- [x] `/auth/signup` + `/auth/login` endpoints in `main.py`.

### Backend — Blood donor system (COMPLETE, verified working end-to-end)
- [x] 6 endpoints: `/donor/register`, `/donor/{user_id}`, `/donor/{user_id}/record-donation`,
      `/donor/{user_id}/availability`, `/donor/request/create`, `/donor/request/find-donors`.

### Backend — Health records (COMPLETE, re-verified + fixed in an earlier session)
- [x] `health_records.py` — all functions `main.py` needs:
      `add_vital`, `get_vitals`, `add_prescription`, `get_prescriptions`,
      `get_full_timeline`, `save_emergency_profile`, `get_emergency_profile`,
      `get_emergency_profile_public`, `generate_qr_token`,
      `save_prescription_analysis`, `get_prescription_analyses`,
      `get_prescription_analysis_by_id`, `save_lab_report_analysis`,
      `get_lab_report_analyses`, `get_lab_report_analysis_by_id`.
  - Mongo collections used: `health_vitals`, `health_prescriptions`,
    `emergency_profiles`, `emergency_qr_tokens`, `prescription_analyses`,
    `lab_report_analyses`.
  - QR-based emergency access is fully implemented backend AND frontend, and
    confirmed working live.
- [x] Endpoints: GET `/health/timeline/{user_id}`, POST `/health/vital`,
      POST `/health/emergency-profile`, GET `/health/emergency-profile/{user_id}`,
      POST `/health/generate-qr/{user_id}`, GET `/health/qr/{token}`, and more.

### Backend — AGENTS audit: 3 new agents/crews — ✅ NOW CONFIRMED WORKING END-TO-END
- [x] Directory audit done first (per user's request) before building anything new.
- [x] **Existing inventory confirmed:** 4 crews (`SpeechCrew`, `FileCrew`, `Nearbyhospitals`, `general_que`), 7 existing agents (`doctor`, `Medical_Data_Extractor`, `care_coordinator`, `prescription_analyst`, `hospital_finder`, `hospital_reporter`, `home_health_assistant`).
- [x] **3 new crews added to `crew.py`** (see `decisions.md` D15 for selection reasoning):
  1. **`LabReportCrew`** (agent: `lab_report_analyst`) — lab report (blood test) photo/PDF → plain-language explanation of each value (normal/abnormal, what to ask a doctor). **Endpoint verified live this session: `POST /lab/analyse`.**
  2. **`MedicineInteractionCrew`** (agent: `interaction_checker`) — multiple medicines in → checks for dangerous interactions. **CONFIRMED WORKING — endpoint `POST /medicine/interactions`.**
  3. **`SymptomTriageCrew`** (agent: `triage_nurse`) — symptoms in → urgency level (home rest / see a doctor / emergency). **CONFIRMED WORKING — endpoint `POST /triage/symptoms`.**
- [x] **6 YAML config files** in `backend/src/agents/config/`: `lab_report_agent.yaml`, `lab_report_task.yaml`, `medicine_interaction_agent.yaml`, `medicine_interaction_task.yaml`, `symptom_triage_agent.yaml`, `symptom_triage_task.yaml`.
- [x] **3 endpoints in `main.py` — paths corrected/verified this session against the actual code** (an earlier doc version had guessed-wrong paths):
      `POST /lab/analyse` (analyze, doesn't save) + `POST /lab/save` (explicit save) +
      `GET /lab/analyses/{user_id}` (list), `POST /medicine/interactions`,
      `POST /triage/symptoms`. These are the real, confirmed paths — use these,
      not any earlier guess.
- [x] **`health_records.py`** — 6 functions added across two features: `save_lab_report_analysis`/`get_lab_report_analyses`/`get_lab_report_analysis_by_id`, and `save_prescription_analysis`/`get_prescription_analyses`/`get_prescription_analysis_by_id`.
- [x] Deferred (not built, explicitly Tier 2): `DietAdvisor`, `MentalWellnessAgent` — candidates proposed but not picked; can be built later if wanted.

### Backend/Frontend — Prescription Analysis save feature
- [x] **`FindMedicine.jsx`** has a `PrescriptionAnalysisCard` component — shows the `prescription_analyst` agent's plain-language breakdown + allergy-conflict banner after a voice/document consultation, with an explicit "Save to my records" button.
- [x] Nothing auto-saves when a consultation runs — saving is a separate, permission-gated action (same philosophy as the confirm-before-cart rule, D2; formalized as D17 in `decisions.md`).
- [x] Backend: `/health/prescription-analysis` (save), `/health/prescription-analyses/{user_id}` (list), `/health/prescription-analysis/{user_id}/{analysis_id}` (detail) — code present; not separately re-tested this session (this session's focus was the 3 new agents specifically).

### Backend/Frontend — Price comparison (COMPLETE, confirmed working end-to-end this session)
- [x] `buying_agent.py` — rewritten extraction-only, two parallel browser-use agents (1mg + Apollo), no purchase/add-to-cart capability at all. See `decisions.md` D21, D22.
- [x] `/medicine/compare` endpoint in `main.py` — unchanged, already wrapped `run_comparison()` correctly.
- [x] `Compare.jsx` — wired to the real endpoint, mock data removed, plain outbound "Buy" links (no cart interaction), live progress UI for the 1-3 minute real-browser wait. **Live-tested and confirmed working by the user.**

### Backend/Frontend — Health Trends / Report History feature (built this session, not yet user-tested)
- [x] `crew.py` — `LabTestResult.numeric_value: Optional[float]` added.
- [x] `lab_report_task.yaml` — agent instructed to fill `numeric_value`, null for qualitative results.
- [x] `health_records.py` — `get_test_trends(user_id)` groups saved tests by name into chronological series, 2+ occurrences only.
- [x] `main.py` — `GET /health/trends/{user_id}` endpoint.
- [x] `LabReport.jsx`/`LabReport.css` — new "Your Health History & Trends" section on the same page: saved-reports list (fixes reload bug) + per-test trend cards with inline SVG charts and plain-language insight lines. See `decisions.md` D23.
- [ ] Not yet live-tested by the user — needs 2+ saved reports with an overlapping test name to see a real chart.

### Backend — Safety guardrails layer (built this session, not yet user-tested)
- [x] `safety_guardrails.py` — `check_emergency(text)`, keyword-based, runs before any LLM call.
- [x] Wired into `/triage/symptoms`, `/consultation/speech`, `/consultation/document`.
- [x] Output shape matches `SymptomTriageOutput` / existing prescription-analysis shape — no frontend changes needed.
- [ ] Not yet live-tested by the user — needs a real request with a red-flag phrase (e.g. "I have chest pain") to confirm it short-circuits before hitting the LLM.

### Backend — Agent eval harness (built this session, fully verified, not yet run)
- [x] `eval_harness.py` — `guardrails` suite (12 cases, zero LLM cost), `triage` suite (3 cases), `interactions` suite (4 cases).
- [x] Pass/fail table + accuracy % + latency stats printed per run; timestamped JSON report written each run.
- [x] Verified against real `crew.py`/task YAMLs — `kickoff` input keys, `urgency_level` enum, `has_major_interaction` field name all confirmed.
- [ ] Not yet run by the user.

### Backend — RAG: shared knowledge base (built this session, not yet tested)
- [x] `crew.py` — `_build_crew_base()` now returns a list of knowledge sources, new optional `shared_kb_files` param.
- [x] 3 new files: `knowledge/medical_kb/{drug_interactions,lab_reference_ranges,symptom_red_flags}.txt`.
- [x] Wired into `LabReportCrew`, `MedicineInteractionCrew`, `SymptomTriageCrew` — each gets its matching reference file alongside the per-user profile source.
- [x] Framing correction documented in `decisions.md` D26 (existing setup was already real embedding search, not keyword lookup — the gap was content, not mechanism).
- [ ] Not yet tested by the user.

### Backend — Lab Report PDF extraction bug fix (this session, ✅ live-tested twice by the user)
- [x] New `extract_text_from_lab_document()` in `main.py` — images unchanged (existing `extract_text_from_image()`), PDFs get `pdfplumber` direct text extraction with a `pdf2image`+Tesseract OCR fallback for scanned/photo PDFs. Raw-PDF-bytes-as-text fallback removed entirely.
- [x] `/lab/analyse` now returns a clean `400` on genuine extraction failure instead of silently degrading.
- [x] New dependency `pdf2image` installed. `pdfplumber` already present.
- [x] Confirmed live-tested with 2 synthetic sample PDFs — correct specific values extracted both times.
- [ ] Poppler-on-PATH (Windows) for the scanned-PDF OCR fallback specifically — not yet confirmed installed; not required for the tested text-PDF path.
- See `decisions.md` D27.

### Backend/Frontend — Health Trends report_date chronology fix (this session, built, not yet live-tested)
- [x] `lab_report_task.yaml` — agent instructed to extract any date on the document, normalise to ISO `YYYY-MM-DD`, `null` if none found.
- [x] `crew.py` — `LabReportAnalysisOutput.report_date: Optional[str]` added.
- [x] `main.py` — `SaveLabReportAnalysisRequest.report_date`, forwarded to `save_lab_report_analysis()` in `/lab/save`.
- [x] `health_records.py` — new `_resolve_report_date()` helper; uses the report's own date for the record's `date` field when parseable, falls back to save-time otherwise (same as old behavior).
- [x] `LabReport.jsx` — `handleSave` payload now forwards `analysis.report_date`.
- [ ] Not yet re-tested end-to-end with all 5 updated files in place.
- See `decisions.md` D28.

## ✅ Resolved (was previously "In Progress / Partial")

- **Groq LLM config scope in `crew.py`** — confirmed project-wide (`groq/llama-3.3-70b-versatile` across all 7 crews) this session via `crew.py`'s own migration comment (see `CLAUDE.md` Bug 3, now closed).

## ❌ Not Started

- JWT/token-based auth — currently plain user_id in localStorage.
- Calling-agent reliability polish.
- No automated tests.
- Deployment — everything still runs locally on Windows only.
- Tier 2 agents from the AGENTS audit brainstorm (deferred, not rejected): `DietAdvisor`, `MentalWellnessAgent`.
- Longer-term roadmap items (RAG/vector store, agent eval harness, safety-guardrail layer, streaming responses, Docker + CI, WhatsApp bot) — see `README.md` "Roadmap", not yet started or prioritized.
- **Medicine Effectiveness feature — ✅ FULLY DONE (both phases), live-tested (see "🆕 Latest session" at top of this doc and `decisions.md` D29/D31).** Phase 1 (direction annotation + delta badge) and Phase 2 (pace verdict via `MedicineEffectivenessCrew`) both built, wired, and confirmed working by the user.
- **Doctor Visit QR / clinical-summary-on-scan** — deprioritized this session in favor of the Medicine Effectiveness feature. Architecture sketch only, see `decisions.md` D29.
- `range_low`/`range_high` shaded normal-range band on Health Trends charts — deliberately dropped from this session's build (see `decisions.md` D23 "Built this session" note), can revisit later.

## Immediate Next Steps

1. **Verify `test_direction_reference.txt`'s actual path matches what `MedicineEffectivenessCrew` assumes** (`knowledge/medical_kb/test_direction_reference.txt`) — flagged as an unverified assumption when Phase 2 was built (see "🆕 Latest session" at top of this doc). Quick check, do it before relying heavily on pace verdicts.
2. Test the RAG build if not already done — run a lab report analysis, a medicine interaction check, and a symptom triage, confirm answers reference the `knowledge/medical_kb/*.txt` reference files.
3. Test the safety guardrails if not already done — hit `/triage/symptoms` with a red-flag phrase like "I have chest pain."
4. Run the agent eval harness (built + verified, not yet run) — `python eval_harness.py --suite guardrails` works standalone; full run needs `--user-id` + `GROQ_API_KEY` + Ollama running locally.
5. **Docker + CI + automated tests** — was deliberately deprioritized behind the Medicine Effectiveness work; now that both phases are done, this is the next real priority if the goal is deployment/portfolio-polish.
6. Confirm Poppler is installed and on PATH on Windows (needed only for the scanned/photo-PDF OCR fallback in `extract_text_from_lab_document()` — the tested pdfplumber text-PDF path doesn't need it).
7. (Optional) Add soft-delete/undo window to the delete-report feature — currently a hard, permanent `delete_one()`.
8. (Optional, deferred) Doctor Visit QR / clinical-summary-on-scan — see `decisions.md` D29 for the architecture sketch.
9. (Optional, deferred) Build Tier 2 agents — `DietAdvisor`, `MentalWellnessAgent` — if user wants to extend further.
## Soft-delete for health records (D35)

- `delete_vital`, `delete_prescription`, `delete_lab_report_analysis` now
  soft-delete (`deleted_at` timestamp) instead of hard-deleting the MongoDB
  document.
- All list/detail read functions (`get_vitals`, `get_prescriptions`,
  `get_lab_report_analyses`, `get_lab_report_analysis_by_id`,
  `get_full_timeline`, `get_test_trends`, `get_annotated_trends`) updated to
  exclude soft-deleted records via a shared `NOT_DELETED_FILTER`.
- No API/frontend changes required — behavior from the outside is identical
  to before; the only difference is deleted data is now recoverable at the
  database level instead of being permanently destroyed.
- Follow-up (not done): no restore endpoint/UI yet. `prescription_analyses`
  has no delete flow at all, so it wasn't touched.
  ## Docker + CI (D36) — ✅ CONFIRMED WORKING (updated from earlier "not yet tested")

`docker compose up --build` runs clean end-to-end: backend serves on
`:8080` (`Uvicorn running` log, no crash loop), frontend serves on `:5173`,
both reachable and confirmed working in-browser by the user. See
`decisions.md` D36 (UPDATE) for the 5 real issues that had to be fixed to
get here — none visible from docs alone, all Linux-container-specific:
missing `config/` folder assumption, `uv sync`/`COPY src` ordering,
2 case-sensitivity import bugs (`Donor`→`donor`, `Donor.css`→`donor.css`),
missing `libportaudio2` system lib, missing `JWT_SECRET_KEY` in `.env`.

## New follow-ups from this session

1. **Audit all frontend imports vs actual on-disk filenames for casing
   mismatches.** Two were found and fixed (`donor.jsx`/`donor.css`) purely
   by hitting them one at a time through Docker builds — Windows' case-
   insensitive filesystem means more could be silently lurking elsewhere
   and would only surface the same way (a future Docker build, or a
   Linux deployment, breaking on an import that's fine on Windows).
2. **Microphone recording will not work inside the container as-is** —
   `libportaudio2` fixes the import-time crash, but Docker doesn't pass
   through host mic hardware by default. Not urgent (backend boots fine),
   relevant only once `/consultation/speech`'s actual recording path is
   tested through Docker specifically.
3. **`JWT_SECRET_KEY` must be set in `backend/.env`** before treating the
   container as anything beyond local testing — it silently falls back to
   an insecure default otherwise (logged as a warning, not an error).
4. **Re-run the full JWT auth test flow (signup/login/401/403) against the
   containerized backend specifically** — previously only verified on
   bare-metal Windows; containerization touches `.env` loading and secret
   values, worth a quick re-confirmation.
5. Still open from the earlier addendum: fix `file_to_text.py`'s hardcoded
   Windows Tesseract path (not yet needed — hasn't been exercised through
   Docker yet, but will break OCR the first time it is).
6. Still open: grow `backend/tests/test_health.py` beyond 2 smoke tests.
7. Still open: JWT auth itself still has no D-numbered decision entry in
   `decisions.md` — the work is real and now doubly confirmed (bare-metal
   earlier, container-boots-with-it now), just still undocumented as a
   decision record.


---

## Phase 0 (P01 / P02 / P02b) — Backend Stability & Security Baseline (1 Nov 2026)

Phase 0 status: CLOSED WITH OPEN ITEMS.

### Open Items
- **C2:** BLOCKED on bare-metal Windows (browser-use mkdir of \tmp). Resolution: remove live scraping in Phase 2 (doc section 11.5), or run the price feature under Docker/WSL until then. (Evidence: P02 Step 2e, `PermissionError: [WinError 5] Access is denied: '\\tmp\\browser-use-downloads-...'` from hardcoded `/tmp` in `browser_use.browser.session` / `profile`).
- **H1 (enabled mode):** OPEN. `/call/status` stays public when `ENABLE_LIVE_CALLS=true`. Needs auth in the frontend phase. (Evidence: `backend/src/agents/main.py:975` branch delegates to `get_call_status()` without auth when enabled).
- **M5:** OPEN. Project-docs is not version controlled (Step 4 result: `git -C Project-docs rev-parse --show-toplevel` returns `fatal: not a git repository` and parent repo `ls-files` contains 0 matches).
- **MongoDB connectivity:** MONGO_FAIL ConfigurationError (Evidence: Step 5 probe executed against cluster URI failed DNS SRV resolution: `pymongo.errors.ConfigurationError: All nameservers failed to answer the query _mongodb._tcp.cluster0.flp2hip.mongodb.net. IN SRV`).

### Fixed Items (with evidence)
- [x] **C1 (Fixed):** `/ready` NameError resolved by importing `get_database` from `agents.db_connect` (Evidence: Step 1a, `main.py:50` import and `main.py:420` call).
- [x] **H1 (disabled mode) (Fixed):** `/call/status` returns safe disabled payload `{"state": "disabled", "to_number": None, "summary": None, "transcript": [], "error": None}` when `ENABLE_LIVE_CALLS` is false or unset, protecting patient privacy (Evidence: Step 1b, `main.py:975` and `test_phase0.py:test_call_status_disabled_by_default` passing).
- [x] **H2 (Fixed):** Proxy-aware client IP extraction (`get_client_ip` parsing rightmost `X-Forwarded-For` when `TRUST_PROXY_HEADERS=true` to prevent spoofing) and periodic expired key pruning in `RateLimiter` (Evidence: Step 1c, `rate_limit.py:7` and `rate_limit.py:45`).
- [x] **M1 (Fixed):** Test suite import hermeticity with in-process `dotenv.load_dotenv` monkeypatched to no-op and purge of `agents.*` from `sys.modules` (Evidence: Step 1d, `test_phase0.py:17-24`).
- [x] **M2 (Fixed):** `jwt_utils.py` calls `load_dotenv()` before reading `JWT_SECRET_KEY` and `APP_ENV` (Evidence: Step 1e, `jwt_utils.py:28-30`).
- [x] **M3 (Fixed):** Documentation references reconciled to actual codebase function names (`get_database()`, `_run_single_site()`, `_load_browser_use()`) and accurate description of `browser_use` internal `BrowserProfile()` instantiation (Evidence: `decisions.md` D40).
- [x] **M4 (Fixed):** Consolidated duplicate `decision.md` into `decisions.md` (verified 100% identical byte contents) and deleted `decision.md` (Evidence: P02 Step 7b).
- [x] **L1 (Fixed):** Replaced deprecated `@app.on_event("startup")` with modern `@asynccontextmanager` `lifespan(app: FastAPI)` with async thread execution of `ensure_indexes()` (Evidence: Step 1f, `Get-ChildItem -Pattern "on_event"` returns 0 matches; `main.py:9` import and `main.py:57` decorator verified).
- [x] **L2 (Fixed):** Repositioned docstring in `compare_prices` to be the first statement inside the function with endpoint description, before the rate-limit check (Evidence: Step 2 ast acceptance test output `DOCSTRING`).
- [x] **L3 (Fixed):** Verified all 20 keys in `.env.example` against code reads; deleted keys with count 0 (`APOLLO_PROFILE_DIR`, `ONEMG_PROFILE_DIR`) leaving 18 active keys all with count >= 1 (Evidence: Step 3c & 3d count output).

### Deferred Items
- Frontend hardcoded `http://localhost:8080` in 20+ locations (deferred to frontend integration phase).
- `POST /medicine/compare` auth dependency deferred to frontend phase to avoid breaking unauthenticated `fetch` calls.


---

## Phase 0 (Prompt 03) — Router Split: main.py Modularization (2 Nov 2026)

Router split: CLOSED. Phase 1 (central config validation, request-id logging, error contract): OPEN.

### Completed Work
- [x] **Split `main.py` into helper modules and routes package:**
  - Extracted 4 helper modules in `backend/src/agents/`: `errors.py` (11 lines), `schemas.py` (103 lines), `file_utils.py` (57 lines), `hospital_parser.py` (58 lines).
  - Created `backend/src/agents/routes/` with `__init__.py` and 12 modular routers: `system.py` (38 lines), `auth.py` (36 lines), `consultation.py` (124 lines), `lab.py` (129 lines), `medicine.py` (90 lines), `triage.py` (33 lines), `emergency.py` (69 lines), `doctor_qr.py` (107 lines), `calls.py` (58 lines), `hospitals.py` (41 lines), `donor.py` (95 lines), `health_records.py` (172 lines).
  - Rewrote `backend/src/agents/main.py` down to 57 lines (reduced by 1,327 lines, well under the 120-line ceiling). Zero `@app.` route decorators remain.
- [x] **Route Parity (100% matched):**
  - All 43 application endpoints preserved with identical methods, paths, and handlers.
  - `Compare-Object` between `P03_routes_before.txt` (43 routes) and `P03_routes_after.txt` (43 routes) showed **zero diff**.
- [x] **OpenAPI Schema Parity (100% matched):**
  - Generated OpenAPI JSON schema matched before and after byte-for-byte.
  - `OPENAPI_BEFORE_SHA256`: `88b004d616466b6cfb13f5088bc0cab02c3026234fb88bdd602ca3e6351e52cb`.
  - `OPENAPI_AFTER_SHA256`: `88b004d616466b6cfb13f5088bc0cab02c3026234fb88bdd602ca3e6351e52cb`.
- [x] **Automated Tests Passing:**
  - Updated 4 patch targets in `backend/tests/test_phase0.py` to target new module paths (`agents.routes.medicine.run_comparison`, `agents.routes.auth.login_user`, and `agents.routes.system.get_database`).
  - `python -m pytest -q`: 17 passed, 0 failed.
- [x] **No Circular Imports & Clean Importability:**
  - `from agents.main import ...` grep across `src/agents/` returned 0 matches.
  - Subprocess import verification with `APP_ENV=development` returned `IMPORT_OK`.
- [x] **Live Smoke Test:**
  - Live uvicorn instance confirmed `GET /health` (`{"status":"ok"}`), `GET /ready` (`{"status":"ready",...}`), and `GET /call/status` (`{"state":"disabled",...}`).

### Deferred Technical Debt
- Redundant LLM task output extraction loop (`getattr(task_output, "pydantic", None)`) duplicated across ~8 handlers.
- Document and speech consultation endpoints share duplicate response formatting logic.
- Domain logic coupled in route handlers (e.g. doctor-visit QR snapshot assembly in `doctor_qr.py`).
- C2 `browser_use` Windows `/tmp` permission blocker.
- H1 public `/call/status` exposure in enabled mode.
- Legacy large files exceeding 500 lines: `crew.py` (676 lines), `health_records.py` (644 lines).


---

## Prompt 04 — Behavior-Neutral Cleanup & Auth Coverage (2 Nov 2026)

Prompt 04 status: CLOSED.

### Completed Work
- [x] **LLM Output Extraction Helper (`llm_output.py`):**
  - Created `first_pydantic_dict(result)` to extract `pyd.dict()` from CrewAI task outputs without copy-pasted loop boilerplate.
  - Replaced repetitive loops in `routes/medicine.py` (2 handlers: interactions, effectiveness), `routes/triage.py` (1 handler), `routes/lab.py` (1 handler), and `routes/doctor_qr.py` (1 handler).
  - Verified with acceptance grep: only `llm_output.py` and `routes/consultation.py` contain `getattr(task_output, "pydantic", None)`.
- [x] **Protected-Route Authentication Coverage Test (`test_routes_auth.py`):**
  - Added test suite dynamically verifying all OpenAPI operations for token rejection.
  - 34 protected endpoints validated returning HTTP 401 Unauthorized when requested without a token.
  - 9 public routes verified against explicit decision records (`/`, `/health`, `/ready`, `/auth/signup`, `/auth/login`, `/medicine/compare`, `/call/status`, `/health/qr/{token}`, `/health/doctor-qr/{token}`).
  - Full pytest suite: **53 passed, 0 failed** (17 baseline + 36 auth suite cases).
- [x] **Parity & Invariant Verification:**
  - Route count preserved: 43 routes. Zero diff between `P03_routes_before.txt` and `P04_routes_after.txt`.
  - OpenAPI schema hash preserved: `88b004d616466b6cfb13f5088bc0cab02c3026234fb88bdd602ca3e6351e52cb`.
  - Live smoke test confirmed `/health` (200), `/ready` (200), and `/triage/symptoms` (401 without token).
- [x] **Documentation Corrections:**
  - Corrected D41 Pydantic model listing to the exact 16 schema class names in `schemas.py`.
  - Documented `__init__.py` existence checks in D41.
  - Added decision D42 recording helper, auth suite, and public allowlist rules.

### Deferred Items
- consultation loop dedupe (Phase 2: service layer)
- doctor_qr business-logic extraction (Phase 2: service layer)
- request-id logging and central config (Phase 1)
- C2 browser_use Windows blocker
- H1 public /call/status when calls are enabled
- M5 Project-docs not under version control


---

## Prompt 05 — Medicine Catalog Data Layer (2 Nov 2026)

Prompt 05 status: CLOSED.

### Completed Work
- [x] **Catalog Normalization & Ingestion (`import_janaushadhi.py`):**
  - Ingested PMBJP product list dated 2 Nov 2026 (`backend/data/janaushadhi/PMBJP_Product_List_2026-11-02.csv`), containing 2,445 rows. Input SHA256: `4ac1c0e8967e16de86aad74b0810fc06342d5f81bbe3e27bb7c6e5d46e02c4d3`.
  - Normalized data written to `backend/data/catalog/janaushadhi.json` with byte-for-byte deterministic reproducibility (verified identical SHA256 across consecutive runs: `b4c2d5946c638b81629c3b5f2c46358e79da6389fb30515f14534fef11ab7622`).
  - Audit report generated at `backend/data/catalog/import_report.json`:
    - Total rows: 2,445
    - Unique drug codes: 2,445
    - Zero MRP rows: 345 (marked `price_status: "not_notified"`, mrp and price_per_unit normalized to null)
    - Parse failed rows: 343 (non-strength consumables/items)
    - Pack count present rows: 1,730
    - Non-medicine rows: 350 (314 Surgical & Medical Consumables + 36 Nutraceuticals)
    - Group case variants: 6 canonicalized groups (`Anti-Fungal`, `Anti-Retroviral`, `Anti-Viral`, `Hemorrhoids & Anal Fissures`, `Hepato-Protective`, `Stomatologicals`)
    - Duplicate name+unit pairs: 1 pair (`L-Ornithine L-Aspartate 150mg and Pancreatin 100mg Tablets`, `10's`) with distinct drug codes `["1738", "2040"]`
- [x] **Catalog Search & Utility Module (`agents/catalog.py`):**
  - Pure in-memory module with zero network dependencies and no import-time I/O.
  - Implements `normalize_text`, `canonical_salt`, `parse_components`, `dosage_form`, `pack_count`, `per_unit_price`, `load_catalog`, and `search`.
  - `synonyms.json` maps common generic aliases (including keeping `s(-)amlodipine` separate as `levamlodipine`).
- [x] **Offline Test Suite (`tests/test_catalog.py`):**
  - Implemented 11 required test suites with autouse network blocking fixture (`socket.socket` raising RuntimeError).
  - 26 tests passed in 0.07s.
- [x] **Parity & Invariants Preserved:**
  - Route count: 43 (0 new routes added).
  - In-memory LF OpenAPI SHA256: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1` (verified exact match).
  - Full test suite: **79 passed, 0 failed** (53 previous + 26 catalog tests).
  - Subprocess import verification with `APP_ENV=development` returned `IMPORT_OK`.
  - Zero network library imports in `catalog.py`.
- [x] **Documentation Updates:**
  - Appended decision D43 to `decisions.md`.

### Open Items & Deferred Items
- Brand MRP seed dataset and savings calculation (deferred to P07).
- `/catalog/search` HTTP route (deferred to P07).
- Removal of live scraping (`buying_agent.py`) and `browser_use` dependency (deferred to P07).
- Frontend Compare page adjustments to use static catalog (deferred to frontend phase).
- `is_medicine` non-medicine groups review (Gautam).
- Silymarin single-salt and Cetirizine 5 mg coverage notes.


---

## Prompt 05b — Parser Fix, Exact-First Search & Metrics Alignment (2 Nov 2026)

Prompt 05b status: CLOSED.

### Completed Work
- [x] **Slash-Strength Combination Support (`catalog.py` & `import_janaushadhi.py`):**
  - Added `SLASH_STRENGTH_PATTERN` to support multi-strength bracketed specs like `(25/12.5 Mg)` or `(30/15/500 Mg)`.
  - Removed row-level `has_strength` override. Each component's `parse_ok` reflects its own parsed strength.
  - Corrected `parse_failed_rows` to `no_strength_rows` in `import_report.json` and added `slash_strength_rows` (41) and `slash_mismatch_rows` (0).
  - Regenerated `janaushadhi.json` (SHA256: `e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`) and verified 100% deterministic re-runs.
- [x] **Exact-First Search Policy (`catalog.py`):**
  - Updated `catalog.search` to return exact component-salt matches first. Fallback to `name_clean` substring match only when 0 exact matches exist.
  - Prevents substring contamination (e.g. searching `amlodipine` excludes chirally pure `levamlodipine` items).
- [x] **Expanded Test Suite (`test_catalog.py`):**
  - Replaced tautological assertion in `test_levothyroxine_synonym_search` to verify `any(c.get("salt") == "levothyroxine")`.
  - Added tests for slash combinations, unflavored syrups without strengths, sr_no 2014 row verification, amlodipine exclusion, and report metrics.
  - Catalog test count increased from 26 to 35 (all passed in 0.08s).
  - Full test suite passed: **88 passed, 0 failed** (53 baseline + 35 catalog tests).
- [x] **Artifacts & Generated File Cleanup:**
  - Deleted 8 intermediate `.txt` test and import logs from `backend/`.
- [x] **Parity & Invariant Verification:**
  - Route count: 43.
  - In-memory LF OpenAPI SHA256: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
  - Zero network imports in `catalog.py`.
- [x] **Documentation Updates:**
  - Appended decision D44 to `decisions.md`.

### Deviations
- Step 4 assertion change: `test_levothyroxine_synonym_search` second assertion changed from `price_status == "listed" or price_per_unit None` (tautological) to `any(c.get("salt") == "levothyroxine" for c in item.get("components", []))`.

### Open & Deferred Items
- Concentration notation (`mg/5 ml`) keeps only the first number (deferred to Phase 2 parser polish).
- Comma splitting on composite names like `Vitamins A,C,D,E` (deferred).
- Brand MRP seed dataset and savings calculation (deferred to P07).
- `/catalog/search` HTTP route (deferred to P07).
- Removal of live scraping (`buying_agent.py`) and `browser_use` dependency (deferred to P07).
- Frontend Compare page adjustments to use static catalog (deferred to frontend phase).
- `is_medicine` non-medicine groups review (Gautam).
- gitignore for `backend/*.txt` and decision on committing `backend/data/`.

---

## Prompt 06 — Phase 1 Close: Config Validation, Request-ID Context, Ownership 403 Coverage, and Catalog Re-verification (3 Nov 2026)

Phase 1 status: CLOSED, except the error contract (deferred to Phase 2).

### Completed Work
- [x] **Central Configuration Module (`agents.config`):**
  - Read-at-call-time functions: `env_bool`, `app_env`, `is_development`, `allowed_origins`, `live_calls_enabled`, and `trust_proxy_headers`.
  - Wildcard origins explicitly rejected with `ValueError`.
  - `validate_startup()` enforces valid `APP_ENV` and checks presence of `REQUIRED_PRODUCTION_SETTINGS` (`MONGO_URI`, `GROQ_API_KEY`, `JWT_SECRET_KEY`) in production mode, reporting variable names only (never secret values).
- [x] **Request ID Context & ASGI Middleware (`agents.request_context`):**
  - Pure ASGI `RequestIdMiddleware` assigns/propagates `x-request-id` headers (validating format `^[A-Za-z0-9\-]{8,64}$`, generating 32-hex UUID on missing/invalid).
  - Context variable `_current_request_id` tracks active ID across async request boundaries.
  - `install_log_record_factory()` attaches `request_id` (`"-"` outside requests) to all Python logging records.
  - `_server_error` in `agents.errors` uses `current_request_id()` to maintain correlation while preserving the client detail contract.
- [x] **Rate Limit & Calls Router Configuration Updates:**
  - `get_client_ip` in `rate_limit.py` uses `trust_proxy_headers()` from `agents.config`; unused `os` import removed.
  - `schedule_call` and `call_status` in `routes/calls.py` use `live_calls_enabled()` from `agents.config`; unused `os` import removed.
- [x] **Ownership Ordering Verification:**
  - Audited all 32 route handlers calling `verify_owner`. Confirmed 100% compliance: `verify_owner` is the first statement outside `try` blocks and precedes any database/LLM calls. Zero line moves needed.
- [x] **Ownership 403 Automated Coverage Suite (`tests/test_ownership.py`):**
  - Unit test for `verify_owner`.
  - 32 parameterized test cases covering 17 path-parameter routes, 11 JSON body routes, and 4 multipart routes, asserting HTTP 403 Forbidden when authenticated as `owner-user` requesting `victim-user` data.
  - Dynamic coverage test asserting every protected route with `{user_id}` in OpenAPI is covered and all test cases map to real routes.
- [x] **Clean-State Catalog Re-verification:**
  - Deleted generated catalog files and ran `scripts/import_janaushadhi.py` twice consecutively from scratch.
  - Both runs yielded identical output SHA256: `e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`.
- [x] **Test Suite & Invariants:**
  - Full test suite: **136 passed, 0 failed** (88 baseline + 48 new tests across `test_config.py`, `test_request_context.py`, and `test_ownership.py`).
  - Route count: 43 (0 new routes added).
  - OpenAPI canonical in-memory LF SHA256 preserved: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
  - Zero network library imports in `catalog.py`.
  - Live smoke test confirmed `/health` with `x-request-id` header (`89018dfd23ed438bbaf5d24385c9d453`) and `/ready` with status `ready`.

### Deviations
- P05b unrecorded deviation noted: `load_catalog.cache_clear()` was added to `tests/test_catalog.py` to prevent stale memory caching across re-import tests; documented in D45.

### Deferred Items (Phase 2 & Beyond)
- Error contract (Phase 2, coordinated with frontend `extractErrorMessage`).
- Concentration notation (`mg/5 ml`) and comma-splitting limitations in catalog parser.
- Brand MRP seed dataset and savings calculation (P07).
- `/catalog/search` HTTP route (P07).
- Removal of live scraping (`buying_agent.py`) and `browser_use` dependency (P07).
- Frontend Compare page adjustments to use static catalog.
- `is_medicine` non-medicine groups review (Gautam).
- H1 (`/call/status` public when calls are enabled).
- C2 (`browser_use` Windows `\tmp`).
- M5 (`Project-docs` not under version control).
- Decision on committing `backend/data/`.

### Constraints for P07
- Concentration rows (for example `"mg/5 ml"`) must not match a tablet strength.
- `dosage_form` is checked first in any brand mapping.

---

## Prompt 07 — Scraping Removal & Catalog-Backed Price Lookup (3 Nov 2026)

Prompt 07 status: CLOSED.

### Completed Work
- [x] **Catalog-Backed Price Lookup (`agents.price_lookup`):**
  - Created pure in-memory module querying PMBJP catalog data without network access.
  - Generates exact response shape matching previous `/medicine/compare` structure (`site: "PMBJP Jan Aushadhi"`, `product_name`, `price`, `quantity`, `delivery_info`, `product_url`, `available`, `notes`).
- [x] **Router Update (`routes/medicine.py`):**
  - Replaced import of `run_comparison` from `buying_agent` with `agents.price_lookup`.
- [x] **Scraping Removal & C2 Closure:**
  - Deleted `backend/src/agents/buying_agent.py`.
  - Zero imports or references to `browser_use` or `playwright` remain across `backend/src/`.
  - C2 (browser-use Windows `\tmp` permission error) is CLOSED in code.
- [x] **Ownership Suite Enhancement (`test_ownership.py`):**
  - Added `test_openapi_request_body_user_ids_covered` verifying that every route with `user_id` or `requester_user_id` in its requestBody schema is explicitly covered in ownership test cases.
- [x] **Price Lookup Test Suite (`tests/test_price_lookup.py`):**
  - Added 8 comprehensive offline tests verifying response shape, synonym lookup, unknown drug fallback, not-notified MRP rows, best price site logic, absence of scraping dependencies in `src`, 200 OK route execution, and OpenAPI hash preservation.
- [x] **Test Suite & Invariants:**
  - Full test suite: **145 passed, 0 failed** in 29.12s (136 baseline + 8 price lookup + 1 ownership requestBody coverage).
  - Route count: 43 (0 new routes added).
  - OpenAPI canonical in-memory LF SHA256 preserved: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
  - Catalog SHA256 invariant preserved: `e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`.
  - Live smoke test confirmed sub-second `/medicine/compare` execution with 10 catalog-backed results for Paracetamol.

### Deferred Items
- Brand seed dataset, brand-to-generic mapping, and savings calculation (P08).
- Strength-aware query matching and cross-form price normalization (P08).
- Removal of `browser_use` and `playwright` from `pyproject.toml`, `uv.lock`, and `Dockerfile` (deployment cleanup prompt).
- Error contract (Phase 2).
- `Access-Control-Expose-Headers` for `x-request-id` (frontend phase).
- Frontend Compare page adjustments to use static catalog (frontend phase).
- H1 (`/call/status` public when calls are enabled).
- M5 (`Project-docs` not under version control).
- Decision on committing `backend/data/`.
- `is_medicine` non-medicine groups review (Gautam).


---

## Prompt 08 — Search Quality: Single-Ingredient First, Strength-Aware Matching, and Concentration Guard (3 Nov 2026)

Prompt 08 status: CLOSED.

### Completed Work
- [x] **Catalog Importer Enhancement (`scripts/import_janaushadhi.py`):**
  - Added `is_combination` (`len(components) > 1`) and `is_concentration` (`re.search(r"\bmg\s*/\s*(\d+(\.\d+)?\s*)?ml\b", name_clean) is not None`) to every catalog item.
  - Added `combination_rows: 878` and `concentration_rows: 1` to `import_report.json`.
  - Determinism verified with two consecutive clean-state importer runs producing identical SHA256: `29ad8926fddb0d6acda164edd9a8ccc2ea0dc4ecd0b0ee813c58aec178860f3f`.
- [x] **Catalog Search Quality (`agents/catalog.py`):**
  - Added `parse_query(q)` parsing generic names, strengths, and units.
  - Updated `search()`:
    - If strength is given: exact salt and strength matching, concentration rows excluded, no fallback to salt-only matches (returns `[]` on mismatch).
    - If no strength is given: exact salt matches first, fallback to `name_clean` substring.
    - Sort order: `(item.is_combination, item.is_concentration, price_per_unit is None, price_per_unit or 0.0, drug_code)`. Single-ingredient products appear first.
- [x] **Price Lookup Formatter Update (`agents/price_lookup.py`):**
  - Appended notes flags in exact order: dosage_form | list dated <date> | combination | concentration (mg/ml) | price not notified.
- [x] **Test Suite & Invariants:**
  - Full test suite: **154 passed, 0 failed** in 28.35s (145 baseline + 9 new search quality tests).
  - Permitted test improvement: `test_best_price_site_when_available` updated from conditional check to unconditional assertion.
  - New test file: `backend/tests/test_search_quality.py` with 9 comprehensive tests covering `parse_query`, single-ingredient priority, 650 exact matches, concentration guards, empty on mismatch, amlodipine/levamlodipine exclusion, concentration regex verification, report counts, and 10-medicine timing.
  - Route count: 43 (0 new routes added).
  - OpenAPI canonical in-memory LF SHA256 preserved: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
  - Subprocess hermetic import verified (`IMPORT_OK`).
  - Zero `browser_use` or `playwright` occurrences in `src`.
  - Live smoke test measured timing: `148.4555 ms` for `["Paracetamol", "Paracetamol 650"]` with Paracetamol returning single-ingredient formulations first.

### Deferred Items
- Brand map and savings (P09, needs verified strip data).
- Frontend Compare update.
- Playwright and browser-use removal from `pyproject.toml`, `uv.lock`, and `Dockerfile` (deployment prompt).
- H1 (`/call/status` public when calls are enabled).
- M5 (`Project-docs` not under version control).
- Decision on committing `backend/data/`.
- `is_medicine` non-medicine groups review (Gautam).
- Concentration unit normalization.
- Comma-split limit.
- `x-request-id` header exposure to browser clients (`Access-Control-Expose-Headers`, frontend phase).


---

## Prompt 08b — Concentration Guard Fix, Strength Fallback, and Strict Network Guard (3 Nov 2026)

Prompt 08b status: CLOSED.

### Completed Work
- [x] **Concentration Guard Fix (`agents/catalog.py` & `scripts/import_janaushadhi.py`):**
  - Added `CONCENTRATION_RX` supporting per-volume expressions ("mg/ml", "mg per ml", "g per ml", "IU per ml").
  - Replaced importer expression; `concentration_rows` increased from 1 to 133, covering all 118 LOOSE matches.
  - Catalog hash updated deliberately: `779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043` (clean-state runs verified identical).
- [x] **Liquid & Drops Exclusion & Strength Fallback (`agents/catalog.py`):**
  - Added `is_concentration_row(item)` checking concentration flag and Liquid/Drops dosage forms.
  - Strength queries exclude `is_concentration_row`. Bare-number queries without unit fall back to full normalized query substring search (enabling `"omega 3"` to match 2 capsule formulations).
- [x] **Strict Network Guard (`tests/test_search_quality.py` & `tests/test_concentration_guard.py`):**
  - Updated `block_network` fixture to guard `socket.socket.connect` directly against non-loopback destinations, removing stack-frame inspection.
- [x] **New Test Suite (`tests/test_concentration_guard.py`):**
  - Added 8 tests verifying LOOSE regex coverage, exclusion of liquids/drops from strength queries, ibuprofen 100 non-concentration, paracetamol 650 regression, paracetamol 9999 empty regression, Omega 3 fallback match, and report concentration counts.
- [x] **Live Smoke Test:**
  - Tested `/medicine/compare` for `["Paracetamol 250", "Omega 3"]` in 373.9033 ms: Paracetamol 250 returned 0 liquid results, Omega 3 returned 2 capsule results.
- [x] **Invariants Maintained:**
  - Route count: 43.
  - OpenAPI canonical in-memory LF SHA256 preserved: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
  - Zero `browser_use` or `playwright` occurrences in `src`.

### Recorded Blockers
- **Step 5c Blocker (`test_concentration_items_have_mg_and_ml`):** The legacy test in `test_search_quality.py` strictly asserted both "mg" and "ml" in `name_clean` for every concentration item. The expanded `CONCENTRATION_RX` correctly flags non-mg per-volume items (e.g. `40 IU per ml` insulin, `10g per 15ml` lactulose). Per Step 5c, this test failure is recorded as an anticipated blocker without modifying the assertion.
- **Step 5a Test 3 Blocker (`test_search_paracetamol_250_first_result`):** The PMBJP dataset contains zero non-liquid (tablet/capsule) Paracetamol 250mg products. Both existing Paracetamol 250 entries (Sr 519, 1051) are oral suspensions. Because liquids are excluded from strength queries, `search("paracetamol 250", items)` returns `[]`, causing test 3 to fail.

### Deferred Items
- Brand map and savings (P09).
- Frontend Compare update.
- Playwright and browser-use removal from `pyproject.toml`, `uv.lock`, and `Dockerfile` (deployment prompt).
- H1 (`/call/status` public when calls are enabled).
- M5 (`Project-docs` not under version control).
- Decision on committing `backend/data/`.
- `is_medicine` non-medicine groups review (Gautam).
- Liquid-exclusion product decision review (Gautam).
- `x-request-id` exposure (frontend phase).


---

## PROMPT 08c: Resolve P08b Blockers, Scratch Disclosure, Open Liquid Policy (3 Nov 2026)
- **Status:** CLOSED (162 tests passed, 0 failed, full suite green in 29.62s).
- **P08b Status Update:** Changed from CLOSED to "CLOSED WITH BLOCKERS RESOLVED IN P08c".
- **Catalog JSON Hash:** `779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043` (unchanged, importer not rerun).
- **Route Count:** 43 operations.
- **OpenAPI In-Memory LF Hash:** `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1` (unchanged).

### Accomplishments
- [x] **Blocker 1 Resolved (`tests/test_search_quality.py`):**
  - Updated `test_concentration_items_have_mg_and_ml` body to assert regex strength unit `(mg|mcg|g|iu|%)` and `"ml"` substring, supporting valid non-mg concentration products like insulin (`40 IU per ml`) and lactulose (`10g per 15ml`).
- [x] **Blocker 2 Resolved (`tests/test_concentration_guard.py`):**
  - Updated `test_search_paracetamol_250_first_result` body to assert catalog data fact (2 liquid Paracetamol 250 rows exist at sr_no 519 & 1051, 0 solid rows) and current search policy (`search("paracetamol 250", items) == []`).
- [x] **Scratch File Audit & Deletion:**
  - Disclosed `backend/scratch/check_openapi.py` (created in P08). Verified absent in Step 0c and Step 6. Ensured no `scratch` directory exists.
- [x] **Git Status Audit:**
  - Corrected P08b checklist note; captured full working tree git status verbatim in P08c dump.
- [x] **Full Suite Verification:**
  - 162 passed, 0 failed across entire backend test suite.

### Open Decisions
- **Liquid Exclusion Policy (Gautam):** Status: OPEN / PENDING. Option A (keep liquid exclusion from strength queries with UI guidance) vs. Option B (allow liquids ranked after solids with dosage warnings). Reviewer recommends Option B.


---

## PROMPT 08d: Liquid Policy Option B, Paediatric Noise-Word Fix, Safety Notes, Solid-First Ranking (3 Nov 2026)
- **Status:** CLOSED (with Step 6c.5 blocker on Latanoprost drops recorded per prompt instructions). Tests: 168 passed, 1 failed.
- **Decision Adopted:** Option B (Gautam, 3 Nov 2026) — Liquids and drops included in strength queries; solid forms rank first; safety notes attached.
- **Catalog JSON Hash:** Deliberately updated to `7662d5a8a0330cd57d3dd7b09cd3ff18dc7291ce47079c65ff388292ae422e08` (old: `779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043`).
- **Live Endpoint Timing:** `POST /medicine/compare` executed in 194.9168 ms.
- **Route Count & OpenAPI Hash:** 43 operations; hash `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1` preserved.

### Accomplishments
- [x] **Paediatric Noise Words (`catalog.py` & Importer Rerun):** Added `"paediatric"` and `"pediatric"` to `_WORDS_TO_REMOVE`. Resolved sr_no 21 salt parsing to `"paracetamol"`. All 2,445 catalog items verified free of paediatric salt artifacts.
- [x] **Solid-First Ranking (`catalog.py`):** Added `is_liquid_form` and `_form_rank`. All search queries sort solid dosage forms ahead of liquids and drops.
- [x] **Per-Volume Safety Notes (`price_lookup.py`):** Added clinical notes for Drops (`"drops: follow the label. Not a tablet strength."`) and Liquids (`"liquid: strength is per volume. Dose is in ml, not tablets. Confirm the dose with a doctor or pharmacist."`).
- [x] **Test Updates (`tests/test_concentration_guard.py`):** Updated 3 test bodies to align with Option B.
- [x] **New Liquid Policy Test Suite (`tests/test_liquid_policy.py`):** Added suite covering Paracetamol 125 liquid inclusions ({21, 458, 476, 634, 1049}), Paracetamol 650 solid-first ranking, Paracetamol 9999 empty result, Paracetamol 250 safety note formatting, catalog hash verification, and absence of paediatric salt components.
- [x] **Live Smoke Test:** Verified `/medicine/compare` live response with Paracetamol 125 (3 liquid/drop results) and Latanoprost in 194.92 ms.

### Open Reviews & Deferred Items
- **Safety Copy Clinician Review (PENDING):** Safety disclaimer wording in `price_lookup.py` requires clinician/pharmacist validation before public deployment.
- **Step 6c.5 Blocker (Latanoprost Drops):** `search("Latanoprost")` returns sr_no 1810 (Liquid combination). Single-ingredient Drops (sr_no 1970) has parsed salt `"latanoprost eye drops"` (not stripped by `_WORDS_TO_REMOVE`), so exact-first logic excludes it.
- **Deferred:** Brand map and savings (P09), Playwright and browser-use removal from pyproject.toml, uv.lock, and Dockerfile (deployment prompt), H1, M5, backend\data commit decision, is_medicine review (Gautam), x-request-id exposure (frontend phase), and frontend Compare update.


---

## PROMPT 08e: Eye-Drop, Nasal and Solution Noise Words, Deliberate Catalog Hash Change, Latanoprost Single-Ingredient Drops (3 Nov 2026)
- **Status:** CLOSED (fully resolved, 0 blockers). Tests: 176 passed, 0 failed.
- **P08d Blocker Resolution:** Fully resolved. `search("Latanoprost")` returns single-ingredient eye drops sr_no 1970 as first result (ahead of combination solution sr_no 1810).
- **Catalog Regeneration Counts (Identical):**
  - `total_rows`: 2,445
  - `zero_mrp_rows`: 345
  - `no_strength_rows`: 382
  - `slash_strength_rows`: 41
  - `slash_mismatch_rows`: 0
  - `combination_rows`: 878
  - `concentration_rows`: 133
  - `pack_count_present_rows`: 1,730
  - `non_medicine_rows`: 350
- **Catalog JSON Hash:** Deliberately updated to `878324ce78166edd10ebe11ae2edcc0e229e7470adb64ce18b9cb8820c6288c3` (old: `7662d5a8a0330cd57d3dd7b09cd3ff18dc7291ce47079c65ff388292ae422e08`). Verified reproducible across 2 consecutive runs.
- **Live Endpoint Timing:** `POST /medicine/compare` executed in 163.36 ms (compared to 194.92 ms in P08d; 31.56 ms faster).
- **Route Count & OpenAPI Hash:** 43 operations; hash `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1` preserved.

### Accomplishments
- [x] **Noise Words in `_WORDS_TO_REMOVE` (`catalog.py`):** Added `"eye drops", "eye drop", "ear drops", "ear drop", "drops", "nasal", "ophthalmic", "opthalmic", "solution"`. Exactly 61 catalog rows had their parsed component salts cleaned; zero components have empty salt strings.
- [x] **Single-Ingredient Eye Drops Match First:** Verified `search("Latanoprost")` yields `[1970, 1810]`. Single-ingredient drops now matches first.
- [x] **New Test Suite (`tests/test_eye_drops.py`):** Added 7 tests covering Latanoprost single-ingredient ranking, nasal drops (Xylometazoline, Saline), solution cleaning (Povidone-Iodine, Lactulose), absence of eye-drop/solution noise tokens across all catalog component salts, and new catalog hash assertion.
- [x] **Existing Test Suite Integrity:** All existing tests pass without edits (176 passed, 0 failed, 2 warnings in ~27 seconds).
- [x] **Live Smoke Test:** Verified `/medicine/compare` live response with `["Latanoprost", "Xylometazoline"]` in 163.36 ms.
- [x] **P08d Status Updated:** P08d blocker is now marked completely resolved.

### Deferred Items
- Leftover catalog noise words: `"respirator"` (sr_no 431) and `"enzyme"` (sr_no 483).
- Safety copy clinical review (pending clinician/pharmacist validation).
- Brand map and savings (P09).
- Playwright / browser-use package removal (deployment prompt).
- Git commit decision on `backend/data/catalog/` artifacts.


---

### P08e-R addendum (3 Nov 2026)
- **Prompt:** 08e-R (Verification & Record Correction from real console output).
- **Test Suite (Real Console):** 176 passed, 0 failed, 2 warnings in 28.40s.
- **Inventory Discrepancy Corrected:** Test suite comprises 12 actual files (`test_catalog.py`: 35, `test_concentration_guard.py`: 8, `test_config.py`: 7, `test_eye_drops.py`: 7, `test_health.py`: 2, `test_liquid_policy.py`: 7, `test_ownership.py`: 35, `test_phase0.py`: 15, `test_price_lookup.py`: 8, `test_request_context.py`: 7, `test_routes_auth.py`: 36, `test_search_quality.py`: 9). No `test_agents.py`, `test_api.py`, etc. exist.
- **Config Audit:** `pytest.ini` does NOT exist (`pyproject.toml` is used).
- **Catalog Hash & Reproducibility:** Verified `878324ce78166edd10ebe11ae2edcc0e229e7470adb64ce18b9cb8820c6288c3` across two fresh importer executions.
- **Search Verification:** `search("latanoprost")` returns `[1970, 1810]` with item 1970 first.
- **Live Endpoint Audit:** `POST /medicine/compare` response conforms strictly to schema keys (`site`, `product_name`, `price`, `quantity`, `delivery_info`, `product_url`, `available`, `notes`).
- **Route Count & Hash:** 43 operations; OpenAPI LF SHA256 `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.


---

## Prompt 08f - Salt cleanup round 2 (3 Nov 2026)
Status: CLOSED. Dump: dumps\P08f_dump.md. Raw evidence: dumps\raw\P08f\.
- Words added to _WORDS_TO_REMOVE: "spray", "respules", "respirator".
- Changed salt rows: 10 (raw: 03_salt_diff.txt). sr_no 421, 425, 431, 771, 1011, 1364, 1731, 1738, 1843, 1866.
- Catalog hash: 4cac87391dbd481922221f2eb81079409f7fa58a27c1ee404d8e0493f2b14ded (two clean runs identical).
- Full suite: 184 passed, 0 failed (raw: 05_pytest_full.txt).
- Empty salts: 0. OpenAPI: 43 operations, hash 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1 unchanged. No browser_use or playwright in src.
- Live /medicine/compare response keys: PASS (raw: 05_live_keys.txt).
- Deviation: the Step 2 expectation (771 not in "fluticasone furoate") was wrong. The substring fallback had matched it. Recorded as a prompt error, not a code bug.
- Open leftovers: "aqueous" (sr 1364), "throat" (sr 1866).
- Open product decision: mixed-route results (cream, nasal spray, inhaler) under one medicine name. Route should be shown.
- Also open (P08f): "throat" leftover (sr 1866), clinician review of safety copy, Playwright/browser-use package cleanup.
- Note (P08f raw evidence): RAW FILE INDEX hashes in P08f_dump refer to the original UTF-16 files (commit d946d3b). The files were converted to UTF-8 in commit a6f712f; decoded content verified identical.


---

## Prompt 09 - Demo session backend & embedder comparison harness (5 Nov 2026)
Status: CLOSED. Dump: dumps\P09_dump.md. Raw evidence: dumps\raw\P09\.
- **Demo Session Endpoint:** `POST /demo/session` added and registered unconditionally in OpenAPI. Returns 403 when `DEMO_MODE_ENABLED` is false.
- **Rate Limit & Security:** 10 requests/min sliding window rate limit per client IP. Generates discarded bcrypt password (login via `/auth/login` rejected with 401).
- **Synthetic Persona:** Seeded with Rahul Kumar (demo) vitals (2 entries), prescriptions (2 entries: Paracetamol Tablets IP 650 mg, Amlodipine), and emergency profile.
- **Token Expiry:** 120 minutes (2 hours) vs standard 7-day user token.
- **Expiry Purge:** Automatic opportunistic purge of expired demo records across `Members` and all 8 user-associated collections (`health_vitals`, `health_prescriptions`, `emergency_profiles`, `emergency_qr_tokens`, `prescription_analyses`, `lab_report_analyses`, `blood_donors`, `doctor_qr_tokens`).
- **Tests:** 8 new tests in `test_demo_session.py`. Full suite: 192 passed, 0 failed in 33.54s.
- **Invariants:** 44 operations (was 43). Canonical OpenAPI SHA256 (separators `(',', ':')`): `2c3de56bfa32bf13518faeae6b9fb81377344dccbb188dcd2a779c0b6ba6ca42`. Indent=2 hash in `test_price_lookup.py`: `c2836fbe8a1a893c4e7f40c5485c16f4b6402347a2b6f100b4d02691ac8bdd67`.
- **Embedder Harness:** `scripts/compare_embedders.py` executed across 10 proposed queries. Measured `mxbai-embed-large` via local Ollama (1024 dim, mean 2473.69 ms, p95 7660.66 ms). Other candidates (`bge-m3`, `all-minilm`, `nomic-embed-text`) recorded as UNAVAILABLE (not pulled in Ollama / sentence-transformers not installed).
- **Pending Decision:** Production embedder choice remains PENDING Gautam's review (D54).


---

## Prompt 09b - Embedder harness retrieval overlap rewrite (5 Nov 2026)
Status: CLOSED. Dump: dumps\P09b_dump.md. Raw evidence: dumps\raw\P09b\.
- **Harness Rewrite:** `backend/scripts/compare_embedders.py` completely rewritten to measure top-5 document retrieval overlap and top-1 snippets on the MediSarthi knowledge base (126 chunks across 5 files in `backend/knowledge/medical_kb`).
- **Results:**
  - Queries: 10
  - Chunks indexed: 126
  - Candidate A: `chromadb-default`
  - Candidate B status: `mxbai-embed-large` (available via Ollama)
  - Mean top-5 overlap: 2.5
  - Runtime: 32.4 seconds
- **Invariants:** 44 operations; OpenAPI SHA256 `2c3de56bfa32bf13518faeae6b9fb81377344dccbb188dcd2a779c0b6ba6ca42` verified identical to P09.
- **Decision:** PENDING Gautam's review of top-1 snippets.


---

## Prompt 09c - Review pack for embedder decision (6 Nov 2026)
Status: CLOSED. Dump: dumps\P09c_dump.md. Raw evidence: dumps\raw\P09c\.
- **Review Pack Generator:** `backend/scripts/review_pack.py` created to resolve all A and B top-1 retrieved documents to full chunk text from the reference knowledge base (`backend/knowledge/medical_kb`).
- **Review Pack Output:** `Project-docs/dumps/raw/P09c/review_pack.md` with all 10 query sections, full top-5 ID listings, top-1 texts, and empty `RATING_A: ____   RATING_B: ____   (sahi / partial / galat)` evaluation lines.
- **Verification:** 10 of 10 queries resolved without drift. 0 ratings filled.
- **Decision:** PENDING Gautam's rating input on `review_pack.md`.


---

## Prompt 09d - Demo purge removes per-user knowledge files & D54 embedder decision (9 Nov 2026)
Status: CLOSED. Dump: dumps\P09d_dump.md. Raw evidence: dumps\raw\P09d\.
- **Per-User Knowledge File Purge:** `_user_knowledge_targets()` in `backend/src/agents/demo.py` safely identifies per-user knowledge directories (`knowledge/user_<id>/`) and files (`profile.txt`) strictly matching valid 24-char ObjectId format. Prevents path traversal (`..` rejected) and guards `medical_kb` from deletion.
- **Safe Purge Deletion:** `purge_expired_demo_users()` cleans up per-user knowledge targets with `shutil.rmtree()` / `unlink()`, trapping `OSError` without escaping exceptions or leaking paths. Returns `PurgeResult` dict (`users_purged`, `files_removed`, `file_errors`) maintaining int-equality backward compatibility with existing tests.
- **Unit Tests:** `backend/tests/test_demo_purge_files.py` added with 5 test scenarios (12 passed, 1 skipped on Windows due to symlink privilege, 0 failed across purge and session tests).
- **Invariants:** 44 OpenAPI operations; canonical SHA256 `2c3de56bfa32bf13518faeae6b9fb81377344dccbb188dcd2a779c0b6ba6ca42` unchanged. Zero diff on `crew.py` or `routes/`.
- **Decisions Recorded:** D54 (Option A provisional decision with 4 recorded known limits) and D55 (knowledge file deletion and error semantics).
- **Blockers & Deviations:** None.
