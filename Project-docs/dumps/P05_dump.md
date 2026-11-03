# P05 Execution Dump: Medicine Catalog Data Layer

## 1. HEADER
- **Prompt ID:** PROMPT 05
- **Date & Time:** 2026-11-02 19:22:30 IST
- **Python Version:** Python 3.11.9 (backend\venv\Scripts\python.exe)
- **Git Commit:** 0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths

---

## 2. INPUT
- **CSV Path:** `backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv`
- **INPUT_SHA256:** `4AC1C0E8967E16DE86AAD74B0810FC06342D5F81BBE3E27BB7C6E5D46E02C4D3`
- **Row Count:** 2,445 data rows (2,446 lines including CSV header)

---

## 3. PRE-FLIGHT
### Step 0a: Python Processes
```powershell
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object { ... }
```
Output:
```
NO_PYTHON_PROCESSES_RUNNING
```

### Step 0b: Test-Path Result
```powershell
Test-Path backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv
```
Output:
```
True
```

### Step 0c: INPUT_SHA256
```powershell
Get-FileHash -Algorithm SHA256 backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv
```
Output:
```
Algorithm       Hash                                                               Path
---------       ----                                                               ----
SHA256          4AC1C0E8967E16DE86AAD74B0810FC06342D5F81BBE3E27BB7C6E5D46E02C4D3   C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv
```

---

## 4. BASELINE
### Step 1a: Baseline Pytest Suite (53 Passed)
```powershell
cd backend ; .\venv\Scripts\python.exe -m pytest -q > pytest_out.txt 2>&1 ; Get-Content pytest_out.txt -Tail 5
```
Output:
```
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
53 passed, 2 warnings in 41.21s
```

### Step 1b: Route & OpenAPI Verification (Baseline)
```powershell
@'
import json, hashlib, sys
sys.path.insert(0, "src")
from agents.main import app
spec_obj = app.openapi()
spec = json.dumps(spec_obj, sort_keys=True, indent=2)
ops = sum(1 for p, ops in spec_obj["paths"].items() for m in ops if m in {"get", "post", "put", "delete", "patch"})
print("OPERATIONS:", ops)
print("OPENAPI_SHA256_INMEMORY_LF:", hashlib.sha256(spec.encode("utf-8")).hexdigest())
'@ | .\venv\Scripts\python.exe -
```
Output:
```
OPERATIONS: 43
OPENAPI_SHA256_INMEMORY_LF: 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1
```

### Step 1c: Git Status & Latest Commit
```powershell
git status --short ; git log -1 --oneline
```
Output:
```
 M backend/src/agents/Calling.py
 M backend/src/agents/Calling_Ai.py
 M backend/src/agents/buying_agent.py
 M backend/src/agents/db_connect.py
 M backend/src/agents/jwt_utils.py
 M backend/src/agents/main.py
?? backend/.env.example
?? backend/data/
?? backend/health_out.txt
?? backend/pytest_auth.txt
?? backend/pytest_health.txt
?? backend/pytest_out.txt
?? backend/pytest_p0.txt
?? backend/scripts/
?? backend/src/agents/catalog.py
?? backend/src/agents/errors.py
?? backend/src/agents/file_utils.py
?? backend/src/agents/hospital_parser.py
?? backend/src/agents/llm_output.py
?? backend/src/agents/rate_limit.py
?? backend/src/agents/routes/
?? backend/src/agents/schemas.py
?? backend/tests/test_phase0.py
?? backend/tests/test_routes_auth.py
?? local-changes.patch
0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths
```

---

## 5. IMPORT
### Step 6a: Run Importer
```powershell
.\venv\Scripts\python.exe scripts\import_janaushadhi.py > import_out.txt 2>&1 ; Get-Content import_out.txt -Tail 10
```
Output:
```
Import completed successfully.
Total rows: 2445
Unique drug codes: 2445
Zero MRP rows: 345
Parse failed rows: 343
Pack count present rows: 1730
Non-medicine rows: 350
Output SHA256: b4c2d5946c638b81629c3b5f2c46358e79da6389fb30515f14534fef11ab7622
```

