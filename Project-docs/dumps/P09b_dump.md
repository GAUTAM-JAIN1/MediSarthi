# P09b Deliverable Dump: Embedder Harness Rewrite to Retrieval Overlap Spec

## 1. HEADER
- **Date:** 2026-11-05
- **uv Python Version:** Python 3.11.9
- **Git Commit Baseline:** 76f653a Demo session backend (off by default), synthetic persona, embedder comparison harness
- **Branch:** p09-demo-backend

---

## 2. RAW INDEX
| Raw File | Bytes | SHA256 |
|---|---|---|
| `00_chroma.txt` | 19 | `88432cd23b95fbb70b12f76c44cc7ad86c7ec8e54a255d579221816460cf6c11` |
| `00_git.txt` | 288 | `cef3c78b06c813869d82b03241df12d2fd461f653ac3cf09cd15eb5a704c1807` |
| `00_kb_source.txt` | 948 | `414a1f43e31b263d7bc971cbc85cedc3be8e344765dcfe009257960d82214d5b` |
| `00_ollama_tags.txt` | 144 | `d4c3e865f934972b8185716233ac72459735a3b9a26c879aaa9827d1cf3d5e20` |
| `00_queries_shape.txt` | 274 | `d52172f495403b1fb6d76ab12acab71b418845441dbe67913db8960a4195ada5` |
| `01_help.txt` | 694 | `7902b9a95382ab6758c9b986a3dd9398c6fec8b0cae144db59c981212da9b25a` |
| `02_run.txt` | 239 | `2fd8ba69a47948cae2d9e2e43e73cae3b0aa2c71245f2f1f1c7ee30fb237bda3` |
| `03_report_checks.txt` | 232 | `544f0847d6674281d99a4dc7fe91e868efbe6c54ce2a0405c5e410c4e3c71573` |
| `04_invariants.txt` | 237 | `a6bfd3c330cb00225b475758c3add860a891d6b2387129fa348aa04316111bfb` |
| `embedder_report_v2.json` | 8908 | `0c0e19555750692e28f092adda7647ba39e01d0599c4ee47cb17d7d8599b6ee7` |

---

## 3. RAW EVIDENCE (STEPS 0 TO 4)
### Step 0a: Git Status (`00_git.txt`)
```text
﻿p09-demo-backend
76f653a Demo session backend (off by default), synthetic persona, embedder comparison harness
3ac4aa5 Merge pull request #5 from GAUTAM-JAIN1/hero-24-7-claims
13cd47b Hero: replace remaining unverified claims (24/7, booking, verified doctors) with app-backed text
```

### Step 0b: KB Source Directory & Files (`00_kb_source.txt`)
```text
﻿KB_DIR: C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\knowledge\medical_kb

Name                            Length FullName                                                                        
----                            ------ --------                                                                        
drug_interactions.txt             5900 C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\knowledge\medic...
lab_reference_ranges.txt          4151 C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\knowledge\medic...
medicine_response_timelines.txt  12656 C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\knowledge\medic...
symptom_red_flags.txt             4686 C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\knowledge\medic...
test_direction_reference.txt      7636 C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\knowledge\medic...
```

### Step 0c: Query File Shape (`00_queries_shape.txt`)
```text
﻿Top-level keys: status, queries
Queries count: 10
First 200 chars: {
  "status": "PROPOSED - not approved",
  "queries": [
    "paracetamol safe for liver patient",
    "amoxicillin 500mg daily dose",
    "metformin empty stomach or after food",
    "cetirizine makes
```

### Step 0d: ChromaDB Import Check (`00_chroma.txt`)
```text
﻿chromadb 1.1.1
```

### Step 0e: Ollama Model Tags (`00_ollama_tags.txt`)
```text
﻿NAME                        ID              SIZE      MODIFIED     
mxbai-embed-large:latest    468836162de7    669 MB    4 months ago
```

