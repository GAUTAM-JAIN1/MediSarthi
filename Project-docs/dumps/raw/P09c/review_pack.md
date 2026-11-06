# Embedder Retrieval Review Pack (Evidence Only)

- **Candidate A:** `chromadb-default`
- **Candidate B:** `mxbai-embed-large`
- **Doc Count:** 126
- **Mean Top-5 Overlap:** 2.5

> [!IMPORTANT]
> Rate each candidate's top-1 retrieved document as `sahi` (accurate/relevant), `partial` (partially relevant), or `galat` (irrelevant/misleading).
> Decision on production embedder will be made after human review of these 10 queries.

---

## Query 1: paracetamol safe for liver patient (Overlap: 3/5)

**Top-5 IDs (chromadb-default):**
`drug_interactions.txt#16`, `drug_interactions.txt#23`, `symptom_red_flags.txt#2`, `medicine_response_timelines.txt#27`, `drug_interactions.txt#3`

**Top-5 IDs (mxbai-embed-large):**
`drug_interactions.txt#16`, `symptom_red_flags.txt#2`, `test_direction_reference.txt#23`, `drug_interactions.txt#23`, `lab_reference_ranges.txt#21`

### Candidate A (chromadb-default) -- Top-1: `drug_interactions.txt#16`
```text
Paracetamol (Acetaminophen) + Alcohol (regular, heavy use): Both are processed
by the liver; regular heavy alcohol use alongside frequent Paracetamol use
raises risk of liver damage. Occasional standard-dose Paracetamol with
moderate alcohol is generally considered low risk; the concern is chronic
heavy combined use.
```

### Candidate B (mxbai-embed-large) -- Top-1: `drug_interactions.txt#16`
```text
Paracetamol (Acetaminophen) + Alcohol (regular, heavy use): Both are processed
by the liver; regular heavy alcohol use alongside frequent Paracetamol use
raises risk of liver damage. Occasional standard-dose Paracetamol with
moderate alcohol is generally considered low risk; the concern is chronic
heavy combined use.
```

RATING_A: ____   RATING_B: ____   (sahi / partial / galat)

---

## Query 2: amoxicillin 500mg daily dose (Overlap: 1/5)

**Top-5 IDs (chromadb-default):**
`drug_interactions.txt#3`, `lab_reference_ranges.txt#18`, `drug_interactions.txt#18`, `drug_interactions.txt#22`, `medicine_response_timelines.txt#11`

**Top-5 IDs (mxbai-embed-large):**
`drug_interactions.txt#17`, `drug_interactions.txt#15`, `symptom_red_flags.txt#2`, `medicine_response_timelines.txt#1`, `lab_reference_ranges.txt#18`

### Candidate A (chromadb-default) -- Top-1: `drug_interactions.txt#3`
```text
Warfarin + Antibiotics (Ciprofloxacin, Metronidazole, many others): Several
common antibiotics inhibit the liver enzymes that clear Warfarin, raising INR
and bleeding risk. Usually needs more frequent INR monitoring during and after
antibiotic course, not necessarily avoidance.
```

### Candidate B (mxbai-embed-large) -- Top-1: `drug_interactions.txt#17`
```text
Antacids (containing Calcium, Magnesium, or Aluminum) + many antibiotics
(Tetracyclines, Fluoroquinolones like Ciprofloxacin): Antacids can bind the
antibiotic in the gut and reduce absorption significantly. Usually managed by
simply spacing doses at least 2 hours apart — a timing interaction, not a
true contraindication.
```

RATING_A: ____   RATING_B: ____   (sahi / partial / galat)

---

## Query 3: metformin empty stomach or after food (Overlap: 3/5)

**Top-5 IDs (chromadb-default):**
`drug_interactions.txt#13`, `medicine_response_timelines.txt#5`, `medicine_response_timelines.txt#4`, `symptom_red_flags.txt#6`, `lab_reference_ranges.txt#7`

