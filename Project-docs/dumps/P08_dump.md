# P08 Dump — Search Quality (Single-Ingredient First, Strength-Aware Queries, Concentration Guard, Strict Tests, Measured Timing)

## 1. HEADER
- **Prompt ID:** PROMPT 08: Search quality (single-ingredient first, strength-aware queries, concentration guard, strict tests, measured timing)
- **Timestamp:** 2026-11-03 07:20:00 IST
- **Venv Python Version:** Python 3.11.9
- **Git Commit:** `0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths`

---

## 2. PRE-FLIGHT
### Step 0a: Active Python Process Check
```powershell
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, CPU
```
Output:
```
(No active python processes running; exit code 1)
```

### Step 0b: PMBJP CSV Verification
```powershell
Test-Path backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv
Get-FileHash -Algorithm SHA256 backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv
```
Output:
```
True

Algorithm       Hash                                                                   Path
---------       ----                                                                   ----
SHA256          4AC1C0E8967E16DE86AAD74B0810FC06342D5F81BBE3E27BB7C6E5D46E02C4D3       C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\janaushadhi\PMBJP_Product_List_2026-11-02.csv
```

---

## 3. BASELINE
### Step 1a: Baseline Pytest Suite Execution
```powershell
cd backend ; .\venv\Scripts\python.exe -m pytest -q --durations=10 > pytest_out.txt 2>&1 ; Get-Content pytest_out.txt -Tail 20
```
Output:
```
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================ slowest 10 durations =============================
14.23s call     tests/test_phase0.py::test_subprocess_import_minimal_env
1.04s call     tests/test_phase0.py::test_subprocess_import_production_fails_without_jwt_secret
0.15s call     tests/test_phase0.py::test_import_hermetic
0.04s call     tests/test_phase0.py::test_auth_login_rate_limit
0.03s call     tests/test_price_lookup.py::test_unknown_medicine
0.03s call     tests/test_phase0.py::test_call_schedule_disabled_by_default
0.02s call     tests/test_price_lookup.py::test_run_comparison_shape
0.02s call     tests/test_price_lookup.py::test_no_scraping_module
0.02s call     tests/test_phase0.py::test_medicine_compare_rate_limit
0.02s call     tests/test_catalog.py::test_row_count_and_unique_codes
145 passed, 2 warnings in 29.60s
```

### Step 1b: Baseline Route Count & OpenAPI Hash
```powershell
import json, hashlib, sys, os
os.environ["APP_ENV"] = "development"
sys.path.insert(0, "src")
from agents.main import app
spec_obj = app.openapi()
spec = json.dumps(spec_obj, sort_keys=True, indent=2)
ops = sum(1 for p, ops in spec_obj['paths'].items() for m in ops if m in {'get', 'post', 'put', 'delete', 'patch'})
print('OPERATIONS:', ops)
print('OPENAPI_SHA256_INMEMORY_LF:', hashlib.sha256(spec.encode('utf-8')).hexdigest())
```
Output:
```
OPERATIONS: 43
OPENAPI_SHA256_INMEMORY_LF: 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1
```

---

## 4. IMPORTER
### Clean-State Run 1:
```powershell
cd backend
Remove-Item -Path data\catalog\janaushadhi.json, data\catalog\import_report.json -Force -ErrorAction SilentlyContinue
.\venv\Scripts\python.exe scripts\import_janaushadhi.py > import_run1.txt 2>&1
Get-Content import_run1.txt -Tail 14
Get-FileHash data\catalog\janaushadhi.json
```
Output:
```
Import completed successfully.
Total rows: 2445
Unique drug codes: 2445
Zero MRP rows: 345
No strength rows: 382
Slash strength rows: 41
Slash mismatch rows: 0
Combination rows: 878
Concentration rows: 1
Pack count present rows: 1730
Non-medicine rows: 350
Output SHA256: 29ad8926fddb0d6acda164edd9a8ccc2ea0dc4ecd0b0ee813c58aec178860f3f

Algorithm       Hash                                                                   Path
---------       ----                                                                   ----
SHA256          29AD8926FDDB0D6ACDA164EDD9A8CCC2EA0DC4ECD0B0EE813C58AEC178860F3F       C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\catalog\janaushadhi.json
```

