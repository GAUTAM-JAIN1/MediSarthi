// HealthVault.jsx — realistic brass/bronze health vault illustration
// Decorative SVG (door, frame, rotating wheel) + 5 clickable HTML "drawers"
// overlaid on the interior recess. Purely presentational — HealthInfo.jsx
// owns all data/state and passes counts + a click handler in.

import { motion } from "framer-motion";
import {
  LuHeartPulse,
  LuPill,
  LuFileText,
  LuTriangleAlert,
  LuHistory,
  LuChevronRight,
  LuLock,
} from "react-icons/lu";
import "./HealthVault.css";

const DRAWERS = [
  { key: "vitals", label: "Vitals", icon: LuHeartPulse },
  { key: "medications", label: "Medications", icon: LuPill },
  { key: "reports", label: "Reports", icon: LuFileText },
  { key: "allergies", label: "Allergies", icon: LuTriangleAlert },
  { key: "medicalHistory", label: "Medical History", icon: LuHistory },
];

export default function HealthVault({ counts = {}, activeKey, onOpen }) {
  return (
    <div className="vault-outer">
      <div className="vault-glow" aria-hidden="true" />

      <div className="vault-wrap">
        {/* ── Decorative realistic vault SVG ── */}
        <svg
          className="vault-svg"
          viewBox="0 0 900 640"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="vFrameGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#F3E7D6" />
              <stop offset="45%" stopColor="#C79A6B" />
              <stop offset="100%" stopColor="#6F472D" />
            </linearGradient>
            <radialGradient id="vDoorGrad" cx="35%" cy="28%" r="85%">
              <stop offset="0%" stopColor="#F3E2C4" />
              <stop offset="45%" stopColor="#B98A5D" />
              <stop offset="100%" stopColor="#5B3C22" />
            </radialGradient>
            <radialGradient id="vInteriorGrad" cx="50%" cy="15%" r="90%">
              <stop offset="0%" stopColor="#3A2A1A" />
              <stop offset="55%" stopColor="#221709" />
              <stop offset="100%" stopColor="#120B05" />
            </radialGradient>
            <radialGradient id="vLampGlow" cx="50%" cy="0%" r="70%">
              <stop offset="0%" stopColor="rgba(255,231,181,0.65)" />
              <stop offset="100%" stopColor="rgba(255,231,181,0)" />
            </radialGradient>
            <radialGradient id="vWheelGrad" cx="35%" cy="30%" r="75%">
              <stop offset="0%" stopColor="#FDF3E1" />
              <stop offset="50%" stopColor="#D7B895" />
              <stop offset="100%" stopColor="#6F472D" />
            </radialGradient>
            <filter id="vShadow" x="-30%" y="-30%" width="160%" height="160%">
              <feDropShadow dx="0" dy="18" stdDeviation="22" floodColor="#3b2412" floodOpacity="0.35" />
            </filter>
          </defs>

          <g filter="url(#vShadow)">
            {/* Outer frame */}
            <rect x="380" y="30" width="480" height="580" rx="26" fill="url(#vFrameGrad)" stroke="#4A2F1A" strokeWidth="2" />
            {Array.from({ length: 7 }).map((_, i) => (
              <circle key={`rt-${i}`} cx={410 + i * 65} cy="44" r="4.5" fill="#4A2F1A" opacity="0.6" />
            ))}
            {Array.from({ length: 7 }).map((_, i) => (
              <circle key={`rb-${i}`} cx={410 + i * 65} cy="596" r="4.5" fill="#4A2F1A" opacity="0.6" />
            ))}
            {Array.from({ length: 8 }).map((_, i) => (
              <circle key={`rr-${i}`} cx="846" cy={54 + i * 68} r="4.5" fill="#4A2F1A" opacity="0.6" />
            ))}

            {/* Interior recess */}
            <rect x="410" y="60" width="420" height="520" rx="18" fill="url(#vInteriorGrad)" />
            <ellipse cx="620" cy="95" rx="200" ry="55" fill="url(#vLampGlow)" />

            {/* Door — swung open, foreshortened for a 3D feel */}
            <g className="vault-door">
              <polygon
                points="380,30 380,610 40,500 40,140"
                fill="url(#vDoorGrad)"
                stroke="#4A2F1A"
                strokeWidth="2"
              />
              <polygon points="88,165 88,478 122,468 122,175" fill="#FFFFFF" opacity="0.09" />

              {/* hinge pins */}
              <circle cx="380" cy="112" r="15" fill="#3B2412" />
              <circle cx="380" cy="112" r="6" fill="#D7B895" />
              <circle cx="380" cy="522" r="15" fill="#3B2412" />
              <circle cx="380" cy="522" r="6" fill="#D7B895" />

              {/* retracted bolt studs */}
              {Array.from({ length: 5 }).map((_, i) => (
                <circle key={`bolt-${i}`} cx="360" cy={160 + i * 80} r="6" fill="#4A2F1A" opacity="0.55" />
              ))}

              {/* Wheel handle */}
              <g className="vault-wheel">
                <circle cx="205" cy="325" r="92" fill="none" stroke="url(#vWheelGrad)" strokeWidth="14" />
                {Array.from({ length: 8 }).map((_, i) => {
                  const angle = (i * Math.PI) / 4;
                  const x2 = 205 + Math.cos(angle) * 78;
                  const y2 = 325 + Math.sin(angle) * 78;
                  return (
                    <line
                      key={`spoke-${i}`}
                      x1="205" y1="325" x2={x2} y2={y2}
                      stroke="url(#vWheelGrad)" strokeWidth="10" strokeLinecap="round"
                    />
                  );
                })}
                <circle cx="205" cy="325" r="30" fill="url(#vWheelGrad)" stroke="#4A2F1A" strokeWidth="2" />
                <ellipse cx="196" cy="315" rx="10" ry="6" fill="#FFFFFF" opacity="0.5" />
              </g>
            </g>
          </g>
        </svg>

        {/* ── Clickable drawers, overlaid on interior recess ── */}
        <div className="vault-drawers">
          {DRAWERS.map(({ key, label, icon: Icon }) => (
            <motion.button
              key={key}
              type="button"
              className={`vault-drawer-btn${activeKey === key ? " is-active" : ""}`}
              onClick={() => onOpen(key)}
              whileHover={{ scale: 1.025, x: 4 }}
              whileTap={{ scale: 0.97 }}
              transition={{ type: "spring", stiffness: 400, damping: 22 }}
            >
              <span className="vault-drawer-icon">
                <Icon size={19} />
              </span>
              <span className="vault-drawer-label">{label}</span>
              <span className="vault-drawer-count">
                {String(counts[key] ?? 0).padStart(2, "0")}
              </span>
              <span className="vault-drawer-chevron">
                <LuChevronRight size={16} />
              </span>
            </motion.button>
          ))}
        </div>
      </div>

      <div className="vault-footer">
        <LuLock size={13} />
        <span>Your health vault is encrypted</span>
      </div>
    </div>
  );
}