import React, { useState, useEffect } from 'react';
import {
  LuSearch, LuExternalLink, LuTrendingDown, LuTruck, LuLoader,
  LuSparkles, LuShieldCheck, LuLock, LuScale, LuStore, LuChevronRight,
  LuChevronDown, LuPlus, LuAward, LuTag, LuPiggyBank,
} from 'react-icons/lu';
import Layout from '../components/Layout.jsx';
import { useUser } from '../hooks/useUser';
import '../components/Layout.css';
import './Compare.css';

// Safe helper — same pattern as Auth.jsx/HealthInfo.jsx/FindMedicine.jsx.
const extractErrorMessage = (detail, fallback) => {
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === 'string' ? d : d?.msg || JSON.stringify(d))).join(', ');
  }
  if (typeof detail === 'object' && detail.msg) return detail.msg;
  return fallback;
};

// Real browser automation genuinely takes 1-3 minutes per medicine — the
// agent is opening actual pharmacy sites, searching, and reading pages, not
// hitting a fast API. A single static "please wait" line over that long a
// wait reads as broken/stuck. This rotates through honest, specific status
// messages and shows elapsed time, so the wait feels alive instead of frozen.
const PROGRESS_MESSAGES = [
  'Apollo Pharmacy khol rahe hain...',
  'Medicine search kar rahe hain...',
  'Product details padh rahe hain...',
  '1mg pe switch kar rahe hain...',
  'Price aur delivery info nikal rahe hain...',
  'Almost done, results compile ho rahe hain...',
];

// UNCHANGED — same interval/timer logic
function LoadingProgress() {
  const [messageIndex, setMessageIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const messageTimer = setInterval(() => {
      setMessageIndex((i) => (i + 1) % PROGRESS_MESSAGES.length);
    }, 8000);
    const clockTimer = setInterval(() => {
      setElapsed((e) => e + 1);
    }, 1000);
    return () => {
      clearInterval(messageTimer);
      clearInterval(clockTimer);
    };
  }, []);

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  const timeLabel = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;

  return (
    <div className="ms-cmp-loading-hint">
      <LuLoader className="ms-cmp-spin" size={14} />
      <span>
        {PROGRESS_MESSAGES[messageIndex]} ({timeLabel} ho gaye — yeh normally
        1-3 minute lagta hai, real pharmacy sites check ho rahi hain)
      </span>
    </div>
  );
}