### Clean-State Run 2:
```powershell
Remove-Item -Path data\catalog\janaushadhi.json, data\catalog\import_report.json -Force -ErrorAction SilentlyContinue
.\venv\Scripts\python.exe scripts\import_janaushadhi.py > import_run2.txt 2>&1
Get-Content import_run2.txt -Tail 14
Get-FileHash data\catalog\janaushadhi.json
```
Output:
```
Import completed successfully.
Total rows: 2445
Unique drug codes: 2445
Zero MRP rows: 345
No strength rows: 382
Slash strength rows: 41
Slash mismatch rows: 0
Combination rows: 878
Concentration rows: 1
Pack count present rows: 1730
Non-medicine rows: 350
Output SHA256: 29ad8926fddb0d6acda164edd9a8ccc2ea0dc4ecd0b0ee813c58aec178860f3f

Algorithm       Hash                                                                   Path
---------       ----                                                                   ----
SHA256          29AD8926FDDB0D6ACDA164EDD9A8CCC2EA0DC4ECD0B0EE813C58AEC178860F3F       C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\catalog\janaushadhi.json
```
Both hashes are strictly identical: `29AD8926FDDB0D6ACDA164EDD9A8CCC2EA0DC4ECD0B0EE813C58AEC178860F3F`.

### import_report.json (Verbatim)
```json
{
  "input_sha256": "4ac1c0e8967e16de86aad74b0810fc06342d5f81bbe3e27bb7c6e5d46e02c4d3",
  "output_sha256": "29ad8926fddb0d6acda164edd9a8ccc2ea0dc4ecd0b0ee813c58aec178860f3f",
  "total_rows": 2445,
  "unique_drug_codes": 2445,
  "zero_mrp_rows": 345,
  "no_strength_rows": 382,
  "slash_strength_rows": 41,
  "slash_mismatch_rows": 0,
  "combination_rows": 878,
  "concentration_rows": 1,
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

### `backend\src\agents\catalog.py` (COMPLETE)
```python
import os
import re
import json
import functools
from typing import Optional, List, Dict, Any, Tuple

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


_QUERY_PATTERN = re.compile(
    r"^(?P<name>.+?)\s+(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|g|iu|%|ml)?$",
    re.IGNORECASE,
)


def parse_query(q: str) -> Tuple[str, Optional[float], Optional[str]]:
    norm = normalize_text(q)
    m = _QUERY_PATTERN.match(norm)
    if m:
        name = m.group("name")
        num = float(m.group("num"))
        unit = m.group("unit").lower() if m.group("unit") else None
        return (canonical_salt(name), num, unit)
    return (canonical_salt(norm), None, None)


