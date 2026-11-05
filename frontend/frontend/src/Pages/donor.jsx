import { API_BASE } from "../config";
import { useState, useEffect, useRef } from "react";
import Layout from "../components/Layout";
import { useUser } from "../hooks/useUser";
import {
  LuHeartHandshake,
  LuDroplet,
  LuMapPin,
  LuPhone,
  LuSearch,
  LuPower,
  LuUser,
  LuBell,
  LuArrowRight,
  LuHeart,
} from "react-icons/lu";
import "./donor.css";

const BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

const COMPATIBILITY = {
  "O-":  { canDonateTo: ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"], canReceiveFrom: ["O-"] },
  "O+":  { canDonateTo: ["O+", "A+", "B+", "AB+"], canReceiveFrom: ["O-", "O+"] },
  "A-":  { canDonateTo: ["A-", "A+", "AB-", "AB+"], canReceiveFrom: ["O-", "A-"] },
  "A+":  { canDonateTo: ["A+", "AB+"], canReceiveFrom: ["O-", "O+", "A-", "A+"] },
  "B-":  { canDonateTo: ["B-", "B+", "AB-", "AB+"], canReceiveFrom: ["O-", "B-"] },
  "B+":  { canDonateTo: ["B+", "AB+"], canReceiveFrom: ["O-", "O+", "B-", "B+"] },
  "AB-": { canDonateTo: ["AB-", "AB+"], canReceiveFrom: ["O-", "A-", "B-", "AB-"] },
  "AB+": { canDonateTo: ["AB+"], canReceiveFrom: ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"] },
};

const ORBIT_ANGLES = [0, 60, 120, 180, 240, 300];

export default function Donor() {
  // AUTH (D34): switched from a manual `localStorage.getItem("ms_user_id")`
  // useEffect to the shared useUser() hook — same userId value either way,
  // but this also gives us `authFetch`, which every protected donor
  // endpoint below now needs (register/profile/availability/donation/
  // find-donors/create-request all require a valid token on the backend
  // now). isLoggedIn from the hook already accounts for "token present too",
  // not just userId, so it's a slightly stricter (more correct) check than
  // the old plain userId-truthy checks below.
  const { userId, isLoggedIn, authFetch } = useUser();

  const [donor, setDonor] = useState(null);
  const [checkingProfile, setCheckingProfile] = useState(true);

  const [form, setForm] = useState({
    name: "",
    blood_group: "",
    city: "",
    state: "",
    phone: "",
  });
  const [registering, setRegistering] = useState(false);
  const [registerError, setRegisterError] = useState("");

  const [findForm, setFindForm] = useState({ blood_group: "", city: "", state: "" });
  const [foundDonors, setFoundDonors] = useState(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");

  const [requestMessage, setRequestMessage] = useState("");
  const [requestStatus, setRequestStatus] = useState("");

  const [toggling, setToggling] = useState(false);
  const [recording, setRecording] = useState(false);

  const [selectedGroup, setSelectedGroup] = useState("O+");
  const registerSectionRef = useRef(null);
  const findSectionRef = useRef(null);

  useEffect(() => {
    if (isLoggedIn && userId) {
      fetchDonorProfile(userId);
    } else {
      setCheckingProfile(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, isLoggedIn]);

  async function fetchDonorProfile(id) {
    setCheckingProfile(true);
    try {
      const res = await authFetch(`${API_BASE}/donor/${id}`);
      if (res.ok) {
        const data = await res.json();
        setDonor(data.donor);
      } else {
        setDonor(null);
      }
    } catch (err) {
      setDonor(null);
    } finally {
      setCheckingProfile(false);
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    setRegisterError("");

    if (!isLoggedIn) {
      setRegisterError("Pehle login karo donor banne ke liye.");
      return;
    }
    if (!form.name || !form.blood_group || !form.city || !form.state || !form.phone) {
      setRegisterError("Saari fields bharo.");
      return;
    }

    setRegistering(true);
    try {
      const res = await authFetch(`${API_BASE}/donor/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          name: form.name,
          blood_group: form.blood_group,
          city: form.city,
          state: form.state,
          phone: form.phone,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Registration fail ho gaya.");
      }
      setDonor(data.donor);
    } catch (err) {
      setRegisterError(err.message || "Kuch gadbad ho gayi.");
    } finally {
      setRegistering(false);
    }
  }

  async function handleToggleAvailability() {
    if (!donor) return;
    setToggling(true);
    try {
      const nextAvailable = !donor.available;
      const res = await authFetch(
        `${API_BASE}/donor/${userId}/availability?available=${nextAvailable}`,
        { method: "POST" }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Status change nahi hua.");
      setDonor(data.donor);
    } catch (err) {
      setRegisterError(err.message || "Status change nahi hua.");
    } finally {
      setToggling(false);
    }
  }

  async function handleRecordDonation() {
    if (!donor) return;
    setRecording(true);
    try {
      const res = await authFetch(`${API_BASE}/donor/${userId}/record-donation`, {
        method: "POST",
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Donation record nahi hui.");
      setDonor(data.donor);
    } catch (err) {
      setRegisterError(err.message || "Donation record nahi hui.");
    } finally {
      setRecording(false);
    }
  }

  async function handleFindDonors(e) {
    if (e) e.preventDefault();
    setSearchError("");
    setFoundDonors(null);

    if (!findForm.blood_group || !findForm.city || !findForm.state) {
      setSearchError("Blood group, city aur state bharo.");
      return;
    }
    if (!isLoggedIn) {
      setSearchError("Pehle login karo.");
      return;
    }

    setSearching(true);
    try {
      const res = await authFetch(`${API_BASE}/donor/request/find-donors`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(findForm),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Search fail ho gaya.");
      setFoundDonors(data.donors || []);
    } catch (err) {
      setSearchError(err.message || "Kuch gadbad ho gayi.");
    } finally {
      setSearching(false);
    }
  }

  async function handleCreateRequest() {
    if (!isLoggedIn) {
      setRequestStatus("Pehle login karo request banane ke liye.");
      return;
    }
    if (!findForm.blood_group || !findForm.city || !findForm.state) {
      setRequestStatus("Pehle blood group, city, state bharo.");
      return;
    }
    setRequestStatus("Bhej rahe hain...");
    try {
      const res = await authFetch(`${API_BASE}/donor/request/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requester_user_id: userId,
          blood_group: findForm.blood_group,
          city: findForm.city,
          state: findForm.state,
          message: requestMessage,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Request fail ho gayi.");
      setRequestStatus("Request bhej di gayi! Nearby donors ko notify kar diya jayega.");
    } catch (err) {
      setRequestStatus(err.message || "Kuch gadbad ho gayi.");
    }
  }

  const scrollToRegister = () => {
    registerSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const scrollToFind = (prefillGroup) => {
    if (prefillGroup) {
      setFindForm((f) => ({ ...f, blood_group: prefillGroup }));
    }
    findSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const matchCount =
    foundDonors === null ? null : foundDonors.filter((d) => d.available !== false).length;

  const compat = COMPATIBILITY[selectedGroup];

  return (
    <Layout>
      <div className="donor-page">
        <section className="donor-hero">
          <div className="donor-hero-left">
            <h1 className="donor-hero-title">
              Be the reason<br />someone <span className="donor-hero-accent">lives.</span>
            </h1>
            <p className="donor-hero-subtitle">
              Your donation can bring hope in someone's darkest hour.
            </p>

            <div className="donor-hero-fact">
              <span className="donor-hero-fact-icon">
                <LuHeart size={20} />
              </span>
              <div>
                <strong>One donation can save up to 3 lives.</strong>
                <span>Register once, help for years to come.</span>
              </div>
            </div>

            {matchCount !== null && (
              <div className="donor-hero-livebadge">
                <span className="donor-live-dot" />
                {matchCount} donor{matchCount === 1 ? "" : "s"} matched your last search
              </div>
            )}
          </div>

          <div className="donor-hero-orbit-zone">
            <div className="donor-orbit-rings" aria-hidden="true">
              <span className="donor-ring donor-ring--1" />
              <span className="donor-ring donor-ring--2" />
            </div>

            <div className="donor-orbit-center">
              <svg viewBox="0 0 100 100" className="donor-drop-svg" aria-hidden="true">
                <defs>
                  <radialGradient id="dropGrad" cx="35%" cy="30%" r="80%">
                    <stop offset="0%" stopColor="#FF8A7A" />
                    <stop offset="55%" stopColor="#E23B3B" />
                    <stop offset="100%" stopColor="#8C1414" />
                  </radialGradient>
                </defs>
                <path
                  d="M50 8 C 66 34, 82 52, 82 68 A 32 32 0 1 1 18 68 C 18 52, 34 34, 50 8 Z"
                  fill="url(#dropGrad)"
                />
                <path
                  d="M50 22 L44 70a10 10 0 0012 0z"
                  fill="#ffffff"
                  opacity="0.18"
                />
              </svg>
              <LuHeart className="donor-drop-heart" size={26} aria-hidden="true" />
            </div>

            <div className="donor-orbit-ring-anim" aria-hidden="true">
              {ORBIT_ANGLES.map((angle, i) => (
                <div
                  key={angle}
                  className="donor-orbit-dot"
                  style={{ transform: `rotate(${angle}deg) translate(150px) rotate(${-angle}deg)` }}
                >
                  <div className="donor-orbit-avatar-inner">
                    <div className="donor-orbit-avatar">
                      <LuUser size={20} />
                      <span className={`donor-online-dot${i % 3 === 0 ? " is-off" : ""}`} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="donor-hero-right">
            <div className="donor-emergency-card">
              <div className="donor-emergency-header">
                <h3>Emergency Need?</h3>
                <span className="donor-bell-badge">
                  <LuBell size={16} />
                </span>
              </div>
              <p>Post an urgent request and reach nearby donors, instantly.</p>

              <div className="donor-emergency-group-picker">
                {BLOOD_GROUPS.map((bg) => (
                  <button
                    key={bg}
                    type="button"
                    className={`donor-group-pill${selectedGroup === bg ? " is-active" : ""}`}
                    onClick={() => setSelectedGroup(bg)}
                  >
                    {bg}
                  </button>
                ))}
              </div>

              <button
                className="donor-emergency-btn"
                onClick={() => scrollToFind(selectedGroup)}
              >
                <LuBell size={16} /> Request Blood
              </button>
              <span className="donor-emergency-hint">
                We'll notify nearby matching donors once you submit the request below.
              </span>
            </div>
          </div>
        </section>

        <section className="donor-cta-row">
          <button className="donor-cta-card donor-cta-card--gold" onClick={scrollToRegister}>
            <span className="donor-cta-icon">
              <LuDroplet size={22} />
            </span>
            <span className="donor-cta-text">
              <strong>Become a Donor</strong>
              <span>Register, donate and make a difference.</span>
            </span>
            <span className="donor-cta-arrow"><LuArrowRight size={20} /></span>
          </button>

          <button className="donor-cta-card donor-cta-card--red" onClick={() => scrollToFind()}>
            <span className="donor-cta-icon">
              <LuSearch size={22} />
            </span>
            <span className="donor-cta-text">
              <strong>Need Blood?</strong>
              <span>Find compatible donors near you.</span>
            </span>
            <span className="donor-cta-arrow"><LuArrowRight size={20} /></span>
          </button>
        </section>

        <section className="donor-card donor-section" ref={registerSectionRef}>
          <div className="donor-section-header">
            <LuHeartHandshake size={22} />
            <h2>Aapki Donor Profile</h2>
          </div>

          {checkingProfile ? (
            <p className="donor-text-secondary">Profile check ho raha hai...</p>
          ) : !isLoggedIn ? (
            <p className="donor-text-secondary">Donor banne ke liye pehle login karo.</p>
          ) : donor ? (
            <div className="donor-profile-card">
              <div className="donor-profile-row">
                <div className="donor-stat">
                  <span className="donor-stat-label">Naam</span>
                  <span className="donor-stat-value">{donor.name}</span>
                </div>
                <div className="donor-stat">
                  <span className="donor-stat-label">Blood Group</span>
                  <span className="donor-stat-value donor-blood-badge">
                    <LuDroplet size={14} /> {donor.blood_group}
                  </span>
                </div>
                <div className="donor-stat">
                  <span className="donor-stat-label">Location</span>
                  <span className="donor-stat-value">
                    <LuMapPin size={14} /> {donor.city}, {donor.state}
                  </span>
                </div>
                <div className="donor-stat">
                  <span className="donor-stat-label">Total Donations</span>
                  <span className="donor-stat-value">{donor.donation_count ?? 0}</span>
                </div>
              </div>

              <div className="donor-actions">
                <button
                  className={`donor-btn-primary donor-availability-btn ${donor.available ? "is-available" : "is-unavailable"}`}
                  onClick={handleToggleAvailability}
                  disabled={toggling}
                >
                  <LuPower size={16} />
                  {toggling
                    ? "Update ho raha hai..."
                    : donor.available
                    ? "Available — tap to pause"
                    : "Unavailable — tap to activate"}
                </button>
                <button className="donor-btn-secondary" onClick={handleRecordDonation} disabled={recording}>
                  {recording ? "Saving..." : "Record a Donation"}
                </button>
              </div>
              {registerError && <p className="donor-form-error">{registerError}</p>}
            </div>
          ) : (
            <form className="donor-form" onSubmit={handleRegister}>
              <div className="donor-form-grid">
                <label className="donor-field">
                  <span>Naam</span>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="Apna pura naam"
                  />
                </label>
                <label className="donor-field">
                  <span>Blood Group</span>
                  <select
                    value={form.blood_group}
                    onChange={(e) => setForm({ ...form, blood_group: e.target.value })}
                  >
                    <option value="">Select karo</option>
                    {BLOOD_GROUPS.map((bg) => (
                      <option key={bg} value={bg}>{bg}</option>
                    ))}
                  </select>
                </label>
                <label className="donor-field">
                  <span>City</span>
                  <input
                    type="text"
                    value={form.city}
                    onChange={(e) => setForm({ ...form, city: e.target.value })}
                    placeholder="e.g. Bhiwani"
                  />
                </label>
                <label className="donor-field">
                  <span>State</span>
                  <input
                    type="text"
                    value={form.state}
                    onChange={(e) => setForm({ ...form, state: e.target.value })}
                    placeholder="e.g. Haryana"
                  />
                </label>
                <label className="donor-field donor-field-wide">
                  <span>Phone</span>
                  <input
                    type="tel"
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    placeholder="10-digit mobile number"
                  />
                </label>
              </div>
              {registerError && <p className="donor-form-error">{registerError}</p>}
              <button className="donor-btn-primary" type="submit" disabled={registering}>
                {registering ? "Register ho raha hai..." : "Donor Banein"}
              </button>
            </form>
          )}
        </section>

        <section className="donor-card donor-section" ref={findSectionRef}>
          <div className="donor-section-header">
            <LuSearch size={22} />
            <h2>Matching Donors Dhundo</h2>
          </div>

          <form className="donor-form" onSubmit={handleFindDonors}>
            <div className="donor-form-grid">
              <label className="donor-field">
                <span>Blood Group</span>
                <select
                  value={findForm.blood_group}
                  onChange={(e) => setFindForm({ ...findForm, blood_group: e.target.value })}
                >
                  <option value="">Select karo</option>
                  {BLOOD_GROUPS.map((bg) => (
                    <option key={bg} value={bg}>{bg}</option>
                  ))}
                </select>
              </label>
              <label className="donor-field">
                <span>City</span>
                <input
                  type="text"
                  value={findForm.city}
                  onChange={(e) => setFindForm({ ...findForm, city: e.target.value })}
                  placeholder="e.g. Bhiwani"
                />
              </label>
              <label className="donor-field">
                <span>State</span>
                <input
                  type="text"
                  value={findForm.state}
                  onChange={(e) => setFindForm({ ...findForm, state: e.target.value })}
                  placeholder="e.g. Haryana"
                />
              </label>
            </div>
            {searchError && <p className="donor-form-error">{searchError}</p>}
            <div className="donor-search-actions">
              <button className="donor-btn-primary" type="submit" disabled={searching}>
                {searching ? "Dhundh rahe hain..." : "Donors Dhundo"}
              </button>
              <button type="button" className="donor-btn-secondary" onClick={handleCreateRequest}>
                Emergency Request Bhejo
              </button>
            </div>
            {requestStatus && <p className="donor-text-secondary donor-request-status">{requestStatus}</p>}
            <label className="donor-field donor-field-wide">
              <span>Request ke saath message (optional)</span>
              <input
                type="text"
                value={requestMessage}
                onChange={(e) => setRequestMessage(e.target.value)}
                placeholder="e.g. Hospital ka naam, urgency ki wajah"
              />
            </label>
          </form>

          {foundDonors && (
            <div className="donor-results">
              {foundDonors.length === 0 ? (
                <p className="donor-text-secondary">Is criteria pe koi donor nahi mila abhi.</p>
              ) : (
                foundDonors.map((d, idx) => (
                  <div className="donor-result-card" key={d.user_id || idx}>
                    <div className="donor-result-main">
                      <span className="donor-result-name">{d.name}</span>
                      <span className="donor-blood-badge">
                        <LuDroplet size={13} /> {d.blood_group}
                      </span>
                    </div>
                    <div className="donor-result-meta">
                      <span><LuMapPin size={13} /> {d.city}, {d.state}</span>
                      {d.phone && <span><LuPhone size={13} /> {d.phone}</span>}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </section>

        <section className="donor-card donor-section donor-compat-section">
          <div className="donor-section-header">
            <LuDroplet size={22} />
            <h2>Check Blood Compatibility</h2>
          </div>

          <div className="donor-group-picker-row">
            {BLOOD_GROUPS.map((bg) => (
              <button
                key={bg}
                type="button"
                className={`donor-group-pill donor-group-pill--lg${selectedGroup === bg ? " is-active" : ""}`}
                onClick={() => setSelectedGroup(bg)}
              >
                {bg}
              </button>
            ))}
          </div>

          {compat && (
            <div className="donor-compat-grid">
              <div className="donor-compat-block">
                <span className="donor-compat-label">Can donate to</span>
                <div className="donor-chip-row">
                  {compat.canDonateTo.map((g) => (
                    <span key={g} className="donor-chip">{g}</span>
                  ))}
                </div>
              </div>
              <div className="donor-compat-block">
                <span className="donor-compat-label">Can receive from</span>
                <div className="donor-chip-row">
                  {compat.canReceiveFrom.map((g) => (
                    <span key={g} className="donor-chip">{g}</span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
}