### Step 1: Comparison CLI Help (`01_help.txt`)
```text
﻿usage: compare_embedders.py [-h] [--queries QUERIES] --out OUT
                            [--ollama-host OLLAMA_HOST] [--top-k TOP_K]

Compare retrieval overlap between Chroma default and Ollama mxbai-embed-large.

options:
  -h, --help            show this help message and exit
  --queries QUERIES     Path to JSON file containing queries array.
  --out OUT             Output path for the comparison JSON report (required).
  --ollama-host OLLAMA_HOST
                        Localhost Ollama endpoint (default:
                        http://127.0.0.1:11434).
  --top-k TOP_K         Number of nearest neighbors to retrieve per query
                        (default: 5).
```

### Step 2: Comparison Execution Output (`02_run.txt`)
```text
﻿Report written to: C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\Project-docs\dumps\raw\P09b\embedder_report_v2.json
Chunks indexed: 126, Queries: 10, B status: mxbai-embed-large
Mean top-5 overlap: 2.5
runtime_seconds=32.4
```

### Step 2 Report Artifact: `embedder_report_v2.json`
```json
{
  "timestamp": "2026-11-05T07:20:07.201145Z",
  "doc_count": 126,
  "A_model": "chromadb-default",
  "B_status": "mxbai-embed-large",
  "per_query": [
    {
      "query": "paracetamol safe for liver patient",
      "a_top_k": [
        "drug_interactions.txt#16",
        "drug_interactions.txt#23",
        "symptom_red_flags.txt#2",
        "medicine_response_timelines.txt#27",
        "drug_interactions.txt#3"
      ],
      "b_top_k": [
        "drug_interactions.txt#16",
        "symptom_red_flags.txt#2",
        "test_direction_reference.txt#23",
        "drug_interactions.txt#23",
        "lab_reference_ranges.txt#21"
      ],
      "overlap": 3,
      "a_top_1_snippet": "Paracetamol (Acetaminophen) + Alcohol (regular, heavy use): Both are processed\nby the liver; regular heavy alcohol use a",
      "b_top_1_snippet": "Paracetamol (Acetaminophen) + Alcohol (regular, heavy use): Both are processed\nby the liver; regular heavy alcohol use a"
    },
    {
      "query": "amoxicillin 500mg daily dose",
      "a_top_k": [
        "drug_interactions.txt#3",
        "lab_reference_ranges.txt#18",
        "drug_interactions.txt#18",
        "drug_interactions.txt#22",
        "medicine_response_timelines.txt#11"
      ],
      "b_top_k": [
        "drug_interactions.txt#17",
        "drug_interactions.txt#15",
        "symptom_red_flags.txt#2",
        "medicine_response_timelines.txt#1",
        "lab_reference_ranges.txt#18"
      ],
      "overlap": 1,
      "a_top_1_snippet": "Warfarin + Antibiotics (Ciprofloxacin, Metronidazole, many others): Several\ncommon antibiotics inhibit the liver enzymes",
      "b_top_1_snippet": "Antacids (containing Calcium, Magnesium, or Aluminum) + many antibiotics\n(Tetracyclines, Fluoroquinolones like Ciproflox"
    },
    {
      "query": "metformin empty stomach or after food",
      "a_top_k": [
        "drug_interactions.txt#13",
        "medicine_response_timelines.txt#5",
        "medicine_response_timelines.txt#4",
        "symptom_red_flags.txt#6",
        "lab_reference_ranges.txt#7"
      ],
      "b_top_k": [
        "lab_reference_ranges.txt#7",
        "medicine_response_timelines.txt#5",
        "drug_interactions.txt#13",
        "test_direction_reference.txt#10",
        "medicine_response_timelines.txt#6"
      ],
      "overlap": 3,
      "a_top_1_snippet": "Metformin + Contrast dye (used in some imaging scans): Rare risk of lactic\nacidosis if kidney function is reduced around",
      "b_top_1_snippet": "Post-Prandial (2hr after meal): Normal <140 mg/dL. Prediabetes 140\u2013199 mg/dL.\nDiabetes \u2265200 mg/dL."
    },
    {
      "query": "cetirizine makes me sleepy alternatives",
      "a_top_k": [
        "drug_interactions.txt#11",
        "drug_interactions.txt#23",
        "drug_interactions.txt#18",
        "drug_interactions.txt#14",
        "drug_interactions.txt#22"
      ],
      "b_top_k": [
        "drug_interactions.txt#23",
        "drug_interactions.txt#21",
        "drug_interactions.txt#18",
        "drug_interactions.txt#20",
        "drug_interactions.txt#22"
      ],
      "overlap": 3,
      "a_top_1_snippet": "Beta-blockers (Atenolol, Metoprolol) + Verapamil/Diltiazem (calcium channel\nblockers): Both slow heart rate and reduce c",
      "b_top_1_snippet": "Paracetamol (Acetaminophen) \u2014 Dolo 650, Crocin, Calpol, Paracip, P-500, Fepanil\nIbuprofen \u2014 Brufen, Combiflam (also cont"
    },
    {
      "query": "atorvastatin side effects muscle pain",
      "a_top_k": [
        "medicine_response_timelines.txt#15",
        "medicine_response_timelines.txt#14",
        "drug_interactions.txt#11",
        "medicine_response_timelines.txt#17",
        "symptom_red_flags.txt#16"
      ],
      "b_top_k": [
        "medicine_response_timelines.txt#15",
        "medicine_response_timelines.txt#14",
        "symptom_red_flags.txt#7",
        "medicine_response_timelines.txt#19",
        "medicine_response_timelines.txt#16"
      ],
      "overlap": 2,
      "a_top_1_snippet": "Rosuvastatin\n  - Total Cholesterol / LDL Cholesterol / Triglycerides: same general\n    window as Atorvastatin above \u2014 4-",
      "b_top_1_snippet": "Rosuvastatin\n  - Total Cholesterol / LDL Cholesterol / Triglycerides: same general\n    window as Atorvastatin above \u2014 4-"
    },
    {
      "query": "azithromycin course 3 days or 5 days",
      "a_top_k": [
        "medicine_response_timelines.txt#28",
        "drug_interactions.txt#17",
        "medicine_response_timelines.txt#16",
        "symptom_red_flags.txt#7",
        "medicine_response_timelines.txt#29"
      ],
      "b_top_k": [
        "medicine_response_timelines.txt#12",
        "medicine_response_timelines.txt#28",
        "medicine_response_timelines.txt#29",
        "symptom_red_flags.txt#3",
        "medicine_response_timelines.txt#11"
      ],
      "overlap": 2,
      "a_top_1_snippet": "Allopurinol\n  - Uric Acid: gradual, dose-dependent lowering \u2014 meaningful reduction\n    typically takes 2-4 weeks, with t",
      "b_top_1_snippet": "Carbimazole\n  - TSH: used for the opposite direction (overactive thyroid) \u2014 response\n    is often faster to begin (some "
    },
    {
      "query": "pantoprazole 40mg before breakfast",
      "a_top_k": [
        "drug_interactions.txt#23",
        "drug_interactions.txt#18",
        "drug_interactions.txt#6",
        "medicine_response_timelines.txt#34",
        "symptom_red_flags.txt#6"
      ],
      "b_top_k": [
        "drug_interactions.txt#23",
        "lab_reference_ranges.txt#7",
        "drug_interactions.txt#17",
        "medicine_response_timelines.txt#5",
        "symptom_red_flags.txt#2"
      ],
      "overlap": 1,
      "a_top_1_snippet": "Paracetamol (Acetaminophen) \u2014 Dolo 650, Crocin, Calpol, Paracip, P-500, Fepanil\nIbuprofen \u2014 Brufen, Combiflam (also cont",
      "b_top_1_snippet": "Paracetamol (Acetaminophen) \u2014 Dolo 650, Crocin, Calpol, Paracip, P-500, Fepanil\nIbuprofen \u2014 Brufen, Combiflam (also cont"
    },
    {
      "query": "losartan potassium blood pressure normal range",
      "a_top_k": [
        "medicine_response_timelines.txt#20",
        "medicine_response_timelines.txt#19",
        "drug_interactions.txt#10",
        "medicine_response_timelines.txt#17",
        "lab_reference_ranges.txt#19"
      ],
      "b_top_k": [
        "medicine_response_timelines.txt#19",
        "drug_interactions.txt#10",
        "medicine_response_timelines.txt#20",
        "medicine_response_timelines.txt#21",
        "lab_reference_ranges.txt#19"
      ],
      "overlap": 4,
      "a_top_1_snippet": "Telmisartan\n  - Creatinine / Blood Urea: same ARB-class pattern as Losartan above \u2014\n    a small expected initial rise th",
      "b_top_1_snippet": "Losartan\n  - Creatinine / Blood Urea: Losartan (an ARB) can cause a small, often\n    expected initial rise in Creatinine"
    },
    {
      "query": "ciprofloxacin interaction with milk dairy",
      "a_top_k": [
        "drug_interactions.txt#3",
        "drug_interactions.txt#17",
        "test_direction_reference.txt#8",
        "drug_interactions.txt#23",
        "symptom_red_flags.txt#19"
      ],
      "b_top_k": [
        "drug_interactions.txt#17",
        "drug_interactions.txt#3",
        "drug_interactions.txt#20",
        "drug_interactions.txt#22",
        "drug_interactions.txt#15"
      ],
      "overlap": 2,
      "a_top_1_snippet": "Warfarin + Antibiotics (Ciprofloxacin, Metronidazole, many others): Several\ncommon antibiotics inhibit the liver enzymes",
      "b_top_1_snippet": "Antacids (containing Calcium, Magnesium, or Aluminum) + many antibiotics\n(Tetracyclines, Fluoroquinolones like Ciproflox"
    },
    {
      "query": "aspirin 75mg blood thinner bruising",
      "a_top_k": [
        "lab_reference_ranges.txt#4",
        "drug_interactions.txt#2",
        "drug_interactions.txt#4",
        "drug_interactions.txt#3",
        "drug_interactions.txt#8"
      ],
      "b_top_k": [
        "drug_interactions.txt#2",
        "lab_reference_ranges.txt#4",
        "drug_interactions.txt#4",
        "drug_interactions.txt#8",
        "drug_interactions.txt#21"
      ],
      "overlap": 4,
      "a_top_1_snippet": "Platelet count: ~150,000\u2013450,000/\u00b5L. Low = increased bleeding/bruising risk\n(causes: viral infection like dengue, some m",
      "b_top_1_snippet": "Warfarin + Aspirin (or other NSAIDs like Ibuprofen, Diclofenac): Both increase\nbleeding risk through different mechanism"
    }
  ],
  "summary": {
    "mean_overlap": 2.5
  },
  "note": "EVIDENCE ONLY. No winner. Human review of top-1 snippets is required before any embedder decision."
}
```

