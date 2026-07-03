import React, { useState, useEffect, useRef } from 'react';
import {
  LuUpload, LuFileText, LuX, LuLoader, LuTriangleAlert,
  LuCheck, LuShieldCheck, LuFlaskConical, LuChevronDown, LuChevronUp,
  LuBrain, LuLock, LuFolderOpen, LuDroplet, LuDroplets, LuTestTube,
  LuClipboardList, LuActivity, LuHeartPulse, LuChevronRight,
  LuFile, LuHighlighter, LuZoomIn, LuMinus, LuPlus, LuDownload,
  LuSend, LuLeaf, LuArrowRight, LuSun, LuSparkles,
} from 'react-icons/lu';
import Layout from '../components/Layout.jsx';
import { useUser } from '../hooks/useUser';
import './LabReport.css';

// ────────────────────────────────────────────────────────────────
// NOTE FOR NEXT DEV PASS: nothing in this file changes the backend
// contract. Same two endpoints, same payload shapes as before:
//   POST /lab/analyse  (FormData: file, user_id) -> { analysis, report_text }
//   POST /lab/save     (JSON: see handleSave below)
// Everything else here is presentation only.
// ────────────────────────────────────────────────────────────────

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

// Purely decorative hero illustration — paper report + magnifying glass +
// a small leaf accent. No data, no logic, just sets the tone.
function LabHeroIllustration() {
  return (
    <svg
      className="ms-lr-hero-illustration-svg"
      viewBox="0 0 240 220"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* paper */}
      <g transform="rotate(-6 100 105)">
        <rect x="48" y="30" width="104" height="144" rx="6" fill="#FFFFFF" stroke="var(--ms-soft-gold)" strokeWidth="1.25" />
        <rect x="62" y="46" width="46" height="6" rx="3" fill="var(--ms-luxury-brown)" opacity="0.4" />
        <line x1="62" y1="66" x2="136" y2="66" stroke="var(--ms-soft-gold)" strokeWidth="1.5" strokeLinecap="round" opacity="0.7" />
        <line x1="62" y1="80" x2="136" y2="80" stroke="var(--ms-soft-gold)" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
        <line x1="62" y1="94" x2="116" y2="94" stroke="var(--ms-soft-gold)" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
        <line x1="62" y1="112" x2="136" y2="112" stroke="var(--lr-green, #2E7D4F)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
        <line x1="62" y1="126" x2="106" y2="126" stroke="var(--ms-soft-gold)" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
      </g>

      {/* leaf accent */}
      <path
        d="M188 36c6 8 5 20-4 26-2-10 0-19 4-26Z"
        fill="var(--lr-green, #2E7D4F)"
        opacity="0.4"
      />

      {/* magnifying glass */}
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

// Pick a note icon by test name keywords — purely cosmetic, no data risk
// since it only ever falls back to a generic icon.
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

// Full detailed breakdown — same fields/handlers as the original
// implementation, just tucked behind a "view full breakdown" toggle now.
function LabAnalysisResult({ analysis, rawText, userId, onSaved }) {
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
      };
      const res = await fetch('http://localhost:8080/lab/save', {
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

export default function LabReport() {
  const { userId, isLoggedIn } = useUser();

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
  const workspaceRef = useRef(null);

  const isPdf = file?.type === 'application/pdf';

  // Build/revoke an object URL for whatever file is selected, so the
  // viewer panel can show the *actual* uploaded document, not a mock.
  useEffect(() => {
    if (!file) {
      setPreviewUrl('');
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  // ── Handlers — logic byte-for-byte the same as before, just also
  // resets zoom / notebook state so the UI doesn't carry over stale bits.
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

      const res = await fetch('http://localhost:8080/lab/analyse', {
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

  // Purely client-side download of a plain-text summary — no new backend
  // endpoint needed, works entirely off data we already have in `analysis`.
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

  // Notes shown in the "AI Notes" notebook: flagged tests first, capped at
  // 4 so the panel stays scannable, then one rollup line for the rest.
  const flaggedTests = tests.filter(t => t.status !== 'Normal').slice(0, 4);
  const restNormalCount = tests.length - flaggedTests.length;

  return (
    <Layout>
      <div className="ms-labreport-page">

        {/* ── Hero ── */}
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

          {/* Upload panel replaces the old decorative placeholder — same
              visual slot, now it's the actual functional uploader. */}
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

          {/* ── Workspace: report viewer + AI notes ── */}
          {fileName && (
            <div className="ms-lr-workspace" ref={workspaceRef}>
              {/* 1. Your Report */}
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

              {/* 2. AI Notes */}
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

          {/* ── 3. Top Insights ── */}
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

          {/* ── Full breakdown toggle — same detailed view + save-to-records
              flow as before, just tucked away so the new layout stays the
              star of the page. ── */}
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
            <LabAnalysisResult analysis={analysis} rawText={rawText} userId={userId} />
          )}

          {/* What we analyze — decorative, unchanged */}
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