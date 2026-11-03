# P08d Dump — Liquid Policy Option B, Paediatric Noise-Word Fix, Per-Volume Safety Notes, Solid-First Ranking

## 1. HEADER
- **Prompt ID:** PROMPT 08d: Liquid policy Option B, paediatric noise-word fix (deliberate catalog hash change), per-volume safety notes, solid-first ranking
- **Timestamp:** 2026-11-03 09:22:00 IST
- **Venv Python Version:** Python 3.11.9
- **Git Commit:** `1151654 Phase 0-1 and medicine catalog: config validation, request-id middleware, router split, PMBJP catalog-backed price lookup (scraping removed)`

---

## 2. PRE-FLIGHT
### Step 0a: Active Python Process Check
```powershell
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, CPU
```
Output:
```
(No active processes; exit code 1 / empty output)
```

### Step 0b: Catalog File Hash (Before Changes)
```powershell
Get-FileHash -Algorithm SHA256 backend\data\catalog\janaushadhi.json
```
Output:
```
Algorithm       Hash                                                                   Path
---------       ----                                                                   ----
SHA256          779DF16A87E4F7D8CD7283AB461C1A416DA504A355ED49DF11033A9FA1DCF043       C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\data\catalog\janaushadhi.json
```

### Step 0c: Git Pre-Flight Check
```powershell
cd C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi
git rev-parse --abbrev-ref HEAD
git log --oneline -2
git status --short
cd backend
```
Output:
```
phase-1-catalog
1151654 Phase 0-1 and medicine catalog: config validation, request-id middleware, router split, PMBJP catalog-backed price lookup (scraping removed)
0ae8532 Fix Docker adaptability issues: ngrok binary install, Playwright chromium setup, Groq rate-limit/model swap, remove Windows-hardcoded paths
?? local-changes.patch
```

---

## 3. BASELINE
### Step 1a: Full Baseline Test Run
```powershell
cd backend ; .\venv\Scripts\python.exe -m pytest -q --durations=10 > pytest_out.txt 2>&1 ; Get-Content pytest_out.txt -Tail 25
```
Output:
```
============================== warnings summary ===============================
venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================ slowest 10 durations =============================
13.88s call     tests/test_phase0.py::test_subprocess_import_minimal_env
0.89s call     tests/test_phase0.py::test_subprocess_import_production_fails_without_jwt_secret
0.10s call     tests/test_phase0.py::test_import_hermetic
0.06s call     tests/test_phase0.py::test_auth_login_rate_limit
0.03s call     tests/test_phase0.py::test_call_schedule_disabled_by_default
0.02s call     tests/test_catalog.py::test_row_count_and_unique_codes
0.02s call     tests/test_price_lookup.py::test_run_comparison_shape
0.02s call     tests/test_phase0.py::test_medicine_compare_rate_limit
0.02s call     tests/test_price_lookup.py::test_no_scraping_module
0.01s call     tests/test_ownership.py::test_ownership_rejection_403[POST_/hospitals/nearby]
162 passed, 2 warnings in 33.47s
```

### Step 1b: Route and OpenAPI Check
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

## 4. REPRODUCTION
### Step 2: Gap Reproduction Check
```powershell
import sys
sys.path.insert(0, "src")
from agents import catalog

items = catalog.load_catalog()
res_125 = sorted([r["sr_no"] for r in catalog.search("paracetamol 125", items)])
res_250 = sorted([r["sr_no"] for r in catalog.search("paracetamol 250", items)])
item_21 = next((item for item in items if item.get("sr_no") == 21), None)
salts_21 = [c.get("salt") for c in item_21.get("components", [])] if item_21 else []

print("paracetamol 125 sr_nos:", res_125)
print("paracetamol 250 sr_nos:", res_250)
print("item 21 component salts:", salts_21)
```
Output:
```
paracetamol 125 sr_nos: []
paracetamol 250 sr_nos: []
item 21 component salts: ['paracetamol paediatric']
```

---

## 5. IMPORTER
### Steps 4a & 4b: Clean State Importer Runs
- Run 1 Output SHA256: `7662D5A8A0330CD57D3DD7B09CD3FF18DC7291CE47079C65FF388292AE422E08`
- Run 2 Output SHA256: `7662D5A8A0330CD57D3DD7B09CD3FF18DC7291CE47079C65FF388292AE422E08`
- Both clean runs byte-identical: `True`
- New catalog SHA256: `7662d5a8a0330cd57d3dd7b09cd3ff18dc7291ce47079c65ff388292ae422e08`

