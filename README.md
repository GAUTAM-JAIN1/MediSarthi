\# 🩺 MediSarthi



\*\*An AI-powered healthcare companion for India\*\* — one place to describe symptoms, get prescriptions explained, compare medicine prices, book appointments via an AI voice agent, find nearby hospitals, track health records, carry an emergency-access QR medical ID, and connect with a blood-donor network.



<p align="center">

&#x20; <img alt="Python" src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python\&logoColor=white">

&#x20; <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi\&logoColor=white">

&#x20; <img alt="React" src="https://img.shields.io/badge/React-19-61DAFB?logo=react\&logoColor=black">

&#x20; <img alt="Vite" src="https://img.shields.io/badge/Vite-7-646CFF?logo=vite\&logoColor=white">

&#x20; <img alt="MongoDB" src="https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb\&logoColor=white">

&#x20; <img alt="CrewAI" src="https://img.shields.io/badge/CrewAI-Multi--Agent-orange">

&#x20; <img alt="License" src="https://img.shields.io/badge/status-in%20development-yellow">

</p>



\---



\## 📖 Overview



MediSarthi combines a \*\*multi-agent AI backend\*\* (CrewAI + LLM orchestration) with a \*\*luxury-styled React frontend\*\* to consolidate the scattered steps of managing personal health into a single assistant-driven flow — from symptom triage to emergency identification.



The project began as a college/personal collaboration and has since been substantially reworked — new authentication system, hardened data model, three new AI agents, and a complete visual redesign — into a portfolio-grade full-stack product.



\## ✨ Features



| Feature | Description |

|---|---|

| 🗣️ \*\*Symptom Consultation\*\* | Describe symptoms by voice/text (Hindi/English); a CrewAI-orchestrated agent provides guidance and can set medicine reminders. |

| 📄 \*\*Prescription OCR\*\* | Upload a photo of a prescription — Tesseract OCR extracts the text and routes it through the same consultation flow. |

| 🧪 \*\*Lab Report Analyser\*\* | Upload a lab/blood test report and get a plain-language, per-value breakdown of what's normal and what's worth a doctor's attention. |

| 💊 \*\*Medicine Interaction Checker\*\* | Enter multiple medicines and check whether they're safe to take together. |

| 🚑 \*\*Symptom Triage\*\* | Get an urgency read — rest at home, see a doctor, or seek emergency care. |

| 💰 \*\*Medicine Price Comparison\*\* | Browser-automation agents scrape live prices across pharmacy sites in parallel, with a human-in-the-loop "confirm before cart" step. |

| 📞 \*\*AI Voice Appointment Booking\*\* | An AI agent calls a clinic and attempts to book an appointment (Twilio + AssemblyAI + Deepgram stack). |

| 🏥 \*\*Nearby Hospital Finder\*\* | OpenStreetMap-based search by city/state. |

| 📊 \*\*Health Records Dashboard\*\* | Vitals (BP, blood sugar, weight) and prescriptions combined into a single timeline. |

| 🆘 \*\*Emergency QR Medical ID\*\* | Generates a QR code linking to a public, no-login page showing blood group, allergies, and emergency contact — for use in real emergencies. |

| 🩸 \*\*Blood Donor Network\*\* | Donor registration, availability toggle, and matching by blood group + location. |

| 📅 \*\*Calendar Reminders\*\* | Google Calendar integration for medicine timing. |



\## 🏗️ Architecture



```

MediSarthi/

├── backend/     → FastAPI + CrewAI multi-agent system (Python)

└── frontend/    → React 19 + Vite single-page application

```



\*\*Multi-agent design:\*\* Domain-specific CrewAI crews (`LabReportCrew`, `MedicineInteractionCrew`, `SymptomTriageCrew`, `SpeechCrew`, `FileCrew`) each own a narrow task, coordinated behind clean FastAPI endpoints.



\*\*Data model:\*\* A hybrid MongoDB approach — bounded, frequently-accessed fields live directly on the user document, while unbounded/append-only data (health timeline entries, donor requests) lives in separate collections.



\## 🛠️ Tech Stack



\*\*Backend\*\*

\- FastAPI · CrewAI · MongoDB (`pymongo`) · Tesseract OCR (`pytesseract`)

\- Twilio + AssemblyAI + Deepgram (AI voice calling agent)

\- `browser-use` (Playwright-based) — live pharmacy price scraping

\- Google Calendar API (OAuth) · `bcrypt` password hashing



\*\*Frontend\*\*

\- React 19 + Vite 7 · `react-router-dom`

\- `react-icons` (Lucide set) · `qrcode.react`

\- Custom CSS design system (no framework) — Playfair Display + Inter typography



\## 🚀 Getting Started



\### Prerequisites

\- Python 3.11 (`>=3.10,<3.14`)

\- Node.js (v18+)

\- MongoDB Atlas account (or local MongoDB)



\### Backend

```bash

cd backend

python -m venv venv

.\\venv\\Scripts\\Activate      # Windows

pip install -e .

cp .env.example .env         # then fill in your own keys

python src/agents/main.py

```



\### Frontend

```bash

cd frontend/frontend

npm install

npm run dev

```



Open the printed local URL (typically `http://localhost:5173`).



\### Environment Variables

Create a `.env` file inside `backend/` with:

```

MONGO\_URI=

GEMINI\_API\_KEY=

GOOGLE\_API\_KEY=

GROQ\_API\_KEY=

ASSEMBLY\_API\_KEY=

DEEPGRAM\_API\_KEY=

TWILIO\_ACCOUNT\_SID=

TWILIO\_AUTH\_TOKEN=

TWILIO\_PHONE\_NUMBER=

```

> None of these are included in this repository. You'll need your own API keys from each provider.



\## 📌 Project Status



\- ✅ Auth, health records, emergency QR ID, and the blood donor system are complete and tested end-to-end.

\- ✅ 8 of 10 frontend routes are wired to the live backend.

\- 🚧 Medicine price comparison is UI-complete, backend integration in progress.

\- 🚧 Lab Report Analyser, Medicine Interaction Checker, and Symptom Triage agents are code-complete, pending live testing.



\## 🔒 Security



\- No credentials, API keys, or tokens are committed to this repository — all secrets are loaded from a local, git-ignored `.env` file.

\- Human-in-the-loop confirmation is required before any automated purchase action.



\## 👤 Author



\*\*Gautam Jain\*\*

Second-year Computer Engineering student, specializing in NLP/LLMs and Deep Learning.

\[GitHub](https://github.com/GAUTAM-JAIN1)



\---



<p align="center"><i>Built as a portfolio project — feedback and suggestions welcome.</i></p>