def search(query: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Search catalog items for query.
    If strength is specified, returns exact salt and strength matches (excluding concentration rows),
    with no fallback to salt-only matches.
    If strength is not specified, returns exact salt matches if any, or falls back to name_clean substring.
    Results are sorted by single-ingredient first, non-concentration first, price_per_unit ascending (None last),
    and drug_code.
    """
    name, strength, unit = parse_query(query)
    exact = [item for item in items if any(c.get("salt") == name for c in item.get("components", []))]

    if strength is not None:
        matches = [
            item for item in exact
            if not item.get("is_concentration")
            and any(
                c.get("salt") == name
                and c.get("strength") == strength
                and (unit is None or c.get("unit") == unit)
                for c in item.get("components", [])
            )
        ]
    else:
        matches = exact if exact else [item for item in items if name in item.get("name_clean", "")]

    matches.sort(
        key=lambda item: (
            item.get("is_combination", False),
            item.get("is_concentration", False),
            item.get("price_per_unit") is None,
            item.get("price_per_unit") or 0.0,
            item.get("drug_code", ""),
        )
    )
    return matches
```

### `backend\src\agents\price_lookup.py` (COMPLETE)
```python
"""Catalog-backed price lookup over the PMBJP list. No network. No scraping."""

from typing import Any, Dict, List, Optional

from agents import catalog

JANAUSHADHI_SITE = "PMBJP Jan Aushadhi"
MAX_RESULTS_PER_MEDICINE = 10


async def run_comparison(medicines: List[str]) -> Dict[str, Any]:
    """Catalog-backed comparison returning PMBJP Jan Aushadhi prices."""
    items = catalog.load_catalog()
    medicines_output: List[Dict[str, Any]] = []

    for raw in medicines:
        name = (raw or "").strip()
        if not name:
            continue

        hits = catalog.search(name, items)[:MAX_RESULTS_PER_MEDICINE]
        results: List[Dict[str, Any]] = []

        for h in hits:
            available = h.get("price_status") == "listed"
            notes = f"{h.get('dosage_form', '')} | list dated {h.get('source_date', '')}"
            if h.get("is_combination"):
                notes += " | combination"
            if h.get("is_concentration"):
                notes += " | concentration (mg/ml)"
            if not available:
                notes += " | price not notified"

            result_entry = {
                "site": JANAUSHADHI_SITE,
                "product_name": h.get("name_raw", ""),
                "price": h.get("mrp"),
                "quantity": h.get("unit_size_raw", ""),
                "delivery_info": "",
                "product_url": "",
                "available": available,
                "notes": notes,
            }
            results.append(result_entry)

        best_price_site: Optional[str] = (
            JANAUSHADHI_SITE if any(r["available"] for r in results) else None
        )

        medicines_output.append(
            {
                "medicine_name": name,
                "results": results,
                "best_price_site": best_price_site,
                "fastest_delivery_site": None,
            }
        )

    return {"medicines": medicines_output}
```

### `backend\scripts\import_janaushadhi.py` (COMPLETE)
```python
import csv
import json
import hashlib
import re
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
            # Check if slash mismatch occurred:
            # If m matched, but row_parse_ok is False, it was a mismatch between salt count and numbers count
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
        is_combination = len(components) > 1
        is_concentration = re.search(r"\bmg\s*/\s*(\d+(\.\d+)?\s*)?ml\b", name_clean) is not None

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
            "is_combination": is_combination,
            "is_concentration": is_concentration,
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
    combination_rows = sum(1 for x in items if x["is_combination"])
    concentration_rows = sum(1 for x in items if x["is_concentration"])
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
        "combination_rows": combination_rows,
        "concentration_rows": concentration_rows,
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
    print(f"Combination rows: {combination_rows}")
    print(f"Concentration rows: {concentration_rows}")
    print(f"Pack count present rows: {pack_count_present_rows}")
    print(f"Non-medicine rows: {non_medicine_rows}")
    print(f"Output SHA256: {output_sha256}")


if __name__ == "__main__":
    run_import()
```

### `backend\tests\test_search_quality.py` (COMPLETE)
```python
"""Tests for search quality, strength-aware matching, and concentration guard."""

import asyncio
import json
from pathlib import Path
import socket
import sys
import time
import traceback
import pytest

# Ensure backend/src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agents import catalog
from agents.price_lookup import run_comparison


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Ensure tests make zero network calls while allowing asyncio internal loopback."""
    orig_socket = socket.socket

    class GuardedSocket(orig_socket):
        def __init__(self, *args, **kwargs):
            stack = traceback.extract_stack()
            # Allow internal self-pipe creation in asyncio on Windows
            if not any("socketpair" in f.name for f in stack):
                raise RuntimeError("Network calls are forbidden during catalog tests")
            super().__init__(*args, **kwargs)

        def connect(self, address):
            host = address[0] if isinstance(address, tuple) else address
            if host not in ("127.0.0.1", "::1", "localhost"):
                raise RuntimeError("Network calls are forbidden during catalog tests")
            return super().connect(address)

    monkeypatch.setattr(socket, "socket", GuardedSocket)


def test_parse_query():
    assert catalog.parse_query("paracetamol 650") == ("paracetamol", 650.0, None)
    assert catalog.parse_query("Levothyroxine 100 mcg") == ("levothyroxine", 100.0, "mcg")
    assert catalog.parse_query("Cetirizine") == ("cetirizine", None, None)
    assert catalog.parse_query("S(-)Amlodipine 2.5 mg") == ("levamlodipine", 2.5, "mg")


def test_search_paracetamol_single_ingredient_first():
    items = catalog.load_catalog()
    results = catalog.search("paracetamol", items)
    assert len(results) > 0
    first = results[0]
    assert first["is_combination"] is False
    assert any(c.get("salt") == "paracetamol" for c in first.get("components", []))


def test_search_paracetamol_650_exact():
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 650", items)
    assert len(results) > 0
    assert results[0]["sr_no"] == 398
    for item in results:
        assert any(
            c.get("salt") == "paracetamol" and c.get("strength") == 650.0
            for c in item.get("components", [])
        )


def test_search_paracetamol_650_no_concentration():
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 650", items)
    assert len(results) > 0
    assert not any(item.get("is_concentration") is True for item in results)


def test_search_paracetamol_9999_empty():
    items = catalog.load_catalog()
    assert catalog.search("paracetamol 9999", items) == []


def test_search_amlodipine_excludes_levamlodipine():
    items = catalog.load_catalog()
    results = catalog.search("amlodipine", items)
    assert len(results) > 0
    assert not any(
        any(c.get("salt") == "levamlodipine" for c in item.get("components", []))
        for item in results
    )


def test_concentration_items_have_mg_and_ml():
    items = catalog.load_catalog()
    conc_items = [item for item in items if item.get("is_concentration") is True]
    assert len(conc_items) > 0
    for item in conc_items:
        clean = item.get("name_clean", "")
        assert "mg" in clean
        assert "ml" in clean


def test_import_report_combination_and_concentration_counts():
    report_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "import_report.json"
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert "combination_rows" in report
    assert isinstance(report["combination_rows"], int)
    assert "concentration_rows" in report
    assert isinstance(report["concentration_rows"], int)

    items = catalog.load_catalog()
    comb_count = sum(1 for item in items if item.get("is_combination") is True)
    conc_count = sum(1 for item in items if item.get("is_concentration") is True)
    assert report["combination_rows"] == comb_count
    assert report["concentration_rows"] == conc_count


def test_timing_10_medicines():
    names = [
        "Paracetamol",
        "Ibuprofen",
        "Metformin",
        "Pantoprazole",
        "Atorvastatin",
        "Amlodipine",
        "Cetirizine",
        "Levothyroxine",
        "Ondansetron",
        "Azithromycin",
    ]
    t0 = time.perf_counter()
    res = asyncio.run(run_comparison(names))
    elapsed = time.perf_counter() - t0
    assert elapsed < 2.0
    assert len(res["medicines"]) == 10
```

### `backend\tests\test_price_lookup.py` (Old and New Function Body)
**Old Function Body:**
```python
def test_best_price_site_when_available():
    res = asyncio.run(run_comparison(["Paracetamol"]))
    m = res["medicines"][0]
    if any(r["available"] for r in m["results"]):
        assert m["best_price_site"] == JANAUSHADHI_SITE
```

**New Function Body:**
```python
def test_best_price_site_when_available():
    res = asyncio.run(run_comparison(["Paracetamol"]))
    m = res["medicines"][0]
    assert any(r["available"] for r in m["results"])
    assert m["best_price_site"] == JANAUSHADHI_SITE
```

### `backend\tests\test_catalog.py` (Added Functions Only)
Added functions: None (all 9 required search quality and concentration tests were implemented in the dedicated test file `backend/tests/test_search_quality.py`). Existing 35 tests in `test_catalog.py` remain untouched and 100% passing.

### `Project-docs\decisions.md` (Appended Text Only)
```markdown
---

## D47 — Search Quality: Single-Ingredient First, Strength-Aware Matching, and Concentration Guard (3 Nov 2026)

**Status:** Built and verified (Prompt 08, 3 Nov 2026). All 154 automated tests passing (145 baseline + 9 new search quality tests). Route count: 43. OpenAPI canonical in-memory LF SHA256 preserved (`37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`). Catalog JSON hash deliberately updated to `29ad8926fddb0d6acda164edd9a8ccc2ea0dc4ecd0b0ee813c58aec178860f3f`. Zero frontend modifications.

**Decisions:**
1. **Single-Ingredient-First Ordering:**
   - In P07 live output, querying "Paracetamol" yielded a combination product ("Paracetamol 325mg and Dicyclomine Hydrochloride 20mg Tablets") as the second result before higher-strength single-ingredient Paracetamol tablets.
   - Products are now ranked with `is_combination == False` ahead of `is_combination == True`. Users querying an active generic ingredient receive pure single-ingredient formulations first before combination therapies.
2. **Strength-Aware Matching & Strict Precision:**
   - Introduced `parse_query(q)` in `agents.catalog` parsing queries with trailing numeric strength and optional unit (e.g., "Paracetamol 650", "Levothyroxine 100 mcg").
   - When a strength is specified, matching strictly requires an exact salt and strength match (`c.strength == strength` and unit alignment). If no product matches the exact strength, `search()` returns `[]` instead of silently falling back to salt-only results. Returning a 500 mg product for a 650 mg query would be clinically inaccurate and unsafe.
3. **Concentration Guard (Carrying P06 Constraint):**
   - Implemented regex heuristic `re.search(r"\bmg\s*/\s*(\d+(\.\d+)?\s*)?ml\b", name_clean)` marking concentration products (e.g., "mg/5 ml", "mg/ml") with `is_concentration: True`.
   - Concentration rows are strictly excluded from strength-qualified tablet/capsule queries, preventing liquid concentrations from erroneously matching solid dosage strengths. Concentration rows sort after solid dosage forms.
4. **Deliberate Catalog Hash Change:**
   - Added `is_combination` (bool) and `is_concentration` (bool) to each catalog item in `backend/scripts/import_janaushadhi.py`.
   - Added `combination_rows: 878` and `concentration_rows: 1` to `import_report.json`.
   - Previous catalog SHA256: `e5d0b82758b702959789f67691b03baa438c9a2ba9713237b8cf6ff14bb68d7c`.
   - New catalog SHA256: `29ad8926fddb0d6acda164edd9a8ccc2ea0dc4ecd0b0ee813c58aec178860f3f`.
   - Determinism verified: two consecutive clean-state importer runs produced identical SHA256 hashes (`29ad8926fddb0d6acda164edd9a8ccc2ea0dc4ecd0b0ee813c58aec178860f3f`).
5. **Permitted Test Change (`test_best_price_site_when_available`):**
   - The original test in `test_price_lookup.py` used a conditional assertion `if any(r["available"] for r in m["results"]): assert m["best_price_site"] == JANAUSHADHI_SITE`. If no results were available, the assertion was silently bypassed, making the test weak.
   - Replaced with strict assertions:
     ```python
     res = asyncio.run(run_comparison(["Paracetamol"]))
     m = res["medicines"][0]
     assert any(r["available"] for r in m["results"])
     assert m["best_price_site"] == JANAUSHADHI_SITE
     ```
   - This explicitly enforces that Paracetamol returns available products and sets `best_price_site` properly.
6. **Live Measured Timing (Verbatim):**
   - Server smoke test measuring `POST /medicine/compare` with `["Paracetamol", "Paracetamol 650"]`:
     `TotalMilliseconds: 148.4555`
   - Test suite timing test (`test_timing_10_medicines`) querying 10 distinct medicines executed in ~0.02s (well below the 2.0s threshold).
7. **Known Limits & Deferred Items:**
   - Brand names (e.g. Dolo 650, Calpol) do not match generic salts until the brand-to-generic mapping and verified strip data are implemented (P09).
   - The 10-result cap (`MAX_RESULTS_PER_MEDICINE = 10`) can hide rare rows when a salt has numerous formulations.
   - Cross-form price per unit normalization (e.g., syrup ml vs tablet units).
   - Concentration unit normalization.
```

### `Project-docs\progress.md` (Appended Text Only)
```markdown
---

## Prompt 08 — Search Quality: Single-Ingredient First, Strength-Aware Matching, and Concentration Guard (3 Nov 2026)

Prompt 08 status: CLOSED.

### Completed Work
- [x] **Catalog Importer Enhancement (`scripts/import_janaushadhi.py`):**
  - Added `is_combination` (`len(components) > 1`) and `is_concentration` (`re.search(r"\bmg\s*/\s*(\d+(\.\d+)?\s*)?ml\b", name_clean) is not None`) to every catalog item.
  - Added `combination_rows: 878` and `concentration_rows: 1` to `import_report.json`.
  - Determinism verified with two consecutive clean-state importer runs producing identical SHA256: `29ad8926fddb0d6acda164edd9a8ccc2ea0dc4ecd0b0ee813c58aec178860f3f`.
- [x] **Catalog Search Quality (`agents/catalog.py`):**
  - Added `parse_query(q)` parsing generic names, strengths, and units.
  - Updated `search()`:
    - If strength is given: exact salt and strength matching, concentration rows excluded, no fallback to salt-only matches (returns `[]` on mismatch).
    - If no strength is given: exact salt matches first, fallback to `name_clean` substring.
    - Sort order: `(item.is_combination, item.is_concentration, price_per_unit is None, price_per_unit or 0.0, drug_code)`. Single-ingredient products appear first.
- [x] **Price Lookup Formatter Update (`agents/price_lookup.py`):**
  - Appended notes flags in exact order: dosage_form | list dated <date> | combination | concentration (mg/ml) | price not notified.
- [x] **Test Suite & Invariants:**
  - Full test suite: **154 passed, 0 failed** in 28.35s (145 baseline + 9 new search quality tests).
  - Permitted test improvement: `test_best_price_site_when_available` updated from conditional check to unconditional assertion.
  - New test file: `backend/tests/test_search_quality.py` with 9 comprehensive tests covering `parse_query`, single-ingredient priority, 650 exact matches, concentration guards, empty on mismatch, amlodipine/levamlodipine exclusion, concentration regex verification, report counts, and 10-medicine timing.
  - Route count: 43 (0 new routes added).
  - OpenAPI canonical in-memory LF SHA256 preserved: `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
  - Subprocess hermetic import verified (`IMPORT_OK`).
  - Zero `browser_use` or `playwright` occurrences in `src`.
  - Live smoke test measured timing: `148.4555 ms` for `["Paracetamol", "Paracetamol 650"]` with Paracetamol returning single-ingredient formulations first.

### Deferred Items
- Brand map and savings (P09, needs verified strip data).
- Frontend Compare update.
- Playwright and browser-use removal from `pyproject.toml`, `uv.lock`, and `Dockerfile` (deployment prompt).
- H1 (`/call/status` public when calls are enabled).
- M5 (`Project-docs` not under version control).
- Decision on committing `backend/data/`.
- `is_medicine` non-medicine groups review (Gautam).
- Concentration unit normalization.
- Comma-split limit.
- `x-request-id` header exposure to browser clients (`Access-Control-Expose-Headers`, frontend phase).
```

### `backend\data\catalog\janaushadhi.json`
- **SHA256:** `29ad8926fddb0d6acda164edd9a8ccc2ea0dc4ecd0b0ee813c58aec178860f3f`
- **File Size:** 1,921,742 bytes
- **Total Catalog Rows:** 2,445 items

*Never include backend\.env. Frontend entries: zero.*

---

## 6. VERIFICATION

### Step 5a: Full Test Suite Execution (Durations Block)
```powershell
.\venv\Scripts\python.exe -m pytest -q --durations=10 > pytest_all.txt 2>&1 ; Get-Content pytest_all.txt -Tail 20
```
Output:
```
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================ slowest 10 durations =============================
13.82s call     tests/test_phase0.py::test_subprocess_import_minimal_env
0.86s call     tests/test_phase0.py::test_subprocess_import_production_fails_without_jwt_secret
0.10s call     tests/test_phase0.py::test_import_hermetic
0.03s call     tests/test_phase0.py::test_auth_login_rate_limit
0.03s call     tests/test_phase0.py::test_call_schedule_disabled_by_default
0.02s call     tests/test_search_quality.py::test_timing_10_medicines
0.02s call     tests/test_phase0.py::test_medicine_compare_rate_limit
0.02s call     tests/test_catalog.py::test_row_count_and_unique_codes
0.01s call     tests/test_price_lookup.py::test_not_notified_rows
0.01s call     tests/test_price_lookup.py::test_no_scraping_module
154 passed, 2 warnings in 28.35s
```

### Step 5b: Subprocess Import Check
```powershell
$env:APP_ENV="development"; .\venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); import agents.main; print('IMPORT_OK')"
```
Output:
```
IMPORT_OK
```

### Step 5c: Route & OpenAPI Hash Verification
```powershell
cd backend ; .\venv\Scripts\python.exe scratch\check_openapi.py
```
Output:
```
OPERATIONS: 43
OPENAPI_SHA256_INMEMORY_LF: 37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1
```

### Step 5d: Zero Scraping References in `src`
```powershell
Get-ChildItem src -Recurse -Filter *.py | Select-String -Pattern "browser_use|playwright"
```
Output:
```
(No matches found)
```

### Step 5e: Live Check with Measure-Command (Verbatim)
```powershell
=== MEASURE-COMMAND OUTPUT ===

TotalMilliseconds
-----------------
         148.4555


=== RESULTS FOR MEDICINES ===
--- Medicine: Paracetamol ---
Best Price Site: PMBJP Jan Aushadhi
First 3 Results:
[
    {
        "site":  "PMBJP Jan Aushadhi",
        "product_name":  "Paracetamol Tablets IP 500 mg",
        "price":  6.56,
        "quantity":  "10\u0027s",
        "delivery_info":  "",
        "product_url":  "",
        "available":  true,
        "notes":  "Tablet | list dated 2026-11-02"
    },
    {
        "site":  "PMBJP Jan Aushadhi",
        "product_name":  "Paracetamol Tablets IP 650 mg",
        "price":  15.47,
        "quantity":  "15\u0027s",
        "delivery_info":  "",
        "product_url":  "",
        "available":  true,
        "notes":  "Tablet | list dated 2026-11-02"
    },
    {
        "site":  "PMBJP Jan Aushadhi",
        "product_name":  "Paracetamol Tablets IP 1000 Mg",
        "price":  15.0,
        "quantity":  "10\u0027s",
        "delivery_info":  "",
        "product_url":  "",
        "available":  true,
        "notes":  "Tablet | list dated 2026-11-02"
    }
]
--- Medicine: Paracetamol 650 ---
Best Price Site: PMBJP Jan Aushadhi
First 3 Results:
[
    {
        "site":  "PMBJP Jan Aushadhi",
        "product_name":  "Paracetamol Tablets IP 650 mg",
        "price":  15.47,
        "quantity":  "15\u0027s",
        "delivery_info":  "",
        "product_url":  "",
        "available":  true,
        "notes":  "Tablet | list dated 2026-11-02"
    },
    {
        "site":  "PMBJP Jan Aushadhi",
        "product_name":  "Paracetamol 650mg and Caffeine 50mg Tablets IP",
        "price":  17.81,
        "quantity":  "10\u0027s",
        "delivery_info":  "",
        "product_url":  "",
        "available":  true,
        "notes":  "Tablet | list dated 2026-11-02 | combination"
    }
]
```

---

## 7. DELETIONS
- `backend\pytest_out.txt`: Deleted successfully.
- `backend\pytest_all.txt`: Deleted successfully.
- `backend\pytest_search.txt`: Did not exist.

---

## 8. CHECKLIST
- [x] Step 0: Pre-flight process check completed (0 active processes) and PMBJP CSV hash verified (`4AC1C0E8967E16DE86AAD74B0810FC06342D5F81BBE3E27BB7C6E5D46E02C4D3`).
- [x] Step 1: Baseline established with 145 passed tests, 43 operations, and OpenAPI hash `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`.
- [x] Step 2: Importer updated with `is_combination` and `is_concentration`; two clean-state runs matched SHA256 `29ad8926fddb0d6acda164edd9a8ccc2ea0dc4ecd0b0ee813c58aec178860f3f`.
- [x] Step 3: Implemented `parse_query(q)` and enhanced `search()` with strength-aware matching, concentration exclusion, and single-ingredient-first ranking.
- [x] Step 4: Updated `price_lookup.py` notes format; replaced body of `test_best_price_site_when_available`; created `test_search_quality.py` with 9 passing tests.
- [x] Step 5: Full test suite passed (154 passed in 28.35s), `IMPORT_OK` confirmed, OpenAPI invariant confirmed, zero scraping references in `src`, live smoke test recorded `148.4555 ms` with Paracetamol single-ingredient first.
- [x] Step 6: Cleaned up temporary test output text files (`pytest_out.txt`, `pytest_all.txt`).
- [x] Step 7: Appended decision D47 to `decisions.md` and P08 entry to `progress.md`.
- [x] Step 8: Generated complete audit dump report at `Project-docs\dumps\P08_dump.md`.

---

## 9. DEVIATIONS AND BLOCKERS
None.
Permitted change in Step 4b/4c: Replaced conditional assertion in `test_best_price_site_when_available` with unconditional assertions to ensure `best_price_site` is actively tested.

---

## 10. DEFERRED
- Brand map and savings (P09, needs verified strip data).
- Frontend Compare update.
- Playwright and browser-use removal from `pyproject.toml`, `uv.lock`, and `Dockerfile` (deployment prompt).
- H1 (`/call/status` public when calls are enabled).
- M5 (`Project-docs` not under version control).
- Decision on committing `backend/data/`.
- `is_medicine` non-medicine groups review (Gautam).
- Concentration unit normalization.
- Comma-split limit.
- `x-request-id` header exposure to browser clients (`Access-Control-Expose-Headers`, frontend phase).