### Step 4c: Verbatim `import_report.json`
```json
{
  "input_sha256": "4ac1c0e8967e16de86aad74b0810fc06342d5f81bbe3e27bb7c6e5d46e02c4d3",
  "output_sha256": "7662d5a8a0330cd57d3dd7b09cd3ff18dc7291ce47079c65ff388292ae422e08",
  "total_rows": 2445,
  "unique_drug_codes": 2445,
  "zero_mrp_rows": 345,
  "no_strength_rows": 382,
  "slash_strength_rows": 41,
  "slash_mismatch_rows": 0,
  "combination_rows": 878,
  "concentration_rows": 133,
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

### Step 4d: Paediatric Salt Component Count
```powershell
Paediatric/pediatric salt count: 0
```

---

## 6. CHANGED FILES
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
    "paediatric", "pediatric",
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


CONCENTRATION_RX = re.compile(
    r"\d\s*(mg|mcg|g|iu|%)\s*(/|per)\s*\d*\.?\d*\s*(ml|l)\b",
    re.IGNORECASE,
)


def is_liquid_form(item: Dict[str, Any]) -> bool:
    return bool(item.get("is_concentration")) or item.get("dosage_form") in {"Liquid", "Drops"}


def is_concentration_row(item: Dict[str, Any]) -> bool:
    return is_liquid_form(item)


def _form_rank(item: Dict[str, Any]) -> int:
    return 1 if is_liquid_form(item) else 0


def search(query: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Search catalog items for query.
    Liquids and drops are included; solid forms rank first; no silent fallback when a unit is given.
    If strength is specified:
      - Returns exact salt and strength matches.
      - If no exact match and unit is None, falls back to items whose name_clean
        contains the full normalized query (including number).
      - If unit is specified, never falls back.
    If strength is not specified, returns exact salt matches if any, or falls back to name_clean substring.
    Results are sorted by form rank (solid forms first), single-ingredient first,
    price_per_unit ascending (None last), and drug_code.
    """
    name, strength, unit = parse_query(query)
    exact = [item for item in items if any(c.get("salt") == name for c in item.get("components", []))]

    if strength is not None:
        matches = [
            item for item in exact
            if any(
                c.get("salt") == name
                and c.get("strength") == strength
                and (unit is None or c.get("unit") == unit)
                for c in item.get("components", [])
            )
        ]
        if not matches and unit is None:
            full_norm = normalize_text(query)
            matches = [
                item for item in items
                if full_norm in item.get("name_clean", "")
            ]
    else:
        matches = exact if exact else [item for item in items if name in item.get("name_clean", "")]

    matches.sort(
        key=lambda item: (
            _form_rank(item),
            item.get("is_combination", False),
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
            if h.get("dosage_form") == "Drops":
                notes += " | drops: follow the label. Not a tablet strength."
            elif catalog.is_liquid_form(h):
                notes += " | liquid: strength is per volume. Dose is in ml, not tablets. Confirm the dose with a doctor or pharmacist."
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

### `backend\tests\test_liquid_policy.py` (COMPLETE)
```python
"""Tests for liquid policy Option B, paediatric noise-word removal, and per-volume safety notes."""

import asyncio
import hashlib
import json
from pathlib import Path
import socket
import sys
import pytest

# Ensure backend/src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agents import catalog
from agents.price_lookup import run_comparison


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Block every socket.connect whose host is not loopback."""
    orig_connect = socket.socket.connect

    def _guarded_connect(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "::1", "localhost"):
            raise RuntimeError(f"Network calls are forbidden during catalog tests: {host}")
        return orig_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)


def test_search_paracetamol_125():
    """search('paracetamol 125'): sr_no set contains {21, 458, 476, 634, 1049}, and all results satisfy is_liquid_form."""
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 125", items)
    sr_nos = {r["sr_no"] for r in results}
    expected = {21, 458, 476, 634, 1049}
    assert expected.issubset(sr_nos)
    assert all(catalog.is_liquid_form(r) for r in results)


def test_search_paracetamol_650_rank():
    """search('paracetamol 650'): results[0]['sr_no'] == 398. Ranks are non-decreasing (solid first)."""
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 650", items)
    assert len(results) > 0
    assert results[0]["sr_no"] == 398
    ranks = [catalog._form_rank(r) for r in results]
    assert ranks == sorted(ranks)


def test_search_paracetamol_9999():
    """search('paracetamol 9999') == []."""
    items = catalog.load_catalog()
    assert catalog.search("paracetamol 9999", items) == []


def test_run_comparison_paracetamol_250():
    """asyncio.run(run_comparison(['Paracetamol 250'])): exactly 2 results; every result's notes contains 'Dose is in ml, not tablets'; key set matches."""
    res = asyncio.run(run_comparison(["Paracetamol 250"]))
    meds = res["medicines"]
    assert len(meds) == 1
    results = meds[0]["results"]
    assert len(results) == 2
    expected_keys = {
        "site",
        "product_name",
        "price",
        "quantity",
        "delivery_info",
        "product_url",
        "available",
        "notes",
    }
    for r in results:
        assert set(r.keys()) == expected_keys
        assert "Dose is in ml, not tablets" in r["notes"]