### Step 6b: Importer Determinism (Identical Output SHA256)
```powershell
Get-FileHash backend\data\catalog\janaushadhi.json ; run the importer again ; Get-FileHash again
```
Output:
```
Algorithm       Hash                                                               Path
---------       ----                                                               ----
SHA256          B4C2D5946C638B81629C3B5F2C46358E79DA6389FB30515F14534FEF11AB7622   C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\catalog\janaushadhi.json
SHA256          B4C2D5946C638B81629C3B5F2C46358E79DA6389FB30515F14534FEF11AB7622   C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\catalog\janaushadhi.json
```
Both hashes match byte-for-byte.

### Step 6c: Verbatim import_report.json
```json
{
  "input_sha256": "4ac1c0e8967e16de86aad74b0810fc06342d5f81bbe3e27bb7c6e5d46e02c4d3",
  "output_sha256": "b4c2d5946c638b81629c3b5f2c46358e79da6389fb30515f14534fef11ab7622",
  "total_rows": 2445,
  "unique_drug_codes": 2445,
  "zero_mrp_rows": 345,
  "parse_failed_rows": 343,
  "pack_count_present_rows": 1730,
  "non_medicine_rows": 350,
  "group_case_variants": [
    {
      "canonical": "Anti-Fungal",
      "variants": [
        "Anti-Fungal",
        "Anti-fungal"
      ]
    },
    {
      "canonical": "Anti-Retroviral",
      "variants": [
        "Anti-Retroviral",
        "Anti-retroviral"
      ]
    },
    {
      "canonical": "Anti-Viral",
      "variants": [
        "Anti-Viral",
        "Anti-viral"
      ]
    },
    {
      "canonical": "Hemorrhoids & Anal Fissures",
      "variants": [
        "Hemorrhoids & Anal Fissures",
        "Hemorrhoids & Anal fissures"
      ]
    },
    {
      "canonical": "Hepato-Protective",
      "variants": [
        "Hepato-Protective",
        "Hepato-protective"
      ]
    },
    {
      "canonical": "Stomatologicals",
      "variants": [
        "STOMATOLOGICALS",
        "Stomatologicals"
      ]
    }
  ],
  "duplicate_name_unit_pairs": [
    {
      "name_clean": "l-ornithine l-aspartate 150mg and pancreatin 100mg tablets",
      "unit_size_raw": "10's",
      "drug_codes": [
        "1738",
        "2040"
      ]
    }
  ]
}
```

---

## 6. CHANGED FILES

