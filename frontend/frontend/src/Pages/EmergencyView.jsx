import { API_BASE } from "../config";
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import "./EmergencyView.css";

// Safe helper — same reason as HealthInfo.jsx (backend "detail" kabhi array bhi hota hai)
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

export default function EmergencyView() {
  const { token } = useParams();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    fetchProfile();
  }, [token]);

  const fetchProfile = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(API_BASE + `/health/qr/${token}`);
      const data = await res.json();
      if (!res.ok) {
        setError(extractErrorMessage(data.detail, "Ye QR valid nahi hai ya expire ho gaya hai."));
      } else {
        setProfile(data);
      }
    } catch {
      setError("Backend se connect nahi ho pa raha.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ms-ev-page">
      <div className="ms-ev-card">
        <div className="ms-ev-header">
          <span className="ms-ev-badge">EMERGENCY MEDICAL ID</span>
        </div>

        {loading && (
          <div className="ms-ev-loading">
            <div className="ms-ev-spinner" />
            <p>Profile load ho raha hai...</p>
          </div>
        )}

        {!loading && error && (
          <div className="ms-ev-error">
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && profile && (
          <div className="ms-ev-body">
            <div className="ms-ev-name-row">
              <h1 className="ms-ev-name">{profile.name || "—"}</h1>
              <span className="ms-ev-bloodgroup">{profile.blood_group || "—"}</span>
            </div>

            {profile.critical_conditions && (
              <div className="ms-ev-section ms-ev-critical">
                <span className="ms-ev-label">Critical Conditions</span>
                <p>{profile.critical_conditions}</p>
              </div>
            )}

            {profile.allergies && (
              <div className="ms-ev-section">
                <span className="ms-ev-label">Allergies</span>
                <p>{profile.allergies}</p>
              </div>
            )}

            {profile.medicines && (
              <div className="ms-ev-section">
                <span className="ms-ev-label">Current Medicines</span>
                <p>{profile.medicines}</p>
              </div>
            )}

            {(profile.emergency_contact_name || profile.emergency_contact_phone) && (
              <div className="ms-ev-section ms-ev-contact">
                <span className="ms-ev-label">Emergency Contact</span>
                <p>
                  {profile.emergency_contact_name}
                  {profile.emergency_contact_name && profile.emergency_contact_phone ? " — " : ""}
                  {profile.emergency_contact_phone && (
                    <a href={`tel:${profile.emergency_contact_phone}`}>
                      {profile.emergency_contact_phone}
                    </a>
                  )}
                </p>
              </div>
            )}

            <p className="ms-ev-footer-note">
              Ye info MediSarthi ke emergency QR se li gayi hai — login ke bina dikhayi
              ja rahi hai taaki emergency mein turant kaam aaye.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}