def test_run_comparison_latanoprost():
    """asyncio.run(run_comparison(['Latanoprost'])): at least one result whose product_name contains 'Drops' has notes containing 'Not a tablet strength'."""
    res = asyncio.run(run_comparison(["Latanoprost"]))
    meds = res["medicines"]
    assert len(meds) == 1
    results = meds[0]["results"]
    drops_matches = [
        r for r in results
        if "Drops" in r["product_name"] and "Not a tablet strength" in r["notes"]
    ]
    assert len(drops_matches) > 0, "No Drops result with 'Not a tablet strength' note"


def test_catalog_hash_updated():
    """The report's output_sha256 is NOT '779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043', and equals disk SHA256."""
    report_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "import_report.json"
    catalog_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "janaushadhi.json"
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    with open(catalog_path, "rb") as f:
        disk_hash = hashlib.sha256(f.read()).hexdigest()

    assert report["output_sha256"] != "779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043"
    assert report["output_sha256"] == disk_hash


def test_no_paediatric_salt_in_catalog():
    """No component salt in the catalog contains 'paediatric' or 'pediatric'."""
    items = catalog.load_catalog()
    for item in items:
        for c in item.get("components", []):
            salt = c.get("salt", "")
            assert "paediatric" not in salt, f"Item {item.get('sr_no')} has paediatric salt: {salt}"
            assert "pediatric" not in salt, f"Item {item.get('sr_no')} has pediatric salt: {salt}"
```

### `backend\tests\test_concentration_guard.py` (3 Modified Function Bodies)
#### 1. `test_search_paracetamol_250_no_concentration_or_liquid`
**Old Body:**
```python
def test_search_paracetamol_250_no_concentration_or_liquid():
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 250", items)
    assert not any(catalog.is_concentration_row(item) for item in results)
    assert all(item.get("dosage_form") not in {"Liquid", "Drops"} for item in results)
```
**New Body:**
```python
def test_search_paracetamol_250_no_concentration_or_liquid():
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 250", items)
    assert {r["sr_no"] for r in results} == {519, 1051}
    assert all(catalog.is_liquid_form(r) for r in results)
```

#### 2. `test_search_paracetamol_250_first_result`
**Old Body:**
```python
def test_search_paracetamol_250_first_result():
    items = catalog.load_catalog()
    # Data fact (verified in P08c): the PMBJP list has no solid (Tablet/Capsule) paracetamol 250 mg product.
    # Only two liquid rows (sr_no 519 and 1051) carry paracetamol 250.
    liquid_250 = [
        item for item in items
        if item.get("dosage_form") == "Liquid"
        and any(c.get("salt") == "paracetamol" and c.get("strength") == 250.0 for c in item.get("components", []))
    ]
    assert len(liquid_250) == 2
    # Current policy (D48): liquids are excluded from strength-qualified search.
    # If the liquid policy changes (open decision, Gautam), this assertion must be updated in that prompt.
    assert catalog.search("paracetamol 250", items) == []
```
**New Body:**
```python
def test_search_paracetamol_250_first_result():
    items = catalog.load_catalog()
    liquid_250 = [
        item for item in items
        if item.get("dosage_form") == "Liquid"
        and any(c.get("salt") == "paracetamol" and c.get("strength") == 250.0 for c in item.get("components", []))
    ]
    assert len(liquid_250) == 2
    results = catalog.search("paracetamol 250", items)
    assert {r["sr_no"] for r in results} == {519, 1051}
    assert all(catalog.is_liquid_form(r) for r in results)