### Step 3: Report Verification Checks (`03_report_checks.txt`)
```text
﻿CHECK 1 (per_query len == 10): PASS
CHECK 2 (overlaps in 0..5): PASS
CHECK 3 (B status recorded): PASS -> mxbai-embed-large
CHECK 4 (doc_count > 0): PASS -> 126
CHECK 5 (note field exact): PASS

OVERALL: ALL CHECKS PASSED
```

### Step 4: OpenAPI Invariants Verification (`04_invariants.txt`)
```text
﻿OPERATIONS 44
OPENAPI_SHA256 2c3de56bfa32bf13518faeae6b9fb81377344dccbb188dcd2a779c0b6ba6ca42
EXPECTED_OPERATIONS 44
EXPECTED_OPENAPI_SHA256 2c3de56bfa32bf13518faeae6b9fb81377344dccbb188dcd2a779c0b6ba6ca42
INVARIANTS MATCH: PASS
```

---

## 4. FULL REWRITTEN compare_embedders.py
```python
#!/usr/bin/env python
"""
compare_embedders.py — Embedder retrieval overlap comparison harness.

Compares retrieval overlap and top-1 snippets between Chroma's default embedder (A)
and Ollama's mxbai-embed-large (B) on the MediSarthi knowledge base.
DOES NOT measure latency, RSS, or declare a winner.
"""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Dict, List, Optional
import urllib.parse
import urllib.request

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

FIXED_NOTE = "EVIDENCE ONLY. No winner. Human review of top-1 snippets is required before any embedder decision."


def validate_localhost(host: str) -> str:
    """Ensure ollama-host is strictly localhost or 127.0.0.1."""
    parsed = urllib.parse.urlparse(host)
    hostname = parsed.hostname or ""
    if hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError(f"Only localhost is allowed for ollama-host, got: {hostname}")
    return host


class OllamaEmbeddingFunction(EmbeddingFunction[Documents]):
    """Custom Chroma embedding function querying a local Ollama instance."""

    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: Embeddings = []
        for text in input:
            url = f"{self.host}/api/embeddings"
            payload = json.dumps({"model": self.model, "prompt": text}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "MediSarthi-Harness"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                embeddings.append(data["embedding"])
        return embeddings


def check_mxbai_available(host: str) -> bool:
    """Check whether mxbai-embed-large is present in local Ollama tags."""
    url = f"{host.rstrip('/')}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MediSarthi-Harness"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for m in data.get("models", []):
                name = m.get("name", "")
                if name == "mxbai-embed-large" or name.startswith("mxbai-embed-large:"):
                    return True
            return False
    except Exception:
        return False


def load_kb_chunks(kb_dir: Path) -> List[tuple[str, str]]:
    """Read all text files in KB directory, split on blank lines, keep chunks 40..1200 chars."""
    chunks: List[tuple[str, str]] = []
    for f in sorted(kb_dir.rglob("*.txt")):
        rel_path = f.relative_to(kb_dir).as_posix()
        text = f.read_text(encoding="utf-8")
        raw_parts = re.split(r"\n\s*\n", text)
        for idx, part in enumerate(raw_parts):
            p_strip = part.strip()
            if 40 <= len(p_strip) <= 1200:
                doc_id = f"{rel_path}#{idx}"
                chunks.append((doc_id, p_strip))
    return chunks


def main():
    parser = argparse.ArgumentParser(
        description="Compare retrieval overlap between Chroma default and Ollama mxbai-embed-large."
    )
    parser.add_argument(
        "--queries",
        type=str,
        default="data/demo/embedder_queries.json",
        help="Path to JSON file containing queries array.",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output path for the comparison JSON report (required).",
    )
    parser.add_argument(
        "--ollama-host",
        type=str,
        default="http://127.0.0.1:11434",
        help="Localhost Ollama endpoint (default: http://127.0.0.1:11434).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of nearest neighbors to retrieve per query (default: 5).",
    )

    args = parser.parse_args()

    # Validate host
    ollama_host = validate_localhost(args.ollama_host)

    # Locate paths
    base_dir = Path(__file__).resolve().parents[1]
    q_path = Path(args.queries)
    if not q_path.is_absolute():
        q_path = base_dir / q_path

    if not q_path.is_file():
        raise FileNotFoundError(f"Queries file not found at: {q_path}")

    with open(q_path, "r", encoding="utf-8") as f:
        q_raw = json.load(f)

    if isinstance(q_raw, dict) and "queries" in q_raw:
        queries = q_raw["queries"]
    elif isinstance(q_raw, list):
        queries = q_raw
    else:
        raise ValueError(f"Unrecognized queries file shape: {type(q_raw)}")

    # Locate KB directory
    kb_dir = base_dir / "knowledge" / "medical_kb"
    if not kb_dir.is_dir():
        raise FileNotFoundError(f"KB directory not found: {kb_dir}")

    chunks = load_kb_chunks(kb_dir)
    doc_count = len(chunks)
    if doc_count == 0:
        raise RuntimeError(f"No valid chunks found in KB directory: {kb_dir}")

    doc_ids = [c[0] for c in chunks]
    doc_texts = [c[1] for c in chunks]

    temp_dir = tempfile.mkdtemp(prefix="chroma_cmp_")

    try:
        # Collection A: chromadb default
        db_path_a = os.path.join(temp_dir, "db_a")
        client_a = chromadb.PersistentClient(path=db_path_a)
        col_a = client_a.get_or_create_collection(name="kb_default")
        col_a.add(ids=doc_ids, documents=doc_texts)
        a_model = "chromadb-default"

        # Collection B: Ollama mxbai-embed-large (if available)
        mxbai_ok = check_mxbai_available(ollama_host)
        col_b = None
        if mxbai_ok:
            b_status = "mxbai-embed-large"
            db_path_b = os.path.join(temp_dir, "db_b")
            client_b = chromadb.PersistentClient(path=db_path_b)
            ef_b = OllamaEmbeddingFunction(host=ollama_host, model="mxbai-embed-large")
            col_b = client_b.get_or_create_collection(name="kb_ollama_mxbai", embedding_function=ef_b)
            col_b.add(ids=doc_ids, documents=doc_texts)
        else:
            b_status = "UNAVAILABLE: mxbai-embed-large not pulled"

        # Query both collections
        per_query_results = []
        overlap_values = []

        for q in queries:
            # Query A
            res_a = col_a.query(query_texts=[q], n_results=args.top_k)
            a_top_k = res_a["ids"][0] if res_a.get("ids") else []
            a_snippets = res_a["documents"][0] if res_a.get("documents") else []
            a_top_1_snippet = a_snippets[0][:120] if a_snippets else ""

            # Query B
            if col_b is not None:
                res_b = col_b.query(query_texts=[q], n_results=args.top_k)
                b_top_k = res_b["ids"][0] if res_b.get("ids") else []
                b_snippets = res_b["documents"][0] if res_b.get("documents") else []
                b_top_1_snippet = b_snippets[0][:120] if b_snippets else ""

                overlap = len(set(a_top_k) & set(b_top_k))
                overlap_values.append(overlap)
            else:
                b_top_k = None
                b_top_1_snippet = None
                overlap = None

            per_query_results.append({
                "query": q,
                "a_top_k": a_top_k,
                "b_top_k": b_top_k,
                "overlap": overlap,
                "a_top_1_snippet": a_top_1_snippet,
                "b_top_1_snippet": b_top_1_snippet,
            })

        mean_overlap = (
            round(sum(overlap_values) / len(overlap_values), 2)
            if overlap_values
            else None
        )

        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "doc_count": doc_count,
            "A_model": a_model,
            "B_status": b_status,
            "per_query": per_query_results,
            "summary": {
                "mean_overlap": mean_overlap,
            },
            "note": FIXED_NOTE,
        }

        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = base_dir / out_path

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"Report written to: {out_path}")
        print(f"Chunks indexed: {doc_count}, Queries: {len(queries)}, B status: {b_status}")
        if mean_overlap is not None:
            print(f"Mean top-{args.top_k} overlap: {mean_overlap}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
```

