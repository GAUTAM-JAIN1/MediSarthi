# P09c Deliverable Dump: Review Pack for Embedder Decision

## 1. HEADER
- **Date:** 2026-11-06
- **uv Python Version:** Python 3.11.9
- **Git Baseline:** 9375139 P09b: embedder harness to retrieval-overlap spec (evidence only, decision pending)
- **Branch:** p09-demo-backend

---

## 2. RAW INDEX
| Raw File | Bytes | SHA256 |
|---|---|---|
| `00_git.txt` | 208 | `3f12f4dbd2e40c39e0eea3e150095c87146ce1b643901eb27d454f3bd2cdc5e7` |
| `00_report_keys.txt` | 194 | `0dcb8aa1877213677a52f545ac61ad296deea5c96a73c5f258c42e3f51ffda84` |
| `02_run.txt` | 149 | `9c5ca0386c252ab4f0991f400a809fa71cca55c599cb22ddbce3bd35829dccab` |
| `03_checks.txt` | 322 | `73144cecf3c77683dd94c86e54c8afa1202828f7924fca264694d7b37d6fec56` |
| `review_pack.md` | 13766 | `6e8dcd716eac77fb5842c6e6769a4d388f50efeb2c2b41e5cb9eef6f660884e0` |

---

## 3. RAW EVIDENCE
### Step 0a: Git Status (`00_git.txt`)
```text
﻿p09-demo-backend
9375139 P09b: embedder harness to retrieval-overlap spec (evidence only, decision pending)
76f653a Demo session backend (off by default), synthetic persona, embedder comparison harness
```

### Step 0b: Report Keys (`00_report_keys.txt`)
```text
﻿Top-level keys: timestamp, doc_count, A_model, B_status, per_query, summary, note
per_query[0] keys: query, a_top_k, b_top_k, overlap, a_top_1_snippet, b_top_1_snippet
per_query count: 10
```

### Step 2a: Run Output (`02_run.txt`)
```text
﻿review_pack.py: generated 10 query sections at: C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\Project-docs\dumps\raw\P09c\review_pack.md
```

### Step 2a Generated Artifact: `review_pack.md`
```markdown
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
```

### Step 2b: Verification Checks (`03_checks.txt`)
```text
﻿CHECK 1 (exactly 10 query sections): PASS
CHECK 2 (every A top-1 id resolved to non-empty text): PASS
CHECK 3 (every B top-1 id resolved or marked B UNAVAILABLE): PASS
CHECK 4 (top-5 id lists identical to v2 report, no drift): PASS
CHECK 5 (every RATING line present and empty): PASS

OVERALL: ALL CHECKS PASSED
```

---

