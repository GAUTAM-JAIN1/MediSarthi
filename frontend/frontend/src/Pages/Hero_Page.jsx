import React from 'react';
import { Link } from 'react-router-dom';
import {
  LuSearch, LuMic, LuFileText, LuMessageCircle,
  LuPill, LuUsers, LuShuffle, LuCalendar, LuFolder, LuBot
} from 'react-icons/lu';
import Layout, { LogoMark } from '../components/Layout.jsx';
import './Hero_Page.css';

const SEGMENTS = [
  { key: 'medicines', icon: <LuPill />, title: 'Medicines', sub: '2,095 product listings', x: 0, y: -147.5, path: '/find-medicine' },
  { key: 'doctors', icon: <LuUsers />, title: 'Consult', sub: 'Symptom triage and nearby hospitals', x: 127.7, y: -73.7, path: '/appointments' },
  { key: 'compare', icon: <LuShuffle />, title: 'Compare', sub: 'Best Prices', x: 127.7, y: 73.7, path: '/compare' },
  { key: 'appointments', icon: <LuCalendar />, title: 'Appointments', sub: 'Book instantly', x: 0, y: 147.5, path: '/appointments' },
  { key: 'records', icon: <LuFolder />, title: 'Health Records', sub: 'Secure & private', x: -127.7, y: 73.7, path: '/health-info' },
  { key: 'ai', icon: <LuBot />, title: 'AI Assistant', sub: '24/7 support', x: -127.7, y: -73.8, path: '/find-medicine' },
];

const DONUT_PATHS = [
  "M -83.89,-181.56 A 200,200 0 0 1 83.89,-181.56 L 39.85,-86.24 A 95,95 0 0 0 -39.85,-86.24 Z",
  "M 115.29,-163.43 A 200,200 0 0 1 199.18,-18.13 L 94.61,-8.61 A 95,95 0 0 0 54.76,-77.63 Z",
  "M 199.18,18.13 A 200,200 0 0 1 115.29,163.43 L 54.76,77.63 A 95,95 0 0 0 94.61,8.61 Z",
  "M 83.89,181.56 A 200,200 0 0 1 -83.89,181.56 L -39.85,86.24 A 95,95 0 0 0 39.85,86.24 Z",
  "M -115.29,163.43 A 200,200 0 0 1 -199.18,18.13 L -94.61,8.61 A 95,95 0 0 0 -54.76,77.63 Z",
  "M -199.18,-18.13 A 200,200 0 0 1 -115.29,-163.43 L -54.76,-77.63 A 95,95 0 0 0 -94.61,-8.61 Z",
];

const FEATURES = [
  { key: 'discovery', color: 'purple', icon: <LuPill />, title: 'Smart Medicine Discovery', sub: 'Find the right medicine with AI suggestions.', path: '/find-medicine' },
  { key: 'compare-save', color: 'olive', icon: <LuShuffle />, title: 'Compare & Save', sub: 'Compare Jan Aushadhi generic prices.', path: '/compare' },
  { key: 'trusted', color: 'blue', icon: <LuUsers />, title: 'Trusted Healthcare', sub: 'Connect with verified doctors near you.', path: '/appointments' },
  { key: 'insights', color: 'orange', icon: <LuMessageCircle />, title: 'Health Insights', sub: 'Personalized tips and health tracking.', path: '/health-info' },
  { key: 'secure', color: 'teal', icon: <LuFolder />, title: 'Secure & Private', sub: 'Your records are saved to your account and protected by login.', path: '/health-info' },
];

const STATS = [
  { key: 'medicines', icon: <LuPill />, num: '2,095', label: 'Jan Aushadhi listings' },
  { key: 'pharmacies', icon: <LuFolder />, num: '2 Nov 2026', label: 'Price list date' },
  { key: 'support', icon: <LuMessageCircle />, num: '24/7', label: 'Support Available' },
];

const TRUST_ITEMS = [
  { key: 'pharmacies', icon: <LuFileText />, title: 'Official price list', sub: 'PMBJP Jan Aushadhi' },
  { key: 'triage', icon: <LuMessageCircle />, title: 'Symptom Triage', sub: 'Check symptoms before you visit a doctor' },
  { key: 'support', icon: <LuMessageCircle />, title: '24/7 Customer Support', sub: "We're always here" },
];