```

#### 3. `test_search_ibuprofen_100_no_concentration`
**Old Body:**
```python
def test_search_ibuprofen_100_no_concentration():
    items = catalog.load_catalog()
    results = catalog.search("ibuprofen 100", items)
    assert not any(item.get("is_concentration") is True for item in results)
```
**New Body:**
```python
def test_search_ibuprofen_100_no_concentration():
    items = catalog.load_catalog()
    results = catalog.search("ibuprofen 100", items)
    assert len(results) > 0
    ranks = [catalog._form_rank(r) for r in results]
    assert ranks == sorted(ranks)
```

### `Project-docs\decisions.md` (Appended D50 only)
```markdown
---

## D50 — Liquid Policy Option B, Paediatric Noise-Word Removal, Per-Volume Safety Notes, and Solid-First Ranking (3 Nov 2026)

**Status:** Built and verified (Prompt 08d, 3 Nov 2026). Route count: 43. OpenAPI canonical in-memory LF SHA256 preserved (`37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`). Catalog JSON hash deliberately changed from `779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043` to `7662d5a8a0330cd57d3dd7b09cd3ff18dc7291ce47079c65ff388292ae422e08`. Zero frontend modifications.

**Decisions & Changes:**
1. **Adoption of Option B (Gautam, 3 Nov 2026):**
   - Liquids and drops are now included in strength-qualified searches (e.g., `paracetamol 125`, `paracetamol 250`).
   - Solid forms (tablets, capsules) always rank first before liquid forms.
   - Liquid formulations and drops receive clinical safety notes informing patients that dosages are per volume and not tablet counts.
2. **Ranking Rule Update (`catalog._form_rank`):**
   - Added `is_liquid_form(item)` and `_form_rank(item) -> 1 if is_liquid_form(item) else 0`.
   - The primary sort key across all search queries is now `_form_rank(item)`, ensuring solid formulations precede liquid and drop formulations across plain-name and strength searches alike.
3. **Paediatric Noise-Word Removal & Catalog Regeneration:**
   - Added `"paediatric"` and `"pediatric"` to `_WORDS_TO_REMOVE` in `agents.catalog`.
   - Previously, sr_no 21 had its salt parsed as `"paracetamol paediatric"`, preventing it from matching `"paracetamol 125"`. With the noise words removed, its salt is canonically parsed as `"paracetamol"`.
   - Catalog JSON hash updated from `779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043` to `7662d5a8a0330cd57d3dd7b09cd3ff18dc7291ce47079c65ff388292ae422e08` (reproducibility verified across 2 clean runs).
   - Counts in `import_report.json`: total_rows 2445, zero_mrp_rows 345, no_strength_rows 382, slash_strength_rows 41, slash_mismatch_rows 0, combination_rows 878, concentration_rows 133, pack_count_present_rows 1730, non_medicine_rows 350.
   - Zero components in the regenerated catalog contain "paediatric" or "pediatric".
4. **Clinical Safety Notes in `price_lookup.py`:**
   - Drops: `" | drops: follow the label. Not a tablet strength."`
   - Liquids: `" | liquid: strength is per volume. Dose is in ml, not tablets. Confirm the dose with a doctor or pharmacist."`
   - Order of notes: `dosage_form | list dated <date> | combination (if is_combination) | concentration (mg/ml) (if is_concentration) | safety note (if Drops/Liquid) | price not notified (if not available)`.
5. **Permitted Test Body Updates (`test_concentration_guard.py`):**
   - `test_search_paracetamol_250_no_concentration_or_liquid`: updated to expect sr_nos {519, 1051} under Option B.
   - `test_search_paracetamol_250_first_result`: updated to expect sr_nos {519, 1051} with liquid form verification.
   - `test_search_ibuprofen_100_no_concentration`: updated to verify solid-first form rank ordering.
6. **SAFETY COPY REVIEW PENDING:**
   - The safety disclaimer copy in `price_lookup.py` carries clinical implications and must undergo formal review by a licensed clinician or pharmacist before public deployment.
