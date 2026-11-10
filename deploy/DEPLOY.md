# MediSarthi Free Tier Deployment Guide

This guide details the step-by-step procedure for deploying MediSarthi completely on free-tier infrastructure:
- **Backend**: Hugging Face Spaces (Docker SDK)
- **Frontend**: Cloudflare Pages
- **Database**: MongoDB Atlas M0 (Free Tier)
- **LLM**: Groq Free Tier (Llama 3.3 / GPT-OSS)

> **SECURITY NOTE**: Never commit secret values to version control. Set all secrets through the platform dashboards as environment variables/secrets.

---

## 1. Groq Key

1. Navigate to the [Groq Console](https://console.groq.com/).
2. Create an account or sign in.
3. Under **API Keys**, click **Create API Key**.
4. Label the key (e.g., `medisarthi-prod`).
5. Copy the generated API key (starts with `gsk_`). Store it temporarily in a password manager.
6. The key name for configuration is `GROQ_API_KEY`.

---

## 2. MongoDB Atlas M0 Setup

1. Sign up or log into [MongoDB Atlas](https://cloud.mongodb.com/).
2. Create a new Organization / Project named `MediSarthi`.
3. Deploy a new Database cluster:
   - Select **M0 Free** (Shared).
   - Choose a cloud provider and region closest to your Hugging Face Space (e.g., AWS `us-east-1` or `eu-central-1`).
4. **Database Access**:
   - Go to **Database Access** -> **Add New Database User**.
   - Select Authentication Method: **Password**.
   - Create a username (e.g., `medisarthi_user`) and a secure password.
   - Assign user privileges: `Read and write to any database`.
5. **Network Access**:
   - Go to **Network Access** -> **Add IP Address**.
   - Add `0.0.0.0/0` (Allow Access from Anywhere) with a description (e.g., `Hugging Face Space dynamic IPs`).
6. **Connection String**:
   - Return to **Database** -> Click **Connect** on cluster.
   - Choose **Drivers** -> Python.
   - Copy the SRV URI connection string: `mongodb+srv://<username>:<password>@<cluster-address>/medisarthi?retryWrites=true&w=majority`.
   - Substitute `<username>` and `<password>`. The variable name for configuration is `MONGO_URI`.

---

## 3. Hugging Face Space (Backend Deployment)

1. Navigate to [Hugging Face Spaces](https://huggingface.co/spaces).
2. Click **Create new Space**:
   - **Space name**: `medisarthi-backend`
   - **License**: `mit` (or choose appropriate)
   - **Space SDK**: **Docker** (Blank)
   - **Space hardware**: `CPU basic • 2 vCPU • 16GB RAM` (Free)
   - **Visibility**: `Public` (or `Private`)
3. Prepare the build directory locally using the automated script:
   ```powershell
   powershell -ExecutionPolicy Bypass -File backend\scripts\build_hf_space.ps1
   ```
   This generates `hf-space-build/` containing `Dockerfile`, `pyproject.toml`, `uv.lock`, `src/`, `knowledge/`, `data/`, and `README.md` with metadata.
4. Push or upload `hf-space-build/` files to your Hugging Face Space repo:
   ```bash
   cd hf-space-build
   git init
   git remote add origin https://huggingface.co/spaces/<YOUR_USERNAME>/medisarthi-backend
   git add .
   git commit -m "Deploy MediSarthi backend"
   git push -u origin main --force
   ```
5. **Configure Space Settings & Secrets**:
   - Go to Space **Settings** -> **Variables and secrets**.
   - Add all configuration entries listed in the Environment Variables table below.
   - Space builds automatically. Wait until status transitions to **Running**.
   - The live API base URL will be: `https://<YOUR_USERNAME>-medisarthi-backend.hf.space`.

---

## 4. Cloudflare Pages (Frontend Deployment)

1. Sign in to the [Cloudflare Dashboard](https://dash.cloudflare.com/) and navigate to **Workers & Pages**.
2. Click **Create Application** -> **Pages** -> **Connect to Git**.
3. Select your GitHub repository (`MediSarthi`).
4. Configure Build settings:
   - **Project Name**: `medisarthi`
   - **Production Branch**: `main`
   - **Framework Preset**: `Vite` (or None)
   - **Root directory**: `frontend/frontend`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
5. **Environment Variables**:
   - In the build configuration under **Environment Variables**, add:
     - `VITE_API_BASE`: `https://<YOUR_USERNAME>-medisarthi-backend.hf.space` (Space URL without trailing slash).
6. Click **Save and Deploy**. Cloudflare Pages will build and deploy the frontend.
7. Record the assigned live URL: `https://medisarthi.pages.dev` (or custom domain).

---

## 5. CORS Configuration

1. Return to your Hugging Face Space **Settings** -> **Variables and secrets**.
2. Update or set `ALLOWED_ORIGINS`:
   - Set value to the Cloudflare Pages live URL, e.g., `https://medisarthi.pages.dev`.
   - If using multiple origins, separate them with commas.
3. Click **Restart this Space** to load the new environment variable.
4. Verify by checking response headers on `OPTIONS` or `GET` requests from browser dev tools:
   - `access-control-allow-origin` matches `https://medisarthi.pages.dev`.

---

## Environment Variables Reference for Hugging Face Space

| Variable Name | Type | Value / Description |
| :--- | :--- | :--- |
| `APP_ENV` | Variable | `production` |
| `JWT_SECRET_KEY` | Secret | Minimum 48-character random string (e.g. generated via `openssl rand -hex 32`) |
| `MONGO_URI` | Secret | MongoDB Atlas SRV URI string with credentials and database name |
| `GROQ_API_KEY` | Secret | Groq API key (`gsk_...`) |
| `ALLOWED_ORIGINS` | Variable | Cloudflare Pages production URL (e.g., `https://medisarthi.pages.dev`) |
| `ENABLE_LIVE_CALLS` | Variable | `false` (disables external telephone/call automation during demo) |
| `TRUST_PROXY_HEADERS` | Variable | `true` (enables reverse-proxy HTTPS protocol recognition behind HF router) |
| `DEMO_MODE_ENABLED` | Variable | `true` (pre-seeds demo accounts and catalog data) |
| `CREWAI_TRACING_ENABLED` | Variable | `false` (disables telemetry/tracing network overhead in production) |

---

## 6. Smoke Test (Manual Checks on Live Deployment)

Run these 7 verification checks against the live deployed application (`https://<YOUR_USERNAME>-medisarthi-backend.hf.space` and `https://medisarthi.pages.dev`):

1. **System Health Check**:
   - `GET /api/v1/system/health` -> Expect status `200` with status `ok` for Mongo, Groq, JWT, and DB.
2. **T1: Emergency Control Triage (In-KB / Chest Pain)**:
   - Submit triage request with "sudden crushing chest pain radiating to left arm".
   - Expect immediate `Emergency` urgency level and clean refusal phrase without home care recommendations.
3. **T2: Out-of-KB Symptom Triage**:
   - Submit query for ungrounded condition (e.g. Fabry disease / rare peripheral neuropathic pain).
   - Expect conservative safety routing, no fabricated medical diagnoses, and no ungrounded drug doses.
4. **I1: Drug-Supplement Interaction Check**:
   - Query interaction for `Ashwagandha` and `Levothyroxine`.
   - Expect `200 OK` response with severity classification and safe guidance.
5. **L1: Lab Report Upload and OCR Extraction**:
   - Upload sample lab PDF/image (e.g., Ceruloplasmin / Hemoglobin test).
   - Expect successful parsing, extraction of lab test values, status, and recommended clinical actions.
6. **E1: Medicine Effectiveness Consultation**:
   - Query effectiveness for chronic therapy drug (e.g., Zelmorin).
   - Expect accurate grounded guidance indicating evidence status and doctor discussion prompt.
7. **Frontend End-to-End Navigation**:
   - Open Cloudflare Pages URL (`https://medisarthi.pages.dev`).
   - Log in using demo credentials (`rajesh@example.com` / demo password).
   - Confirm timeline, reports, medicine comparison, and appointment views render without console CORS errors.

---

## Known Limits & Operational Notes

- **Hugging Face Space Sleep**: Free CPU spaces enter sleep mode after 48 hours of inactivity. The first visitor will experience a container wake-up delay (~30-60 seconds).
- **Cold Start Latency**: PyTorch/Chroma and model initialization on container boot takes ~15-20 seconds before uvicorn begins accepting traffic.
- **Groq Free Tier TPM Limit (8000 Tokens/Min)**: Groq free tier enforces a strict 8,000 tokens-per-minute rate limit. Rapid successive multi-agent crew invocations may receive HTTP 429 errors. Space queries should be paced with 15-20 second intervals between heavy agent calls.
- **Chroma Model Baked into Image**: The Chroma embedder model (`all-MiniLM-L6-v2`) is pre-warmed during `docker build` into `/home/user/.cache/chroma`, eliminating cold download latencies on first query.
- **Knowledge Sources Instantiated Per Request**: As identified in runtime analysis, `TextFileKnowledgeSource` is instantiated on each crew run (`_build_crew_base`), ensuring user-specific profile updates are immediately reflected in RAG context.