### `backend\scripts\import_janaushadhi.py`
```python
import csv
import json
import hashlib
from collections import defaultdict, Counter
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from agents import catalog


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_import():
    csv_path = BASE_DIR / "data" / "janaushadhi" / "PMBJP_Product_List_2026-11-02.csv"
    non_med_path = BASE_DIR / "data" / "catalog" / "non_medicine_groups.json"
    output_json = BASE_DIR / "data" / "catalog" / "janaushadhi.json"
    report_json = BASE_DIR / "data" / "catalog" / "import_report.json"

    input_sha256 = compute_sha256(csv_path)

    with open(non_med_path, "r", encoding="utf-8") as f:
        non_medicine_groups = set(json.load(f))

    raw_rows = []
    groups_by_lower = defaultdict(Counter)

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_rows.append(row)
            grp = row["Group Name"].strip()
            groups_by_lower[grp.lower()][grp] += 1

    canonical_group_map = {}
    group_case_variants = []
    for low, counter in sorted(groups_by_lower.items()):
        most_common = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
        canonical = most_common[0][0]
        canonical_group_map[low] = canonical
        if len(counter) > 1:
            group_case_variants.append({
                "canonical": canonical,
                "variants": sorted(list(counter.keys()))
            })

    items = []
    for row in raw_rows:
        drug_code = row["Drug Code"].strip()
        sr_no = int(row["Sr No"].strip())
        name_raw = row["Generic Name"].strip()
        name_clean = catalog.normalize_text(name_raw)
        components = catalog.parse_components(name_raw)
        parse_ok = len(components) > 0 and all(c.get("parse_ok", False) for c in components)
        unit_size_raw = row["Unit Size"].strip()
        dosage_form = catalog.dosage_form(name_raw, unit_size_raw)
        pack_count = catalog.pack_count(unit_size_raw)

        mrp_str = row["MRP"].strip()
        try:
            mrp_val = float(mrp_str)
        except ValueError:
            mrp_val = 0.0

        if mrp_val > 0.0:
            mrp = mrp_val
            price_status = "listed"
        else:
            mrp = None
            price_status = "not_notified"

        price_per_unit = catalog.per_unit_price(mrp, pack_count)
        group_canonical = canonical_group_map[row["Group Name"].strip().lower()]
        is_medicine = group_canonical not in non_medicine_groups

        item = {
            "drug_code": drug_code,
            "sr_no": sr_no,
            "name_raw": name_raw,
            "name_clean": name_clean,
            "components": components,
            "parse_ok": parse_ok,
            "dosage_form": dosage_form,
            "unit_size_raw": unit_size_raw,
            "pack_count": pack_count,
            "mrp": mrp,
            "price_status": price_status,
            "price_per_unit": price_per_unit,
            "group_canonical": group_canonical,
            "is_medicine": is_medicine,
            "source": "PMBJP Product List",
            "source_date": "2026-11-02",
        }
        items.append(item)

    items.sort(key=lambda x: x["sr_no"])

    drug_codes = [item["drug_code"] for item in items]
    if len(set(drug_codes)) != len(items):
        raise ValueError(
            f"Duplicate drug codes found! Unique: {len(set(drug_codes))}, Total: {len(items)}"
        )

    pairs = defaultdict(list)
    for item in items:
        pairs[(item["name_clean"], item["unit_size_raw"])].append(item["drug_code"])

    duplicate_name_unit_pairs = []
    for (name_clean, unit_raw), codes in sorted(pairs.items()):
        if len(codes) > 1:
            duplicate_name_unit_pairs.append({
                "name_clean": name_clean,
                "unit_size_raw": unit_raw,
                "drug_codes": codes,
            })

    total_rows = len(items)
    unique_drug_codes = len(set(drug_codes))
    zero_mrp_rows = sum(1 for x in items if x["price_status"] == "not_notified")
    parse_failed_rows = sum(1 for x in items if not x["parse_ok"])
    pack_count_present_rows = sum(1 for x in items if x["pack_count"] is not None)
    non_medicine_rows = sum(1 for x in items if not x["is_medicine"])

    output_dir = output_json.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    json_bytes = (json.dumps(items, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    with open(output_json, "wb") as f:
        f.write(json_bytes)

    output_sha256 = hashlib.sha256(json_bytes).hexdigest()

    report = {
        "input_sha256": input_sha256,
        "output_sha256": output_sha256,
        "total_rows": total_rows,
        "unique_drug_codes": unique_drug_codes,
        "zero_mrp_rows": zero_mrp_rows,
        "parse_failed_rows": parse_failed_rows,
        "pack_count_present_rows": pack_count_present_rows,
        "non_medicine_rows": non_medicine_rows,
        "group_case_variants": group_case_variants,
        "duplicate_name_unit_pairs": duplicate_name_unit_pairs,
    }

    report_bytes = (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    with open(report_json, "wb") as f:
        f.write(report_bytes)

    print(f"Import completed successfully.")
    print(f"Total rows: {total_rows}")
    print(f"Unique drug codes: {unique_drug_codes}")
    print(f"Zero MRP rows: {zero_mrp_rows}")
    print(f"Parse failed rows: {parse_failed_rows}")
    print(f"Pack count present rows: {pack_count_present_rows}")
    print(f"Non-medicine rows: {non_medicine_rows}")
    print(f"Output SHA256: {output_sha256}")


if __name__ == "__main__":
    run_import()
```

