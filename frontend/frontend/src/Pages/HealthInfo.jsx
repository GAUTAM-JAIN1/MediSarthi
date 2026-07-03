import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { QRCodeSVG } from "qrcode.react";
import Layout from "../components/Layout";
import HealthVault from "../components/HealthVault";
import { useUser } from "../hooks/useUser";
import {
  LuX,
  LuHeartPulse,
  LuPill,
  LuFileText,
  LuTriangleAlert,
  LuHistory,
} from "react-icons/lu";
import "./HealthInfo.css";

// Safe helper — FastAPI validation error "detail" kabhi string, kabhi array of
// {type, loc, msg, input} objects hota hai. Ye hamesha ek plain string return
// karta hai taaki JSX mein direct render karne pe kabhi crash na ho.
const extractErrorMessage = (detail, fallback) => {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === "string" ? d : d?.msg || JSON.stringify(d)))
      .join(", ");
  }
  if (typeof detail === "object" && detail.msg) return detail.msg;
  return fallback;
};

const PANEL_META = {
  vitals: { title: "Vitals", icon: LuHeartPulse },
  medications: { title: "Medications", icon: LuPill },
  reports: { title: "Reports", icon: LuFileText },
  allergies: { title: "Allergies", icon: LuTriangleAlert },
  medicalHistory: { title: "Medical History", icon: LuHistory },
};

