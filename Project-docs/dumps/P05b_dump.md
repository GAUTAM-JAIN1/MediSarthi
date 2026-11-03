# P05b Execution Dump: Parser Fix, Search Exact-First, No-Strength Rename, Record Corrections

## 1. HEADER
- **Prompt ID:** PROMPT 05b
- **Date & Time:** 2026-11-02 19:47:45 IST
- **Python Version:** Python 3.11.9 (backend\venv\Scripts\python.exe)
- **Git Commit:** 0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths

---

## 2. PRE-FLIGHT
### Step 0a: Python Processes
```powershell
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, CPU
```
Output:
```
(Command exited with code 1, no running python processes found)
```

### Step 0b: Test-Path & Input Hash Check
```powershell
Test-Path backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv; Get-FileHash -Algorithm SHA256 backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv
```
Output:
```
True

Algorithm       Hash                                                               Path
---------       ----                                                               ----
SHA256          4AC1C0E8967E16DE86AAD74B0810FC06342D5F81BBE3E27BB7C6E5D46E02C4D3   C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv
```

---

## 3. BASELINE
### Step 0c: Baseline Pytest Suite (79 Passed)
```powershell
cd backend ; .\venv\Scripts\python.exe -m pytest -q > pytest_out.txt 2>&1 ; Get-Content pytest_out.txt -Tail 5
```
Output:
```
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
79 passed, 2 warnings in 25.34s
```

### Step 0d: Route & OpenAPI Verification (Baseline)
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

---

## 4. IMPORT
### Importer Hashes (Determinism Check)
```powershell
Get-FileHash data\catalog\janaushadhi.json -Algorithm SHA256; .\venv\Scripts\python.exe scripts\import_janaushadhi.py > $null; Get-FileHash data\catalog\janaushadhi.json -Algorithm SHA256
```
Output:
```
Algorithm       Hash                                                               Path
---------       ----                                                               ----
SHA256          E5D0B82758B702959789F67691B03BAA438C9A2BA9713237B8CF6FF14BB68D7C   C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\catalog\janaushadhi.json
SHA256          E5D0B82758B702959789F67691B03BAA438C9A2BA9713237B8CF6FF14BB68D7C   C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\catalog\janaushadhi.json
```
Both hashes match byte-for-byte (`e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`).

