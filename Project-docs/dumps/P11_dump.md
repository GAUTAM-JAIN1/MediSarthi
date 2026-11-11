# P11 Dump: Free Deployment Prep (HF Space Backend + Cloudflare Pages Frontend + Atlas M0)

- **Date:** 10 Nov 2026
- **Branch:** `p11-free-deploy`
- **Base Commit:** `c085b50` (Merge pull request #10 from GAUTAM-JAIN1/p10d-triage-safety)
- **Scope:** Free-tier deployment preparation, Dockerfile rewrite for Hugging Face Space (UID 1000, port 7860), dependency cleanup (`browser-use` and `playwright` removed), HF Space build script (`backend/scripts/build_hf_space.ps1`), static deployment test (`backend/tests/test_deploy_config.py`), deploy guide (`deploy/DEPLOY.md`), and architectural decision D57.

---

## 1. RAW FILE INDEX

| File Name | SHA256 Hash |
| :--- | :--- |
| `00_precheck.txt` | `6DFECD83213F0773B25BF3E64B036D886F0EAACE46C703C4B9704AD1FB2F279F` |
| `00_dockerfile.txt` | `C8445051CD6D49EF671DF0E4A49D5F1140F2B7EDA9B399C46F1269D12EB663F6` |
| `00_docker_version.txt` | `81D1000365AC3B5F47BA496D1D44F35BF4D7D78341EFE254AB0E7A27433EE2B6` |
| `00_browser_refs.txt` | `EF73B6768B89A6B99412B0E47EDD8C69A1360490ADE63DBA9B14ED0C806727FD` |
| `00_runtime_pins.txt` | `AECC3E1482FB0CC5EE41E894A7D23CF81041773B7F604DBCCEC73FB5ACA3257E` |
| `00_tracing.txt` | `4AE2B527658B13028C174C5CBE14B9276C22AF1DCFF8EC80F41DFA69C2AC5271` |
| `00_kb_runtime.txt` | `4324748FFB34AAEBC0BADECD8DC445228C65D95C3A15149D37EA5FAF48183659` |
| `01_dockerfile_new.txt` | `9B9EB4AC9E4D4A23EFC210336D327584F109430C0BD72C5A540D1CE6377A242A` |
| `02_lock_diff.txt` | `548ECC2FC6CC77A886157961BD086FC88E6AE4605B6BA86722C43F90EA075F57` |
| `02_openapi.txt` | `BE40E923B760770AC8A7CEC8D1B8C6ECD9E9EF492177E87E52DC11034D5B2C28` |
| `02_pytest.txt` | `10E1B38F0CE47442E8E4CE5FF4301C11504567760DC2BF1D6FE2034E75513A5A` |
| `03_build_script.txt` | `0288352C6F194DBEC3F6FF59B0D6092C2524EE60BF6AFA30E4C127FCF146A964` |
| `04_tests.txt` | `89B99E3EE377750E211112751CFCBA810B61738C68CD08F56E5FBDCB1E1D2400` |

---

## 2. CLAIMS TABLE

| Claim | Raw File | Status |
| :--- | :--- | :--- |
| Precheck branch is `p11-free-deploy` branched from main at `c085b50` with clean scope files | `00_precheck.txt` | TRUE |
| Browser packages (`browser-use`, `playwright`) only referenced in build/packaging files and removed from pyproject | `00_browser_refs.txt` | TRUE |
| Docker CLI version detected (`Docker version 29.7.2`); daemon not running | `00_docker_version.txt` | TRUE |
| Knowledge sources instantiated per crew invocation in `_build_crew_base` | `00_kb_runtime.txt` | TRUE |
| Dockerfile rewritten for HF Space: python:3.11-slim, uid 1000, EXPOSE 7860, port 7860, embedder pre-warm | `01_dockerfile_new.txt` | TRUE |
| Browser-use and playwright removed from uv.lock | `02_lock_diff.txt` | TRUE |
| Runtime pins unchanged (`fastapi 0.124.0`, `pydantic 2.12.5`, `starlette 0.50.0`) | `02_lock_diff.txt` | TRUE |
| Canonical OpenAPI hash `2c3de56bfa32bf13518faeae6b9fb81377344dccbb188dcd2a779c0b6ba6ca42` (44 operations) unchanged | `02_openapi.txt` | TRUE |
| Full backend test suite passes: 210 passed, 1 skipped, 0 failed | `02_pytest.txt` | TRUE |
| HF Space packaging script `build_hf_space.ps1` runs cleanly and secret scan finds 0 matches | `03_build_script.txt` | TRUE |
| Static deploy test `backend/tests/test_deploy_config.py` passes (1 passed, 0 failed) | `04_tests.txt` | TRUE |
| Docker image build verified locally | — | NOT VERIFIED (Docker daemon not running locally; CI docker-build job is the verification) |

---

## 3. DEVIATIONS

1. **Direct Declaration of `python-multipart` and `groq` in `pyproject.toml`:**
   - When `browser-use` was removed from `pyproject.toml`, its transitive dependencies `python-multipart` and `groq` were removed by `uv lock`.
   - `python-multipart` is strictly required by FastAPI for `Form(...)` parsing in `/lab/analyse` and `/auth/login` (FastAPI raises `RuntimeError` at import time if missing).
   - `groq` is directly imported in `Calling_Ai.py`.
   - Both were explicitly declared in `pyproject.toml` dependencies. All runtime pins (`fastapi 0.124.0`, `pydantic 2.12.5`, `starlette 0.50.0`) and OpenAPI schema remained 100% byte-for-byte identical.
2. **Local Docker Build:**
   - Docker daemon was not running on the host machine. In accordance with Prompt 11 rules ("If Docker is not installed locally, record 'docker build: NOT VERIFIED locally; CI docker-build job is the verification' and continue. Do not install Docker"), local docker build was not executed and is deferred to CI.
