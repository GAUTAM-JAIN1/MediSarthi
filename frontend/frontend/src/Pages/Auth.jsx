import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import "./Auth.css";

export default function Auth() {
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [form, setForm] = useState({ name: "", email: "", password: "" });
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
    if (mode === "signup" && !form.name) {
      setError("Naam bhi bharo bhai.");
      return;
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
              // signup ke liye backend ko extra fields chahiye honge
              // (age, gender, city, state) — abhi defaults bhej rahe hain,
              // signup form mein ye fields add karne honge baad mein.
              name: form.name,
              email: form.email,
              password: form.password,
              age: 0,
              gender: "",
              allergies: "",
              city: "",
              state: "",
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