import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import "./Auth.css";

const EMPTY_FORM = {
  name: "",
  email: "",
  password: "",
  age: "",
  gender: "",
  allergies: "",
  city: "",
  state: "",
};

export default function Auth() {
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
  };

  // Backend kabhi string error deta hai, kabhi FastAPI validation array.
  // Ye function hamesha ek safe, readable string return karega.
  const extractErrorMessage = (data, fallback) => {
    if (!data) return fallback;
    const detail = data.detail;
    if (!detail) return fallback;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (item && item.msg ? item.msg : JSON.stringify(item)))
        .join(", ");
    }
    if (typeof detail === "object") {
      return detail.msg || JSON.stringify(detail);
    }
    return fallback;
  };

  const handleSubmit = async () => {
    setError("");
    if (!form.email || !form.password) {
      setError("Email aur password dono zaroori hain.");
      return;
    }
    if (mode === "signup") {
      if (!form.name) {
        setError("Naam bhi bharo bhai.");
        return;
      }
      if (!form.age || Number(form.age) <= 0) {
        setError("Sahi age daalo.");
        return;
      }
      if (!form.gender) {
        setError("Gender select karo.");
        return;
      }
      if (!form.city || !form.state) {
        setError("City aur State dono zaroori hain.");
        return;
      }
    }

    setLoading(true);
    try {
      const endpoint =
        mode === "login"
          ? "http://localhost:8080/auth/login"
          : "http://localhost:8080/auth/signup";

      // Backend Pydantic model (JSON body) expect karta hai, FormData nahi.
      const payload =
        mode === "login"
          ? { email: form.email, password: form.password }
          : {
              name: form.name,
              email: form.email,
              password: form.password,
              age: Number(form.age),
              gender: form.gender,
              allergies: form.allergies,
              city: form.city,
              state: form.state,
            };

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(extractErrorMessage(data, "Kuch gadbad ho gayi, dobara try karo."));
      } else {
        // user_id save karo localStorage mein
        localStorage.setItem("ms_user_id", data.user_id);
        localStorage.setItem("ms_user_name", data.name || form.email);
        localStorage.setItem("ms_token", data.access_token);
        navigate("/");
      }
    } catch {
      setError("Server se connect nahi ho pa raha. Backend chal raha hai?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="ms-auth-wrapper">
        <div className="ms-auth-card">
          {/* Logo / heading */}
          <div className="ms-auth-header">
            <div className="ms-auth-logo">✦</div>
            <h1 className="ms-auth-title">MediSarthi</h1>
            <p className="ms-auth-subtitle">
              {mode === "login"
                ? "Apne account mein wapis aao"
                : "Naya account banao"}
            </p>
          </div>

          {/* Tab switcher */}
          <div className="ms-auth-tabs">
            <button
              className={`ms-auth-tab ${mode === "login" ? "active" : ""}`}
              onClick={() => { setMode("login"); setError(""); }}
            >
              Login
            </button>
            <button
              className={`ms-auth-tab ${mode === "signup" ? "active" : ""}`}
              onClick={() => { setMode("signup"); setError(""); }}
            >
              Sign Up
            </button>
          </div>

          {/* Form */}
          <div className="ms-auth-form">
            {mode === "signup" && (
              <div className="ms-auth-field">
                <label className="ms-auth-label">Naam</label>
                <input
                  className="ms-auth-input"
                  type="text"
                  name="name"
                  placeholder="Tumhara naam"
                  value={form.name}
                  onChange={handleChange}
                />
              </div>
            )}

            <div className="ms-auth-field">
              <label className="ms-auth-label">Email</label>
              <input
                className="ms-auth-input"
                type="email"
                name="email"
                placeholder="email@example.com"
                value={form.email}
                onChange={handleChange}
              />
            </div>

            <div className="ms-auth-field">
              <label className="ms-auth-label">Password</label>
              <input
                className="ms-auth-input"
                type="password"
                name="password"
                placeholder="••••••••"
                value={form.password}
                onChange={handleChange}
              />
            </div>

            {mode === "signup" && (
              <>
                <div className="ms-auth-row">
                  <div className="ms-auth-field">
                    <label className="ms-auth-label">Age</label>
                    <input
                      className="ms-auth-input"
                      type="number"
                      name="age"
                      min="1"
                      max="120"
                      placeholder="21"
                      value={form.age}
                      onChange={handleChange}
                    />
                  </div>

                  <div className="ms-auth-field">
                    <label className="ms-auth-label">Gender</label>
                    <select
                      className="ms-auth-input ms-auth-select"
                      name="gender"
                      value={form.gender}
                      onChange={handleChange}
                    >
                      <option value="">Select</option>
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>

                <div className="ms-auth-row">
                  <div className="ms-auth-field">
                    <label className="ms-auth-label">City</label>
                    <input
                      className="ms-auth-input"
                      type="text"
                      name="city"
                      placeholder="Faridabad"
                      value={form.city}
                      onChange={handleChange}
                    />
                  </div>

                  <div className="ms-auth-field">
                    <label className="ms-auth-label">State</label>
                    <input
                      className="ms-auth-input"
                      type="text"
                      name="state"
                      placeholder="Haryana"
                      value={form.state}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="ms-auth-field">
                  <label className="ms-auth-label">Allergies (optional)</label>
                  <input
                    className="ms-auth-input"
                    type="text"
                    name="allergies"
                    placeholder="e.g. Penicillin, Dust — chhod do agar koi nahi"
                    value={form.allergies}
                    onChange={handleChange}
                  />
                </div>
              </>
            )}

            {error && <p className="ms-auth-error">{error}</p>}

            <button
              className="ms-btn-primary ms-auth-submit"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading
                ? "Wait karo..."
                : mode === "login"
                ? "Login Karo"
                : "Account Banao"}
            </button>
          </div>

          <p className="ms-auth-switch">
            {mode === "login" ? (
              <>
                Naya user ho?{" "}
                <span onClick={() => { setMode("signup"); setError(""); }}>
                  Sign up karo
                </span>
              </>
            ) : (
              <>
                Pehle se account hai?{" "}
                <span onClick={() => { setMode("login"); setError(""); }}>
                  Login karo
                </span>
              </>
            )}
          </p>
        </div>
      </div>
    </Layout>
  );
}