// One site's result card. "Buy" is always a plain link out to the pharmacy's
// own product page — nothing is ever added to a cart by this app on the
// user's behalf. UNCHANGED — no logic touched, only used inside the
// expandable detail panel of a comparison row now.
function SiteResultCard({ result, isBestPrice, isFastestDelivery }) {
  const unavailable = !result.available;

  return (
    <div className={`ms-cmp-row ms-card ${unavailable ? 'ms-cmp-row--unavailable' : ''}`}>
      <div className="ms-cmp-row-main">
        <div className="ms-cmp-pharmacy">
          <span className="ms-cmp-pharmacy-icon"><LuStore /></span>
          {result.site}
          {isBestPrice && (
            <span className="ms-cmp-tag ms-cmp-tag--price">
              <LuTrendingDown size={13} /> Best price
            </span>
          )}
          {isFastestDelivery && (
            <span className="ms-cmp-tag ms-cmp-tag--delivery">
              <LuTruck size={13} /> Fastest delivery
            </span>
          )}
        </div>

        {unavailable ? (
          <div className="ms-cmp-unavailable">Medicine nahi mili is site par.</div>
        ) : (
          <>
            <div className="ms-cmp-product-name">{result.product_name}</div>
            {result.quantity && <div className="ms-cmp-quantity">{result.quantity}</div>}
            {result.delivery_info && (
              <div className="ms-cmp-delivery">
                <LuTruck size={13} /> {result.delivery_info}
              </div>
            )}
            {result.notes && <div className="ms-cmp-notes">{result.notes}</div>}
          </>
        )}
      </div>

      {!unavailable && (
        <>
          <div className="ms-cmp-price">
            {result.price != null ? `₹${result.price}` : '—'}
          </div>

          <div className="ms-cmp-row-actions">
            {result.product_url ? (
              <a
                href={result.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="ms-btn-primary ms-cmp-buy-link"
              >
                Buy on {result.site} <LuExternalLink size={14} />
              </a>
            ) : (
              <a
                href={`https://www.google.com/search?q=${encodeURIComponent(result.product_name + ' ' + result.site)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="ms-btn-secondary ms-cmp-buy-link"
              >
                Find on {result.site} <LuExternalLink size={14} />
              </a>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// Full per-site breakdown for one medicine — shown inside a row's expanded
// detail panel. UNCHANGED logic, just reused in a new place.
function MedicineComparisonBlock({ entry }) {
  const { results, best_price_site, fastest_delivery_site } = entry;
  const noneAvailable = results.every((r) => !r.available);

  return (
    <div className="ms-cmp-medicine-block">
      {noneAvailable ? (
        <div className="ms-empty-state">
          Yeh medicine kisi bhi checked pharmacy par nahi mili. Naam check karo ya kisi
          alternate spelling/brand se try karo.
        </div>
      ) : (
        <div className="ms-cmp-results">
          {results.map((r, i) => (
            <SiteResultCard
              key={i}
              result={r}
              isBestPrice={best_price_site === r.site}
              isFastestDelivery={fastest_delivery_site === r.site}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Helpers: pull a two-site (siteA vs siteB) comparison pair out of one
//    medicine's `results` array. Backend always checks exactly 2 sites
//    (1mg + Apollo, see buying_agent.py) so this stays generic on site
//    *names* — it reads them from the actual API response, never hardcodes
//    "1mg"/"Apollo" as data, only as a display fallback. ──
function getSiteResult(entry, siteName) {
  return entry.results?.find((r) => r.site === siteName) || null;
}

function getPair(entry, siteA, siteB) {
  const a = getSiteResult(entry, siteA);
  const b = getSiteResult(entry, siteB);
  if (!a || !b || !a.available || !b.available || a.price == null || b.price == null) {
    return null;
  }
  const lowerSite = a.price <= b.price ? siteA : siteB;
  return {
    a, b,
    lowerSite,
    higherSite: lowerSite === siteA ? siteB : siteA,
    lowerPrice: Math.min(a.price, b.price),
    higherPrice: Math.max(a.price, b.price),
    diff: Math.abs(a.price - b.price),
  };
}

// ── Balance scale — SVG + CSS animation only, no external library. ──
// phase: 'idle' (nothing searched yet, gentle float) | 'loading' (actively
// weighing, keeps oscillating up-down) | 'settled' (comparison done, tips
// toward the winner and stays there).
function BalanceScale({ phase, winnerSide, labelA, labelB }) {
  const tilt = phase === 'settled' ? (winnerSide === 'A' ? -9 : winnerSide === 'B' ? 9 : 0) : 0;

  return (
    <svg viewBox="0 0 320 270" className={`ms-cmp-scale-svg ms-cmp-scale-svg--${phase}`}>
      <defs>
        <linearGradient id="cmpBronzeH" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#5E3D22" />
          <stop offset="18%" stopColor="#9C6B3E" />
          <stop offset="45%" stopColor="#E8C57E" />
          <stop offset="52%" stopColor="#FBEFCE" />
          <stop offset="60%" stopColor="#E8C57E" />
          <stop offset="82%" stopColor="#9C6B3E" />
          <stop offset="100%" stopColor="#5E3D22" />
        </linearGradient>
        <linearGradient id="cmpBronzeV" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#EAC886" />
          <stop offset="35%" stopColor="#B4834A" />
          <stop offset="70%" stopColor="#7C532C" />
          <stop offset="100%" stopColor="#54341B" />
        </linearGradient>
        <radialGradient id="cmpClockFace" cx="35%" cy="30%" r="75%">
          <stop offset="0%" stopColor="#FFFDF6" />
          <stop offset="65%" stopColor="#FAF1DC" />
          <stop offset="100%" stopColor="#E7D6AE" />
        </radialGradient>
        <radialGradient id="cmpPanGrad" cx="32%" cy="20%" r="85%">
          <stop offset="0%" stopColor="#F5E3B8" />
          <stop offset="45%" stopColor="#C8963F" />
          <stop offset="100%" stopColor="#764B22" />
        </radialGradient>
        <radialGradient id="cmpGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#E88C3A" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#E88C3A" stopOpacity="0" />
        </radialGradient>
        <filter id="cmpShadow" x="-40%" y="-20%" width="180%" height="160%">
          <feDropShadow dx="0" dy="7" stdDeviation="7" floodColor="#3A2411" floodOpacity="0.22" />
        </filter>
      </defs>

      {/* soft contact shadow under the base */}
      <ellipse cx="160" cy="252" rx="58" ry="9" fill="#3A2411" opacity="0.16" />

      <g filter="url(#cmpShadow)">
        {/* base + post */}
        <ellipse cx="160" cy="248" rx="50" ry="9" fill="url(#cmpBronzeH)" />
        <rect x="153" y="112" width="14" height="138" rx="5" fill="url(#cmpBronzeV)" />
        <ellipse cx="160" cy="112" rx="9" ry="4" fill="#EAC886" opacity="0.8" />

        {/* clock */}
        <circle cx="160" cy="52" r="34" fill="url(#cmpClockFace)" stroke="url(#cmpBronzeH)" strokeWidth="6" />
        {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((deg) => {
          const rad = (deg * Math.PI) / 180;
          const x1 = 160 + Math.sin(rad) * 27;
          const y1 = 52 - Math.cos(rad) * 27;
          const x2 = 160 + Math.sin(rad) * 31;
          const y2 = 52 - Math.cos(rad) * 31;
          return <line key={deg} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#B4834A" strokeWidth="1.4" />;
        })}
        <line x1="160" y1="52" x2="160" y2="33" stroke="#54341B" strokeWidth="2.6" strokeLinecap="round" />
        <line x1="160" y1="52" x2="173" y2="52" stroke="#54341B" strokeWidth="2.6" strokeLinecap="round" />
        <circle cx="160" cy="52" r="3" fill="#54341B" />

        {/* neck connecting clock to the wing/beam */}
        <path d="M 148 84 Q 160 96 172 84 L 172 100 Q 160 108 148 100 Z" fill="url(#cmpBronzeV)" />

        {/* rotating wing/beam group — pivot at (160, 108) */}
        <g
          className={`ms-cmp-scale-beam ms-cmp-scale-beam--${phase}`}
          style={phase === 'settled' ? { transform: `rotate(${tilt}deg)` } : undefined}
        >
          <path
            d="M 62 118 Q 110 96 160 108 Q 210 96 258 118 L 258 126 Q 210 106 160 118 Q 110 106 62 126 Z"
            fill="url(#cmpBronzeH)"
          />
          <circle cx="160" cy="110" r="7" fill="#54341B" />

          {/* left pan (A) */}
          <line x1="62" y1="122" x2="62" y2="168" stroke="#B4834A" strokeWidth="1.6" />
          <line x1="62" y1="122" x2="40" y2="168" stroke="#B4834A" strokeWidth="1.6" />
          <line x1="62" y1="122" x2="84" y2="168" stroke="#B4834A" strokeWidth="1.6" />
          <path d="M 34 168 Q 62 198 90 168 Z" fill="url(#cmpPanGrad)" stroke="#5E3D22" strokeWidth="1.2" />
          <ellipse cx="62" cy="168" rx="28" ry="4" fill="#F5E3B8" opacity="0.55" />

          <g className="ms-cmp-scale-storechip" transform="translate(62, 100)">
            <rect x="-30" y="-13" width="60" height="22" rx="11" fill="#FBF6EE" stroke="#E8DDCC" />
            <text x="0" y="2" textAnchor="middle" className="ms-cmp-scale-chip-text">{labelA}</text>
          </g>

          {phase === 'settled' && winnerSide === 'A' && (
            <g className="ms-cmp-scale-check ms-cmp-scale-check--left">
              <circle cx="86" cy="150" r="11" fill="#E8621C" />
              <path d="M 81 150 L 84.5 153.5 L 91.5 145.5" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </g>
          )}

          {/* right pan (B) */}
          <line x1="258" y1="122" x2="258" y2="168" stroke="#B4834A" strokeWidth="1.6" />
          <line x1="258" y1="122" x2="236" y2="168" stroke="#B4834A" strokeWidth="1.6" />
          <line x1="258" y1="122" x2="280" y2="168" stroke="#B4834A" strokeWidth="1.6" />
          <path d="M 230 168 Q 258 198 286 168 Z" fill="url(#cmpPanGrad)" stroke="#5E3D22" strokeWidth="1.2" />
          <ellipse cx="258" cy="168" rx="28" ry="4" fill="#F5E3B8" opacity="0.55" />

          <g className="ms-cmp-scale-storechip" transform="translate(258, 100)">
            <rect x="-30" y="-13" width="60" height="22" rx="11" fill="#FBF6EE" stroke="#E8DDCC" />
            <text x="0" y="2" textAnchor="middle" className="ms-cmp-scale-chip-text">{labelB}</text>
          </g>

          {phase === 'settled' && winnerSide === 'B' && (
            <g className="ms-cmp-scale-check ms-cmp-scale-check--right">
              <circle cx="282" cy="150" r="11" fill="#E8621C" />
              <path d="M 277 150 L 280.5 153.5 L 287.5 145.5" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </g>
          )}

          {phase === 'settled' && (
            <ellipse
              cx={winnerSide === 'A' ? 62 : 258}
              cy="185"
              rx="34"
              ry="14"
              fill="url(#cmpGlow)"
            />
          )}
        </g>
      </g>
    </svg>
  );
}

// ── One compact comparison row (collapsed = quick glance, expand = full
//    per-site detail with real Buy links, via MedicineComparisonBlock). ──
function ComparisonRow({ entry, siteA, siteB, expanded, onToggle }) {
  const pair = getPair(entry, siteA, siteB);

  return (
    <div className="ms-cmp-compact-card">
      <button type="button" className="ms-cmp-compact-row" onClick={onToggle}>
        <div className="ms-cmp-compact-icon"><LuStore /></div>

        <div className="ms-cmp-compact-name-col">
          <div className="ms-cmp-compact-name">{entry.medicine_name}</div>
          {pair && (
            <div className="ms-cmp-compact-sites">{siteA} vs {siteB}</div>
          )}
        </div>

        {pair ? (
          <>
            <div className="ms-cmp-compact-bars">
              <div className="ms-cmp-compact-bar-track">
                <span
                  className={`ms-cmp-compact-bar ${pair.a.price <= pair.b.price ? 'ms-cmp-compact-bar--low' : 'ms-cmp-compact-bar--high'}`}
                  style={{ width: `${(pair.a.price / pair.higherPrice) * 100}%` }}
                />
                <span className="ms-cmp-compact-bar-price">₹{pair.a.price}</span>
              </div>
              <div className="ms-cmp-compact-bar-track">
                <span
                  className={`ms-cmp-compact-bar ${pair.b.price <= pair.a.price ? 'ms-cmp-compact-bar--low' : 'ms-cmp-compact-bar--high'}`}
                  style={{ width: `${(pair.b.price / pair.higherPrice) * 100}%` }}
                />
                <span className="ms-cmp-compact-bar-price">₹{pair.b.price}</span>
              </div>
            </div>

            <div className="ms-cmp-compact-saved">
              <span className="ms-cmp-compact-saved-amount">₹{pair.diff.toFixed(2)}</span>
              <span className="ms-cmp-compact-saved-label">saved</span>
            </div>

            <div className="ms-cmp-compact-winner-pill">{pair.lowerSite}</div>
          </>
        ) : (
          <div className="ms-cmp-compact-unavailable">Ek ya dono site par nahi mili</div>
        )}

        <LuChevronDown className={`ms-cmp-compact-chevron ${expanded ? 'ms-cmp-compact-chevron--open' : ''}`} />
      </button>

      {expanded && (
        <div className="ms-cmp-compact-detail">
          <MedicineComparisonBlock entry={entry} />
        </div>
      )}
    </div>
  );
}

export default function Compare() {
  const { userId, isLoggedIn } = useUser();

  const [medicineInput, setMedicineInput] = useState('');
  const [medicines, setMedicines] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [comparedAt, setComparedAt] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expandedRows, setExpandedRows] = useState({});

  // ── ALL handlers below are unchanged from the original file, except
  //    handleSearch now also stamps `comparedAt` for the "Live prices from
  //    HH:MM" label — purely cosmetic, no request/response shape touched. ──
  const addMedicine = () => {
    const trimmed = medicineInput.trim();
    if (!trimmed) return;
    if (medicines.includes(trimmed)) {
      setMedicineInput('');
      return;
    }
    setMedicines([...medicines, trimmed]);
    setMedicineInput('');
  };

  const removeMedicine = (name) => {
    setMedicines(medicines.filter((m) => m !== name));
  };

  const handleInputKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addMedicine();
    }
  };

  const handleSearch = async () => {
    if (medicines.length === 0) {
      setError('Kam se kam ek medicine add karo.');
      return;
    }
    if (!isLoggedIn) {
      setError('Pehle login karo.');
      return;
    }

    setLoading(true);
    setError('');
    setComparison(null);
    setExpandedRows({});

    try {
      const res = await fetch('http://localhost:8080/medicine/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ medicines, user_id: userId }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(extractErrorMessage(data.detail, 'Comparison nahi ho saka.'));
      } else {
        setComparison(data);
        setComparedAt(new Date());
      }
    } catch {
      setError('Backend se connect nahi ho pa raha. Backend chalu hai?');
    } finally {
      setLoading(false);
    }
  };

  const toggleRow = (i) => {
    setExpandedRows((prev) => ({ ...prev, [i]: !prev[i] }));
  };

  // ── Derived comparison stats — pure computation from `comparison`, never
  //    mutates it, never touches the request/response shape. ──
  const entries = comparison?.medicines || [];
  const allSiteNames = [...new Set(entries.flatMap((e) => (e.results || []).map((r) => r.site)))];
  const siteA = allSiteNames[0] || '1mg';
  const siteB = allSiteNames[1] || 'Apollo Pharmacy';

  const pairs = entries
    .map((entry) => ({ entry, pair: getPair(entry, siteA, siteB) }))
    .filter((x) => x.pair);

  const winCounts = {};
  pairs.forEach(({ pair }) => {
    winCounts[pair.lowerSite] = (winCounts[pair.lowerSite] || 0) + 1;
  });
  const overallWinnerSite = Object.entries(winCounts).sort((x, y) => y[1] - x[1])[0]?.[0] || null;
  const overallWinCount = overallWinnerSite ? winCounts[overallWinnerSite] : 0;
  const winPercent = pairs.length ? Math.round((overallWinCount / pairs.length) * 100) : 0;
  const totalSavings = pairs.reduce((sum, { pair }) => sum + pair.diff, 0);
  const totalSiteA = pairs.reduce((sum, { pair }) => sum + (pair.a?.price ?? 0), 0);
  const totalSiteB = pairs.reduce((sum, { pair }) => sum + (pair.b?.price ?? 0), 0);

  const hasSettledResult = !loading && pairs.length > 0;
  const scalePhase = loading ? 'loading' : hasSettledResult ? 'settled' : 'idle';
  const winnerSide = overallWinnerSite === siteA ? 'A' : overallWinnerSite === siteB ? 'B' : null;

  return (
    <Layout>
      <div className="ms-compare-page">

        {/* ── Hero: text + animated balance scale + cheapest-overall card ── */}
        <div className="ms-page-header ms-cmp-hero">
          <div className="ms-cmp-hero-left">
            <div className="ms-page-badge ms-cmp-eyebrow">
              <LuScale /> AI Powered Price Comparison
            </div>
            <h1 className="ms-page-title">
              Same medicine,<br />
              <span className="ms-accent ms-cmp-accent">the best price.</span>
            </h1>
            <p className="ms-page-desc">
              We check trusted pharmacies for you — real prices, real delivery estimates.
              We never add anything to a cart on your behalf; every "Buy" link takes you
              straight to the pharmacy's own page so you're always in control.
            </p>

            <div className="ms-cmp-trust-row">
              <span className="ms-cmp-trust-badge"><LuSparkles /> Live Price Check</span>
              <span className="ms-cmp-trust-badge ms-cmp-trust-badge--gold"><LuShieldCheck /> No Auto-Purchase</span>
              <span className="ms-cmp-trust-badge ms-cmp-trust-badge--blue"><LuLock /> You Stay In Control</span>
            </div>
          </div>

          <div className="ms-cmp-hero-scale">
            <BalanceScale phase={scalePhase} winnerSide={winnerSide} labelA={siteA} labelB={siteB} />
            <div className={`ms-cmp-winner-tag ms-cmp-winner-tag--${scalePhase}`}>
              {scalePhase === 'loading' && 'Weighing prices...'}
              {scalePhase === 'idle' && 'Add medicines to begin'}
              {scalePhase === 'settled' && (
                <>
                  <span className="ms-cmp-winner-tag-label">Winner</span>
                  <span className="ms-cmp-winner-tag-name">{overallWinnerSite}</span>
                </>
              )}
            </div>
          </div>

          <div className="ms-cmp-winner-card">
            {hasSettledResult ? (
              <>
                <div className="ms-cmp-winner-card-head">
                  <div>
                    <div className="ms-cmp-winner-card-label">Cheapest overall</div>
                    <div className="ms-cmp-winner-card-name">{overallWinnerSite}</div>
                  </div>
                  <div className="ms-cmp-winner-card-icon"><LuAward /></div>
                </div>
                <div className="ms-cmp-winner-card-sub">
                  Won {overallWinCount} out of {pairs.length} medicines
                </div>
                <div className="ms-cmp-winner-bar-track">
                  <div className="ms-cmp-winner-bar-fill" style={{ width: `${winPercent}%` }} />
                </div>
                <div className="ms-cmp-winner-percent">{winPercent}%</div>

                <div className="ms-cmp-winner-save-box">
                  <div className="ms-cmp-winner-save-label">Total you save</div>
                  <div className="ms-cmp-winner-save-amount">₹{totalSavings.toFixed(2)}</div>
                  <div className="ms-cmp-winner-save-sub">by choosing the right pharmacy</div>
                </div>
              </>
            ) : (
              <div className="ms-cmp-winner-card-placeholder">
                <LuScale />
                <p>Compare karne ke baad yahan cheapest pharmacy aur total savings dikhengi.</p>
              </div>
            )}
          </div>
        </div>

        <div className="ms-section">
          <div className="ms-card ms-cmp-search">
            <div className="ms-cmp-search-head">
              <div className="ms-cmp-search-icon"><LuSearch /></div>
              <div>
                <div className="ms-cmp-search-title">Add medicines to compare</div>
                <div className="ms-cmp-search-sub">Ek ya zyada daal sakte ho, phir sab ek saath compare hongi</div>
              </div>
              <LuSparkles className="ms-cmp-search-sparkle" />
            </div>

            <div className="ms-cmp-input-row">
              <LuSearch className="ms-icon" />
              <input
                type="text"
                placeholder="Medicine ka naam daalo, e.g. Paracetamol 650mg"
                value={medicineInput}
                onChange={(e) => setMedicineInput(e.target.value)}
                onKeyDown={handleInputKeyDown}
              />
              <button
                type="button"
                className="ms-btn-secondary ms-cmp-add-btn"
                onClick={addMedicine}
                disabled={!medicineInput.trim()}
              >
                <LuPlus size={14} /> Add
              </button>
            </div>

            {medicines.length > 0 && (
              <div className="ms-cmp-chips">
                {medicines.map((m) => (
                  <span key={m} className="ms-cmp-chip">
                    {m}
                    <button
                      type="button"
                      className="ms-cmp-chip-remove"
                      onClick={() => removeMedicine(m)}
                      aria-label={`Remove ${m}`}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}

            {!isLoggedIn && (
              <p className="ms-cmp-warn">
                ⚠️ Pehle <a href="/auth">login karo</a> — price comparison ke liye zaruri hai.
              </p>
            )}

            {error && <p className="ms-cmp-error">{error}</p>}

            <button
              type="button"
              className="ms-btn-primary ms-cmp-search-btn"
              onClick={handleSearch}
              disabled={medicines.length === 0 || loading || !isLoggedIn}
            >
              {loading ? (
                <><LuLoader className="ms-cmp-spin" /> Sites check ho rahi hain...</>
              ) : (
                <><LuSearch size={16} /> Compare prices <LuChevronRight size={15} /></>
              )}
            </button>

            {loading && <LoadingProgress />}
          </div>

          {!comparison && !loading && (
            <div className="ms-empty-state ms-cmp-empty">
              <LuScale className="ms-cmp-empty-icon" />
              Medicine add karo aur compare prices dabao — hum {siteA} aur {siteB}
              dono check karenge.
            </div>
          )}

          {comparison && entries.length > 0 && (
            <>
              <div className="ms-cmp-meta-row">
                <div className="ms-cmp-meta-left">
                  <strong>{entries.length}</strong> Medicines
                  {comparedAt && (
                    <>
                      <span className="ms-cmp-meta-dot">·</span>
                      Live prices from {comparedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      <span className="ms-cmp-live-badge"><span className="ms-cmp-live-dot" /> Live</span>
                    </>
                  )}
                </div>
                <div className="ms-cmp-legend">
                  <span><span className="ms-cmp-legend-dot ms-cmp-legend-dot--low" /> Lower price</span>
                  <span><span className="ms-cmp-legend-dot ms-cmp-legend-dot--high" /> Higher price</span>
                </div>
              </div>

              <div className="ms-cmp-all-results">
                {entries.map((entry, i) => (
                  <ComparisonRow
                    key={i}
                    entry={entry}
                    siteA={siteA}
                    siteB={siteB}
                    expanded={!!expandedRows[i]}
                    onToggle={() => toggleRow(i)}
                  />
                ))}
              </div>

              {pairs.length > 0 && (
                <div className="ms-cmp-stats-row">
                  <div className="ms-cmp-stat-card">
                    <div className="ms-cmp-stat-icon"><LuTag /></div>
                    <div>
                      <div className="ms-cmp-stat-label">Total ({siteA})</div>
                      <div className="ms-cmp-stat-value">₹{totalSiteA.toFixed(2)}</div>
                    </div>
                  </div>
                  <div className="ms-cmp-stat-card">
                    <div className="ms-cmp-stat-icon"><LuTag /></div>
                    <div>
                      <div className="ms-cmp-stat-label">Total ({siteB})</div>
                      <div className="ms-cmp-stat-value">₹{totalSiteB.toFixed(2)}</div>
                    </div>
                  </div>
                  <div className="ms-cmp-stat-card ms-cmp-stat-card--accent">
                    <div className="ms-cmp-stat-icon"><LuPiggyBank /></div>
                    <div>
                      <div className="ms-cmp-stat-label">Total Savings</div>
                      <div className="ms-cmp-stat-value">₹{totalSavings.toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          <div className="ms-cmp-footer-strip">
            <div className="ms-cmp-footer-feature">
              <div className="ms-cmp-footer-icon ms-cmp-footer-icon--green"><LuTrendingDown /></div>
              <div>
                <div className="ms-cmp-footer-feature-title">Real-Time Prices</div>
                <div className="ms-cmp-footer-feature-sub">Live scraped from actual pharmacy pages</div>
              </div>
            </div>
            <div className="ms-cmp-footer-feature">
              <div className="ms-cmp-footer-icon ms-cmp-footer-icon--gold"><LuTruck /></div>
              <div>
                <div className="ms-cmp-footer-feature-title">Delivery Estimates</div>
                <div className="ms-cmp-footer-feature-sub">Know when your medicine will arrive</div>
              </div>
            </div>
            <div className="ms-cmp-footer-feature">
              <div className="ms-cmp-footer-icon ms-cmp-footer-icon--blue"><LuShieldCheck /></div>
              <div>
                <div className="ms-cmp-footer-feature-title">No Auto-Purchase</div>
                <div className="ms-cmp-footer-feature-sub">We never add to cart on your behalf</div>
              </div>
            </div>
            <div className="ms-cmp-privacy-card">
              <LuLock />
              <span>Every "Buy" link takes you straight to the pharmacy — you're always in control</span>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}