---

## 5. CLAIMS TABLE
| Claim | Raw File Evidence | Status |
|---|---|---|
| `doc_count` greater than 0 | `02_run.txt`, `03_report_checks.txt` (126 chunks) | **TRUE** |
| Query count matches step 0c (10 queries) | `00_queries_shape.txt`, `03_report_checks.txt` | **TRUE** |
| Overlap values valid (integers 0..5) | `03_report_checks.txt`, `embedder_report_v2.json` | **TRUE** |
| B status matches the Ollama list (`mxbai-embed-large`) | `00_ollama_tags.txt`, `03_report_checks.txt` | **TRUE** |
| Runtime under 600 seconds (`32.4s`) | `02_run.txt` (`runtime_seconds=32.4`) | **TRUE** |
| Invariants unchanged (`OPERATIONS 44`, SHA256 matches P09) | `04_invariants.txt` | **TRUE** |
| No HuggingFace or sentence-transformers used | `backend/scripts/compare_embedders.py` | **TRUE** |
| No production store written (temp dir used) | `backend/scripts/compare_embedders.py` | **TRUE** |

---

## 6. DEVIATIONS AND BLOCKERS
None

---

## 7. DEFERRED
- The embedder decision (Gautam, after human review of the top-1 snippets)
- P10 frontend demo integration
- Pharmacist / clinician review of safety copy