**Top-5 IDs (mxbai-embed-large):**
`lab_reference_ranges.txt#7`, `medicine_response_timelines.txt#5`, `drug_interactions.txt#13`, `test_direction_reference.txt#10`, `medicine_response_timelines.txt#6`

### Candidate A (chromadb-default) -- Top-1: `drug_interactions.txt#13`
```text
Metformin + Contrast dye (used in some imaging scans): Rare risk of lactic
acidosis if kidney function is reduced around the time of contrast imaging.
Doctors typically pause Metformin briefly around such procedures — this is a
procedural interaction, not a general everyday-use one.
```

### Candidate B (mxbai-embed-large) -- Top-1: `lab_reference_ranges.txt#7`
```text
Post-Prandial (2hr after meal): Normal <140 mg/dL. Prediabetes 140–199 mg/dL.
Diabetes ≥200 mg/dL.
```

RATING_A: ____   RATING_B: ____   (sahi / partial / galat)

---

## Query 4: cetirizine makes me sleepy alternatives (Overlap: 3/5)

**Top-5 IDs (chromadb-default):**
`drug_interactions.txt#11`, `drug_interactions.txt#23`, `drug_interactions.txt#18`, `drug_interactions.txt#14`, `drug_interactions.txt#22`

**Top-5 IDs (mxbai-embed-large):**
`drug_interactions.txt#23`, `drug_interactions.txt#21`, `drug_interactions.txt#18`, `drug_interactions.txt#20`, `drug_interactions.txt#22`

### Candidate A (chromadb-default) -- Top-1: `drug_interactions.txt#11`
```text
Beta-blockers (Atenolol, Metoprolol) + Verapamil/Diltiazem (calcium channel
blockers): Both slow heart rate and reduce contraction strength; combined use
can cause dangerously slow heart rate or worsen heart failure. Usually
Moderate to Major, dose-dependent.
```

### Candidate B (mxbai-embed-large) -- Top-1: `drug_interactions.txt#23`
```text
Paracetamol (Acetaminophen) — Dolo 650, Crocin, Calpol, Paracip, P-500, Fepanil
Ibuprofen — Brufen, Combiflam (also contains Paracetamol)
Cetirizine — Cetzine, Alerid, Okacet
Domperidone — Domstal, Vomistop
Pantoprazole — Pantocid, Pan-D (also contains Domperidone)
```

RATING_A: ____   RATING_B: ____   (sahi / partial / galat)

---

## Query 5: atorvastatin side effects muscle pain (Overlap: 2/5)

**Top-5 IDs (chromadb-default):**
`medicine_response_timelines.txt#15`, `medicine_response_timelines.txt#14`, `drug_interactions.txt#11`, `medicine_response_timelines.txt#17`, `symptom_red_flags.txt#16`

**Top-5 IDs (mxbai-embed-large):**
`medicine_response_timelines.txt#15`, `medicine_response_timelines.txt#14`, `symptom_red_flags.txt#7`, `medicine_response_timelines.txt#19`, `medicine_response_timelines.txt#16`

### Candidate A (chromadb-default) -- Top-1: `medicine_response_timelines.txt#15`
```text
Rosuvastatin
  - Total Cholesterol / LDL Cholesterol / Triglycerides: same general
    window as Atorvastatin above — 4-6 weeks for initial movement,
    8-12 weeks for the fuller, more stable effect. Considered slightly
    more potent per-mg than Atorvastatin but the response timeline is
    comparable.
  - HDL Cholesterol: same caveat as Atorvastatin — smaller, more variable
    effect, don't judge this as the main marker of response.
```

### Candidate B (mxbai-embed-large) -- Top-1: `medicine_response_timelines.txt#15`
```text
Rosuvastatin
  - Total Cholesterol / LDL Cholesterol / Triglycerides: same general
    window as Atorvastatin above — 4-6 weeks for initial movement,
    8-12 weeks for the fuller, more stable effect. Considered slightly
    more potent per-mg than Atorvastatin but the response timeline is
    comparable.
  - HDL Cholesterol: same caveat as Atorvastatin — smaller, more variable
    effect, don't judge this as the main marker of response.
```

