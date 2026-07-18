import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  LuUpload, LuFileText, LuX, LuLoader, LuTriangleAlert,
  LuCheck, LuShieldCheck, LuFlaskConical, LuChevronDown, LuChevronUp,
  LuBrain, LuLock, LuFolderOpen, LuDroplet, LuDroplets, LuTestTube,
  LuClipboardList, LuActivity, LuHeartPulse, LuChevronRight,
  LuFile, LuHighlighter, LuZoomIn, LuMinus, LuPlus, LuDownload,
  LuSend, LuLeaf, LuArrowRight, LuSun, LuSparkles,
  LuHistory, LuTrendingUp, LuTrendingDown, LuCalendar, LuInfo, LuPill, LuTrash2,
} from 'react-icons/lu';
import Layout from '../components/Layout.jsx';
import { useUser } from '../hooks/useUser';
import './LabReport.css';

// AUTH (D34): every fetch() below that hits a protected endpoint now goes
// through `authFetch` instead — same signature as fetch(url, options), it
// just attaches the Authorization: Bearer <token> header (see useUser.js).
// Several components below don't call useUser() themselves, so `authFetch`
// is threaded down as a prop alongside the existing `userId` prop.

const extractErrorMessage = (detail, fallback) => {
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === 'string' ? d : d?.msg || JSON.stringify(d))).join(', ');
  }
  if (typeof detail === 'object' && detail.msg) return detail.msg;
  return fallback;
};

const STATUS_CONFIG = {
  'Normal':        { color: 'green',  label: 'Normal' },
  'Low':           { color: 'yellow', label: 'Low' },
  'High':          { color: 'yellow', label: 'High' },
  'Critical Low':  { color: 'red',    label: 'Critical Low' },
  'Critical High': { color: 'red',    label: 'Critical High' },
  'Unknown':       { color: 'grey',   label: 'Unknown' },
};

const URGENCY_RANK = { 'Critical Low': 0, 'Critical High': 0, 'Low': 1, 'High': 1, 'Unknown': 2, 'Normal': 3 };

const ACTION_CONFIG = {
  'No action needed':                { icon: '✓',  color: 'green' },
  'Mention to doctor at next visit': { icon: '→',  color: 'yellow' },
  'Consult doctor soon':             { icon: '!',  color: 'orange' },
  'Seek care today':                 { icon: '!!', color: 'red' },
};

const ANALYZE_TYPES = [
  { label: 'Blood Tests', icon: <LuDroplet />, tone: 'red' },
  { label: 'Urine Tests', icon: <LuTestTube />, tone: 'amber' },
  { label: 'Health Checkups', icon: <LuClipboardList />, tone: 'purple' },
  { label: 'Thyroid Profiles', icon: <LuActivity />, tone: 'green' },
  { label: 'Diabetes Tests', icon: <LuDroplets />, tone: 'blue' },
  { label: 'Lipid Profiles', icon: <LuHeartPulse />, tone: 'orange' },
];

function LabHeroIllustration() {
  return (
    <svg
      className="ms-lr-hero-illustration-svg"
      viewBox="0 0 240 220"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <g transform="rotate(-6 100 105)">
        <rect x="48" y="30" width="104" height="144" rx="6" fill="#FFFFFF" stroke="var(--ms-soft-gold)" strokeWidth="1.25" />
        <rect x="62" y="46" width="46" height="6" rx="3" fill="var(--ms-luxury-brown)" opacity="0.4" />
        <line x1="62" y1="66" x2="136" y2="66" stroke="var(--ms-soft-gold)" strokeWidth="1.5" strokeLinecap="round" opacity="0.7" />
        <line x1="62" y1="80" x2="136" y2="80" stroke="var(--ms-soft-gold)" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
        <line x1="62" y1="94" x2="116" y2="94" stroke="var(--ms-soft-gold)" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
        <line x1="62" y1="112" x2="136" y2="112" stroke="var(--lr-green, #2E7D4F)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
        <line x1="62" y1="126" x2="106" y2="126" stroke="var(--ms-soft-gold)" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
      </g>
      <path
        d="M188 36c6 8 5 20-4 26-2-10 0-19 4-26Z"
        fill="var(--lr-green, #2E7D4F)"
        opacity="0.4"
      />
      <circle cx="150" cy="118" r="38" fill="rgba(156,107,69,0.06)" stroke="var(--ms-luxury-brown)" strokeWidth="2.5" />
      <path
        d="M136 118c0-7 6-13 13-13"
        stroke="var(--ms-soft-gold)"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.8"
      />
      <line x1="176" y1="144" x2="198" y2="166" stroke="var(--ms-luxury-brown)" strokeWidth="5" strokeLinecap="round" />
    </svg>
  );
}

function pickNoteIcon(name = '') {
  const n = name.toLowerCase();
  if (n.includes('hemoglobin') || n.includes('blood') || n.includes('rbc') || n.includes('platelet') || n.includes('wbc')) {
    return <LuDroplet />;
  }
  if (n.includes('vitamin d')) return <LuSun />;
  if (n.includes('sgpt') || n.includes('sgot') || n.includes('liver') || n.includes('alt') || n.includes('ast')) {
    return <LuFlaskConical />;
  }
  if (n.includes('sugar') || n.includes('glucose') || n.includes('hba1c')) return <LuDroplets />;
  if (n.includes('thyroid') || n.includes('tsh')) return <LuActivity />;
  if (n.includes('cholesterol') || n.includes('lipid') || n.includes('hdl') || n.includes('ldl') || n.includes('triglyceride')) {
    return <LuHeartPulse />;
  }
  if (n.includes('creatinine') || n.includes('kidney') || n.includes('urea')) return <LuTestTube />;
  return <LuClipboardList />;
}