export default function Hero_Page() {
  return (
    <Layout>
      <section className="ms-hero">
        <div className="ms-hero-left">
          <div className="ms-badge">
            <svg viewBox="0 0 24 24" fill="currentColor" width="13" height="13">
              <path d="M12 2c1.5 2 1.5 4.5 0 6.5C10.5 6.5 10.5 4 12 2Z" />
              <path d="M12 22c-1.5-2-1.5-4.5 0-6.5 1.5 2 1.5 4.5 0 6.5Z" />
              <path d="M2 12c2-1.5 4.5-1.5 6.5 0-2 1.5-4.5 1.5-6.5 0Z" />
              <path d="M22 12c-2 1.5-4.5 1.5-6.5 0 2-1.5 4.5-1.5 6.5 0Z" />
            </svg>
            Welcome to Medisarthi
          </div>

          <h1 className="ms-headline">
            Intelligent care,<br />
            <span className="ms-accent">simplified</span> for you.
          </h1>

          <p className="ms-hero-desc">
            Your all-in-one partner for medicines, trusted doctors, health insights
            and more — all just a search or voice away.
          </p>

          <form className="ms-search-bar" onSubmit={(e) => e.preventDefault()}>
            <LuSearch className="ms-icon" />
            <input type="text" placeholder="Describe your symptoms or health query..." />
            <button type="submit">
              <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                <path d="M12 2c1.2 1.8 1.2 3.8 0 5.5C10.8 5.8 10.8 3.8 12 2Z" />
                <path d="M2 12c1.8-1.2 3.8-1.2 5.5 0C5.8 13.2 3.8 13.2 2 12Z" />
                <path d="M12 22c1.2-1.8 1.2-3.8 0-5.5 1.2 1.7 1.2 3.7 0 5.5Z" />
                <path d="M22 12c-1.8 1.2-3.8 1.2-5.5 0 1.7-1.2 3.7-1.2 5.5 0Z" />
              </svg>
              Ask Medisarthi
            </button>
          </form>

          <div className="ms-quick-actions">
            <Link to="/find-medicine" className="ms-qa-chip">
              <span className="ms-qa-icon"><LuMic /></span>
              <span>
                <span className="ms-qa-title">Voice search</span>
                <span className="ms-qa-sub">Tap to speak</span>
              </span>
            </Link>
            <Link to="/find-medicine" className="ms-qa-chip">
              <span className="ms-qa-icon"><LuFileText /></span>
              <span>
                <span className="ms-qa-title">Scan prescription</span>
                <span className="ms-qa-sub">Upload &amp; analyze</span>
              </span>
            </Link>
            <Link to="/find-medicine" className="ms-qa-chip">
              <span className="ms-qa-icon"><LuMessageCircle /></span>
              <span>
                <span className="ms-qa-title">AI assistant</span>
                <span className="ms-qa-sub">Chat anytime</span>
              </span>
            </Link>
          </div>
        </div>

        <div className="ms-hero-right">
          <div className="ms-ring-stage">
            <div className="ms-podium" />

            <div className="ms-donut-wrap">
              <svg className="ms-donut-svg" viewBox="-210 -210 420 420">
                <defs>
                  <linearGradient id="msSegGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#FCFAF6" />
                    <stop offset="100%" stopColor="#EFE5D6" />
                  </linearGradient>
                  <filter id="msSegShadow" x="-50%" y="-50%" width="200%" height="200%">
                    <feDropShadow dx="0" dy="6" stdDeviation="8" floodColor="#9C6B45" floodOpacity="0.22" />
                  </filter>
                </defs>
                <g filter="url(#msSegShadow)">
                  {DONUT_PATHS.map((d, i) => (
                    <path key={i} className="ms-donut-seg" d={d} fill="url(#msSegGrad)" />
                  ))}
                </g>
              </svg>

              <div className="ms-seg-content-orbit">
                {SEGMENTS.map((seg) => (
                  <Link
                    key={seg.key}
                    to={seg.path}
                    className="ms-seg-content"
                    style={{ left: `calc(50% + ${seg.x}px)`, top: `calc(50% + ${seg.y}px)` }}
                  >
                    <div className="ms-ic">{seg.icon}</div>
                    <div className="ms-t">{seg.title}</div>
                    <div className="ms-s">{seg.sub}</div>
                  </Link>
                ))}
              </div>
            </div>

            <div className="ms-ring-center">
              <div className="ms-glow-pulse" />
              <LogoMark size={36} accent="#D7B895" center="#9C6B45" />
            </div>
          </div>
        </div>
      </section>

      <section className="ms-features-row">
        {FEATURES.map((f) => (
          <Link key={f.key} to={f.path} className="ms-feat-card">
            <div className={`ms-feat-icon ${f.color}`}>{f.icon}</div>
            <div className="ms-feat-title">{f.title}</div>
            <div className="ms-feat-sub">{f.sub}</div>
            <div className="ms-feat-arrow">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </div>
          </Link>
        ))}
      </section>

      <section className="ms-stats-bar">
        {STATS.map((s, i) => (
          <React.Fragment key={s.key}>
            <div className="ms-stat-item">
              <div className="ms-stat-icon">{s.icon}</div>
              <div>
                <div className="ms-stat-num">{s.num}</div>
                <div className="ms-stat-label">{s.label}</div>
              </div>
            </div>
            {i < STATS.length - 1 && <div className="ms-stat-divider" />}
          </React.Fragment>
        ))}
      </section>

      <footer className="ms-footer-trust">
        <div className="ms-trust-line">Trusted by thousands of users across the country</div>
        <div className="ms-trust-grid">
          {TRUST_ITEMS.map((t) => (
            <div key={t.key} className="ms-trust-item">
              {t.icon}
              <div>
                <div className="ms-trust-title">{t.title}</div>
                <div className="ms-trust-sub">{t.sub}</div>
              </div>
            </div>
          ))}
        </div>
      </footer>
    </Layout>
  );
}