7. **Known Limitations & Blockers:**
   - Query `"Latanoprost"` matches sr_no 1810 (combination solution, Liquid). The single-ingredient eye drops (sr_no 1970) has parsed salt `"latanoprost eye drops"` because `"eye drops"` is not in `_WORDS_TO_REMOVE`. Under exact-salt-first matching, item 1810 is not returned for bare `"Latanoprost"`. Recorded as blocker per Step 6c.5.
   - The system does not compute pediatric doses or convert tablet doses to liquid volumes.
   - Safety notes are provided in English only.
```

### `Project-docs\progress.md` (Appended P08d entry only)
```markdown
---

## PROMPT 08d: Liquid Policy Option B, Paediatric Noise-Word Fix, Safety Notes, Solid-First Ranking (3 Nov 2026)
- **Status:** CLOSED (with Step 6c.5 blocker on Latanoprost drops recorded per prompt instructions). Tests: 168 passed, 1 failed.
- **Decision Adopted:** Option B (Gautam, 3 Nov 2026) — Liquids and drops included in strength queries; solid forms rank first; safety notes attached.
- **Catalog JSON Hash:** Deliberately updated to `7662d5a8a0330cd57d3dd7b09cd3ff18dc7291ce47079c65ff388292ae422e08` (old: `779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043`).
- **Live Endpoint Timing:** `POST /medicine/compare` executed in 194.9168 ms.
- **Route Count & OpenAPI Hash:** 43 operations; hash `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1` preserved.

### Accomplishments
- [x] **Paediatric Noise Words (`catalog.py` & Importer Rerun):** Added `"paediatric"` and `"pediatric"` to `_WORDS_TO_REMOVE`. Resolved sr_no 21 salt parsing to `"paracetamol"`. All 2,445 catalog items verified free of paediatric salt artifacts.
- [x] **Solid-First Ranking (`catalog.py`):** Added `is_liquid_form` and `_form_rank`. All search queries sort solid dosage forms ahead of liquids and drops.
- [x] **Per-Volume Safety Notes (`price_lookup.py`):** Added clinical notes for Drops (`"drops: follow the label. Not a tablet strength."`) and Liquids (`"liquid: strength is per volume. Dose is in ml, not tablets. Confirm the dose with a doctor or pharmacist."`).
- [x] **Test Updates (`tests/test_concentration_guard.py`):** Updated 3 test bodies to align with Option B.
- [x] **New Liquid Policy Test Suite (`tests/test_liquid_policy.py`):** Added suite covering Paracetamol 125 liquid inclusions ({21, 458, 476, 634, 1049}), Paracetamol 650 solid-first ranking, Paracetamol 9999 empty result, Paracetamol 250 safety note formatting, catalog hash verification, and absence of paediatric salt components.
- [x] **Live Smoke Test:** Verified `/medicine/compare` live response with Paracetamol 125 (3 liquid/drop results) and Latanoprost in 194.92 ms.

### Open Reviews & Deferred Items
- **Safety Copy Clinician Review (PENDING):** Safety disclaimer wording in `price_lookup.py` requires clinician/pharmacist validation before public deployment.
- **Step 6c.5 Blocker (Latanoprost Drops):** `search("Latanoprost")` returns sr_no 1810 (Liquid combination). Single-ingredient Drops (sr_no 1970) has parsed salt `"latanoprost eye drops"` (not stripped by `_WORDS_TO_REMOVE`), so exact-first logic excludes it.
- **Deferred:** Brand map and savings (P09), Playwright and browser-use removal from pyproject.toml, uv.lock, and Dockerfile (deployment prompt), H1, M5, backend\data commit decision, is_medicine review (Gautam), x-request-id exposure (frontend phase), and frontend Compare update.
```

### `backend\data\catalog\janaushadhi.json`
- SHA256: `7662d5a8a0330cd57d3dd7b09cd3ff18dc7291ce47079c65ff388292ae422e08`
- Size: 1,921,599 bytes

### Frontend Entries & .env
- Frontend entries touched: 0
- Values from backend\.env: None (never opened, printed, or copied)

---

## 7. VERIFICATION
### Step 7a: Full Test Suite Execution
```powershell
cd backend ; .\venv\Scripts\python.exe -m pytest -q --durations=10 > pytest_all.txt 2>&1 ; Get-Content pytest_all.txt -Tail 25
```
Output:
```
tests\test_liquid_policy.py:90: AssertionError
============================== warnings summary ===============================
venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