### Full import_report.json Verbatim
```json
{
  "input_sha256": "4ac1c0e8967e16de86aad74b0810fc06342d5f81bbe3e27bb7c6e5d46e02c4d3",
  "output_sha256": "e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c",
  "total_rows": 2445,
  "unique_drug_codes": 2445,
  "zero_mrp_rows": 345,
  "no_strength_rows": 382,
  "slash_strength_rows": 41,
  "slash_mismatch_rows": 0,
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

## 5. CHANGED FILES

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

SLASH_STRENGTH_PATTERN = re.compile(
    r"\(\s*(\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)+)\s*(mg|mcg|g|iu|%|ml)\s*\)",
    re.IGNORECASE,
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
    m = SLASH_STRENGTH_PATTERN.search(norm_name)
    if m:
        nums = [float(x) for x in re.split(r"\s*/\s*", m.group(1))]
        unit = m.group(2).lower()
        norm_name = norm_name[:m.start()] + " " + norm_name[m.end():]
        norm_name = re.sub(r"\s+", " ", norm_name).strip()
    else:
        nums = None
        unit = None

    parts = _SPLIT_PATTERN.split(norm_name)
    raw_salts = []

    for part in parts:
        part = part.strip()
        if not part:
            continue
        pm = _NUM_UNIT_PATTERN.search(part)
        if pm:
            salt_raw = part[:pm.start()]
        else:
            salt_raw = part

        salt_clean = _REMOVE_PATTERN.sub(" ", salt_raw)
        salt_clean = re.sub(r"\s+\([^)]*\)\s*$", "", salt_clean)
        salt_clean = re.sub(r"\s*\([^\)]*$", "", salt_clean)
        salt_clean = normalize_text(salt_clean)
        if salt_clean:
            salt = canonical_salt(salt_clean)
            raw_salts.append((salt, pm))

    if not raw_salts:
        return [{
            "salt": canonical_salt(generic_name),
            "strength": None,
            "unit": None,
            "parse_ok": False,
        }]

    components = []
    if nums is not None:
        if len(raw_salts) == len(nums):
            for i, (salt, _) in enumerate(raw_salts):
                components.append({
                    "salt": salt,
                    "strength": nums[i],
                    "unit": unit,
                    "parse_ok": True,
                })
        else:
            for salt, _ in raw_salts:
                components.append({
                    "salt": salt,
                    "strength": None,
                    "unit": None,
                    "parse_ok": False,
                })
    else:
        for salt, pm in raw_salts:
            if pm:
                s_val = float(pm.group(1))
                u_val = pm.group(2).lower()
                ok = True
            else:
                s_val = None
                u_val = None
                ok = False
            components.append({
                "salt": salt,
                "strength": s_val,
                "unit": u_val,
                "parse_ok": ok,
            })

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
    """
    Search catalog items for query.
    Return exact component-salt matches first.
    Fall back to name_clean substring matches only when there are no exact matches.
    Results are sorted by per_unit_price ascending (None last), then by drug_code.
    """
    q = canonical_salt(query)
    exact_matches = [
        item for item in items
        if any(c.get("salt") == q for c in item.get("components", []))
    ]
    if exact_matches:
        matches = exact_matches
    else:
        matches = [item for item in items if q in item.get("name_clean", "")]

    matches.sort(
        key=lambda x: (
            x.get("price_per_unit") is None,
            x.get("price_per_unit") if x.get("price_per_unit") is not None else 0.0,
            x.get("drug_code", ""),
        )
    )
    return matches
```

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
    slash_strength_rows = 0
    slash_mismatch_rows = 0

    for row in raw_rows:
        drug_code = row["Drug Code"].strip()
        sr_no = int(row["Sr No"].strip())
        name_raw = row["Generic Name"].strip()
        name_clean = catalog.normalize_text(name_raw)

        m = catalog.SLASH_STRENGTH_PATTERN.search(name_clean)
        if m:
            slash_strength_rows += 1

        components = catalog.parse_components(name_raw)
        row_parse_ok = bool(components) and all(c.get("parse_ok", False) for c in components)

        if m:
            if not row_parse_ok:
                slash_mismatch_rows += 1

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
            "parse_ok": row_parse_ok,
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
    no_strength_rows = sum(1 for x in items if not x["parse_ok"])
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
        "no_strength_rows": no_strength_rows,
        "slash_strength_rows": slash_strength_rows,
        "slash_mismatch_rows": slash_mismatch_rows,
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
    print(f"No strength rows: {no_strength_rows}")
    print(f"Slash strength rows: {slash_strength_rows}")
    print(f"Slash mismatch rows: {slash_mismatch_rows}")
    print(f"Pack count present rows: {pack_count_present_rows}")
    print(f"Non-medicine rows: {non_medicine_rows}")
    print(f"Output SHA256: {output_sha256}")


if __name__ == "__main__":
    run_import()
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
    catalog.load_catalog.cache_clear()
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
        assert any(c.get("salt") == "levothyroxine" for c in item.get("components", []))


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


@pytest.mark.parametrize(
    "raw_name, expected",
    [
        (
            "Atenolol + Chlorthalidone Tablet (25/12.5 Mg)",
            [("atenolol", 25.0, "mg", True), ("chlorthalidone", 12.5, "mg", True)],
        ),
        (
            "Gliclazide + Pioglitazone + Metformin Tablet (30/15/500 Mg)",
            [("gliclazide", 30.0, "mg", True), ("pioglitazone", 15.0, "mg", True), ("metformin", 500.0, "mg", True)],
        ),
        (
            "Amlodipine + Enalapril Tablet (5/5 Mg)",
            [("amlodipine", 5.0, "mg", True), ("enalapril", 5.0, "mg", True)],
        ),
        (
            "Paracetamol Tablets IP 650 mg",
            [("paracetamol", 650.0, "mg", True)],
        ),
    ],
)
def test_parse_components_slash_and_base_cases(raw_name, expected):
    comps = catalog.parse_components(raw_name)
    actual = [(c["salt"], c["strength"], c["unit"], c["parse_ok"]) for c in comps]
    assert actual == expected