### `backend\src\agents\catalog.py`
```python
import os
import re
import json
import functools
from typing import Optional, List, Dict, Any

_SYNONYMS_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "catalog", "synonyms.json")
)
_JANAUSHADHI_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "catalog", "janaushadhi.json")
)

_WORDS_TO_REMOVE = [
    "gastro-resistant", "gastro resistant", "enteric coated",
    "gastro", "resistant", "enteric", "coated",
    "tablets", "tablet", "tab", "ip", "capsules", "capsule",
    "injection", "syrup", "suspension", "gel", "cream",
    "sr", "er", "prolonged", "sustained", "release",
    "delayed", "modified", "extended", "dispersible", "oral", "granules",
]
_REMOVE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in sorted(_WORDS_TO_REMOVE, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
_NUM_UNIT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|g|iu|%|ml)", re.IGNORECASE)
_SPLIT_PATTERN = re.compile(r"\s+and\s+|,|&|\+", re.IGNORECASE)
_PACK_RE = re.compile(r"^\s*(\d+)\s*(?:['’‘\ufffd]\s*s\b|s\b|['’‘\ufffd]\b)", re.IGNORECASE)

_DOSAGE_FORMS = [
    ("Injection", re.compile(r"injection|inection|infusion", re.IGNORECASE)),
    ("Liquid", re.compile(r"syrup|suspension|oral solution|solution", re.IGNORECASE)),
    ("Drops", re.compile(r"drops|ophthalmic|eye drop|ear drop", re.IGNORECASE)),
    ("Gel", re.compile(r"\bgel\b", re.IGNORECASE)),
    ("Topical", re.compile(r"cream|ointment|lotion|spray|patch", re.IGNORECASE)),
    ("Capsule", re.compile(r"capsule", re.IGNORECASE)),
    ("Tablet", re.compile(r"tablet|tabelts|\btab\b", re.IGNORECASE)),
    ("Powder", re.compile(r"powder|sachet|granule", re.IGNORECASE)),
]


@functools.lru_cache(maxsize=1)
def _load_synonyms() -> Dict[str, str]:
    if os.path.exists(_SYNONYMS_FILE):
        with open(_SYNONYMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"\s*\(\s*-\s*\)\s*", "(-)", s)
    s = s.replace("tabelts", "tablets")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def canonical_salt(name: str) -> str:
    norm = normalize_text(name)
    synonyms = _load_synonyms()
    return synonyms.get(norm, norm)


def parse_components(generic_name: str) -> List[Dict[str, Any]]:
    norm_name = normalize_text(generic_name)
    parts = _SPLIT_PATTERN.split(norm_name)
    components = []
    has_strength = False

    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = _NUM_UNIT_PATTERN.search(part)
        if m:
            strength = float(m.group(1))
            unit = m.group(2).lower()
            salt_raw = part[:m.start()]
            has_strength = True
        else:
            strength = None
            unit = None
            salt_raw = part

        salt_clean = _REMOVE_PATTERN.sub(" ", salt_raw)
        salt_clean = re.sub(r"\s+\([^)]*\)\s*$", "", salt_clean)
        salt_clean = normalize_text(salt_clean)
        if salt_clean:
            salt = canonical_salt(salt_clean)
            components.append({
                "salt": salt,
                "strength": strength,
                "unit": unit,
                "parse_ok": True,
            })

    if not components or not any(c.get("salt") for c in components):
        return [{
            "salt": canonical_salt(generic_name),
            "strength": None,
            "unit": None,
            "parse_ok": False,
        }]

    # If none of the components had a strength, mark parse_ok = False
    if not has_strength:
        for c in components:
            c["parse_ok"] = False

    return components


def dosage_form(generic_name: str, unit_size: str = "") -> str:
    generic_name = generic_name or ""
    unit_size = unit_size or ""
    for name, pattern in _DOSAGE_FORMS:
        if pattern.search(generic_name):
            return name
    for name, pattern in _DOSAGE_FORMS:
        if pattern.search(unit_size):
            return name
    return "Other"


def pack_count(unit_size: str) -> Optional[int]:
    if not unit_size:
        return None
    m = _PACK_RE.search(unit_size)
    if m:
        return int(m.group(1))
    return None


def per_unit_price(mrp: Optional[float], pack: Optional[int]) -> Optional[float]:
    if mrp is None or pack is None or mrp == 0:
        return None
    return round(mrp / pack, 2)


@functools.lru_cache(maxsize=1)
def load_catalog(path: Optional[str] = None) -> List[Dict[str, Any]]:
    catalog_path = path or _JANAUSHADHI_FILE
    with open(catalog_path, "r", encoding="utf-8") as f:
        return json.load(f)


def search(query: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    q = canonical_salt(query)
    matches = []
    for item in items:
        component_match = any(c.get("salt") == q for c in item.get("components", []))
        name_match = q in item.get("name_clean", "")
        if component_match or name_match:
            matches.append(item)

    matches.sort(
        key=lambda x: (
            x.get("price_per_unit") is None,
            x.get("price_per_unit") if x.get("price_per_unit") is not None else 0.0,
            x.get("drug_code", ""),
        )
    )
    return matches
```