RATING_A: ____   RATING_B: ____   (sahi / partial / galat)

---

## Query 6: azithromycin course 3 days or 5 days (Overlap: 2/5)

**Top-5 IDs (chromadb-default):**
`medicine_response_timelines.txt#28`, `drug_interactions.txt#17`, `medicine_response_timelines.txt#16`, `symptom_red_flags.txt#7`, `medicine_response_timelines.txt#29`

**Top-5 IDs (mxbai-embed-large):**
`medicine_response_timelines.txt#12`, `medicine_response_timelines.txt#28`, `medicine_response_timelines.txt#29`, `symptom_red_flags.txt#3`, `medicine_response_timelines.txt#11`

### Candidate A (chromadb-default) -- Top-1: `medicine_response_timelines.txt#28`
```text
Allopurinol
  - Uric Acid: gradual, dose-dependent lowering — meaningful reduction
    typically takes 2-4 weeks, with the fuller effect often not reached
    until 6-8 weeks, especially if the dose is being titrated upward
    over that period (common practice with this medicine).
```

### Candidate B (mxbai-embed-large) -- Top-1: `medicine_response_timelines.txt#12`
```text
Carbimazole
  - TSH: used for the opposite direction (overactive thyroid) — response
    is often faster to begin (some early effect within 1-2 weeks) but
    can take 4-8 weeks for TSH/T3/T4 to fully normalize, and dose is
    often adjusted more than once along the way.
  - Free T3 / Free T4: often the first to show visible improvement,
    sometimes within 2-3 weeks, ahead of TSH normalizing.
```

RATING_A: ____   RATING_B: ____   (sahi / partial / galat)

---

## Query 7: pantoprazole 40mg before breakfast (Overlap: 1/5)

**Top-5 IDs (chromadb-default):**
`drug_interactions.txt#23`, `drug_interactions.txt#18`, `drug_interactions.txt#6`, `medicine_response_timelines.txt#34`, `symptom_red_flags.txt#6`

**Top-5 IDs (mxbai-embed-large):**
`drug_interactions.txt#23`, `lab_reference_ranges.txt#7`, `drug_interactions.txt#17`, `medicine_response_timelines.txt#5`, `symptom_red_flags.txt#2`

### Candidate A (chromadb-default) -- Top-1: `drug_interactions.txt#23`
```text
Paracetamol (Acetaminophen) — Dolo 650, Crocin, Calpol, Paracip, P-500, Fepanil
Ibuprofen — Brufen, Combiflam (also contains Paracetamol)
Cetirizine — Cetzine, Alerid, Okacet
Domperidone — Domstal, Vomistop
Pantoprazole — Pantocid, Pan-D (also contains Domperidone)
```

### Candidate B (mxbai-embed-large) -- Top-1: `drug_interactions.txt#23`
```text
Paracetamol (Acetaminophen) — Dolo 650, Crocin, Calpol, Paracip, P-500, Fepanil
Ibuprofen — Brufen, Combiflam (also contains Paracetamol)
Cetirizine — Cetzine, Alerid, Okacet
Domperidone — Domstal, Vomistop
Pantoprazole — Pantocid, Pan-D (also contains Domperidone)
```

RATING_A: ____   RATING_B: ____   (sahi / partial / galat)

---

## Query 8: losartan potassium blood pressure normal range (Overlap: 4/5)

**Top-5 IDs (chromadb-default):**
`medicine_response_timelines.txt#20`, `medicine_response_timelines.txt#19`, `drug_interactions.txt#10`, `medicine_response_timelines.txt#17`, `lab_reference_ranges.txt#19`

**Top-5 IDs (mxbai-embed-large):**
`medicine_response_timelines.txt#19`, `drug_interactions.txt#10`, `medicine_response_timelines.txt#20`, `medicine_response_timelines.txt#21`, `lab_reference_ranges.txt#19`