def test_parse_components_no_strength_unflavored_base():
    comps = catalog.parse_components("Syrup of Iron and Folic Acid in a flavoured Base")
    assert all(c["parse_ok"] is False for c in comps)


def test_importer_row_2014_slash_strength():
    items = catalog.load_catalog()
    sr2014 = next((item for item in items if item["sr_no"] == 2014), None)
    assert sr2014 is not None
    assert len(sr2014["components"]) == 2
    assert sr2014["components"][0]["strength"] == 25.0
    assert sr2014["components"][1]["strength"] == 12.5
    assert sr2014["components"][0]["parse_ok"] is True
    assert sr2014["components"][1]["parse_ok"] is True
    assert sr2014["parse_ok"] is True


def test_search_exclusion_amlodipine():
    items = catalog.load_catalog()
    results = catalog.search("amlodipine", items)
    assert not any(
        any(c.get("salt") == "levamlodipine" for c in item.get("components", []))
        for item in results
    )


def test_search_fallback_levamlodipine():
    items = catalog.load_catalog()
    results = catalog.search("levamlodipine", items)
    assert len(results) >= 1


def test_report_keys_and_values():
    report_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "import_report.json"
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    assert "no_strength_rows" in report
    assert "slash_strength_rows" in report
    assert "slash_mismatch_rows" in report
    assert "parse_failed_rows" not in report
    assert report["slash_strength_rows"] == 41
    assert report["slash_mismatch_rows"] == 0
```

### `backend\data\catalog\janaushadhi.json`
- **SHA256:** `e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`
- **Size:** 1,775,921 bytes (~1.78 MB)
- *(Full contents omitted per prompt instruction: 2,445 objects).*

### `Project-docs\decisions.md` (Appended D44)
```markdown
## D44 — Catalog Parser Refinements, Exact-First Search, and Record Corrections (2 Nov 2026)

**Status:** Built and verified (Prompt 05b, 2 Nov 2026). All 88 automated tests passing (53 baseline + 35 catalog tests). Route count: 43. OpenAPI canonical in-memory LF SHA256 preserved (`37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`).

**Decisions:**
1. **Corrections to D43:**
   - `parse_failed_rows` is renamed to `no_strength_rows`. It represents rows where `parse_ok` is False (at least one component lacks a parsed numeric strength). It was never only consumables. Of the original count, 295 were non-medicine groups and 48 were medicine groups (vitamins, enzymes, electrolytes, vaccines).
   - The assertion in D43 that S(-)Amlodipine has "distinct dosing and tolerability profiles" is explicitly retracted as unverified in this project. The mapping of `s(-)amlodipine` / `s-amlodipine` to `levamlodipine` (the recommended INN for the S-enantiomer) is retained, keeping it distinct from racemic `amlodipine`. Formal clinical review remains pending (Gautam).
2. **Parser Rules (Slash-Strength & Component Independence):**
   - Implemented `SLASH_STRENGTH_PATTERN` matching bracketed slash combinations such as `(25/12.5 Mg)` or `(30/15/500 Mg)`.
   - When matched, the slash numbers are extracted and paired 1-to-1 with the split salt components if the count matches; if the component count differs from number count, components are assigned None with `parse_ok = False`.
   - Each component's `parse_ok` is determined strictly by its own numeric strength (`strength is not None`). The previous row-level `has_strength` override is completely removed.
   - Row-level `parse_ok` is True if and only if all components in the row have `parse_ok = True`.