### `backend\tests\test_catalog.py`
```python
import json
import hashlib
from pathlib import Path
import socket
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agents import catalog


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Ensure catalog code makes zero network calls."""
    def _guarded(*args, **kwargs):
        raise RuntimeError("Network calls are forbidden during catalog tests")
    monkeypatch.setattr(socket, "socket", _guarded)


def test_row_count_and_unique_codes():
    items = catalog.load_catalog()
    assert len(items) == 2445
    codes = [item["drug_code"] for item in items]
    assert len(set(codes)) == 2445


def test_zero_mrp_rows_are_null():
    items = catalog.load_catalog()
    not_notified = [item for item in items if item["price_status"] == "not_notified"]
    assert len(not_notified) == 345
    for item in not_notified:
        assert item["mrp"] is None
        assert item["price_per_unit"] is None


def test_paracetamol_650_per_unit():
    items = catalog.load_catalog()
    sr398 = next((item for item in items if item["sr_no"] == 398), None)
    assert sr398 is not None
    assert sr398["mrp"] == 15.47
    assert sr398["pack_count"] == 15
    assert sr398["price_per_unit"] == 1.03
    assert sr398["dosage_form"] == "Tablet"


def test_levothyroxine_synonym_search():
    items = catalog.load_catalog()
    results = catalog.search("levothyroxine", items)
    assert len(results) >= 8
    for item in results:
        assert item["price_status"] == "listed" or item["price_per_unit"] is None


def test_duplicate_name_different_codes():
    items = catalog.load_catalog()
    sr1042 = next((item for item in items if item["sr_no"] == 1042), None)
    sr1295 = next((item for item in items if item["sr_no"] == 1295), None)
    assert sr1042 is not None
    assert sr1295 is not None
    assert sr1042["drug_code"] != sr1295["drug_code"]
    assert sr1042["mrp"] != sr1295["mrp"]


def test_group_canonicalization():
    items = catalog.load_catalog()
    report_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "import_report.json"
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    expected_canonical = next(
        g["canonical"] for g in report["group_case_variants"] if g["canonical"].lower() == "anti-fungal"
    )

    anti_fungals = [item["group_canonical"] for item in items if item["group_canonical"].lower() == "anti-fungal"]
    assert len(anti_fungals) > 0
    distinct_spellings = set(anti_fungals)
    assert len(distinct_spellings) == 1
    assert distinct_spellings == {expected_canonical}


@pytest.mark.parametrize(
    "raw_name, expected",
    [
        ("Paracetamol Tablets IP 650 mg", [("paracetamol", 650.0, "mg")]),
        ("Amoxycillin 500mg and Potassium Clavulanate 125mg Tablets IP", [("amoxicillin", 500.0, "mg"), ("clavulanic acid", 125.0, "mg")]),
        ("Thyroxine Sodium Tablets IP 100 mcg", [("levothyroxine", 100.0, "mcg")]),
        ("Metformin Hydrochloride Sustained Release Tablets IP 1000 mg", [("metformin", 1000.0, "mg")]),
        ("Atorvastatin 10mg and Clopidogrel 75mg Capsules", [("atorvastatin", 10.0, "mg"), ("clopidogrel", 75.0, "mg")]),
        ("Glimepiride Tablets  IP 3mg", [("glimepiride", 3.0, "mg")]),
        ("Losartan Potassium 50mg and Hydrochlorothiazide 12.5mg Tabelts IP", [("losartan potassium", 50.0, "mg"), ("hydrochlorothiazide", 12.5, "mg")]),
        ("S(-)Amlodipine Tablets IP 2.5 mg", [("levamlodipine", 2.5, "mg")]),
    ]
)
def test_parse_components_cases(raw_name, expected):
    comps = catalog.parse_components(raw_name)
    actual = [(c["salt"], c["strength"], c["unit"]) for c in comps]
    assert actual == expected


@pytest.mark.parametrize(
    "unit_size, expected",
    [
        ("10's", 10),
        ("4'S", 4),
        ("1’s Sachet", 1),
        ("100's in Bottle", 100),
        ("100 ml", None),
        ("Vial & Wfi", None),
        ("30g", None),
    ]
)
def test_pack_count_cases(unit_size, expected):
    assert catalog.pack_count(unit_size) == expected


@pytest.mark.parametrize(
    "raw_name, expected",
    [
        ("Ondansetron Injection IP 2mg per ml", "Injection"),
        ("Pantoprazole Gastro Resistant Tablets IP 40 mg", "Tablet"),
        ("Pilocarpine Eye Drops IP 2% W/V", "Drops"),
    ]
)
def test_dosage_form_cases(raw_name, expected):
    assert catalog.dosage_form(raw_name) == expected


def test_per_unit_price_rules():
    assert catalog.per_unit_price(0, 10) is None
    assert catalog.per_unit_price(15.47, None) is None
    assert catalog.per_unit_price(15.47, 15) == 1.03


def test_importer_deterministic():
    report_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "import_report.json"
    catalog_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "janaushadhi.json"

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    h = hashlib.sha256()
    with open(catalog_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    current_hash = h.hexdigest()

    assert report["output_sha256"] == current_hash
```

