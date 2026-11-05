import { API_BASE } from "../config";
// ============================================================================
// NEW FILE: frontend/frontend/src/pages/DoctorVisitView.jsx
// Modeled directly on EmergencyView.jsx (same "public, no Layout, no auth"
// pattern) — but renders the Doctor Visit QR snapshot instead of the
// permanent Emergency profile. Uses the same extractErrorMessage() helper
// since the backend's `detail` field has the same string-or-array shape
// everywhere in this app.
// ============================================================================

import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import "./DoctorVisitView.css";

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

export default function DoctorVisitView() {
  const { token } = useParams();

  const [snapshot, setSnapshot] = useState(null);
  const [generatedAt, setGeneratedAt] = useState(null);
  const [expiresAt, setExpiresAt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    fetchSnapshot();
  }, [token]);

  const fetchSnapshot = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(API_BASE + `/health/doctor-qr/${token}`);
      const data = await res.json();
      if (!res.ok) {
        setError(extractErrorMessage(data.detail, "Ye QR invalid hai ya expire ho gaya hai."));
      } else {
        setSnapshot(data.snapshot || {});
        setGeneratedAt(data.generated_at);
        setExpiresAt(data.expires_at);
      }
    } catch {
      setError("Backend se connect nahi ho pa raha.");
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleString("en-IN", {
      day: "numeric", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  };

  const clinicalSummary = snapshot?.clinical_summary || {};
  const labReports = snapshot?.lab_reports || [];
  const trends = snapshot?.trends || [];
  const prescriptions = snapshot?.prescriptions || [];

  return (
    <div className="ms-dv-page">
      <div className="ms-dv-card">
        <div className="ms-dv-header">
          <span className="ms-dv-badge">DOCTOR VISIT SUMMARY</span>
          {expiresAt && (
            <span className="ms-dv-expiry">Valid until {formatDateTime(expiresAt)}</span>
          )}
        </div>

        {loading && (
          <div className="ms-dv-loading">
            <div className="ms-dv-spinner" />
            <p>Summary load ho raha hai...</p>
          </div>
        )}

        {!loading && error && (
          <div className="ms-dv-error">
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && snapshot && (
          <div className="ms-dv-body">
            {/* ── Clinical summary block ── */}
            <section className="ms-dv-section ms-dv-summary-section">
              <span className="ms-dv-label">Clinical Summary</span>
              <p className="ms-dv-summary-text">
                {clinicalSummary.clinical_summary || "No summary available."}
              </p>

              {clinicalSummary.key_flags && clinicalSummary.key_flags.length > 0 && (
                <div className="ms-dv-flags">
                  {clinicalSummary.key_flags.map((f, i) => (
                    <span key={i} className="ms-dv-flag-chip">{f}</span>
                  ))}
                </div>
              )}

              {clinicalSummary.active_medicines_note && (
                <p className="ms-dv-meds-note">{clinicalSummary.active_medicines_note}</p>
              )}
            </section>

            {/* ── Lab history ── */}
            <section className="ms-dv-section">
              <span className="ms-dv-label">Saved Lab Reports ({labReports.length})</span>
              {labReports.length === 0 ? (
                <p className="ms-dv-empty-line">No saved lab reports.</p>
              ) : (
                <div className="ms-dv-list">
                  {labReports.map((r, i) => (
                    <div key={r._id || i} className="ms-dv-list-item">
                      <div className="ms-dv-list-item-top">
                        <span className="ms-dv-report-type">{r.report_type || "Unknown"}</span>
                        <span className="ms-dv-date">{(r.date || "").slice(0, 10)}</span>
                      </div>
                      <div className="ms-dv-test-row">
                        {(r.tests || []).map((t, ti) => (
                          <span
                            key={ti}
                            className={`ms-dv-test-chip ${
                              t.status && t.status !== "Normal" ? "ms-dv-test-chip--flag" : ""
                            }`}
                          >
                            {t.test_name}: {t.value}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* ── Trends ── */}
            <section className="ms-dv-section">
              <span className="ms-dv-label">Trends ({trends.length})</span>
              {trends.length === 0 ? (
                <p className="ms-dv-empty-line">No test has 2+ saved data points yet.</p>
              ) : (
                <div className="ms-dv-list">
                  {trends.map((tr, i) => (
                    <div key={i} className="ms-dv-list-item">
                      <div className="ms-dv-list-item-top">
                        <span className="ms-dv-report-type">{tr.test_name}</span>
                        <span className={`ms-dv-trend-dir ms-dv-trend-dir--${tr.trend_direction || "stable"}`}>
                          {tr.trend_direction === "up" ? "↑" : tr.trend_direction === "down" ? "↓" : "→"}
                        </span>
                      </div>
                      <p className="ms-dv-trend-points">
                        {(tr.points || [])
                          .map((p) => `${(p.date || "").slice(0, 10)}: ${p.value}`)
                          .join("  →  ")}
                      </p>
                      {(tr.annotations || []).length > 0 && (
                        <p className="ms-dv-trend-annotation">
                          {tr.annotations
                            .map((a) => `${a.medicine_name} since ${(a.start_date || "").slice(0, 10)}`)
                            .join(", ")}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* ── Prescriptions ── */}
            <section className="ms-dv-section">
              <span className="ms-dv-label">Saved Prescriptions ({prescriptions.length})</span>
              {prescriptions.length === 0 ? (
                <p className="ms-dv-empty-line">No saved prescriptions.</p>
              ) : (
                <div className="ms-dv-list">
                  {prescriptions.map((rx, i) => (
                    <div key={rx._id || i} className="ms-dv-list-item">
                      <div className="ms-dv-list-item-top">
                        <span className="ms-dv-report-type">
                          {(rx.medicines || []).join(", ") || "—"}
                        </span>
                        <span className="ms-dv-date">{(rx.date || "").slice(0, 10)}</span>
                      </div>
                      {rx.doctor_notes && <p className="ms-dv-rx-notes">{rx.doctor_notes}</p>}
                    </div>
                  ))}
                </div>
              )}
            </section>

            <p className="ms-dv-disclaimer">
              {clinicalSummary.disclaimer ||
                "This summary is generated from the patient's own saved app data and does not replace your own clinical judgment."}
            </p>

            {generatedAt && (
              <p className="ms-dv-generated-note">Generated {formatDateTime(generatedAt)}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}