### Candidate A (chromadb-default) -- Top-1: `medicine_response_timelines.txt#20`
```text
Telmisartan
  - Creatinine / Blood Urea: same ARB-class pattern as Losartan above —
    a small expected initial rise that should stabilize within 2-4 weeks.
```

### Candidate B (mxbai-embed-large) -- Top-1: `medicine_response_timelines.txt#19`
```text
Losartan
  - Creatinine / Blood Urea: Losartan (an ARB) can cause a small, often
    expected initial rise in Creatinine when first started or when the
    dose increases — usually stabilizes within 2-4 weeks. A modest early
    increase is not automatically a bad sign; a large or continuously
    rising Creatinine, or one that hasn't stabilized by 4-6 weeks,
    is what's actually worth flagging to a doctor.
```

RATING_A: ____   RATING_B: ____   (sahi / partial / galat)

---

## Query 9: ciprofloxacin interaction with milk dairy (Overlap: 2/5)

**Top-5 IDs (chromadb-default):**
`drug_interactions.txt#3`, `drug_interactions.txt#17`, `test_direction_reference.txt#8`, `drug_interactions.txt#23`, `symptom_red_flags.txt#19`

**Top-5 IDs (mxbai-embed-large):**
`drug_interactions.txt#17`, `drug_interactions.txt#3`, `drug_interactions.txt#20`, `drug_interactions.txt#22`, `drug_interactions.txt#15`

### Candidate A (chromadb-default) -- Top-1: `drug_interactions.txt#3`
```text
Warfarin + Antibiotics (Ciprofloxacin, Metronidazole, many others): Several
common antibiotics inhibit the liver enzymes that clear Warfarin, raising INR
and bleeding risk. Usually needs more frequent INR monitoring during and after
antibiotic course, not necessarily avoidance.
```

### Candidate B (mxbai-embed-large) -- Top-1: `drug_interactions.txt#17`
```text
Antacids (containing Calcium, Magnesium, or Aluminum) + many antibiotics
(Tetracyclines, Fluoroquinolones like Ciprofloxacin): Antacids can bind the
antibiotic in the gut and reduce absorption significantly. Usually managed by
simply spacing doses at least 2 hours apart — a timing interaction, not a
true contraindication.
```

RATING_A: ____   RATING_B: ____   (sahi / partial / galat)

---

## Query 10: aspirin 75mg blood thinner bruising (Overlap: 4/5)

**Top-5 IDs (chromadb-default):**
`lab_reference_ranges.txt#4`, `drug_interactions.txt#2`, `drug_interactions.txt#4`, `drug_interactions.txt#3`, `drug_interactions.txt#8`

**Top-5 IDs (mxbai-embed-large):**
`drug_interactions.txt#2`, `lab_reference_ranges.txt#4`, `drug_interactions.txt#4`, `drug_interactions.txt#8`, `drug_interactions.txt#21`

### Candidate A (chromadb-default) -- Top-1: `lab_reference_ranges.txt#4`
```text
Platelet count: ~150,000–450,000/µL. Low = increased bleeding/bruising risk
(causes: viral infection like dengue, some medications, autoimmune conditions).
High = can occur with inflammation, iron deficiency, or after major bleeding.
```

### Candidate B (mxbai-embed-large) -- Top-1: `drug_interactions.txt#2`
```text
Warfarin + Aspirin (or other NSAIDs like Ibuprofen, Diclofenac): Both increase
bleeding risk through different mechanisms (Warfarin blocks clotting factors,
NSAIDs affect platelet function and can irritate the GI lining). Combined use
significantly raises risk of serious bleeding, especially GI bleeds. Generally
classified Major to Contraindicated depending on dose/duration. Requires close
doctor supervision if unavoidable.
```

RATING_A: ____   RATING_B: ____   (sahi / partial / galat)

---