3. **Search Policy (Exact Component Match First):**
   - `catalog.search(query, items)` queries exact component-salt equality first (`c["salt"] == canonical_salt(query)`).
   - Only when zero exact salt matches exist across the catalog does the search fall back to substring matching against `name_clean`.
   - Results are sorted by `price_per_unit` ascending (None last), then by `drug_code`.
   - This prevents broader substrings from polluting salt queries (e.g., searching for `amlodipine` does not return pure `levamlodipine` rows).
4. **Known Parser Limitations (Deferred):**
   - Concentration notation (such as `250 mg/5 ml`): currently retains only the first numeric value (`250.0 mg`).
   - Comma splitting: splitting on commas can split composite generic listings (e.g. `Vitamins A,C,D,E`).
```

### `Project-docs\progress.md` (Appended P05b)
```markdown
## Prompt 05b — Parser Fix, Exact-First Search & Metrics Alignment (2 Nov 2026)

Prompt 05b status: CLOSED.

### Completed Work
- [x] **Slash-Strength Combination Support (`catalog.py` & `import_janaushadhi.py`):**
  - Added `SLASH_STRENGTH_PATTERN` to support multi-strength bracketed specs like `(25/12.5 Mg)` or `(30/15/500 Mg)`.
  - Removed row-level `has_strength` override. Each component's `parse_ok` reflects its own parsed strength.
  - Corrected `parse_failed_rows` to `no_strength_rows` in `import_report.json` and added `slash_strength_rows` (41) and `slash_mismatch_rows` (0).
  - Regenerated `janaushadhi.json` (SHA256: `e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`) and verified 100% deterministic re-runs.
- [x] **Exact-First Search Policy (`catalog.py`):**
  - Updated `catalog.search` to return exact component-salt matches first. Fallback to `name_clean` substring match only when 0 exact matches exist.
  - Prevents substring contamination (e.g. searching `amlodipine` excludes chirally pure `levamlodipine` items).
- [x] **Expanded Test Suite (`test_catalog.py`):**
  - Replaced tautological assertion in `test_levothyroxine_synonym_search` to verify `any(c.get("salt") == "levothyroxine")`.
  - Added tests for slash combinations, unflavored syrups without strengths, sr_no 2014 row verification, amlodipine exclusion, and report metrics.
  - Catalog test count increased from 26 to 35 (all passed in 0.08s).
  - Full test suite passed: **88 passed, 0 failed** (53 baseline + 35 catalog tests).
- [x] **Artifacts & Generated File Cleanup:**
  - Deleted 8 intermediate `.txt` test and import logs from `backend/`.
- [x] **Parity & Invariant Verification:**
  - Route count: 43.
  - In-memory LF OpenAPI SHA256: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
  - Zero network imports in `catalog.py`.
- [x] **Documentation Updates:**
  - Appended decision D44 to `decisions.md`.

### Deviations
- Step 4 assertion change: `test_levothyroxine_synonym_search` second assertion changed from `price_status == "listed" or price_per_unit None` (tautological) to `any(c.get("salt") == "levothyroxine" for c in item.get("components", []))`.

