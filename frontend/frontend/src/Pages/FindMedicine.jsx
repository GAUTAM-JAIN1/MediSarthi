import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  LuMic, LuUpload, LuFileText, LuX, LuLoader, LuTriangleAlert, LuCheck, LuShieldCheck,
  LuSparkles, LuLock, LuSend, LuLanguages, LuChevronRight, LuFolderOpen, LuClock,
  LuThermometer, LuBrain, LuSnowflake, LuMicVocal, LuWaves, LuEye, LuActivity, LuFrown, LuWind,
  LuHand, LuBatteryLow, LuDroplets, LuPlus, LuUserRound,
} from 'react-icons/lu';
import Layout from '../components/Layout.jsx';
import { useUser } from '../hooks/useUser';
import '../components/Layout.css';
import './FindMedicine.css';

// Safe helper — same pattern as Auth.jsx/HealthInfo.jsx/EmergencyView.jsx.
const extractErrorMessage = (detail, fallback) => {
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === 'string' ? d : d?.msg || JSON.stringify(d))).join(', ');
  }
  if (typeof detail === 'object' && detail.msg) return detail.msg;
  return fallback;
};

const INNER_SYMPTOMS = [
  { key: 'fever', label: 'Fever', icon: LuThermometer },
  { key: 'headache', label: 'Headache', icon: LuBrain },
  { key: 'cold', label: 'Cold', icon: LuSnowflake },
  { key: 'cough', label: 'Cough', icon: LuWind },
  { key: 'stomach', label: 'Stomach Pain', icon: LuActivity },
  { key: 'nausea', label: 'Nausea', icon: LuFrown },
  { key: 'weakness', label: 'Weakness', icon: LuBatteryLow },
  { key: 'bodypain', label: 'Body Pain', icon: LuUserRound },
];

const OUTER_SYMPTOMS = [
  { key: 'eyestrain', label: 'Eye Strain', icon: LuEye },
  { key: 'dizziness', label: 'Dizziness', icon: LuWaves },
  { key: 'sorethroat', label: 'Sore Throat', icon: LuMicVocal },
  { key: 'allergy', label: 'Allergy', icon: LuSparkles },
  { key: 'skinissue', label: 'Skin Issue', icon: LuHand },
  { key: 'breathless', label: 'Breathless', icon: LuWind },
  { key: 'diarrhea', label: 'Diarrhea', icon: LuDroplets },
];

function ringPositions(items, radius, startAngle = -90) {
  const step = 360 / items.length;
  return items.map((item, i) => {
    const angle = ((startAngle + i * step) * Math.PI) / 180;
    return { ...item, x: Math.cos(angle) * radius, y: Math.sin(angle) * radius };
  });
}

const POPULAR_SEARCHES = [
  { label: 'Fever and headache', text: 'I have a fever and headache since yesterday.' },
  { label: 'Cold and cough', text: 'I have a cold and cough.' },
  { label: 'Stomach pain', text: 'I have stomach pain.' },
  { label: 'Body pain', text: 'I have body pain and weakness.' },
  { label: 'Weakness', text: 'I am feeling very tired and weak.' },
];
const MORE_POPULAR_SEARCHES = [
  { label: 'Vomiting', text: 'I am feeling nauseous and vomiting.' },
  { label: 'Allergy', text: 'I think I am having an allergic reaction.' },
  { label: 'Sore throat', text: 'I have a sore throat and mild cough.' },
];

const MODES = [
  { id: 'describe', title: 'Describe symptoms', sub: 'Type your symptoms', icon: LuFileText },
  { id: 'voice', title: 'Voice search', sub: 'Speak your symptoms', icon: LuMic },
  { id: 'scan', title: 'Scan prescription', sub: 'Upload & analyze', icon: LuUpload },
];