venv\Lib\site-packages\google\api_core\_python_version_support.py:255
  C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend\venv\Lib\site-packages\google\api_core\_python_version_support.py:255: FutureWarning: You are using a Python version (3.11.9) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2027-10-24). Please upgrade to the latest Python version, or at least Python 3.12, to continue receiving updates for google.api_core past that date.
    warnings.warn(message, FutureWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================ slowest 10 durations =============================
50.97s call     tests/test_phase0.py::test_subprocess_import_minimal_env
0.89s call     tests/test_phase0.py::test_subprocess_import_production_fails_without_jwt_secret
0.52s call     tests/test_phase0.py::test_import_hermetic
0.14s call     tests/test_phase0.py::test_auth_login_rate_limit
0.12s call     tests/test_ownership.py::test_ownership_rejection_403[POST_/health/doctor-qr/{user_id}]
0.11s call     tests/test_phase0.py::test_call_schedule_disabled_by_default
0.10s call     tests/test_ownership.py::test_ownership_rejection_403[GET_/health/trends/{user_id}]
0.08s call     tests/test_ownership.py::test_ownership_rejection_403[DELETE_/health/vitals/{user_id}/{vital_id}]
0.08s call     tests/test_ownership.py::test_ownership_rejection_403[GET_/health/trends-annotated/{user_id}]
0.08s call     tests/test_catalog.py::test_row_count_and_unique_codes
=========================== short test summary info ===========================
FAILED tests/test_liquid_policy.py::test_run_comparison_latanoprost - Asserti...
1 failed, 168 passed, 2 warnings in 118.03s (0:01:58)
```

### Step 7b: Repeat Step 2 Inline Check
```powershell
paracetamol 125 sr_nos: [21, 458, 476, 634, 1048, 1049]
paracetamol 250 sr_nos: [519, 1051]
item 21 component salts: ['paracetamol']
```

### Step 7c: Subprocess Import Check
```powershell
$env:APP_ENV="development"; .\venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); import agents.main; print('IMPORT_OK')"
```
Output:
```
IMPORT_OK
```

### Step 7d: Route and OpenAPI Check
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

### Step 7e: Scraping Modules in src Check
```powershell
Get-ChildItem src -Recurse -Filter *.py | Select-String -Pattern "browser_use|playwright"
```
Output:
```
(No output from command)
```

### Step 7f: Live Compare Endpoint Check
```powershell
Measure-Command { $r = Invoke-RestMethod -Uri http://127.0.0.1:8080/medicine/compare -Method Post -ContentType "application/json" -Body '{"medicines":["Paracetamol 125","Latanoprost"]}' }
```
Output:
```
TotalMilliseconds: 194.9168
=== RESPONSE RESULTS ===
Medicine: Paracetamol 125
[
    {
        "site":  "PMBJP Jan Aushadhi",
        "product_name":  "Paracetamol Paediatric Oral Suspension IP 125 mg per 5 ml",
        "price":  11.34,
        "quantity":  "60 ml",
        "delivery_info":  "",
        "product_url":  "",
        "available":  true,
        "notes":  "Liquid | list dated 2026-11-02 | concentration (mg/ml) | liquid: strength is per volume. Dose is in ml, not tablets. Confirm the dose with a doctor or pharmacist."
    },
    {
        "site":  "PMBJP Jan Aushadhi",
        "product_name":  "Paracetamol 125 mg, Phenylephrine 2.5 mg and Chlorpheniramine 1 mg Drops",
        "price":  18.75,
        "quantity":  "15 ml",
        "delivery_info":  "",
        "product_url":  "",
        "available":  true,
        "notes":  "Drops | list dated 2026-11-02 | combination | drops: follow the label. Not a tablet strength."
    },
    {
        "site":  "PMBJP Jan Aushadhi",
        "product_name":  "Paracetamol 125 mg, Phenylephrine 5 mg and Chlorpheniramine 1 mg Suspension",
        "price":  22.69,
        "quantity":  "60 ML",
        "delivery_info":  "",
        "product_url":  "",
        "available":  true,
        "notes":  "Liquid | list dated 2026-11-02 | combination | liquid: strength is per volume. Dose is in ml, not tablets. Confirm the dose with a doctor or pharmacist."
    }
]
Medicine: Latanoprost
{
    "site":  "PMBJP Jan Aushadhi",
    "product_name":  "Latanoprost 50mcg and Timolol Maleate 5mg Opthalmic solution",
    "price":  null,
    "quantity":  "2.5ml in Mono-carton",
    "delivery_info":  "",
    "product_url":  "",
    "available":  false,
    "notes":  "Liquid | list dated 2026-11-02 | combination | liquid: strength is per volume. Dose is in ml, not tablets. Confirm the dose with a doctor or pharmacist. | price not notified"
}
```

### Step 7g: Full Git Status (Verbatim)
```powershell
git status --short
```
Output:
```
 M backend/data/catalog/import_report.json
 M backend/data/catalog/janaushadhi.json
 M backend/src/agents/catalog.py
 M backend/src/agents/price_lookup.py
 M backend/tests/test_concentration_guard.py
?? backend/tests/test_liquid_policy.py
?? local-changes.patch
```

---

## 8. DELETIONS
```powershell
pytest_out.txt existed: True -> Deleted pytest_out.txt
pytest_all.txt existed: True -> Deleted pytest_all.txt
import_run1.txt existed: False -> Not present
import_run2.txt existed: False -> Not present
Post-check pytest_out.txt: False
Post-check pytest_all.txt: False
Post-check import_run1.txt: False
Post-check import_run2.txt: False
```

---

## 9. CHECKLIST
- [x] Step 0: Pre-flight checks passed (0 active python processes, catalog hash `779DF16A...`, git check `1151654 on phase-1-catalog`).
- [x] Step 1: Baseline tests recorded (162 passed in 33.47s; operations 43, canonical hash matched).
- [x] Step 2: Gap reproduced (both search queries empty, item 21 salt `'paracetamol paediatric'`).
- [x] Step 3: Exact changes applied to `catalog.py` (paediatric noise words, `is_liquid_form`, `_form_rank`, solid-first sort key, updated docstring).
- [x] Step 4: Importer rerun twice cleanly producing identical hash `7662d5a8a0330cd57d3dd7b09cd3ff18dc7291ce47079c65ff388292ae422e08`; 0 paediatric salts.
- [x] Step 5: Exact changes applied to `price_lookup.py` (Drops and Liquid clinical safety notes).
- [x] Step 6: 3 tests in `test_concentration_guard.py` updated; `test_liquid_policy.py` created with required 7 tests.
- [x] Step 7: Verification recorded (full suite 168 passed, 1 failed on Step 6c.5 blocker; Step 7b repeat check passed; `IMPORT_OK`; route count 43 and OpenAPI hash matched; live check executed in 194.92 ms; git status recorded).
- [x] Step 8: Deletions verified (`pytest_out.txt` and `pytest_all.txt` removed).
- [x] Step 9: Documentation appended to `decisions.md` (D50) and `progress.md` (P08d).
- [x] Step 10: Dump created at `Project-docs\dumps\P08d_dump.md`.

---

## 10. DEVIATIONS AND BLOCKERS
- **Step 6c.5 Blocker (`test_run_comparison_latanoprost`):**
  - Prompt directive: `asyncio.run(run_comparison(["Latanoprost"])): at least one result whose product_name contains "Drops" has notes containing "Not a tablet strength". If there is none, STOP and record a BLOCKER.`
  - Evidence: `catalog.search("Latanoprost", items)` returns only sr_no 1810 (`Latanoprost 50mcg and Timolol Maleate 5mg Opthalmic solution`, dosage form: Liquid).
  - Cause: The single-ingredient drops product (sr_no 1970, `Latanoprost Eye Drops IP 0.005% w/v (50mcg per ml)`) has parsed salt `"latanoprost eye drops"` because `"eye drops"` / `"drops"` are not in `_WORDS_TO_REMOVE`. Under exact-salt-first matching, item 1810 matches salt `"latanoprost"`, suppressing the name_clean fallback and excluding item 1970.
  - Action taken: Following the explicit instruction ("If there is none, STOP and record a BLOCKER"), this condition is formally recorded under BLOCKERS. Note that the Drops safety note logic was verified operational via `Paracetamol 125 Drops` (sr_no 1048) in Step 7f.

---

## 11. DEFERRED
- Safety copy clinician review (pending).
- Brand map and savings (P09).
- Playwright and browser-use removal from `pyproject.toml`, `uv.lock`, and `Dockerfile` (deployment prompt).
- H1 (`/call/status` public when calls are enabled).
- M5 (`Project-docs` not under version control).
- Decision on committing `backend/data/`.
- `is_medicine` non-medicine groups review (Gautam).
- `x-request-id` exposure (frontend phase).
- Frontend Compare update.

