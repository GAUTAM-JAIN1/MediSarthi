<div align="center">

# 🩺 MediSarthi

### AI-powered healthcare companion for India

*Symptom triage · Prescription analysis · Medicine price comparison · AI voice appointment booking · Emergency QR Medical ID · Blood donor network*

<br>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-7-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)

<br>

[![Status](https://img.shields.io/badge/status-active%20development-yellow?style=flat-square)](.)
[![Made with CrewAI](https://img.shields.io/badge/multi--agent-CrewAI-orange?style=flat-square)](.)
[![Last Commit](https://img.shields.io/github/last-commit/GAUTAM-JAIN1/MediSarthi?style=flat-square&color=blue)](.)

</div>

<br>

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Project Status](#-project-status)
- [Security](#-security)
- [Roadmap](#-roadmap)
- [Author](#-author)

<br>

## 📖 Overview

> People juggle disconnected steps when dealing with health — describing symptoms, reading confusing prescriptions, comparing medicine prices, booking appointments, finding a hospital in an emergency, and having no quick way to share critical medical info with a stranger. **MediSarthi consolidates all of this into one AI-driven flow.**

MediSarthi pairs a **multi-agent AI backend** (CrewAI orchestration) with a **luxury-styled React frontend**. What started as a college collaboration has been substantially reworked — new authentication system, hardened MongoDB data model, three additional AI agents, and a complete visual redesign — into a portfolio-grade full-stack product.

<br>

## ✨ Features

<table>
<tr>
<td width="50%" valign="top">

### 🤖 AI Health Agents
- 🗣️ **Symptom Consultation** — voice/text (Hindi/English), sets medicine reminders
- 📄 **Prescription OCR** — photo → extracted text → guidance
- 🧪 **Lab Report Analyser** — plain-language breakdown of test values
- 💊 **Medicine Interaction Checker** — safety check across multiple medicines
- 🚑 **Symptom Triage** — home rest, doctor visit, or emergency care

</td>
<td width="50%" valign="top">

### 🏥 Platform Features
- 💰 **Medicine Price Comparison** — live pharmacy scraping, human-confirmed cart
- 📞 **AI Voice Appointment Booking** — agent calls & books with a clinic
- 🏥 **Nearby Hospital Finder** — OpenStreetMap-based search
- 📊 **Health Records Dashboard** — vitals + prescriptions timeline
- 🆘 **Emergency QR Medical ID** — public no-login emergency page
- 🩸 **Blood Donor Network** — registration, availability, matching

</td>
</tr>
</table>

<br>

## 🏗️ Architecture

```
MediSarthi/
├── backend/      FastAPI + CrewAI multi-agent system (Python)
│   └── src/agents/
│       ├── main.py           → All HTTP endpoints
│       ├── crew.py           → CrewAI agent/crew definitions
│       ├── auth.py           → Email/password authentication
│       ├── health_records.py → Vitals, timeline, emergency QR logic
│       ├── donor.py          → Blood donor matching
│       └── buying_agent.py   → Parallel pharmacy price scraping
│
└── frontend/     React 19 + Vite single-page application
    └── frontend/src/Pages/   → 10 routed pages, custom design system
```

<details>
<summary><b>🧠 Multi-agent design details</b></summary>
<br>

Domain-specific CrewAI crews (`LabReportCrew`, `MedicineInteractionCrew`, `SymptomTriageCrew`, `SpeechCrew`, `FileCrew`) each own a narrow task, coordinated behind clean FastAPI endpoints — rather than one monolithic prompt handling everything.

**Data model:** a hybrid MongoDB approach — bounded, frequently-accessed fields live directly on the user document, while unbounded/append-only data (health timeline entries, donor requests) lives in separate collections for scalability.

</details>

<br>

## 🛠️ Tech Stack

<table>
<tr>
<th>Layer</th>
<th>Technologies</th>
</tr>
<tr>
<td><b>Backend</b></td>
<td>
<img src="https://img.shields.io/badge/-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white">
<img src="https://img.shields.io/badge/-CrewAI-orange?style=flat-square">
<img src="https://img.shields.io/badge/-MongoDB-47A248?style=flat-square&logo=mongodb&logoColor=white">
<img src="https://img.shields.io/badge/-Tesseract%20OCR-black?style=flat-square">
<img src="https://img.shields.io/badge/-Twilio-F22F46?style=flat-square&logo=twilio&logoColor=white">
<img src="https://img.shields.io/badge/-Playwright-2EAD33?style=flat-square&logo=playwright&logoColor=white">
</td>
</tr>
<tr>
<td><b>Frontend</b></td>
<td>
<img src="https://img.shields.io/badge/-React%2019-61DAFB?style=flat-square&logo=react&logoColor=black">
<img src="https://img.shields.io/badge/-Vite%207-646CFF?style=flat-square&logo=vite&logoColor=white">
<img src="https://img.shields.io/badge/-React%20Router-CA4245?style=flat-square&logo=reactrouter&logoColor=white">
<img src="https://img.shields.io/badge/-Custom%20CSS-1572B6?style=flat-square&logo=css3&logoColor=white">
</td>
</tr>
<tr>
<td><b>Infra & Auth</b></td>
<td>
<img src="https://img.shields.io/badge/-Google%20Calendar%20API-4285F4?style=flat-square&logo=googlecalendar&logoColor=white">
<img src="https://img.shields.io/badge/-bcrypt-blue?style=flat-square">
<img src="https://img.shields.io/badge/-Deepgram-13EF93?style=flat-square">
</td>
</tr>
</table>

<br>

## 🚀 Getting Started

### Prerequisites
`Python 3.11` · `Node.js 18+` · `MongoDB Atlas account`

### Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate      # Windows
pip install -e .
cp .env.example .env         # then fill in your own keys
python src/agents/main.py
```

### Frontend
```bash
cd frontend/frontend
npm install
npm run dev
```

Open the printed local URL — typically `http://localhost:5173`.

<details>
<summary><b>🔑 Environment variables reference</b></summary>
<br>

Create a `.env` file inside `backend/`:
```env
MONGO_URI=
GEMINI_API_KEY=
GOOGLE_API_KEY=
GROQ_API_KEY=
ASSEMBLY_API_KEY=
DEEPGRAM_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
```
> ⚠️ None of these are included in this repository. You'll need your own API keys from each provider.

</details>

<br>

## 📌 Project Status

| Module | Status |
|---|---|
| Auth, Health Records, Emergency QR ID, Blood Donor System | ✅ Complete & tested end-to-end |
| Frontend routes wired to live backend | ✅ 8 / 10 |
| Medicine Price Comparison | 🚧 UI complete, backend integration in progress |
| Lab Report Analyser · Medicine Interaction Checker · Symptom Triage | 🚧 Code complete, pending live testing |

<br>

## 🔒 Security

- No credentials, API keys, or tokens are committed to this repository — all secrets load from a local, git-ignored `.env` file.
- Human-in-the-loop confirmation is required before any automated purchase action.
- Emergency QR pages expose only an explicitly opted-in safe subset of data — never full account access.

<br>

## 🗺️ Roadmap

- [ ] Complete live testing for the 3 newest AI agents
- [ ] Wire Medicine Price Comparison to the real backend
- [ ] Harden AI voice-calling agent reliability
- [ ] Deploy to a public environment

<br>

## 👤 Author

**Gautam Jain**
Second-year Computer Engineering student · NLP/LLMs & Deep Learning

[![GitHub](https://img.shields.io/badge/GitHub-GAUTAM--JAIN1-181717?style=for-the-badge&logo=github)](https://github.com/GAUTAM-JAIN1)

<br>

<div align="center">

*Built as a portfolio project — feedback and suggestions welcome.*

</div>