// AUTH (D34): PrescriptionAnalysisCard's one protected POST call now takes
// `authFetch` as a prop (passed down from the page-level useUser() call)
// instead of using plain fetch().
function PrescriptionAnalysisCard({ analysis, rawMedicines, source, userId, onSaved, authFetch }) {
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
        overall_summary: analysis.overall_summary,
        medicines: analysis.medicines || [],
        has_allergy_conflict: !!analysis.has_allergy_conflict,
        safety_note: analysis.safety_note || '',
        source,
        raw_medicines: rawMedicines || [],
      };
      const res = await authFetch('http://localhost:8080/health/prescription-analysis', {
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
    <div className="ms-fm-analysis">
      {analysis.has_allergy_conflict && (
        <div className="ms-fm-allergy-banner">
          <LuTriangleAlert />
          <span>
            Ek ya zyada medicine aapki saved allergy se match kar rahi hai — neeche har dawai ke
            "Allergy Warning" section mein detail dekh lo, aur dawai lene se pehle doctor/pharmacist
            se confirm kar lo.
          </span>
        </div>
      )}

      <div className="ms-fm-analysis-summary">
        <div className="ms-fm-analysis-title">Plain-Language Summary</div>
        <p>{analysis.overall_summary}</p>
      </div>

      <div className="ms-fm-medicines-list">
        {(analysis.medicines || []).map((med, i) => (
          <div
            key={i}
            className={`ms-fm-medicine-item ${med.allergy_warning ? 'ms-fm-medicine-item--warn' : ''}`}
          >
            <div className="ms-fm-medicine-name">
              {med.allergy_warning ? <LuTriangleAlert className="ms-fm-warn-icon" /> : null}
              {med.name}
            </div>
            <div className="ms-fm-medicine-row">
              <span className="ms-fm-medicine-label">Kis liye hai:</span>
              <span>{med.purpose}</span>
            </div>
            <div className="ms-fm-medicine-row">
              <span className="ms-fm-medicine-label">Kaise lena hai:</span>
              <span>{med.how_to_take}</span>
            </div>
            <div className="ms-fm-medicine-row">
              <span className="ms-fm-medicine-label">Common side effects:</span>
              <span>{med.common_side_effects}</span>
            </div>
            {med.precautions && (
              <div className="ms-fm-medicine-row">
                <span className="ms-fm-medicine-label">Precautions:</span>
                <span>{med.precautions}</span>
              </div>
            )}
            {med.allergy_warning && (
              <div className="ms-fm-medicine-allergy-warning">
                <LuTriangleAlert /> {med.allergy_warning}
              </div>
            )}
          </div>
        ))}
      </div>

      {analysis.safety_note && (
        <div className="ms-fm-safety-note">
          <LuShieldCheck /> {analysis.safety_note}
        </div>
      )}

      <div className="ms-fm-save-row">
        {saveError && <p className="ms-fm-error">{saveError}</p>}
        {saved ? (
          <span className="ms-fm-saved-chip"><LuCheck /> Records mein save ho gaya</span>
        ) : (
          <button type="button" className="ms-btn-secondary" onClick={handleSave} disabled={saving}>
            {saving ? <><LuLoader className="ms-fm-spin" /> Save ho raha hai...</> : 'Apne records mein save karo'}
          </button>
        )}
      </div>
    </div>
  );
}