### `backend\data\catalog\synonyms.json`
```json
{
  "thyroxine sodium": "levothyroxine",
  "levo-thyroxine sodium": "levothyroxine",
  "levothyroxine sodium": "levothyroxine",
  "amoxycillin": "amoxicillin",
  "potassium clavulanate": "clavulanic acid",
  "clavulanate potassium": "clavulanic acid",
  "acetaminophen": "paracetamol",
  "metformin hydrochloride": "metformin",
  "atorvastatin calcium": "atorvastatin",
  "amlodipine besylate": "amlodipine",
  "s(-)amlodipine": "levamlodipine",
  "s-amlodipine": "levamlodipine"
}
```
*Note:* `s(-)amlodipine` is intentionally mapped to `levamlodipine` and kept strictly distinct from `amlodipine`.

### `backend\data\catalog\non_medicine_groups.json`
```json
["Surgical & Medical Consumables", "Nutraceuticals"]
```

### `backend\data\catalog\janaushadhi.json`
- **SHA256:** `b4c2d5946c638b81629c3b5f2c46358e79da6389fb30515f14534fef11ab7622`
- **Size:** 1,777,809 bytes (~1.78 MB)
- *(Full contents omitted per prompt instruction: 2,445 objects).*

### `backend\data\catalog\import_report.json`
*(Included in full above under Section 5)*

### `Project-docs\decisions.md` (Appended D43)
```markdown
## D43 — Medicine Catalog Data Layer: Jan Aushadhi Normalization & Search Architecture (2 Nov 2026)

**Status:** Built and verified (Prompt 05, 2 Nov 2026). All 79 automated tests passing (53 existing + 26 catalog tests). Zero route changes. OpenAPI SHA256 invariant preserved (`37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`).

**Decisions:**
1. **Catalog Data Source:**
   - Source is the official PMBJP (Pradhan Mantri Bhartiya Janaushadhi Pariyojana) product list dated 2 Nov 2026 (`backend/data/janaushadhi/PMBJP_Product_List_2026-11-02.csv`), containing 2,445 items.
   - The government NPPA ceiling price source is currently unreachable, making the PMBJP product list the sole authoritative government catalog source for Phase 1.
2. **Keying by Drug Code:**
   - Items are keyed uniquely by `drug_code` (str). While generic names and unit sizes repeat (e.g. `L-Ornithine L-Aspartate 150mg and Pancreatin 100mg Tablets`, `10's` appears under both drug code `1738` at ₹18.75 and drug code `2040` at ₹30.94), `drug_code` is 100% unique across all 2,445 rows.
3. **Price Status & Zero MRP Policy:**
   - In PMBJP data, an MRP of `0.0` or empty signifies an unnotified price (`price_status: "not_notified"`), not free medicine. Exactly 345 rows have MRP 0.
   - For all `not_notified` rows, `mrp` and `price_per_unit` are normalized strictly to `None` / `null`. They are never presented as ₹0.00 to users.
4. **Brand MRP & Savings Calculation Deferral:**
   - The PMBJP dataset contains only Jan Aushadhi generic MRPs, not branded drug MRPs. Brand ceiling prices / branded market prices and savings percentage calculations are deferred to P07 (seed brand MRP data layer / replacement of live scraping).
