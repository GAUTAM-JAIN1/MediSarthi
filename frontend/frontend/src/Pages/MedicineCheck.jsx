import React, { useState } from 'react';
import {
  LuPill, LuPlus, LuX, LuLoader, LuTriangleAlert, LuShieldCheck,
  LuCircleAlert, LuCircleCheck, LuActivity
} from 'react-icons/lu';
import Layout from '../components/Layout.jsx';
import { useUser } from '../hooks/useUser';
import './MedicineCheck.css';

const extractErrorMessage = (detail, fallback) => {
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === 'string' ? d : d?.msg || JSON.stringify(d))).join(', ');
  }
  if (typeof detail === 'object' && detail.msg) return detail.msg;
  return fallback;
};

const SEVERITY_CONFIG = {
  'None':            { color: 'green',  label: 'No Interaction' },
  'Minor':           { color: 'yellow', label: 'Minor' },
  'Moderate':        { color: 'orange', label: 'Moderate' },
  'Major':           { color: 'red',    label: 'Major' },
  'Contraindicated': { color: 'red',    label: '⛔ Contraindicated' },
};

const URGENCY_CONFIG = {
  'Home Care':                { color: 'green',  icon: LuCircleCheck },
  'See a Doctor Soon':        { color: 'yellow', icon: LuCircleAlert },
  'Visit Emergency / Go Now': { color: 'red',    icon: LuTriangleAlert },
};

// AUTH (D34): both sections below now take `authFetch` as a prop from the
// page-level useUser() call, and use it instead of plain fetch() for their
// one protected POST call each.