### Open & Deferred Items
- Concentration notation (`mg/5 ml`) keeps only the first number (deferred to Phase 2 parser polish).
- Comma splitting on composite names like `Vitamins A,C,D,E` (deferred).
- Brand MRP seed dataset and savings calculation (deferred to P07).
- `/catalog/search` HTTP route (deferred to P07).
- Removal of live scraping (`buying_agent.py`) and `browser_use` dependency (deferred to P07).
- Frontend Compare page adjustments to use static catalog (deferred to frontend phase).
- `is_medicine` non-medicine groups review (Gautam).
- gitignore for `backend/*.txt` and decision on committing `backend/data/`.
```

---

## 6. VERIFICATION
### Step 4: Catalog Test Suite
```powershell
.\venv\Scripts\python.exe -m pytest -q tests\test_catalog.py > pytest_catalog.txt 2>&1 ; Get-Content pytest_catalog.txt -Tail 5
```
Output:
```
...................................                                      [100%]
35 passed in 0.08s
```

### Step 6a: Full Test Suite
```powershell
.\venv\Scripts\python.exe -m pytest -q > pytest_all.txt 2>&1 ; Get-Content pytest_all.txt -Tail 5
```
Output:
```
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
88 passed, 2 warnings in 15.58s
```

### Step 6b: Subprocess Import Check
```powershell
$env:APP_ENV="development"; .\venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); import agents.main; print('IMPORT_OK')"
```
Output:
```
IMPORT_OK
```

### Step 6c: Route & OpenAPI Verification (Post-Step 6)
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

### Step 6d: Forbidden Network Import Check in `catalog.py`
```powershell
Select-String -Path src\agents\catalog.py -Pattern "requests|urllib|httpx|socket"
```
Output:
```
(No matches found)
```

### Step 6e: Git Status & Latest Commit
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
?? backend/pytest_all.txt
?? backend/scripts/
?? backend/src/agents/catalog.py
?? backend/src/agents/errors.py
?? backend/src/agents/file_utils.py
?? backend/src/agents/hospital_parser.py
?? backend/src/agents/llm_output.py
?? backend/src/agents/rate_limit.py
?? backend/src/agents/routes/
?? backend/src/agents/schemas.py
?? backend/tests/test_catalog.py
?? backend/tests/test_phase0.py
?? backend/tests/test_routes_auth.py
?? local-changes.patch
0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths
```

---

## 7. DELETIONS
Step 5 execution results:
- **Deleted (8 files):**
  - `health_out.txt`
  - `import_out.txt`
  - `pytest_out.txt`
  - `pytest_all.txt`
  - `pytest_catalog.txt`
  - `pytest_health.txt`
  - `pytest_p0.txt`
  - `pytest_auth.txt`
- **Did not exist (0 files):** None

---

## 8. CHECKLIST
- [x] Step 0: Pre-flight verified (no python processes running; input CSV verified: `4AC1C0E8967E16DE86AAD74B0810FC06342D5F81BBE3E27BB7C6E5D46E02C4D3`; 79 baseline tests passed; 43 routes; canonical OpenAPI hash: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`)
- [x] Step 1: `parse_components` rewritten with `SLASH_STRENGTH_PATTERN`, per-component `parse_ok`, and removal of row-level `has_strength` override
- [x] Step 2: `catalog.search` updated to exact component match first with fallback to substring match
- [x] Step 3: `import_janaushadhi.py` updated with `no_strength_rows`, `slash_strength_rows`, and `slash_mismatch_rows`; deterministic re-runs confirmed (`e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`)
- [x] Step 4: `tests/test_catalog.py` updated with permitted assertion modification and new test suites; all 35 passed in 0.08s
- [x] Step 5: Allowed untracked `.txt` output files cleanly deleted from `backend/`
- [x] Step 6: Invariants verified (88 passed in full suite; `IMPORT_OK`; 43 operations; canonical OpenAPI hash unchanged; zero network imports in `catalog.py`)
- [x] Step 7: Documentation updated (appended decision D44 and progress entry P05b)
- [x] Step 8: Dump created (`Project-docs\dumps\P05b_dump.md`)

---

## 9. DEVIATIONS AND BLOCKERS
- **Step 4 Assertion Change (Intentional):** In `test_levothyroxine_synonym_search`, replaced the tautological second assertion (`assert item["price_status"] == "listed" or item["price_per_unit"] is None`) with `assert any(c.get("salt") == "levothyroxine" for c in item.get("components", []))`, verifying that every returned item actually contains the searched canonical salt.

---

## 10. DEFERRED
- Concentration notation (`mg/5 ml`) keeps only the first number.
- Comma splitting on composite names like `Vitamins A,C,D,E`.
- Brand MRP seed dataset and savings calculation (deferred to P07).
- `/catalog/search` HTTP route (deferred to P07).
- Removal of live scraping (`buying_agent.py`) and `browser_use` dependency (deferred to P07).
- Frontend Compare page adjustments to use static catalog (deferred to frontend phase).
- `is_medicine` non-medicine groups review (Gautam).
- gitignore for `backend/*.txt` and decision on committing `backend/data/`.