function TestResultCard({ test }) {
  const [expanded, setExpanded] = useState(false);
  const statusCfg = STATUS_CONFIG[test.status] || { color: 'grey', label: test.status };
  const actionCfg = ACTION_CONFIG[test.action_needed] || { icon: '→', color: 'grey' };
  const isCritical = test.status === 'Critical Low' || test.status === 'Critical High';

  return (
    <div className={`ms-lr-test-card ${isCritical ? 'ms-lr-test-card--critical' : ''}`}>
      <div className="ms-lr-test-header" onClick={() => setExpanded(v => !v)}>
        <div className="ms-lr-test-left">
          <span className={`ms-lr-status-dot ms-lr-status-dot--${statusCfg.color}`} />
          <span className="ms-lr-test-name">{test.test_name}</span>
          <span className={`ms-lr-status-badge ms-lr-status-badge--${statusCfg.color}`}>
            {statusCfg.label}
          </span>
        </div>
        <div className="ms-lr-test-right">
          <span className="ms-lr-test-value">{test.value}</span>
          {test.normal_range && test.normal_range !== 'Not provided' && (
            <span className="ms-lr-test-range">({test.normal_range})</span>
          )}
          {expanded ? <LuChevronUp size={16} /> : <LuChevronDown size={16} />}
        </div>
      </div>

      {expanded && (
        <div className="ms-lr-test-body">
          <p className="ms-lr-test-explanation">{test.plain_explanation}</p>
          {test.action_needed && (
            <div className={`ms-lr-action ms-lr-action--${actionCfg.color}`}>
              <span className="ms-lr-action-icon">{actionCfg.icon}</span>
              <span>{test.action_needed}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function LabAnalysisResult({ analysis, rawText, userId, onSaved, authFetch }) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState('');

  if (!analysis || !analysis.overall_summary) return null;

  const handleSave = async () => {
    setSaving(true);
    setSaveError('');
    try {
      const payload = {
        user_id: userId,
        report_type: analysis.report_type || 'Unknown',
        overall_summary: analysis.overall_summary,
        tests: analysis.tests || [],
        urgent_flags: analysis.urgent_flags || [],
        has_urgent_values: !!analysis.has_urgent_values,
        next_steps: analysis.next_steps || '',
        disclaimer: analysis.disclaimer || '',
        raw_text: rawText || '',
        report_date: analysis.report_date || '',
      };
      const res = await authFetch('http://localhost:8080/lab/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setSaveError(extractErrorMessage(data.detail, 'Save nahi hua.'));
      } else {
        setSaved(true);
        onSaved?.();
      }
    } catch {
      setSaveError('Backend se connect nahi ho pa raha.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="ms-lr-result">
      <div className="ms-lr-report-type">
        <LuFlaskConical size={16} />
        <span>{analysis.report_type}</span>
      </div>

      {analysis.has_urgent_values && (
        <div className="ms-lr-urgent-banner">
          <LuTriangleAlert size={18} />
          <div>
            <strong>Critical values mili hain:</strong>{' '}
            {(analysis.urgent_flags || []).join(', ')} — please doctor se aaj hi baat karo.
          </div>
        </div>
      )}

      <div className="ms-lr-summary-box">
        <div className="ms-lr-section-label">Overall Summary</div>
        <p>{analysis.overall_summary}</p>
      </div>

      <div className="ms-lr-section-label" style={{ marginTop: '1rem' }}>
        Test Results ({(analysis.tests || []).length})
      </div>
      <div className="ms-lr-tests-list">
        {(analysis.tests || []).map((test, i) => (
          <TestResultCard key={i} test={test} />
        ))}
      </div>

      {analysis.next_steps && (
        <div className="ms-lr-next-steps">
          <div className="ms-lr-section-label">Aage Kya Karein</div>
          <p>{analysis.next_steps}</p>
        </div>
      )}

      {analysis.disclaimer && (
        <div className="ms-lr-disclaimer">
          <LuShieldCheck size={15} />
          <span>{analysis.disclaimer}</span>
        </div>
      )}

      <div className="ms-lr-save-row">
        {saveError && <p className="ms-lr-error">{saveError}</p>}
        {saved ? (
          <span className="ms-lr-saved-chip">
            <LuCheck size={14} /> Records mein save ho gaya
          </span>
        ) : (
          <button
            type="button"
            className="ms-btn-secondary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving
              ? <><LuLoader className="ms-lr-spin" /> Save ho raha hai...</>
              : 'Apne records mein save karo'
            }
          </button>
        )}
      </div>
    </div>
  );
}

const formatShortDate = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
};

const formatFullDate = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
};

function buildTrendInsight(trend) {
  const chain = trend.points.map((p) => p.value).join(' → ');
  const latest = trend.latest_status;
  let verdict;
  if (latest === 'Normal') {
    const wasEverAbnormal = trend.points.some((p) => p.status !== 'Normal');
    verdict = wasEverAbnormal
      ? "it's now back within the normal range."
      : "it's been staying within the normal range.";
  } else if (latest === 'Critical Low' || latest === 'Critical High') {
    verdict = "it's currently at a critical level — please talk to your doctor about this soon.";
  } else if (latest === 'Low' || latest === 'High') {
    verdict = trend.trend_direction === (latest === 'Low' ? 'up' : 'down')
      ? "it's moving in the right direction, but still worth mentioning to your doctor."
      : `it's currently ${latest.toLowerCase()} — worth keeping an eye on.`;
  } else {
    verdict = 'keep tracking this alongside your doctor.';
  }
  return `${chain} — ${verdict}`;
}

const DOT_COLORS = { green: '#2E7D4F', yellow: '#B7791F', red: '#C0392B', grey: '#999', orange: '#D35400' };
const ANNOTATION_COLOR = '#D35400';
const MAX_RENDERED_ANNOTATIONS = 3;

function annotationXPosition(coords, startDateIso) {
  if (!coords.length) return null;
  const startTime = new Date(startDateIso).getTime();
  if (Number.isNaN(startTime)) return null;

  if (startTime <= new Date(coords[0].date).getTime()) return coords[0].x;
  if (startTime >= new Date(coords[coords.length - 1].date).getTime()) return coords[coords.length - 1].x;

  for (let i = 0; i < coords.length - 1; i++) {
    const t1 = new Date(coords[i].date).getTime();
    const t2 = new Date(coords[i + 1].date).getTime();
    if (startTime >= t1 && startTime <= t2) {
      const frac = t2 === t1 ? 0 : (startTime - t1) / (t2 - t1);
      return coords[i].x + frac * (coords[i + 1].x - coords[i].x);
    }
  }
  return coords[coords.length - 1].x;
}

function dedupeAnnotations(annotations = []) {
  const seen = new Set();
  const out = [];
  for (const a of annotations) {
    const key = `${a.medicine_name}|${a.start_date}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(a);
  }
  return out;
}

function buildDeltaBadge(annotation, numericPoints) {
  const startTime = new Date(annotation.start_date).getTime();
  if (Number.isNaN(startTime)) return null;

  const afterStart = numericPoints.filter((p) => new Date(p.date).getTime() >= startTime);
  if (afterStart.length < 1) return null;

  const beforePoints = numericPoints.filter((p) => new Date(p.date).getTime() < startTime);
  const baseline = beforePoints.length ? beforePoints[beforePoints.length - 1] : afterStart[0];
  const latest = numericPoints[numericPoints.length - 1];

  if (baseline.numeric_value === latest.numeric_value && afterStart.length < 2) {
    if (beforePoints.length === 0) return null;
  }

  const delta = latest.numeric_value - baseline.numeric_value;
  const rankBefore = URGENCY_RANK[baseline.status] ?? 2;
  const rankLatest = URGENCY_RANK[latest.status] ?? 2;
  const improving = rankLatest > rankBefore || (rankLatest === rankBefore && rankLatest === 3);

  return {
    medicineName: annotation.medicine_name,
    fromValue: baseline.value,
    toValue: latest.value,
    delta,
    improving,
    unchanged: delta === 0,
  };
}

function TestTrendChart({ trend }) {
  const width = 560;
  const height = 150;
  const padX = 26;
  const padY = 22;
  const topMargin = 20;
  const points = trend.points;

  const numericPoints = points.filter((p) => typeof p.numeric_value === 'number');

  if (numericPoints.length < 2) {
    return (
      <div className="ms-lr-trend-fallback">
        {points.map((p, i) => {
          const cfg = STATUS_CONFIG[p.status] || { color: 'grey', label: p.status };
          return (
            <div key={i} className="ms-lr-trend-fallback-item">
              <span className={`ms-lr-status-badge ms-lr-status-badge--${cfg.color}`}>{p.value || '—'}</span>
              <span className="ms-lr-trend-fallback-date">{formatShortDate(p.date)}</span>
            </div>
          );
        })}
      </div>
    );
  }

  const values = numericPoints.map((p) => p.numeric_value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || Math.abs(max) || 1;
  const lo = min - range * 0.15;
  const hi = max + range * 0.15;
  const span = hi - lo || 1;

  const plotTop = padY + topMargin;

  const coords = points.map((p, i) => {
    const x = padX + (i * (width - 2 * padX)) / Math.max(points.length - 1, 1);
    const v = typeof p.numeric_value === 'number' ? p.numeric_value : lo;
    const y = height - padY - ((v - lo) / span) * (height - plotTop - padY);
    return { x, y, ...p };
  });

  const linePath = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`).join(' ');
  const areaPath = `${linePath} L ${coords[coords.length - 1].x.toFixed(1)} ${(height - padY).toFixed(1)} L ${coords[0].x.toFixed(1)} ${(height - padY).toFixed(1)} Z`;
  const gradientId = `ms-lr-trend-grad-${(trend.test_name || 'x').replace(/[^a-zA-Z0-9]/g, '')}`;

  const annotations = dedupeAnnotations(trend.annotations).slice(0, MAX_RENDERED_ANNOTATIONS);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="ms-lr-trend-svg" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--ms-soft-gold)" stopOpacity="0.28" />
          <stop offset="100%" stopColor="var(--ms-soft-gold)" stopOpacity="0" />
        </linearGradient>
      </defs>

      <path d={areaPath} fill={`url(#${gradientId})`} stroke="none" />

      {annotations.map((a, i) => {
        const x = annotationXPosition(coords, a.start_date);
        if (x === null) return null;
        const anchor = i === 0 ? 'start' : 'middle';
        const labelX = i === 0 ? Math.min(x + 4, width - 100) : x;
        return (
          <g key={`${a.medicine_name}-${a.start_date}`} className="ms-lr-trend-annotation">
            <line
              x1={x} y1={plotTop - 6} x2={x} y2={height - padY}
              stroke={ANNOTATION_COLOR}
              strokeWidth="1.5"
              strokeDasharray="4 3"
              opacity="0.8"
            />
            <text
              x={labelX}
              y={plotTop - 10}
              textAnchor={anchor}
              className="ms-lr-trend-annotation-label"
            >
              {a.medicine_name}
            </text>
          </g>
        );
      })}

      <path d={linePath} fill="none" stroke="var(--ms-soft-gold)" strokeWidth="2.25" strokeLinejoin="round" strokeLinecap="round" />

      {coords.map((c, i) => {
        const cfg = STATUS_CONFIG[c.status] || { color: 'grey' };
        const isEndpoint = i === coords.length - 1;
        return (
          <g key={i}>
            <circle
              cx={c.x} cy={c.y}
              r={isEndpoint ? 6.5 : 5.5}
              fill={DOT_COLORS[cfg.color] || '#999'}
              stroke="#fff"
              strokeWidth={isEndpoint ? 2 : 1.5}
            />
            <text x={c.x} y={height - 4} textAnchor="middle" className="ms-lr-trend-axis-label">
              {formatShortDate(c.date)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function TrendDeltaBadges({ trend }) {
  const numericPoints = trend.points.filter((p) => typeof p.numeric_value === 'number');
  const annotations = dedupeAnnotations(trend.annotations);
  if (!annotations.length || numericPoints.length < 2) return null;

  const badges = annotations
    .map((a) => buildDeltaBadge(a, numericPoints))
    .filter(Boolean);

  if (!badges.length) return null;

  return (
    <div className="ms-lr-delta-badge-row">
      {badges.map((b, i) => {
        const Icon = b.unchanged ? null : (b.improving ? LuTrendingUp : LuTrendingDown);
        const tone = b.unchanged ? 'grey' : (b.improving ? 'green' : 'yellow');
        return (
          <div key={i} className={`ms-lr-delta-badge ms-lr-delta-badge--${tone}`}>
            <LuPill size={12} />
            <span className="ms-lr-delta-badge-text">
              Since <strong>{b.medicineName}</strong>: {b.fromValue} → {b.toValue}
            </span>
            {Icon && <Icon size={13} />}
          </div>
        );
      })}
    </div>
  );
}

const PACE_TONE = {
  'On track': 'green',
  'Too early to tell': 'grey',
  'Slower than typical, still within expected window': 'yellow',
  'Not responding as expected': 'red',
};

function EffectivenessCard({ userId, testName, normalRange, annotation, numericPoints, authFetch }) {
  const [loading, setLoading] = useState(false);
  const [checked, setChecked] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleCheck = async () => {
    setLoading(true);
    setError('');
    try {
      const payload = {
        user_id: userId,
        medicine_name: annotation.medicine_name,
        test_name: testName,
        start_date: annotation.start_date,
        points: numericPoints.map((p) => ({
          date: p.date,
          value: p.value,
          numeric_value: p.numeric_value,
          status: p.status,
        })),
        normal_range: normalRange || '',
      };
      const res = await authFetch('http://localhost:8080/medicine/effectiveness', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(extractErrorMessage(data.detail, 'Pace check nahi ho paya.'));
      } else {
        setResult(data.effectiveness || null);
      }
    } catch {
      setError('Backend se connect nahi ho pa raha.');
    } finally {
      setLoading(false);
      setChecked(true);
    }
  };

  if (!checked) {
    return (
      <button
        type="button"
        className="ms-lr-effectiveness-check-btn"
        onClick={handleCheck}
        disabled={loading}
      >
        {loading
          ? <><LuLoader className="ms-lr-spin" size={13} /> Checking pace...</>
          : <><LuBrain size={13} /> Check {annotation.medicine_name}'s response pace</>
        }
      </button>
    );
  }

  if (error) {
    return (
      <div className="ms-lr-effectiveness-card ms-lr-effectiveness-card--error">
        <p className="ms-lr-error">{error}</p>
        <button
          type="button"
          className="ms-lr-effectiveness-check-btn"
          onClick={() => { setChecked(false); }}
        >
          Try again
        </button>
      </div>
    );
  }

  if (!result || !result.pace_verdict) return null;

  const tone = PACE_TONE[result.pace_verdict] || 'grey';

  return (
    <div className={`ms-lr-effectiveness-card ms-lr-effectiveness-card--${tone}`}>
      <div className="ms-lr-effectiveness-head">
        <LuBrain size={14} />
        <span className="ms-lr-effectiveness-medicine">{annotation.medicine_name}</span>
        <span className={`ms-lr-effectiveness-verdict ms-lr-effectiveness-verdict--${tone}`}>
          {result.pace_verdict}
        </span>
      </div>
      <p className="ms-lr-effectiveness-explanation">{result.plain_explanation}</p>
      {result.doctor_talk_recommended && (
        <div className="ms-lr-effectiveness-doctor-flag">
          <LuTriangleAlert size={13} /> Doctor se agli visit mein iska zikr karna worth hai.
        </div>
      )}
      {result.disclaimer && (
        <div className="ms-lr-disclaimer">
          <LuShieldCheck size={13} />
          <span>{result.disclaimer}</span>
        </div>
      )}
    </div>
  );
}

function TrendCard({ trend, userId, authFetch }) {
  const cfg = STATUS_CONFIG[trend.latest_status] || { color: 'grey', label: trend.latest_status };
  const TrendIcon = trend.trend_direction === 'up' ? LuTrendingUp : trend.trend_direction === 'down' ? LuTrendingDown : null;

  const numericPoints = trend.points.filter((p) => typeof p.numeric_value === 'number');
  const annotations = dedupeAnnotations(trend.annotations);
  const showEffectivenessRow = annotations.length > 0 && numericPoints.length >= 2;

  return (
    <div className="ms-lr-trend-card">
      <div className="ms-lr-trend-card-head">
        <div className="ms-lr-trend-card-title">
          {pickNoteIcon(trend.test_name)}
          <span>{trend.test_name}</span>
        </div>
        <div className="ms-lr-trend-card-right">
          {TrendIcon && <TrendIcon size={15} className={`ms-lr-trend-arrow ms-lr-trend-arrow--${trend.trend_direction}`} />}
          <span className={`ms-lr-status-badge ms-lr-status-badge--${cfg.color}`}>{cfg.label}</span>
        </div>
      </div>

      <TrendDeltaBadges trend={trend} />

      <TestTrendChart trend={trend} />

      <p className="ms-lr-trend-insight">{buildTrendInsight(trend)}</p>

      {showEffectivenessRow && (
        <div className="ms-lr-effectiveness-row">
          {annotations.map((a) => (
            <EffectivenessCard
              key={`${a.medicine_name}-${a.start_date}`}
              userId={userId}
              testName={trend.test_name}
              normalRange={trend.latest_normal_range}
              annotation={a}
              numericPoints={numericPoints}
              authFetch={authFetch}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function PastReportItem({ report, userId, onDeleted, authFetch }) {
  const [open, setOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  const tests = report.tests || [];
  const abnormal = tests.filter((t) => t.status === 'Critical Low' || t.status === 'Critical High').length;
  const attention = tests.filter((t) => t.status === 'Low' || t.status === 'High').length;

  const handleDeleteClick = (e) => {
    e.stopPropagation();
    setConfirming(true);
    setConfirmText('');
    setDeleteError('');
  };

  const handleCancelDelete = (e) => {
    e.stopPropagation();
    setConfirming(false);
    setConfirmText('');
    setDeleteError('');
  };

  const handleConfirmDelete = async (e) => {
    e.stopPropagation();
    if (confirmText !== 'DELETE' || deleting) return;
    setDeleting(true);
    setDeleteError('');
    try {
      const res = await authFetch(`http://localhost:8080/lab/analyses/${userId}/${report._id}`, {
        method: 'DELETE',
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setDeleteError(extractErrorMessage(data.detail, 'Delete nahi ho paya.'));
        setDeleting(false);
        return;
      }
      onDeleted?.(report._id);
    } catch {
      setDeleteError('Backend se connect nahi ho pa raha.');
      setDeleting(false);
    }
  };

  return (
    <div className="ms-lr-past-report">
      <button type="button" className="ms-lr-past-report-head" onClick={() => setOpen((v) => !v)}>
        <div className="ms-lr-past-report-left">
          <LuCalendar size={15} />
          <span className="ms-lr-past-report-date">{formatFullDate(report.date)}</span>
          <span className="ms-lr-past-report-type">{report.report_type}</span>
        </div>
        <div className="ms-lr-past-report-right">
          {abnormal > 0 && <span className="ms-lr-status-badge ms-lr-status-badge--red">{abnormal} critical</span>}
          {attention > 0 && <span className="ms-lr-status-badge ms-lr-status-badge--yellow">{attention} to watch</span>}
          {abnormal === 0 && attention === 0 && <span className="ms-lr-status-badge ms-lr-status-badge--green">All normal</span>}
          <span
            role="button"
            tabIndex={0}
            className="ms-lr-past-report-delete-btn"
            title="Delete this report"
            onClick={handleDeleteClick}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleDeleteClick(e); }}
          >
            <LuTrash2 size={15} />
          </span>
          {open ? <LuChevronUp size={15} /> : <LuChevronDown size={15} />}
        </div>
      </button>

      {confirming && (
        <div className="ms-lr-delete-confirm" onClick={(e) => e.stopPropagation()}>
          <p className="ms-lr-delete-confirm-text">
            Is report ko permanently delete karna hai? Health Trends chart se bhi iska data hat jayega.
            Confirm karne ke liye neeche <strong>DELETE</strong> type karo.
          </p>
          <div className="ms-lr-delete-confirm-row">
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder="DELETE"
              autoFocus
              disabled={deleting}
            />
            <button type="button" className="ms-btn-secondary" onClick={handleCancelDelete} disabled={deleting}>
              Cancel
            </button>
            <button
              type="button"
              className="ms-lr-delete-confirm-btn"
              onClick={handleConfirmDelete}
              disabled={confirmText !== 'DELETE' || deleting}
            >
              {deleting
                ? <><LuLoader className="ms-lr-spin" size={14} /> Deleting...</>
                : <><LuTrash2 size={14} /> Delete Permanently</>
              }
            </button>
          </div>
          {deleteError && <p className="ms-lr-error">{deleteError}</p>}
        </div>
      )}

      {open && (
        <div className="ms-lr-past-report-body">
          <p className="ms-lr-past-report-summary">{report.overall_summary}</p>
          <div className="ms-lr-past-report-tests">
            {tests.map((t, i) => (
              <div key={i} className="ms-lr-past-report-test-row">
                <span className={`ms-lr-status-dot ms-lr-status-dot--${(STATUS_CONFIG[t.status] || {}).color || 'grey'}`} />
                <span className="ms-lr-past-report-test-name">{t.test_name}</span>
                <span className="ms-lr-past-report-test-value">{t.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function HealthHistorySection({ userId, isLoggedIn, refreshKey, authFetch }) {
  const [reports, setReports] = useState([]);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isLoggedIn || !userId) return;

    let cancelled = false;
    setLoading(true);
    setError('');

    Promise.all([
      authFetch(`http://localhost:8080/lab/analyses/${userId}`).then((r) => r.json()),
      authFetch(`http://localhost:8080/health/trends-annotated/${userId}`).then((r) => r.json()),
    ])
      .then(([analysesData, trendsData]) => {
        if (cancelled) return;
        setReports(analysesData.analyses || []);
        setTrends(trendsData.trends || []);
      })
      .catch(() => {
        if (!cancelled) setError('History load nahi ho payi. Backend chal raha hai?');
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
          setLoaded(true);
        }
      });

    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, isLoggedIn, refreshKey]);

  const handleReportDeleted = useCallback((deletedId) => {
    setReports((prev) => prev.filter((r) => r._id !== deletedId));
    authFetch(`http://localhost:8080/health/trends-annotated/${userId}`)
      .then((r) => r.json())
      .then((data) => setTrends(data.trends || []))
      .catch(() => {
        // Non-fatal — the report list itself already reflects the delete.
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  if (!isLoggedIn) return null;

  return (
    <div className="ms-lr-history-section">
      <div className="ms-lr-panel-heading">
        <LuHistory size={18} /> Your Health History &amp; Trends
      </div>

      {loading && (
        <div className="ms-lr-notes-loading">
          <div className="ms-spinner" />
          <p>Past reports load ho rahe hain...</p>
        </div>
      )}

      {error && <p className="ms-lr-error">{error}</p>}

      {!loading && loaded && reports.length === 0 && !error && (
        <div className="ms-lr-notes-empty">
          <LuFolderOpen size={22} />
          <p>Abhi tak koi report save nahi hui. Ek report analyse karo aur "Apne records mein save karo" dabao — agli baar yahan history aur trends dikhenge.</p>
        </div>
      )}

      {!loading && trends.length > 0 && (
        <div className="ms-lr-trends-block">
          <div className="ms-lr-history-subheading">
            <LuInfo size={14} />
            <span>Tests jo 2 ya zyada reports mein repeat hue hain — dekho kya improve ho raha hai, kya nahi</span>
          </div>
          <div className="ms-lr-trends-grid">
            {trends.map((t) => <TrendCard key={t.test_name} trend={t} userId={userId} authFetch={authFetch} />)}
          </div>
        </div>
      )}

      {!loading && reports.length > 0 && (
        <div className="ms-lr-past-reports-block">
          <div className="ms-lr-history-subheading">
            <LuFileText size={14} />
            <span>All saved reports ({reports.length})</span>
          </div>
          <div className="ms-lr-past-reports-list">
            {reports.map((r) => (
              <PastReportItem key={r._id || r.date} report={r} userId={userId} onDeleted={handleReportDeleted} authFetch={authFetch} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function LabReport() {
  const { userId, isLoggedIn, authFetch } = useUser();

  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [previewUrl, setPreviewUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [rawText, setRawText] = useState('');
  const [zoom, setZoom] = useState(100);
  const [showFullBreakdown, setShowFullBreakdown] = useState(false);
  const [question, setQuestion] = useState('');
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);
  const workspaceRef = useRef(null);

  const handleReportSaved = () => setHistoryRefreshKey((k) => k + 1);

  const isPdf = file?.type === 'application/pdf';

  useEffect(() => {
    if (!file) {
      setPreviewUrl('');
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const handleFileChange = (e) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setFileName(f.name);
      setAnalysis(null);
      setRawText('');
      setError('');
      setZoom(100);
      setShowFullBreakdown(false);
    }
  };

  const handleRemoveFile = (e) => {
    e.preventDefault();
    setFile(null);
    setFileName('');
    setAnalysis(null);
    setRawText('');
    setError('');
  };

  const handleAnalyse = async () => {
    if (!file) return;
    if (!isLoggedIn) {
      setError('Pehle login karo.');
      return;
    }
    setLoading(true);
    setError('');
    setAnalysis(null);
    setRawText('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', userId);

      const res = await authFetch('http://localhost:8080/lab/analyse', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        setError(extractErrorMessage(data.detail, 'Lab report analyse nahi ho saki.'));
      } else {
        setAnalysis(data.analysis || null);
        setRawText(data.report_text || '');
      }
    } catch {
      setError('Backend se connect nahi ho pa raha. Backend chal raha hai?');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadSummary = () => {
    if (!analysis) return;
    const lines = [
      `MediSarthi — Lab Report Summary`,
      `Report type: ${analysis.report_type || 'Unknown'}`,
      ``,
      `Overall Summary`,
      analysis.overall_summary || '',
      ``,
      `Test Results`,
      ...(analysis.tests || []).map(
        (t) => `- ${t.test_name}: ${t.value} (${t.status}${t.normal_range ? `, range ${t.normal_range}` : ''})`
      ),
      ``,
      analysis.next_steps ? `Next steps\n${analysis.next_steps}` : '',
      analysis.disclaimer ? `\nDisclaimer\n${analysis.disclaimer}` : '',
    ].join('\n');

    const blob = new Blob([lines], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `MediSarthi-lab-summary-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const tests = analysis?.tests || [];
  const abnormalCount = tests.filter(t => t.status === 'Critical Low' || t.status === 'Critical High').length;
  const attentionCount = tests.filter(t => t.status === 'Low' || t.status === 'High').length;
  const normalCount = tests.filter(t => t.status === 'Normal').length;

  const flaggedTests = tests.filter(t => t.status !== 'Normal').slice(0, 4);
  const restNormalCount = tests.length - flaggedTests.length;

  return (
    <Layout>
      <div className="ms-labreport-page">

        <div className="ms-page-header ms-lr-hero">
          <div className="ms-lr-hero-left">
            <div className="ms-lr-page-badge"><LuSparkles size={12} /> AI Powered Insights</div>
            <h1 className="ms-page-title">
              Understand your report,<br />
              <span className="ms-lr-accent">not just the numbers.</span>
            </h1>
            <p className="ms-page-subtitle">
              Upload a photo or scan of any blood test, urine report, or health check —
              our AI reads every value, explains what it means in plain language, and flags
              anything that needs your attention.
            </p>

            <div className="ms-lr-trust-row">
              <div className="ms-lr-trust-item">
                <div className="ms-lr-trust-icon"><LuBrain /></div>
                <div>
                  <div className="ms-lr-trust-title">AI-Powered</div>
                  <div className="ms-lr-trust-sub">Smart Analysis</div>
                </div>
              </div>
              <div className="ms-lr-trust-item">
                <div className="ms-lr-trust-icon"><LuShieldCheck /></div>
                <div>
                  <div className="ms-lr-trust-title">100% Secure</div>
                  <div className="ms-lr-trust-sub">Your data is private</div>
                </div>
              </div>
              <div className="ms-lr-trust-item">
                <div className="ms-lr-trust-icon"><LuFileText /></div>
                <div>
                  <div className="ms-lr-trust-title">Easy to Understand</div>
                  <div className="ms-lr-trust-sub">Results in plain language</div>
                </div>
              </div>
            </div>
          </div>

          <div className="ms-lr-hero-illustration">
            <LabHeroIllustration />
          </div>

          <div className="ms-lr-hero-right">
            <div className="ms-lr-hero-blob ms-lr-hero-blob--1" />
            <div className="ms-lr-hero-blob ms-lr-hero-blob--2" />

            <div className={`ms-lr-upload-panel ${fileName ? 'ms-lr-upload-panel--selected' : ''}`}>
              <input
                id="ms-lr-file-input"
                type="file"
                accept="image/*,.pdf"
                onChange={handleFileChange}
                hidden
              />

              {!fileName ? (
                <>
                  <div className="ms-lr-upload-icon"><LuUpload size={26} /></div>
                  <div className="ms-lr-upload-title">Upload your lab report</div>
                  <div className="ms-lr-upload-sub">PDF, JPG or PNG (Max 10MB)</div>
                  <label htmlFor="ms-lr-file-input" className="ms-btn-primary ms-lr-upload-choose">
                    <LuFolderOpen size={15} /> Choose File
                  </label>
                </>
              ) : (
                <>
                  <span className="ms-lr-file-chip ms-lr-file-chip--panel">
                    <LuFileText size={14} />
                    <span>{fileName}</span>
                    <button type="button" className="ms-lr-file-remove" onClick={handleRemoveFile}>
                      <LuX size={12} />
                    </button>
                  </span>

                  <button
                    type="button"
                    className="ms-btn-primary ms-lr-upload-choose"
                    disabled={loading || !isLoggedIn}
                    onClick={handleAnalyse}
                  >
                    {loading
                      ? <><LuLoader className="ms-lr-spin" size={16} /> Analysing...</>
                      : <><LuFlaskConical size={16} /> Analyse Report <LuChevronRight size={15} /></>
                    }
                  </button>
                </>
              )}

              {!isLoggedIn && fileName && (
                <p className="ms-lr-warn">
                  ⚠️ Pehle <a href="/auth">login karo</a> — analysis ke liye zaruri hai.
                </p>
              )}
              {error && <p className="ms-lr-error">{error}</p>}

              <div className="ms-lr-upload-secure">
                <LuShieldCheck size={13} /> Your data is 100% secure &amp; private
              </div>
            </div>
          </div>
        </div>

        <div className="ms-lr-content">

          {fileName && (
            <div className="ms-lr-workspace" ref={workspaceRef}>
              <div className="ms-card ms-lr-viewer-card">
                <div className="ms-lr-panel-heading">
                  <span className="ms-lr-panel-num">1</span> Your Report
                </div>

                <div className="ms-lr-viewer-body">
                  <div className="ms-lr-viewer-tabs">
                    <button type="button" className="ms-lr-viewer-tab active" title="Page">
                      <LuFile size={16} /><span>Page</span>
                    </button>
                    <button type="button" className="ms-lr-viewer-tab" disabled title="Coming soon">
                      <LuHighlighter size={16} /><span>Highlights</span>
                    </button>
                    <button type="button" className="ms-lr-viewer-tab" title="Zoom">
                      <LuZoomIn size={16} /><span>Zoom</span>
                    </button>
                  </div>

                  <div className="ms-lr-viewer-main">
                    <div className="ms-lr-viewer-toolbar">
                      <span className="ms-lr-viewer-filename" title={fileName}>
                        <LuFileText size={14} /> {fileName}
                      </span>
                      <div className="ms-lr-zoom-controls">
                        <button type="button" onClick={() => setZoom(z => Math.max(50, z - 25))}>
                          <LuMinus size={13} />
                        </button>
                        <span>{zoom}%</span>
                        <button type="button" onClick={() => setZoom(z => Math.min(200, z + 25))}>
                          <LuPlus size={13} />
                        </button>
                      </div>
                      {previewUrl && (
                        <a
                          href={previewUrl}
                          download={fileName}
                          className="ms-lr-viewer-download"
                          title="Download original file"
                        >
                          <LuDownload size={15} />
                        </a>
                      )}
                    </div>

                    <div className="ms-lr-viewer-frame">
                      {!previewUrl ? (
                        <div className="ms-lr-viewer-placeholder">
                          <LuFileText size={30} />
                        </div>
                      ) : isPdf ? (
                        <iframe
                          className="ms-lr-viewer-pdf"
                          title="Lab report preview"
                          src={`${previewUrl}#zoom=${zoom}`}
                        />
                      ) : (
                        <div className="ms-lr-viewer-imgwrap">
                          <img
                            src={previewUrl}
                            alt="Uploaded lab report"
                            style={{ transform: `scale(${zoom / 100})` }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="ms-card ms-lr-notes-card">
                <div className="ms-lr-panel-heading">
                  <span className="ms-lr-panel-num">2</span> AI Notes
                  {analysis && (
                    <span className="ms-lr-confidence-badge">
                      {abnormalCount + attentionCount > 0
                        ? `${abnormalCount + attentionCount} to review`
                        : 'All clear'}
                    </span>
                  )}
                </div>

                <div className="ms-lr-notebook">
                  <div className="ms-lr-notebook-rings" aria-hidden="true">
                    {Array.from({ length: 9 }).map((_, i) => <span key={i} />)}
                  </div>

                  <div className="ms-lr-notebook-body">
                    {loading && (
                      <div className="ms-lr-notes-loading">
                        <div className="ms-spinner" />
                        <p>AI har test result padh raha hai — 20-40 seconds lag sakte hain...</p>
                      </div>
                    )}

                    {!loading && !analysis && (
                      <div className="ms-lr-notes-empty">
                        <LuBrain size={22} />
                        <p>"Analyse Report" par click karo — AI yahan tumhare results plain language mein samjhayega.</p>
                      </div>
                    )}

                    {!loading && analysis && (
                      <>
                        <p className="ms-lr-notes-intro">Here's what I found after analysing your report:</p>

                        {flaggedTests.map((t, i) => {
                          const statusCfg = STATUS_CONFIG[t.status] || { color: 'grey' };
                          return (
                            <div className="ms-lr-note-item" key={i}>
                              <div className={`ms-lr-note-icon ms-lr-note-icon--${statusCfg.color}`}>
                                {pickNoteIcon(t.test_name)}
                              </div>
                              <div>
                                <div className="ms-lr-note-title">
                                  {t.test_name} is {(t.status || '').toLowerCase()}
                                  {t.value ? ` (${t.value})` : ''}.
                                </div>
                                <div className="ms-lr-note-sub">{t.plain_explanation}</div>
                              </div>
                            </div>
                          );
                        })}

                        {restNormalCount > 0 && (
                          <div className="ms-lr-note-item">
                            <div className="ms-lr-note-icon ms-lr-note-icon--green"><LuShieldCheck /></div>
                            <div>
                              <div className="ms-lr-note-title">
                                {flaggedTests.length > 0
                                  ? `Other ${restNormalCount} parameter${restNormalCount > 1 ? 's are' : ' is'} within normal range.`
                                  : 'All parameters are within normal range.'}
                              </div>
                              <div className="ms-lr-note-sub">
                                {analysis.has_urgent_values
                                  ? 'A couple of values need attention soon — see details below.'
                                  : 'Overall, your report looks stable.'}
                              </div>
                            </div>
                          </div>
                        )}

                        <form
                          className="ms-lr-notes-ask"
                          onSubmit={(e) => e.preventDefault()}
                        >
                          <input
                            type="text"
                            placeholder="Ask a question about your report... (coming soon)"
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            disabled
                          />
                          <button type="submit" disabled title="Coming soon">
                            <LuSend size={15} />
                          </button>
                        </form>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {analysis && (
            <div className="ms-lr-insights-row">
              <div className="ms-lr-insights-stats">
                <div className="ms-lr-insights-label">
                  <span className="ms-lr-panel-num">3</span> Top Insights
                </div>
                <div className="ms-lr-stat-chips">
                  <div className="ms-lr-stat-chip ms-lr-stat-chip--red">
                    <div className="ms-lr-stat-num">{abnormalCount}</div>
                    <div className="ms-lr-stat-label">Abnormal</div>
                  </div>
                  <div className="ms-lr-stat-chip ms-lr-stat-chip--amber">
                    <div className="ms-lr-stat-num">{attentionCount}</div>
                    <div className="ms-lr-stat-label">Attention</div>
                  </div>
                  <div className="ms-lr-stat-chip ms-lr-stat-chip--green">
                    <div className="ms-lr-stat-num">{normalCount}</div>
                    <div className="ms-lr-stat-label">Normal</div>
                  </div>
                </div>
              </div>

              <div className="ms-lr-quote-card">
                <LuLeaf size={22} />
                <p>Small changes today<br />build a healthier tomorrow.</p>
              </div>

              <button type="button" className="ms-lr-download-card" onClick={handleDownloadSummary}>
                <div className="ms-lr-download-icon"><LuDownload size={17} /></div>
                <div className="ms-lr-download-text">
                  <div className="ms-lr-download-title">Download Summary</div>
                  <div className="ms-lr-download-sub">Get a simple summary of your report</div>
                </div>
                <LuArrowRight size={16} />
              </button>
            </div>
          )}

          {analysis && (
            <div className="ms-lr-full-toggle-row">
              <button
                type="button"
                className="ms-btn-secondary"
                onClick={() => setShowFullBreakdown(v => !v)}
              >
                {showFullBreakdown ? 'Hide full breakdown' : 'View full report breakdown'}
                {showFullBreakdown ? <LuChevronUp size={15} /> : <LuChevronDown size={15} />}
              </button>
            </div>
          )}

          {showFullBreakdown && analysis && (
            <LabAnalysisResult analysis={analysis} rawText={rawText} userId={userId} onSaved={handleReportSaved} authFetch={authFetch} />
          )}

          <HealthHistorySection userId={userId} isLoggedIn={isLoggedIn} refreshKey={historyRefreshKey} authFetch={authFetch} />

          <div className="ms-lr-analyze-row">
            <div className="ms-lr-analyze-label">What we analyze</div>
            <div className="ms-lr-analyze-chips">
              {ANALYZE_TYPES.map((t) => (
                <span key={t.label} className={`ms-lr-analyze-chip ms-lr-analyze-chip--${t.tone}`}>
                  {t.icon} {t.label}
                </span>
              ))}
              <span className="ms-lr-analyze-chip ms-lr-analyze-chip--more">
                ··· &amp; more
              </span>
            </div>
          </div>

          <div className="ms-lr-privacy-banner">
            <div className="ms-lr-privacy-icon"><LuLock /></div>
            <div>
              <div className="ms-lr-privacy-title">Your health data is 100% private &amp; secure</div>
              <div className="ms-lr-privacy-sub">We use end-to-end encryption and never share your data.</div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}