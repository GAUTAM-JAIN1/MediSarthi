import { useState, useEffect, useRef } from "react";
import {
  LuPhone, LuMapPin, LuSearch, LuLoader, LuBot,
  LuCircleCheck, LuTriangleAlert, LuExternalLink,
  LuClock, LuPhoneCall, LuSparkles, LuLocate,
  LuShieldCheck, LuCalendarCheck, LuChevronDown,
} from "react-icons/lu";
import Layout from "../components/Layout";
import { useUser } from "../hooks/useUser";
import "./Appointments.css";

const extractErrorMessage = (detail, fallback) => {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((d) => (typeof d === "string" ? d : d?.msg || JSON.stringify(d))).join(", ");
  if (typeof detail === "object" && detail.msg) return detail.msg;
  return fallback;
};

const CALL_STATUS_MESSAGES = {
  dialing: "AI agent number dial kar raha hai...",
  in_call: "Call connect ho gayi — AI baat kar raha hai...",
};

// 4-step visual progress the "AI Call Agent" card shows. Backend only ever
// reports two real in-flight states (dialing / in_call) plus a terminal
// completed/failed — there's no distinct "confirming slot" signal from the
// server. So dialing→step 0, in_call→step 2 (folds "checking availability"
// and "confirming" together, since both happen inside one phone call we
// can't see the inside of), completed→step 3. This is a UI approximation
// of real signals, not fabricated progress — don't add a fake step 1 tick
// independent of an actual backend state.
const STEPS = [
  { key: "calling", label: "Calling Clinic", icon: LuPhoneCall },
  { key: "checking", label: "Checking Slots", icon: LuCalendarCheck },
  { key: "confirming", label: "Confirming", icon: LuShieldCheck },
  { key: "done", label: "Booking Done", icon: LuCircleCheck },
];

const HOSPITALS_PAGE_SIZE = 4;