5. **Non-Medicine Group Heuristic (`is_medicine`):**
   - Products belonging to `Surgical & Medical Consumables` (314 rows) and `Nutraceuticals` (36 rows) are classified as `is_medicine: false` (350 total rows).
   - All vitamins, supplements, and other groups remain `is_medicine: true`.
   - This list is a heuristic documented in `non_medicine_groups.json` and subject to clinical review by Gautam.
6. **Salt Canonicalization & Synonym Rules:**
   - Generic names are normalized via `normalize_text` and matched against `synonyms.json`.
   - `S(-)Amlodipine` (`s(-)amlodipine` / `s-amlodipine`) is intentionally normalized to `levamlodipine` and kept strictly distinct from racemic `amlodipine`, as chirally pure S-amlodipine possesses distinct dosing and tolerability profiles.
   - Other mapped pairs include `thyroxine sodium` -> `levothyroxine`, `amoxycillin` -> `amoxicillin`, `potassium clavulanate` -> `clavulanic acid`, `acetaminophen` -> `paracetamol`, `metformin hydrochloride` -> `metformin`, and `atorvastatin calcium` -> `atorvastatin`.
7. **Offline Hermetic Execution:**
   - Catalog ingestion (`import_janaushadhi.py`) and search module (`catalog.py`) are pure in-memory functions with zero network calls and no I/O at import time. Automated tests enforce network isolation by monkeypatching `socket.socket` to raise.
```

### `Project-docs\progress.md` (Appended P05)
```markdown
## Prompt 05 — Medicine Catalog Data Layer (2 Nov 2026)

Prompt 05 status: CLOSED.

### Completed Work
- [x] **Catalog Normalization & Ingestion (`import_janaushadhi.py`):**
  - Ingested PMBJP product list dated 2 Nov 2026 (`backend/data/janaushadhi/PMBJP_Product_List_2026-11-02.csv`), containing 2,445 rows. Input SHA256: `4ac1c0e8967e16de86aad74b0810fc06342d5f81bbe3e27bb7c6e5d46e02c4d3`.
  - Normalized data written to `backend/data/catalog/janaushadhi.json` with byte-for-byte deterministic reproducibility (verified identical SHA256 across consecutive runs: `b4c2d5946c638b81629c3b5f2c46358e79da6389fb30515f14534fef11ab7622`).
  - Audit report generated at `backend/data/catalog/import_report.json`:
    - Total rows: 2,445
    - Unique drug codes: 2,445
    - Zero MRP rows: 345 (marked `price_status: "not_notified"`, mrp and price_per_unit normalized to null)
    - Parse failed rows: 343 (non-strength consumables/items)
    - Pack count present rows: 1,730
    - Non-medicine rows: 350 (314 Surgical & Medical Consumables + 36 Nutraceuticals)
    - Group case variants: 6 canonicalized groups (`Anti-Fungal`, `Anti-Retroviral`, `Anti-Viral`, `Hemorrhoids & Anal Fissures`, `Hepato-Protective`, `Stomatologicals`)
    - Duplicate name+unit pairs: 1 pair (`L-Ornithine L-Aspartate 150mg and Pancreatin 100mg Tablets`, `10's`) with distinct drug codes `["1738", "2040"]`
- [x] **Catalog Search & Utility Module (`agents/catalog.py`):**
  - Pure in-memory module with zero network dependencies and no import-time I/O.
  - Implements `normalize_text`, `canonical_salt`, `parse_components`, `dosage_form`, `pack_count`, `per_unit_price`, `load_catalog`, and `search`.
  - `synonyms.json` maps common generic aliases (including keeping `s(-)amlodipine` separate as `levamlodipine`).
- [x] **Offline Test Suite (`tests/test_catalog.py`):**
  - Implemented 11 required test suites with autouse network blocking fixture (`socket.socket` raising RuntimeError).
  - 26 tests passed in 0.07s.
- [x] **Parity & Invariants Preserved:**
  - Route count: 43 (0 new routes added).
  - In-memory LF OpenAPI SHA256: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1` (verified exact match).
  - Full test suite: **79 passed, 0 failed** (53 previous + 26 catalog tests).
  - Subprocess import verification with `APP_ENV=development` returned `IMPORT_OK`.
  - Zero network library imports in `catalog.py`.
- [x] **Documentation Updates:**
  - Appended decision D43 to `decisions.md`.

### Open Items & Deferred Items
- Brand MRP seed dataset and savings calculation (deferred to P07).
- `/catalog/search` HTTP route (deferred to P07).
- Removal of live scraping (`buying_agent.py`) and `browser_use` dependency (deferred to P07).
- Frontend Compare page adjustments to use static catalog (deferred to frontend phase).
- `is_medicine` non-medicine groups review (Gautam).
- Silymarin single-salt and Cetirizine 5 mg coverage notes.
```