function InteractionChecker({ userId, isLoggedIn, authFetch }) {
  const [medicines, setMedicines] = useState(['', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const addMedicine = () => {
    if (medicines.length < 8) setMedicines([...medicines, '']);
  };

  const removeMedicine = (i) => {
    if (medicines.length <= 2) return;
    setMedicines(medicines.filter((_, idx) => idx !== i));
  };

  const updateMedicine = (i, val) => {
    const updated = [...medicines];
    updated[i] = val;
    setMedicines(updated);
  };

  const handleCheck = async () => {
    const filled = medicines.map(m => m.trim()).filter(Boolean);
    if (filled.length < 1) {
      setError('Kam se kam ek medicine ka naam daalo.');
      return;
    }
    if (!isLoggedIn) {
      setError('Pehle login karo.');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await authFetch('http://localhost:8080/medicine/interactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, medicines: filled }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(extractErrorMessage(data.detail, 'Check nahi ho saka.'));
      } else {
        setResult(data.interactions || null);
      }
    } catch {
      setError('Backend se connect nahi ho pa raha.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ms-mc-section ms-card">
      <div className="ms-mc-section-head">
        <div className="ms-mc-icon ms-mc-icon--brown"><LuPill size={20} /></div>
        <div>
          <div className="ms-mc-section-title">Medicine Interaction Checker</div>
          <div className="ms-mc-section-sub">
            Jo medicines tum le rahe ho unhe daalo — AI check karega koi problem toh nahi
          </div>
        </div>
      </div>

      <div className="ms-mc-medicines-inputs">
        {medicines.map((med, i) => (
          <div key={i} className="ms-mc-med-row">
            <input
              className="ms-input ms-mc-med-input"
              placeholder={`Medicine ${i + 1} ka naam, e.g. Metformin 500mg`}
              value={med}
              onChange={(e) => updateMedicine(i, e.target.value)}
            />
            {medicines.length > 2 && (
              <button
                type="button"
                className="ms-mc-remove-btn"
                onClick={() => removeMedicine(i)}
                aria-label="Remove"
              >
                <LuX size={14} />
              </button>
            )}
          </div>
        ))}

        {medicines.length < 8 && (
          <button type="button" className="ms-mc-add-btn" onClick={addMedicine}>
            <LuPlus size={15} /> Aur ek medicine add karo
          </button>
        )}
      </div>

      {!isLoggedIn && (
        <p className="ms-mc-warn">
          ⚠️ Pehle <a href="/auth">login karo</a> — interaction check ke liye zaruri hai.
        </p>
      )}

      {error && <p className="ms-mc-error">{error}</p>}

      <button
        type="button"
        className="ms-btn-primary"
        onClick={handleCheck}
        disabled={loading || !isLoggedIn}
      >
        {loading
          ? <><LuLoader className="ms-mc-spin" /> Check ho raha hai...</>
          : <><LuShieldCheck size={16} /> Interactions Check Karo</>
        }
      </button>

      {result && <InteractionResult result={result} />}
    </div>
  );
}

function InteractionResult({ result }) {
  if (!result) return null;

  const interactions = (result.interactions || []).filter(
    (i) => i.severity && i.severity !== 'None'
  );

  return (
    <div className="ms-mc-result">
      {result.has_major_interaction && (
        <div className="ms-mc-major-banner">
          <LuTriangleAlert size={18} />
          <div>
            <strong>Major interaction mili hai</strong> — koi bhi medicine lene se pehle
            apne doctor ya pharmacist se confirm karo.
          </div>
        </div>
      )}

      {!result.has_major_interaction && interactions.length === 0 && (
        <div className="ms-mc-safe-banner">
          <LuCircleCheck size={18} />
          <span>Koi significant interaction nahi mila in medicines mein.</span>
        </div>
      )}

      {interactions.length > 0 && (
        <div className="ms-mc-interactions-list">
          <div className="ms-mc-result-label">
            Interactions Found ({interactions.length})
          </div>
          {interactions.map((item, i) => {
            const cfg = SEVERITY_CONFIG[item.severity] || { color: 'grey', label: item.severity };
            return (
              <div
                key={i}
                className={`ms-mc-interaction-card ms-mc-interaction-card--${cfg.color}`}
              >
                <div className="ms-mc-interaction-header">
                  <span className="ms-mc-interaction-pair">
                    {item.medicine_a}
                    {item.medicine_b && item.medicine_b !== 'ALLERGY ALERT'
                      ? ` + ${item.medicine_b}`
                      : item.medicine_b === 'ALLERGY ALERT' ? ' (Allergy Alert)' : ''}
                  </span>
                  <span className={`ms-mc-severity-badge ms-mc-severity-badge--${cfg.color}`}>
                    {cfg.label}
                  </span>
                </div>
                <p className="ms-mc-interaction-desc">{item.description}</p>
                {item.recommendation && (
                  <div className="ms-mc-interaction-rec">
                    <strong>Kya karein:</strong> {item.recommendation}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {result.overall_safety_summary && (
        <div className="ms-mc-summary-box">
          <div className="ms-mc-result-label">Overall Safety Picture</div>
          <p>{result.overall_safety_summary}</p>
        </div>
      )}

      {result.recommendation && (
        <div className="ms-mc-recommendation">
          <strong>Recommendation:</strong> {result.recommendation}
        </div>
      )}

      {result.disclaimer && (
        <div className="ms-mc-disclaimer">
          <LuShieldCheck size={14} /> {result.disclaimer}
        </div>
      )}
    </div>
  );
}


function SymptomTriage({ userId, isLoggedIn, authFetch }) {
  const [symptoms, setSymptoms] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleTriage = async () => {
    if (!symptoms.trim()) {
      setError('Symptoms likho pehle.');
      return;
    }
    if (!isLoggedIn) {
      setError('Pehle login karo.');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await authFetch('http://localhost:8080/triage/symptoms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, symptoms }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(extractErrorMessage(data.detail, 'Triage nahi ho saka.'));
      } else {
        setResult(data.triage || null);
      }
    } catch {
      setError('Backend se connect nahi ho pa raha.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ms-mc-section ms-card">
      <div className="ms-mc-section-head">
        <div className="ms-mc-icon ms-mc-icon--gold"><LuActivity size={20} /></div>
        <div>
          <div className="ms-mc-section-title">Symptom Triage</div>
          <div className="ms-mc-section-sub">
            Symptoms batao — AI bata dega ghar pe rest karo ya doctor ke paas jao
          </div>
        </div>
      </div>

      <textarea
        className="ms-textarea ms-mc-triage-textarea"
        placeholder={`Apne symptoms describe karo — jitna detail doge utna better.\n\nExample: Kal raat se bukhar hai, 101°F, saath mein sar dard aur thakaan. Koi khansi ya saans ki takleef nahi hai. Paracetamol li thi, thodi rahat mili.`}
        value={symptoms}
        onChange={(e) => setSymptoms(e.target.value)}
        rows={5}
      />

      {!isLoggedIn && (
        <p className="ms-mc-warn">
          ⚠️ Pehle <a href="/auth">login karo</a> — triage ke liye zaruri hai.
        </p>
      )}

      {error && <p className="ms-mc-error">{error}</p>}

      <button
        type="button"
        className="ms-btn-primary"
        onClick={handleTriage}
        disabled={loading || !symptoms.trim() || !isLoggedIn}
      >
        {loading
          ? <><LuLoader className="ms-mc-spin" /> Assessment ho raha hai...</>
          : <><LuActivity size={16} /> Triage Assessment Karo</>
        }
      </button>

      {result && <TriageResult result={result} />}
    </div>
  );
}

function TriageResult({ result }) {
  if (!result || !result.urgency_level) return null;

  const cfg = URGENCY_CONFIG[result.urgency_level] || {
    color: 'yellow', icon: LuCircleAlert
  };
  const UrgencyIcon = cfg.icon;

  return (
    <div className="ms-mc-triage-result">
      {/* Urgency level card */}
      <div className={`ms-mc-urgency-card ms-mc-urgency-card--${cfg.color}`}>
        <UrgencyIcon size={28} className={`ms-mc-urgency-icon--${cfg.color}`} />
        <div>
          <div className={`ms-mc-urgency-level ms-mc-urgency-level--${cfg.color}`}>
            {result.urgency_level}
          </div>
          <p className="ms-mc-urgency-headline">{result.headline}</p>
        </div>
      </div>

      {result.explanation && (
        <div className="ms-mc-triage-section">
          <div className="ms-mc-result-label">Kyun Yeh Assessment?</div>
          <p>{result.explanation}</p>
        </div>
      )}

      {result.flags && result.flags.length > 0 && (
        <div className="ms-mc-triage-section">
          <div className="ms-mc-result-label">Key Observations</div>
          <div className="ms-mc-flags-list">
            {result.flags.map((flag, i) => (
              <div key={i} className="ms-mc-flag-item">
                <span className="ms-mc-flag-symptom">{flag.symptom}</span>
                <span className="ms-mc-flag-reason">{flag.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {result.home_care_tips && result.home_care_tips.length > 0 && (
        <div className="ms-mc-triage-section">
          <div className="ms-mc-result-label">Ghar Pe Kya Karein</div>
          <ul className="ms-mc-tips-list">
            {result.home_care_tips.map((tip, i) => (
              <li key={i}>{tip}</li>
            ))}
          </ul>
        </div>
      )}

      {result.warning_signs && result.warning_signs.length > 0 && (
        <div className="ms-mc-triage-section ms-mc-warning-section">
          <div className="ms-mc-result-label">
            <LuTriangleAlert size={13} /> Yeh Hone Par Turant Doctor Ke Paas Jao
          </div>
          <ul className="ms-mc-warnings-list">
            {result.warning_signs.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {result.disclaimer && (
        <div className="ms-mc-disclaimer">
          <LuShieldCheck size={14} /> {result.disclaimer}
        </div>
      )}
    </div>
  );
}


export default function MedicineCheck() {
  const { userId, isLoggedIn, authFetch } = useUser();

  return (
    <Layout>
      <div className="ms-page-header">
        <div className="ms-mc-page-badge">Safety Tools</div>
        <h1 className="ms-page-title">
          Medicine safety &amp; symptom check,<br />
          <span className="ms-mc-accent">before it becomes a problem.</span>
        </h1>
        <p className="ms-page-subtitle">
          Check if your medicines are safe to take together, or describe your symptoms
          and get an instant triage — home care, see a doctor, or go to emergency.
        </p>
      </div>

      <div className="ms-mc-content">
        <InteractionChecker userId={userId} isLoggedIn={isLoggedIn} authFetch={authFetch} />
        <SymptomTriage userId={userId} isLoggedIn={isLoggedIn} authFetch={authFetch} />
      </div>
    </Layout>
  );
}