export default function Appointments() {
  const { userId, isLoggedIn } = useUser();

  // ── Hospital search ────────────────────────────────────────────────────────
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [hospitals, setHospitals] = useState([]);
  const [hospitalLoading, setHospitalLoading] = useState(false);
  const [hospitalError, setHospitalError] = useState("");
  const [visibleCount, setVisibleCount] = useState(HOSPITALS_PAGE_SIZE);
  const [locationMsg, setLocationMsg] = useState("");
  const cityInputRef = useRef(null);

  // ── AI call booking ────────────────────────────────────────────────────────
  const [callForm, setCallForm] = useState({
    number: "",
    patient_name: "",
    disease: "",
    reason: "",
    doctor_name: "",
    availability: "",
  });
  const [callStatus, setCallStatus] = useState("idle"); // idle | loading | success | error
  const [callMsg, setCallMsg] = useState("");
  const [callSummary, setCallSummary] = useState(null);
  const [callTranscript, setCallTranscript] = useState([]);
  const [activeStep, setActiveStep] = useState(0);
  const [targetHospitalName, setTargetHospitalName] = useState(""); // for the "Trying: X" illustration line
  const pollRef = useRef(null);

  // ── Hospital search ────────────────────────────────────────────────────────
  const searchHospitals = async () => {
    if (!isLoggedIn) { setHospitalError("Pehle login karo."); return; }
    if (!city && !state) { setHospitalError("City ya state toh daalo."); return; }
    setHospitalError("");
    setHospitalLoading(true);
    setHospitals([]);
    setVisibleCount(HOSPITALS_PAGE_SIZE);
    try {
      const res = await fetch("http://localhost:8080/hospitals/nearby", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          city: city || undefined,
          state: state || undefined,
          country: "India",
          limit: 10,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setHospitalError(extractErrorMessage(data.detail, "Kuch gadbad ho gayi."));
      } else {
        const list = Array.isArray(data.hospitals) ? data.hospitals : [];
        setHospitals(list);
        if (list.length === 0) setHospitalError("Is area mein koi hospital nahi mila.");
      }
    } catch {
      setHospitalError("Backend se connect nahi ho pa raha. Server chal raha hai?");
    } finally {
      setHospitalLoading(false);
    }
  };

  // "Use my location" — we don't have a reverse-geocoding endpoint on the
  // backend, so this can't auto-fill city/state. It asks the browser for
  // permission (real signal) and then hands control back to the user
  // honestly instead of pretending to auto-detect a city.
  const useMyLocation = () => {
    if (!navigator.geolocation) {
      setLocationMsg("Is browser mein location access nahi hai — manually daal do.");
      return;
    }
    setLocationMsg("Location maang rahe hain...");
    navigator.geolocation.getCurrentPosition(
      () => {
        setLocationMsg("Location mil gayi — city/state neeche khud confirm kar do.");
        cityInputRef.current?.focus();
      },
      () => setLocationMsg("Location access nahi mila — manually city/state daal do.")
    );
  };

  // ── Prefill call form from hospital card ──────────────────────────────────
  const numberInputRef = useRef(null);

  const prefillFromHospital = (h) => {
    const hasPhone = Boolean(h.phone);
    setCallForm((f) => ({
      ...f,
      number: hasPhone ? h.phone : f.number,
    }));
    setTargetHospitalName(h.name || "");
    document.querySelector(".ms-appt-call-card")?.scrollIntoView({ behavior: "smooth" });
    setTimeout(() => {
      numberInputRef.current?.focus();
      if (hasPhone) numberInputRef.current?.select();
    }, 400);
  };

  // ── Schedule call ─────────────────────────────────────────────────────────
  const handleCallChange = (e) =>
    setCallForm({ ...callForm, [e.target.name]: e.target.value });

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const pollCallStatus = () => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch("http://localhost:8080/call/status");
        if (!res.ok) return;
        const data = await res.json();

        if (data.state === "completed") {
          setCallSummary(data.summary || "Call complete ho gayi, par summary nahi mili.");
          setCallTranscript(data.transcript || []);
          setCallStatus("success");
          setCallMsg("Call complete ho gayi!");
          setActiveStep(3);
          stopPolling();
        } else if (data.state === "failed") {
          setCallMsg(data.error || "Call fail ho gayi.");
          setCallStatus("error");
          stopPolling();
        } else if (CALL_STATUS_MESSAGES[data.state]) {
          setCallMsg(CALL_STATUS_MESSAGES[data.state]);
          setActiveStep(data.state === "dialing" ? 0 : 2);
        }
      } catch {
        // network blip — just retry on the next tick
      }
    }, 3000);
  };

  useEffect(() => stopPolling, []);

  const scheduleCall = async () => {
    if (!isLoggedIn) { setCallMsg("Pehle login karo."); setCallStatus("error"); return; }
    if (!callForm.number.trim()) {
      setCallMsg("Clinic ka phone number zaroori hai.");
      setCallStatus("error");
      return;
    }
    setCallStatus("loading");
    setCallMsg("");
    setCallSummary(null);
    setCallTranscript([]);
    setActiveStep(0);
    if (!targetHospitalName) setTargetHospitalName(callForm.number.trim());
    try {
      const res = await fetch("http://localhost:8080/call/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          number: callForm.number.trim(),
          disease: callForm.disease || "General Checkup",
          doctor_name: callForm.doctor_name || "Any Doctor",
          availability: callForm.availability || "Any Available Time",
          patient_name: callForm.patient_name,
          reason: callForm.reason,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setCallMsg(extractErrorMessage(data.detail, "Call schedule nahi ho saka."));
        setCallStatus("error");
      } else {
        setCallMsg(data.message || "AI agent call kar raha hai!");
        setCallStatus("loading");
        pollCallStatus();
      }
    } catch {
      setCallMsg("Backend se connect nahi ho pa raha.");
      setCallStatus("error");
    }
  };

  const visibleHospitals = hospitals.slice(0, visibleCount);
  const hasMoreHospitals = hospitals.length > visibleCount;
  // First hospital with a real phone number is the actionable one — a real
  // signal, not a fabricated ranking, so it's fair to badge it.
  const recommendedIndex = hospitals.findIndex((h) => h.phone);

  const isLive = callStatus === "loading";

  return (
    <Layout>
      {/* ── Hero ── */}
      <div className="ms-appt-hero">
        <div className="ms-appt-hero-left">
          <div className="ms-page-badge">Appointments</div>
          <h1 className="ms-appt-hero-title">
            Find care,<br />
            <span className="ms-accent">book it instantly.</span>
          </h1>
          <p className="ms-appt-hero-desc">
            Search hospitals near you, then let our AI agent call the clinic and
            book an appointment on your behalf.
          </p>
          <div className="ms-appt-pills">
            <span className="ms-appt-pill"><LuClock size={14} /> Real-time availability</span>
            <span className="ms-appt-pill"><LuPhoneCall size={14} /> AI calls &amp; confirms</span>
            <span className="ms-appt-pill"><LuSparkles size={14} /> No waiting, just care</span>
          </div>
        </div>

        <div className="ms-appt-hero-right">
          <div className="ms-appt-illustration">
            <div className={`ms-appt-phone-mock${isLive ? " ms-appt-phone-mock--live" : ""}`}>
              <div className="ms-appt-phone-notch" />
              <div className="ms-appt-bot-avatar">
                <svg viewBox="0 0 64 64" width="46" height="46" fill="none">
                  <rect x="12" y="18" width="40" height="34" rx="14" fill="var(--ms-dark-navy)" />
                  <circle cx="24" cy="35" r="4.5" fill="var(--ms-soft-gold)" />
                  <circle cx="40" cy="35" r="4.5" fill="var(--ms-soft-gold)" />
                  <rect x="26" y="46" width="12" height="3" rx="1.5" fill="var(--ms-soft-gold)" opacity="0.7" />
                  <line x1="32" y1="18" x2="32" y2="10" stroke="var(--ms-luxury-brown)" strokeWidth="2.5" strokeLinecap="round" />
                  <circle cx="32" cy="7" r="3.5" fill="var(--ms-luxury-brown)" />
                </svg>
              </div>
              <div className="ms-appt-waveform" aria-hidden="true">
                {Array.from({ length: 14 }).map((_, i) => (
                  <span key={i} style={{ animationDelay: `${(i % 7) * 0.09}s` }} />
                ))}
              </div>
              <p className="ms-appt-phone-label">AI Agent Calling...</p>
              <p className="ms-appt-phone-sub">
                Trying: {targetHospitalName || "Select a hospital below"}
              </p>
              <p className="ms-appt-phone-eta">Estimated wait: 10–20 sec</p>
            </div>

            <svg className="ms-appt-arrow" viewBox="0 0 160 60" width="140" height="55" fill="none" aria-hidden="true">
              <path d="M2 10 C 60 10, 100 50, 155 45" stroke="var(--ms-soft-gold)" strokeWidth="2.5" strokeDasharray="6 7" strokeLinecap="round" />
              <path d="M144 38 L157 45 L146 53" stroke="var(--ms-soft-gold)" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            </svg>

            <div className="ms-appt-hospital-mock">
              <svg viewBox="0 0 120 120" width="130" height="130">
                <ellipse cx="60" cy="108" rx="42" ry="6" fill="var(--ms-luxury-brown)" opacity="0.12" />
                <rect x="22" y="34" width="76" height="70" rx="6" fill="var(--ms-white-card)" stroke="var(--ms-soft-gold)" strokeWidth="2" />
                <polygon points="14,38 60,10 106,38" fill="var(--ms-btn)" />
                <rect x="50" y="16" width="20" height="20" fill="var(--ms-soft-gold)" />
                <rect x="57" y="10" width="6" height="32" fill="var(--ms-btn)" />
                <rect x="44" y="19" width="32" height="6" fill="var(--ms-btn)" />
                {[0, 1, 2].map((row) =>
                  [0, 1, 2, 3].map((col) => (
                    <rect
                      key={`${row}-${col}`}
                      x={30 + col * 16}
                      y={48 + row * 16}
                      width="9" height="9" rx="1.5"
                      fill="var(--ms-bg-secondary)"
                    />
                  ))
                )}
                <rect x="52" y="90" width="16" height="14" rx="1.5" fill="var(--ms-luxury-brown)" />
              </svg>
              <div className="ms-appt-hospital-pin">
                <LuMapPin size={16} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {!isLoggedIn && (
        <div className="ms-appt-login-notice">
          <LuTriangleAlert size={14} />
          &nbsp;Yeh features use karne ke liye&nbsp;
          <a href="/auth">login karo</a>.
        </div>
      )}

      <div className="ms-appt-grid">
        {/* ── Hospital Search ── */}
        <section className="ms-card ms-appt-section ms-appt-find-card">
          <div className="ms-appt-section-header">
            <span className="ms-appt-step-num">1</span>
            <div>
              <h2 className="ms-appt-section-title"><LuMapPin size={16} /> Find Nearby Hospitals</h2>
              <p className="ms-appt-section-desc">We show top hospitals with live availability near you.</p>
            </div>
          </div>

          <div className="ms-appt-search-bar">
            <LuSearch size={16} className="ms-appt-search-icon" />
            <input
              className="ms-appt-search-input"
              placeholder="City, e.g. Faridabad"
              value={city}
              ref={cityInputRef}
              onChange={(e) => setCity(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && searchHospitals()}
            />
            <span className="ms-appt-search-divider" />
            <input
              className="ms-appt-search-input"
              placeholder="State, e.g. Haryana"
              value={state}
              onChange={(e) => setState(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && searchHospitals()}
            />
            <button className="ms-appt-locate-btn" onClick={useMyLocation} type="button" title="Use my location">
              <LuLocate size={15} />
            </button>
          </div>
          {locationMsg && <p className="ms-appt-location-msg">{locationMsg}</p>}

          <button
            className="ms-btn-primary ms-appt-search-btn"
            onClick={searchHospitals}
            disabled={hospitalLoading || !isLoggedIn}
          >
            {hospitalLoading ? <LuLoader className="ms-spin" /> : <LuSearch size={15} />}
            {hospitalLoading ? " Dhundh raha hoon..." : " Search Nearby"}
          </button>

          {/* Decorative map mockup — illustrative only, no live map data */}
          <div className="ms-appt-map">
            <svg viewBox="0 0 300 160" width="100%" height="140" preserveAspectRatio="none" aria-hidden="true">
              <rect width="300" height="160" fill="var(--ms-bg-primary)" />
              <path d="M0 40 H300 M0 90 H300 M0 130 H300" stroke="var(--ms-soft-gold)" strokeWidth="1" opacity="0.5" />
              <path d="M60 0 V160 M160 0 V160 M230 0 V160" stroke="var(--ms-soft-gold)" strokeWidth="1" opacity="0.5" />
              <circle cx="150" cy="80" r="34" fill="var(--ms-luxury-brown)" opacity="0.1" />
            </svg>
            {visibleHospitals.slice(0, 3).map((_, i) => (
              <span
                key={i}
                className="ms-appt-map-pin"
                style={{ left: `${28 + i * 26}%`, top: `${30 + (i % 2) * 34}%` }}
              >
                <LuMapPin size={16} />
              </span>
            ))}
          </div>

          {hospitalError && <p className="ms-appt-error">{hospitalError}</p>}

          {visibleHospitals.length > 0 && (
            <>
              <div className="ms-hospital-list">
                {visibleHospitals.map((h, i) => (
                  <div key={i} className="ms-hospital-card">
                    <div className="ms-hospital-pin-box"><LuMapPin size={16} /></div>
                    <div className="ms-hospital-info">
                      <p className="ms-hospital-name">
                        {h.name || "Hospital"}
                        {i === recommendedIndex && (
                          <span className="ms-badge ms-badge--gold ms-hospital-badge">Recommended</span>
                        )}
                      </p>
                      <p className="ms-hospital-addr">{h.address || h.city || "Address unavailable"}</p>
                      {h.phone && <p className="ms-hospital-phone"><LuPhone size={12} /> {h.phone}</p>}
                    </div>
                    <div className="ms-hospital-actions">
                      <button
                        className="ms-btn-secondary ms-hospital-btn"
                        onClick={() => prefillFromHospital(h)}
                      >
                        <LuBot size={13} /> Select
                      </button>
                      {h.maps_url && (
                        <a
                          href={h.maps_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ms-btn-secondary ms-hospital-btn"
                        >
                          <LuExternalLink size={13} /> Map
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              {hasMoreHospitals && (
                <button
                  className="ms-appt-more-btn"
                  onClick={() => setVisibleCount((v) => v + HOSPITALS_PAGE_SIZE)}
                >
                  View more hospitals <LuChevronDown size={14} />
                </button>
              )}
            </>
          )}
        </section>

        {/* ── AI Call Booking ── */}
        <section className="ms-card ms-appt-section ms-appt-call-card">
          <div className="ms-appt-section-header">
            <span className="ms-appt-step-num">2</span>
            <div>
              <h2 className="ms-appt-section-title"><LuBot size={16} /> AI Call Agent</h2>
              <p className="ms-appt-section-desc">
                Our AI agent will call the clinic, talk to the receptionist, and book the appointment for you.
              </p>
            </div>
            {isLive && <span className="ms-appt-live-badge"><span className="ms-appt-live-dot" />Live</span>}
          </div>

          <div className="ms-appt-steps">
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              const stepState =
                callStatus === "error" && i === activeStep ? "error" :
                i < activeStep || (i === activeStep && callStatus === "success") ? "done" :
                i === activeStep && isLive ? "active" : "pending";
              return (
                <div key={s.key} className={`ms-appt-step ms-appt-step--${stepState}`}>
                  <div className="ms-appt-step-icon"><Icon size={16} /></div>
                  <span className="ms-appt-step-label">{s.label}</span>
                  {i < STEPS.length - 1 && <span className="ms-appt-step-connector" />}
                </div>
              );
            })}
          </div>

          {isLive && (
            <div className="ms-appt-call-banner">
              <div className="ms-appt-call-banner-icon"><LuPhoneCall size={16} /></div>
              <div>
                <p className="ms-appt-call-banner-title">
                  Calling {targetHospitalName || "clinic"}...
                </p>
                <p className="ms-appt-call-banner-sub">{callMsg || "AI agent is on the call."}</p>
              </div>
              <div className="ms-appt-waveform ms-appt-waveform--sm" aria-hidden="true">
                {Array.from({ length: 8 }).map((_, i) => (
                  <span key={i} style={{ animationDelay: `${(i % 5) * 0.1}s` }} />
                ))}
              </div>
            </div>
          )}

          <div className="ms-appt-form">
            <div className="ms-appt-form-row">
              <div className="ms-field">
                <label className="ms-label">Your Phone Number *</label>
                <input
                  className="ms-input"
                  name="number"
                  placeholder="+91 98765 43210"
                  value={callForm.number}
                  onChange={handleCallChange}
                  ref={numberInputRef}
                />
              </div>
              <div className="ms-field">
                <label className="ms-label">Your Name</label>
                <input
                  className="ms-input"
                  name="patient_name"
                  placeholder="Tumhara naam"
                  value={callForm.patient_name}
                  onChange={handleCallChange}
                />
              </div>
            </div>

            <div className="ms-field">
              <label className="ms-label">Appointment Reason</label>
              <textarea
                className="ms-textarea"
                name="reason"
                placeholder="e.g. Sar dard aur bukhar ke liye checkup"
                value={callForm.reason}
                onChange={handleCallChange}
                rows={2}
              />
            </div>

            <div className="ms-appt-form-row">
              <div className="ms-field">
                <label className="ms-label">Condition / Disease</label>
                <input
                  className="ms-input"
                  name="disease"
                  placeholder="e.g. Fever, Back pain"
                  value={callForm.disease}
                  onChange={handleCallChange}
                />
              </div>
              <div className="ms-field">
                <label className="ms-label">Doctor Preference</label>
                <input
                  className="ms-input"
                  name="doctor_name"
                  placeholder="e.g. Dr. Sharma, Any ortho"
                  value={callForm.doctor_name}
                  onChange={handleCallChange}
                />
              </div>
            </div>

            <div className="ms-field">
              <label className="ms-label">Preferred Time Slot</label>
              <input
                className="ms-input"
                name="availability"
                placeholder="e.g. Kal subah 10-12 baje, weekday morning"
                value={callForm.availability}
                onChange={handleCallChange}
              />
            </div>

            {callMsg && !isLive && (
              <div className={`ms-appt-msg ms-appt-msg--${callStatus}`}>
                {callStatus === "success" && <LuCircleCheck size={15} />}
                {callStatus === "error" && <LuTriangleAlert size={15} />}
                &nbsp;{callMsg}
              </div>
            )}

            {callStatus === "success" && callSummary && (
              <div className="ms-appt-call-summary">
                <h3 className="ms-appt-call-summary-title">
                  <LuCircleCheck size={15} /> Call Summary
                </h3>
                <p className="ms-appt-call-summary-text">{callSummary}</p>

                {callTranscript.length > 0 && (
                  <details className="ms-appt-transcript">
                    <summary>Pura conversation dekho</summary>
                    <ul className="ms-appt-transcript-list">
                      {callTranscript.map((line, i) => (
                        <li key={i}>{line}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
            )}

            <div className="ms-appt-confirm-note">
              <LuShieldCheck size={16} />
              <div>
                <p className="ms-appt-confirm-title">We will call, confirm and book.</p>
                <p className="ms-appt-confirm-sub">Your details are secure and only used for booking.</p>
              </div>
            </div>

            <button
              className="ms-btn-primary ms-appt-call-btn"
              onClick={scheduleCall}
              disabled={callStatus === "loading" || !isLoggedIn}
            >
              {callStatus === "loading"
                ? <><LuLoader className="ms-spin" /> Call ho rahi hai...</>
                : <><LuBot size={16} /> Start AI Call &amp; Book Appointment</>
              }
            </button>
          </div>
        </section>
      </div>
    </Layout>
  );
}