export default function HealthInfo() {
  const { userId, isLoggedIn } = useUser();

  const [records, setRecords] = useState([]);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [recordsError, setRecordsError] = useState("");

  const [vitalForm, setVitalForm] = useState({
    bp_systolic: "",
    bp_diastolic: "",
    blood_sugar: "",
    weight: "",
    notes: "",
  });
  const [savingVital, setSavingVital] = useState(false);
  const [vitalMsg, setVitalMsg] = useState({ text: "", type: "" });

  // ---- Emergency profile + QR state ----
  const [emergencyForm, setEmergencyForm] = useState({
    name: "",
    blood_group: "",
    allergies: "",
    critical_conditions: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
    medicines: "",
  });
  const [loadingEmergency, setLoadingEmergency] = useState(false);
  const [savingEmergency, setSavingEmergency] = useState(false);
  const [emergencyMsg, setEmergencyMsg] = useState({ text: "", type: "" });
  const [qrToken, setQrToken] = useState("");
  const [generatingQr, setGeneratingQr] = useState(false);
  const [qrMsg, setQrMsg] = useState({ text: "", type: "" });

  // ---- NEW: Lab reports (best-effort — see note in fetchLabReports) ----
  const [labReports, setLabReports] = useState([]);

  // ---- NEW: which vault drawer is open ----
  const [activePanel, setActivePanel] = useState(null);

  useEffect(() => {
    if (!isLoggedIn || !userId) return;
    fetchRecords();
    fetchEmergencyProfile();
    fetchLabReports();
  }, [userId, isLoggedIn]);

  const fetchRecords = async () => {
    setLoadingRecords(true);
    setRecordsError("");
    try {
      const res = await fetch(`http://localhost:8080/health/timeline/${userId}`);
      const data = await res.json();
      if (!res.ok) {
        setRecordsError(extractErrorMessage(data.detail, "Records load nahi ho sake."));
      } else {
        setRecords(data.timeline || []);
      }
    } catch {
      setRecordsError("Backend se connect nahi ho pa raha.");
    } finally {
      setLoadingRecords(false);
    }
  };

  // ⚠️ Backend GET route for saved Lab Report Analyser results isn't confirmed
  // yet in main.py (see PROJECT_CONTEXT.md §1 — the 3 new-agent endpoints are
  // flagged unverified). Trying the most likely path here; fails silently to
  // an empty list if it's wrong, so it never breaks the page. Once you confirm
  // the real route in main.py, just update the URL below.
  const fetchLabReports = async () => {
    try {
      const res = await fetch(`http://localhost:8080/lab-report/history/${userId}`);
      if (res.ok) {
        const data = await res.json();
        setLabReports(data.reports || data.analyses || []);
      }
    } catch {
      // silently ignore — Reports drawer just shows an empty state
    }
  };

  const saveVital = async () => {
    if (!isLoggedIn) {
      setVitalMsg({ text: "Pehle login karo.", type: "error" });
      return;
    }
    const hasValue =
      vitalForm.bp_systolic || vitalForm.blood_sugar || vitalForm.weight;
    if (!hasValue) {
      setVitalMsg({ text: "Koi toh value daalo.", type: "error" });
      return;
    }
    setSavingVital(true);
    setVitalMsg({ text: "", type: "" });

    try {
      const payload = {
        user_id: userId,
        vital_type: "general",
        value: parseFloat(vitalForm.weight || vitalForm.blood_sugar || vitalForm.bp_systolic),
        unit: vitalForm.weight ? "kg" : vitalForm.blood_sugar ? "mg/dL" : "mmHg",
        notes: vitalForm.notes || "",
        bp_systolic: vitalForm.bp_systolic ? parseFloat(vitalForm.bp_systolic) : null,
        bp_diastolic: vitalForm.bp_diastolic ? parseFloat(vitalForm.bp_diastolic) : null,
        blood_sugar: vitalForm.blood_sugar ? parseFloat(vitalForm.blood_sugar) : null,
        weight: vitalForm.weight ? parseFloat(vitalForm.weight) : null,
      };

      const res = await fetch("http://localhost:8080/health/vital", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setVitalMsg({ text: extractErrorMessage(data.detail, "Save nahi hua."), type: "error" });
      } else {
        setVitalMsg({ text: "Vital save ho gaya!", type: "success" });
        setVitalForm({ bp_systolic: "", bp_diastolic: "", blood_sugar: "", weight: "", notes: "" });
        fetchRecords();
      }
    } catch {
      setVitalMsg({ text: "Backend se connect nahi ho pa raha.", type: "error" });
    } finally {
      setSavingVital(false);
    }
  };

  // ---- Emergency profile handlers ----

  const fetchEmergencyProfile = async () => {
    setLoadingEmergency(true);
    try {
      const res = await fetch(`http://localhost:8080/health/emergency-profile/${userId}`);
      const data = await res.json();
      if (res.ok && data) {
        setEmergencyForm({
          name: data.name || "",
          blood_group: data.blood_group || "",
          allergies: data.allergies || "",
          critical_conditions: data.critical_conditions || "",
          emergency_contact_name: data.emergency_contact_name || "",
          emergency_contact_phone: data.emergency_contact_phone || "",
          medicines: data.medicines || "",
        });
        if (data.qr_token) {
          setQrToken(data.qr_token);
        }
      }
      // agar profile abhi tak nahi bana (404), ye normal hai — form empty rahega
    } catch {
      // silently ignore — pehli baar profile na hona koi error nahi hai
    } finally {
      setLoadingEmergency(false);
    }
  };

  const saveEmergencyProfile = async () => {
    if (!isLoggedIn) {
      setEmergencyMsg({ text: "Pehle login karo.", type: "error" });
      return;
    }
    if (!emergencyForm.name || !emergencyForm.blood_group) {
      setEmergencyMsg({ text: "Naam aur blood group zaroori hai.", type: "error" });
      return;
    }
    setSavingEmergency(true);
    setEmergencyMsg({ text: "", type: "" });

    try {
      const payload = {
        user_id: userId,
        name: emergencyForm.name,
        blood_group: emergencyForm.blood_group,
        allergies: emergencyForm.allergies,
        critical_conditions: emergencyForm.critical_conditions,
        emergency_contact_name: emergencyForm.emergency_contact_name,
        emergency_contact_phone: emergencyForm.emergency_contact_phone,
        medicines: emergencyForm.medicines,
      };

      const res = await fetch("http://localhost:8080/health/emergency-profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setEmergencyMsg({ text: extractErrorMessage(data.detail, "Save nahi hua."), type: "error" });
      } else {
        setEmergencyMsg({ text: "Emergency profile save ho gaya!", type: "success" });
      }
    } catch {
      setEmergencyMsg({ text: "Backend se connect nahi ho pa raha.", type: "error" });
    } finally {
      setSavingEmergency(false);
    }
  };

  const generateQr = async () => {
    if (!isLoggedIn) return;
    setGeneratingQr(true);
    setQrMsg({ text: "", type: "" });
    try {
      const res = await fetch(`http://localhost:8080/health/generate-qr/${userId}`, {
        method: "POST",
      });
      const data = await res.json();
      if (!res.ok) {
        setQrMsg({ text: extractErrorMessage(data.detail, "QR generate nahi hua."), type: "error" });
      } else {
        setQrToken(data.token || data.qr_token || "");
        setQrMsg({ text: "QR ban gaya! Print ya screenshot le sakte ho.", type: "success" });
      }
    } catch {
      setQrMsg({ text: "Backend se connect nahi ho pa raha.", type: "error" });
    } finally {
      setGeneratingQr(false);
    }
  };

  const emergencyUrl = qrToken
    ? `${window.location.origin}/emergency/${qrToken}`
    : "";

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  };

  const typeLabel = (type) => {
    if (type === "vital") return { label: "Vitals", color: "green" };
    if (type === "prescription") return { label: "Prescription", color: "gold" };
    if (type === "symptom") return { label: "Symptom", color: "gold" };
    return { label: type, color: "gold" };
  };

  // ---- Derived data for the vault drawers ----
  const vitalRecords = records
    .filter((r) => r.type === "vital")
    .sort((a, b) => new Date(b.date) - new Date(a.date));
  const prescriptionRecords = records
    .filter((r) => r.type === "prescription")
    .sort((a, b) => new Date(b.date) - new Date(a.date));
  const latestVitals = vitalRecords[0]?.data || {};

  const allergyList = emergencyForm.allergies
    ? emergencyForm.allergies.split(",").map((s) => s.trim()).filter(Boolean)
    : [];
  const conditionList = emergencyForm.critical_conditions
    ? emergencyForm.critical_conditions.split(",").map((s) => s.trim()).filter(Boolean)
    : [];

  const counts = {
    vitals: vitalRecords.length,
    medications: prescriptionRecords.length,
    reports: labReports.length,
    allergies: allergyList.length,
    medicalHistory: records.length,
  };

  const closePanel = () => setActivePanel(null);
  const PanelIcon = activePanel ? PANEL_META[activePanel].icon : null;

  return (
    <Layout>
      <div className="ms-health-page">
        <div className="ms-page-header">
          <h1 className="ms-page-title">Health Records</h1>
          <p className="ms-page-subtitle">
            Apna health vault kholo — vitals, medications, reports, sab ek jagah.
          </p>
        </div>

        {!isLoggedIn ? (
          <div className="ms-health-login-notice">
            Health records dekhne ke liye <a href="/auth">login karo</a>.
          </div>
        ) : (
          <>
            <div className="ms-health-hero">
              <HealthVault counts={counts} activeKey={activePanel} onOpen={setActivePanel} />

              {/* Emergency Medical ID + QR — always visible, critical for physical scanning */}
              <div className="ms-card ms-health-emergency-card">
                <h2 className="ms-health-section-title">Emergency Medical ID</h2>
                <p className="ms-page-subtitle" style={{ marginBottom: "1rem" }}>
                  Ye info QR scan karne par bina login dikhegi.
                </p>

                {loadingEmergency ? (
                  <div className="ms-health-loading">
                    <div className="ms-spinner" />
                    <p>Profile load ho raha hai...</p>
                  </div>
                ) : (
                  <>
                    <div className="ms-health-qr-box">
                      {qrToken ? (
                        <div className="ms-health-qr-render">
                          <QRCodeSVG value={emergencyUrl} size={168} />
                        </div>
                      ) : (
                        <div className="ms-empty-state" style={{ padding: "1.5rem" }}>
                          <p>Abhi QR generate nahi hua.</p>
                        </div>
                      )}
                    </div>

                    <div className="ms-health-quick-info">
                      <div>
                        <span className="ms-label">Blood Group</span>
                        <p className="ms-health-quick-value">{emergencyForm.blood_group || "-"}</p>
                      </div>
                      <div>
                        <span className="ms-label">Emergency Contact</span>
                        <p className="ms-health-quick-value">
                          {emergencyForm.emergency_contact_name || "-"}
                          {emergencyForm.emergency_contact_phone && (
                            <span className="ms-health-quick-phone">
                              📞 {emergencyForm.emergency_contact_phone}
                            </span>
                          )}
                        </p>
                      </div>
                    </div>

                    {qrMsg.text && (
                      <p className={`ms-health-msg ms-health-msg--${qrMsg.type}`}>{qrMsg.text}</p>
                    )}

                    <button className="ms-btn-secondary" onClick={generateQr} disabled={generatingQr} style={{ width: "100%" }}>
                      {generatingQr ? "Generate ho raha hai..." : qrToken ? "QR Re-generate karo" : "QR Generate karo"}
                    </button>

                    <details className="ms-health-edit-details">
                      <summary>Emergency profile edit karo</summary>
                      <div className="ms-health-form" style={{ marginTop: "0.9rem" }}>
                        <div className="ms-health-form-row">
                          <div className="ms-field">
                            <label className="ms-label">Naam</label>
                            <input
                              className="ms-input"
                              placeholder="Apna naam"
                              value={emergencyForm.name}
                              onChange={(e) => setEmergencyForm({ ...emergencyForm, name: e.target.value })}
                            />
                          </div>
                          <div className="ms-field">
                            <label className="ms-label">Blood Group</label>
                            <input
                              className="ms-input"
                              placeholder="O+"
                              value={emergencyForm.blood_group}
                              onChange={(e) => setEmergencyForm({ ...emergencyForm, blood_group: e.target.value })}
                            />
                          </div>
                        </div>

                        <div className="ms-field">
                          <label className="ms-label">Allergies (comma se separate karo)</label>
                          <input
                            className="ms-input"
                            placeholder="Penicillin, Peanuts"
                            value={emergencyForm.allergies}
                            onChange={(e) => setEmergencyForm({ ...emergencyForm, allergies: e.target.value })}
                          />
                        </div>

                        <div className="ms-field">
                          <label className="ms-label">Critical Conditions (agar ho)</label>
                          <input
                            className="ms-input"
                            placeholder="Diabetes, Asthma"
                            value={emergencyForm.critical_conditions}
                            onChange={(e) => setEmergencyForm({ ...emergencyForm, critical_conditions: e.target.value })}
                          />
                        </div>

                        <div className="ms-field">
                          <label className="ms-label">Current Medicines</label>
                          <input
                            className="ms-input"
                            placeholder="Metformin 500mg"
                            value={emergencyForm.medicines}
                            onChange={(e) => setEmergencyForm({ ...emergencyForm, medicines: e.target.value })}
                          />
                        </div>

                        <div className="ms-health-form-row">
                          <div className="ms-field">
                            <label className="ms-label">Emergency Contact Naam</label>
                            <input
                              className="ms-input"
                              placeholder="Papa / Mama / Spouse"
                              value={emergencyForm.emergency_contact_name}
                              onChange={(e) =>
                                setEmergencyForm({ ...emergencyForm, emergency_contact_name: e.target.value })
                              }
                            />
                          </div>
                          <div className="ms-field">
                            <label className="ms-label">Emergency Contact Phone</label>
                            <input
                              className="ms-input"
                              placeholder="9876543210"
                              value={emergencyForm.emergency_contact_phone}
                              onChange={(e) =>
                                setEmergencyForm({ ...emergencyForm, emergency_contact_phone: e.target.value })
                              }
                            />
                          </div>
                        </div>

                        {emergencyMsg.text && (
                          <p className={`ms-health-msg ms-health-msg--${emergencyMsg.type}`}>{emergencyMsg.text}</p>
                        )}

                        <button className="ms-btn-primary" onClick={saveEmergencyProfile} disabled={savingEmergency}>
                          {savingEmergency ? "Save ho raha hai..." : "Save Emergency Profile"}
                        </button>
                      </div>
                    </details>
                  </>
                )}
              </div>
            </div>

            {/* ── Vault drawer panel ── */}
            <AnimatePresence>
              {activePanel && (
                <>
                  <motion.div
                    className="ms-drawer-backdrop"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={closePanel}
                  />
                  <motion.div
                    className="ms-drawer-panel"
                    initial={{ x: "100%" }}
                    animate={{ x: 0 }}
                    exit={{ x: "100%" }}
                    transition={{ type: "spring", stiffness: 320, damping: 34 }}
                  >
                    <div className="ms-drawer-header">
                      <h2>
                        {PanelIcon && <PanelIcon size={20} />}
                        {PANEL_META[activePanel].title}
                      </h2>
                      <button className="ms-drawer-close" onClick={closePanel}>
                        <LuX size={20} />
                      </button>
                    </div>

                    <div className="ms-drawer-body">
                      {/* ── VITALS ── */}
                      {activePanel === "vitals" && (
                        <>
                          <div className="ms-vitals-row">
                            <div className="ms-vital-chip">
                              <span className="ms-vital-label">Blood Pressure</span>
                              <span className="ms-vital-value">
                                {latestVitals.bp_systolic && latestVitals.bp_diastolic
                                  ? `${latestVitals.bp_systolic}/${latestVitals.bp_diastolic}`
                                  : "-"}
                              </span>
                              <span className="ms-vital-unit">mmHg</span>
                            </div>
                            <div className="ms-vital-chip">
                              <span className="ms-vital-label">Blood Sugar</span>
                              <span className="ms-vital-value">{latestVitals.blood_sugar || "-"}</span>
                              <span className="ms-vital-unit">mg/dL</span>
                            </div>
                            <div className="ms-vital-chip">
                              <span className="ms-vital-label">Weight</span>
                              <span className="ms-vital-value">{latestVitals.weight || "-"}</span>
                              <span className="ms-vital-unit">kg</span>
                            </div>
                          </div>

                          <div className="ms-card">
                            <h3 className="ms-health-section-title">Add Vital</h3>
                            <div className="ms-health-form">
                              <div className="ms-health-form-row">
                                <div className="ms-field">
                                  <label className="ms-label">BP Systolic</label>
                                  <input
                                    className="ms-input"
                                    placeholder="120"
                                    value={vitalForm.bp_systolic}
                                    onChange={(e) => setVitalForm({ ...vitalForm, bp_systolic: e.target.value })}
                                  />
                                </div>
                                <div className="ms-field">
                                  <label className="ms-label">BP Diastolic</label>
                                  <input
                                    className="ms-input"
                                    placeholder="80"
                                    value={vitalForm.bp_diastolic}
                                    onChange={(e) => setVitalForm({ ...vitalForm, bp_diastolic: e.target.value })}
                                  />
                                </div>
                              </div>
                              <div className="ms-health-form-row">
                                <div className="ms-field">
                                  <label className="ms-label">Blood Sugar (mg/dL)</label>
                                  <input
                                    className="ms-input"
                                    placeholder="90"
                                    value={vitalForm.blood_sugar}
                                    onChange={(e) => setVitalForm({ ...vitalForm, blood_sugar: e.target.value })}
                                  />
                                </div>
                                <div className="ms-field">
                                  <label className="ms-label">Weight (kg)</label>
                                  <input
                                    className="ms-input"
                                    placeholder="65"
                                    value={vitalForm.weight}
                                    onChange={(e) => setVitalForm({ ...vitalForm, weight: e.target.value })}
                                  />
                                </div>
                              </div>
                              <div className="ms-field">
                                <label className="ms-label">Notes (optional)</label>
                                <textarea
                                  className="ms-textarea"
                                  placeholder="Kuch aur note karna ho toh..."
                                  rows={2}
                                  value={vitalForm.notes}
                                  onChange={(e) => setVitalForm({ ...vitalForm, notes: e.target.value })}
                                />
                              </div>

                              {vitalMsg.text && (
                                <p className={`ms-health-msg ms-health-msg--${vitalMsg.type}`}>{vitalMsg.text}</p>
                              )}

                              <button className="ms-btn-primary" onClick={saveVital} disabled={savingVital}>
                                {savingVital ? "Save ho raha hai..." : "Save Vital"}
                              </button>
                            </div>
                          </div>

                          {loadingRecords && (
                            <div className="ms-health-loading">
                              <div className="ms-spinner" />
                              <p>Records load ho rahe hain...</p>
                            </div>
                          )}
                          {recordsError && !loadingRecords && <p className="ms-health-error">{recordsError}</p>}

                          {!loadingRecords && vitalRecords.length === 0 ? (
                            <div className="ms-empty-state">
                              <div className="ms-empty-state-icon">📂</div>
                              <p>Abhi koi vital record nahi hai.</p>
                            </div>
                          ) : (
                            vitalRecords.map((r, i) => (
                              <div key={r._id || i} className="ms-drawer-list-item">
                                <div className="ms-timeline-top">
                                  <span className="ms-badge ms-badge--green">Vitals</span>
                                  <span className="ms-timeline-date">{formatDate(r.date)}</span>
                                </div>
                                <div className="ms-timeline-vitals">
                                  {r.data?.bp_systolic && <span>BP: {r.data.bp_systolic}/{r.data.bp_diastolic} mmHg</span>}
                                  {r.data?.blood_sugar && <span>Sugar: {r.data.blood_sugar} mg/dL</span>}
                                  {r.data?.weight && <span>Weight: {r.data.weight} kg</span>}
                                </div>
                                {r.data?.notes && <p className="ms-timeline-notes">📝 {r.data.notes}</p>}
                              </div>
                            ))
                          )}
                        </>
                      )}

                      {/* ── MEDICATIONS ── */}
                      {activePanel === "medications" && (
                        <>
                          {prescriptionRecords.length === 0 ? (
                            <div className="ms-empty-state">
                              <div className="ms-empty-state-icon">💊</div>
                              <p>Abhi koi prescription record nahi hai.</p>
                              <p style={{ fontSize: "0.85rem", marginTop: "0.5rem" }}>
                                <a href="/find-medicine">Find Medicine</a> page se prescription upload karke try karo.
                              </p>
                            </div>
                          ) : (
                            prescriptionRecords.map((r, i) => (
                              <div key={r._id || i} className="ms-drawer-list-item">
                                <div className="ms-timeline-top">
                                  <span className="ms-badge ms-badge--gold">Prescription</span>
                                  <span className="ms-timeline-date">{formatDate(r.date)}</span>
                                </div>
                                {r.data?.summary && <p className="ms-timeline-summary">{r.data.summary}</p>}
                                {r.data?.notes && <p className="ms-timeline-notes">📝 {r.data.notes}</p>}
                              </div>
                            ))
                          )}
                        </>
                      )}

                      {/* ── REPORTS ── */}
                      {activePanel === "reports" && (
                        <>
                          {labReports.length === 0 ? (
                            <div className="ms-empty-state">
                              <div className="ms-empty-state-icon">📄</div>
                              <p>Abhi koi lab report analysis save nahi hai.</p>
                              <p style={{ fontSize: "0.85rem", marginTop: "0.5rem" }}>
                                <a href="/lab-report">Lab Report</a> page se ek report analyze karo.
                              </p>
                            </div>
                          ) : (
                            labReports.map((r, i) => (
                              <div key={r._id || i} className="ms-drawer-list-item">
                                <div className="ms-timeline-top">
                                  <span className="ms-badge ms-badge--gold">Report</span>
                                  <span className="ms-timeline-date">{formatDate(r.date)}</span>
                                </div>
                                {r.summary && <p className="ms-timeline-summary">{r.summary}</p>}
                              </div>
                            ))
                          )}
                        </>
                      )}

                      {/* ── ALLERGIES ── */}
                      {activePanel === "allergies" && (
                        <>
                          {allergyList.length === 0 ? (
                            <div className="ms-empty-state">
                              <div className="ms-empty-state-icon">⚠️</div>
                              <p>Koi allergy record nahi hai.</p>
                              <p style={{ fontSize: "0.85rem", marginTop: "0.5rem" }}>
                                Emergency ID card mein "Emergency profile edit karo" se add kar sakte ho.
                              </p>
                            </div>
                          ) : (
                            <div className="ms-chip-row">
                              {allergyList.map((a, i) => (
                                <span key={i} className="ms-chip">{a}</span>
                              ))}
                            </div>
                          )}
                        </>
                      )}

                      {/* ── MEDICAL HISTORY (full timeline) ── */}
                      {activePanel === "medicalHistory" && (
                        <>
                          {conditionList.length > 0 && (
                            <div>
                              <h3 className="ms-health-section-title" style={{ fontSize: "1rem" }}>
                                Critical Conditions
                              </h3>
                              <div className="ms-chip-row">
                                {conditionList.map((c, i) => (
                                  <span key={i} className="ms-chip">{c}</span>
                                ))}
                              </div>
                            </div>
                          )}

                          {loadingRecords && (
                            <div className="ms-health-loading">
                              <div className="ms-spinner" />
                              <p>Records load ho rahe hain...</p>
                            </div>
                          )}
                          {recordsError && !loadingRecords && <p className="ms-health-error">{recordsError}</p>}

                          {!loadingRecords && records.length === 0 && !recordsError && (
                            <div className="ms-empty-state">
                              <div className="ms-empty-state-icon">📂</div>
                              <p>Abhi koi record nahi hai.</p>
                            </div>
                          )}

                          {records.length > 0 && (
                            <div className="ms-timeline-list">
                              {[...records]
                                .sort((a, b) => new Date(b.date) - new Date(a.date))
                                .map((r, i) => {
                                  const { label, color } = typeLabel(r.type);
                                  return (
                                    <div key={r._id || i} className="ms-timeline-item">
                                      <div className="ms-timeline-dot" />
                                      <div className="ms-timeline-content">
                                        <div className="ms-timeline-top">
                                          <span className={`ms-badge ms-badge--${color}`}>{label}</span>
                                          <span className="ms-timeline-date">{formatDate(r.date)}</span>
                                        </div>
                                        {r.type === "vital" && r.data && (
                                          <div className="ms-timeline-vitals">
                                            {r.data.bp_systolic && <span>BP: {r.data.bp_systolic}/{r.data.bp_diastolic} mmHg</span>}
                                            {r.data.blood_sugar && <span>Sugar: {r.data.blood_sugar} mg/dL</span>}
                                            {r.data.weight && <span>Weight: {r.data.weight} kg</span>}
                                          </div>
                                        )}
                                        {r.type !== "vital" && r.data?.summary && (
                                          <p className="ms-timeline-summary">{r.data.summary}</p>
                                        )}
                                        {r.data?.notes && <p className="ms-timeline-notes">📝 {r.data.notes}</p>}
                                      </div>
                                    </div>
                                  );
                                })}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </>
        )}
      </div>
    </Layout>
  );
}