function TriageResultCard({ triage }) {
  if (!triage || !triage.urgency_level) return null;

  const colorClass =
    triage.urgency_color === 'red'
      ? 'ms-fm-triage--red'
      : triage.urgency_color === 'yellow'
      ? 'ms-fm-triage--yellow'
      : 'ms-fm-triage--green';

  return (
    <div className="ms-fm-triage">
      <span className={`ms-fm-triage-badge ${colorClass}`}>{triage.urgency_level}</span>

      {triage.headline && <div className="ms-fm-triage-headline">{triage.headline}</div>}
      {triage.explanation && <p className="ms-fm-triage-explanation">{triage.explanation}</p>}

      {Array.isArray(triage.flags) && triage.flags.length > 0 && (
        <div className="ms-fm-triage-section">
          <div className="ms-fm-triage-section-title">Key symptoms noted</div>
          <ul className="ms-fm-triage-list">
            {triage.flags.map((f, i) => (
              <li key={i}>
                <strong>{f.symptom}:</strong> {f.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {Array.isArray(triage.home_care_tips) && triage.home_care_tips.length > 0 && (
        <div className="ms-fm-triage-section">
          <div className="ms-fm-triage-section-title">Home care tips</div>
          <ul className="ms-fm-triage-list">
            {triage.home_care_tips.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </div>
      )}

      {Array.isArray(triage.warning_signs) && triage.warning_signs.length > 0 && (
        <div className="ms-fm-triage-section ms-fm-triage-section--warn">
          <div className="ms-fm-triage-section-title">
            <LuTriangleAlert /> Seek care immediately if you notice
          </div>
          <ul className="ms-fm-triage-list">
            {triage.warning_signs.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {triage.disclaimer && (
        <div className="ms-fm-safety-note">
          <LuShieldCheck /> {triage.disclaimer}
        </div>
      )}
    </div>
  );
}

export default function FindMedicine() {
  const { userId, isLoggedIn, authFetch } = useUser();

  const [query, setQuery] = useState('');

  const [triageResult, setTriageResult] = useState(null);
  const [textLoading, setTextLoading] = useState(false);
  const [textError, setTextError] = useState('');

  const [textResult, setTextResult] = useState(null);
  const [textAnalysis, setTextAnalysis] = useState(null);
  const [textRawMedicines, setTextRawMedicines] = useState([]);

  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState(null);
  const [fileResult, setFileResult] = useState(null);
  const [fileAnalysis, setFileAnalysis] = useState(null);
  const [fileRawMedicines, setFileRawMedicines] = useState([]);
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState('');

  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const [hindiMode, setHindiMode] = useState(false);

  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [activeMode, setActiveMode] = useState('describe');
  const [showMorePopular, setShowMorePopular] = useState(false);

  const drawerRef = useRef(null);
  const textareaRef = useRef(null);

  const innerBubbles = useMemo(() => ringPositions(INNER_SYMPTOMS, 150, -90), []);
  const outerBubbles = useMemo(() => ringPositions(OUTER_SYMPTOMS, 245, -90 + 360 / OUTER_SYMPTOMS.length / 2), []);

  const toggleSymptom = (label) => {
    setSelectedSymptoms((prev) =>
      prev.includes(label) ? prev.filter((s) => s !== label) : [...prev, label]
    );
  };

  const openDescribeAndFocus = () => {
    setActiveMode('describe');
    setTimeout(() => {
      drawerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      textareaRef.current?.focus();
    }, 150);
  };

  const combinedQuery = useMemo(() => {
    const parts = [];
    if (selectedSymptoms.length) parts.push(`Symptoms: ${selectedSymptoms.join(', ')}.`);
    if (query.trim()) parts.push(query.trim());
    return parts.join(' ');
  }, [selectedSymptoms, query]);

  const handleTextSubmit = async () => {
    if (!combinedQuery.trim()) return;
    if (!isLoggedIn) {
      setTextError('Pehle login karo.');
      return;
    }
    setTextLoading(true);
    setTextError('');
    setTriageResult(null);
    try {
      const res = await authFetch('http://localhost:8080/triage/symptoms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, symptoms: combinedQuery }),
      });
      const data = await res.json();
      if (!res.ok) {
        setTextError(extractErrorMessage(data.detail, 'Kuch error aa gaya.'));
      } else {
        setTriageResult(data.triage || null);
      }
    } catch {
      setTextError('Backend se connect nahi ho pa raha. Backend chalu hai?');
    } finally {
      setTextLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach((t) => t.stop());
      };
      mediaRecorder.start();
      setRecording(true);
    } catch {
      setTextError('Microphone access nahi mila. Browser settings check karo.');
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  };

  const submitVoice = async () => {
    if (!audioBlob) return;
    if (!isLoggedIn) {
      setTextError('Pehle login karo.');
      return;
    }
    setTextLoading(true);
    setTextError('');
    setTextResult(null);
    setTextAnalysis(null);
    setTextRawMedicines([]);
    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');
      formData.append('user_id', userId);

      const res = await authFetch('http://localhost:8080/consultation/speech', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        setTextError(extractErrorMessage(data.detail, 'Kuch error aa gaya.'));
      } else {
        setTextResult(data.consultation_result || JSON.stringify(data));
        setTextAnalysis(data.analysis || null);
        setTextRawMedicines(data.prescription?.medicines || []);
        setAudioBlob(null);
      }
    } catch {
      setTextError('Backend se connect nahi ho pa raha.');
    } finally {
      setTextLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setFileName(f.name);
      setFileResult(null);
      setFileAnalysis(null);
      setFileRawMedicines([]);
      setFileError('');
    }
  };

  const handleFileSubmit = async () => {
    if (!file) return;
    if (!isLoggedIn) {
      setFileError('Pehle login karo.');
      return;
    }
    setFileLoading(true);
    setFileError('');
    setFileResult(null);
    setFileAnalysis(null);
    setFileRawMedicines([]);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', userId);

      const res = await authFetch('http://localhost:8080/consultation/document', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        setFileError(extractErrorMessage(data.detail, 'File analyze nahi ho saki.'));
      } else {
        setFileResult(data.extraction_result || JSON.stringify(data));
        setFileAnalysis(data.analysis || null);
        setFileRawMedicines(data.prescription?.medicines || []);
      }
    } catch {
      setFileError('Backend se connect nahi ho pa raha.');
    } finally {
      setFileLoading(false);
    }
  };

  const isBusy = textLoading || fileLoading;
  const hasResult = Boolean(textResult || fileResult || textAnalysis || fileAnalysis || triageResult);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!isBusy) {
      setElapsed(0);
      return;
    }
    const t = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(t);
  }, [isBusy]);

  const analysisState = isBusy ? 'loading' : hasResult ? 'done' : 'idle';

  return (
    <Layout>
      <div className="ms-findmedicine-page">
        <div className={`ms-fm-shell ${analysisState === 'idle' ? 'ms-fm-shell--wide' : ''}`}>
          <aside className="ms-fm-left ms-fm-anim" style={{ animationDelay: '0s' }}>
            <div className="ms-fm-eyebrow">
              <LuSparkles /> AI Powered Medicine Discovery
            </div>

            <h1 className="ms-fm-headline">
              Discover the cause,<br />
              find the <span className="ms-fm-accent">right medicine</span>.
            </h1>

            <p className="ms-fm-desc">
              Select your symptoms, speak or upload a prescription. Our AI will
              analyze everything and suggest the best medicines for you.
            </p>

            <div className="ms-fm-mode-cards">
              {MODES.map((m) => {
                const Icon = m.icon;
                return (
                  <button
                    key={m.id}
                    type="button"
                    className={`ms-fm-mode-card ${activeMode === m.id ? 'active' : ''}`}
                    onClick={() => {
                      setActiveMode(m.id);
                      setTimeout(() => drawerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 100);
                    }}
                  >
                    <span className="ms-fm-mode-icon"><Icon /></span>
                    <span className="ms-fm-mode-text">
                      <span className="ms-fm-mode-title">{m.title}</span>
                      <span className="ms-fm-mode-sub">{m.sub}</span>
                    </span>
                    <LuChevronRight className="ms-fm-mode-arrow" size={16} />
                  </button>
                );
              })}
            </div>

            <div className="ms-fm-tip-box">
              <span className="ms-fm-tip-icon"><LuSparkles size={14} /></span>
              <span className="ms-fm-tip-text">
                <strong>Tip</strong>
                Select all that apply for better and accurate results.
              </span>
              <LuShieldCheck className="ms-fm-tip-shield" size={20} />
            </div>

            <Link to="/health-info" className="ms-fm-history-card">
              <span className="ms-fm-history-icon"><LuClock /></span>
              <span>
                <span className="ms-fm-history-title">Medical History</span>
                <span className="ms-fm-history-sub">View your past records</span>
              </span>
              <LuChevronRight size={15} style={{ marginLeft: 'auto', color: 'var(--ms-text-secondary)' }} />
            </Link>

            <div>
              <div className="ms-fm-popular-head">
                <LuSparkles /> Popular Searches
              </div>
              <div className="ms-fm-popular-chips">
                {POPULAR_SEARCHES.map((s) => (
                  <button
                    key={s.label}
                    type="button"
                    className="ms-fm-pop-chip"
                    onClick={() => { setQuery(s.text); openDescribeAndFocus(); }}
                  >
                    {s.label}
                  </button>
                ))}
                {showMorePopular &&
                  MORE_POPULAR_SEARCHES.map((s) => (
                    <button
                      key={s.label}
                      type="button"
                      className="ms-fm-pop-chip"
                      onClick={() => { setQuery(s.text); openDescribeAndFocus(); }}
                    >
                      {s.label}
                    </button>
                  ))}
                <button
                  type="button"
                  className={`ms-fm-pop-viewall ${showMorePopular ? 'open' : ''}`}
                  onClick={() => setShowMorePopular((v) => !v)}
                >
                  {showMorePopular ? 'Show less' : 'View all'} <LuChevronRight size={13} />
                </button>
              </div>
            </div>
          </aside>

          <main className="ms-fm-center ms-fm-anim" style={{ animationDelay: '0.08s' }}>
            <div className="ms-fm-map-stage">
              <svg className="ms-fm-map-rings" viewBox="-310 -310 620 620" aria-hidden="true">
                <circle cx="0" cy="0" r="150" fill="none" stroke="rgba(156,107,69,0.14)" strokeDasharray="2 6" />
                <circle cx="0" cy="0" r="245" fill="none" stroke="rgba(156,107,69,0.1)" strokeDasharray="2 6" />
              </svg>

              {innerBubbles.map((s) => {
                const Icon = s.icon;
                const isSelected = selectedSymptoms.includes(s.label);
                return (
                  <button
                    key={s.key}
                    type="button"
                    title={s.label}
                    className={`ms-fm-bubble ms-fm-bubble--inner ${isSelected ? 'selected' : ''}`}
                    style={{ '--x': `${s.x}px`, '--y': `${s.y}px`, animationDelay: `${(s.x + 300) / 100}s` }}
                    onClick={() => toggleSymptom(s.label)}
                  >
                    <Icon />
                    <span className="ms-fm-bubble-label">{s.label}</span>
                    {isSelected && (
                      <span className="ms-fm-bubble-check"><LuCheck /></span>
                    )}
                  </button>
                );
              })}

              {outerBubbles.map((s) => {
                const Icon = s.icon;
                const isSelected = selectedSymptoms.includes(s.label);
                return (
                  <button
                    key={s.key}
                    type="button"
                    title={s.label}
                    className={`ms-fm-bubble ms-fm-bubble--outer ${isSelected ? 'selected' : ''}`}
                    style={{ '--x': `${s.x}px`, '--y': `${s.y}px`, animationDelay: `${(s.y + 300) / 100}s` }}
                    onClick={() => toggleSymptom(s.label)}
                  >
                    <Icon />
                    <span className="ms-fm-bubble-label">{s.label}</span>
                    {isSelected && (
                      <span className="ms-fm-bubble-check"><LuCheck /></span>
                    )}
                  </button>
                );
              })}

              <div className="ms-fm-map-center">
                <div className="ms-fm-map-center-glow" />
                <LuSparkles className="ms-fm-center-icon" />
                <div className="ms-fm-map-center-title">AI HEALTH MAP</div>
                <div className="ms-fm-map-center-sub">Your symptoms are connected</div>
              </div>
            </div>

            <div className="ms-fm-selected-row">
              <span className="ms-fm-selected-label">Selected Symptoms ({selectedSymptoms.length})</span>
              {selectedSymptoms.map((label) => {
                const match = [...INNER_SYMPTOMS, ...OUTER_SYMPTOMS].find((s) => s.label === label);
                const Icon = match?.icon || LuCheck;
                return (
                  <span key={label} className="ms-fm-sel-chip">
                    <Icon />
                    {label}
                    <button type="button" onClick={() => toggleSymptom(label)} aria-label={`Remove ${label}`}>
                      <LuX size={12} />
                    </button>
                  </span>
                );
              })}
              <button type="button" className="ms-fm-selected-add" onClick={openDescribeAndFocus} aria-label="Add more">
                <LuPlus size={14} />
              </button>
            </div>

            <div className="ms-fm-drawer" ref={drawerRef}>
              {activeMode === 'describe' && (
                <>
                  <div className="ms-fm-drawer-head"><LuFileText /> Describe your symptoms</div>
                  <div className="ms-fm-textarea-wrap">
                    <textarea
                      ref={textareaRef}
                      className="ms-textarea ms-fm-textarea"
                      placeholder={
                        hindiMode
                          ? 'जैसे: मुझे कल से हल्का बुखार और गले में खराश है...'
                          : 'e.g. I have a mild fever and sore throat since yesterday...'
                      }
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      rows={5}
                    />
                    <button
                      type="button"
                      className="ms-fm-textarea-send"
                      disabled={!combinedQuery.trim() || textLoading}
                      onClick={handleTextSubmit}
                      aria-label="Ask Medisarthi"
                    >
                      <LuSend />
                    </button>
                  </div>

                  {!isLoggedIn && (
                    <p className="ms-fm-warn">⚠️ Pehle <a href="/auth">login karo</a> — AI consultation ke liye zaruri hai.</p>
                  )}
                  {textError && <p className="ms-fm-error">{textError}</p>}

                  <div className="ms-fm-drawer-footer">
                    <button
                      type="button"
                      className="ms-btn-secondary ms-fm-pill-btn ms-fm-lang-btn"
                      onClick={() => setHindiMode((v) => !v)}
                    >
                      <LuLanguages /> {hindiMode ? 'Type in English' : 'हिंदी में लिखें'}
                    </button>
                    <button
                      type="button"
                      className="ms-btn-primary ms-fm-pill-btn"
                      disabled={!combinedQuery.trim() || textLoading}
                      onClick={handleTextSubmit}
                    >
                      {textLoading ? <><LuLoader className="ms-fm-spin" /> Analyzing...</> : <><LuSparkles /> Ask Medisarthi</>}
                    </button>
                  </div>
                </>
              )}

              {activeMode === 'voice' && (
                <>
                  <div className="ms-fm-drawer-head"><LuMic /> Speak your symptoms</div>
                  <div className="ms-fm-voice-stage">
                    {!recording && !audioBlob && (
                      <button type="button" className="ms-fm-mic-btn" onClick={startRecording}>
                        <LuMic />
                      </button>
                    )}
                    {recording && (
                      <button type="button" className="ms-fm-mic-btn recording" onClick={stopRecording}>
                        <LuMic />
                      </button>
                    )}
                    {audioBlob && !recording && (
                      <button type="button" className="ms-btn-primary ms-fm-pill-btn" onClick={submitVoice} disabled={textLoading}>
                        {textLoading ? <><LuLoader className="ms-fm-spin" /> Analyzing...</> : <><LuSend /> Submit Recording</>}
                      </button>
                    )}
                    <p className="ms-fm-voice-hint">
                      {recording ? 'Recording... tap to stop' : audioBlob ? 'Recording ready — submit karo ya dobara bolo' : 'Tap the mic and speak naturally, Hindi ya English mein'}
                    </p>
                  </div>
                  {!isLoggedIn && (
                    <p className="ms-fm-warn">⚠️ Pehle <a href="/auth">login karo</a> — AI consultation ke liye zaruri hai.</p>
                  )}
                  {textError && <p className="ms-fm-error">{textError}</p>}
                </>
              )}

              {activeMode === 'scan' && (
                <>
                  <div className="ms-fm-drawer-head"><LuUpload /> Scan a prescription</div>
                  <label className="ms-fm-dropzone">
                    <input type="file" accept="image/*,.pdf" onChange={handleFileChange} hidden />
                    {fileName ? (
                      <div className="ms-fm-file-chip">
                        <LuFileText />
                        <span>{fileName}</span>
                        <button
                          type="button"
                          className="ms-fm-file-remove"
                          onClick={(e) => { e.preventDefault(); setFile(null); setFileName(null); setFileResult(null); setFileAnalysis(null); setFileRawMedicines([]); }}
                        >
                          <LuX />
                        </button>
                      </div>
                    ) : (
                      <>
                        <LuUpload className="ms-fm-dropzone-icon" />
                        <div className="ms-fm-dropzone-title">Drag &amp; drop your file here</div>
                        <div className="ms-fm-dropzone-sub">JPG, PNG or PDF — max 10MB</div>
                        <span className="ms-fm-choose-btn"><LuFolderOpen /> Choose File</span>
                      </>
                    )}
                  </label>

                  {!isLoggedIn && (
                    <p className="ms-fm-warn">⚠️ Pehle <a href="/auth">login karo</a> — prescription scan ke liye zaruri hai.</p>
                  )}
                  {fileError && <p className="ms-fm-error">{fileError}</p>}

                  <div className="ms-fm-drawer-footer">
                    <button
                      type="button"
                      className="ms-btn-primary ms-fm-pill-btn"
                      disabled={!fileName || fileLoading}
                      onClick={handleFileSubmit}
                    >
                      {fileLoading ? <><LuLoader className="ms-fm-spin" /> Analyzing...</> : <><LuFileText /> Analyze prescription</>}
                    </button>
                  </div>
                </>
              )}

              {activeMode === 'describe' && <TriageResultCard triage={triageResult} />}

              {activeMode === 'voice' && textResult && !textAnalysis && (
                <div className="ms-fm-result">
                  <div className="ms-fm-result-title">AI Response</div>
                  <p className="ms-fm-result-text">{textResult}</p>
                </div>
              )}
              {activeMode === 'voice' && (
                <PrescriptionAnalysisCard analysis={textAnalysis} rawMedicines={textRawMedicines} source="voice" userId={userId} authFetch={authFetch} />
              )}
              {activeMode === 'scan' && fileResult && !fileAnalysis && (
                <div className="ms-fm-result">
                  <div className="ms-fm-result-title">Prescription Analysis</div>
                  <p className="ms-fm-result-text">{fileResult}</p>
                </div>
              )}
              {activeMode === 'scan' && (
                <PrescriptionAnalysisCard analysis={fileAnalysis} rawMedicines={fileRawMedicines} source="document" userId={userId} authFetch={authFetch} />
              )}
            </div>
          </main>

          {analysisState !== 'idle' && (
            <aside className="ms-fm-right ms-fm-anim" style={{ animationDelay: '0.1s' }}>
              <div className="ms-fm-analysis-card">
                <div className="ms-fm-analysis-head">
                  <span className="ms-fm-analysis-head-icon"><LuSparkles /></span>
                  <span>
                    <span className="ms-fm-analysis-head-title">AI Analysis</span>
                    <span className="ms-fm-analysis-head-sub">
                      {analysisState === 'loading' ? 'Working on your query' : 'Latest result below'}
                    </span>
                  </span>
                </div>

                {analysisState === 'loading' && (
                  <div className="ms-fm-analysis-loading">
                    <div className="ms-spinner" />
                    <p className="ms-fm-analysis-loading-text">AI aapka query analyze kar raha hai...</p>
                    <p className="ms-fm-analysis-loading-time">{elapsed}s</p>
                  </div>
                )}

                {analysisState === 'done' && (
                  <div className="ms-fm-analysis-done">
                    <LuCheck /> Analysis ready — result neeche dekho.
                  </div>
                )}
              </div>

              <div className="ms-fm-privacy-bar">
                <LuLock /> Your data is 100% secure &amp; private
              </div>
            </aside>
          )}
        </div>
      </div>
    </Layout>
  );
}