---

## 7. VERIFICATION
### Step 7: Catalog Test Suite
```powershell
.\venv\Scripts\python.exe -m pytest -q tests\test_catalog.py > pytest_catalog.txt 2>&1 ; Get-Content pytest_catalog.txt -Tail 5
```
Output:
```
..........................                                               [100%]
26 passed in 0.07s
```

### Step 8a: Full Test Suite
```powershell
.\venv\Scripts\python.exe -m pytest -q > pytest_all.txt 2>&1 ; Get-Content pytest_all.txt -Tail 5
```
Output:
```
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
79 passed, 2 warnings in 29.10s
```

### Step 8b: Subprocess Import Check
```powershell
$env:APP_ENV="development"; .\venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); import agents.main; print('IMPORT_OK')"
```
Output:
```
IMPORT_OK
```

### Step 8c: Route & OpenAPI Verification (Post-Step 8)
```powershell
@'
import json, hashlib, sys
sys.path.insert(0, "src")
from agents.main import app
spec_obj = app.openapi()
spec = json.dumps(spec_obj, sort_keys=True, indent=2)
ops = sum(1 for p, ops in spec_obj["paths"].items() for m in ops if m in {"get", "post", "put", "delete", "patch"})
print("OPERATIONS:", ops)
print("OPENAPI_SHA256_INMEMORY_LF:", hashlib.sha256(spec.encode("utf-8")).hexdigest())
'@ | .\venv\Scripts\python.exe -
```
Output:
```
OPERATIONS: 43
OPENAPI_SHA256_INMEMORY_LF: 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1
```

### Step 8d: Forbidden Network Import Check in `catalog.py`
```powershell
Select-String -Path src\agents\catalog.py -Pattern "requests|urllib|httpx|socket"
```
Output:
```
(No matches found)
```

---

## 8. CHECKLIST
- [x] Step 0: Pre-flight verified (no python processes running; input CSV verified; INPUT_SHA256 recorded: `4AC1C0E8967E16DE86AAD74B0810FC06342D5F81BBE3E27BB7C6E5D46E02C4D3`)
- [x] Step 1: Baseline established (53 passed; 43 operations; canonical OpenAPI hash: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`; git status recorded)
- [x] Step 2: `synonyms.json` created verbatim (S(-)Amlodipine mapped to `levamlodipine` and kept separate)
- [x] Step 3: `non_medicine_groups.json` created verbatim (`["Surgical & Medical Consumables", "Nutraceuticals"]`)
- [x] Step 4: `agents/catalog.py` implemented with pure functions and no I/O at import
- [x] Step 5: `scripts/import_janaushadhi.py` created with deterministic normalization logic
- [x] Step 6: Importer run and determinism confirmed (consecutive runs produced identical SHA256: `b4c2d5946c638b81629c3b5f2c46358e79da6389fb30515f14534fef11ab7622`)
- [x] Step 7: `tests/test_catalog.py` created and passed (26 passed in 0.07s)
- [x] Step 8: Invariants verified (79 passed; IMPORT_OK; 43 operations; canonical OpenAPI hash unchanged; zero network imports in `catalog.py`)
- [x] Step 9: Documentation updated (appended decision D43 and progress entry P05)
- [x] Step 10: Dump created (`Project-docs\dumps\P05_dump.md`)

---

## 9. DEVIATIONS AND BLOCKERS
None.

---

## 10. DEFERRED
- Brand MRP seed dataset and savings calculation (deferred to P07).
- `/catalog/search` HTTP route (deferred to P07).
- Removal of live scraping (`buying_agent.py`) and `browser_use` dependency (deferred to P07).
- Frontend Compare page adjustments to use static catalog (deferred to frontend phase).
- `is_medicine` non-medicine groups review (Gautam).
- Silymarin single-salt and Cetirizine 5 mg coverage notes.