## 4. FULL review_pack.py CODE
```python
#!/usr/bin/env python
"""
review_pack.py — Generate a human-review markdown pack for embedder decision.

Resolves top-1 document snippets to their full chunk text from the knowledge base
and outputs a template for Gautam to rate retrieval accuracy.
DOES NOT fill in ratings, rank candidates, or make an architectural decision.
"""

import argparse
import json
import os
from pathlib import Path
import sys

# Ensure backend/scripts is on path so compare_embedders can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_embedders import load_kb_chunks

RATING_LINE = "RATING_A: ____   RATING_B: ____   (sahi / partial / galat)"


def generate_review_pack(report_path: Path, out_path: Path, kb_dir: Path) -> int:
    """Generate review_pack.md from v2 report and KB chunks.

    Returns count of resolved queries.
    """
    if not report_path.is_file():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    if not kb_dir.is_dir():
        raise FileNotFoundError(f"KB directory not found: {kb_dir}")

    chunks = load_kb_chunks(kb_dir)
    chunk_map = {doc_id: text for doc_id, text in chunks}

    per_query = report.get("per_query", [])
    a_model = report.get("A_model", "Candidate A")
    b_status = report.get("B_status", "Candidate B")

    lines = [
        "# Embedder Retrieval Review Pack (Evidence Only)",
        "",
        f"- **Candidate A:** `{a_model}`",
        f"- **Candidate B:** `{b_status}`",
        f"- **Doc Count:** {report.get('doc_count', len(chunks))}",
        f"- **Mean Top-5 Overlap:** {report.get('summary', {}).get('mean_overlap', 'N/A')}",
        "",
        "> [!IMPORTANT]",
        "> Rate each candidate's top-1 retrieved document as `sahi` (accurate/relevant), `partial` (partially relevant), or `galat` (irrelevant/misleading).",
        "> Decision on production embedder will be made after human review of these 10 queries.",
        "",
        "---",
        "",
    ]

    for idx, item in enumerate(per_query, 1):
        query_text = item.get("query", "")
        overlap = item.get("overlap")
        a_top_k = item.get("a_top_k", [])
        b_top_k = item.get("b_top_k")

        a_top_1_id = a_top_k[0] if a_top_k else None
        b_top_1_id = b_top_k[0] if b_top_k else None

        a_full_text = chunk_map.get(a_top_1_id) if a_top_1_id else None
        b_full_text = chunk_map.get(b_top_1_id) if b_top_1_id else None

        overlap_str = f"{overlap}/5" if overlap is not None else "N/A"
        lines.append(f"## Query {idx}: {query_text} (Overlap: {overlap_str})")
        lines.append("")
        lines.append(f"**Top-5 IDs ({a_model}):**")
        lines.append(", ".join(f"`{x}`" for x in a_top_k) if a_top_k else "(none)")
        lines.append("")

        if b_top_k is not None:
            lines.append(f"**Top-5 IDs ({b_status}):**")
            lines.append(", ".join(f"`{x}`" for x in b_top_k) if b_top_k else "(none)")
        else:
            lines.append(f"**Top-5 IDs ({b_status}):** B UNAVAILABLE")
        lines.append("")

        # Candidate A Top-1
        lines.append(f"### Candidate A ({a_model}) -- Top-1: `{a_top_1_id}`")
        if a_full_text:
            lines.append("```text")
            lines.append(a_full_text)
            lines.append("```")
        else:
            lines.append(f"(Unable to resolve chunk for id: {a_top_1_id})")
        lines.append("")

        # Candidate B Top-1
        if b_top_1_id is not None:
            lines.append(f"### Candidate B ({b_status}) -- Top-1: `{b_top_1_id}`")
            if b_full_text:
                lines.append("```text")
                lines.append(b_full_text)
                lines.append("```")
            else:
                lines.append(f"(Unable to resolve chunk for id: {b_top_1_id})")
        else:
            lines.append(f"### Candidate B ({b_status}) -- Top-1: B UNAVAILABLE")
        lines.append("")

        lines.append(RATING_LINE)
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return len(per_query)


def main():
    parser = argparse.ArgumentParser(description="Generate human-review markdown pack from embedder report.")
    parser.add_argument(
        "--report",
        type=str,
        required=True,
        help="Path to embedder report JSON (required).",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output markdown path (required).",
    )
    parser.add_argument(
        "--kb-dir",
        type=str,
        default="knowledge/medical_kb",
        help="Path to KB directory containing reference texts.",
    )

    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = base_dir / report_path

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = base_dir / out_path

    kb_dir = Path(args.kb_dir)
    if not kb_dir.is_absolute():
        kb_dir = base_dir / kb_dir

    count = generate_review_pack(report_path=report_path, out_path=out_path, kb_dir=kb_dir)
    print(f"review_pack.py: generated {count} query sections at: {out_path}")


if __name__ == "__main__":
    main()
```

---

## 5. CLAIMS TABLE
| Claim | Raw File Evidence | Status |
|---|---|---|
| Exactly 10 query sections generated | `03_checks.txt`, `review_pack.md` | **TRUE** |
| Every A top-1 id resolved to non-empty chunk text | `03_checks.txt`, `review_pack.md` | **TRUE** |
| Every B top-1 id resolved to non-empty chunk text | `03_checks.txt`, `review_pack.md` | **TRUE** |
| Top-5 doc ids match v2 report identically (no drift) | `03_checks.txt` | **TRUE** |
| Every RATING line is present and empty | `03_checks.txt`, `review_pack.md` | **TRUE** |
| Script never fills ratings | `backend/scripts/review_pack.py` | **TRUE** |
| Writes nothing outside $RAW | `backend/scripts/review_pack.py` | **TRUE** |
| Never writes to a production Chroma store | `backend/scripts/review_pack.py` | **TRUE** |

---

## 6. DEVIATIONS AND BLOCKERS
None

---

## 7. DEFERRED
- Embedder decision after Gautam fills the RATING lines in `Project-docs/dumps/raw/P09c/review_pack.md`
- P10 frontend demo integration
