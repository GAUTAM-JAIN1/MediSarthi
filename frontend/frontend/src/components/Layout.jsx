import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./Layout.css";

// ── Gold particles ambient background ────────────────────────────────────
export function GoldParticles({ count = 18 }) {
  const particles = Array.from({ length: count }, (_, i) => ({
    id: i,
    left: `${5 + ((i * 37 + i * i * 13) % 90)}%`,
    top: `${5 + ((i * 53 + i * 7) % 88)}%`,
    size: 2 + (i % 3),
    delay: `${(i * 0.7) % 6}s`,
    duration: `${8 + (i % 6)}s`,
  }));
  return (
    <div className="ms-particles" aria-hidden="true">
      {particles.map((p) => (
        <span
          key={p.id}
          className="ms-particle"
          style={{
            left: p.left,
            top: p.top,
            width: p.size,
            height: p.size,
            animationDelay: p.delay,
            animationDuration: p.duration,
          }}
        />
      ))}
    </div>
  );
}

// ── Ambient background ────────────────────────────────────────────────────
export function AmbientBackground() {
  return (
    <div className="ms-ambient" aria-hidden="true">
      <div className="ms-ambient-orb ms-ambient-orb--1" />
      <div className="ms-ambient-orb ms-ambient-orb--2" />
    </div>
  );
}

// ── Logo mark ──────────────────────────────────────────────────────────────
export function LogoMark({ size = 32, accent = false, center = false }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      style={{ display: "block", margin: center ? "0 auto" : undefined }}
    >
      <circle
        cx="16" cy="16" r="12"
        stroke={accent ? "var(--ms-soft-gold)" : "var(--ms-luxury-brown)"}
        strokeWidth="2" fill="none"
      />
      <circle
        cx="16" cy="16" r="5"
        fill={accent ? "var(--ms-soft-gold)" : "var(--ms-luxury-brown)"}
        opacity="0.85"
      />
      <line x1="16" y1="4"  x2="16" y2="10" stroke={accent ? "var(--ms-soft-gold)" : "var(--ms-luxury-brown)"} strokeWidth="2" strokeLinecap="round" />
      <line x1="16" y1="22" x2="16" y2="28" stroke={accent ? "var(--ms-soft-gold)" : "var(--ms-luxury-brown)"} strokeWidth="2" strokeLinecap="round" />
      <line x1="4"  y1="16" x2="10" y2="16" stroke={accent ? "var(--ms-soft-gold)" : "var(--ms-luxury-brown)"} strokeWidth="2" strokeLinecap="round" />
      <line x1="22" y1="16" x2="28" y2="16" stroke={accent ? "var(--ms-soft-gold)" : "var(--ms-luxury-brown)"} strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

// ── Nav links config ───────────────────────────────────────────────────────
const NAV_LINKS = [
  { to: "/find-medicine",  label: "Find Medicine" },
  { to: "/lab-report",     label: "Lab Report" },
  { to: "/medicine-check", label: "Safety Check" },
  { to: "/compare",        label: "Compare" },
  { to: "/appointments",   label: "Appointments" },
  { to: "/health-info",    label: "Health Info" },
  { to: "/donor",          label: "Donor" },
];

// ── Main Layout ─────────────────────────────────────────────────────────────
export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userName, setUserName] = useState(null);

  useEffect(() => {
    const name = localStorage.getItem("ms_user_name");
    setUserName(name);
  }, [location.pathname]);

  const handleLogout = () => {
    localStorage.removeItem("ms_user_id");
    localStorage.removeItem("ms_user_name");
    setUserName(null);
    navigate("/auth");
  };

  return (
    <div className="ms-root">
      <AmbientBackground />
      <GoldParticles />

      {/* ── Nav ── */}
      <nav className="ms-nav">
        <Link to="/" className="ms-nav-brand" onClick={() => setMenuOpen(false)}>
          <LogoMark size={28} />
          <span className="ms-nav-brand-name">MediSarthi</span>
        </Link>

        {/* Desktop links */}
        <div className="ms-nav-links">
          {NAV_LINKS.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`ms-nav-link${location.pathname === to ? " active" : ""}`}
            >
              {label}
            </Link>
          ))}
        </div>

        {/* Auth area */}
        <div className="ms-nav-auth">
          {userName ? (
            <>
              <span className="ms-nav-username">✦ {userName.split(" ")[0]}</span>
              <button className="ms-nav-logout" onClick={handleLogout}>
                Logout
              </button>
            </>
          ) : (
            <Link to="/auth" className="ms-btn-primary ms-nav-login-btn">
              Login
            </Link>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="ms-nav-hamburger"
          onClick={() => setMenuOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          <span /><span /><span />
        </button>
      </nav>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="ms-mobile-menu">
          {NAV_LINKS.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className="ms-mobile-link"
              onClick={() => setMenuOpen(false)}
            >
              {label}
            </Link>
          ))}
          <div className="ms-mobile-auth">
            {userName ? (
              <>
                <span className="ms-nav-username">✦ {userName.split(" ")[0]}</span>
                <button className="ms-nav-logout" onClick={() => { handleLogout(); setMenuOpen(false); }}>
                  Logout
                </button>
              </>
            ) : (
              <Link to="/auth" className="ms-btn-primary" onClick={() => setMenuOpen(false)}>
                Login
              </Link>
            )}
          </div>
        </div>
      )}

      {/* ── Page content ── */}
      <main className="ms-main">{children}</main>
    </div>
  );
}